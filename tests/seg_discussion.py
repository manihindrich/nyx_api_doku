"""Live tests for segment `discussion` (Swagger 0.0.1). Writes only in the test discussion (guard-enforced)."""
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from http.client import IncompleteRead  # noqa: E402
from nyx import Client, Forbidden, Result, nonce, save_fixture  # noqa: E402
from nyx import TEST_USER, PEER_USER, TEST_DISC, PUBLIC_DISC, PEER_POST, HEADER_ITEM  # noqa: E402

SEG = "discussion"
DISC = TEST_DISC            # "test discussion": the only discussion written to
HEADER_ORIG = None         # original header text, read live before the save test
DP = f"/discussion/{DISC}"
RG = f"{DP}/rating"
RM = f"{DP}/reminder"
BMP = f"{DP}/bookmark"
c = Client(SEG)


def C(*a, **k):
    """Transport errors become status -1 -> FAIL; harness is not changed."""
    try:
        return c.call(*a, **k)
    except (IncompleteRead, OSError) as e:
        return Result(-1, f"transport: {type(e).__name__}: {e}"[:200], {}, 0)


rows = []        # (tid, status, verdict, note, Result|None)
_n = [0]
FIX = {}         # fixture name -> first successful body
ALIVE = []       # own posts still existing (cleanup list)
DELETED = []
CREATED = []
DIRTY = set()    # posts with a rating that may still be set (cleanup: remove)
SENT = {}        # send label -> post id


def tid():
    _n[0] += 1
    return f"T-{SEG}-{_n[0]:02d}"


def emit(t, status, verdict, note, res=None):
    if res is not None and res.status == -1:
        verdict = "FAIL"
    rows.append((t, status, verdict, note, res))
    print(f"{t} | {status} | {verdict} | {note}")


# Swagger shapes. "x?" = nullable. Undocumented/uncertain fields are typed "any".
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


POST_SPEC = {"id": "int", "discussion_id": "int", "username": "str", "content": "str?", "content_raw": "any",
             "post_type": "str?", "reminder": "bool", "rating": "int", "my_rating": "str?", "replies": "list",
             "inserted_at": "dt", "activity": "dict?", "new": "bool", "preview": "bool",
             "can_be_deleted": "bool", "can_be_rated": "bool", "can_be_reminded": "bool",
             "can_ignore_discussion": "bool", "rating_friends": "list"}
POST_REQ = ("id", "discussion_id", "username", "content", "inserted_at")
TOP = {"context": "dict", "discussion_common": "dict?", "posts": "list", "presence": "list?"}
COMMON = {"discussion": "dict", "owner": "dict?", "access_right": "dict?", "bookmark": "dict?",
          "waiting_files": "list", "discussion_specific_data": "dict?"}
DISC_OBJ = {"id": "int", "domain_id": "int", "domain_category_id": "int", "name_static": "str",
            "name_dynamic": "str?", "has_header": "bool", "has_home": "bool", "last_post_id": "int?",
            "posts_count": "int", "image_posts_count": "int", "link_posts_count": "int", "ar_read": "bool",
            "ar_write": "bool", "ar_delete": "bool", "ar_edit": "bool", "ar_rights": "bool", "public": "bool",
            "discussion_type": "str", "last_header_change": "dt", "hashtags": "list"}
BOOK_SPEC = {"discussion_id": "int", "bookmark": "bool", "category_id": "int?", "replies_count": "int",
             "last_seen_post_id": "int", "last_seen_posts_count": "int", "last_seen_image_posts_count": "int",
             "last_seen_link_posts_count": "int", "last_visited_at": "dt"}
ACC_SPEC = {"discussion_id": "int", "ar_read": "bool", "ar_write": "bool", "ar_delete": "bool",
            "ar_edit": "bool", "ar_rights": "bool", "days_left": "int"}
ITEM_SPEC = {"id": "int", "discussion_id": "int", "location": "str", "sort_order": "int", "content": "str?",
             "content_raw": "any", "post_type": "str?"}
TAG_SPEC = {"username": "str", "tag": "str"}
TAGS = {"positive", "negative", "negative_visible", "removed", "reminder"}
JSON_ERR = {"error": "bool", "code": "str", "message": "str"}

GET_CLAIM = ("GET /discussion/{discussionId} 200 {context, discussion_common, posts[TemplatePost], presence}; "
             "required context, posts; user Username; text SearchExpression; rating int (negative: lower than value, "
             "positive: greater than value; disables text search); reminders bool; order newest|newer_than|"
             "older_than|oldest (newer_than/older_than need from_id); last_visit int>=1; from_id int>=1; 400 JsonError")
