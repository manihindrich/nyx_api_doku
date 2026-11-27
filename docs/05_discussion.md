# Discussion

Reading discussions and working with posts. Access rights of other users are in [Discussion rights](06_discussion_rights.md).

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/discussion/{discussionId}` | Discussion info and posts |
| `POST` | `/api/discussion/{discussionId}/send/text` | Write a post |
| `DELETE` | `/api/discussion/{discussion_id}/delete/{id}` | Delete a post |
| `GET` | `/api/discussion/{discussion_id}/rating/{id}` | Who rated a post |
| `POST` | `/api/discussion/{discussion_id}/rating/{id}/{action}` | Rate a post |
| `POST` | `/api/discussion/{discussion_id}/reminder/{id}/{new_state}` | Add/remove a post from reminders |
| `GET`, `POST` | `/api/discussion/{discussion_id}/bookmark` | Watch / unwatch the discussion |
| `POST` | `/api/discussion/{discussionId}/content/{contentId}/save` | Edit a header (board) section |

Verification: live tests in [`tests/seg_discussion.py`](../tests/seg_discussion.py), 2026-11-25, in discussion 100001 (owned by the test account) and read-only in the public discussion 100002. Test IDs are in brackets, `T-` prefix omitted (`D-25` = `T-discussion-25`).

---

## GET /api/discussion/{discussionId}

```bash
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" "https://nyx.cz/api/discussion/100002?rating=2"
```

| Parameter | Type | Effect |
|---|---|---|
| `user` | nickname | Only posts by this user. Case-insensitive [D-02…04]. |
| `text` | search expression | Only matching posts [D-05]. See [Search](10_search.md#search-expressions). |
| `rating` | integer | Positive `n`: posts with rating **≥ n**. Negative `n`: posts with rating **≤ n** [D-102, -103]. `0` has no effect [D-08]. Overrides `text` [D-104]. |
| `reminders` | `true` | Only posts in the user's reminders [D-57]. `false` has no effect [D-107]. |
| `order` | `newest`, `oldest`, `newer_than`, `older_than` | Paging, see below |
| `from_id` | post ID | Used with `newer_than` / `older_than` |
| `last_visit` | post ID | No observable effect in tests [D-14, D-106] |

### Paging

One page has **20** posts, newest first [D-10].

| `order` | `from_id` | Result | Test |
|---|---|---|---|
| none or `newest` | – | newest 20 | D-10 |
| `oldest` | – | oldest 20, still sorted newest first within the page | D-11 |
| `older_than` | ID | 20 posts with ID < `from_id` | D-13 |
| `newer_than` | ID | posts with ID > `from_id` (max. 20) | D-12 |
| `newer_than` / `older_than` | missing | same as `newest` | D-15, -16 |

`from_id=0`, `from_id=abc` and `order=foo` are ignored without an error [D-17…19].

### Response

**200** with four keys: `context`, `discussion_common`, `posts`, `presence` [D-01].

```json
{
  "context": { … },
  "discussion_common": {
    "discussion": { "id": 100001, "name_static": "Test discussion", "discussion_type": "discussion",
                    "ar_read": false, "ar_write": false, "ar_delete": false, "ar_edit": false, … },
    "owner": { "user": { "username": "TESTUSER" } },
    "access_right": null,
    "bookmark": { "discussion_id": 100001, "bookmark": true, "category_id": null, "replies_count": 0,
                  "last_seen_post_id": 50000019, "last_visited_at": "2026-11-25T15:57:28" },
    "discussion_specific_data": { "header": [ { "id": 60004, "location": "header", "sort_order": 2,
        "content": "…", "content_raw": { "type": "text", "data": { "data": "…", "format": "html" } } } ] },
    "waiting_files": []
  },
  "posts": [
    { "id": 50000013, "discussion_id": 100001, "username": "PEERUSER", "inserted_at": "…", "content": "…",
      "can_be_deleted": true, "can_be_rated": true, "can_be_reminded": true, "activity": { … } }
  ],
  "presence": []
}
```

- `discussion_specific_data.header` holds the header (board) sections. Their `id` is the `contentId` for [content save](#post-apidiscussiondiscussionidcontentcontentidsave).
- `bookmark` shows whether the user watches the discussion and the last seen post.
- Post fields such as `rating`, `my_rating`, `reminder` appear only when they have a value [D-01, D-46…52]. See [Models](12_models.md).

> [!WARNING]
> The `ar_*` flags in `discussion` were all `false` for the discussion owner, who could still write, delete and edit [D-01, D-25, D-86]. Do not use them to decide what the user may do; try the action and handle the error.

> [!WARNING]
> **Swagger says** only `context` and `posts` are required; `discussion_common` and `presence` are described as optional. In reality all four are always present.

### Access without a token

| Discussion | Token | Status | Body | Test |
|---|---|---|---|---|
| public (100002) | missing or invalid | **200**, full content | | D-99, -100 |
| 100001 | missing or invalid | 400 | `{"error": true, "message": "Přístup odmítnut."}` | D-23, -24 |
| non-existent (`999999999`) | any | 400 | `{"error": true, "message": "Nepodařilo se načíst diskuzi."}` | D-97, -98 |
| `abc` | valid | 404 | `{"error": true, "message": "Not Found"}` | D-22 |

Unlike other endpoints, this one never returned 401.

Fixtures: [`discussion_get_200.json`](../tests/fixtures/discussion/discussion_get_200.json), [`discussion_get_foreign_200.json`](../tests/fixtures/discussion/discussion_get_foreign_200.json)

---

## POST /api/discussion/{discussionId}/send/text

Form fields: `content` (required), `format` (`text` or `html`).

```bash
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" \
  --data-urlencode "content=Hello" -d "format=html" \
  https://nyx.cz/api/discussion/100001/send/text
