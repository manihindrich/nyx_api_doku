# Datové modely

Tento dokument popisuje všechny datové struktury používané v NYX.CZ API.

## Základní typy

### Username
```json
"string"
```
Uživatelské jméno ve formátu [A-Z0-9_]{3,15}

**Příklad**: `"USERNAME"`

### SearchExpression
```json
"string"
```
Vyhledávací výraz s možnostmi:
- `=foo` - přesná shoda
- `"phrase match"` - fráze
- `@username` - od konkrétního uživatele

**Příklad**: `"=foo \"phrase match\" @username"`

## Uživatelské struktury

### User
```json
{
  "username": "string",
  "mail_unread": "integer",
  "mail_last_from": "string | null",
  "notifications_unread": "integer",
  "notifications_last_visit": "string (date-time)"
}
```

### UserSearch
```json
{
  "username": "string"
}
```

### Activity
```json
{
  "username": "string",
  "last_activity": "string (date-time)",
  "last_access_method": "string",
  "status_details": "string",
  "location": "string",
  "location_url": "string"
}
```

**last_access_method**: `"Web"` | `"Api"`

## Kontextové struktury

### Context
```json
{
  "user": "User",
  "active_friends": ["Activity"]
}
```

## Diskuzní struktury

### Discussion
```json
{
  "id": "integer",
  "domain_id": "integer",
  "domain_category_id": "integer",
  "name_static": "string",
  "name_dynamic": "string | null",
  "has_header": "boolean",
  "has_home": "boolean",
  "last_post_id": "integer | null",
  "posts_count": "integer",
  "image_posts_count": "integer",
  "link_posts_count": "integer",
  "ar_read": "boolean",
  "ar_write": "boolean",
  "ar_delete": "boolean",
  "ar_edit": "boolean",
  "ar_rights": "boolean",
  "public": "boolean",
  "discussion_type": "DiscussionTypeEnum",
  "last_header_change": "string (date-time)",
  "hashtags": ["string"]
}
```

### DiscussionTypeEnum
- `"discussion"` - Diskuze
- `"event"` - Událost
- `"advertisement"` - Inzerát

### DiscussionAccessRight
```json
{
  "discussion_id": "integer",
  "ar_read": "boolean",
  "ar_write": "boolean",
  "ar_delete": "boolean",
  "ar_edit": "boolean",
  "ar_rights": "boolean",
  "days_left": "integer"
}
```

### DiscussionBookmark
```json
{
  "discussion_id": "integer",
  "bookmark": "boolean",
  "category_id": "integer | null",
  "replies_count": "integer",
  "last_seen_post_id": "integer",
  "last_seen_posts_count": "integer",
  "last_seen_image_posts_count": "integer",
  "last_seen_link_posts_count": "integer",
  "last_visited_at": "string (date-time)"
}
```

## Příspěvkové struktury

### DiscussionPostWithName
```json
{
  "id": "integer",
  "discussion_id": "integer",
  "username": "string",
  "content": "string | null",
  "content_raw": "PostContentEnum",
  "post_type": "PostTypeEnum",
  "reminder": "boolean",
  "rating": "integer",
  "my_rating": "TagTypeEnum | null",
  "replies": ["integer"],
  "inserted_at": "string (date-time)"
}
```

### TemplatePost
Rozšířená verze DiscussionPostWithName:
```json
{
  "id": "integer",
  "discussion_id": "integer",
  "username": "string",
  "content": "string | null",
  "content_raw": "PostContentEnum",
  "post_type": "PostTypeEnum",
  "reminder": "boolean",
  "rating": "integer",
  "my_rating": "TagTypeEnum | null",
  "replies": ["integer"],
  "inserted_at": "string (date-time)",
  "activity": "Activity",
  "new": "boolean",
  "preview": "boolean",
  "can_be_deleted": "boolean",
  "can_be_rated": "boolean",
  "can_be_reminded": "boolean",
  "can_ignore_discussion": "boolean",
  "rating_friends": ["string"]
}
```

### PostTypeEnum
- `"text"` - Textový příspěvek
- `"poll"` - Anketa
- `"dice"` - Kostky
- `"log_message"` - Log zpráva
- `"event"` - Událost
- `"advertisement"` - Inzerát
- `"discussion_request"` - Požadavek na diskuzi
- `"registration"` - Registrace

### TagTypeEnum
- `"positive"` - Kladné hodnocení
- `"negative"` - Záporné hodnocení
- `"negative_visible"` - Záporné hodnocení viditelné
- `"removed"` - Odebráno
- `"reminder"` - Upomínka

## Obsah příspěvků

### PostContentEnum
Union type pro různé typy obsahu:
- `PostContentText`
- `PostContentPoll`
- `PostContentDice`

### PostContentText
```json
{
  "data": "string",
  "format": "ContentFormat"
}
```

