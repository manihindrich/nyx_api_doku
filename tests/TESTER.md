# Tester brief (template for segment test agents)

You test one segment of the nyx.cz API live and record results. You do **not** write documentation.

## Setup
- Repo: this repository. Write only `tests/seg_<segment>.py` and `tests/fixtures/<segment>/`.
- Harness: `tests/nyx.py` (read it first). Use `Client("<segment>")`, `c.call(method, path, params=, data=, files=, auth=, test_id=, claim=)`, `save_fixture()`, `shape()`, `nonce()`.
- Run: `python3 -I tests/seg_<segment>.py` from the repo root (token and test account values in `.env`, see `.env.example`)
  (Bash tool: pass `allowed_domains: ["nyx.cz"]`). Never print, log or commit the token.
- The guard in `nyx.py` blocks writes outside the allowlist. If it raises `Forbidden`, do **not** work around it; report it.

## Rules
- One `test_id` per case: `T-<segment>-NN`. Every case has a `claim` = the exact Swagger statement it checks (or "undocumented: …").
- Cover: every parameter, every enum value, boundary values (0, -1, huge, wrong type), missing required params, no token, invalid token.
- Writes: always include `nonce()` in written text; register created objects in `c.created` and remove them in `finally`.
- Script prints one line per case: `T-id | status | verdict | note`, verdict ∈ `OK` (matches Swagger), `DIFF` (differs), `FAIL` (broken/unexpected), `INFO` (undocumented behaviour).
- Save 1 fixture per distinct successful response shape (`save_fixture(segment, name, body)`) and 1 per distinct error shape.
- Compare response structure to the Swagger schema given in the brief: list missing fields, extra fields, wrong types, nullability.

## Report (≤ 15 lines, nothing else)
1. Command run + count of cases per verdict.
2. Each DIFF/FAIL/INFO in one line: `T-id: what Swagger says → what really happens`.
3. Fixtures saved (file names).
4. Anything you could not test and why.
