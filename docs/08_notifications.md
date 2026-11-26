# Notifications

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/notifications` | Ratings of and replies to the user's posts |
| `POST` | `/api/register_for_notifications/{token}/{client}/{client_token}` | Register a device for push notifications |

Verification: live tests in [`tests/seg_notifications.py`](../tests/seg_notifications.py), 2026-11-27. Test IDs are in brackets, `N-` = `T-notifications-`.

---

## GET /api/notifications

No parameters.

```bash
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" https://nyx.cz/api/notifications
```

**200** [N-01]

```json
{
  "context": { … },
  "notifications": [
    {
      "type": "post",
      "data": { "id": 59120957, "discussion_id": 275939, "discussion_name": "…", "username": "NYXOT",
                "user_id": 94404, "domain_id": 14, "inserted_at": "…", "content": "…", "content_raw": { … },
                "post_type": "text", "rating": 6, "rating_relative": 2, "my_rating": null,
                "reminder": false, "replies": [ … ] },
      "details": {
        "thumbs_up": [ { "username": "USER1", "inserted_at": "2026-11-16T11:59:45" } ],
        "replies": [ { "id": …, "discussion_id": …, "username": "USER2", "inserted_at": "…", "content": "…" } ]
      }
    }
  ]
}
```

- Each item is one of the user's posts (`data`) with who rated it positively (`details.thumbs_up`) and replies to it (`details.replies`).
- All 23 items had `type: "post"`.
- `details.replies` is missing when there are no replies (12 of 23 items).
- Unlike posts in other endpoints, `data` always contains `rating`, `my_rating` (may be `null`), `reminder` (may be `false`), `replies`, `user_id`, `domain_id` and `rating_relative`.

> [!WARNING]
> **Swagger says** the list is in `posts` (while also listing `notifications` as required). In reality the key is `notifications`. `user_id`, `domain_id` and `rating_relative` in `data` are not documented.

Fixture: [`tests/fixtures/notifications/get_notifications_200.json`](../tests/fixtures/notifications/get_notifications_200.json)

| Token | Status | Body | Test |
|---|---|---|---|
| missing | 401 | `{"error": true, "message": "Authorization needed"}` | N-02 |
| invalid | 401 | `{"error": true, "message": "Invalid token"}` | N-03 |

---

## POST /api/register_for_notifications/{token}/{client}/{client_token}

| Parameter | In | Meaning (Swagger) |
|---|---|---|
| `token` | path | a nyx API token; lets a request authenticated with token A register notifications for token B |
| `client` | path | `nyx`, `fyx`, `nyxdroid` |
| `client_token` | path | the device's push token (Firebase ~140 characters, APNs 64) |

The request itself is authenticated with the normal `Authorization` header.

> [!CAUTION]
> This endpoint puts an API token **into the URL**, where it can end up in server and proxy logs.
>
> **Not verified:** a successful registration. By decision, the tests never put a real token in a URL.

Behaviour with a fake `token` [N-04…11]:

| Case | Status | Body |
|---|---|---|
| valid `Authorization`, fake `token`, any `client` (also `foo`), any `client_token` | 404 | `{"error": true, "message": "Nepodařilo se načíst token."}` |
| `GET` instead of `POST` | 404 | `{"error": true, "message": "Not Found"}` |
| missing or invalid `Authorization` | 401 | `{"error": {"code": 401, "reason": "Unauthorized", "description": "The request requires user authentication."}}` |

With a fake `token`, every `client` value gave the same error, so validation of `client` could not be observed.