```

**200** `{}`. The response does not contain the post ID. To find it, read the discussion (`?user=<you>&order=newest`) and match the content [D-25].

| `format` | Input | Stored `content` | Test |
|---|---|---|---|
| `text` | `line1⏎line2 <b>x</b>` | `line1<br>line2 &lt;b&gt;x&lt;/b&gt;` | D-25 |
| `html` | `<b>bold</b>⏎line2` | `<b>bold</b><br>line2` | D-26 |
| `markdown` (undocumented) | `**bold**` | `**bold**`, not converted | D-27 |
| missing | plain text | plain text | D-28 |
| `foo` (invalid) | text | accepted with 200, not rejected | T-verify-39 |

A 20 000-character post was accepted [D-32].

| Case | Status | Body | Test |
|---|---|---|---|
| empty `content` | 400 | `{"error": true, "message": "Nepodařilo se odeslat příspěvek."}` | D-29 |
| same text as the user's previous post | 400 | same message | D-30, -31 |

> [!IMPORTANT]
> Duplicate posts are rejected with the same generic message as other failures. Add something unique to automated posts.

---

## DELETE /api/discussion/{discussion_id}/delete/{id}

```bash
curl -s -X DELETE -H "Authorization: Bearer $NYX_API_TOKEN" https://nyx.cz/api/discussion/100001/delete/50000018
```

**200** `{}`, the post is gone [D-86, -87]. Deleting it again: 400 `{"error": true, "message": "Příspěvek neexistuje."}` [D-88].

> [!CAUTION]
> **Not tested:** deleting another user's post. The test harness only deletes posts it created.

---

## GET /api/discussion/{discussion_id}/rating/{id}

**200** list of users who rated the post **positively** [D-47]:

```json
[ { "username": "TESTUSER", "tag": "positive" } ]
```

Negative ratings (`negative`, `negative_visible`) are not listed [D-49, -51]. A post without positive ratings or a non-existent ID returns `[]` [D-35, D-55].

## POST /api/discussion/{discussion_id}/rating/{id}/{action}

`action`: `positive`, `negative`, `negative_visible`, `remove`.

```bash
curl -s -X POST -H "Authorization: Bearer $NYX_API_TOKEN" \
  https://nyx.cz/api/discussion/100001/rating/50000013/positive
