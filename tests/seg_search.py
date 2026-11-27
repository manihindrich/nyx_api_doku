"""Live GET-only tests for segment `search` (Swagger 0.0.1). Writes nothing."""
import re
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from http.client import IncompleteRead  # noqa: E402
from nyx import Client, Result, save_fixture, shape  # noqa: E402
from nyx import TEST_USER, TEST_DISC  # noqa: E402

SEG = "search"
c = Client(SEG)


def C(*a, **k):
    """Transport errors (urllib saw a truncated body) become status -1 -> FAIL; harness is not changed."""
    try:
        return c.call(*a, **k)
    except (IncompleteRead, OSError) as e:
        return Result(-1, f"transport: {type(e).__name__}: {e}"[:200], {}, 0)
rows = []   # (tid, status, verdict, note, Result|None)
_n = [0]
USER_RE = r"[A-Z0-9_]{3,15}"    # Username (/search, /search-v2)
PREFIX_RE = r"[A-Z0-9_]{2,15}"  # path param of /search/username


def tid():
    _n[0] += 1
    return f"T-{SEG}-{_n[0]:02d}"


def emit(t, status, verdict, note, res=None):
    if res is not None and res.status == -1:
        verdict = "FAIL"
    rows.append((t, status, verdict, note, res))
    print(f"{t} | {status} | {verdict} | {note}")


def type_ok(v, t):
    if t == "any":
        return True
    if t == "int":
        return isinstance(v, int) and not isinstance(v, bool)
    if t == "int?":
        return v is None or type_ok(v, "int")
    if t == "str":
        return isinstance(v, str)
    if t == "str?":
        return v is None or isinstance(v, str)
    if t == "dict?":
        return v is None or isinstance(v, dict)
    if t == "bool":
        return isinstance(v, bool)
    if t == "dt":
        return isinstance(v, str) and re.match(r"\d{4}-\d{2}-\d{2}T", v) is not None
    if t == "dict":
        return isinstance(v, dict)
    if t == "list":
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


# Swagger schemas (TemplatePost = DiscussionPostWithName + allOf extras)
POST = {"id": "int", "discussion_id": "int", "username": "str", "content": "str?", "content_raw": "any",
        "post_type": "any", "reminder": "bool", "rating": "int", "my_rating": "any", "replies": "list",
        "inserted_at": "dt", "activity": "dict?", "new": "bool", "preview": "bool", "can_be_deleted": "bool",
        "can_be_rated": "bool", "can_be_reminded": "bool", "can_ignore_discussion": "bool",
        "rating_friends": "list"}
POST_REQ = ("id", "discussion_id", "username", "content", "inserted_at")
CONTEXT = {"user": "dict", "active_friends": "list"}
UNAME_RES = {"exact": "list", "friends": "list", "others": "list"}
UNAME_ROW = {"user": "dict", "activity": "dict?"}
UN_USER = {"username": "str"}
UNI_DISC = {"discussions": "list", "events": "list", "advertisements": "list"}
UNI_DISC_ROW = {"id": "int", "discussion_type": "str", "discussion_name": "str",
                "discussion_name_highlighted": "str", "summary": "str?", "summary_highlighted": "str?"}
UNI_POST_ROW = {"discussion_id": "int", "post_id": "int", "discussion_name": "str",
                "discussion_name_highlighted": "str", "content": "str"}
JSON_ERR = {"error": "bool", "code": "str", "message": "str"}


def msg(r):
    return r.body.get("message") if isinstance(r.body, dict) else str(r.body)[:80]


def posts_of(r):
    if r.status == 200 and isinstance(r.body, dict) and isinstance(r.body.get("posts"), list):
        return [p for p in r.body["posts"] if isinstance(p, dict)]
    return []


def top_issues(b):
    """/search and /search-v2: {context, posts[TemplatePost]}."""
    iss, extra = cmp(b, {"context": "dict", "posts": "list"}, ("context", "posts"))
    if not isinstance(b, dict):
        return iss, []
    if isinstance(b.get("context"), dict):
        iss += [f"context.{x}" for x in cmp(b["context"], CONTEXT, ("user", "active_friends"))[0]]
    pex = set()
    for i, p in enumerate(b.get("posts") if isinstance(b.get("posts"), list) else []):
        pi, pe = cmp(p, POST, POST_REQ)
        iss += [f"posts[{i}].{x}" for x in pi]
        pex |= set(pe)
    return iss, sorted(pex)


def row_name(row):
    """Swagger: row.user.username; observed: row.username (flat)."""
    return row.get("username") or (row.get("user") or {}).get("username") or ""