SEND_CLAIM = ("POST /discussion/{discussionId}/send/text form content string required, format ContentFormatEnum "
              "text|html (default html); 200 empty body (JsonOk {}); 400")
RATE_CLAIM = ("POST /discussion/{discussion_id}/rating/{id}/{action} action remove|positive|negative|"
              "negative_visible; 200 DiscussionPostWithName; 400; 403 NeedsConfirmation")
RATEGET_CLAIM = ("GET /discussion/{discussion_id}/rating/{id} 200 array of {username, tag TagTypeEnum "
                 "(positive|negative|negative_visible|removed|reminder)}; 400")
REM_CLAIM = "POST /discussion/{discussion_id}/reminder/{id}/{new_state} id int>=1, new_state boolean; 200 empty; 400"
BM_CLAIM = ("POST|GET /discussion/{discussion_id}/bookmark query new_state boolean required, category int optional; "
            "200 empty; 400; discussion_common.bookmark {bookmark bool, category_id int nullable}")
SAVE_CLAIM = ("POST /discussion/{discussionId}/content/{contentId}/save form content string required, format "
              "ContentFormatEnum; 'Ulozeni obsahu diskuze (text prispevku ci obsah sekce na nastence)'; 200; 400")
DEL_CLAIM = "DELETE /discussion/{discussion_id}/delete/{id} 'Smaze prispevek'; 200; 400"


def msg(r):
    return r.body.get("message") if isinstance(r.body, dict) else str(r.body)[:80]


def err_shape(r):
    iss, _ = cmp(r.body, JSON_ERR, ("error", "message"))
    return f"msg={msg(r)!r}" + (f"; JsonError {iss}" if iss else "")


def posts_of(r):
    if r.status == 200 and isinstance(r.body, dict) and isinstance(r.body.get("posts"), list):
        return [p for p in r.body["posts"] if isinstance(p, dict)]
    return []


def ids_of(r):
    return [p.get("id") for p in posts_of(r)]


def users_in(r):
    return {str(p.get("username")) for p in posts_of(r)}


def plain(s):
    return re.sub(r"<[^>]+>", "", s or "").replace("&amp;", "&").lower()


def bmk(b):
    dc = b.get("discussion_common") if isinstance(b, dict) else None
    return dc.get("bookmark") if isinstance(dc, dict) else None


def header_items(b):
    dc = b.get("discussion_common") if isinstance(b, dict) else None
    dc = dc if isinstance(dc, dict) else {}
    sd = dc.get("discussion_specific_data") if isinstance(dc.get("discussion_specific_data"), dict) else {}
    h = sd.get("header")
    if h is None:
        h = dc.get("header")
    return h if isinstance(h, list) else []


def hdr_item(r):
    return next((i for i in header_items(r.body) if isinstance(i, dict) and i.get("id") == HEADER_ITEM), None)


def body_issues(b):
    if not isinstance(b, dict):
        return [f"not object ({type(b).__name__})"], []
    iss, ex = cmp(b, TOP, ("context", "posts"))
    pex = {f"top.{x}" for x in ex}
    for i, p in enumerate(b.get("posts") if isinstance(b.get("posts"), list) else []):
        pi, pe = cmp(p, POST_SPEC, POST_REQ)
        iss += [f"posts[{i}].{x}" for x in pi]
        pex |= {f"posts.{x}" for x in pe}
    dc = b.get("discussion_common")
    if isinstance(dc, dict):
        di, de = cmp(dc, COMMON)
        iss += [f"discussion_common.{x}" for x in di]
        pex |= {f"discussion_common.{x}" for x in de}
        for key, spec in (("discussion", DISC_OBJ), ("bookmark", BOOK_SPEC), ("access_right", ACC_SPEC)):
            if isinstance(dc.get(key), dict):
                si, se = cmp(dc[key], spec)
                iss += [f"{key}.{x}" for x in si]
                pex |= {f"{key}.{x}" for x in se}
        for i, it in enumerate(header_items(b)):
            ii, ie = cmp(it, ITEM_SPEC)
            iss += [f"header[{i}].{x}" for x in ii]
            pex |= {f"header.{x}" for x in ie}
    return iss, sorted(pex)


