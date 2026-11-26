"""Live tests for segment `bookmarks` (Swagger 0.0.1).

Reads: /bookmarks, /bookmarks/all, /bookmarks/history, /bookmarks/history/more.
Writes: only the history / read state of discussion 288360 (guard-enforced in nyx.py).
Guard cases (discussion_ids missing or empty) are recorded as not testable and never sent.
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from http.client import IncompleteRead  # noqa: E402
from nyx import Client, Forbidden, Result, save_fixture  # noqa: E402

SEG = "bookmarks"
DISC = 288360            # "NYXOT ~ testing NYX API" (owner NYXOT): the only discussion written to
BM, ALL = "/bookmarks", "/bookmarks/all"
HIST, MORE = "/bookmarks/history", "/bookmarks/history/more"
REMOVE = "/bookmarks/history/remove_from_history"
MARK = "/bookmarks/history/mark_as_read"
DP = f"/discussion/{DISC}"
BAD_TOKEN = "invalid-nyxapidoku-token"
WP = {"show_read": "true", "show_booked": "true"}   # view that lists DISC whenever it is in history
NEW_KEYS = ("new_replies_count", "new_posts_count", "new_links_count", "new_images_count")
STATE_KEYS = NEW_KEYS + ("last_seen_post_id", "last_visited_at")

# Swagger shapes. "x?" = nullable. Swagger declares no required[] for these; all listed fields are expected.
BMDATA = {"context": "obj", "reminder_count": "int", "bookmarks": "list"}
GROUP = {"category": "obj", "bookmarks": "list"}
CAT = {"id": "int", "category_name": "str"}
BDISC = {"discussion_id": "int", "is_owner": "bool", "full_name": "str",
         "new_replies_count": "int", "new_posts_count": "int", "new_links_count": "int",
         "new_images_count": "int", "last_visited_at": "str", "last_seen_post_id": "int"}
BDISC_REQ = ("discussion_id", "last_visited_at", "last_seen_post_id")
HIST_SPEC = {"context": "obj", "discussions": "list", "show_load_more": "bool"}

BM_CLAIM = "GET /bookmarks (query expand int 'Rozbalit nejakou konkretni kategorii'): 'Nacte bookmarky podle nastaveni uzivatele'; 200 BookmarksData"
BM_EXP_CLAIM = "GET /bookmarks query expand integer 'Rozbalit nejakou konkretni kategorii'; 200 BookmarksData"
ALL_CLAIM = "GET /bookmarks/all: 'Nacte bookmarky se vsemi kategoriemi rozbalenymi'; 200 BookmarksData"
HIST_CLAIM = ("GET /bookmarks/history query more_results, show_read, show_booked (booleans; 'Pokud chybi, pouzije se "
              "hodnota pro web rozhrani'); 200 {context, discussions:[BookmarkedDiscussion], show_load_more:boolean}")
MORE_CLAIM = ("GET /bookmarks/history/more query show_read, show_booked (booleans) 'Zobrazovat i ... s vice zaznamy'; "
              "200 {context, discussions:[BookmarkedDiscussion], show_load_more:boolean}")
REMOVE_CLAIM = ("POST /bookmarks/history/remove_from_history form discussion_ids array<int> required, encoding "
                "style=form explode=true ('Odebere diskuze z historie'); 200 and 400 documented without schema")
MARK_CLAIM = ("POST /bookmarks/history/mark_as_read form discussion_ids array<int> required, encoding style=form "
              "explode=true ('Oznaci diskuze za prectene'); 200 and 400 documented without schema")
AUTH_CLAIM = "undocumented: no 401 in Swagger for bookmarks endpoints; token required"
VISIT_CLAIM = "undocumented: GET /discussion/{id} used as a visit to re-add a discussion to history (restore step)"

HIST_VARIANTS = [
    ("no params", {}, "plain"),
    ("more_results=true", {"more_results": "true"}, "plain"),
    ("more_results=false", {"more_results": "false"}, "plain"),
    ("show_read=true", {"show_read": "true"}, "plain"),
    ("show_read=false", {"show_read": "false"}, "plain"),
    ("show_booked=true", {"show_booked": "true"}, "plain"),
    ("show_booked=false", {"show_booked": "false"}, "plain"),
    ("show_read=true&show_booked=true", {"show_read": "true", "show_booked": "true"}, "plain"),
    ("show_read=false&show_booked=false", {"show_read": "false", "show_booked": "false"}, "plain"),
    ("all three true", {"more_results": "true", "show_read": "true", "show_booked": "true"}, "plain"),
    ("all three false", {"more_results": "false", "show_read": "false", "show_booked": "false"}, "plain"),
    ("more_results=1", {"more_results": "1"}, "bad"),
    ("show_read=1", {"show_read": "1"}, "bad"),
    ("show_booked=1", {"show_booked": "1"}, "bad"),
]
MORE_VARIANTS = [
    ("no params", {}, "plain"),
    ("show_read=true", {"show_read": "true"}, "plain"),
    ("show_read=false", {"show_read": "false"}, "plain"),
    ("show_booked=true", {"show_booked": "true"}, "plain"),
    ("show_booked=false", {"show_booked": "false"}, "plain"),
    ("show_read=true&show_booked=true", {"show_read": "true", "show_booked": "true"}, "plain"),
    ("show_read=false&show_booked=false", {"show_read": "false", "show_booked": "false"}, "plain"),
    ("show_read=1", {"show_read": "1"}, "bad"),
]

c = Client(SEG)
rows = []                # (tid, status, verdict, note)
_n = [0]
FIX = {}                 # fixture name -> first successful body
ERRS = {}                # (status, message) -> first error body of that kind
HSTORE = {}              # (path, params key) -> set of discussion ids returned
BASE = None              # body of GET /bookmarks (no params)
BASE_EXP = []            # category ids expanded in BASE
REMOVED = [False]        # True while 288360 may be out of history (restore required)


# ---------------------------------------------------------------- shape helpers
def type_ok(v, t):
    if t.endswith("?") and v is None:
        return True
    base = t.rstrip("?")
    checks = {
        "int": lambda x: isinstance(x, int) and not isinstance(x, bool),
        "str": lambda x: isinstance(x, str),
        "bool": lambda x: isinstance(x, bool),
        "obj": lambda x: isinstance(x, dict),
        "list": lambda x: isinstance(x, list),
    }
    return checks[base](v)


def cmp(obj, spec, required=()):
    """-> (issues, extra keys). spec = {field: type}; `required` fields must be present."""
    if not isinstance(obj, dict):
        return [f"not object ({type(obj).__name__})"], []
    issues = [f"missing {k}" for k in required if k not in obj]
    issues += [f"{k}={type(v).__name__} (want {spec[k]})"
               for k, v in obj.items() if k in spec and not type_ok(v, spec[k])]
    return issues, sorted(set(obj) - set(spec))


def groups_raw(body):
    v = body.get("bookmarks") if isinstance(body, dict) else None
    return v if isinstance(v, list) else []


def groups(body):
    """-> [(category id, category name, items)] for BookmarksData."""
    out = []
    for g in groups_raw(body):
        if isinstance(g, dict):
            cat = g.get("category") if isinstance(g.get("category"), dict) else {}
            items = g.get("bookmarks") if isinstance(g.get("bookmarks"), list) else []
            out.append((cat.get("id"), cat.get("category_name"), items))
    return out


def disc_list(body):
    v = body.get("discussions") if isinstance(body, dict) else None
    return v if isinstance(v, list) else []


def find_disc(body):
    for d in disc_list(body):
        if isinstance(d, dict) and d.get("discussion_id") == DISC:
            return d
    return None


def unread(d):
    return sum((d.get(k) or 0) for k in NEW_KEYS)


def state_diff(a, b):
    d = {k: (a.get(k), b.get(k)) for k in STATE_KEYS if a.get(k) != b.get(k)}
    return d or "no change in state fields"


def check_bm(body):
    iss, ex = cmp(body, BMDATA, tuple(BMDATA))
    for g in groups_raw(body):
        gi, ge = cmp(g, GROUP, tuple(GROUP))
        iss += gi
        ex += ge
        if isinstance(g, dict):
            ci, ce = cmp(g.get("category"), CAT, tuple(CAT))
            iss += ci
            ex += ce
            if isinstance(g.get("bookmarks"), list):
                for d in g["bookmarks"]:
                    di, de = cmp(d, BDISC, BDISC_REQ)
                    iss += di
                    ex += de
    return iss, sorted(set(ex))


def check_hist(body):
    iss, ex = cmp(body, HIST_SPEC, tuple(HIST_SPEC))
    for d in disc_list(body):
        di, de = cmp(d, BDISC, BDISC_REQ)
        iss += di
        ex += de
    return iss, sorted(set(ex))


def tail(iss, ex):
    s = ""
    if iss:
        s += f"; issues {iss[:4]}"
    if ex:
        s += f"; extra keys {ex}"
    return s


def summ_bm(body):
    gs = groups(body)
    cats = ", ".join(f"{i}:{n}:{len(it)}" for i, n, it in gs)
    exp = [i for i, _, it in gs if it]
    tot = sum(len(it) for _, _, it in gs)
    hit = [i for i, _, it in gs if any(isinstance(d, dict) and d.get("discussion_id") == DISC for d in it)]
    return f"cats[id:name:items]=[{cats}]; expanded={exp}; items={tot}; {DISC} in cats {hit}"


def summ_hist(body):
    if not isinstance(body, dict):
        return "non-dict body"
    d = find_disc(body)
    s = (f"discussions={len(disc_list(body))}; show_load_more={body.get('show_load_more')!r}; "
         f"{DISC} {'LISTED' if d else 'absent'}")
    if d:
        s += f" (unread={unread(d)}, last_seen_post_id={d.get('last_seen_post_id')})"
    return s


def brief(r):
    s = r.body if isinstance(r.body, str) else str(r.body)
    return f"{r.status} {s[:160]}"


def pkey(params):
    return tuple(sorted((params or {}).items()))


# ---------------------------------------------------------------- runner
def tid():
    _n[0] += 1
    return f"T-{SEG}-{_n[0]:02d}"


def emit(t, status, verdict, note):
    rows.append((t, status, verdict, note))
    print(f"{t} | {status} | {verdict} | {note}")


def req(label, method, path, claim, judge, *, fix=None, **kw):
    t = tid()
    try:
        r = c.call(method, path, test_id=t, claim=claim, **kw)
    except (IncompleteRead, OSError) as e:
        r = Result(-1, f"transport: {type(e).__name__}: {e}"[:200], {}, 0)
    v, note = ("FAIL", "transport error") if r.status == -1 else judge(r)
    emit(t, r.status, v, f"{label}: {note}")
    if r.status == 200 and fix and fix not in FIX:
        FIX[fix] = r.body
    if r.status >= 400:
        m = r.body.get("message") if isinstance(r.body, dict) else str(r.body)[:60]
        ERRS.setdefault((r.status, m), r.body)
    return r


def guarded(label, method, path, claim, **kw):
    t = tid()
    try:
        c.call(method, path, test_id=t, claim=claim, **kw)
    except Forbidden as e:
        emit(t, "-", "INFO", f"{label}: not testable (guard): {e}")
        return
    emit(t, "-", "FAIL", f"{label}: request was sent (guard not active?)")


# ---------------------------------------------------------------- judges: (Result) -> (verdict, note)
def j_auth(r):
    if r.status == 200:
        return "DIFF", f"accepted without valid token: {brief(r)}"
    if r.status >= 500:
        return "FAIL", brief(r)
    return "INFO", f"status {r.status}: {brief(r)}"


def j_bm(mode, target=None):
    """mode: plain | exists (target is a category id from BASE) | missing | bad (wrong type)."""
    def j(r):
        if r.status >= 500:
            return "FAIL", brief(r)
        if r.status != 200:
            return "INFO", f"undocumented status {r.status} (Swagger documents only 200): {brief(r)}"
        iss, ex = check_bm(r.body)
        note = summ_bm(r.body) + tail(iss, ex)
        if target is not None:
            exp = [i for i, _, it in groups(r.body) if it]
            note += f"; target {target} expanded={target in exp}; BASE expanded={BASE_EXP}"
        if iss:
            return "DIFF", note
        if mode in ("missing", "bad"):
            return "INFO", note
        return "OK", note
    return j


def j_all(r):
    if r.status >= 500:
        return "FAIL", brief(r)
    if r.status != 200:
        return "INFO", brief(r)
    iss, ex = check_bm(r.body)
    gb, ga = groups(BASE), groups(r.body)
    ids_b = [i for i, _, _ in gb]
    ids_a = [i for i, _, _ in ga]
    lost = [i for i, _, it in gb if it and not any(j == i and len(x) >= len(it) for j, _, x in ga)]
    tot_b = sum(len(it) for _, _, it in gb)
    tot_a = sum(len(it) for _, _, it in ga)
    note = (summ_bm(r.body) + f"; /bookmarks items={tot_b}, /all items={tot_a}; "
            f"cat ids same as /bookmarks={ids_a == ids_b}; base-expanded categories not covered={lost}")
    note += tail(iss, ex)
    if iss or lost or ids_a != ids_b:
        return "DIFF", note
    return "OK", note


def j_has_bm(r):
    if r.status != 200:
        return "INFO", brief(r)
    hits = [i for i, _, it in groups(r.body) for d in it if isinstance(d, dict) and d.get("discussion_id") == DISC]
    return "INFO", f"{DISC} in bookmarks={bool(hits)} (category ids {hits})"


def j_list(path, key, mode):
    """Shape check for /bookmarks/history and /bookmarks/history/more; compares with the /history twin."""
    def j(r):
        if r.status >= 500:
            return "FAIL", brief(r)
        if r.status != 200:
            return "INFO", f"undocumented status {r.status}: {brief(r)}"
        iss, ex = check_hist(r.body)
        ids = {d.get("discussion_id") for d in disc_list(r.body) if isinstance(d, dict)}
        HSTORE[(path, key)] = ids
        note = summ_hist(r.body) + tail(iss, ex)
        if path == MORE:
            twin = HSTORE.get((HIST, key))
            if twin is None:
                note += "; no /history twin with same params"
            else:
                note += (f"; /history twin ids={len(twin)}, more-ids={len(ids)}, "
                         f"overlap={len(ids & twin)}, only-in-more={len(ids - twin)}")
        if iss:
            return "DIFF", note
        if mode == "bad":
            return "INFO", note
        return "OK", note
    return j


def j_write(mode):
    """mode: plain (Swagger form) | bracket (harness list form discussion_ids[]) | repeat (already removed)."""
    def j(r):
        if r.status >= 500:
            return "FAIL", brief(r)
        if mode == "repeat":
            return "INFO", brief(r)
        if r.status == 200:
            return ("OK" if mode == "plain" else "INFO"), f"200 (no schema in Swagger): {brief(r)}"
        if r.status == 400:
            return ("DIFF" if mode == "plain" else "INFO"), f"400: {brief(r)}"
        return "INFO", f"undocumented status {r.status}: {brief(r)}"
    return j


def j_snap(expect, strict, before=None, state_check=False):
    def j(r):
        if r.status >= 500:
            return "FAIL", brief(r)
        if r.status != 200:
            return "INFO", brief(r)
        a = find_disc(r.body)
        note = f"{DISC} {'listed' if a else 'absent'}"
        if a:
            note += f" (unread={unread(a)}, last_seen_post_id={a.get('last_seen_post_id')})"
        if state_check:
            if before is None or a is None:
                return "INFO", note + "; no before/after pair to compare"
            ub, ua = unread(before), unread(a)
            d = state_diff(before, a)
            if ub == 0:
                return "INFO", f"nothing unread before (0), after={ua}; diff={d}"
            if ua == 0:
                return "OK", f"unread {ub}->0; diff={d}"
            return "DIFF", f"Swagger: marked as read, but unread {ub}->{ua}; diff={d}"
        if (a is not None) == expect:
            return "OK", note
        msg = f"expected {'listed' if expect else 'absent'}; {note}"
        return ("DIFF" if strict else "INFO"), msg
    return j


def j_visit(r):
    if r.status >= 500:
        return "FAIL", brief(r)
    return "INFO", brief(r)


# ---------------------------------------------------------------- steps
def snap(label, expect=True, strict=False, before=None, state_check=False):
    r = req(label, "GET", HIST, HIST_CLAIM, j_snap(expect, strict, before, state_check), params=WP)
    return find_disc(r.body) if r.status == 200 else None


def restore(tag):
    """Visit the discussion to re-add it to history; fall back to order=newest. -> True if listed again."""
    req(f"{tag}a GET /discussion/{DISC} (visit)", "GET", DP, VISIT_CLAIM, j_visit)
    if snap(f"{tag}b history after visit", expect=True) is not None:
        REMOVED[0] = False
        return True
    req(f"{tag}c GET /discussion/{DISC}?order=newest (visit)", "GET", DP, VISIT_CLAIM, j_visit,
        params={"order": "newest"})
    ok = snap(f"{tag}d history after order=newest visit", expect=True) is not None
    if ok:
        REMOVED[0] = False
    return ok


def read_phase():
    global BASE, BASE_EXP
    b0 = req("B0 GET /bookmarks (no params)", "GET", BM, BM_CLAIM, j_bm("plain"), fix="bookmarks_200")
    if b0.status == 200:
        BASE = b0.body
        BASE_EXP = [i for i, _, it in groups(BASE) if it]
    ids = [i for i, _, _ in groups(BASE)]
    for cid in ids:
        req(f"E1 expand={cid} (category from BASE)", "GET", BM, BM_EXP_CLAIM, j_bm("exists", cid),
            params={"expand": str(cid)})
    for v in (0, -1, 99999):
        if v not in ids:
            req(f"E2 expand={v}", "GET", BM, BM_EXP_CLAIM, j_bm("missing", v), params={"expand": str(v)})
    req("E3 expand=abc", "GET", BM, BM_EXP_CLAIM, j_bm("bad"), params={"expand": "abc"})

    req("L1 GET /bookmarks/all", "GET", ALL, ALL_CLAIM, j_all, fix="bookmarks_all_200")

    for label, params, mode in HIST_VARIANTS:
        req(f"H {label}", "GET", HIST, HIST_CLAIM, j_list(HIST, pkey(params), mode),
            params=params, fix="history_200")
    for label, params, mode in MORE_VARIANTS:
        req(f"M {label}", "GET", MORE, MORE_CLAIM, j_list(MORE, pkey(params), mode),
            params=params, fix="history_more_200")

    req("A1 GET /bookmarks no token", "GET", BM, AUTH_CLAIM, j_auth, auth=False)
    req("A2 GET /bookmarks invalid token", "GET", BM, AUTH_CLAIM, j_auth, auth=BAD_TOKEN)
    req("A3 GET /bookmarks/history no token", "GET", HIST, AUTH_CLAIM, j_auth, auth=False)
    req("A4 GET /bookmarks/history invalid token", "GET", HIST, AUTH_CLAIM, j_auth, auth=BAD_TOKEN)
    req("A5 GET /bookmarks/history/more no token", "GET", MORE, AUTH_CLAIM, j_auth, auth=False)
    req("A6 GET /bookmarks/history/more invalid token", "GET", MORE, AUTH_CLAIM, j_auth, auth=BAD_TOKEN)


def guards():
    guarded("G1 remove_from_history: discussion_ids omitted", "POST", REMOVE, REMOVE_CLAIM)
    guarded("G2 remove_from_history: discussion_ids=[]", "POST", REMOVE, REMOVE_CLAIM,
            data={"discussion_ids": []})
    guarded("G3 mark_as_read: discussion_ids omitted", "POST", MARK, MARK_CLAIM)
    guarded("G4 mark_as_read: discussion_ids=[]", "POST", MARK, MARK_CLAIM, data={"discussion_ids": []})


def write_phase():
    s0 = snap("W0 history pre-state", expect=True)
    req("W1 mark_as_read discussion_ids[]=288360 (bracket form)", "POST", MARK, MARK_CLAIM,
        j_write("bracket"), data={"discussion_ids": [DISC]}, fix="write_mark_200")
    s1 = snap("W2 history after W1 (unread changed?)", expect=True, before=s0, state_check=True)
    req("W3 mark_as_read discussion_ids=288360 (plain form)", "POST", MARK, MARK_CLAIM,
        j_write("plain"), data={"discussion_ids": DISC})
    snap("W4 history after W3 (unread changed?)", expect=True, before=s1, state_check=True)

    REMOVED[0] = True
    req("W5 remove_from_history discussion_ids[]=288360 (bracket form)", "POST", REMOVE, REMOVE_CLAIM,
        j_write("bracket"), data={"discussion_ids": [DISC]}, fix="write_remove_200")
    snap("W6 history after W5 (gone?)", expect=False, strict=True)
    req("W7 GET /bookmarks/all (still bookmarked?)", "GET", ALL, ALL_CLAIM, j_has_bm)
    req("W8 remove_from_history again (already removed)", "POST", REMOVE, REMOVE_CLAIM,
        j_write("repeat"), data={"discussion_ids": [DISC]})
    snap("W9 history after W8", expect=False)

    if restore("R1"):
        REMOVED[0] = True
        req("W10 remove_from_history discussion_ids=288360 (plain form)", "POST", REMOVE, REMOVE_CLAIM,
            j_write("plain"), data={"discussion_ids": DISC})
        snap("W11 history after W10 (gone?)", expect=False, strict=True)
        restore("R2")
    else:
        emit("W10", "-", "INFO", "plain remove skipped: 288360 not back in history after restore (not testable)")


try:
    read_phase()
    guards()
    write_phase()
finally:
    if REMOVED[0]:
        print("FINALLY: 288360 may be out of history, restoring")
        restore("RF")
    final = snap("F1 final history (show_read+show_booked)", expect=True)
    req("F2 final GET /bookmarks/all", "GET", ALL, ALL_CLAIM, j_has_bm)
    print("FINAL STATE: 288360 in history =", final is not None, "| unread =",
          unread(final) if final else None)

print("counts:", dict(Counter(v for _, _, v, _ in rows)))
for name, body in FIX.items():
    save_fixture(SEG, name, body)
kinds = Counter()
for (st, m), body in ERRS.items():
    kinds[st] += 1
    save_fixture(SEG, f"err_{st}_{kinds[st]}", body)
    print(f"error shape: {st} {m!r} -> err_{st}_{kinds[st]}.json")
print("fixtures: tests/fixtures/bookmarks/", sorted(FIX), "+", len(ERRS), "error shapes")
