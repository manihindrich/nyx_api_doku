# Bookmarks API

Bookmarks API umožňuje správu záložek a historie navštívených diskuzí. Poskytuje funkcionalitu pro načítání záložek, historie a manipulaci s nimi.

## Endpoints

### GET /api/bookmarks

Načte bookmarky podle nastavení uživatele.

**Popis**: Načte bookmarky podle nastavení uživatele

**Parametry**:
- `expand` (query, optional): Rozbalit nějakou konkrétní kategorii (integer)

**Odpověď**:
- **200 OK**: Vrátí seznam kategorií s bookmarky

**Příklad požadavku**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/bookmarks?expand=1"
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
  "reminder_count": 5,
  "bookmarks": [
    {
      "category": {
        "id": 1,
        "category_name": "Oblíbené"
      },
      "bookmarks": [
        {
          "discussion_id": 123,
          "is_owner": false,
          "full_name": "Zajímavá diskuze",
          "new_replies_count": 3,
          "new_posts_count": 5,
          "new_links_count": 1,
          "new_images_count": 2,
          "last_visited_at": "2024-01-31T20:39:42+02:00"
        }
      ]
    }
  ]
}
```

### GET /api/bookmarks/all

Načte bookmarky se všemi kategoriemi rozbalenými.

**Popis**: Načte bookmarky se všemi kategoriemi rozbalenými

**Parametry**: Žádné

**Odpověď**:
- **200 OK**: Vrátí seznam kategorií s bookmarky

**Příklad požadavku**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/bookmarks/all
```

### GET /api/bookmarks/history

Načte historii navštívených diskuzí.

**Popis**: Načte historii navštívených diskuzí

**Parametry**:
- `more_results` (query, optional): Zobrazovat více výsledků? (boolean)
- `show_read` (query, optional): Zobrazovat i diskuze s nula novými? Pokud chybí, použije se hodnota pro web rozhraní (boolean)
- `show_booked` (query, optional): Zobrazovat i sledované diskuze? Pokud chybí, použije se hodnota pro web rozhraní (boolean)

**Odpověď**:
- **200 OK**: Vrátí seznam kategorií s bookmarky

**Příklad požadavku**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/bookmarks/history?show_read=true&show_booked=false"
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
  "discussions": [
    {
      "discussion_id": 123,
      "is_owner": false,
      "full_name": "Navštívená diskuze",
      "new_replies_count": 0,
      "new_posts_count": 0,
      "new_links_count": 0,
      "new_images_count": 0,
      "last_visited_at": "2024-01-31T20:39:42+02:00"
    }
  ],
  "show_load_more": true
}
```

### GET /api/bookmarks/history/more

**DEPRECATED** - Načte historii navštívených diskuzí s více záznamy.

**Popis**: Načte historii navštívených diskuzí s více záznamy

**Parametry**:
- `show_read` (query, optional): Zobrazovat i diskuze s nula novými? (boolean)
- `show_booked` (query, optional): Zobrazovat i sledované diskuze? (boolean)

**Odpověď**:
- **200 OK**: Vrátí seznam kategorií s bookmarky

### POST /api/bookmarks/history/remove_from_history

Odebere diskuze z historie.

**Popis**: Odebere diskuze z historie

**Parametry**:
- `discussion_ids` (form data, required): Pole ID diskuzí k odebrání (array of integers)

**Odpověď**:
- **200 OK**: Úspěch
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "discussion_ids[]=123&discussion_ids[]=456" \
     https://nyx.cz/api/bookmarks/history/remove_from_history
```

### POST /api/bookmarks/history/mark_as_read

Označí diskuze za přečtené.

**Popis**: Označí diskuze za přečtené

**Parametry**:
- `discussion_ids` (form data, required): Pole ID diskuzí k označení (array of integers)

**Odpověď**:
- **200 OK**: Úspěch
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "discussion_ids[]=123&discussion_ids[]=456" \
     https://nyx.cz/api/bookmarks/history/mark_as_read
```

## Datové struktury

### BookmarksData

Hlavní struktura odpovědi pro bookmarks API.

```json
{
  "context": "Context",
  "reminder_count": "integer",
  "bookmarks": ["BookmarkDataGroup"]
}
```

### BookmarkDataGroup

Skupina záložek podle kategorie.

```json
{
  "category": "DiscussionBookmarkCategory",
  "bookmarks": ["BookmarkedDiscussion"]
}
```

### DiscussionBookmarkCategory

Kategorie záložek.

```json
{
  "id": "integer",
  "category_name": "string"
}
```

### BookmarkedDiscussion

Diskuze v záložkách nebo historii.

```json
{
  "discussion_id": "integer",
  "is_owner": "boolean",
  "full_name": "string",
  "new_replies_count": "integer",
  "new_posts_count": "integer",
  "new_links_count": "integer",
  "new_images_count": "integer",
  "last_visited_at": "string (date-time)"
}
```

## Poznámky k implementaci

- Všechny endpointy vyžadují autentifikaci
- `expand` parametr rozbalí konkrétní kategorii záložek
- Historie obsahuje informace o nových příspěvcích od poslední návštěvy
- `show_load_more` indikuje, zda je možné načíst více záznamů
- Form data pro POST požadavky používá explode formát pro pole
- Endpoint `/api/bookmarks/history/more` je označen jako deprecated

## Chybové stavy

- **400 Bad Request**: Neplatné parametry nebo chyba v požadavku
- **401 Unauthorized**: Chybí nebo neplatný autentifikační token
- **404 Not Found**: Požadovaný zdroj neexistuje
- **500 Internal Server Error**: Vnitřní chyba serveru
