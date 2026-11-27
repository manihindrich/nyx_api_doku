# Errors

Collected from all live tests, 2026-11-25 to 2026-11-27. Each row links to a test in `tests/results/` (not committed) and the chapters' test IDs.

## Body shape

Almost all errors look like this:

```json
{ "error": true, "message": "Nepodařilo se uložit práva." }
```

- `message` is in Czech for application errors.
- There is **no `code` field**, except in one 403 [T-file-19].

> [!WARNING]
> **Swagger says** errors are `JsonError` with `error`, `message` and an optional `code`, returned as **400** (plus one **403** with `code: NeedsConfirmation` for rating). In reality `code` is usually missing (it appears only on 403 and in the second 401 shape), and errors use 400, 401, 403, 404 and 422.

## Status codes

| Status | Meaning in practice | Example body |
|---|---|---|
| **400** | Application error: object not found, not allowed, duplicate, invalid state | `{"error": true, "message": "Příspěvek neexistuje."}` |
| **401** | Missing or invalid token | see below |
| **403** | No permission for the target (seen once, on file upload) | `{"error": true, "code": "forbidden", "message": "Nemáte právo tohle upravovat."}` |
| **404** | Path does not match: a non-numeric ID, a missing required query parameter, wrong HTTP method | `{"error": true, "message": "Not Found"}` |
| **422** | Invalid value in a path or query parameter: enum (`action=foo`), boolean (`set=1`), missing required field | `{"error": true, "message": "422"}` |

### 401 Unauthorized

Two shapes were observed:

| Shape | Where | Test |
|---|---|---|
| `{"error": true, "message": "Authorization needed"}` (missing token) or `"Invalid token"` (invalid token) | `GET` endpoints | T-notepad-07, -08; T-last-27, -28; T-mail-14, -15 … |
| `{"error": {"code": 401, "reason": "Unauthorized", "description": "The request requires user authentication."}}` | `POST /discussion/rights/add`, `PUT /file/upload`, `POST /register_for_notifications/…` | T-rights-28, -29; T-file-20, -21; T-notifications-10, -11 |

Check for both when handling 401.

### Booleans and enums

Use only the literal `true` and `false` for booleans. Other values (`1`, `0`, `abc`) return 422 in paths (`/reminder/{id}/1`) and in some query parameters (`rights?set=1`, `bookmark?new_state=abc`), and are silently ignored in list filters (`/api/last?rated_by_me=1`) [T-discussion-60, T-rights-18, T-discussion-79, T-last-24].

### Invalid values that do **not** cause an error

Many invalid inputs are ignored and return 200 with default behaviour:

- unknown `order` or invalid `from_id` in mail, discussion and search paging [T-mail-11…13, T-discussion-17…19, T-search-50…53]
- unknown `domain`, `min_rating`, `expand`, `limit` values [T-last-07, -16; T-bookmarks-04…06; T-search-64]
- reminder on a non-existent mail ID [T-mail-28, -29]
- deleting an already deleted file [T-file-33]

Do not rely on errors to validate your input.

## Application error messages

| Message | Endpoint | Cause | Test |
|---|---|---|---|
| `Nepodařilo se načíst diskuzi.` | `GET /discussion/{id}` | discussion does not exist | T-discussion-97 |
| `Přístup odmítnut.` | `GET /discussion/{id}` | no token for a non-public discussion | T-discussion-23 |
| `Nepodařilo se odeslat příspěvek.` | `POST /discussion/{id}/send/text` | empty content or same text as the previous post | T-discussion-29, -31 |
| `Nejspíš jde o omylem dvojitě posílanou zprávu.` | `POST /mail/send` | same text as the previous message | T-mail-22 |
| `Nelze odeslat prázdnou zprávu.` | `POST /mail/send` | empty message | T-mail-20 |
| `Příspěvek neexistuje.` | `DELETE /discussion/{id}/delete/{post}` | post does not exist | T-discussion-88 |
| `Nemůžete označit vlastní příspěvky.` | `POST …/rating/{post}/{action}` | rating one's own post | T-discussion-37 |
| `Nepodařilo se načíst příspěvek.` | `POST …/rating/{post}/{action}` | post does not exist | T-discussion-54 |
| `Nepodařilo se uložit upomínku.` | `POST …/reminder/{post}/{state}` | post does not exist | T-discussion-64, -66 |
| `Nelze vypnout sledování u vlastní diskuze.` | `…/bookmark?new_state=false` | own discussion | T-discussion-68 |
| `Nepodařilo se uložit do sledovaných.` | `…/bookmark?category=…` | invalid category | T-discussion-77 |
| `Nepodařilo se uložit obsah.` | `POST …/content/{id}/save` | not a header section | T-discussion-33, -34 |
| `Nepodařilo se uložit práva.` | `POST` / `DELETE /discussion/rights` | user not in the list, or `grant_edit_rights` / `public` | T-rights-13…16, -32, -33 |
| `Uživatel již má uživatelská práva nastavená.` | `POST /discussion/rights/add` | user already in the list | T-rights-26 |
| `Nepodařilo se načíst kategorie v bloku.` | `GET /notepad/{id}` | note does not exist | T-notepad-03 |
| `Chybné hledání.` | `GET /search/unified` | `@` with a 2-character nickname | T-search-66 |
| `Nepodařilo se načíst token.` (404) | `POST /register_for_notifications/…` | unknown token in the path | T-notifications-04 |
| `Nemáte právo tohle upravovat.` (403) | `PUT /file/upload` | `id_specific` of a discussion the user cannot edit | T-file-19 |

## Rate limiting

No 429 response was observed. The tests sent about one request per second.

> [!CAUTION]
> **Not verified:** rate limits. They were not probed on purpose.
