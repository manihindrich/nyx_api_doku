# Mail API

Mail API umožňuje správu zpráv a konverzací mezi uživateli. Poskytuje funkcionalitu pro načítání pošty, odesílání zpráv a správu upomínek.

## Endpoints

### GET /api/mail

Načte poštu s příspěvky.

**Popis**: Load mail with posts

**Parametry**:
- `user` (query, optional): Uživatelské jméno pro filtrování (Username)
- `text` (query, optional): Vyhledávací výraz (SearchExpression)
- `order` (query, optional): Směr navigace - newer_than a older_than vyžadují from_id (ApiNavigationDirection)
- `from_id` (query, optional): Používá se společně s 'order' pro získání příspěvků v určitém směru od konkrétního ID (integer, minimum: 1)

**Odpověď**:
- **200 OK**: Úspěšně vrácena pošta a seznam příspěvků
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/mail?user=USERNAME&order=newest"
```

**Příklad odpovědi**:
```json
{
  "context": {
    "user": {
      "username": "USERNAME",
      "mail_unread": 2,
      "mail_last_from": "SENDER",
      "notifications_unread": 0,
      "notifications_last_visit": "2024-01-31T20:39:42+02:00"
    },
    "active_friends": []
  },
  "conversations": [
    {
      "username": "FRIEND",
      "conversed_at": "2024-01-31T20:39:42+02:00",
      "incoming": true,
      "has_unread_mail": true,
      "activity": {
        "username": "FRIEND",
        "last_activity": "2024-01-31T20:39:42+02:00",
        "last_access_method": "Api",
        "status_details": "Online",
        "location": "Discussion",
        "location_url": "/discussion/123"
      }
    }
  ],
  "posts": [
    {
      "id": 456,
      "username": "FRIEND",
      "incoming": true,
      "content": "Ahoj, jak se máš?",
      "reminder": false,
      "unread": true,
      "inserted_at": "2024-01-31T20:39:42+02:00",
      "activity": {
        "username": "FRIEND",
        "last_activity": "2024-01-31T20:39:42+02:00",
        "last_access_method": "Api",
        "status_details": "Online",
        "location": "Discussion",
        "location_url": "/discussion/123"
      },
      "new": true,
      "preview": false
    }
  ],
  "reminders": [],
  "waiting_files": []
}
```

### POST /api/mail/send

Odeslání textového příspěvku.

**Popis**: Odeslání textového příspěvku

**Parametry**:
- `recipient` (form data, required): Příjemce zprávy (Username)
- `message` (form data, required): Obsah zprávy (string)
- `format` (form data, optional): Formát obsahu (ContentFormatEnum)

**Odpověď**:
- **200 OK**: Úspěch
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "recipient=USERNAME&message=Ahoj%2C%20jak%20se%20máš%3F&format=html" \
     https://nyx.cz/api/mail/send
```

### POST /api/mail/reminder/{id}/{newState}

Vytvoření upomínky.

**Popis**: Vytvoření upomínky

**Parametry**:
- `id` (path, required): ID zprávy (integer, minimum: 1)
- `newState` (path, required): Nový stav upomínky (boolean)

**Odpověď**:
- **200 OK**: Úspěch
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/mail/reminder/456/true
```

## Datové struktury

### MailConversationWithActivity

Konverzace s informacemi o aktivitě.

```json
{
  "username": "string",
  "conversed_at": "string (date-time)",
  "incoming": "boolean",
  "has_unread_mail": "boolean",
  "activity": "Activity"
}
```

### MailPost

Poštovní příspěvek.

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

### Activity

Informace o aktivitě uživatele.

```json
{
  "username": "string",
  "last_activity": "string (date-time)",
  "last_access_method": "string (Web|Api)",
  "status_details": "string",
  "location": "string",
  "location_url": "string"
}
```

### ContentFormatEnum

Možné formáty obsahu:
- `text` - Prostý text
- `html` - HTML formát (výchozí)

### ApiNavigationDirection

Možné směry navigace:
- `newest` - Nejnovější
- `newer_than` - Novější než
- `older_than` - Starší než
- `oldest` - Nejstarší

## Poznámky k implementaci

- Všechny endpointy vyžadují autentifikaci
- `incoming` označuje, zda je zpráva příchozí (true) nebo odchozí (false)
- `unread` označuje nepřečtené zprávy
- `reminder` označuje zprávy označené jako upomínky
- `new` označuje nové zprávy v aktuálním načtení
- `preview` označuje zkrácené zobrazení zprávy
- Parametry `newer_than` a `older_than` vyžadují zadání `from_id`
- `waiting_files` obsahuje soubory čekající na zpracování
- Formát zpráv může být `text` nebo `html`

## Chybové stavy

- **400 Bad Request**: Neplatné parametry nebo chyba v požadavku
- **401 Unauthorized**: Chybí nebo neplatný autentifikační token
- **404 Not Found**: Požadovaný zdroj neexistuje
- **500 Internal Server Error**: Vnitřní chyba serveru

## Příklady použití

### Načtení nejnovějších zpráv
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/mail?order=newest"
```

### Vyhledání zpráv od konkrétního uživatele
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/mail?user=USERNAME"
```

### Odeslání HTML zprávy
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "recipient=USERNAME&message=<p>Ahoj!</p>&format=html" \
     https://nyx.cz/api/mail/send
```

### Označení zprávy jako upomínka
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/mail/reminder/456/true
