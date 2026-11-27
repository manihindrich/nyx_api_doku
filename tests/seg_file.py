"""Live tests for segment `file` (Swagger 0.0.1). Uploads/embeds/deletes touch only files registered by this run.
Discussion uploads and the one post go to the test discussion only (guard-enforced). Mail is never sent."""
import os
import re
import struct
import sys
import uuid
import zlib
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from http.client import IncompleteRead  # noqa: E402
from nyx import Client, Forbidden, Result, nonce, save_fixture  # noqa: E402
from nyx import TEST_DISC  # noqa: E402

SEG = "file"
DISC = TEST_DISC            # "test discussion": the only discussion written to
DP = f"/discussion/{DISC}"
UP = "/file/upload"
c = Client(SEG)


def C(*a, **k):
    """Transport errors become status -1 -> FAIL; harness is not changed."""
    try:
        return c.call(*a, **k)
    except (IncompleteRead, OSError) as e:
        return Result(-1, f"transport: {type(e).__name__}: {e}"[:200], {}, 0)


rows = []
_n = [0]
FIX = {}                 # fixture name -> first successful body
ERR_SEEN = set()         # (status, message) already saved as error fixture
UPLOADED = []            # dicts: label, id, url, mime, status
CREATED_FILES = []       # ids registered via c.created
DELETED_FILES = set()
POSTS = []               # own post ids still to clean up
POST_IDS = []            # every own post id created in this run


def tid():
    _n[0] += 1
    return f"T-{SEG}-{_n[0]:02d}"


def emit(t, status, verdict, note, res=None):
    if res is not None and res.status == -1:
        verdict = "FAIL"
    rows.append((t, status, verdict, note))
    print(f"{t} | {status} | {verdict} | {note}")


def type_ok(v, t):
    if t == "any":
        return True
    if t.endswith("?") and v is None:
        return True
    base = t.rstrip("?")
    if base == "int":
        return isinstance(v, int) and not isinstance(v, bool)
    if base == "str":
        return isinstance(v, str)
    if base == "bool":
        return isinstance(v, bool)
    if base == "dt":
        return isinstance(v, str) and re.match(r"\d{4}-\d{2}-\d{2}T", v) is not None
    if base == "dict":
        return isinstance(v, dict)
    if base == "list":
        return isinstance(v, list)
    raise ValueError(t)


def cmp(obj, spec, required=()):
    """-> (issues, extra keys). spec = {field: type}; `required` fields must be present."""
    if not isinstance(obj, dict):
        return [f"not object ({type(obj).__name__})"], []
    issues = [f"missing {k}" for k in required if k not in obj]
    issues += [f"{k}={type(v).__name__} (want {spec[k]})"
               for k, v in obj.items() if k in spec and not type_ok(v, spec[k])]
    return issues, sorted(set(obj) - set(spec))


# Swagger FileWithUrl (no field is marked required in the spec; the list below is the schema's full property set)
FILE_SPEC = {"id": "int", "file_type": "str", "id_specific": "int?", "id_specific2": "int?", "filename": "str",
             "size": "int", "uploaded_at": "dt", "mimetype": "str", "image_width": "int?",
             "image_height": "int?", "image_avg_color_hex": "str?", "image_embed": "bool", "url": "str",
             "thumb_url": "str"}
FILE_REQ = ("id", "file_type", "filename", "size", "uploaded_at", "mimetype", "image_embed", "url", "thumb_url")
JSON_ERR = {"error": "bool", "code": "str", "message": "str"}
UP_CLAIM = ("PUT /file/upload multipart: file binary, file_type FileTypeEnum (free_file|mail_attachment|mail_backup|"
            "discussion_attachment|discussion_backup|market_attachment|event_attachment), id_specific int "
            "('Podle typu souboru - id diskuze, 0 pro N/A (posta)'); 200 FileWithUrl; 400")
EMB_CLAIM = ("POST /file/embed/{id}/{state} id int, state boolean ('Prepne jestli se soubor ma ukladat jako odkaz "
             "nebo embedovat jako obrazek'; true = embed); 200; 400")
DEL_CLAIM = "DELETE /file/delete/{id} 'ID souboru ke smazani'; 200; 400"
SEND_CLAIM = ("POST /discussion/{discussionId}/send/text form content string required, format ContentFormatEnum "
              "text|html (default html); 200 empty body (JsonOk {}); 400")
