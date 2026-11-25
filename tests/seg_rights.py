"""Live tests for segment `rights` (Swagger 0.0.1). Writes only to access rights of BOD in discussion 288360 (guard-enforced).
BOD's rights are restored in `finally` and verified against the step-0 baseline."""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from http.client import IncompleteRead  # noqa: E402
from nyx import Client, Forbidden, Result, save_fixture  # noqa: E402

SEG = "rights"
DISC = 288360            # "NYXOT ~ testing NYX API" (owner NYXOT): the only discussion written to
BOD = "BOD"              # the only user whose rights are written
RSS = "RSS"              # guard case only (must be Forbidden)
OTHER_DISC = 18379       # guard case only (must be Forbidden)
DP = f"/discussion/{DISC}"
RR = "/discussion/rights"
RADD = "/discussion/rights/add"
RIGHTS = ["read", "write", "delete", "edit", "edit_rights", "grant_edit_rights", "public"]
# DiscussionAccessRight field per right; grant_edit_rights and public have no ar_* field there.
FIELD = {"read": "ar_read", "write": "ar_write", "delete": "ar_delete", "edit": "ar_edit", "edit_rights": "ar_rights"}
# grant_edit_rights never appears in any response. Brief says BOD has ALL rights -> assumed True.
GRANT_ASSUMED = True

c = Client(SEG)
rows = []                # (tid, status, verdict, note)
_n = [0]
FIX = {}                 # fixture name -> first successful body
ERRS = {}                # (status, message) -> first error body of that kind
BASELINE = None          # BOD's DiscussionAccessRight body from step 0
BASE_PUBLIC = None       # discussion.public from step 0
STARTED = False          # destructive calls begun -> restore required
FINAL = None             # Result of final no-op verification call
FINAL_PUBLIC = None
PUBLIC_CHANGED = []


# Swagger shapes. "x?" = nullable.
def type_ok(v, t):
    if t.endswith("?") and v is None:
        return True
    base = t.rstrip("?")
    if base == "int":
        return isinstance(v, int) and not isinstance(v, bool)
    if base == "str":
        return isinstance(v, str)
    if base == "bool":
        return isinstance(v, bool)
    raise ValueError(t)


def cmp(obj, spec, required=()):
    """-> (issues, extra keys). spec = {field: type}; `required` fields must be present."""
    if not isinstance(obj, dict):
        return [f"not object ({type(obj).__name__})"], []
    issues = [f"missing {k}" for k in required if k not in obj]
    issues += [f"{k}={type(v).__name__} (want {spec[k]})"
               for k, v in obj.items() if k in spec and not type_ok(v, spec[k])]
    return issues, sorted(set(obj) - set(spec))


ACC_SPEC = {"discussion_id": "int", "ar_read": "bool", "ar_write": "bool", "ar_delete": "bool",
            "ar_edit": "bool", "ar_rights": "bool", "days_left": "int"}
GLOBAL_SPEC = {"read": "bool", "write": "bool", "delete": "bool", "edit": "bool", "public": "bool"}
JSON_ERR = {"error": "bool", "code": "str?", "message": "str"}

GET_CLAIM = ("GET /discussion/{discussionId} 200 {context, discussion_common {discussion.public bool, access_right}, "
             "posts, presence}")
SET_CLAIM = ("POST /discussion/rights query discussion_id int>=1 req, username optional, right AccessRightType "
             "(read|write|delete|edit|edit_rights|grant_edit_rights|public) req, set boolean req; 'Nastavi uzivateli "
             "(nebo globalne) pravo na novou hodnotu'; 200 'Successfully updated access right and returned new state' "
             "oneOf DiscussionAccessRight|DiscussionGlobalRights; 400 JsonError")
ADD_CLAIM = ("POST /discussion/rights/add query discussion_id int>=1 req, username req; 'Prida uzivatele do "
             "uzivatelskych prav'; 200 JsonOk {}; 400 JsonError")