def unwrap(b):
    """Unified 200 is wrapped under one key ({"discussion": {...}}); return (key, inner)."""
    if isinstance(b, dict) and len(b) == 1 and isinstance(next(iter(b.values())), (dict, list)):
        k, v = next(iter(b.items()))
        return k, v
    return None, b


def username_issues(b):
    iss, _ = cmp(b, UNAME_RES)
    if not isinstance(b, dict):
        return iss
    for g in ("exact", "friends", "others"):
        for i, row in enumerate(b.get(g) if isinstance(b.get(g), list) else []):
            iss += [f"{g}[{i}].{x}" for x in cmp(row, UNAME_ROW, ("user",))[0]]
            if isinstance(row, dict) and isinstance(row.get("user"), dict):
                iss += [f"{g}[{i}].user.{x}" for x in cmp(row["user"], UN_USER, ("username",))[0]]
    return iss


def ukind(b):
    if isinstance(b, list):
        return "posts"
    if isinstance(b, dict) and "exact" in b:
        return "username"
    if isinstance(b, dict) and "discussions" in b:
        return "discussion"
    return "other"


def unified_issues(b):
    k = ukind(b)  # b is already unwrapped
    if k == "posts":
        return [f"[{i}] {x}" for i, it in enumerate(b) for x in cmp(it, UNI_POST_ROW, tuple(UNI_POST_ROW))[0]]
    if k == "username":
        return username_issues(b)
    if k == "discussion":
        iss, _ = cmp(b, UNI_DISC)
        for g in ("discussions", "events", "advertisements"):
            for i, it in enumerate(b.get(g) if isinstance(b.get(g), list) else []):
                iss += [f"{g}[{i}].{x}" for x in cmp(it, UNI_DISC_ROW, ("id", "discussion_name"))[0]]
        return iss
    return [f"body is {type(b).__name__}, no oneOf branch matches"]


def group_sizes(b):
    if isinstance(b, list):
        return {"posts": len(b)}
    if isinstance(b, dict):
        return {k: len(v) for k, v in b.items() if isinstance(v, list)}
    return {}


def match_issues(p, user, words):
    out = []
    if user and str(p.get("username") or "").upper() != user.upper():
        out.append(f"author {p.get('username')}")
    txt = re.sub(r"<[^>]+>", "", p.get("content") or "").replace("&amp;", "&").lower()
    out += [f"no '{w}'" for w in words if w not in txt]
    return out


# ---------------------------------------------------------------- username (path)
def eval_un(u, what, r):
    valid = re.fullmatch(PREFIX_RE, u) is not None
    if r.status == 200:
        b = r.body if isinstance(r.body, dict) else {}
        sizes = {g: len(b.get(g) or []) for g in ("exact", "friends", "others")}
        rws = [row for g in ("exact", "friends", "others") for row in (b.get(g) or []) if isinstance(row, dict)]
        bad = [row for row in rws if not str(row_name(row)).upper().startswith(u.upper())]
        note = f"{sizes}"
        if not valid:
            return "INFO", f"200 for input outside pattern ({what}); {note}"
        iss = username_issues(r.body)
        if iss:
            return "DIFF", f"schema {iss[:3]}; {note}"
        if bad:
            return "FAIL", f"{len(bad)} rows do not start with prefix; {note}"
        return "OK", note
    if r.status == 400:
        iss, _ = cmp(r.body, JSON_ERR, ("error", "message"))
        note = f"400 msg={msg(r)!r}" + (f"; JsonError {iss}" if iss else "")
        return ("OK" if not valid else "DIFF"), (f"400 for input outside pattern ({what}); " if not valid
                                                  else "400 for pattern-valid input; ") + note
    if r.status >= 500:
        return "FAIL", f"server error {r.status}"
    return "DIFF", f"status {r.status} (Swagger documents only 200/400)"


UN_CASES = [(TEST_USER, "exact"), (TEST_USER.lower(), "lowercase"), (TEST_USER[:3], "prefix"), (TEST_USER[:2], "2 chars"),
            ("N", "1 char"), ("A" * 15, "15 chars"), ("A" * 16, "16 chars"), ("XQZJWQ_NOPE", "no match"),
            ("a-b", "hyphen"), ("ž", "non-ascii"), ("", "empty")]
UN_CLAIM = ("GET /search/username/{username} 200 UsernameSearchResult {exact,friends,others}; "
            "username [A-Z0-9_]{2,15}; 400 JsonError")