GET_CLAIM = ("GET /discussion/{discussionId} 200 {context, discussion_common, posts[TemplatePost], presence}; "
             "discussion_common.waiting_files list (undocumented item schema)")
MAIL_CLAIM = "GET /mail: undocumented in this brief; checks whether waiting_files is present for mail attachments"


# ---------------------------------------------------------------- test files (generated, no disk input)
def png(w=1, h=1, rgb=(255, 0, 0)):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


GIF = (b"GIF89a\x01\x00\x01\x00\x80\x00\x00" + b"\xff\xff\xff\x00\x00\x00"
       + b"!\xf9\x04\x01\x00\x00\x00\x00" + b",\x00\x00\x00\x00\x01\x00\x01\x00\x00"
       + b"\x02\x02D\x01\x00" + b";")                       # 1x1 GIF89a
JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"  # SOI+APP0+EOI only
PDF = b"%PDF-1.4\n% fake test bytes\n%%EOF\n"


def fname(ext):
    return f"nyxapidoku-{uuid.uuid4().hex[:10]}.{ext}"


def fpart(ext, content, mime):
    return {"file": (fname(ext), content, mime)}


# ---------------------------------------------------------------- helpers
def msg(r):
    return r.body.get("message") if isinstance(r.body, dict) else str(r.body)[:80]


def save_err(r):
    key = (r.status, str(msg(r))[:80])
    if r.status >= 400 and key not in ERR_SEEN:
        ERR_SEEN.add(key)
        save_fixture(SEG, f"err_{r.status}_{len(ERR_SEEN)}", r.body)


def remember_fixture(name, r):
    if name not in FIX and r.status == 200:
        FIX[name] = r.body


def verdict_for(r, expect):
    """expect: '200' (Swagger 200), '400' (Swagger 400), 'auth' (no undocumented code allowed), 'any' (undocumented)."""
    s = r.status
    if s == -1:
        return "FAIL", "transport error"
    if s >= 500:
        return "FAIL", f"server error {s}: {msg(r)!r}"
    if expect == "200":
        if s == 200:
            return None, None          # caller checks the body
        if s == 400:
            return "DIFF", f"Swagger 200 -> 400 {msg(r)!r}"
        return "INFO", f"undocumented status {s}: {msg(r)!r}"
    if expect == "400":
        if s == 400:
            return "OK", f"400 {msg(r)!r}"
        if s == 200:
            return "DIFF", "Swagger 400 -> 200 accepted"
        return "INFO", f"undocumented status {s}: {msg(r)!r}"
    if expect == "auth":
        if s in (401, 403):
            return "INFO", f"undocumented auth rejection {s}: {msg(r)!r}"
        if s == 200:
            return "FAIL", "accepted without a valid token"
        return "INFO", f"undocumented status {s}: {msg(r)!r}"
    # 'any': Swagger does not mark the parameter required or document the case
    return "INFO", f"undocumented case, status {s}: {msg(r)!r}"


def upload(label, data, files, expect, auth=True):
    """-> (registered id or None, Result). Every id returned by a 200 is registered for cleanup at once."""
    t = tid()
    r = C("PUT", UP, data=data, files=files, auth=auth, test_id=t, claim=f"{UP_CLAIM}; {label}")
    fid = None
    if r.status == 200 and isinstance(r.body, dict) and isinstance(r.body.get("id"), int):
        fid = r.body["id"]
        c.created.append(("file", fid))
        CREATED_FILES.append(fid)
        UPLOADED.append({"label": label, "id": fid, "url": r.body.get("url"), "mime": (files or {}).get("file", ("", b"", ""))[2] if files else None, "status": 200})
    v, note = verdict_for(r, expect)
    if v is None:  # 200 on a 200-expected case: compare with FileWithUrl
        issues, extra = cmp(r.body, FILE_SPEC, FILE_REQ)
        if fid is None:
            v, note = "FAIL", "200 without integer id"
        elif issues or extra:
            v, note = "DIFF", f"id={fid} issues={issues} extra={extra}"
        else:
            v, note = "OK", f"id={fid} mimetype={r.body.get('mimetype')} size={r.body.get('size')} " \
                            f"embed={r.body.get('image_embed')}"
        remember_fixture("upload_200", r)
    elif r.status == 200 and fid is not None:
        note = f"id={fid} (200 where {expect} expected: {note})"
    emit(t, r.status, v, f"{label}: {note}", r)
    if r.status >= 400:
        save_err(r)
    return fid, r


