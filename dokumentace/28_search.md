# Search API

Search API umožňuje vyhledávání v obsahu platformy. Poskytuje funkcionalitu pro vyhledávání uživatelů, příspěvků a diskuzí s různými filtry a možnostmi.

## Endpoints

### GET /api/search/username/{username}

Hledá uživatele podle počátečních písmen v nicku.

**Popis**: Hledá uživatele podle počátečních písmen v nicku

**Parametry**:
- `username` (path, required): Část uživatelského jména [A-Z0-9_]{2,15} (string)

**Odpověď**:
- **200 OK**: Nalezení uživatelé
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/search/username/USER
```

**Příklad odpovědi**:
```json
{
  "exact": [
    {
      "user": {
        "username": "USER"
      },
      "activity": {
        "username": "USER",
        "last_activity": "2024-01-31T20:39:42+02:00",
        "last_access_method": "Api",
        "status_details": "Online",
        "location": "Discussion",
        "location_url": "/discussion/123"
      }
    }
  ],
  "friends": [
    {
      "user": {
        "username": "USERFRIEND"
      },
      "activity": {
        "username": "USERFRIEND",
        "last_activity": "2024-01-31T20:39:42+02:00",
        "last_access_method": "Web",
        "status_details": "Online",
        "location": "Mail",
        "location_url": "/mail"
      }
    }
  ],
  "others": [
    {
      "user": {
        "username": "USERNAME123"
      },
      "activity": {
        "username": "USERNAME123",
        "last_activity": "2024-01-31T20:39:42+02:00",
        "last_access_method": "Web",
        "status_details": "Offline",
        "location": "",
        "location_url": ""
      }
    }
  ]
}
```

### GET /api/search

**DEPRECATED** - Načte vyhledávání s příspěvky.

**Popis**: Load search with posts

**Parametry**:
- `user` (query, optional): Uživatelské jméno (Username)
- `text` (query, optional): Vyhledávací výraz (SearchExpression)

**Odpověď**:
- **200 OK**: Úspěšně vrácena pošta a seznam příspěvků
- **400 Bad Request**: Chyba v požadavku

### GET /api/search-v2

Načte vyhledávání s příspěvky (nová verze).

**Popis**: Load search with posts

**Parametry**:
- `user` (query, optional): Uživatelské jméno (Username)
- `text` (query, optional): Vyhledávací výraz (SearchExpression)
- `order` (query, optional): Směr navigace - newer_than a older_than vyžadují from_id (ApiNavigationDirection)
- `from_id` (query, optional): Používá se společně s 'order' pro získání příspěvků v určitém směru od konkrétního ID (integer, minimum: 1)

**Odpověď**:
- **200 OK**: Úspěšně vrácena pošta a seznam příspěvků
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/search-v2?text=hledaný%20text&order=newest"
```

**Příklad odpovědi**:
```json
{
  "context": {
    "user": {
      "username": "USERNAME",
      "mail_unread": 0,
      "mail_last_from": null,
      "notifications_unread": 0,
      "notifications_last_visit": "2024-01-31T20:39:42+02:00"
    },
    "active_friends": []
  },
  "posts": [
    {
      "id": 123,
      "discussion_id": 456,
      "username": "AUTHOR",
      "content": "Obsah příspěvku s hledaným textem",
      "content_raw": {
        "data": "Obsah příspěvku s hledaným textem",
        "format": "html"
      },
      "post_type": "text",
      "reminder": false,
      "rating": 5,
      "my_rating": null,
      "replies": [],
      "inserted_at": "2024-01-31T20:39:42+02:00",
      "activity": {
        "username": "AUTHOR",
        "last_activity": "2024-01-31T20:39:42+02:00",
        "last_access_method": "Web",
        "status_details": "Online",
        "location": "Discussion",
        "location_url": "/discussion/456"
      },
      "new": false,
      "preview": true,
      "can_be_deleted": false,
      "can_be_rated": true,
      "can_be_reminded": true,
      "can_ignore_discussion": true,
      "rating_friends": []
    }
  ]
}
```

### GET /api/search/unified

Jednotné vyhledávání napříč obsahem.

**Popis**: Load search with posts

**Parametry**:
- `search` (query, required): Vyhledávací výraz s různými možnostmi:
  - `foo` - hledá diskuze, události a inzeráty
  - `@foo` - hledá uživatele začínající na foo
  - `@foo bar` - hledá příspěvky od @foo obsahující bar (SearchExpression)
- `limit` (query, optional): Limit výsledků (integer, default: 5)