DEL_CLAIM = ("DELETE /discussion/rights query discussion_id int>=1 req, username req; 'Odebere uzivateli vsechna "
             "prava v diskuzi'; 200 JsonOk {}; 400 JsonError")
AUTH_CLAIM = "POST /discussion/rights/add: undocumented auth behaviour (no 401 in Swagger); token required"
FORM_CLAIM = "POST /discussion/rights: parameters documented as query string (in: query); form body undocumented"


def b(v):
    return "true" if v else "false"


def pset(right, val, username=BOD, disc=DISC):
    p = {"discussion_id": str(disc), "right": right, "set": val}
    if username is not None:
        p["username"] = username
    return p


def padd(username=BOD, disc=DISC):
    return {"discussion_id": str(disc), "username": username}


def brief(r):
    s = r.body if isinstance(r.body, str) else json.dumps(r.body, ensure_ascii=False)
    return f"{r.status} {s[:160]}"


def public_of(r):
    try:
        return r.body["discussion_common"]["discussion"]["public"]
    except (KeyError, TypeError):
        return None


def either(body):
    """-> ('access'|'global'|None, extra keys) for the oneOf of the 200 response."""
    ia, ea = cmp(body, ACC_SPEC, tuple(ACC_SPEC))
    if not ia:
        return "access", ea
    ig, eg = cmp(body, GLOBAL_SPEC, tuple(GLOBAL_SPEC))
    if not ig:
        return "global", eg
    return None, ia


def state_of(body, right):
    if not isinstance(body, dict):
        return None
    if right == "public":
        return body.get("public")
    return body.get(FIELD.get(right, "-"))


# ---------------------------------------------------------------- judges: (Result) -> (verdict, note)
def j_get(r):
    if r.status != 200 or not isinstance(r.body, dict):
        return "FAIL", brief(r)
    pub = public_of(r)
    if pub is None:
        return "DIFF", "discussion_common.discussion.public missing"
    dc = r.body.get("discussion_common") if isinstance(r.body.get("discussion_common"), dict) else {}
    return "OK", f"discussion.public={pub}; access_right={json.dumps(dc.get('access_right'))}"


def j_set(right, want):
    def j(r):
        if r.status != 200:
            return "FAIL", f"set {right}={b(want)} not 200: {brief(r)}"
        kind, extra = either(r.body)
        if kind is None:
            return "DIFF", f"200 body matches neither oneOf schema: {brief(r)}"
        note = f"{kind} schema" + (f"; extra keys {extra}" if extra else "")
        got = state_of(r.body, right)
        if got is None:
            return "INFO", f"{note}; {right} not in response, state not verified"
        if got != want:
            return "DIFF", f"requested {right}={b(want)}, response {right}={got}"
        return "OK", f"{note}; {right}={got}"
    return j


def j_err(codes):
    def j(r):
        if r.status in codes:
            iss, _ = cmp(r.body, JSON_ERR, ("error", "message"))
            return ("DIFF" if iss else "OK"), brief(r) + (f"; {iss}" if iss else "")
        if r.status == 200:
            return "DIFF", f"200 accepted, Swagger documents only {codes}: {brief(r)}"
        if r.status >= 500:
            return "FAIL", brief(r)
        return "INFO", f"undocumented status {r.status}: {brief(r)}"
    return j


def j_ok(r):
    if r.status == 200:
        return ("OK", "200 {} (JsonOk)") if r.body == {} else ("DIFF", f"200 body is not {{}}: {brief(r)}")
    return j_err((400,))(r)


def j_info(r):
    if r.status >= 500:
        return "FAIL", brief(r)
    return "INFO", brief(r)


def j_auth(r):
    if r.status == 200:
        return "DIFF", f"accepted without valid token: {brief(r)}"
    if r.status >= 500:
        return "FAIL", brief(r)
    return "INFO", f"status {r.status}: {brief(r)}"