# ---------------------------------------------------------------- A UPLOAD
PNG = png()
A_ids = {}
try:
    A_ids["png_disc"], _ = upload(f"A1 PNG discussion_attachment/{TEST_DISC}",
                                  {"file_type": "discussion_attachment", "id_specific": DISC},
                                  fpart("png", PNG, "image/png"), "200")
    A_ids["png_mail"], _ = upload("A2 PNG mail_attachment/0",
                                  {"file_type": "mail_attachment", "id_specific": 0},
                                  fpart("png", PNG, "image/png"), "200")
    # Other file_types: 0 as N/A. the test discussion only for discussion types (market/event the test discussion would be foreign objects).
    for ft in ("free_file", "mail_backup", "market_attachment", "event_attachment"):
        upload(f"A3 PNG {ft}/0", {"file_type": ft, "id_specific": 0}, fpart("png", PNG, "image/png"), "200")
    upload(f"A3 PNG discussion_backup/{TEST_DISC}", {"file_type": "discussion_backup", "id_specific": DISC},
           fpart("png", PNG, "image/png"), "200")
    A_ids["gif"], _ = upload(f"A4 GIF discussion_attachment/{TEST_DISC}", {"file_type": "discussion_attachment",
                                                                      "id_specific": DISC},
                             fpart("gif", GIF, "image/gif"), "200")
    upload(f"A4 JPEG discussion_attachment/{TEST_DISC}", {"file_type": "discussion_attachment", "id_specific": DISC},
           fpart("jpg", JPEG, "image/jpeg"), "200")
    upload(f"A4 text/html discussion_attachment/{TEST_DISC}", {"file_type": "discussion_attachment", "id_specific": DISC},
           fpart("html", f"<p>{nonce()}</p>".encode(), "text/html"), "200")
    upload("A4 random bytes, mime application/octet-stream (not in FileMimeTypeEnum)",
           {"file_type": "discussion_attachment", "id_specific": DISC},
           fpart("bin", os.urandom(64), "application/octet-stream"), "400")
    upload("A4 random bytes, mime octet/stream (FileMimeTypeEnum value)",
           {"file_type": "discussion_attachment", "id_specific": DISC},
           fpart("bin", os.urandom(64), "octet/stream"), "200")
    upload("A4 fake PDF, mime application/pdf (not in FileMimeTypeEnum)",
           {"file_type": "discussion_attachment", "id_specific": DISC},
           fpart("pdf", PDF, "application/pdf"), "400")
    # size: Swagger documents no limit -> any status is INFO, 5xx is FAIL
    upload("A5 ~5 MB random bytes discussion_attachment",
           {"file_type": "discussion_attachment", "id_specific": DISC},
           fpart("bin", os.urandom(5 * 1024 * 1024), "octet/stream"), "any")
    # error matrix
    upload("A6 missing file part", {"file_type": "discussion_attachment", "id_specific": DISC}, None, "400")
    upload("A6 missing file_type", {"id_specific": DISC}, fpart("png", PNG, "image/png"), "any")
    upload("A6 file_type=foo", {"file_type": "foo", "id_specific": DISC}, fpart("png", PNG, "image/png"), "400")
    upload("A6 id_specific missing", {"file_type": "discussion_attachment"}, fpart("png", PNG, "image/png"), "any")
    upload("A6 id_specific=999999999", {"file_type": "discussion_attachment", "id_specific": 999999999},
           fpart("png", PNG, "image/png"), "400")
    # auth
    upload("A7 no token", {"file_type": "discussion_attachment", "id_specific": DISC},
           fpart("png", PNG, "image/png"), "auth", auth=False)
    upload("A7 invalid token", {"file_type": "discussion_attachment", "id_specific": DISC},
           fpart("png", PNG, "image/png"), "auth", auth="invalid-token-nyxapidoku")

    # ------------------------------------------------------------ B WAITING FILES (before the post)
    t = tid()
    r = C("GET", DP, params={"order": "newest"}, test_id=t, claim=GET_CLAIM + "; B waiting_files before send")
    wf = (r.body.get("discussion_common") or {}).get("waiting_files") if isinstance(r.body, dict) else None
    if isinstance(wf, list):
        ids = [x.get("id") if isinstance(x, dict) else x for x in wf]
        own = [i for i in ids if i in CREATED_FILES]
        emit(t, r.status, "OK", f"waiting_files n={len(wf)} ids={ids} own={own} item_keys="
                                f"{sorted(wf[0]) if wf and isinstance(wf[0], dict) else '-'}", r)
        if wf:
            save_fixture(SEG, "waiting_files_example", wf)
    else:
        emit(t, r.status, "DIFF" if r.status == 200 else "FAIL", f"waiting_files missing/not list: {type(wf).__name__}", r)
    t = tid()
    r = C("GET", "/mail", test_id=t, claim=MAIL_CLAIM)
    mwf = (r.body.get("waiting_files") if isinstance(r.body, dict) else None)
    if isinstance(mwf, list):
        mids = [x.get("id") if isinstance(x, dict) else x for x in mwf]
        emit(t, r.status, "OK", f"mail waiting_files n={len(mwf)} ids={mids}", r)
    else:
        emit(t, r.status, "INFO", f"mail: no waiting_files list in response (type={type(mwf).__name__})", r)

    # ------------------------------------------------------------ C ATTACH (one post; no more posts)
    N = nonce()
    t = tid()
    r = C("POST", f"{DP}/send/text", data={"content": f"<p>file test {N}</p>", "format": "html"},
          test_id=t, claim=SEND_CLAIM + "; C post after uploads")
    if r.status == 200:
        emit(t, 200, "OK" if r.body in ({}, None, "") else "DIFF",
             f"send body={r.body!r:.60}", r)
    else:
        emit(t, r.status, "FAIL" if r.status == -1 else "INFO", f"send not 200: {msg(r)!r}", r)
    t = tid()
    r = C("GET", DP, params={"order": "newest"}, test_id=t, claim=GET_CLAIM + "; C find own post")
    found = [p for p in (r.body.get("posts") or []) if N in str(p)] if isinstance(r.body, dict) else []
    if found:
        p = found[0]
        POSTS.append(p["id"])
        POST_IDS.append(p["id"])
        c.created.append(("post", p["id"]))
        blob = str(p)
        refs = [u["id"] for u in UPLOADED if u.get("url") and u["url"] in blob]
        refs_id = [u["id"] for u in UPLOADED if str(u["id"]) in blob]
        emit(t, 200, "OK", f"own post {p['id']} found; uploaded urls in post: {refs}; ids mentioned: {refs_id}", r)
    else:
        emit(t, r.status, "FAIL" if r.status == 200 else "INFO", "own post not found in newest posts", r)
    t = tid()
    r = C("GET", DP, params={"order": "newest"}, test_id=t, claim=GET_CLAIM + "; C waiting_files after send")
    wf2 = (r.body.get("discussion_common") or {}).get("waiting_files") if isinstance(r.body, dict) else None
    left = [x.get("id") if isinstance(x, dict) else x for x in (wf2 or [])]
    emit(t, r.status, "INFO", f"waiting_files after send: n={len(left)} ids={left}", r)

    # ------------------------------------------------------------ D EMBED
    pid = A_ids.get("png_disc")
    if pid is None:
        emit(tid(), "-", "INFO", "D skipped: A1 upload not registered")
    else:
        for state in ("true", "false"):
            t = tid()
            r = C("POST", f"/file/embed/{pid}/{state}", test_id=t, claim=f"{EMB_CLAIM}; D embed {state}")
            if r.status == 200:
                issues, extra = cmp(r.body, FILE_SPEC, FILE_REQ) if isinstance(r.body, dict) and "id" in r.body else (["no FileWithUrl body"], [])
                exp = state == "true"
                got = r.body.get("image_embed") if isinstance(r.body, dict) else None
                v = "OK" if not issues and got is exp else "INFO"
                emit(t, 200, v, f"embed {state}: image_embed={got} issues={issues} extra={extra}", r)
                remember_fixture("embed_200", r)
            else:
                v, note = verdict_for(r, "400")
                emit(t, r.status, v, f"embed {state}: {note}", r)
                save_err(r)
        for st, exp in (("1", "400"), ("abc", "400")):
            t = tid()
            r = C("POST", f"/file/embed/{pid}/{st}", test_id=t, claim=f"{EMB_CLAIM}; D state={st}")
            v, note = verdict_for(r, exp)
            emit(t, r.status, v, f"state={st!r} (boolean expected): {note}", r)
            save_err(r)
        t = tid()
        try:
            C("POST", "/file/embed/999999999/true", test_id=t, claim=f"{EMB_CLAIM}; D non-registered id")
            emit(t, "-", "FAIL", "D non-registered embed: request sent (guard not active?)")
        except Forbidden as e:
            emit(t, "-", "INFO", f"D embed 999999999: not testable, guard Forbidden ({e})")

    # ------------------------------------------------------------ E DELETE
    gid = A_ids.get("gif")
    if gid is None:
        emit(tid(), "-", "INFO", "E skipped: GIF upload not registered")
    else:
        t = tid()
        r = C("DELETE", f"/file/delete/{gid}", test_id=t, claim=f"{DEL_CLAIM}; E delete uploaded GIF {gid}")
        if r.status == 200:
            DELETED_FILES.add(gid)
            remember_fixture("delete_200", r)
            emit(t, 200, "OK", f"deleted {gid}; body={str(r.body)[:80]!r}", r)
        else:
            v, note = verdict_for(r, "400")
            emit(t, r.status, v, f"delete {gid}: {note}", r)
            save_err(r)
        t = tid()
        r = C("DELETE", f"/file/delete/{gid}", test_id=t, claim=f"{DEL_CLAIM}; E delete again {gid}")
        v, note = verdict_for(r, "400")
        if r.status == 200:
            v, note = "DIFF", "second delete of same id returned 200"
        emit(t, r.status, v, f"delete again: {note}", r)
        save_err(r)
    t = tid()
    try:
        C("DELETE", "/file/delete/999999999", test_id=t, claim=f"{DEL_CLAIM}; E delete non-registered")
        emit(t, "-", "FAIL", "E delete 999999999: request sent (guard not active?)")
    except Forbidden as e:
        emit(t, "-", "INFO", f"E delete 999999999: not testable, guard Forbidden ({e})")

