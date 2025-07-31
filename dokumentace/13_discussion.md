# Discussion API

Discussion API umožňuje správu diskuzí a příspěvků. Poskytuje funkcionalitu pro načítání diskuzí, odesílání příspěvků, hodnocení, správu upomínek a práv.

## Endpoints

### GET /api/discussion/{discussionId}

Načte diskuzi s příspěvky.

**Popis**: Load discussion with posts

**Parametry**:
- `discussionId` (path, required): ID diskuze (integer, minimum: 1)
- `user` (query, optional): Uživatelské jméno pro filtrování (Username)
- `text` (query, optional): Vyhledávací výraz (SearchExpression)
- `rating` (query, optional): Záporná čísla zobrazí příspěvky s hodnocením nižším než hodnota, kladná s vyšším. Vypne textové vyhledávání (integer)
- `reminders` (query, optional): Pouze příspěvky v upomínkách. Vypne textové vyhledávání (integer)
- `order` (query, optional): Směr navigace - newer_than a older_than vyžadují from_id (ApiNavigationDirection)
- `from_id` (query, optional): Používá se společně s 'order' pro získání příspěvků v určitém směru od konkrétního ID (integer, minimum: 1)

**Odpověď**:
- **200 OK**: Úspěšně vrácena diskuze a seznam příspěvků
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/discussion/123?order=newest"
```

### POST /api/discussion/{discussionId}/send/text

Odeslání textového příspěvku.

**Popis**: Odeslání textového příspěvku

**Parametry**:
- `discussionId` (path, required): ID diskuze (integer, minimum: 1)
- `content` (form data, required): Obsah příspěvku (string)
- `format` (form data, optional): Formát obsahu (ContentFormatEnum)

**Odpověď**:
- **200 OK**: Úspěch
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "content=Můj%20příspěvek&format=html" \
     https://nyx.cz/api/discussion/123/send/text
```

### GET /api/discussion/{discussion_id}/rating/{id}

Načtení hodnocení příspěvku.

**Popis**: Načtení hodnocení příspěvku

**Parametry**:
- `discussion_id` (path, required): ID diskuze (integer, minimum: 1)
- `id` (path, required): ID příspěvku (integer, minimum: 1)

**Odpověď**:
- **200 OK**: Načteno hodnocení
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/discussion/123/rating/456
```

### POST /api/discussion/{discussion_id}/rating/{id}/{action}

Odeslání hodnocení příspěvku.

**Popis**: Odeslání hodnocení příspěvku

**Parametry**:
- `discussion_id` (path, required): ID diskuze (integer, minimum: 1)
- `id` (path, required): ID příspěvku (integer, minimum: 1)
- `action` (path, required): Akce hodnocení (RatingAction)

**Odpověď**:
- **200 OK**: Uděleno hodnocení
- **400 Bad Request**: Chyba v požadavku
- **403 Forbidden**: Uživatel si nepřeje dostávat anonymní hlasy

**Příklad požadavku**:
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/discussion/123/rating/456/positive
```

### POST /api/discussion/{discussion_id}/reminder/{id}/{new_state}

Nastaví jestli je příspěvek v upomínkách nebo ne.

**Popis**: Nastaví jestli je příspěvek v upomínkách nebo ne

**Parametry**:
- `discussion_id` (path, required): ID diskuze (integer, minimum: 1)
- `id` (path, required): ID příspěvku (integer, minimum: 1)
- `new_state` (path, required): Nový stav upomínky (boolean)

**Odpověď**:
- **200 OK**: Úspěch
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/discussion/123/reminder/456/true
```

### POST /api/discussion/{discussion_id}/bookmark

Nastaví jestli je diskuze v bookmarkách nebo ne.

**Popis**: Nastaví jestli je diskuze v bookmarkách nebo ne

**Parametry**:
- `discussion_id` (path, required): ID diskuze (integer, minimum: 1)
- `new_state` (query, required): Vložit/vyřadit do/z bookmarků (boolean)
- `category` (query, optional): Kategorie, kam ho dát (integer)

**Odpověď**:
- **200 OK**: Úspěch
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/discussion/123/bookmark?new_state=true&category=1"
```

### DELETE /api/discussion/{discussion_id}/delete/{id}

Smaže příspěvek.

**Popis**: Smaže příspěvek

**Parametry**:
- `discussion_id` (path, required): ID diskuze (integer, minimum: 1)
- `id` (path, required): ID příspěvku (integer, minimum: 1)