def j_same(base):
    def j(r):
        if r.status != 200:
            return "FAIL", brief(r)
        if r.body == base:
            return "OK", "body equals BASELINE"
        keys = sorted(set(base) | set(r.body)) if isinstance(r.body, dict) else []
        diff = [k for k in keys if (r.body or {}).get(k) != base.get(k)]
        return "DIFF", f"body differs from BASELINE in {diff}: {brief(r)}"
    return j


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


def get_public(label):
    box = {}

    def j(r):
        box["pub"] = public_of(r)
        return j_get(r)
    req(label, "GET", DP, GET_CLAIM, j)
    return box.get("pub")


def target(right):
    if right == "public":
        return BASE_PUBLIC
    if right == "grant_edit_rights":
        return GRANT_ASSUMED
    return BASELINE[FIELD[right]]


def check_public(label):
    pub = get_public(f"{label} GET discussion.public")
    if pub is None or pub == BASE_PUBLIC:
        return
    PUBLIC_CHANGED.append(f"{label}: {BASE_PUBLIC} -> {pub}")
    print(f"!!! PUBLIC CHANGED from baseline {BASE_PUBLIC} to {pub} ({label}); reverting now")
    req(f"{label} REVERT public set={b(BASE_PUBLIC)}", "POST", RR, SET_CLAIM,
        j_set("public", BASE_PUBLIC), params=pset("public", b(BASE_PUBLIC)))
    if get_public(f"{label} verify public after revert") != BASE_PUBLIC:
        print("!!! REVERT DID NOT RESTORE discussion.public")


# ---------------------------------------------------------------- steps
def step1():
    for right in RIGHTS:
        for val in (False, True):
            req(f"S1 {right} set={b(val)}", "POST", RR, SET_CLAIM, j_set(right, val),
                params=pset(right, b(val)))
        if right == "public":
            check_public("S1 after public calls")


def step2():
    req("V1 set=1 right=read", "POST", RR, SET_CLAIM, j_info,
        params={"discussion_id": str(DISC), "username": BOD, "right": "read", "set": "1"})
    req("V2 set=0 right=write", "POST", RR, SET_CLAIM, j_info,
        params={"discussion_id": str(DISC), "username": BOD, "right": "write", "set": "0"})
    req("V2b restore write set=true", "POST", RR, SET_CLAIM, j_set("write", True),
        params=pset("write", "true"))
    req("V3 set=abc right=read", "POST", RR, SET_CLAIM, j_info,
        params={"discussion_id": str(DISC), "username": BOD, "right": "read", "set": "abc"})
    req("V4 right=foo", "POST", RR, SET_CLAIM, j_err((400,)),
        params={"discussion_id": str(DISC), "username": BOD, "right": "foo", "set": "true"})
    req("V5 right missing", "POST", RR, SET_CLAIM, j_err((400,)),
        params={"discussion_id": str(DISC), "username": BOD, "set": "true"})
    req("V6 set missing", "POST", RR, SET_CLAIM, j_err((400,)),
        params={"discussion_id": str(DISC), "username": BOD, "right": "read"})
    req("V7 form body (data=) POST rights", "POST", RR, FORM_CLAIM, j_info,
        data=pset("read", "true"))
    req("V8 rights/add BOD (already listed)", "POST", RADD, ADD_CLAIM, j_ok,
        params=padd(), fix="add_200")
    req("V9 rights/add form body (data=)", "POST", RADD, FORM_CLAIM, j_info, data=padd())
    req("V10 rights/add no token", "POST", RADD, AUTH_CLAIM, j_auth, params=padd(), auth=False)
    req("V11 rights/add invalid token", "POST", RADD, AUTH_CLAIM, j_auth, params=padd(),
        auth="invalid-nyxapidoku-token")
    req("V12 state after V8-V11: read=true no-op", "POST", RR, SET_CLAIM, j_same(BASELINE),
        params=pset("read", "true"))


