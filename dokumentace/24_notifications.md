# Notifications API

Notifications API umožňuje správu notifikací a registraci zařízení pro příjem push notifikací.

## Endpoints

### GET /api/notifications

Seznam notifikací.

**Popis**: Seznam notifikací

**Parametry**: Žádné

**Odpověď**:
- **200 OK**: Notifikace
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/notifications
```

**Příklad odpovědi**:
```json
{
  "context": {
    "user": {
      "username": "USERNAME",
      "mail_unread": 0,
      "mail_last_from": null,
      "notifications_unread": 2,
      "notifications_last_visit": "2024-01-31T20:39:42+02:00"
    },
    "active_friends": []
  },
  "posts": [
    {
      "details": {
        "thumbs_up": [
          {
            "username": "FRIEND",
            "inserted_at": "2024-01-31T20:39:42+02:00"
          }
        ],
        "replies": [
          {
            "id": 789,
            "discussion_id": 123,
            "username": "FRIEND",
            "content": "Odpověď na váš příspěvek",
            "content_raw": {
              "data": "Odpověď na váš příspěvek",
              "format": "html"
            },
            "post_type": "text",
            "reminder": false,
            "rating": 0,
            "my_rating": null,
            "replies": [],
            "inserted_at": "2024-01-31T20:39:42+02:00"
          }
        ]
      },
      "type": "post",
      "data": {
        "id": 456,
        "discussion_id": 123,
        "username": "USERNAME",
        "content": "Můj původní příspěvek",
        "content_raw": {
          "data": "Můj původní příspěvek",
          "format": "html"
        },
        "post_type": "text",
        "reminder": false,
        "rating": 1,
        "my_rating": null,
        "replies": [789],
        "inserted_at": "2024-01-31T20:39:42+02:00",
        "discussion_name": "Název diskuze"
      }
    }
  ]
}
```

### POST /api/register_for_notifications/{token}/{client}/{client_token}

Zaregistruje dané zařízení pro příjem notifikací k příslušnému tokenu.

**Popis**: Zaregistruje dané zařízení pro příjem notifikací k příslušnému tokenu

**Parametry**:
- `token` (path, required): Auth token nyxi (tj. to, co se posílá normálně přes Authorization Bearer) - pro případ, že by se autorizaci přes token A registrovala notifikace na token B (string)
- `client` (path, required): Dohodnutý název klienta (string)
  - Možné hodnoty: `nyx`, `fyx`, `nyxdroid`
- `client_token` (path, required): Autorizační token pro dané zařízení na notifikace (u firebase očekávám cca 140 znaků, u apns 64 znaků) (string)

**Odpověď**:
- **200 OK**: Úspěch
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/register_for_notifications/YOUR_TOKEN/nyxdroid/FIREBASE_TOKEN_HERE
```

## Datové struktury

### Notification

Notifikace s detaily.

```json
{
  "details": "NotificationDetails",
  "type": "string",
  "data": "DiscussionPostWithNameAndDiscussionName"
}
```

### NotificationDetails

Detaily notifikace.

```json
{
  "thumbs_up": ["NotificationThumbUp"],
  "replies": ["DiscussionPostWithName"]
}
```

### NotificationThumbUp

Informace o kladném hodnocení.

```json
{
  "username": "string",
  "inserted_at": "string (date-time)"
}
```

### DiscussionPostWithNameAndDiscussionName

Příspěvek s názvem diskuze pro notifikace.

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
  "my_rating": "TagTypeEnum",
  "replies": ["integer"],
  "inserted_at": "string (date-time)",
  "discussion_name": "string"
}
```

## Typy notifikací

### post
Notifikace o aktivitě na příspěvku:
- **thumbs_up**: Seznam uživatelů, kteří dali kladné hodnocení
- **replies**: Seznam odpovědí na příspěvek

## Podporované klienty

### nyx
Webový klient Nyx.cz

### fyx  
Mobilní aplikace Fyx

### nyxdroid
Android aplikace

## Poznámky k implementaci

- Všechny endpointy vyžadují autentifikaci
- Registrace notifikací umožňuje použít jiný token než aktuální session
- `client_token` je specifický pro každou platformu:
  - Firebase (Android): ~140 znaků
  - APNS (iOS): ~64 znaků
- Notifikace jsou seskupeny podle typu aktivity
- `details` obsahuje agregované informace o všech aktivitách
- `data` obsahuje původní příspěvek, ke kterému se notifikace vztahuje

## Chybové stavy

- **400 Bad Request**: Neplatné parametry nebo chyba v požadavku
- **401 Unauthorized**: Chybí nebo neplatný autentifikační token
- **404 Not Found**: Požadovaný zdroj neexistuje
- **500 Internal Server Error**: Vnitřní chyba serveru

## Příklady použití

### Načtení notifikací
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/notifications
```

### Registrace Android zařízení
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/register_for_notifications/YOUR_TOKEN/nyxdroid/FIREBASE_TOKEN_140_CHARS
```

### Registrace iOS zařízení
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/register_for_notifications/YOUR_TOKEN/fyx/APNS_TOKEN_64_CHARS
```

### Registrace webového klienta
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/register_for_notifications/YOUR_TOKEN/nyx/WEB_PUSH_TOKEN
```

## Bezpečnostní poznámky

- Tokeny pro notifikace jsou citlivé informace
- Registrujte pouze důvěryhodná zařízení
- Pravidelně obnovujte registrace pro aktivní zařízení
- Zrušte registrace pro nepoužívaná zařízení
