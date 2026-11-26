"""Live tests for segment `mail` (Swagger 0.0.1). Writes only to recipient BOD (guard-enforced)."""
import re
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from http.client import IncompleteRead  # noqa: E402
from nyx import Client, Result, save_fixture, nonce  # noqa: E402

SEG = "mail"
c = Client(SEG)


def C(*a, **k):
    """Transport errors (urllib saw a truncated body) become status -1 -> FAIL; harness is not changed."""
    try:
        return c.call(*a, **k)
    except (IncompleteRead, OSError) as e:
        return Result(-1, f"transport: {type(e).__name__}: {e}"[:200], {}, 0)


rows = []   # (tid, status, verdict, note, Result|None)
_n = [0]
GET_CLAIM = ("GET /mail 200 {context, conversations[MailConversationWithActivity], posts[MailPost], "
             "reminders[MailPost], waiting_files[FileWithUrl]} all required; user Username [A-Z0-9_]{3,15}; "
             "text SearchExpression; order newest|newer_than|older_than|oldest (newer_than/older_than need from_id); "
             "from_id integer>=1; 400 JsonError")
SEND_CLAIM = ("POST /mail/send form recipient Username + message string required, format ContentFormatEnum "
              "text|html (default html); 200 JsonOk {}; 400 JsonError")
REM_CLAIM = ("POST /mail/reminder/{id}/{newState} id integer>=1, newState boolean; 200 JsonOk; 400 JsonError")
JSON_ERR = {"error": "bool", "code": "str", "message": "str"}


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
    if t == "bool":
        return isinstance(v, bool)
    if t == "bool?":
        return v is None or isinstance(v, bool)
    if t == "dt":
        return isinstance(v, str) and re.match(r"\d{4}-\d{2}-\d{2}T", v) is not None
    if t == "dict":
        return isinstance(v, dict)
    if t == "dict?":
        return v is None or isinstance(v, dict)
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


# Swagger schemas. Mail posts: incoming is boolean in Swagger (not nullable) -> "bool?" to see real values.
MAIL_POST = {"id": "int", "username": "str", "incoming": "bool?", "content": "str", "reminder": "bool",
             "unread": "bool", "inserted_at": "dt", "activity": "dict?", "new": "bool", "preview": "bool"}
POST_REQ = ("id", "username", "content", "inserted_at")
CONV = {"username": "str", "conversed_at": "dt", "incoming": "bool", "has_unread_mail": "bool", "activity": "dict?"}
FILE = {"id": "int", "file_type": "any", "id_specific": "int?", "id_specific2": "int?", "filename": "str",
        "size": "int", "uploaded_at": "dt", "mimetype": "any", "image_width": "int?", "image_height": "int?",
        "image_avg_color_hex": "str?", "image_embed": "bool", "url": "str", "thumb_url": "str"}
TOP = {"context": "dict", "conversations": "list", "posts": "list", "reminders": "list", "waiting_files": "list"}


def top_issues(b):
    iss, extra = cmp(b, TOP, tuple(TOP))
    if not isinstance(b, dict):
        return iss, []
    pex = set(extra)
    for key, spec, req in (("posts", MAIL_POST, POST_REQ), ("reminders", MAIL_POST, POST_REQ),
                           ("conversations", CONV, ("username",)), ("waiting_files", FILE, ("id", "url"))):
        for i, it in enumerate(b.get(key) if isinstance(b.get(key), list) else []):
            pi, pe = cmp(it, spec, req)
            iss += [f"{key}[{i}].{x}" for x in pi]
            pex |= {f"{key}.{x}" for x in pe}
    return iss, sorted(pex)


def msg(r):
    return r.body.get("message") if isinstance(r.body, dict) else str(r.body)[:80]


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


def err_shape(r):
    iss, _ = cmp(r.body, JSON_ERR, ("error", "message"))
    return f"msg={msg(r)!r}" + (f"; JsonError {iss}" if iss else "")


def check_200(r):
    """Generic 200 check: schema + page sizes + sort order."""
    if r.status != 200:
        return ("FAIL" if r.status >= 500 else "DIFF"), f"status {r.status} {err_shape(r)}"
    ps = posts_of(r)
    iss, ex = top_issues(r.body)
    ids = [p.get("id") for p in ps]
    dts = [p.get("inserted_at") for p in ps]
    order = ("desc" if ids == sorted(ids, reverse=True) and dts == sorted(dts, reverse=True)
             else "asc" if ids == sorted(ids) and dts == sorted(dts) else "mixed")
    sizes = {k: len(r.body.get(k) or []) for k in ("conversations", "posts", "reminders", "waiting_files")}
    note = f"sizes={sizes} order={order} users={sorted(users_in(r))}"
    nulls = sum(p.get("incoming") is None for p in ps)
    if nulls:
        note += f" incoming=null x{nulls}"
    if ex:
        note += f"; extra {ex}"
    if iss:
        return "DIFF", f"schema {iss[:3]}; {note}"
    return "OK", note


def check_plain(r):
    v, note = check_200(r)
    if v == "OK" and "incoming=null" in note:
        return "DIFF", note + " (Swagger: incoming boolean, not nullable)"
    return v, note


