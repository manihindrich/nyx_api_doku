# Bookmarks and history

Watched discussions (bookmarks) and the history of visited discussions.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/bookmarks` | Bookmark categories, one optionally expanded |
| `GET` | `/api/bookmarks/all` | All categories expanded |
| `GET` | `/api/bookmarks/history` | Recently visited discussions |
| `GET` | `/api/bookmarks/history/more` | Same, longer list |
| `POST` | `/api/bookmarks/history/mark_as_read` | Mark discussions as read |
| `POST` | `/api/bookmarks/history/remove_from_history` | Remove discussions from history |

Watching or unwatching a discussion is done with [`/api/discussion/{id}/bookmark`](05_discussion.md#get--post-apidiscussiondiscussion_idbookmark).

Verification: live tests in [`tests/seg_bookmarks.py`](../tests/seg_bookmarks.py), 2026-11-25, on an account with 2 bookmarks and 10 history entries. Test IDs are in brackets, `B-` = `T-bookmarks-`.

---

## GET /api/bookmarks

| Parameter | Type | Effect |
|---|---|---|
| `expand` | category ID | Lists the discussions of this category |

```bash
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" "https://nyx.cz/api/bookmarks?expand=-2"
```

**200** [B-02]

```json
{
  "context": { … },
  "bookmarks": [
    { "category": { "id": -2, "category_name": "vlastní diskuze" },
      "bookmarks": [ { "discussion_id": 100001, "full_name": "Test discussion", "is_owner": true,
                       "last_visited_at": "2026-11-25T16:21:17", "last_seen_post_id": 50000019 } ] },
    { "category": { "id": -1, "category_name": "nezařazené diskuze" }, "bookmarks": [] }
  ],
  "reminder_count": 0
}
```

- Without `expand`, every category has an empty `bookmarks` list [B-01].
- Built-in categories: `-2` own discussions, `-1` uncategorised [B-01].
- `expand=0`, `99999` and `abc` are ignored without an error [B-04…06].
- `is_owner` appears only on the user's own discussions [B-07].

## GET /api/bookmarks/all

Same structure with every category expanded [B-07].

Fixtures: [`bookmarks_200.json`](../tests/fixtures/bookmarks/bookmarks_200.json), [`bookmarks_all_200.json`](../tests/fixtures/bookmarks/bookmarks_all_200.json)

---

## GET /api/bookmarks/history and /api/bookmarks/history/more

| Parameter | `/history` | `/history/more` | Effect |
|---|---|---|---|
| `show_read` | ✓ | ✓ | `false` hides discussions with no new posts |
| `show_booked` | ✓ | ✓ | `false` hides watched discussions |
| `more_results` | ✓ | – | longer list |

Missing `show_read` / `show_booked` use the user's web settings. For the test account the defaults gave the same result as `true` [B-08, B-15].

```bash
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" \
  "https://nyx.cz/api/bookmarks/history?show_read=true&show_booked=true"
```

**200** [B-08]

```json
{
  "context": { … },
  "discussions": [
    { "discussion_id": 100001, "full_name": "Test discussion", "is_owner": true,
      "last_visited_at": "2026-11-25T16:21:17", "last_seen_post_id": 50000019 }
  ],
  "show_load_more": false
}
```

| Input | Result | Test |
|---|---|---|
| no parameters | 10 discussions | B-08 |
| `show_read=false` | 6 (read discussions hidden) | B-12 |
| `show_booked=false` | 8 (watched discussions hidden) | B-14 |
| both `false` | 6 | B-16 |
| `more_results=true` / `false` | 10 | B-09, -10 |
| `/history/more` with the same flags | same lists as `/history` | B-22…28 |
| `show_read=1`, `show_booked=1`, `more_results=1` | 10 | B-19…21, -29 |

> [!CAUTION]
> **Not verified:** what `more_results` and `/history/more` add. The test account had only 10 history entries, and `show_load_more` was always `false`. Whether `1` means `true` cannot be told apart from the default.

- `new_posts_count`, `new_links_count` and `new_images_count` appear only when they are not zero, e.g. `"new_posts_count": 13, "new_links_count": 3` [B-14]. `new_replies_count`, listed by Swagger, never appeared.

Fixtures: [`history_200.json`](../tests/fixtures/bookmarks/history_200.json), [`history_more_200.json`](../tests/fixtures/bookmarks/history_more_200.json)

---

## POST /api/bookmarks/history/mark_as_read and remove_from_history

Form field `discussion_ids` (list of discussion IDs). Both `discussion_ids[]=100001` and `discussion_ids=100001` work [B-41, -43, -45, -52].

```bash
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" \
  -d "discussion_ids[]=100001" https://nyx.cz/api/bookmarks/history/remove_from_history
```

Both return **200** `{}`.

| Endpoint | Effect | Test |
|---|---|---|
| `mark_as_read` | `last_visited_at` of the discussion is set to now | B-41…44 |
| `remove_from_history` | the discussion disappears from history; it stays in bookmarks | B-45…47 |
| `remove_from_history` again | 200 `{}`, no error | B-48 |

- A removed discussion returns to history as soon as the user opens it (`GET /api/discussion/{id}`) [B-50, -51].
- Effect of `mark_as_read` on unread posts: **not verified** (none existed).

> [!CAUTION]
> **Not tested:** an empty or missing `discussion_ids`, and other users' discussions. The test harness only allows the test discussion.

---

## Authentication errors

Missing token: 401 `Authorization needed`. Invalid token: 401 `Invalid token` [B-30…35]. See [Errors](11_errors.md).
