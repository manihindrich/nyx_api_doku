<p align="center">
  <img src="assets/nyx-logo.png" alt="nyx" width="120">
</p>

<h1 align="center">NYX.CZ API — verified documentation</h1>

<p align="center">
  Unofficial documentation of the <a href="https://nyx.cz">nyx.cz</a> REST API.<br>
  Every statement is checked against the live API, not copied from the spec.
</p>

---

## Why

The official [Swagger 0.0.1](https://app.swaggerhub.com/apis/nyx.cz/nyx.cz/0.0.1) is incomplete and wrong in many places. This repository describes what the API **actually does**. Each claim links to a live test (`[T-mail-22]`), and every place where reality differs from Swagger is marked **Swagger says** and summarised in [Swagger vs. reality](docs/15_swagger-diff.md). Anything that could not be tested is marked **Not verified**.

Tested 2026-11-25 to 2026-11-27: 414 recorded live requests covering all 33 operations.

## Quick start

1. Create an API token in your nyx.cz account settings.
2. Call the API with it:

```bash
export NYX_API_TOKEN="…"
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" "https://nyx.cz/api/mail?order=newest"
```

Base URL: `https://nyx.cz/api`. Responses are JSON.

## Documentation

| Chapter | Endpoints |
|---|---|
| [Authentication](docs/01_authentication.md) | token, requests without a token |
| [Notepad](docs/02_notepad.md) | `GET /notepad`, `/notepad/{id}` |
| [Bookmarks and history](docs/03_bookmarks.md) | `/bookmarks`, `/bookmarks/all`, `/bookmarks/history…` |
| [Mail](docs/04_mail.md) | `GET /mail`, `/mail/send`, `/mail/reminder` |
| [Discussion](docs/05_discussion.md) | read, post, delete, rating, reminder, bookmark, header |
| [Discussion rights](docs/06_discussion_rights.md) | `/discussion/rights`, `/rights/add` |
| [Last posts](docs/07_last.md) | `GET /last` |
| [Notifications](docs/08_notifications.md) | `GET /notifications`, `register_for_notifications` |
| [Files](docs/09_file.md) | upload, embed, delete, attachments |
| [Search](docs/10_search.md) | users, posts, unified search, search expressions |
| [Errors](docs/11_errors.md) | status codes and all error messages seen |
| [Models](docs/12_models.md) | shared objects and field rules |
| [HTML](docs/13_html.md) | which HTML is kept, changed or removed |
| [Good practice](docs/14_practices.md) | lessons from running a bot on the API |
| [Swagger vs. reality](docs/15_swagger-diff.md) | all differences in one place |

## Five things to know first

1. **Missing means false.** Boolean flags and counters are left out when unset ([Models](docs/12_models.md#general-rules)).
2. **Writes return `{}`.** Find the new post or message ID by reading it back ([Good practice](docs/14_practices.md#writing-posts-and-mail)).
3. **Duplicates are rejected.** A text identical to your previous post or message fails with 400.
4. **Errors are loose.** Many invalid values are ignored with 200; others return 422, not 400 ([Errors](docs/11_errors.md)).
5. **Every `\n` becomes `<br>`**, and URLs are turned into links ([HTML](docs/13_html.md)).

## Tests

The tests are the evidence for the documentation. They run against the live API with a real account and **write** to it, so they are guarded: writes are allowed only to one test discussion, one mail recipient and objects the run created itself (see `ALLOWLIST` in [`tests/nyx.py`](tests/nyx.py)).

```bash
# token from the environment or from a .env file (never commit it)
NYX_ENV_FILE=/path/to/.env python3 -I tests/seg_search.py
```

| Path | Content |
|---|---|
| `tests/nyx.py` | client: auth, pacing (1 request/s), retry, write allowlist, recording |
| `tests/seg_*.py` | one script per chapter; prints `T-id \| status \| verdict` |
| `tests/fixtures/` | shortened sample responses, other users anonymised |
| `tests/results/` | full recorded responses (local only, git-ignored) |
| `tests/models_check.py` | compares response fields with the Swagger schemas |

Before running write tests, change the allowlist to your own test discussion and recipient.

---

<sub>Unofficial project, not affiliated with nyx.cz. The nyx logo belongs to its owners.</sub>
