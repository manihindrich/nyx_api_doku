"""Live GET-only tests for segment `last` (Swagger 0.0.1). Writes nothing."""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nyx import Client, save_fixture, shape  # noqa: E402

SEG = "last"
c = Client(SEG)
rows = []          # (tid, status, verdict, note, Result|None)


def emit(tid, status, verdict, note, res=None):
    rows.append((tid, status, verdict, note, res))
    print(f"{tid} | {status} | {verdict} | {note}")


def type_ok(v, t):
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
    if t == "dt":
        return isinstance(v, str) and len(v) >= 19 and v[4] == "-" and v[10] == "T"
    if t == "dict":
        return isinstance(v, dict)
    if t == "list":
        return isinstance(v, list)
    raise ValueError(t)


def cmp(obj, spec, required=()):
    """Compare dict against spec {key: type}; list missing required, wrong types, extras."""
    if not isinstance(obj, dict):
        return [f"not object ({type(obj).__name__})"]
    issues = []
    for k in required:
        if k not in obj:
            issues.append(f"missing required {k}")
    for k, t in spec.items():
        if k in obj and not type_ok(obj[k], t):
            issues.append(f"{k}={type(obj[k]).__name__} (want {t})")
    extra = sorted(set(obj) - set(spec))
    if extra:
        issues.append(f"extra {extra}")
    return issues


# TemplatePost = DiscussionPostWithName (required id, discussion_id, username, content, inserted_at)
# + activity, new, preview, can_be_deleted, can_be_rated, can_be_reminded, can_ignore_discussion, rating_friends
POST_SPEC = {"id": "int", "discussion_id": "int", "username": "str", "content": "str?", "content_raw": "dict",
             "post_type": "str", "reminder": "bool", "rating": "int", "my_rating": "str", "replies": "list",
             "inserted_at": "dt", "activity": "dict", "new": "bool", "preview": "bool",
             "can_be_deleted": "bool", "can_be_rated": "bool", "can_be_reminded": "bool",
             "can_ignore_discussion": "bool", "rating_friends": "list"}
POST_REQ = ("id", "discussion_id", "username", "content", "inserted_at")
ACTIVITY_SPEC = {"username": "str", "last_activity": "dt", "last_access_method": "str",
                 "status_details": "str", "location": "str", "location_url": "str"}
CONTEXT_SPEC = {"user": "dict", "active_friends": "list"}
DOMAIN_SPEC = {"user_id": "int", "domain_id": "int", "name": "str", "ignored": "bool"}
DISC_SPEC = {"user_id": "int", "discussion_id": "int", "full_name": "str"}
JSON_ERR = {"error": "bool", "code": "str", "message": "str"}


def posts_of(body):
    return body.get("posts") or []


def ids_of(body):
    return {p["id"] for p in posts_of(body)}


def effectively_same(posts, same_ids):
    """Live list drifts between calls; treat >=90% overlap with the baseline as identical."""
    ids = {p["id"] for p in posts}
    return len(ids & same_ids) >= 0.9 * max(len(same_ids), 1) and len(ids) >= 0.9 * max(len(same_ids), 1)


# ---------------------------------------------------------------- T-01 no params
r1 = c.call("GET", "/last", test_id="T-last-01",
            claim="GET /last 200: object {context, posts[TemplatePost], ignored_domains, ignored_discussions} "
                  "required; 'Vrati seznam poslednich prispevku'")