un_fixture = None
for u, what in UN_CASES:
    t = tid()
    r = C("GET", f"/search/username/{urllib.parse.quote(u, safe='')}", test_id=t,
               claim=f"{UN_CLAIM}; case {what}")
    if u == TEST_USER:
        un_fixture = r
    v, note = eval_un(u, what, r)
    emit(t, r.status, v, f"{what}: {note}", r)

# ---------------------------------------------------------------- /search, /search-v2 text/user matrix
SEARCH_CLAIM = {
    "/search": "GET /search (deprecated) 200 {context, posts[TemplatePost]} required; user Username [A-Z0-9_]{3,15}; "
               "text SearchExpression",
    "/search-v2": "GET /search-v2 200 {context, posts[TemplatePost]} required; user Username [A-Z0-9_]{3,15}; "
                  "text SearchExpression; order/from_id",
}
CASES = [  # (label, params, expected author, words that must occur in content)
    ("text=test", {"text": "test"}, None, ["test"]),
    (f"user={TEST_USER}", {"user": TEST_USER}, TEST_USER, []),
    ("user+text", {"user": TEST_USER, "text": "test"}, TEST_USER, ["test"]),
    ("none", {}, None, []),
    ("=test", {"text": "=test"}, None, ["test"]),
    ("phrase", {"text": '"testing NYX"'}, None, ["testing nyx"]),
    (f"@{TEST_USER}", {"text": f"@{TEST_USER}"}, TEST_USER, []),
    ("combo", {"text": f"@{TEST_USER} test"}, TEST_USER, ["test"]),
    (f"user={TEST_USER.lower()}", {"user": TEST_USER.lower()}, TEST_USER, []),
    ("user=NY", {"user": TEST_USER[:2]}, TEST_USER[:2], []),
]


def eval_search(label, params, user, words, r):
    uvalid = params.get("user") is None or re.fullmatch(USER_RE, params["user"]) is not None
    if r.status >= 500:
        return "FAIL", f"server error {r.status}", []
    if r.status == 400:
        iss, _ = cmp(r.body, JSON_ERR, ("error", "message"))
        note = f"400 msg={msg(r)!r}" + (f"; JsonError {iss}" if iss else "")
        if label == "none":
            return "INFO", "400 without params (Swagger silent): " + note, []
        if not uvalid:
            return "OK", "400 for username outside pattern; " + note, []
        return "DIFF", "400 for valid query; " + note, []
    if r.status != 200:
        return "DIFF", f"status {r.status}", []
    iss, extra = top_issues(r.body)
    posts = posts_of(r)
    ids = [p.get("id") for p in posts]
    mism = [(p.get("id"), m) for p in posts for m in [match_issues(p, user, words)] if m]
    note = f"posts={len(posts)} ids={ids[:4]} mismatch={len(mism)}"
    if extra:
        note += f"; extra post fields {extra}"
    if mism:
        note += f"; e.g. {mism[0]}"
    if iss:
        return "DIFF", f"schema {iss[:3]}; " + note, posts
    if label == "none":
        return "INFO", "200 without params: " + note, posts
    if not uvalid:
        return "INFO", "200 for username outside pattern; " + note, posts
    if mism:
        return "FAIL", "results do not match query; " + note, posts
    return "OK", note, posts


got = {}
for ep in ("/search", "/search-v2"):
    for label, params, user, words in CASES:
        t = tid()
        r = C("GET", ep, params=params, test_id=t, claim=f"{SEARCH_CLAIM[ep]}; case {label}")
        v, note, posts = eval_search(label, params, user, words, r)
        got[(ep, label)] = (r, [p.get("id") for p in posts])
        emit(t, r.status, v, f"{ep} {label}: {note}", r)

for label, *_ in CASES:
    t = tid()
    ra, ida = got[("/search", label)]
    rb, idb = got[("/search-v2", label)]
    same = ra.status == rb.status and ida == idb
    emit(t, rb.status, "OK" if same else "DIFF",
         f"{label}: /search {ra.status} n={len(ida)} vs /search-v2 {rb.status} n={len(idb)}; identical={same}")

# ---------------------------------------------------------------- search-v2 order / from_id
def expect_400(r, what):
    if r.status == 400:
        return "OK", f"400 as expected ({what})"
    if r.status == 200:
        return "DIFF", f"200 accepted, posts={len(posts_of(r))}"
    return "FAIL", f"status {r.status}"


def order_call(params, claim, check):
    t = tid()
    r = C("GET", "/search-v2", params={"text": "test", **params}, test_id=t, claim=claim)
    v, note = check(r)
    emit(t, r.status, v, f"{params}: {note}", r)
    return r