### PostContentPoll
```json
{
  "question": "string",
  "instructions": "string",
  "public_results": "boolean",
  "allowed_votes": "integer",
  "allow_answers_until": "string (date-time)",
  "show_answers_after": "string (date-time)",
  "answers": {
    "1": "PostContentPollAnswer",
    "2": "PostContentPollAnswer"
  },
  "computed_values": "PostContentPollComputedValues"
}
```

### PostContentPollAnswer
```json
{
  "answer": "string",
  "result": {
    "respondents": "string"
  }
}
```

### PostContentPollComputedValues
```json
{
  "can_modify": "boolean",
  "user_did_vote": "boolean",
  "total_votes": "integer",
  "total_respondents": "integer",
  "maximum_answer_votes": "integer"
}
```

### PostContentDice
```json
{
  "reason": "string",
  "dice_count": "integer",
  "dice_sides": "integer",
  "allow_rolls_until": "string (date-time)",
  "show_rolls_after": "string (date-time)",
  "rolls": ["PostContentDiceRoll"]
}
```

### PostContentDiceRoll
```json
{
  "user": "UserSearch",
  "rolls": ["integer"]
}
```

### ContentFormat
- `"text"` - Prostý text
- `"html"` - HTML
- `"markdown"` - Markdown

### ContentFormatEnum
- `"text"` - Prostý text
- `"html"` - HTML (výchozí)

## Souborové struktury

### FileWithUrl
```json
{
  "id": "integer",
  "file_type": "FileTypeEnum",
  "id_specific": "integer | null",
  "id_specific2": "integer | null",
  "filename": "string",
  "size": "integer",
  "uploaded_at": "string (date-time)",
  "mimetype": "FileMimeTypeEnum",
  "image_width": "integer | null",
  "image_height": "integer | null",
  "image_avg_color_hex": "string | null",
  "image_embed": "boolean",
  "url": "string",
  "thumb_url": "string"
}
```

### FileTypeEnum
- `"free_file"` - Volný soubor
- `"mail_attachment"` - Příloha k poště
- `"mail_backup"` - Záloha pošty
- `"discussion_attachment"` - Příloha k diskuzi
- `"discussion_backup"` - Záloha diskuze
- `"market_attachment"` - Příloha k inzerátu
- `"event_attachment"` - Příloha k události

### FileMimeTypeEnum
- `"image/gif"` - GIF obrázek
- `"image/jpeg"` - JPEG obrázek
- `"image/png"` - PNG obrázek
- `"text/html"` - HTML soubor
- `"octet/stream"` - Binární soubor

## Poštovní struktury

### MailPost
```json
{
  "id": "integer",
  "username": "string",
  "incoming": "boolean",
  "content": "string",
  "reminder": "boolean",
  "unread": "boolean",
  "inserted_at": "string (date-time)",
  "activity": "Activity",
  "new": "boolean",
  "preview": "boolean"
}
```

### MailConversationWithActivity
```json
{
  "username": "string",
  "conversed_at": "string (date-time)",
  "incoming": "boolean",
  "has_unread_mail": "boolean",
  "activity": "Activity"
}
```

## Notifikační struktury

### Notification
```json
{
  "details": "NotificationDetails",
  "type": "string",
  "data": "DiscussionPostWithNameAndDiscussionName"
}
```

### NotificationDetails
```json
{
  "thumbs_up": ["NotificationThumbUp"],
  "replies": ["DiscussionPostWithName"]
}
```

### NotificationThumbUp
```json
{
  "username": "string",
  "inserted_at": "string (date-time)"
}
```

## Navigační struktury

### ApiNavigationDirection
- `"newest"` - Nejnovější
- `"newer_than"` - Novější než
- `"older_than"` - Starší než
- `"oldest"` - Nejstarší

## Vyhledávací struktury

### UsernameSearchResult
```json
{
  "exact": ["UsernameSearchResultRow"],
  "friends": ["UsernameSearchResultRow"],
  "others": ["UsernameSearchResultRow"]
}
```

### UsernameSearchResultRow
```json
{
  "user": "UserSearch",
  "activity": "Activity"
}
```

## Odpovědi API

### JsonOk
```json
{}
```
Prázdný objekt signalizující úspěch.

### JsonError
```json
{
  "error": "boolean",
  "code": "string",
  "message": "string"
}
```

## Poznámky k datovým typům

- **date-time**: ISO 8601 formát (`2024-01-31T20:39:42+02:00`)
- **integer**: Celé číslo
- **boolean**: `true` nebo `false`
- **string**: Textový řetězec
- **null**: Prázdná hodnota
- **array**: Pole hodnot `["item1", "item2"]`
- **object**: Objekt s vlastnostmi `{"key": "value"}`

## Union typy

Některé vlastnosti mohou mít více možných typů:
- `"string | null"` - buď string nebo null
- `"integer | null"` - buď integer nebo null
- `"TagTypeEnum | null"` - buď hodnota z enum nebo null

## Enum hodnoty

Všechny enum typy mají předem definované možné hodnoty. Používejte pouze hodnoty uvedené v dokumentaci.