def check_200(r):
    if r.status != 200:
        return ("FAIL" if r.status >= 500 else "DIFF"), f"status {r.status} {err_shape(r)}"
    if not isinstance(r.body, dict):
        return "DIFF", f"body not object ({type(r.body).__name__})"
    ps = posts_of(r)
    iss, ex = body_issues(r.body)
    ids = [p.get("id") for p in ps]
    dts = [p.get("inserted_at") for p in ps]
    order = ("desc" if ids == sorted(ids, reverse=True) and dts == sorted(dts, reverse=True)
             else "asc" if ids == sorted(ids) and dts == sorted(dts) else "mixed")
    dc = r.body.get("discussion_common")
    note = (f"posts={len(ps)} order={order} users={sorted(users_in(r))} "
            f"common_keys={sorted(dc) if isinstance(dc, dict) else dc} "
            f"presence={len(r.body.get('presence') or [])}")
    if ex:
        note += f"; extra {ex[:8]}"
    if iss:
        return "DIFF", f"schema {iss[:4]}; {note}"
    return "OK", note


def check_user(want):
    def f(r):
        v, note = check_200(r)
        if v != "OK":
            return v, note
        extra = users_in(r) - {want}
        return ("INFO", f"other users in result {sorted(extra)}; {note}") if extra else ("OK", note)
    return f


def check_word(word):
    def f(r):
        v, note = check_200(r)
        if v != "OK":
            return v, note
        miss = [p.get("id") for p in posts_of(r) if word not in plain(p.get("content"))]
        return ("FAIL", f"posts without '{word}': {miss[:3]}; {note}") if miss else ("OK", note)
    return f


def check_rating(v):
    def f(r):
        vv, note = check_200(r)
        if vv != "OK":
            return vv, note
        rs = [p.get("rating") for p in posts_of(r)]
        if v == 0:
            return "INFO", f"rating=0 (semantics undocumented) ratings={rs[:8]}; {note}"
        if not rs:
            return "INFO", f"empty page; {note}"
        bad = [x for x in rs if not isinstance(x, int) or (x < v if v > 0 else x > v)]
        return ("DIFF" if bad else "OK"), f"ratings={rs[:8]} violating(vs {v})={bad[:4]}; {note}"
    return f


def check_reminders(r):
    v, note = check_200(r)
    if v != "OK":
        return v, note
    ps = posts_of(r)
    if not ps:
        return "INFO", f"empty; {note}"
    bad = [p.get("id") for p in ps if p.get("reminder") is not True]
    return ("DIFF" if bad else "OK"), f"non-reminder posts {bad[:3]}; {note}"


def check_dir(desc):
    def f(r):
        v, note = check_200(r)
        if v != "OK":
            return v, note
        ids = ids_of(r)
        good = ids == sorted(ids, reverse=desc)
        return ("OK" if good else "DIFF"), f"{'desc' if desc else 'asc'} by id ok={good}; {note}"
    return f


def check_oldest(r):
    v, note = check_200(r)
    if v != "OK":
        return v, note
    return "INFO", f"oldest page; ids order={ids_of(r)[:4]} (desc within page?); {note}"


def check_range(P, above):
    def f(r):
        v, note = check_200(r)
        if v != "OK":
            return v, note
        ids = ids_of(r)
        if not ids:
            return "INFO", f"empty page around from_id={P}"
        good = all(i > P for i in ids) if above else all(i < P for i in ids)
        return ("OK" if good else "DIFF"), f"ids={ids[:3]} all {'>' if above else '<'} {P}: {good}; {note}"
    return f


def check_lv(L, base):
    def f(r):
        v, note = check_200(r)
        if v != "OK":
            return v, note
        new = lambda b: sum(1 for p in (b.get("posts") or []) if isinstance(p, dict) and p.get("new"))
        same_ids = ids_of(r) == ids_of(base)
        return ("INFO", f"last_visit={L}: same ids as no-param page={same_ids}; "
                        f"new-flags {new(r.body)} vs {new(base.body)}; "
                        f"bookmark.last_seen_post_id {(bmk(r.body) or {}).get('last_seen_post_id')} vs "
                        f"{(bmk(base.body) or {}).get('last_seen_post_id')}; {note}")
    return f


def check_anon(r):
    if r.status == 200:
        return "INFO", f"200 without/with invalid token: undocumented access, posts={len(posts_of(r))}"
    if r.status in (400, 401, 403):
        return "INFO", f"{r.status} {err_shape(r)} (Swagger: 401 not documented)"
    return ("FAIL" if r.status >= 500 else "INFO"), f"status {r.status}"


def neg(what, ok=(400,)):
    """Negative case: documented 400 is OK; other codes are recorded as INFO/DIFF."""
    def f(r):
        if r.status in ok:
            return "OK", f"{r.status} ({what}) {err_shape(r)}"
        if r.status == 200:
            return "INFO", f"200 accepted ({what}); posts={len(posts_of(r))} body={str(r.body)[:60]!r}"
        if r.status == 422:
            return "DIFF", f"422 (Swagger documents 400 only) {err_shape(r)}"
        if r.status == 404:
            return "INFO", f"404 undocumented ({what}) {err_shape(r)}"
        return ("FAIL" if r.status >= 500 or r.status == -1 else "INFO"), f"status {r.status} ({what}) {err_shape(r)}"
    return f


