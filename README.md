<p align="center">
  <img src="assets/nyx-logo.png" alt="nyx" width="120">
</p>

<h1 align="center">NYX.CZ API — verified documentation</h1>

<p align="center">
  A practical, test-backed guide to the <a href="https://nyx.cz">nyx.cz</a> REST API<br>
  for anyone building a bot, a client or an integration.
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#documentation">Chapters</a> ·
  <a href="#five-things-to-know-first">Five things to know</a> ·
  <a href="#tests">Tests</a>
</p>

---

## What is nyx

[nyx.cz](https://nyx.cz) is a long-running Czech online community. At its heart are **discussion clubs** on every topic imaginable, and around them sit private **mail**, **bookmarks** and reading history, **notifications** about replies and ratings, a personal **notepad**, file sharing, events and more.

Besides the web interface, nyx offers a **REST API**: with a personal token you can read discussions, post, send mail, rate posts, manage access rights, upload files and search. That is what bots, alternative and mobile clients, feed readers and other integrations are built on.

## What this repository is for

Building on an API is easier when you know exactly how it behaves: which fields come back, what an error looks like, what happens at the edges. This repository answers those questions for every one of the 33 API operations, in plain chapters with copy-paste examples.

It is written for developers who want to:

- **write a bot or a client** without trial and error,
- **look up** a request, a response shape or an error message quickly,
- **re-check** any statement themselves: each one links to a live test that can be run again.

> [!NOTE]
> This is an independent community project, not official nyx.cz documentation. User names and IDs in the examples are placeholders.

## What you get

- **Verified behaviour.** Every statement was checked against the live API and links to the test that backs it (`[T-mail-22]`). Anything that could not be tested is marked **Not verified**.
- **Real examples.** Requests and responses as the API returns them today.
- **Exact errors.** Status codes and every error message seen, with their causes.
- **Edge cases.** Paging, booleans, duplicates, HTML handling, file uploads, access rights.
- **Practical advice** from running a bot on the API.

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
| [Notes on the spec](docs/15_swagger-diff.md) | where the observed behaviour differs from the published spec |

## Five things to know first

1. **Missing means false in posts.** In post objects, boolean flags and counters are left out when unset; elsewhere `false` and `0` do appear ([Models](docs/12_models.md#general-rules)).
2. **Writes return `{}`.** Find the new post or message ID by reading it back ([Good practice](docs/14_practices.md#writing-posts-and-mail)).
3. **Duplicates are rejected.** A text identical to your previous post or message fails with 400.
4. **Errors are loose.** Many invalid values are ignored with 200; others return 422, not 400 ([Errors](docs/11_errors.md)).
5. **Every `\n` becomes `<br>`**, and URLs are turned into links ([HTML](docs/13_html.md)).

## Tests

The tests are the evidence for the documentation. They run against the live API with a real account and **write** to it, so they are guarded: writes are allowed only to one test discussion, one mail recipient and objects the run created itself (see `ALLOWLIST` in [`tests/nyx.py`](tests/nyx.py)).

Copy [`.env.example`](.env.example) to `.env` (git-ignored) and fill in your token and your own test accounts and discussion. Then:

```bash
python3 -I tests/seg_search.py
```

| Path | Content |
|---|---|
| `tests/nyx.py` | client: auth, pacing (1 request/s), retry, write allowlist, recording |
| `tests/seg_*.py` | one script per chapter; prints `T-id \| status \| verdict` |
| `tests/fixtures/` | shortened sample responses; users, IDs and discussion names replaced by placeholders |
| `tests/results/` | full recorded responses (local only, git-ignored) |
| `tests/models_check.py` | compares response fields with the Swagger schemas |

---

<sub>Unofficial project, not affiliated with nyx.cz. The nyx logo belongs to its owners.</sub>