def step3():
    req("D1 DELETE rights BOD", "DELETE", RR, DEL_CLAIM, j_ok, params=padd(), fix="delete_200")
    req("D2 DELETE BOD again", "DELETE", RR, DEL_CLAIM, j_info, params=padd())
    req("D3 POST rights read=true (BOD removed)", "POST", RR, SET_CLAIM, j_err((400,)),
        params=pset("read", "true"))
    req("D4 GET discussion after removal", "GET", DP, GET_CLAIM, j_get)


def guards():
    guarded("G1 username omitted (global rights)", "POST", RR, SET_CLAIM,
            params={"discussion_id": str(DISC), "right": "read", "set": "true"})
    guarded("G2 username=RSS", "POST", RR, SET_CLAIM, params=pset("read", "true", username=RSS))
    guarded("G3 discussion_id=18379", "POST", RR, SET_CLAIM, params=pset("read", "true", disc=OTHER_DISC))


def restore():
    global FINAL, FINAL_PUBLIC
    if not STARTED:
        print("RESTORE: no destructive call was made, nothing to restore")
        return
    if BASELINE is None or BASE_PUBLIC is None:
        print("RESTORE IMPOSSIBLE: no baseline captured")
        return
    req("R1 rights/add BOD (re-add)", "POST", RADD, ADD_CLAIM, j_ok, params=padd())
    for right in RIGHTS:
        want = target(right)
        req(f"R2 set {right}={b(want)}", "POST", RR, SET_CLAIM, j_set(right, want),
            params=pset(right, b(want)))
    FINAL_PUBLIC = get_public("R3 GET discussion.public")
    FINAL = req("R4 final no-op read=baseline", "POST", RR, SET_CLAIM, j_same(BASELINE),
                params=pset("read", b(BASELINE["ar_read"])))


def report_final():
    print("\n=== BASELINE vs FINAL (BOD in discussion %d) ===" % DISC)
    print("BASELINE:", json.dumps(BASELINE, ensure_ascii=False, sort_keys=True))
    fb = FINAL.body if FINAL is not None else None
    print("FINAL   :", json.dumps(fb, ensure_ascii=False, sort_keys=True))
    for k in sorted(set(BASELINE or {}) | set(fb or {})):
        bv, fv = (BASELINE or {}).get(k, "<absent>"), (fb or {}).get(k, "<absent>")
        print(f"  {k:<14} base={str(bv):<9} final={str(fv):<9} {'same' if bv == fv else 'DIFF'}")
    eq = FINAL is not None and FINAL.status == 200 and fb == BASELINE
    print("equal:", "yes" if eq else "no")
    print("discussion.public before:", BASE_PUBLIC, "| after:", FINAL_PUBLIC,
          "| changed during run:", PUBLIC_CHANGED or "no")


try:
    g0 = req("B0 GET discussion", "GET", DP, GET_CLAIM, j_get)
    BASE_PUBLIC = public_of(g0)
    b0 = req("B0 POST rights read=true (no-op = BASELINE)", "POST", RR, SET_CLAIM,
             j_set("read", True), params=pset("read", "true"), fix="post_200_access")
    if b0.status == 200 and either(b0.body)[0] == "access":
        BASELINE = b0.body
    if BASELINE is None or BASE_PUBLIC is None:
        print("no usable baseline: destructive steps skipped")
    else:
        STARTED = True
        step1()
        step2()
        step3()
    guards()
finally:
    restore()
    if BASELINE is not None:
        report_final()

print("counts:", dict(Counter(v for _, _, v, _ in rows)))
for name, body in FIX.items():
    save_fixture(SEG, name, body)
for i, (_, body) in enumerate(ERRS.items(), 1):
    save_fixture(SEG, f"err_{i}", body)
print("fixtures: tests/fixtures/rights/ (", sorted(FIX), "+", len(ERRS), "error shapes )")