def check_empty(r):
    """Valid request whose Swagger answer is an empty 200 body."""
    if r.status == 200:
        return ("OK" if r.body == {} else "DIFF"), f"200 body={r.body!r}"
    if r.status == 400:
        return "FAIL", f"400 on valid request {err_shape(r)}"
    return ("FAIL" if r.status >= 500 or r.status == -1 else "DIFF"), f"status {r.status} {err_shape(r)}"


def check_literal(r):
    if r.status == 200:
        return "INFO", f"non-boolean literal '1' accepted (200 body={r.body!r}) (Swagger: boolean)"
    if r.status == 400:
        return "OK", f"400 {err_shape(r)}"
    return ("FAIL" if r.status >= 500 or r.status == -1 else "DIFF"), f"status {r.status}"


def check_tags(r):
    if r.status != 200:
        return ("FAIL" if r.status >= 500 or r.status == -1 else "DIFF"), f"status {r.status} {err_shape(r)}"
    if not isinstance(r.body, list):
        return "DIFF", f"not list ({type(r.body).__name__})"
    bad = [x for x in r.body if not (isinstance(x, dict) and not body_bad(x))]
    mine = [x.get("tag") for x in r.body if isinstance(x, dict) and x.get("username") == TEST_USER]
    keys = sorted({k for x in r.body if isinstance(x, dict) for k in x})
    note = f"n={len(r.body)} {TEST_USER} tags={mine} keys={keys}"
    if bad:
        return "DIFF", f"bad items {bad[:2]}; {note}"
    return "OK", note


def body_bad(x):
    iss, _ = cmp(x, TAG_SPEC, ("username", "tag"))
    return bool(iss) or x.get("tag") not in TAGS


def check_rate(action):
    want = {"positive": {"positive"}, "negative": {"negative"},
            "negative_visible": {"negative_visible"}, "remove": {None, "removed"}}[action]

    def f(r):
        if r.status == 200:
            iss, _ = cmp(r.body, POST_SPEC, POST_REQ)
            mine = r.body.get("my_rating") if isinstance(r.body, dict) else None
            rating = r.body.get("rating") if isinstance(r.body, dict) else None
            note = f"my_rating={mine!r} rating={rating!r} want {sorted(map(str, want))}"
            if iss:
                return "DIFF", f"schema {iss[:3]}; {note}"
            return ("OK" if mine in want else "DIFF"), note
        if r.status == 403:
            code = r.body.get("code") if isinstance(r.body, dict) else None
            return ("OK" if code == "NeedsConfirmation" else "DIFF"), f"403 code={code!r} (Swagger: NeedsConfirmation)"
        if r.status == 400:
            return "INFO", f"400 {err_shape(r)}"
        return ("FAIL" if r.status >= 500 or r.status == -1 else "DIFF"), f"status {r.status} {err_shape(r)}"
    return f


def check_bm(want, want_cat="any"):
    """want_cat='any' ignores category_id; otherwise must equal (None = null)."""
    def f(r):
        bk = bmk(r.body)
        if r.status != 200 or not isinstance(bk, dict):
            return "DIFF", f"status {r.status}, bookmark object={bk!r}"
        got, cat = bk.get("bookmark"), bk.get("category_id")
        ok = got == want and (want_cat == "any" or cat == want_cat)
        return ("OK" if ok else "DIFF"), f"bookmark={got} category_id={cat} (want bookmark={want} category={want_cat})"
    return f


def check_hdr(judge):
    def f(r):
        if r.status != 200:
            return "DIFF", f"status {r.status} {err_shape(r)}"
        it = hdr_item(r)
        if it is None:
            return "FAIL", f"item {HEADER_ITEM} not in header"
        cr = it.get("content_raw") or {}
        raw = (cr.get("data") or {}).get("data", "") if isinstance(cr, dict) else str(cr)   # {type, data:{data, format}}
        v, note = judge(raw)
        return v, f"{note}; content_raw={raw!r}"
    return f


def check_rem(want_in, pid):
    def f(r):
        v, note = check_200(r)
        if v != "OK":
            return v, note
        ids = ids_of(r)
        inn = pid in ids
        return ("OK" if inn == want_in else "DIFF"), f"post {pid} in reminders={inn} (want {want_in}) ids={ids[:5]}"
    return f


