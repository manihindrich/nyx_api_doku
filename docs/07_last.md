# Last posts

Latest posts across all discussions the user can read, with optional filters.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/last` | Latest posts (max. 50) |

Verification: live tests in [`tests/seg_last.py`](../tests/seg_last.py), 2026-11-25. Test IDs are in brackets.

---

## GET /api/last

```bash
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" "https://nyx.cz/api/last?min_rating=5"
```

| Parameter | Type | Effect |
|---|---|---|
| `domain` | integer | Only posts from discussions in this category. IDs and names are in `ignored_domains` of any response. |
| `min_rating` | integer | Only posts with rating ≥ value. Posts without a rating are excluded. |
| `rated_by_friends` | boolean | Only posts rated by the user's friends. |
| `rated_by_me` | boolean | Only posts rated by the user. |

There are no paging parameters. Every call returned at most **50** posts [T-last-01].

### Parameter behaviour

| Input | Result | Test |
|---|---|---|
| `domain=1`, `2`, `5`, `10` | list limited to that category | T-last-03…06 |
| `domain=0`, `domain=-1` | empty list | T-last-02, -08 |
| `domain=99999`, `domain=abc` | ignored, unfiltered list | T-last-07, -09 |
| `min_rating=1`, `5`, `10` | 50 posts, all with `rating` ≥ value. Older posts are included to fill the list. | T-last-11…13 |
| `min_rating=50` | empty list at test time | T-last-14 |
| `min_rating=0`, `-5`, `abc` | ignored | T-last-10, -15, -16 |
| `rated_by_friends=true`, `rated_by_me=true` | empty list for the test account | T-last-17, -22 |
| `…=false`, `…=0`, `…=1`, `…=abc` | ignored, unfiltered list | T-last-18…21, -23…25 |
| `min_rating=5&rated_by_me=false` | same as `min_rating=5` | T-last-26 |

> [!IMPORTANT]
> Booleans must be the literal `true`. The value `1` is silently ignored.

> [!CAUTION]
> **Not verified:** what `rated_by_friends=true` and `rated_by_me=true` return when matching posts exist. The test account had no matching posts.

Invalid values never cause an error. No case returned 400.

### Response

**200** `application/json` [T-last-01]

```json
{
  "context": { "user": { … }, "active_friends": [] },
  "posts": [
    { "id": 50000015, "discussion_id": 100008, "discussion_name": "Example discussion G",
      "username": "USER1", "inserted_at": "2026-11-25T15:32:03", "content": "<redacted>",
      "rating": 1, "can_be_rated": true, "can_be_reminded": true }
  ],
  "ignored_domains": [ { "user_id": 10001, "domain_id": 1, "name": "SYSTEMOVE KLUBY", "ignored": false } ],
  "ignored_discussions": []
}
```

- `ignored_domains` lists **all** categories, each with the flag `ignored`. It is the source of valid `domain` IDs.
- Post fields are described in [Models](12_models.md). Some appear only when relevant. In a sample of 50 posts: `rating` 13×, `activity` 33×, `replies` 6×, `content_raw` and `post_type` 2× each.

> [!WARNING]
> **Swagger says** posts are `TemplatePost`. Every post also has `discussion_name`, which Swagger does not list.

Fixture: [`tests/fixtures/last/get_last_200.json`](../tests/fixtures/last/get_last_200.json)

### Errors

| Token | Status | Body | Test |
|---|---|---|---|
| missing | 401 | `{"error": true, "message": "Authorization needed"}` | T-last-27 |
| invalid | 401 | `{"error": true, "message": "Invalid token"}` | T-last-28 |
