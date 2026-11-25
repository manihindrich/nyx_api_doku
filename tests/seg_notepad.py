"""Live GET-only tests for segment `notepad` (Swagger 0.0.1). Writes nothing."""
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nyx import Client, save_fixture, shape  # noqa: E402

SEG = "notepad"
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
    if t == "bool":
        return isinstance(v, bool)
    if t == "dt":
        return isinstance(v, str) and re.match(r"\d{4}-\d{2}-\d{2}T", v) is not None
    if t == "dict":
        return isinstance(v, dict)
    if t == "list":
        return isinstance(v, list)
    raise ValueError(t)


def cmp(obj, spec):
    if not isinstance(obj, dict):
        return [f"not object ({type(obj).__name__})"]
    issues = []
    for k, t in spec.items():
        if k not in obj:
            issues.append(f"missing {k}")
        elif not type_ok(obj[k], t):
            issues.append(f"{k}={type(obj[k]).__name__} (want {t})")
    extra = sorted(set(obj) - set(spec))
    if extra:
        issues.append(f"extra {extra}")
    return issues


ENTRY_FULL = {"id": "int", "category_id": "int?", "title": "str", "content": "str",
              "content_raw": "str", "public": "bool", "sharing_token": "str",
              "inserted_at": "dt", "updated_at": "dt"}
ENTRY_MIN = {"id": "int", "category_id": "int?", "title": "str", "public": "bool",
             "inserted_at": "dt", "updated_at": "dt"}
CATEGORY_GROUP = {"category": "dict", "entries": "list"}   # what the real API returns in `entries`
JSON_ERR = {"error": "bool", "code": "str", "message": "str"}
NOT_FOUND_MSG = "The specified resource was not found"


def ctype(res):
    return next((v for k, v in res.headers.items() if k.lower() == "content-type"), None)


def is_group(e):
    return isinstance(e, dict) and "category" in e and "entries" in e


def flat_entries(body):
    """Entries as the API really returns them: grouped by category (`entries[].entries[]`)."""
    out = []
    for e in body.get("entries") or []:
        if is_group(e):
            out += e["entries"]
        else:
            out.append(e)
    return out


def check_data(body):
    """Issues vs NotepadData; selected_entry may be null, entries may be category groups."""
    issues = []
    if not isinstance(body, dict):
        return [f"not object ({type(body).__name__})"]
    for k in ("context", "selected_entry", "entries"):
        if k not in body:
            issues.append(f"missing {k}")
    if not isinstance(body.get("context"), dict) and "context" in body:
        issues.append("context not object")
    if not isinstance(body.get("entries"), list) and "entries" in body:
        issues.append("entries not list")
    sel = body.get("selected_entry", None)
    if sel is not None and not isinstance(sel, dict):
        issues.append("selected_entry neither null nor object")
    for i, e in enumerate(body.get("entries") or []):
        if is_group(e):
            sub = cmp(e, CATEGORY_GROUP)
            sub += [f"entries[{i}].category: {x}" for x in cmp(e["category"], {"id": "int", "category_name": "str"})]
            for j, x in enumerate(e["entries"]):
                sub += [f"entries[{i}].entries[{j}]: {y}" for y in cmp(x, ENTRY_MIN)]
            issues += [f"entries[{i}]: {x}" for x in sub] if sub else []
        else:
            sub = cmp(e, ENTRY_MIN)
            if sub:
                issues.append(f"entries[{i}]: {sub}")
    return issues


def err_issues(body):
    return cmp(body, JSON_ERR)


# ---------------------------------------------------------------- T-01
r1 = c.call("GET", "/notepad", test_id="T-notepad-01",
            claim="GET /notepad 200: NotepadData {context, selected_entry (null), entries[NotepadEntryMinimal]}; "
                  "'Vrati seznam kategorii s bookmarky - selected_entry je prazdna'")
print("shape(01 body):", shape(r1.body))
flat = []
if r1.status == 200 and isinstance(r1.body, dict):
    issues = check_data(r1.body)
    sel = r1.body.get("selected_entry", "<absent>")
    notes = list(issues)
    if sel is not None:
        notes.append(f"selected_entry not null")
    groups = [e for e in r1.body.get("entries") or [] if is_group(e)]
    notes.append(f"entries are category groups: {len(groups)}/{len(r1.body.get('entries') or [])}")
    notes.append("categories: entries[].category {id,category_name} (not a top-level field)"
                 if groups else "categories: none")
    notes.append(f"entries flat={len(flat_entries(r1.body))}")
    notes.append(f"context keys={list((r1.body.get('context') or {}).keys())}")
    verdict = "DIFF" if (issues or sel is not None or groups) else "OK"
    flat = flat_entries(r1.body)
    emit("T-notepad-01", r1.status, verdict, "; ".join(notes), r1)
else:
    emit("T-notepad-01", r1.status, "FAIL", f"non-200/non-object: {str(r1.body)[:120]}", r1)