def check_user(want):
    def f(r):
        v, note = check_200(r)
        if v != "OK":
            return v, note
        extra = users_in(r) - {want, "NYXOT"}
        return ("INFO", f"posts from other users {sorted(extra)}; {note}") if extra else ("OK", note)
    return f


def check_word(word):
    def f(r):
        v, note = check_200(r)
        if v != "OK":
            return v, note
        miss = [p.get("id") for p in posts_of(r) if word not in plain(p.get("content"))]
        return ("FAIL", f"posts without '{word}': {miss[:3]}; {note}") if miss else ("OK", note)
    return f


def check_dir(desc):
    def f(r):
        v, note = check_200(r)
        if v != "OK":
            return v, note
        ids = ids_of(r)
        good = ids == sorted(ids, reverse=desc)
        return ("OK" if good else "DIFF"), f"{'desc' if desc else 'asc'} by id ok={good}; {note}"
    return f


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


def expect_400(what):
    def f(r):
        if r.status == 400:
            return "OK", f"400 ({what}) {err_shape(r)}"
        if r.status == 200:
            return "DIFF", f"200 accepted ({what}); posts={len(posts_of(r))}"
        if r.status == 422:
            return "DIFF", f"422 (Swagger documents 400 only) {err_shape(r)}"
        return "FAIL", f"status {r.status}"
    return f


def check_anon(r):
    if r.status == 200:
        return "INFO", f"200 without/with invalid token: undocumented access, posts={len(posts_of(r))}"
    if r.status in (400, 401):
        return "INFO", f"{r.status} without/with invalid token {err_shape(r)} (Swagger: 401 not documented)"
    return "FAIL", f"status {r.status}"


def check_oldest(r):
    v, note = check_200(r)
    if v != "OK":
        return v, note
    return "INFO", f"oldest page, order within page desc; ids={ids_of(r)[:3]}; {note}"


def read(label, params, claim, check, auth=True):
    t = tid()
    r = C("GET", "/mail", params=params or None, auth=auth, test_id=t, claim=f"{GET_CLAIM}; {claim}")
    v, note = ("FAIL", f"server error {r.status}") if r.status >= 500 else check(r)
    emit(t, r.status, v, f"{label}: {note}", r)
    return r