```

**200** returns the updated post [D-46…52]:

| `action` | Post after the call |
|---|---|
| `positive` | `"rating": 1, "my_rating": "positive"` |
| `negative` | `"rating": -1, "my_rating": "negative"` |
| `negative_visible` | `"rating": -1, "my_rating": "negative_visible"` |
| `remove` | no `rating` and no `my_rating` |

Each call replaces the user's previous rating.

| Case | Status | Body | Test |
|---|---|---|---|
| own post | 400 | `{"error": true, "message": "Nemůžete označit vlastní příspěvky."}` | D-37…43 |
| non-existent post | 400 | `{"error": true, "message": "Nepodařilo se načíst příspěvek."}` | D-54 |
| `action=foo` | 422 | `{"error": true, "message": "422"}` | D-45 |

Fixtures: [`rating_get_200.json`](../tests/fixtures/discussion/rating_get_200.json), [`rating_post_200.json`](../tests/fixtures/discussion/rating_post_200.json)

---

## POST /api/discussion/{discussion_id}/reminder/{id}/{new_state}

`new_state`: `true` or `false`. **200** `{}`. With `true` the post appears in `GET …?reminders=true`; with `false` it disappears [D-56…59].

| Case | Status | Body | Test |
|---|---|---|---|
| `new_state=1`, `abc`; `id=abc` | 422 | `{"error": true, "message": "422"}` | D-60, -63, -65 |
| `id=0`, non-existent ID | 400 | `{"error": true, "message": "Nepodařilo se uložit upomínku."}` | D-64, -66 |

---

## GET / POST /api/discussion/{discussion_id}/bookmark

Query parameters: `new_state` (`true`/`false`, required), `category` (bookmark category ID). Both methods behave the same [D-70, D-74].

```bash
curl -s -X POST -H "Authorization: Bearer $NYX_API_TOKEN" \
  "https://nyx.cz/api/discussion/100001/bookmark?new_state=true"
```

**200** `{}`. The state is visible in `discussion_common.bookmark` of `GET /api/discussion/{id}`.

| Case | Status | Body | Test |
|---|---|---|---|
| `new_state=false` on the user's own discussion | 400 | `{"error": true, "message": "Nelze vypnout sledování u vlastní diskuze."}` | D-68, -72 |
| `category=-2` | 400 | `{"error": true, "message": "Nepodařilo se uložit do sledovaných."}` | D-77 |
| `new_state=abc` | 422 | `{"error": true, "message": "422"}` | D-79 |

> [!CAUTION]
> **Not verified:** `new_state=false` and a valid `category` on a discussion the user does not own. The test account may only write to its own discussion.

> [!NOTE]
> A `GET` request that changes state is unusual. Prefer `POST`.

---

## POST /api/discussion/{discussionId}/content/{contentId}/save

Replaces the content of a header (board) section. Form fields: `content`, `format`. `contentId` is the `id` of a section in `discussion_common.discussion_specific_data.header`.

```bash
curl -s -H "Authorization: Bearer $NYX_API_TOKEN" \
  --data-urlencode $'content=line1\nline2' -d "format=html" \
  https://nyx.cz/api/discussion/100001/content/60004/save
```

**200** `{}`. The new text is stored in `content_raw.data.data` exactly as sent, including `\r\n` [D-82, D-108, -109].

| Case | Status | Body | Test |
|---|---|---|---|
| post ID as `contentId` | 400 | `{"error": true, "message": "Nepodařilo se uložit obsah."}` | D-33 |
| non-existent `contentId` | 400 | same | D-34 |

> [!WARNING]
> **Swagger says** this endpoint saves "post text or a header section". Using a post ID failed; posts cannot be edited through the API.

---

## Errors in this chapter

Invalid enum or boolean values in the path return **422** `{"error": true, "message": "422"}`, not 400 as Swagger says. See [Errors](11_errors.md).
