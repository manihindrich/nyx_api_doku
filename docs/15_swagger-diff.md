# Swagger vs. reality

Summary of every place where the official [Swagger 0.0.1](https://app.swaggerhub.com/apis/nyx.cz/nyx.cz/0.0.1) differs from the live API (tests 2026-11-25 to 2026-11-27). Details and test IDs are in the linked chapters.

## Across the API

| Swagger | Reality | Chapter |
|---|---|---|
| No authentication scheme, no 401 | Bearer token; 401 in two different body shapes | [Authentication](01_authentication.md), [Errors](11_errors.md#401-unauthorized) |
| Errors are `JsonError {error, code, message}` with status 400 | `code` missing; statuses 400, 401, 403, 404, 422 | [Errors](11_errors.md) |
| Invalid parameter values → 400 | 422 for invalid path values and some query values; many invalid values silently ignored | [Errors](11_errors.md#booleans-and-enums) |
| Boolean and optional fields always present | Omitted when `false` / `0` (except in notifications) | [Models](12_models.md#general-rules) |
| `Activity.status_details` | `Activity.status` | [Models](12_models.md#activity) |
| `format`: `text`, `html` | `markdown` also accepted, stored unconverted | [Mail](04_mail.md), [Discussion](05_discussion.md) |

## Per endpoint

| Endpoint | Swagger | Reality | Chapter |
|---|---|---|---|
| `GET /notepad` | `entries`: flat list of notes | list of categories, each with `entries` | [Notepad](02_notepad.md) |
| `GET /notepad/{id}` | missing note: 400 "resource not found" | 400 `Nepodařilo se načíst kategorie v bloku.`; non-numeric ID 404 | [Notepad](02_notepad.md) |
| `GET /bookmarks/history` | entries have `new_replies_count` | never present | [Bookmarks](03_bookmarks.md) |
| `GET /mail` | `incoming`, `reminder` booleans; `unread`, `new`, `preview` | `true` or missing; the other three never appear; undocumented `other_mail_id` | [Mail](04_mail.md) |
| `POST /mail/reminder/{id}/{state}` | invalid input → 400 | invalid state 422; non-existent ID 200 | [Mail](04_mail.md) |
| `GET /discussion/{id}` | response `{context, posts}` | also `discussion_common`, `presence` | [Discussion](05_discussion.md) |
| `GET /discussion/{id}?rating=n` | "greater than" / "lower than" | ≥ n / ≤ n (inclusive) | [Discussion](05_discussion.md) |
| `GET /discussion/{id}` without token | (not described) | public discussion: 200; others: 400 `Přístup odmítnut.` | [Discussion](05_discussion.md) |
| `POST …/content/{contentId}/save` | saves post text or header section | header sections only | [Discussion](05_discussion.md) |
| `POST /discussion/rights` | `right` incl. `grant_edit_rights`, `public`; `set` required | those two always fail; missing `set` accepted; hierarchy of rights | [Discussion rights](06_discussion_rights.md) |
| `GET /last` | posts are `TemplatePost` | plus `discussion_name`; boolean filters need literal `true` | [Last posts](07_last.md) |
| `GET /notifications` | list in `posts` | list in `notifications` | [Notifications](08_notifications.md) |
| `PUT /file/upload` | 5 MIME types; `thumb_url` string | any file accepted; `thumb_url` may be `null`; extra `image_embed_option` | [Files](09_file.md) |
| `DELETE /file/delete/{id}` | errors → 400 | deleting twice → 200 | [Files](09_file.md) |
| `GET /search/username/{u}` | rows `{user: {…}, activity}`; invalid → 400 | rows `{username, activity}`; invalid → 404 | [Search](10_search.md) |
| `GET /search-v2` | `newer_than` / `older_than` need `from_id` | without it: same as `newest` | [Search](10_search.md) |
| `GET /search/unified` | result is directly one of three schemas | wrapped in `user`, `discussion` or `discussion_post` | [Search](10_search.md) |

## Not verifiable

- `GET /notepad/{id}` with an existing note (the test account has none, the API cannot create one).
- Successful `register_for_notifications` (it requires a real token in the URL).
- `rights` without `username` (global rights).
- Rate limits.