# ---------------------------------------------------------------- reads
base = read("no params", None, "no params (all params optional); shape/page/sort", check_plain)
base_posts = sorted(ids_of(base))
words = [w for p in posts_of(base) for w in re.findall(r"[^\W\d_]{4,}", plain(p.get("content")))]
word = words[0] if words else "test"
P = base_posts[len(base_posts) // 2] if len(base_posts) >= 2 else None

r_bod = read("user=BOD", {"user": "BOD"}, "user Username [A-Z0-9_]{3,15}", check_user("BOD"))
r_bod_lc = read("user=bod", {"user": "bod"}, "user pattern uppercase; lowercase case",
                lambda r: ("OK", f"400 for lowercase ({err_shape(r)})") if r.status == 400
                else ("INFO", f"status {r.status}; ids identical to user=BOD: {ids_of(r) == ids_of(r_bod)}"))
read(f"text={word}", {"text": word}, f"text SearchExpression; word '{word}' from a returned post",
     check_word(word))
read("order=newest", {"order": "newest"}, "order=newest", check_dir(True))
read("order=oldest", {"order": "oldest"}, "order=oldest", check_oldest)
if P is not None:
    read(f"order=newer_than from_id={P}", {"order": "newer_than", "from_id": P},
         "newer_than with from_id", check_range(P, True))
    read(f"order=older_than from_id={P}", {"order": "older_than", "from_id": P},
         "older_than with from_id", check_range(P, False))
else:
    emit(tid(), "-", "INFO", "fewer than 2 posts: from_id range cases skipped")
read("order=newer_than (no from_id)", {"order": "newer_than"}, "newer_than requires from_id",
     expect_400("from_id required"))
read("order=older_than (no from_id)", {"order": "older_than"}, "older_than requires from_id",
     expect_400("from_id required"))
read("from_id=0", {"order": "newest", "from_id": 0}, "from_id minimum 1", expect_400("from_id>=1"))
read("from_id=abc", {"order": "newest", "from_id": "abc"}, "from_id integer", expect_400("integer"))
read("order=foo", {"order": "foo"}, "order enum", expect_400("enum"))
read("no token", None, "undocumented: no bearer token (no 401 in Swagger)", check_anon, auth=False)
read("invalid token", None, "undocumented: invalid bearer token", check_anon, auth=("invalidtoken123"))

# ---------------------------------------------------------------- writes (BOD only, 7 sends max)
SENT = {}


def find_by(n):
    """Newest BOD mail page; return post whose content contains nonce n."""
    r = C("GET", "/mail", params={"user": "BOD", "order": "newest"})
    for p in posts_of(r):
        if n in (p.get("content") or ""):
            return p
    return None


def do_send(label, message, fmt=None, n=None, expect_err=False, undoc=False):
    data = {"recipient": "BOD", "message": message}
    if fmt is not None:
        data["format"] = fmt
    t = tid()
    r = C("POST", "/mail/send", data=data, test_id=t, claim=f"{SEND_CLAIM}; case {label}")
    if r.status == 400:
        v = "OK" if expect_err else "INFO"
        emit(t, 400, v, f"{label}: 400 {err_shape(r)}", r)
        return None
    if r.status != 200:
        emit(t, r.status, "FAIL", f"{label}: status {r.status}", r)
        return None
    body_v = "OK" if r.body == {} else "DIFF"
    if n is None:
        emit(t, 200, "INFO" if expect_err else "OK", f"{label}: 200 body={r.body!r}; no nonce possible (empty message)", r)
        return None
    found = find_by(n)
    if found is None:
        emit(t, 200, "FAIL", f"{label}: 200 but nonce not found in GET /mail?user=BOD&order=newest", r)
        return None
    same = found.get("content") == message
    note = (f"body={r.body!r} id={found.get('id')} incoming={found.get('incoming')!r} "
            f"stored==sent:{same} sent={message!r} stored={found.get('content')!r}")
    v = "INFO" if undoc or not same else body_v   # undocumented value or transformed content
    emit(t, 200, v, f"{label}: {note}", r)
    c.created.append(("mail", found.get("id")))
    SENT[label] = found.get("id")
    return found.get("id")


try:
    n1, n2, n3, n4, n6 = nonce(), nonce(), nonce(), nonce(), nonce()
    do_send("format=text", f"text {n1}\nline2 <b>x</b>", "text", n1)
    do_send("format=html", f"html {n2}\n<b>bold</b>", "html", n2)
    do_send("format=markdown", f"markdown {n3} **bold**", "markdown", n3, undoc=True)
    do_send("no format", f"noformat {n4}", None, n4)
    do_send("empty message", "", None, None, expect_err=True)
    do_send("duplicate #1", f"dup {n6}", None, n6)
    do_send("duplicate #2 (same text)", f"dup {n6}", None, n6)

    # ------------------------------------------------------------ reminder (only on own id)
    rid = SENT.get("format=text")

    def state_of(pid):
        r = C("GET", "/mail", params={"user": "BOD"})
        if r.status != 200:
            return f"GET {r.status}"
        flag = [p.get("reminder") for p in posts_of(r) if p.get("id") == pid]
        in_rem = pid in [p.get("id") for p in (r.body.get("reminders") or []) if isinstance(p, dict)]
        return flag, in_rem

    def rem(label, pid, state, want=None, expect_err=False, soft=False):
        t = tid()
        r = C("POST", f"/mail/reminder/{pid}/{state}", test_id=t, claim=f"{REM_CLAIM}; case {label}")
        if r.status == 200:
            st = state_of(pid)
            if soft:
                v, note = "INFO", f"200 (non-boolean literal {state!r} accepted); state after={st}"
            else:
                v = "OK" if isinstance(st, tuple) and st[0] == [want] else "DIFF"
                note = f"200 body={r.body!r}; want reminder={want}; state after={st}"
            emit(t, 200, v, f"{label}: {note}", r)
        elif r.status == 400:
            emit(t, 400, "OK" if expect_err else "INFO", f"{label}: 400 {err_shape(r)}", r)
        elif r.status == 422:
            emit(t, 422, "DIFF", f"{label}: 422 (Swagger documents 400 only) {err_shape(r)}", r)
        else:
            emit(t, r.status, "FAIL", f"{label}: status {r.status}", r)

    if rid is not None:
        rem("newState=true", rid, "true", want=True)
        rem("newState=false", rid, "false", want=False)
        rem("newState=1", rid, "1", want=True, soft=True)
        rem("newState=0", rid, "0", want=False, soft=True)
        rem("newState=abc", rid, "abc", expect_err=True)
    else:
        emit(tid(), "-", "INFO", "no own sent id: reminder cases skipped")
    rem("id=0", 0, "true", expect_err=True)
    rem("id=999999999999", 999999999999, "true", expect_err=True)
    rem("id=abc", "abc", "true", expect_err=True)
    emit(tid(), "-", "INFO", "reminder on a foreign mail id: skipped (not available to this test)")
finally:
    print("created mail ids:", [i for k, i in c.created if k == "mail"])

# ---------------------------------------------------------------- fixtures
print("counts:", dict(Counter(v for _, _, v, _, _ in rows)))
if base.status == 200:
    save_fixture(SEG, "mail_200", base.body)
ok_send = next((r for _, _, _, _, r in rows if r is not None and r.status == 200 and r.body == {}), None)
if ok_send is not None:
    save_fixture(SEG, "send_200", ok_send.body)
seen = set()
for _, _, _, _, r in rows:
    if r is None or r.status < 400:
        continue
    key = (r.status, tuple(sorted(r.body)) if isinstance(r.body, dict) else type(r.body).__name__)
    if key in seen:
        continue
    seen.add(key)
    save_fixture(SEG, f"err_{r.status}_{len(seen)}", r.body)
print("fixtures: see tests/fixtures/mail/")
