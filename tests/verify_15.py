"""Strict re-verification of every claim in docs/15_swagger-diff.md against the live API.

Run from the repo root: python3 -I tests/verify_15.py (token and test account values in .env)
Records: tests/results/verify/T-verify-NN.json (+ summary.json). Writes only in the allowlist
(the test discussion, the peer user) and cleans up after itself.
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nyx import RESULTS, Client, nonce  # noqa: E402
from nyx import TEST_USER, PEER_USER, TEST_DISC, PUBLIC_DISC, HEADER_ITEM  # noqa: E402

SEG = "verify"
DISC = TEST_DISC            # own test discussion (write target)
PUBLIC = PUBLIC_DISC           # someone else's public discussion (GET only)
c = Client(SEG)
N = 0
OUT = {}                 # claim id -> list of evidence lines
ERRORS = []              # every non-2xx body seen: (tid, status, body)
BODIES = {}              # endpoint label -> list of 200 bodies (for field scans)


def call(cid, method, path, **kw):
    global N
    N += 1
    tid = f"T-verify-{N:02d}"
    r = c.call(method, path, test_id=tid, claim=f"{cid}: docs/15_swagger-diff.md", **kw)
    if not r.ok:
        ERRORS.append((tid, r.status, r.body))
    return tid, r


def ev(cid, tid, text):
    line = f"{tid} | {text}"
    OUT.setdefault(cid, []).append(line)
    print(f"{cid} | {line}")


def walk(o, path=""):
    """Yield (path, key, value) for every dict entry."""
    if isinstance(o, dict):
        for k, v in o.items():
            yield path, k, v
            yield from walk(v, f"{path}.{k}")
    elif isinstance(o, list):
        for x in o:
            yield from walk(x, path + "[]")


def brief(r):
    return json.dumps(r.body, ensure_ascii=False)[:160]


def posts(r):
    return r.body.get("posts") or [] if isinstance(r.body, dict) else []


def header_item(body):
    dc = body.get("discussion_common") or {}
    sd = dc.get("discussion_specific_data") if isinstance(dc.get("discussion_specific_data"), dict) else {}
    items = sd.get("header") or dc.get("header") or []
    return next((i for i in items if isinstance(i, dict) and i.get("id") == HEADER_ITEM), None)


def raw_of(item):
    cr = (item or {}).get("content_raw") or {}
    d = cr.get("data") if isinstance(cr, dict) else None
    return (d.get("data"), d.get("format")) if isinstance(d, dict) else (None, None)


def find_post(text, tries=3):
    for _ in range(tries):
        tid, r = call("helper", "GET", f"/discussion/{DISC}")
        for p in posts(r):
            if text in json.dumps(p, ensure_ascii=False):
                return p
        time.sleep(2)
    return None


try:
    # ------------------------------------------------------------ A1 auth / 401 shapes
    tid, r = call("A1", "GET", "/notepad", auth=False)
    ev("A1", tid, f"GET /notepad no token -> {r.status} {brief(r)}")
    tid, r = call("A1", "GET", "/notepad", auth="invalid-nyxapidoku")
    ev("A1", tid, f"GET /notepad invalid token -> {r.status} {brief(r)}")
    tid, r = call("A1", "POST", "/discussion/rights/add",
                  params={"discussion_id": DISC, "username": PEER_USER}, auth=False)
    ev("A1", tid, f"POST /discussion/rights/add no token -> {r.status} {brief(r)}")
    tid, r = call("A1", "GET", "/notepad")
    ev("A1", tid, f"GET /notepad with Bearer token -> {r.status}")
    notepad = r.body

    # ------------------------------------------------------------ A2/A3 error statuses + code field
    tid, r = call("A2", "GET", "/notepad/999999999")
    ev("A2", tid, f"GET /notepad/999999999 -> {r.status} {brief(r)}")
    ev("E2", tid, f"GET /notepad/999999999 -> {r.status} {brief(r)}")
    tid, r = call("A2", "GET", "/notepad/abc")
    ev("A2", tid, f"GET /notepad/abc -> {r.status} {brief(r)}")
    ev("E2", tid, f"GET /notepad/abc -> {r.status} {brief(r)}")
    tid, r = call("A3", "POST", "/mail/reminder/1/abc")
    ev("A3", tid, f"POST /mail/reminder/1/abc (path bool) -> {r.status} {brief(r)}")
    ev("E5", tid, f"POST /mail/reminder/1/abc -> {r.status} {brief(r)}")
    tid, r = call("A3", "POST", "/mail/reminder/1/1")
    ev("A3", tid, f"POST /mail/reminder/1/1 -> {r.status} {brief(r)}")
    tid, r = call("A3", "GET", f"/discussion/{DISC}/bookmark", params={"new_state": "abc"})
    ev("A3", tid, f"GET /discussion/{DISC}/bookmark?new_state=abc (query bool) -> {r.status} {brief(r)}")
    tid, r = call("E5", "POST", "/mail/reminder/999999999/true")
    ev("E5", tid, f"POST /mail/reminder/999999999/true -> {r.status} {brief(r)}")
    tid, r = call("A2", "PUT", "/file/upload", data={"file_type": "discussion_attachment", "id_specific": 999999999},
                  files={"file": ("nyxapidoku-x.txt", nonce().encode(), "text/plain")})
    ev("A2", tid, f"PUT /file/upload id_specific=999999999 -> {r.status} {brief(r)}")
    if r.ok and isinstance(r.body, dict) and r.body.get("id"):
        c.created.append(("file", r.body["id"]))

    # ------------------------------------------------------------ A3 silently ignored values
    base = call("A3", "GET", "/last")
    one = call("A3", "GET", "/last", params={"rated_by_me": "1"})
    tru = call("A3", "GET", "/last", params={"rated_by_me": "true"})
    ids = lambda r: [p.get("id") for p in posts(r)]
    ev("A3", one[0], f"/last?rated_by_me=1 -> {one[1].status}; same ids as no filter: {ids(one[1]) == ids(base[1])}")
    ev("E11", one[0], f"/last?rated_by_me=1 same as no filter: {ids(one[1]) == ids(base[1])}; "
                      f"=true same as no filter: {ids(tru[1]) == ids(base[1])} ({len(ids(tru[1]))} posts)")
    rbf1 = call("E11", "GET", "/last", params={"rated_by_friends": "1"})
    rbft = call("E11", "GET", "/last", params={"rated_by_friends": "true"})
    ev("E11", rbf1[0], f"/last?rated_by_friends=1 same as none: {ids(rbf1[1]) == ids(base[1])}; "
                       f"=true same as none: {ids(rbft[1]) == ids(base[1])}")
    tid, r = call("A3", "GET", "/mail", params={"order": "foo"})
    ev("A3", tid, f"/mail?order=foo -> {r.status}")
    BODIES.setdefault("last", []).append(base[1].body)

    # E11: discussion_name in /last posts
    ps = posts(base[1])
    ev("E11", base[0], f"/last: {len(ps)} posts, with discussion_name: {sum('discussion_name' in p for p in ps)}")

    # ------------------------------------------------------------ E1 notepad structure
    ents = (notepad or {}).get("entries") if isinstance(notepad, dict) else None
    ev("E1", "T-verify-04", f"/notepad top keys {list((notepad or {}).keys())}; entries[0] keys "
                            f"{list(ents[0].keys()) if ents else None}; n={len(ents or [])}; "
                            f"each entry has 'entries': {all('entries' in e for e in ents or [])}")
    notes = [x for e in ents or [] for x in (e.get("entries") or [])]
    ev("N1", "T-verify-04", f"notepad notes inside categories: {len(notes)}")

    # ------------------------------------------------------------ E3 bookmarks history
    hist_total, hist_with = 0, 0
    for params in ({}, {"more_results": "true"}, {"show_read": "true", "more_results": "true"},
                   {"show_read": "true", "show_booked": "true", "more_results": "true"}):
        tid, r = call("E3", "GET", "/bookmarks/history", params=params)
        ds = (r.body or {}).get("discussions") or []
        w = sum("new_replies_count" in d for d in ds)
        hist_total += len(ds); hist_with += w
        ev("E3", tid, f"/bookmarks/history {params} -> {r.status}, {len(ds)} entries, with new_replies_count: {w}")
        BODIES.setdefault("history", []).append(r.body)
    tid, r = call("E3", "GET", "/bookmarks/history/more", params={"show_read": "true"})
    ds = (r.body or {}).get("discussions") or []
    ev("E3", tid, f"/bookmarks/history/more -> {r.status}, {len(ds)} entries, with new_replies_count: "
                  f"{sum('new_replies_count' in d for d in ds)}")
    tid, r = call("E3", "GET", "/bookmarks/all")
    cnt = sum(1 for _, k, _ in walk(r.body) if k == "new_replies_count")
    ev("E3", tid, f"(context) /bookmarks/all -> new_replies_count occurrences: {cnt}")
    BODIES.setdefault("bookmarks_all", []).append(r.body)

    # ------------------------------------------------------------ E4 mail (several pages)
    mail_posts, mail_rem, convs = [], [], []
    tid, r = call("E4", "GET", "/mail")
    pages = [r]
    for _ in range(5):
        last = posts(pages[-1])
        if not last:
            break
        tid, r = call("E4", "GET", "/mail", params={"order": "older_than", "from_id": min(p["id"] for p in last)})
        pages.append(r)
    for r in pages:
        mail_posts += posts(r)
        mail_rem += (r.body or {}).get("reminders") or []
        convs += (r.body or {}).get("conversations") or []
        BODIES.setdefault("mail", []).append(r.body)
    allp = mail_posts + mail_rem

    def vals(lst, k):
        return sorted({json.dumps(p[k]) for p in lst if k in p}), sum(k in p for p in lst)
    for k in ("incoming", "reminder", "unread", "new", "preview", "other_mail_id"):
        v, n = vals(allp, k)
        ev("E4", tid, f"/mail posts+reminders ({len(allp)} items, {len(pages)} pages): '{k}' present in {n}, values {v[:4]}")
    v, n = vals(convs, "incoming")
    ev("E4", tid, f"(context) conversations ({len(convs)}): 'incoming' present in {n}, values {v}")

    # ------------------------------------------------------------ E6/E7/E8 discussion
    tid, r = call("E6", "GET", f"/discussion/{DISC}")
    ev("E6", tid, f"/discussion/{DISC} top keys: {list((r.body or {}).keys())}")
    BODIES.setdefault("discussion", []).append(r.body)
    orig_header = raw_of(header_item(r.body))
    tid, r = call("E6", "GET", f"/discussion/{PUBLIC}")
    ev("E6", tid, f"/discussion/{PUBLIC} top keys: {list((r.body or {}).keys())}")
    BODIES.setdefault("discussion", []).append(r.body)
    pub_base = posts(r)
    rated = sorted({p.get("rating") for p in pub_base if isinstance(p.get("rating"), int) and p.get("rating")})
    ev("E7", tid, f"ratings present in base page of {PUBLIC}: {rated}")
    # pick thresholds actually present so inclusivity is observable
    pos = [x for x in rated if x > 0]
    neg = [x for x in rated if x < 0]
    for n in ([pos[len(pos) // 2]] if pos else [1]) + ([neg[0]] if neg else [-1]):
        tid, r = call("E7", "GET", f"/discussion/{PUBLIC}", params={"rating": n})
        rs = [p.get("rating", 0) for p in posts(r)]
        ok = all(x >= n for x in rs) if n > 0 else all(x <= n for x in rs)
        ev("E7", tid, f"rating={n}: {len(rs)} posts, ratings min {min(rs) if rs else None} max {max(rs) if rs else None}; "
                      f"posts with rating == {n}: {rs.count(n)}; all {'>=' if n > 0 else '<='} {n}: {ok}")
    tid, r = call("E8", "GET", f"/discussion/{PUBLIC}", auth=False)
    ev("E8", tid, f"/discussion/{PUBLIC} (public) without token -> {r.status} {len(posts(r))} posts")
    tid, r = call("E8", "GET", f"/discussion/{DISC}", auth=False)
    ev("E8", tid, f"/discussion/{DISC} (non-public) without token -> {r.status} {brief(r)}")

    # ------------------------------------------------------------ A4 booleans / A5 Activity
    for label, bodies in BODIES.items():
        false_k, zero_k, bool_true = set(), set(), set()
        for b in bodies:
            for p, k, v in walk(b):
                if v is False:
                    false_k.add(k)
                elif v is True:
                    bool_true.add(k)
                elif v == 0 and isinstance(v, int) and not isinstance(v, bool):
                    zero_k.add(k)
        ev("A4", "-", f"{label}: keys with false: {sorted(false_k)}; keys with 0: {sorted(zero_k)[:15]}")
    tid, r = call("A4", "GET", "/notifications")
    nb = r.body if isinstance(r.body, dict) else {}
    fk = sorted({k for _, k, v in walk(nb) if v is False})
    ev("A4", tid, f"/notifications: keys with false: {fk}")
    ev("E12", tid, f"/notifications top keys: {list(nb.keys())}; notifications len "
                   f"{len(nb.get('notifications') or [])}; 'posts' present: {'posts' in nb}")
    act_keys = {}
    for bodies in BODIES.values():
        for b in bodies:
            for p, k, v in walk(b):
                if k == "activity" and isinstance(v, dict):
                    for kk in v:
                        act_keys[kk] = act_keys.get(kk, 0) + 1
                if k == "active_friends" and isinstance(v, list):
                    for a in v:
                        for kk in a:
                            act_keys[kk] = act_keys.get(kk, 0) + 1
    ev("A5", "-", f"Activity keys seen (count): {act_keys}")

    # ------------------------------------------------------------ A6 format=markdown (discussion)
    mark = nonce()
    md = f"**bold** _it_ {mark}"
    tid, r = call("A6", "POST", f"/discussion/{DISC}/send/text", data={"content": md, "format": "markdown"})
    ev("A6", tid, f"send/text format=markdown -> {r.status} {brief(r)}")
    p = find_post(mark) if r.ok else None
    md_post = p
    if p:
        c.created.append(("post", p["id"]))
        ev("A6", tid, f"stored content={json.dumps(p.get('content'), ensure_ascii=False)[:120]}; "
                      f"content_raw={json.dumps(p.get('content_raw'), ensure_ascii=False)[:160]}")
    m2 = nonce()
    tid, r = call("A6", "POST", f"/discussion/{DISC}/send/text", data={"content": f"x {m2}", "format": "foo"})
    ev("A6", tid, f"(context) send/text format=foo -> {r.status} {brief(r)}")
    if r.ok:
        p2 = find_post(m2)
        if p2:
            c.created.append(("post", p2["id"]))

    # ------------------------------------------------------------ E9 content save
    if md_post:
        tid, r = call("E9", "POST", f"/discussion/{DISC}/content/{md_post['id']}/save",
                      data={"content": f"edited {nonce()}", "format": "text"})
        ev("E9", tid, f"save on own post {md_post['id']} -> {r.status} {brief(r)}")
        after = find_post(mark)
        ev("E9", tid, f"post content after save attempt still original: {bool(after) and mark in (after.get('content') or '')}")
    ev("E9", "-", f"header item {HEADER_ITEM} original raw: {orig_header}")
    if orig_header[0] is not None:
        hm = nonce()
        tid, r = call("E9", "POST", f"/discussion/{DISC}/content/{HEADER_ITEM}/save",
                      data={"content": f"verify {hm}", "format": "text"})
        ev("E9", tid, f"save on header item -> {r.status} {brief(r)}")
        t2, r2 = call("E9", "GET", f"/discussion/{DISC}")
        ev("E9", t2, f"header after save contains marker: {hm in json.dumps(header_item(r2.body), ensure_ascii=False)}")
        t3, r3 = call("E9", "POST", f"/discussion/{DISC}/content/{HEADER_ITEM}/save",
                      data={"content": orig_header[0], "format": orig_header[1] or "text"})
        t4, r4 = call("E9", "GET", f"/discussion/{DISC}")
        ev("E9", t4, f"header restored -> {r3.status}; raw equal to original: {raw_of(header_item(r4.body)) == orig_header}")

    # ------------------------------------------------------------ E10 rights
    RP = "/discussion/rights"
    q = lambda right, s=None: {k: v for k, v in {"discussion_id": DISC, "username": PEER_USER, "right": right,
                                                  "set": s}.items() if v is not None}
    tid, r = call("E10", "POST", RP, params=q("read"))
    ev("E10", tid, f"rights right=read WITHOUT set -> {r.status} {brief(r)}")
    base_r = r.body if r.ok and isinstance(r.body, dict) else None
    t0, rd = call("E10", "GET", f"/discussion/{DISC}")
    pub0 = (((rd.body or {}).get("discussion_common") or {}).get("discussion") or {}).get("public")
    ev("E10", t0, f"discussion.public before: {pub0}")
    for right in ("grant_edit_rights", "public"):
        for s in ("false", "true"):
            tid, r = call("E10", "POST", RP, params=q(right, s))
            ev("E10", tid, f"right={right} set={s} -> {r.status} {brief(r)}")
    t0, rd = call("E10", "GET", f"/discussion/{DISC}")
    pub1 = (((rd.body or {}).get("discussion_common") or {}).get("discussion") or {}).get("public")
    ev("E10", t0, f"discussion.public after: {pub1} (unchanged: {pub0 == pub1})")
    if base_r:
        order = ["ar_read", "ar_write", "ar_delete", "ar_edit", "ar_rights"]
        names = {"ar_read": "read", "ar_write": "write", "ar_delete": "delete", "ar_edit": "edit", "ar_rights": "edit_rights"}
        held = [f for f in order if base_r.get(f)]
        ev("E10", "-", f"{PEER_USER} baseline rights: {held}")
        if len(held) >= 2:
            low = held[0]
            tid, r = call("E10", "POST", RP, params=q(names[low], "false"))
            still = isinstance(r.body, dict) and r.body.get(low)
            ev("E10", tid, f"remove '{names[low]}' while higher '{names[held[-1]]}' set -> {r.status}; "
                           f"{low} still true: {still}")
            if not still:
                t2, r2 = call("E10", "POST", RP, params=q(names[low], "true"))
                ev("E10", t2, f"restored {names[low]} -> {r2.status} {brief(r2)}")
        tid, r = call("E10", "POST", RP, params=q("read"))
        ev("E10", tid, f"final {PEER_USER} rights equal baseline: {r.body == base_r}")

    # ------------------------------------------------------------ E13/E14 file upload / delete
    up = []
    samples = [("pdf", b"%PDF-1.4\n% nyxapidoku\n%%EOF\n", "application/pdf"),
               ("bin", os.urandom(64), "application/octet-stream"),
               ("zip", b"PK\x05\x06" + b"\x00" * 18, "application/zip"),
               ("txt", nonce().encode(), "text/plain")]
    for ext, data, mime in samples:
        tid, r = call("E13", "PUT", "/file/upload", data={"file_type": "discussion_attachment", "id_specific": DISC},
                      files={"file": (f"nyxapidoku-verify.{ext}", data, mime)})
        b = r.body if isinstance(r.body, dict) else {}
        if r.ok and b.get("id"):
            c.created.append(("file", b["id"]))
            up.append(b["id"])
        ev("E13", tid, f"upload {mime} -> {r.status}; mimetype={b.get('mimetype')} thumb_url={json.dumps(b.get('thumb_url'))} "
                       f"image_embed_option={b.get('image_embed_option')!r} (key present: {'image_embed_option' in b})")
    if up:
        fid = up[0]
        tid, r = call("E14", "DELETE", f"/file/delete/{fid}")
        ev("E14", tid, f"delete {fid} first -> {r.status} {brief(r)}")
        tid, r = call("E14", "DELETE", f"/file/delete/{fid}")
        ev("E14", tid, f"delete {fid} second -> {r.status} {brief(r)}")
        for f in up[1:]:
            call("cleanup", "DELETE", f"/file/delete/{f}")
        up = []

    # ------------------------------------------------------------ E15 search username
    for u in (TEST_USER[:3], TEST_USER):
        tid, r = call("E15", "GET", f"/search/username/{u}")
        rows = [x for k in ("exact", "friends", "others") for x in ((r.body or {}).get(k) or [])]
        ev("E15", tid, f"/search/username/{u} -> {r.status}; row keys {sorted({k for x in rows for k in x})}")
    for u in ("N", "!!", "A" * 20, ""):
        tid, r = call("E15", "GET", f"/search/username/{u}")
        ev("E15", tid, f"/search/username/{u!r} -> {r.status} {brief(r)[:80]}")

    # ------------------------------------------------------------ E16 search-v2 order without from_id
    t, rn = call("E16", "GET", "/search-v2", params={"user": TEST_USER, "order": "newest"})
    for o in ("newer_than", "older_than"):
        tid, r = call("E16", "GET", "/search-v2", params={"user": TEST_USER, "order": o})
        ev("E16", tid, f"search-v2 order={o} no from_id -> {r.status}; ids == newest: {ids(r) == ids(rn)} ({len(ids(r))})")
    t, ro = call("E16", "GET", "/search-v2", params={"user": TEST_USER, "order": "oldest"})
    ev("E16", t, f"(control) order=oldest ids == newest: {ids(ro) == ids(rn)}")

    # ------------------------------------------------------------ E17 unified
    for s in ("nyx", "@NYX", f"@{TEST_USER} test"):
        tid, r = call("E17", "GET", "/search/unified", params={"search": s})
        b = r.body
        ev("E17", tid, f"unified search={s!r} -> {r.status}; type {type(b).__name__}; "
                       f"top keys {list(b.keys()) if isinstance(b, dict) else None}; "
                       f"inner keys {list(next(iter(b.values())).keys()) if isinstance(b, dict) and b and isinstance(next(iter(b.values())), dict) else None}")

    # ------------------------------------------------------------ N4 rate-limit headers (passive)
    tid, r = call("N4", "GET", "/notifications")
    rl = {k: v for k, v in r.headers.items() if "rate" in k.lower() or "limit" in k.lower() or k.lower() == "retry-after"}
    ev("N4", tid, f"rate-limit related headers: {rl or 'none'}")

finally:
    # cleanup: own posts and files created in this run
    for kind, oid in list(c.created):
        try:
            if kind == "post":
                tid, r = call("cleanup", "DELETE", f"/discussion/{DISC}/delete/{oid}")
                print(f"cleanup post {oid} -> {r.status}")
            elif kind == "file":
                tid, r = call("cleanup", "DELETE", f"/file/delete/{oid}")
                print(f"cleanup file {oid} -> {r.status}")
        except Exception as e:  # noqa: BLE001
            print("cleanup error", kind, oid, e)
    # catch any stray post from format=foo
    try:
        tid, r = call("cleanup", "GET", f"/discussion/{DISC}")
        for p in posts(r):
            if p.get("username") == TEST_USER and "nyxapidoku" in (p.get("content") or "") and ("post", p["id"]) not in c.created:
                print("STRAY own test post left:", p["id"])
    except Exception as e:  # noqa: BLE001
        print("final check error", e)
    codes = {}
    for tid, st, body in ERRORS:
        has = isinstance(body, dict) and ("code" in body or (isinstance(body.get("error"), dict) and "code" in body["error"]))
        codes.setdefault(st, []).append((tid, has))
    for st, lst in sorted(codes.items()):
        ev("A2", "-", f"status {st}: {len(lst)} responses, with a 'code' key: {sum(h for _, h in lst)} {[t for t, h in lst if h]}")
    d = RESULTS / SEG
    d.mkdir(parents=True, exist_ok=True)
    (d / "summary.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1))
    print("calls:", N)
