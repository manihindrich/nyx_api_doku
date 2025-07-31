# Notepad API

Notepad API umožňuje správu poznámkového bloku uživatele. Poskytuje funkcionalitu pro načítání seznamu poznámek a zobrazení konkrétních záznamů.

## Endpoints

### GET /api/notepad

Načte seznam všech poznámek uživatele.

**Popis**: Načte obsah bloku

**Parametry**: Žádné

**Odpověď**:
- **200 OK**: Vrátí seznam kategorií s bookmarky - selected_entry je prázdná
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/notepad
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
  "selected_entry": null,
  "entries": [
    {
      "id": 1,
      "category_id": null,
      "title": "Moje poznámka",
      "public": false,
      "inserted_at": "2024-01-31T20:39:42+02:00",
      "updated_at": "2024-01-31T20:39:42+02:00"
    }
  ]
}
```

### GET /api/notepad/{entry_id}

Načte konkrétní poznámku podle ID.

**Popis**: Načte obsah bloku

**Parametry**:
- `entry_id` (path, required): ID poznámky k zobrazení (integer)

**Odpověď**:
- **200 OK**: Vrátí seznam kategorií s bookmarky - selected_entry je naplněna pokud existuje
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/notepad/123
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
  "selected_entry": {
    "id": 123,
    "category_id": null,
    "title": "Moje poznámka",
    "content": "<p>Obsah poznámky v HTML formátu</p>",
    "content_raw": "Obsah poznámky v raw formátu",
    "public": false,
    "sharing_token": "abc123def456",
    "inserted_at": "2024-01-31T20:39:42+02:00",
    "updated_at": "2024-01-31T20:39:42+02:00"
  },
  "entries": [
    {
      "id": 123,
      "category_id": null,
      "title": "Moje poznámka",
      "public": false,
      "inserted_at": "2024-01-31T20:39:42+02:00",
      "updated_at": "2024-01-31T20:39:42+02:00"
    }
  ]
}
```

## Datové struktury

### NotepadData

Hlavní struktura odpovědi pro notepad API.

```json
{
  "context": "Context",
  "selected_entry": "NotepadEntry | null",
  "entries": ["NotepadEntryMinimal"]
}
```

### NotepadEntry

Kompletní struktura poznámky.

```json
{
  "id": "integer",
  "category_id": "integer | null",
  "title": "string",
  "content": "string",
  "content_raw": "string",
  "public": "boolean",
  "sharing_token": "string",
  "inserted_at": "string (date-time)",
  "updated_at": "string (date-time)"
}
```

### NotepadEntryMinimal

Zjednodušená struktura poznámky pro seznam.

```json
{
  "id": "integer",
  "category_id": "integer | null",
  "title": "string",
  "public": "boolean",
  "inserted_at": "string (date-time)",
  "updated_at": "string (date-time)"
}
```

## Poznámky k implementaci

- Všechny endpointy vyžadují autentifikaci
- `selected_entry` je `null` při načítání seznamu bez konkrétního ID
- `category_id` může být `null` pro nezařazené poznámky
- `public` určuje, zda je poznámka veřejně přístupná
- `sharing_token` slouží pro sdílení poznámek
- Časové údaje jsou ve formátu ISO 8601

## Chybové stavy

- **400 Bad Request**: Neplatné parametry nebo chyba v požadavku
- **401 Unauthorized**: Chybí nebo neplatný autentifikační token
- **404 Not Found**: Poznámka s daným ID neexistuje
- **500 Internal Server Error**: Vnitřní chyba serveru