ORD_CLAIM = ("GET /search-v2 order enum newest|newer_than|older_than|oldest; newer_than/older_than "
             "require from_id; from_id integer >=1")


def sorted_check(desc):
    def f(r):
        ps = posts_of(r)
        if r.status != 200:
            return "FAIL", f"status {r.status}"
        ids = [p["id"] for p in ps]
        ts = [p.get("inserted_at") for p in ps]
        ok = ids == sorted(ids, reverse=desc) and ts == sorted(ts, reverse=desc)
        return ("OK" if ok else "DIFF"), f"posts={len(ps)} ids={ids[:3]} id+time order ok={ok}"
    return f


def range_check(P, above):
    def f(r):
        ps = posts_of(r)
        if r.status != 200:
            return "FAIL", f"status {r.status}"
        ids = [p["id"] for p in ps]
        if not ids:
            return "DIFF", f"empty page around from_id={P}"
        ok = all(i > P for i in ids) if above else all(i < P for i in ids)
        direction = "asc" if ids == sorted(ids) else ("desc" if ids == sorted(ids, reverse=True) else "mixed")
        return ("OK" if ok else "DIFF"), f"posts={len(ps)} ids={ids[:3]} all {'>' if above else '<'} {P}: {ok}; order={direction}"
    return f


newest_r = order_call({"order": "newest"}, ORD_CLAIM + "; order=newest", sorted_check(True))
new_posts = posts_of(newest_r)
P = new_posts[len(new_posts) // 2]["id"] if len(new_posts) >= 2 else None
order_call({"order": "oldest"}, ORD_CLAIM + "; order=oldest",
           lambda r: (lambda ps: ("INFO", f"posts={len(ps)} ids={[p['id'] for p in ps[:3]]} "
                                  f"time range {ps[-1]['inserted_at'][:10]}..{ps[0]['inserted_at'][:10]}; "
                                  f"within page desc={[p['inserted_at'] for p in ps] == sorted((p['inserted_at'] for p in ps), reverse=True)}"))(posts_of(r)))
order_call({"order": "newer_than"}, ORD_CLAIM + "; newer_than without from_id", lambda r: expect_400(r, "from_id required"))
order_call({"order": "older_than"}, ORD_CLAIM + "; older_than without from_id", lambda r: expect_400(r, "from_id required"))
if P is not None:
    order_call({"order": "newer_than", "from_id": P}, ORD_CLAIM + "; newer_than with from_id", range_check(P, True))
    order_call({"order": "older_than", "from_id": P}, ORD_CLAIM + "; older_than with from_id", range_check(P, False))
    order_call({"from_id": P}, ORD_CLAIM + "; from_id without order",
               lambda r: ("INFO", f"status {r.status}, posts={len(posts_of(r))}"))
    order_call({"order": "newest", "from_id": P}, ORD_CLAIM + "; newest with from_id",
               lambda r: ("INFO", f"status {r.status}, same ids as plain newest={[p['id'] for p in posts_of(r)] == [p['id'] for p in new_posts]}"))
else:
    emit(f"T-{SEG}-{_n[0] + 1:02d}", "-", "INFO", "newest page <2 posts: from_id cases skipped")
    _n[0] += 1
order_call({"order": "newest", "from_id": 0}, ORD_CLAIM + "; from_id=0 (minimum 1)", lambda r: expect_400(r, "from_id>=1"))
order_call({"order": "newest", "from_id": -1}, ORD_CLAIM + "; from_id=-1", lambda r: expect_400(r, "from_id>=1"))
order_call({"order": "newest", "from_id": "abc"}, ORD_CLAIM + "; from_id non-integer", lambda r: expect_400(r, "integer"))
order_call({"order": "foo"}, ORD_CLAIM + "; order not in enum", lambda r: expect_400(r, "enum"))
order_call({"order": "NEWEST"}, ORD_CLAIM + "; order case",
           lambda r: ("OK", "400 (enum is case-sensitive)") if r.status == 400
           else ("INFO", f"200, case-insensitive order, posts={len(posts_of(r))}"))

# ---------------------------------------------------------------- unified
UNI_CLAIM = ("GET /search/unified 200 oneOf UsernameSearchResult|UnifiedSearchDiscussionResult|"
             "UnifiedSearchDiscussionPostResult; search SearchExpression required; limit integer default 5")
UNI_CASES = [  # (label, search or None, limit param or None, effective limit)
    (TEST_USER, TEST_USER, None, 5), ("testing", "testing", None, 5), (f"{TEST_DISC}", f"{TEST_DISC}", None, 5),
    (f"@{TEST_USER}", f"@{TEST_USER}", None, 5), ("limit=1", "testing", 1, 1), ("limit=5", "testing", 5, 5),
    ("limit=20", "testing", 20, 20), ("limit=0", "testing", 0, 0), ("limit=-1", "testing", -1, -1),
    ("limit=abc", "testing", "abc", None), ("missing search", None, 5, None),
    ("@NY (swagger example)", "@NY", None, 5), (f"@{TEST_USER} test (swagger example)", f"@{TEST_USER} test", None, 5)]
uni_fixtures = {}
for label, search, limit, eff in UNI_CASES:
    params = {}
    if search is not None:
        params["search"] = search
    if limit is not None:
        params["limit"] = limit
    t = tid()
    r = C("GET", "/search/unified", params=params, test_id=t, claim=f"{UNI_CLAIM}; case {label}")
    if r.status >= 500:
        v, note = "FAIL", f"server error {r.status}"
    elif search is None or limit == "abc":
        if r.status == 400:
            v, note = "OK", "400 as expected"
        else:
            wk, inner = unwrap(r.body)
            v, note = "DIFF", (f"status {r.status} (Swagger: 400 JsonError)" if search is None
                               else f"status {r.status}: non-integer limit accepted; kind={ukind(inner)} "
                                    f"sizes={group_sizes(inner)}")
    elif r.status == 400:
        iss, _ = cmp(r.body, JSON_ERR, ("error", "message"))
        if eff is not None and eff <= 0:
            v, note = "INFO", f"400 for limit={limit}: msg={msg(r)!r}"
        else:
            v, note = "DIFF", f"400 for valid query: msg={msg(r)!r}"
    elif r.status == 200:
        wk, inner = unwrap(r.body)
        kind = ukind(inner)
        iss = unified_issues(inner)
        sizes = group_sizes(inner)
        uni_fixtures.setdefault(kind, r)
        note = f"wrapper={wk} kind={kind} sizes={sizes}"
        if iss:
            v, note = "DIFF", f"schema {iss[:3]}; {note}"
        elif eff is not None and eff <= 0:
            v, note = "INFO", f"limit={limit} accepted; {note}"
        elif eff is not None and max(sizes.values() or [0]) > eff:
            v, note = "DIFF", f"group larger than limit {eff}; {note}"
        else:
            v = "OK"
        if eff is None and label.startswith("limit"):
            note += " (default limit 5 assumed)"
    else:
        v, note = "DIFF", f"status {r.status}"
    emit(t, r.status, v, f"{label}: {note}", r)

# ---------------------------------------------------------------- auth (on /search-v2)
for label, auth in (("no token", False), ("invalid token", "invalidtoken123")):
    t = tid()
    r = C("GET", "/search-v2", params={"text": "test"}, auth=auth, test_id=t,
               claim="undocumented: GET /search-v2 without / with invalid bearer token (Swagger lists no 401)")
    if r.status == 200:
        emit(t, r.status, "INFO", f"{label}: 200, posts={len(posts_of(r))} (undocumented access)", r)
    elif r.status >= 500:
        emit(t, r.status, "FAIL", f"{label}: server error {r.status}", r)
    else:
        iss, _ = cmp(r.body, JSON_ERR, ("error", "message"))
        emit(t, r.status, "INFO", f"{label}: {r.status} msg={msg(r)!r}" + (f"; JsonError {iss}" if iss else ""), r)

# ---------------------------------------------------------------- fixtures
print("counts:", dict(Counter(v for _, _, v, _, _ in rows)))
if un_fixture is not None and un_fixture.status == 200:
    save_fixture(SEG, "username_200", un_fixture.body)
s2 = got[("/search-v2", "text=test")][0]
s1 = got[("/search", "text=test")][0]
if s2.status == 200:
    save_fixture(SEG, "search_v2_200", s2.body)
    if s1.status == 200 and shape(s1.body) != shape(s2.body):
        save_fixture(SEG, "search_200", s1.body)
for kind, r in uni_fixtures.items():
    save_fixture(SEG, f"unified_{kind}_200", r.body)
seen = set()
for _, _, _, _, r in rows:
    if r is None or r.status < 400:
        continue
    key = (r.status, tuple(sorted(r.body)) if isinstance(r.body, dict) else type(r.body).__name__)
    if key in seen:
        continue
    seen.add(key)
    save_fixture(SEG, f"err_{r.status}_{len(seen)}", r.body)
print("fixtures:", sorted(p.name for p in (Path(__file__).parent / "fixtures" / SEG).glob("*.json")))