finally:
    # cleanup: own post(s) first, then every registered file not yet deleted
    for pid_ in list(POSTS):
        t = tid()
        r = C("DELETE", f"{DP}/delete/{pid_}", test_id=t, claim="DELETE /discussion/{discussion_id}/delete/{id} "
                                                              "'Smaze prispevek'; CLEANUP own post")
        if r.status == 200:
            POSTS.remove(pid_)
        emit(t, r.status, "OK" if r.status == 200 else "FAIL", f"CLEANUP post {pid_}: {msg(r)!r:.60}", r)
    for fid_ in CREATED_FILES:
        if fid_ in DELETED_FILES:
            continue
        t = tid()
        r = C("DELETE", f"/file/delete/{fid_}", test_id=t, claim=f"{DEL_CLAIM}; CLEANUP registered file")
        if r.status == 200:
            DELETED_FILES.add(fid_)
            remember_fixture("delete_200", r)
        emit(t, r.status, "OK" if r.status == 200 else "FAIL", f"CLEANUP file {fid_}: {str(r.body)[:60]!r}", r)

# ---------------------------------------------------------------- F FINAL CHECK
t = tid()
r = C("GET", DP, params={"order": "newest"}, test_id=t, claim=GET_CLAIM + "; F final waiting_files")
wf_final = (r.body.get("discussion_common") or {}).get("waiting_files") if isinstance(r.body, dict) else None
still = [x.get("id") if isinstance(x, dict) else x for x in (wf_final or [])]
alive_posts = [p["id"] for p in (r.body.get("posts") or []) if p.get("id") in POST_IDS] if isinstance(r.body, dict) else []
emit(t, r.status, "OK" if wf_final == [] and not alive_posts else "FAIL",
     f"F final discussion waiting_files={still}; own posts still visible={alive_posts}", r)
t = tid()
r = C("GET", "/mail", test_id=t, claim=MAIL_CLAIM + "; F final")
mwf_f = r.body.get("waiting_files") if isinstance(r.body, dict) else None
emit(t, r.status, "OK" if mwf_f == [] else ("INFO" if mwf_f is None else "FAIL"),
     f"F final mail waiting_files={mwf_f if mwf_f is None else [x.get('id') if isinstance(x, dict) else x for x in mwf_f]}", r)

# ---------------------------------------------------------------- summary + fixtures
print("registered file ids:", CREATED_FILES)
print("deleted file ids:", sorted(DELETED_FILES), "| not deleted:", [i for i in CREATED_FILES if i not in DELETED_FILES])
print("posts created:", POST_IDS, "| still undeleted:", POSTS)
print("counts:", dict(Counter(v for _, _, v, _ in rows)))
for name, body in FIX.items():
    save_fixture(SEG, name, body)
print("fixtures: see tests/fixtures/file/")
