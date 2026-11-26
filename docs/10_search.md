# Search

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/search/username/{username}` | Users by nickname prefix |
| `GET` | `/api/search` | Posts (no paging) |
| `GET` | `/api/search-v2` | Posts, with paging |
| `GET` | `/api/search/unified` | Discussions, users or posts, depending on the query |

Verification: live tests in [`tests/seg_search.py`](../tests/seg_search.py), 2026-11-25. Test IDs are in brackets.

---

## Search expressions

`text` (`/search`, `/search-v2`) and `search` (`/search/unified`) accept these forms:

| Expression | Matches | Test |
|---|---|---|
| `test` | words **starting** with `test` (`testy`, `tested`, `testosterone`) | T-search-22 |
| `=test` | the exact word `test`, any letter case | T-search-26 |
| `"testing NYX"` | the phrase | T-search-27 |
| `@NYXOT` | posts by `NYXOT` | T-search-28 |
| `@NYXOT test` | posts by `NYXOT` containing `test…` | T-search-29 |

Matches in `content` are wrapped in `<em class='search-match'>…</em>` [T-search-22].

---

## GET /api/search/username/{username}

Finds users whose nickname starts with `username`.

```bash
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" https://nyx.cz/api/search/username/NYX
```

**200** [T-search-03]

```json
{
  "exact":   [ { "username": "NYX" } ],
  "friends": [],
  "others":  [ { "username": "NYXOT",
                 "activity": { "username": "NYXOT", "last_activity": "2026-11-25T15:37:16",
                               "last_access_method": "Api", "status": "Active",
                               "location": "hledat", "location_url": "/search" } } ]
}
```

- `exact` holds the user with exactly this nickname. `friends` and `others` hold users whose nickname starts with the query.
- `exact` is case-sensitive. `nyxot` returns `NYXOT` only in `others` [T-search-02].
- `activity` is present only for some users (`NYX` has none).

| Input | Result | Test |
|---|---|---|
| 2–15 characters `[A-Za-z0-9_]` | 200 | T-search-04, -06 |
| no match | 200, three empty lists | T-search-08 |
| 1 character, 16+ characters, `-`, `ž`, empty | **404** `{"error": true, "message": "Not Found"}` | T-search-05, -07, -09…-11 |

> [!WARNING]
> **Swagger says** each row is `{user: {username, …}, activity}`. In reality `username` is directly on the row. Swagger documents 400 for invalid input; the real response is 404.

Fixture: [`tests/fixtures/search/username_200.json`](../tests/fixtures/search/username_200.json)

---

## GET /api/search and GET /api/search-v2

| Parameter | Type | `/search` | `/search-v2` |
|---|---|---|---|
| `user` | nickname | ✓ | ✓ |
| `text` | search expression | ✓ | ✓ |
| `order` | `newest`, `oldest`, `newer_than`, `older_than` | – | ✓ |
| `from_id` | post ID | – | ✓ |

```bash
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" \
  "https://nyx.cz/api/search-v2?text=test&order=older_than&from_id=59138633"
```

**200** `{ "context": {…}, "posts": [ … ] }` [T-search-22]. Post fields are described in [Models](12_models.md).

- Both endpoints returned identical results for all 10 shared queries [T-search-12…31].
- One page has **20** posts, ordered newest first.
- `user` is case-insensitive (`nyxot` works) and needs the full nickname. `user=NY` returns no posts [T-search-20, -21].
- Without `user` and `text` the result is an empty list, not an error [T-search-15, -25].

### Paging (`/search-v2`)

| `order` | `from_id` | Result | Test |
|---|---|---|---|
| none or `newest` | ignored | newest 20 posts | T-search-42, -48, -49 |
| `oldest` | – | oldest 20 posts (2003), still sorted newest first within the page | T-search-43 |
| `older_than` | ID | 20 posts with ID < `from_id` | T-search-47 |
| `newer_than` | ID | posts with ID > `from_id` (max. 20), newest first | T-search-46 |
| `newer_than` / `older_than` | missing | same as `newest` | T-search-44, -45 |

Invalid `order` (`foo`) and invalid `from_id` (`0`, `-1`, `abc`) are ignored without an error. `order` is case-insensitive (`NEWEST` works) [T-search-50…54].

> [!WARNING]
> **Swagger says** `newer_than` and `older_than` require `from_id` and lists 400 for invalid input. In reality the API falls back to `newest` and returns 200.

Fixture: [`tests/fixtures/search/search_v2_200.json`](../tests/fixtures/search/search_v2_200.json)

---

## GET /api/search/unified

| Parameter | Type | Required | Default |
|---|---|---|---|
| `search` | search expression | yes | – |
| `limit` | integer | no | 5 |

The form of `search` decides what is searched and which single key the response contains:

| `search` | Response | Test |
|---|---|---|
| `testing` | `{"discussion": {"discussions": […], "events": […], "advertisements": […]}}` | T-search-56 |
| `@NYXOT` | `{"user": {"exact": […], "friends": […], "others": […]}}` (same rows as `/search/username`) | T-search-58 |
| `@NYXOT test` | `{"discussion_post": [ {discussion_id, post_id, discussion_name, discussion_name_highlighted, content} ]}` | T-search-67 |

```bash
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" "https://nyx.cz/api/search/unified?search=testing&limit=5"
```

Discussion rows have `id, discussion_type, discussion_name, discussion_name_highlighted, summary, summary_highlighted` [T-search-56].

| Input | Result | Test |
|---|---|---|
| `limit=1`, `5` | 1, 5 discussions | T-search-59, -60 |
| `limit=20` | 19 discussions | T-search-61 |
| `limit=0`, `-1` | empty lists | T-search-62, -63 |
| `limit=abc` | default 5 | T-search-64 |
| `@NYXOT test` (default `limit`) | 10 posts, so the default of 5 does not apply | T-search-67 |
| `288360` (discussion ID) | no results; IDs are not searched | T-search-57 |
| `@NY` | **400** `{"error": true, "message": "Chybné hledání."}` | T-search-66 |
| `search` missing | **404** `{"error": true, "message": "Not Found"}` | T-search-65 |

> [!WARNING]
> **Swagger says** the response is directly one of `UsernameSearchResult`, `UnifiedSearchDiscussionResult` or `UnifiedSearchDiscussionPostResult`, and that `@foo` finds users *starting with* `foo`. In reality the result is wrapped in a key (`user`, `discussion`, `discussion_post`), and `@NY` returns 400.

Fixtures: [`unified_discussion_200.json`](../tests/fixtures/search/unified_discussion_200.json), [`unified_username_200.json`](../tests/fixtures/search/unified_username_200.json), [`unified_posts_200.json`](../tests/fixtures/search/unified_posts_200.json)

---

## Authentication errors

All endpoints return **401**: missing token `Authorization needed` [T-search-68], invalid token `Invalid token` [T-search-69]. See [Errors](11_errors.md).
