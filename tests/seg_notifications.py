"""Live tests for segment `notifications` (Swagger 0.0.1).

GET /notifications is read-only. POST /register_for_notifications uses only fake
path tokens (`nyxapidoku-test-*`); the real token travels only in the Bearer header.
"""
import re
import secrets
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nyx import Client, save_fixture, shape  # noqa: E402

SEG = "notifications"
c = Client(SEG)
rows = []          # (tid, status, verdict, note, Result|None)
TYPES = {"dict": dict, "list": list, "str": str}


def emit(tid, status, verdict, note, res=None):
    rows.append((tid, status, verdict, note, res))
    print(f"{tid} | {status} | {verdict} | {note}")


def short(body):
    return str(body)[:120]


def cmp(obj, spec, required=()):
    """Compare dict against {key: type}; list missing required, wrong types, extras."""
    if not isinstance(obj, dict):
        return [f"not object ({type(obj).__name__})"]
    issues = [f"missing {k}" for k in required if k not in obj]
    issues += [f"{k}={type(obj[k]).__name__} (want {t})"
               for k, t in spec.items() if k in obj and not isinstance(obj[k], TYPES[t])]
    extra = sorted(set(obj) - set(spec))
    if extra:
        issues.append(f"extra {extra}")
    return issues


# Notification = {details: NotificationDetails{thumbs_up, replies}, type: enum["post"], data}
NOTIF_SPEC = {"details": "dict", "type": "str", "data": "dict"}
DETAILS_SPEC = {"thumbs_up": "list", "replies": "list"}
NOTIF_ENUM = {"post"}

# ---------------------------------------------------------------- T-01 shape
r1 = c.call("GET", "/notifications", test_id="T-notifications-01",
            claim="GET /notifications 200: object {context, notifications[Notification]} required; "
                  "'Seznam notifikaci' (listed property is posts[Notification])")
print("shape(01 body):", shape(r1.body, max_depth=4))
if r1.status == 200 and isinstance(r1.body, dict):
    b = r1.body
    issues = []
    if "notifications" not in b:
        issues.append(f"no 'notifications' key; top keys={sorted(b)}")
    if "posts" in b:
        issues.append("list under 'posts' (schema requires 'notifications')")
    if "context" not in b:
        issues.append("missing context")
    lst = b.get("notifications", b.get("posts")) or []
    items = [n for n in lst if isinstance(n, dict)] if isinstance(lst, list) else []
    item_issues, det_issues = set(), set()
    for n in items:
        item_issues |= set(cmp(n, NOTIF_SPEC, NOTIF_SPEC.keys()))
        if isinstance(n.get("details"), dict):
            det_issues |= set(cmp(n["details"], DETAILS_SPEC, DETAILS_SPEC.keys()))
    types = Counter(n.get("type") for n in items)
    detail_keys = sorted({k for n in items if isinstance(n.get("details"), dict) for k in n["details"]})
    data_keys = sorted({k for n in items if isinstance(n.get("data"), dict) for k in n["data"]})
    if set(types) - NOTIF_ENUM:
        issues.append(f"type outside enum: {sorted(map(str, set(types) - NOTIF_ENUM))}")
    note = (f"list={'notifications' if 'notifications' in b else 'posts'} n={len(items)}; "
            f"types={dict(types)}; details keys={detail_keys}; data keys={data_keys[:12]}")
    if issues or item_issues or det_issues:
        note += f"; issues={sorted(issues + sorted(item_issues) + sorted(det_issues))[:6]}"
        emit("T-notifications-01", 200, "DIFF", note, r1)
    elif not items:
        emit("T-notifications-01", 200, "INFO", "empty list; item shape unverified; " + note, r1)
    else:
        emit("T-notifications-01", 200, "OK", note, r1)
else:
    emit("T-notifications-01", r1.status, "FAIL" if r1.status >= 500 else "INFO",
         f"non-200: {short(r1.body)}", r1)

# ---------------------------------------------------------------- auth on GET
r2 = c.call("GET", "/notifications", auth=False, test_id="T-notifications-02",
            claim="undocumented: GET /notifications without Authorization header (no 401 in Swagger)")
r3 = c.call("GET", "/notifications", auth="invalidtoken123", test_id="T-notifications-03",
            claim="undocumented: GET /notifications with invalid bearer token (no 401 in Swagger)")
for tid, r in (("T-notifications-02", r2), ("T-notifications-03", r3)):
    if r.status >= 500:
        emit(tid, r.status, "FAIL", f"server error: {short(r.body)}", r)
    elif r.status == 200:
        emit(tid, 200, "INFO", f"200 without valid token, n={len(r.body.get('notifications', r.body.get('posts', [])) or []) if isinstance(r.body, dict) else '?'}; undocumented", r)
    else:
        emit(tid, r.status, "INFO", f"undocumented {r.status}; body={short(r.body)}", r)