**Odpověď**:
- **200 OK**: Úspěšně vráceny výsledky vyhledávání
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/search/unified?search=@USERNAME%20text&limit=10"
```

**Příklady odpovědí**:

**Vyhledávání uživatelů (@foo)**:
```json
{
  "exact": [
    {
      "user": {
        "username": "FOO"
      },
      "activity": {
        "username": "FOO",
        "last_activity": "2024-01-31T20:39:42+02:00",
        "last_access_method": "Api",
        "status_details": "Online",
        "location": "Discussion",
        "location_url": "/discussion/123"
      }
    }
  ],
  "friends": [],
  "others": []
}
```

**Vyhledávání diskuzí (foo)**:
```json
{
  "discussions": [
    {
      "id": 123,
      "discussion_type": "discussion",
      "discussion_name": "Zajímavá diskuze",
      "discussion_name_highlighted": "Zajímavá <mark>foo</mark> diskuze",
      "summary": "Popis diskuze",
      "summary_highlighted": "Popis <mark>foo</mark> diskuze"
    }
  ],
  "events": [],
  "advertisements": []
}
```

**Vyhledávání příspěvků (@foo bar)**:
```json
[
  {
    "discussion_id": 123,
    "post_id": 456,
    "discussion_name": "Diskuze",
    "discussion_name_highlighted": "Diskuze",
    "content": "Obsah příspěvku s hledaným textem"
  }
]
```

## Datové struktury

### UsernameSearchResult

Výsledek vyhledávání uživatelů.

```json
{
  "exact": ["UsernameSearchResultRow"],
  "friends": ["UsernameSearchResultRow"],
  "others": ["UsernameSearchResultRow"]
}
```

### UsernameSearchResultRow

Řádek výsledku vyhledávání uživatele.

```json
{
  "user": "UserSearch",
  "activity": "Activity"
}
```

### UnifiedSearchDiscussionResult

Výsledek vyhledávání diskuzí.

```json
{
  "discussions": ["UnifiedSearchRowDiscussion"],
  "events": ["UnifiedSearchRowDiscussion"],
  "advertisements": ["UnifiedSearchRowDiscussion"]
}
```

### UnifiedSearchRowDiscussion

Řádek výsledku vyhledávání diskuze.

```json
{
  "id": "integer",
  "discussion_type": "DiscussionTypeEnum",
  "discussion_name": "string",
  "discussion_name_highlighted": "string",
  "summary": "string | null",
  "summary_highlighted": "string | null"
}
```

### UnifiedSearchRowPost

Řádek výsledku vyhledávání příspěvku.

```json
{
  "discussion_id": "integer",
  "post_id": "integer",
  "discussion_name": "string",
  "discussion_name_highlighted": "string",
  "content": "string"
}
```

### SearchExpression

Vyhledávací výraz s možnostmi:
- `=foo` - přesná shoda
- `"phrase match"` - fráze
- `@username` - od konkrétního uživatele
- Kombinace výše uvedených

## Poznámky k implementaci

- Všechny endpointy vyžadují autentifikaci
- `/api/search` je označen jako deprecated, používejte `/api/search-v2`
- Unified search automaticky rozpoznává typ vyhledávání podle formátu
- `highlighted` pole obsahují HTML s `<mark>` tagy pro zvýraznění
- Výsledky jsou rozděleny podle typu (exact, friends, others pro uživatele)
- Limit se aplikuje na každou kategorii výsledků
- Parametry `newer_than` a `older_than` vyžadují zadání `from_id`
- Vyhledávání uživatelů vyžaduje minimálně 2 znaky

## Chybové stavy

- **400 Bad Request**: Neplatné parametry nebo chyba v požadavku
- **401 Unauthorized**: Chybí nebo neplatný autentifikační token
- **404 Not Found**: Požadovaný zdroj neexistuje
- **500 Internal Server Error**: Vnitřní chyba serveru

## Příklady použití

### Vyhledání uživatelů začínajících na "USER"
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/search/username/USER
```

### Vyhledání příspěvků obsahujících text
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/search-v2?text=hledaný%20text"
```

### Vyhledání příspěvků od konkrétního uživatele
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/search-v2?user=USERNAME"
```

### Jednotné vyhledávání diskuzí
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/search/unified?search=diskuze&limit=5"
```

### Vyhledání uživatelů přes unified search
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/search/unified?search=@USER"
```

### Vyhledání příspěvků od uživatele s textem
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/search/unified?search=@USERNAME%20hledaný%20text"