def check_gone(pid):
    def f(r):
        v, note = check_200(r)
        if v != "OK":
            return v, note
        return ("OK" if pid not in ids_of(r) else "DIFF"), f"post {pid} gone={pid not in ids_of(r)}"
    return f


def call(label, method, path, check, claim, fix=None, **kw):
    t = tid()
    r = C(method, path, test_id=t, claim=f"{claim}; {label}", **kw)
    v, note = ("FAIL", f"server error {r.status}") if r.status >= 500 else check(r)
    emit(t, r.status, v, f"{label}: {note}", r)
    if fix and r.status == 200:
        FIX.setdefault(fix, r.body)
    return r


def find_own(pid):
    r = C("GET", DP, params={"user": TEST_USER, "order": "newest"})
    return next((p for p in posts_of(r) if p.get("id") == pid), None)


# ---------------------------------------------------------------- A. reads (GET discussion)
def get_disc(label, params, check, claim="", disc=DISC, **kw):
    return call(label, "GET", f"/discussion/{disc}", check, GET_CLAIM + ("; " + claim if claim else ""),
                params=params or None, **kw)


base = get_disc("A no params", None, check_200, "no params: shape, page size, order, discussion_common",
                fix="discussion_get_200")
base_ids = ids_of(base)
words = [w for p in posts_of(base) for w in re.findall(r"[^\W\d_]{4,}", plain(p.get("content")))]
word = words[0] if words else "test"
P = sorted(base_ids)[len(base_ids) // 2] if len(base_ids) >= 2 else None

r_me = get_disc(f"A user={TEST_USER}", {"user": TEST_USER}, check_user(TEST_USER), "user Username")
r_peer = get_disc(f"A user={PEER_USER}", {"user": PEER_USER}, check_user(PEER_USER), "user Username")
get_disc(f"A user={PEER_USER.lower()}", {"user": PEER_USER.lower()},
         lambda r: ("OK", f"400 for lowercase ({err_shape(r)})") if r.status == 400
         else ("INFO", f"status {r.status}; ids identical to user={PEER_USER}: {ids_of(r) == ids_of(r_peer)}"),
         "Username pattern [A-Z0-9_]{3,15} (uppercase); lowercase case")
get_disc(f"A text={word}", {"text": word}, check_word(word), "text SearchExpression")
for v in (1, -1, 0):
    get_disc(f"A rating={v}", {"rating": v}, check_rating(v), "rating integer")
get_disc("A reminders=true", {"reminders": "true"}, check_reminders, "reminders boolean")
get_disc("A order=newest", {"order": "newest"}, check_dir(True), "order=newest")
get_disc("A order=oldest", {"order": "oldest"}, check_oldest, "order=oldest")
if P is not None:
    get_disc(f"A order=newer_than from_id={P}", {"order": "newer_than", "from_id": P},
             check_range(P, True), "newer_than with from_id")
    get_disc(f"A order=older_than from_id={P}", {"order": "older_than", "from_id": P},
             check_range(P, False), "older_than with from_id")
    get_disc(f"A last_visit={P} (no order)", {"last_visit": P}, check_lv(P, base),
             "last_visit override: compare with no-param page")
else:
    emit(tid(), "-", "INFO", "fewer than 2 posts: from_id/last_visit range cases skipped")
get_disc("A order=newer_than (no from_id)", {"order": "newer_than"}, neg("from_id required"),
         "newer_than requires from_id")
get_disc("A order=older_than (no from_id)", {"order": "older_than"}, neg("from_id required"),
         "older_than requires from_id")
get_disc("A from_id=0", {"order": "newest", "from_id": 0}, neg("from_id>=1"), "from_id minimum 1")
get_disc("A from_id=abc", {"order": "newest", "from_id": "abc"}, neg("from_id integer"), "from_id integer")
get_disc("A order=foo", {"order": "foo"}, neg("order enum"), "order enum")
get_disc(f"A foreign discussion {PUBLIC_DISC}", None, check_200, "foreign public discussion (read only)",
         disc=PUBLIC_DISC, fix="discussion_get_foreign_200")
get_disc("A discussion 999999999", None, neg("discussion 999999999"), "non-existent discussion")
get_disc("A discussion abc", None, neg("discussion id not integer"), "non-integer discussion id", disc="abc")
get_disc("A no token", None, check_anon, "undocumented: no bearer token", auth=False)
get_disc("A invalid token", None, check_anon, "undocumented: invalid bearer token", auth="invalidtoken123")

# ---------------------------------------------------------------- B. sends (own posts only)


def snapshot():
    r = C("GET", DP, params={"order": "newest"})
    return set(ids_of(r)) if r.status == 200 else None


def new_own(before, n):
    """Posts by the test user that were not on the page before the send. Without nonce only empty posts newer than all seen."""
    r = C("GET", DP, params={"order": "newest"})
    if r.status != 200:
        return None
    out = []
    for p in posts_of(r):
        if p.get("username") != TEST_USER or p.get("id") in before:
            continue
        content = p.get("content") or ""
        if n is not None and n in content:
            out.append(p)
        elif n is None and not content.strip() and p.get("id", 0) > max(before, default=0):
            out.append(p)
    return out


def do_send(label, content, fmt, n, mode):
    """mode: send (200 expected) | reject (400 expected) | enum (markdown: 400 expected) | dup | long"""
    before = snapshot()
    if before is None:
        emit(tid(), "-", "FAIL", f"{label}: pre-send snapshot failed; send skipped")
        return None
    data = {"content": content}
    if fmt is not None:
        data["format"] = fmt
    t = tid()
    r = C("POST", f"{DP}/send/text", data=data, test_id=t, claim=f"{SEND_CLAIM}; case {label}")
    if r.status == 200:
        found = new_own(before, n)
        if found is None:
            emit(t, 200, "FAIL", f"{label}: 200 but post lookup failed")
            return None
        for p in found:
            c.created.append(("post", p["id"]))
            CREATED.append(p["id"])
            ALIVE.append(p["id"])
        if not found:
            emit(t, 200, "INFO" if mode in ("reject", "dup") else "FAIL",
                 f"{label}: 200 body={r.body!r}; no new own post found")
            return None
        p = found[0]
        stored = p.get("content") or ""
        same = stored == content
        note = (f"body={r.body!r} (send response carries no post id) new_ids={[x['id'] for x in found]} "
                f"content_raw={p.get('content_raw')!r} stored==sent:{same} len sent={len(content)} "
                f"stored={len(stored)} stored_head={stored[:50]!r}")
        if r.body != {}:
            v = "DIFF"
        elif mode == "enum":
            v = "DIFF"          # Swagger ContentFormatEnum is text|html only
        elif mode == "send":
            v = "OK" if same and len(found) == 1 else "INFO"
        else:
            v = "INFO"
        emit(t, 200, v, f"{label}: {note}", r)
        SENT[label] = p["id"]
        return p["id"]
    if r.status == 400:
        v = "OK" if mode in ("reject", "enum") else ("FAIL" if mode == "send" else "INFO")
        emit(t, 400, v, f"{label}: 400 {err_shape(r)}", r)
        return None
    emit(t, r.status, "FAIL" if r.status >= 500 or r.status == -1 else "INFO",
         f"{label}: status {r.status} {err_shape(r)}", r)
    return None


n1, n2, n3, n4, n6, n7 = (nonce() for _ in range(6))
long_txt = f"{n7} " + ("lorem ipsum dolor sit amet " * 800)[:20000 - len(n7) - 1]
try:
    do_send("format=text", f"line1\nline2 <b>x</b> {n1}", "text", n1, "send")
    do_send("format=html", f"<b>bold</b>\nline2 {n2}", "html", n2, "send")
    do_send("format=markdown", f"**bold** {n3}", "markdown", n3, "enum")
    do_send("no format", f"noformat {n4}", None, n4, "send")
    do_send("empty content", "", None, None, "reject")
    do_send("duplicate #1", f"dup {n6}", None, n6, "send")
    do_send("duplicate #2 (same text)", f"dup {n6}", None, n6, "dup")
    do_send(f"long text ({len(long_txt)} chars)", long_txt, None, n7, "long")

    own = SENT.get("format=text") or SENT.get("no format")

    # -------------------------------------------------------- C. edit own post (contentId = post id assumed)
    if own:
        n5 = nonce()
        t = tid()
        r = C("POST", f"{DP}/content/{own}/save", data={"content": f"<b>edited</b> {n5}", "format": "html"},
              test_id=t, claim=f"{SAVE_CLAIM}; own post {own} used as contentId")
        p = find_own(own)
        reflected = bool(p) and n5 in (p.get("content") or "")
        v = ("OK" if reflected and r.body == {} else "DIFF") if r.status == 200 else "INFO"
        emit(t, r.status, v, f"C edit own post {own}: reflected={reflected} "
                             f"content_raw={(p or {}).get('content_raw')!r} body={r.body!r} {err_shape(r) if r.status != 200 else ''}", r)
    call("C save contentId 999999999", "POST", f"{DP}/content/999999999/save", neg("contentId 999999999"),
         SAVE_CLAIM, data={"content": f"x {nonce()}", "format": "html"})

    # -------------------------------------------------------- D. rating
    if own:
        call("D GET rating own", "GET", f"{RG}/{own}", check_tags, RATEGET_CLAIM, fix="rating_get_200")
    call(f"D GET rating {PEER_USER} post {PEER_POST}", "GET", f"{RG}/{PEER_POST}", check_tags, RATEGET_CLAIM)

    def rate_cycle(label, pid):
        for action in ("positive", "negative", "negative_visible", "remove"):
            if action != "remove":
                DIRTY.add(pid)
            r = call(f"D {label} POST {action}", "POST", f"{RG}/{pid}/{action}", check_rate(action),
                     RATE_CLAIM, fix="rating_post_200")
            call(f"D {label} GET rating after {action}", "GET", f"{RG}/{pid}", check_tags, RATEGET_CLAIM)
            if action == "remove" and r.status == 200:
                DIRTY.discard(pid)

    if own:
        rate_cycle("own", own)
        call("D POST action=foo (own)", "POST", f"{RG}/{own}/foo", neg("action foo"), RATE_CLAIM)
    rate_cycle(f"{PEER_USER} {PEER_POST}", PEER_POST)
    call("D POST rating id 999999999 positive", "POST", f"{RG}/999999999/positive", neg("rating id 999999999"),
         RATE_CLAIM)
    call("D GET rating id 999999999", "GET", f"{RG}/999999999", neg("rating id 999999999 GET"), RATEGET_CLAIM)

    # -------------------------------------------------------- E. reminder (own post only)
    if own:
        call("E POST newState=true", "POST", f"{RM}/{own}/true", check_empty, REM_CLAIM)
        call("E GET ?reminders=true after true", "GET", DP, check_rem(True, own), GET_CLAIM,
             params={"reminders": "true"})
        call("E POST newState=false", "POST", f"{RM}/{own}/false", check_empty, REM_CLAIM)
        call("E GET ?reminders=true after false", "GET", DP, check_rem(False, own), GET_CLAIM,
             params={"reminders": "true"})
        call("E POST newState=1", "POST", f"{RM}/{own}/1", check_literal, REM_CLAIM)
        call("E POST newState=false (restore after '1')", "POST", f"{RM}/{own}/false", check_empty, REM_CLAIM)
        call("E GET ?reminders=true after restore", "GET", DP, check_rem(False, own), GET_CLAIM,
             params={"reminders": "true"})
        call("E POST newState=abc", "POST", f"{RM}/{own}/abc", neg("newState abc"), REM_CLAIM)
    call("E POST id=0", "POST", f"{RM}/0/true", neg("id 0"), REM_CLAIM)
    call("E POST id=abc", "POST", f"{RM}/abc/true", neg("id abc"), REM_CLAIM)
    call("E POST id=999999999", "POST", f"{RM}/999999999/true", neg("id 999999999"), REM_CLAIM)

    # -------------------------------------------------------- F. bookmark (restore: bookmark=true, category null)
    def bm_verify(label, want, want_cat="any"):
        return call(f"{label} [verify]", "GET", DP, check_bm(want, want_cat),
                    "GET /discussion/{id} discussion_common.bookmark state")

    bm_verify("F initial state (expected bookmark=true, category null)", True, None)
    try:
        call("F POST new_state=false", "POST", BMP, check_empty, BM_CLAIM, params={"new_state": "false"})
        bm_verify("F after POST false", False)
        call("F POST new_state=true", "POST", BMP, check_empty, BM_CLAIM, params={"new_state": "true"})
        bm_verify("F after POST true", True)
        call("F GET new_state=false", "GET", BMP, check_empty, BM_CLAIM, params={"new_state": "false"})
        bm_verify("F after GET false", False)
        call("F GET new_state=true", "GET", BMP, check_empty, BM_CLAIM, params={"new_state": "true"})
        bm_verify("F after GET true", True)
        cr = call("F GET /bookmarks/all (category ids)", "GET", "/bookmarks/all",
                  lambda r: ("OK" if r.status == 200 else "DIFF", f"status {r.status}"),
                  "GET /bookmarks/all (categories for the category case)")
        cats = []

        def find_cats(o):
            if isinstance(o, dict):
                if isinstance(o.get("id"), int) and "category_name" in o:
                    cats.append(o["id"])
                for v in o.values():
                    find_cats(v)
            elif isinstance(o, list):
                for v in o:
                    find_cats(v)
        if cr.status == 200:
            find_cats(cr.body)
        if cats:
            call(f"F POST new_state=true category={cats[0]}", "POST", BMP, check_empty, BM_CLAIM,
                 params={"new_state": "true", "category": str(cats[0])})
            bm_verify(f"F after category={cats[0]}", True, cats[0])
        else:
            emit(tid(), "-", "INFO", "F category: no bookmark category ids returned; case skipped")
        call("F POST new_state=abc", "POST", BMP, neg("new_state abc"), BM_CLAIM, params={"new_state": "abc"})
    finally:
        call("F RESTORE POST new_state=true (no category)", "POST", BMP, check_empty, BM_CLAIM,
             params={"new_state": "true"})
        bm_verify("F restored: expect bookmark=true, category null", True, None)

    # -------------------------------------------------------- G. header item the header item (save + restore)
    item0 = hdr_item(base)
    if item0 is None:
        emit(tid(), "-", "INFO", f"G header item {HEADER_ITEM} not in discussion header: save skipped")
    else:
        orig = item0.get("content_raw")
        HEADER_ORIG = ((orig or {}).get("data") or {}).get("data") or ""
        hn = nonce()
        try:
            call(f"G save header {HEADER_ITEM} (text + nonce)", "POST", f"{DP}/content/{HEADER_ITEM}/save",
                 check_empty, SAVE_CLAIM, data={"content": f"{HEADER_ORIG} {hn}", "format": "html"})
            call("G readback after save", "GET", DP,
                 check_hdr(lambda s: ("OK", "nonce present") if hn in s else ("DIFF", "nonce missing")),
                 GET_CLAIM)
        finally:
            call(f"G RESTORE header {HEADER_ITEM}", "POST", f"{DP}/content/{HEADER_ITEM}/save", check_empty, SAVE_CLAIM,
                 data={"content": HEADER_ORIG, "format": "html"})
            call("G readback after restore", "GET", DP,
                 check_hdr(lambda s: ("OK" if s == HEADER_ORIG else "DIFF",
                                      f"restored text == brief text: {s == HEADER_ORIG}; "
                                      f"byte-equal to original raw {orig!r}: {s == orig}")),
                 GET_CLAIM)

    # -------------------------------------------------------- H. delete (own only)
    victim = SENT.get("no format")
    if victim:
        call(f"H DELETE own post {victim}", "DELETE", f"{DP}/delete/{victim}", check_empty, DEL_CLAIM)
        r = call(f"H verify {victim} gone", "GET", DP, check_gone(victim), GET_CLAIM,
                 params={"user": TEST_USER, "order": "newest"})
        if r.status == 200 and victim not in ids_of(r) and victim in ALIVE:
            ALIVE.remove(victim)
            DELETED.append(victim)
        call(f"H DELETE {victim} again (already deleted)", "DELETE", f"{DP}/delete/{victim}",
             neg("already deleted", ok=(400,)), DEL_CLAIM)
    t = tid()
    try:
        C("DELETE", f"{DP}/delete/999999999", test_id=t, claim=f"{DEL_CLAIM}; H delete 999999999")
        emit(t, "-", "FAIL", "H delete 999999999: request was sent (guard not active?)")
    except Forbidden as e:
        emit(t, "-", "INFO", f"H delete 999999999: not testable, guard Forbidden ({e})")

finally:
    # cleanup: only posts registered in this run; never the peer user's post
    for pid in sorted(DIRTY):
        call(f"CLEANUP remove rating {pid}", "POST", f"{RG}/{pid}/remove", check_rate("remove"), RATE_CLAIM)
    for pid in list(ALIVE):
        r = call(f"CLEANUP delete own post {pid}", "DELETE", f"{DP}/delete/{pid}", check_empty, DEL_CLAIM)
        if r.status == 200:
            ALIVE.remove(pid)
            DELETED.append(pid)

# ---------------------------------------------------------------- final state
fin = call("FINAL state GET", "GET", DP, check_200, GET_CLAIM)
print("final bookmark:", bmk(fin.body), f"| final header {HEADER_ITEM} content_raw:",
      (hdr_item(fin) or {}).get("content_raw"))
print("created own post ids:", CREATED)
print("deleted:", DELETED, "| still alive (should be empty):", ALIVE)
print("counts:", dict(Counter(v for _, _, v, _, _ in rows)))

# ---------------------------------------------------------------- fixtures
for name, body in FIX.items():
    save_fixture(SEG, name, body)
seen = set()
for _, _, _, _, r in rows:
    if r is None or r.status < 400:
        continue
    key = (r.status, tuple(sorted(r.body)) if isinstance(r.body, dict) else type(r.body).__name__)
    if key in seen:
        continue
    seen.add(key)
    save_fixture(SEG, f"err_{r.status}_{len(seen)}", r.body)
print("fixtures: see tests/fixtures/discussion/")