print("shape(01 body):", shape(r1.body, max_depth=3))
base_ids = set()
base_domains = {}
if r1.status == 200 and isinstance(r1.body, dict):
    b = r1.body
    top = cmp(b, {"context": "dict", "posts": "list", "ignored_domains": "list",
                  "ignored_discussions": "list"},
              required=("context", "posts", "ignored_domains", "ignored_discussions"))
    issues = list(top)
    posts = posts_of(b)
    post_issues = Counter()
    act_issues = Counter()
    extra_post, extra_act = set(), set()
    for p in posts:
        for x in cmp(p, POST_SPEC, POST_REQ):
            if x.startswith("extra"):
                extra_post |= set(eval(x[6:]))
            else:
                post_issues[x.split(" (")[0]] += 1
        if isinstance(p.get("activity"), dict):
            for x in cmp(p["activity"], ACTIVITY_SPEC, ("username", "last_activity")):
                if x.startswith("extra"):
                    extra_act |= set(eval(x[6:]))
                else:
                    act_issues[x.split(" (")[0]] += 1
    if extra_post:
        post_issues["extra " + ",".join(sorted(extra_post))] = sum(1 for p in posts if set(p) - set(POST_SPEC))
    if extra_act:
        act_issues["extra " + ",".join(sorted(extra_act))] = 1
    issues += [f"context: {x}" for x in cmp(b.get("context"), CONTEXT_SPEC, ("user", "active_friends"))]
    for d in b.get("ignored_domains") or []:
        issues += [f"ignored_domains: {x}" for x in cmp(d, DOMAIN_SPEC, DOMAIN_SPEC.keys())]
    for d in b.get("ignored_discussions") or []:
        issues += [f"ignored_discussions: {x}" for x in cmp(d, DISC_SPEC, DISC_SPEC.keys())]
    base_ids = ids_of(b)
    base_domains = {d["domain_id"]: d["name"] for d in b.get("ignored_domains") or [] if isinstance(d, dict)}
    notes = [f"posts={len(posts)}", f"ignored_domains={len(b.get('ignored_domains') or [])}",
             f"ignored_discussions={len(b.get('ignored_discussions') or [])}"]
    if issues:
        notes.append(f"top-level: {issues[:6]}")
    if post_issues:
        notes.append(f"post vs TemplatePost: {dict(post_issues)}")
    if act_issues:
        notes.append(f"activity vs Activity: {dict(act_issues)}")
    notes.append("posts carry discussion_name (undocumented), no domain_id")
    verdict = "DIFF" if (issues or post_issues or act_issues) else "OK"
    emit("T-last-01", r1.status, verdict, "; ".join(notes), r1)
else:
    emit("T-last-01", r1.status, "FAIL", f"non-200/non-object: {str(r1.body)[:120]}", r1)


def run(tid, params, claim, judge, **kw):
    """One GET with params; judge(posts, same_as_base) -> (verdict, note)."""
    r = c.call("GET", "/last", params=params, test_id=tid, claim=claim, **kw)
    if r.status != 200 or not isinstance(r.body, dict):
        emit(tid, r.status, "FAIL" if r.status >= 500 else "INFO",
             f"status {r.status}: {str(r.body)[:120]}", r)
        return r
    posts = posts_of(r.body)
    same = effectively_same(posts, base_ids)
    verdict, note = judge(posts, same)
    emit(tid, r.status, verdict, f"n={len(posts)}; {note}", r)
    return r


# ---------------------------------------------------------------- domain (= ignored_domains.domain_id)
def domain_judge(v):
    def j(posts, same):
        name = base_domains.get(v, "not in ignored_domains") if isinstance(v, int) else "-"
        if not posts:
            return "INFO", f"0 posts (domain_id {v}={name!r})"
        if same:
            return "INFO", "identical to unfiltered list: filter ignored"
        names = Counter(p["discussion_name"] for p in posts).most_common(2)
        return "OK", f"filtered; domain_id {v}={name!r}; top discussions {[n for n, _ in names]}"
    return j


for tid, v in (("T-last-02", 0), ("T-last-03", 1), ("T-last-04", 2), ("T-last-05", 5),
               ("T-last-06", 10), ("T-last-07", 99999), ("T-last-08", -1), ("T-last-09", "abc")):
    run(tid, {"domain": v}, "domain integer, 'Kategorie diskuzi' (filters posts by category)",
        domain_judge(v))


# ---------------------------------------------------------------- min_rating
def rating_judge(v):
    def j(posts, same):
        if isinstance(v, int) and v > 0:
            bad = [p for p in posts if p.get("rating") is None or p["rating"] < v]
            ratings = sorted({p.get("rating") for p in posts if p.get("rating") is not None})
            if bad:
                return "DIFF", (f"{len(bad)} posts with rating<{v} or no rating field; "
                                f"ratings returned={ratings[:8]}")
            return "OK", f"all rated >= {v}; ratings={ratings[:8]}"
        if isinstance(v, int):
            return ("OK", "<=0: identical to unfiltered") if same else ("DIFF", "<=0 filters the list")
        return ("INFO", "non-integer: identical to unfiltered") if same else ("INFO", "non-integer: list differs")
    return j