# ---------------------------------------------------------------- T-02
r2 = None
if flat:
    eid = flat[0]["id"]
    r2 = c.call("GET", f"/notepad/{eid}", test_id="T-notepad-02",
                claim="GET /notepad/{entry_id} 200: selected_entry filled when entry exists (NotepadEntry)")
    if r2.status == 200 and isinstance(r2.body, dict):
        issues = check_data(r2.body)
        sel = r2.body.get("selected_entry")
        notes = list(issues)
        if not isinstance(sel, dict):
            notes.append("selected_entry null/absent")
        else:
            sub = cmp(sel, ENTRY_FULL)
            if sub:
                notes.append(f"selected_entry: {sub}")
            if sel.get("id") != eid:
                notes.append(f"selected_entry.id={sel.get('id')} != {eid}")
        emit("T-notepad-02", r2.status, "OK" if not notes else "DIFF",
             "; ".join(notes) or f"id={eid} filled", r2)
    else:
        emit("T-notepad-02", r2.status, "FAIL", f"{str(r2.body)[:120]}", r2)
else:
    emit("T-notepad-02", "-", "INFO", "no entries in T-01 (categories empty), skipped")

# ---------------------------------------------------------------- invalid ids
def id_case(tid, path_id, claim):
    r = c.call("GET", f"/notepad/{path_id}", test_id=tid, claim=claim)
    msg = r.body.get("message") if isinstance(r.body, dict) else None
    if r.status == 400:
        iss = err_issues(r.body)
        note = f"JsonError {'ok' if not iss else iss}; message={msg!r}"
        verdict = "OK" if not iss else "DIFF"
        if tid == "T-notepad-03" and msg != NOT_FOUND_MSG:
            verdict = "DIFF"
            note += " (message differs from Swagger)"
    elif r.status == 200:
        verdict = "INFO"
        note = f"200 for id {path_id!r}; keys {list(r.body) if isinstance(r.body, dict) else type(r.body).__name__}"
    elif r.status >= 500:
        verdict, note = "FAIL", f"server error {r.status}"
    else:
        verdict, note = "DIFF", f"status {r.status} (Swagger documents only 200/400)"
    emit(tid, r.status, verdict, note, r)
    return r


id_case("T-notepad-03", 999999999,
        "GET /notepad/{entry_id} 400 JsonError 'The specified resource was not found' for missing id")
id_case("T-notepad-04", 0, "entry_id integer; 0 not a real id; 400 JsonError documented")
id_case("T-notepad-05", -1, "entry_id integer; -1 negative; 400 JsonError documented")
id_case("T-notepad-06", "abc", "entry_id integer; non-integer string; 400 JsonError documented")

# ---------------------------------------------------------------- auth
r7 = c.call("GET", "/notepad", auth=False, test_id="T-notepad-07",
            claim="undocumented: GET /notepad without Authorization header (Swagger lists no 401)")
r8 = c.call("GET", "/notepad", auth="invalidtoken123", test_id="T-notepad-08",
            claim="undocumented: GET /notepad with invalid bearer token (Swagger lists no 401)")
for tid, r in (("T-notepad-07", r7), ("T-notepad-08", r8)):
    if r.status == 200:
        emit(tid, r.status, "INFO", "200 without valid token: data returned, undocumented", r)
    elif r.status == 400:
        iss = err_issues(r.body)
        emit(tid, r.status, "INFO",
             f"400 (no 401 in Swagger); JsonError {'ok' if not iss else iss}; "
             f"message={r.body.get('message') if isinstance(r.body, dict) else r.body!r}", r)
    elif r.status >= 500:
        emit(tid, r.status, "FAIL", f"server error {r.status}", r)
    else:
        emit(tid, r.status, "INFO", f"status {r.status} undocumented", r)

# ---------------------------------------------------------------- T-09 (error body / ctype summary)
errs = [r for _, _, _, _, r in rows if r is not None and r.status >= 400]
bad = [err_issues(r.body) for r in errs if err_issues(r.body)]
ctypes = dict(Counter(ctype(r) for r in errs))
code_types = dict(Counter(type(r.body.get("code")).__name__ for r in errs if isinstance(r.body, dict)))
note = f"error Content-Type {ctypes}; error.code types {code_types}"
if bad:
    emit("T-notepad-09", "-", "DIFF", f"JsonError mismatch: {bad[0]}; {note}")
elif "str" not in code_types and code_types:
    emit("T-notepad-09", "-", "DIFF", f"code is not str; {note}")
else:
    emit("T-notepad-09", "-", "OK", f"error bodies match JsonError; {note}")

# ---------------------------------------------------------------- fixtures
if r1.status == 200:
    save_fixture(SEG, "get_notepad_200", r1.body)
if r2 is not None and r2.status == 200:
    save_fixture(SEG, "get_notepad_id_200", r2.body)
seen = set()
for r in errs:
    key = (r.status, tuple(sorted(r.body)) if isinstance(r.body, dict) else type(r.body).__name__)
    if key in seen:
        continue
    seen.add(key)
    save_fixture(SEG, f"err_{r.status}_{len(seen)}", r.body)

print("counts:", dict(Counter(v for _, _, v, _, _ in rows)))
