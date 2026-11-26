# Models

Objects that appear in several endpoints. The field lists were produced by [`tests/models_check.py`](../tests/models_check.py) from all live responses (2026-11-25 to 2026-11-27) and compared with the Swagger schemas.

## General rules

- **Optional fields are omitted, not `null`.** Flags such as `incoming`, `reminder`, `is_owner`, `new` and `can_be_*` never appeared with `false`; counters such as `new_posts_count` never appeared as `0`. Treat a missing field as `false` / `0`.
- Exception: in [notifications](08_notifications.md) the post in `data` always has `rating`, `my_rating` (may be `null`) and `reminder` (may be `false`).
- Timestamps have no time zone: `"2026-11-25T15:44:18"`.
- URLs of files are relative to `https://nyx.cz`.

---

## Context

Returned as `context` by almost every `GET`.

```json
{ "user": { "username": "NYXOT", "mail_unread": 0, "mail_last_from": "RSS",
            "notifications_unread": 0, "notifications_last_visit": "2025-07-29T12:47:28" },
  "active_friends": [] }
```

Matches Swagger (`Context`, `User`).

## Activity

Where and when a user was last active. Attached to posts, mail and users as `activity`.

```json
{ "username": "NYXOT", "last_activity": "2026-11-25T15:37:16", "last_access_method": "Api",
  "status": "Active", "location": "hledat", "location_url": "/search" }
```

| Field | Values seen |
|---|---|
| `last_access_method` | `Api`, `Web` |
| `status` | `Active` |
| `location` | page name or discussion name, may be empty |

> [!WARNING]
> **Swagger says** the field is `status_details`. In reality it is `status`.

## Post

Posts in [discussions](05_discussion.md), [last posts](07_last.md) and [search](10_search.md).

| Field | Present | Notes |
|---|---|---|
| `id`, `discussion_id`, `username`, `inserted_at`, `content` | always | `content` is HTML |
| `discussion_name` | last posts, search | not in Swagger's `TemplatePost` |
| `activity` | often | see [Activity](#activity) |
| `can_be_rated`, `can_be_reminded`, `can_be_deleted` | when `true` | not in Swagger's `DiscussionPostWithName` |
| `new` | when `true` | seen only in discussion posts |
| `rating` | usually only when not 0 | sum of ratings; `0` appeared 4 times in ~2 500 posts |
| `my_rating` | when set | `positive`, `negative`, `negative_visible` |
| `reminder` | when `true` | |
| `replies` | when there are replies | list of post IDs |
| `post_type`, `content_raw` | on some posts | e.g. `advertisement`; `content_raw` is `{type, data}` |

`post_type` values seen: `text`, `advertisement`, `event`, `log_message`, `discussion_request`.

> [!NOTE]
> Swagger's `TemplatePost` also lists `can_ignore_discussion`, `preview` and `rating_friends`. They never appeared.

## Mail message

See [Mail](04_mail.md#response). Fields: `id`, `username` (the other party), `content`, `inserted_at`, `other_mail_id`, `activity`; `incoming` and `reminder` only when `true`.

> [!WARNING]
> **Swagger's** `MailPost` lists `unread`, `new` and `preview`, which never appeared, and omits `other_mail_id`. `MailConversationWithActivity.has_unread_mail` never appeared either.

## Bookmarked discussion

Items of [bookmarks and history](03_bookmarks.md): `discussion_id`, `full_name`, `last_visited_at`, `last_seen_post_id`; `is_owner`, `new_posts_count`, `new_links_count`, `new_images_count` only when set. `new_replies_count` (Swagger) never appeared.

## File

See [Files](09_file.md#put-apifileupload). Matches Swagger's `FileWithUrl` plus `image_embed_option` (`full` or `link`).

## Notification

See [Notifications](08_notifications.md). `{type, data, details}`; `type` was always `post`.

## Enums

| Enum | Values in Swagger | Seen live |
|---|---|---|
| `ContentFormatEnum` (`format` of posts and mail) | `text`, `html` | `text`, `html`; `markdown` accepted but not converted |
| `RatingAction` | `positive`, `negative`, `negative_visible`, `remove` | all four |
| `AccessRightType` | `read`, `write`, `delete`, `edit`, `edit_rights`, `grant_edit_rights`, `public` | first five; the last two fail |
| `ApiNavigationDirection` (`order`) | `newest`, `oldest`, `newer_than`, `older_than` | all four |
| `FileTypeEnum` | 7 values | all seven |
| `FileMimeTypeEnum` | `image/gif`, `image/jpeg`, `image/png`, `text/html`, `octet/stream` | `image/gif`, `image/png`, `image/jpeg`, `text/html`, `octet/stream` |