for tid, v in (("T-last-10", 0), ("T-last-11", 1), ("T-last-12", 5), ("T-last-13", 10),
               ("T-last-14", 50), ("T-last-15", -5), ("T-last-16", "abc")):
    run(tid, {"min_rating": v}, "min_rating integer, 'Minimalni hodnoceni' (posts with rating >= value)",
        rating_judge(v))


# ---------------------------------------------------------------- rated_by_friends / rated_by_me
def flag_judge(pred, truthy, pname):
    def j(posts, same):
        if truthy is None:      # non-boolean value
            return "INFO", f"non-boolean value: {'identical to unfiltered' if same else 'list differs'}"
        if not truthy:
            return ("OK", "false: identical to unfiltered") if same else ("DIFF", "false still filters")
        if not posts:
            return "INFO", "filter applied, 0 matches (base list has no matching post; positive path unverifiable)"
        if same:
            return "DIFF", "true-value ignored: list identical to unfiltered"
        failing = sum(1 for p in posts if not pred(p))
        if failing:
            return "DIFF", f"{failing}/{len(posts)} posts lack {pname}"
        return "OK", f"all posts have {pname}"
    return j


friends_pred = lambda p: bool(p.get("rating_friends"))          # noqa: E731
me_pred = lambda p: p.get("my_rating") is not None              # noqa: E731
for tid, v, truthy in (("T-last-17", "true", True), ("T-last-18", "false", False),
                       ("T-last-19", "1", True), ("T-last-20", "0", False),
                       ("T-last-21", "abc", None)):
    run(tid, {"rated_by_friends": v}, "rated_by_friends boolean, 'Prispevky hodnocene prateli'",
        flag_judge(friends_pred, truthy, "rating_friends"))
for tid, v, truthy in (("T-last-22", "true", True), ("T-last-23", "false", False),
                       ("T-last-24", "1", True), ("T-last-25", "0", False)):
    run(tid, {"rated_by_me": v}, "rated_by_me boolean, 'Prispevky hodnocene mnou'",
        flag_judge(me_pred, truthy, "my_rating"))


# ---------------------------------------------------------------- combination
r26 = run("T-last-26", {"min_rating": 5, "rated_by_me": "false"},
          "min_rating=5 combined with rated_by_me=false: every post rating >= 5",
          lambda posts, same: (("OK", f"all rated >= 5; ratings={sorted({p.get('rating') for p in posts}, key=str)[:6]}")
                               if posts and all((p.get("rating") or -1) >= 5 for p in posts)
                               else ("DIFF", "post with rating < 5 returned or empty")))


# ---------------------------------------------------------------- auth
r27 = c.call("GET", "/last", auth=False, test_id="T-last-27",
             claim="undocumented: GET /last without Authorization header (Swagger lists no 401)")
r28 = c.call("GET", "/last", auth="invalidtoken123", test_id="T-last-28",
             claim="undocumented: GET /last with invalid bearer token (Swagger lists no 401)")
for tid, r in (("T-last-27", r27), ("T-last-28", r28)):
    if r.status == 200:
        emit(tid, r.status, "INFO", f"200 without valid token: posts={len(posts_of(r.body))}, undocumented", r)
    elif r.status == 400:
        iss = cmp(r.body, JSON_ERR, ("error", "message"))
        emit(tid, r.status, "INFO", f"400 JsonError {'ok' if not iss else iss}; "
             f"message={r.body.get('message') if isinstance(r.body, dict) else r.body!r}", r)
    elif r.status >= 500:
        emit(tid, r.status, "FAIL", f"server error {r.status}", r)
    else:
        emit(tid, r.status, "INFO", f"status {r.status} undocumented; body={str(r.body)[:100]}", r)

# ---------------------------------------------------------------- fixtures
if r1.status == 200:
    save_fixture(SEG, "get_last_200", r1.body)
seen = set()
for _, _, _, _, r in rows:
    if r is None or r.status < 400:
        continue
    key = (r.status, tuple(sorted(r.body)) if isinstance(r.body, dict) else type(r.body).__name__)
    if key in seen:
        continue
    seen.add(key)
    save_fixture(SEG, f"err_{r.status}_{len(seen)}", r.body)

print("counts:", dict(Counter(v for _, _, v, _, _ in rows)))
