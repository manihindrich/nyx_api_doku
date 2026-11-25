# Notepad

Read-only access to the user's personal notepad. The API has no endpoints to create, edit or delete notes.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/notepad` | List notes grouped by category |
| `GET` | `/api/notepad/{entry_id}` | Same list plus one selected note |

Verification: live tests in [`tests/seg_notepad.py`](../tests/seg_notepad.py), 2026-11-25. Test IDs are in brackets.

---

## GET /api/notepad

No parameters.

```bash
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" https://nyx.cz/api/notepad
```

**200** `application/json` [T-notepad-01]

```json
{
  "context": { "user": { "username": "NYXOT", "mail_unread": 0, "mail_last_from": "RSS",
                         "notifications_unread": 0, "notifications_last_visit": "2025-07-29T12:47:28" },
               "active_friends": [] },
  "selected_entry": null,
  "entries": [
    { "category": { "id": -1, "category_name": "nezařazené poznámky" }, "entries": [] }
  ]
}
```

- `context` is the common context object, see [Models](12_models.md).
- `selected_entry` is always `null` here.
- `entries` is a list of **categories**, each with its own `entries` list. Uncategorised notes are in the category with `id: -1`. The `-1` category is returned even when it is empty.

> [!WARNING]
> **Swagger says** `entries` is a flat array of `NotepadEntryMinimal`. In reality it is an array of `{category: {id, category_name}, entries: [...]}`.

Fixture: [`tests/fixtures/notepad/get_notepad_200.json`](../tests/fixtures/notepad/get_notepad_200.json)

---

## GET /api/notepad/{entry_id}

| Parameter | In | Type | Required |
|---|---|---|---|
| `entry_id` | path | integer | yes |

```bash
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" https://nyx.cz/api/notepad/12345
```

**200**: per Swagger, the same body as `GET /api/notepad`, with `selected_entry` set to the note.

> [!CAUTION]
> **Not verified.** The test account has no notes and the API cannot create one. Swagger's `NotepadEntry` has the fields `id, category_id, title, content, content_raw, public, sharing_token, inserted_at, updated_at`.

**Errors**

| Input | Status | Body | Test |
|---|---|---|---|
| non-existent ID (`999999999`), `0`, `-1` | 400 | `{"error": true, "message": "Nepodařilo se načíst kategorie v bloku."}` | T-notepad-03, -04, -05 |
| non-numeric ID (`abc`) | 404 | `{"error": true, "message": "Not Found"}` | T-notepad-06 |

> [!WARNING]
> **Swagger says** a missing note returns 400 "The specified resource was not found" in `JsonError` with a `code` field. In reality the message is the Czech text above and there is no `code`. Swagger does not list 404.

---

## Authentication errors

Both endpoints return **401**. Swagger does not document 401. See [Errors](11_errors.md).

| Token | Body | Test |
|---|---|---|
| missing | `{"error": true, "message": "Authorization needed"}` | T-notepad-07 |
| invalid | `{"error": true, "message": "Invalid token"}` | T-notepad-08 |
