# Mail

Private messages between users.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/mail` | Read mail (all conversations or one) |
| `POST` | `/api/mail/send` | Send a message |
| `POST` | `/api/mail/reminder/{id}/{newState}` | Add or remove a message from reminders |

The API cannot delete messages.

Verification: live tests in [`tests/seg_mail.py`](../tests/seg_mail.py), 2026-11-25. Test IDs are in brackets.

---

## GET /api/mail

| Parameter | Type | Effect |
|---|---|---|
| `user` | nickname | Only the conversation with this user. Case-insensitive (`bod` works) [T-mail-02, -03]. |
| `text` | search expression | Only messages matching the text; matches are wrapped in `<em class='search-match'>` [T-mail-04]. See [Search](10_search.md#search-expressions). |
| `order` | `newest`, `oldest`, `newer_than`, `older_than` | Paging, see below |
| `from_id` | message ID | Used with `newer_than` / `older_than` |

```bash
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" "https://nyx.cz/api/mail?user=BOD"
```

Without `user` the response contains messages from **all** conversations [T-mail-01].

### Paging

One page has **20** messages, newest first [T-mail-05].

| `order` | `from_id` | Result | Test |
|---|---|---|---|
| none or `newest` | – | newest 20 | T-mail-05 |
| `oldest` | – | oldest 20, still sorted newest first within the page | T-mail-06 |
| `older_than` | ID | 20 messages with ID < `from_id` | T-mail-08 |
| `newer_than` | ID | messages with ID > `from_id` (max. 20) | T-mail-07 |
| `newer_than` / `older_than` | missing | same as `newest` | T-mail-09, -10 |

`from_id=0`, `from_id=abc` and `order=foo` are ignored without an error [T-mail-11…13].

> [!TIP]
> To poll for new mail, remember the highest ID you have seen and call `?order=newer_than&from_id=<id>`.

### Response

**200** [T-mail-01, T-mail-33]

```json
{
  "context": { … },
  "conversations": [
    { "username": "RSS", "conversed_at": "2026-11-25T13:43:18",
      "activity": { "username": "RSS", "last_activity": "2026-11-25T15:43:16", "last_access_method": "Api",
                    "status": "Active", "location": "pošta", "location_url": "/mail" } }
  ],
  "posts": [
    { "id": 176692472, "username": "BOD", "inserted_at": "2026-11-25T15:44:18",
      "content": "text [nyxapidoku 2026-11-25 15:44:16 b1cf3b]<br>line2 &lt;b&gt;x&lt;/b&gt;",
      "other_mail_id": 176692473, "reminder": true, "activity": { … } }
  ],
  "reminders": [ { "id": 176692472, … } ],
  "waiting_files": []
}
```

- `username` is always the **other** party of the conversation, for incoming and outgoing messages alike.
- `other_mail_id` is the ID of the same message in the other user's mailbox. Swagger does not list it.
- Boolean flags are present **only when true**:
  - `incoming: true` marks a received message. Sent messages have no `incoming` field [T-mail-01].
  - `reminder: true` appears only on messages in reminders [T-mail-33, -35].
- `reminders` lists the messages in reminders [T-mail-33].

> [!WARNING]
> **Swagger says** `incoming` and `reminder` are booleans. In reality they are either `true` or missing, never `false`.

Fixture: [`tests/fixtures/mail/mail_200.json`](../tests/fixtures/mail/mail_200.json)

---

## POST /api/mail/send

Form fields (`application/x-www-form-urlencoded`):

| Field | Required | Values |
|---|---|---|
| `recipient` | yes | nickname |
| `message` | yes | text |
| `format` | no | `text`, `html` |

```bash
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" \
  --data-urlencode "recipient=BOD" --data-urlencode "message=Hello" -d "format=text" \
  https://nyx.cz/api/mail/send
```

**200** `{}`. The response does not contain the new message ID. Read it back with `GET /api/mail?user=<recipient>` [T-mail-16].

How `message` is stored [T-mail-31]:

| `format` | Input | Stored `content` | Test |
|---|---|---|---|
| `text` | `line1⏎line2 <b>x</b>` | `line1<br>line2 &lt;b&gt;x&lt;/b&gt;` | T-mail-16 |
| `html` | `line1⏎<b>bold</b>` | `line1<br><b>bold</b>` | T-mail-17 |
| `markdown` (undocumented) | `**bold**` | `**bold**`, not converted | T-mail-18 |
| missing | plain text | plain text | T-mail-19 |

- Newlines become `<br>` in both formats.
- `text` escapes HTML; `html` keeps it. See [HTML](13_html.md).

**Errors**

| Case | Status | Body | Test |
|---|---|---|---|
| empty `message` | 400 | `{"error": true, "message": "Nelze odeslat prázdnou zprávu."}` | T-mail-20 |
| same text as the previous message | 400 | `{"error": true, "message": "Nejspíš jde o omylem dvojitě posílanou zprávu."}` | T-mail-21, -22 |

> [!IMPORTANT]
> nyx rejects a message identical to the previous one. Add something unique (e.g. a timestamp) to automated messages.

> [!CAUTION]
> **Not in the test suite:** a missing or non-existent `recipient`. The test harness only allows sending to one account. An earlier observation (2026-11-24) returned 400 `Chybný příjemce.` for a non-existent nickname.

---

## POST /api/mail/reminder/{id}/{newState}

| Parameter | In | Values |
|---|---|---|
| `id` | path | message ID |
| `newState` | path | `true`, `false` |

```bash
curl -s -X POST -H "Authorization: Bearer $NYX_API_TOKEN" https://nyx.cz/api/mail/reminder/176692472/true
```

**200** `{}`. `true` adds the message to `reminders`, `false` removes it [T-mail-32…35].

| Input | Status | Body | Test |
|---|---|---|---|
| `newState=1`, `0`, `abc` | 422 | `{"error": true, "message": "422"}` | T-mail-25…27 |
| `id=abc` | 422 | same | T-mail-30 |
| `id=0`, `id=999999999999` | 200 | `{}`, nothing happens | T-mail-28, -29 |

> [!WARNING]
> **Swagger says** `newState` is a boolean and errors are 400. In reality only the literal `true`/`false` work, other values return **422**, and a non-existent ID returns 200.

---

## Authentication errors

Missing token: 401 `Authorization needed` [T-mail-14]. Invalid token: 401 `Invalid token` [T-mail-15]. See [Errors](11_errors.md).