**Odpověď**:
- **200 OK**: Úspěch
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -X DELETE \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/discussion/123/delete/456
```

### POST /api/discussion/rights/add

Přidá uživatele do uživatelských práv.

**Popis**: Přidá uživatele do uživatelských práv

**Parametry**:
- `discussion_id` (query, required): ID diskuze (integer, minimum: 1)
- `username` (query, required): Uživatelské jméno (Username)

**Odpověď**:
- **200 OK**: Úspěch
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/discussion/rights/add?discussion_id=123&username=USERNAME"
```

### POST /api/discussion/rights

Nastaví uživateli (nebo globálně) právo na novou hodnotu.

**Popis**: Nastaví uživateli (nebo globálně) právo na novou hodnotu

**Parametry**:
- `discussion_id` (query, required): ID diskuze (integer, minimum: 1)
- `username` (query, optional): Uživatelské jméno (Username)
- `right` (query, required): Typ práva (AccessRightType)
- `set` (query, required): Nastavit právo (boolean)

**Odpověď**:
- **200 OK**: Úspěch
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/discussion/rights?discussion_id=123&username=USERNAME&right=write&set=true"
```

### POST /api/discussion/{discussionId}/content/{contentId}/save

Úprava položky na nástěnce.

**Popis**: Úprava položky na nástěnce

**Parametry**:
- `discussionId` (path, required): ID diskuze (integer, minimum: 1)
- `contentId` (path, required): ID obsahu (integer, minimum: 1)
- `content` (form data, required): Obsah (string)
- `format` (form data, optional): Formát obsahu (ContentFormatEnum)

**Odpověď**:
- **200 OK**: Úspěch
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "content=Upravený%20obsah&format=html" \
     https://nyx.cz/api/discussion/123/content/789/save
```

## Datové struktury

### TemplatePost

Příspěvek v diskuzi s rozšířenými informacemi.

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

### DiscussionCommon

Společné informace o diskuzi.

```json
{
  "discussion": "Discussion",
  "owner": "UserDiscussionOwner",
  "access_right": "DiscussionAccessRight | null",
  "bookmark": "DiscussionBookmark | null",
  "waiting_files": ["FileWithUrl"]
}
```

### RatingAction

Možné akce hodnocení:
- `remove` - Odebrat hodnocení
- `positive` - Kladné hodnocení
- `negative` - Záporné hodnocení
- `negative_visible` - Záporné hodnocení viditelné

### AccessRightType

Typy přístupových práv:
- `read` - Čtení
- `write` - Psaní
- `delete` - Mazání
- `edit` - Úpravy
- `edit_rights` - Úprava práv
- `grant_edit_rights` - Udělování práv na úpravy
- `public` - Veřejné

### PostTypeEnum

Typy příspěvků:
- `text` - Textový příspěvek
- `poll` - Anketa
- `dice` - Kostky
- `log_message` - Log zpráva
- `event` - Událost
- `advertisement` - Inzerát
- `discussion_request` - Požadavek na diskuzi
- `registration` - Registrace

### TagTypeEnum

Typy hodnocení:
- `positive` - Kladné
- `negative` - Záporné
- `negative_visible` - Záporné viditelné
- `removed` - Odebráno
- `reminder` - Upomínka

## Poznámky k implementaci

- Všechny endpointy vyžadují autentifikaci
- Hodnocení `negative_visible` se používá pro potvrzení záporného hodnocení
- Parametry `newer_than` a `older_than` vyžadují zadání `from_id`
- `rating` parametr vypíná textové vyhledávání
- `reminders` parametr vypíná textové vyhledávání
- Práva lze nastavovat globálně (bez username) nebo konkrétnímu uživateli
- `can_be_*` pole určují, jaké akce může uživatel provádět
- `rating_friends` obsahuje seznam přátel, kteří příspěvek hodnotili

## Chybové stavy

- **400 Bad Request**: Neplatné parametry nebo chyba v požadavku
- **401 Unauthorized**: Chybí nebo neplatný autentifikační token
- **403 Forbidden**: Nedostatečná oprávnění nebo speciální podmínky
- **404 Not Found**: Diskuze nebo příspěvek neexistuje
- **500 Internal Server Error**: Vnitřní chyba serveru

## Příklady použití

### Načtení diskuze s nejnovějšími příspěvky
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/discussion/123?order=newest"
```

### Vyhledání příspěvků od konkrétního uživatele
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/discussion/123?user=USERNAME"
```

### Odeslání HTML příspěvku
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "content=<p>Můj příspěvek</p>&format=html" \
     https://nyx.cz/api/discussion/123/send/text
```

### Kladné hodnocení příspěvku
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/discussion/123/rating/456/positive
```

### Přidání diskuze do bookmarků
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/discussion/123/bookmark?new_state=true&category=1"