# ---------------------------------------------------------------- register_for_notifications
FAKE = f"nyxapidoku-test-{secrets.token_hex(3)}"     # fake path token, never the real one
HEX64 = secrets.token_hex(32)                        # 64 chars (apns-like)
TOK140 = secrets.token_hex(70)                       # 140 chars (firebase-like)
REG_CLAIM = ("POST /register_for_notifications/{token}/{client}/{client_token} 200: "
             "'Zaregistruje dany device pro prijem notifikaci'; client enum nyx|fyx|nyxdroid; "
             "400 undocumented")


def reg(tid, client, ctok, method="POST", auth=True, expect_ok=True, what=""):
    path = f"/register_for_notifications/{FAKE}/{client}/{ctok}"
    r = c.call(method, path, auth=auth, test_id=tid, claim=REG_CLAIM + f" [{what}]")
    note = f"{what}; len(client_token)={len(ctok)}"
    if r.status >= 500:
        emit(tid, r.status, "FAIL", f"server error: {short(r.body)}; {note}", r)
    elif r.status == 200:
        if expect_ok:
            emit(tid, 200, "OK", f"documented 200 (fake token); {note}; registration may persist, "
                 "no removal endpoint in Swagger", r)
        else:
            emit(tid, 200, "DIFF", f"invalid input accepted with 200; {note}", r)
    else:
        emit(tid, r.status, "INFO", f"undocumented {r.status}; {note}; body={short(r.body)}", r)
    return r


reg("T-notifications-04", "nyx", HEX64, what="client=nyx, 64-char token, Bearer")
reg("T-notifications-05", "fyx", TOK140, what="client=fyx, 140-char token, Bearer")
reg("T-notifications-06", "nyxdroid", TOK140, what="client=nyxdroid, 140-char token, Bearer")
reg("T-notifications-07", "foo", TOK140, expect_ok=False, what="client=foo (outside enum)")
reg("T-notifications-08", "nyx", "x", expect_ok=False, what="client_token='x' (too short)")
reg("T-notifications-09", "nyx", HEX64, method="GET", expect_ok=False,
    what="GET instead of POST (Swagger: POST only)")
reg("T-notifications-10", "nyx", HEX64, auth=False, expect_ok=False,
    what="no Authorization header, fake path token")
reg("T-notifications-11", "nyx", HEX64, auth="invalidtoken123", expect_ok=False,
    what="invalid Authorization header, fake path token")

# ---------------------------------------------------------------- after-state checks (read-only)
r12 = c.call("GET", "/notifications", test_id="T-notifications-12",
             claim="GET /notifications after register calls: any change vs T-01?")
if r12.status == 200 and isinstance(r12.body, dict) and isinstance(r1.body, dict):
    l12 = r12.body.get("notifications", r12.body.get("posts")) or []
    l01 = r1.body.get("notifications", r1.body.get("posts")) or []
    same = len(l12) == len(l01) and [sorted(n) for n in l12] == [sorted(n) for n in l01]
    emit("T-notifications-12", 200, "INFO",
         f"n before={len(l01)} after={len(l12)}; same count/keys={same}", r12)
else:
    emit("T-notifications-12", r12.status, "INFO", f"status {r12.status}; body={short(r12.body)}", r12)

r13 = c.call("GET", "/notepad", test_id="T-notifications-13",
             claim="undocumented: GET /notepad context.user scanned for device/push registration fields "
                   "(record only)")
if r13.status == 200 and isinstance(r13.body, dict):
    user = (r13.body.get("context") or {}).get("user") or {}
    hits = sorted(k for k in user if re.search(r"device|push|notif|firebase|apns|fcm", k, re.I))
    emit("T-notifications-13", 200, "INFO",
         f"context.user keys={sorted(user)}; registration-like keys={hits or 'none'}", r13)
else:
    emit("T-notifications-13", r13.status, "INFO", f"status {r13.status}; body={short(r13.body)}", r13)

# ---------------------------------------------------------------- fixtures
if r1.status == 200:
    save_fixture(SEG, "get_notifications_200", r1.body)
seen = set()
for tid, status, _, _, r in rows:
    if r is None or tid in ("T-notifications-01", "T-notifications-12", "T-notifications-13"):
        continue
    key = (status, tuple(sorted(r.body)) if isinstance(r.body, dict) else type(r.body).__name__)
    if key in seen:
        continue
    seen.add(key)
    save_fixture(SEG, f"{tid[-2:]}_{status}", r.body)

print("counts:", dict(Counter(v for _, _, v, _, _ in rows)))
