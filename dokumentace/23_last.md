# Last Posts API

Last Posts API umožňuje načítání nejnovějších příspěvků z platformy s různými filtry a možnostmi řazení.

## Endpoints

### GET /api/last

Vrátí seznam posledních příspěvků.

**Popis**: Vrátí seznam posledních příspěvků

**Parametry**:
- `domain` (query, optional): Kategorie diskuzí (integer)
- `min_rating` (query, optional): Minimální hodnocení (integer)
- `rated_by_friends` (query, optional): Příspěvky hodnocené přáteli (boolean)
- `rated_by_me` (query, optional): Příspěvky hodnocené mnou (boolean)

**Odpověď**:
- **200 OK**: Úspěšně vrácen seznam posledních příspěvků
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/last?domain=1&min_rating=5&rated_by_friends=true"
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
      "content": "Obsah nejnovějšího příspěvku",
      "content_raw": {
        "data": "Obsah nejnovějšího příspěvku",
        "format": "html"
      },
      "post_type": "text",
      "reminder": false,
      "rating": 8,
      "my_rating": "positive",
      "replies": [789, 790],
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
      "rating_friends": ["FRIEND1", "FRIEND2"]
    }
  ],
  "ignored_domains": [
    {
      "user_id": 1,
      "domain_id": 2,
      "name": "Ignorovaná kategorie",
      "ignored": true
    }
  ],
  "ignored_discussions": [
    {
      "user_id": 1,
      "discussion_id": 999,
      "full_name": "Ignorovaná diskuze"
    }
  ]
}
```

## Datové struktury

### LastIgnoredDomainsWithName

Ignorované domény s názvy.

```json
{
  "user_id": "integer",
  "domain_id": "integer", 
  "name": "string",
  "ignored": "boolean"
}
```

### LastIgnoredDiscussionsWithName

Ignorované diskuze s názvy.

```json
{
  "user_id": "integer",
  "discussion_id": "integer",
  "full_name": "string"
}
```

## Filtry a parametry

### domain
Filtruje příspěvky podle kategorie diskuzí:
- Číselná hodnota odpovídající ID domény/kategorie
- Bez parametru se zobrazí příspěvky ze všech kategorií

### min_rating
Filtruje příspěvky podle minimálního hodnocení:
- Zobrazí pouze příspěvky s hodnocením vyšším nebo rovným zadané hodnotě
- Hodnocení je součet všech kladných a záporných hlasů

### rated_by_friends
Filtruje příspěvky hodnocené přáteli:
- `true`: Zobrazí pouze příspěvky, které hodnotil alespoň jeden přítel
- `false`: Zobrazí všechny příspěvky bez ohledu na hodnocení přátel

### rated_by_me
Filtruje příspěvky podle vlastního hodnocení:
- `true`: Zobrazí pouze příspěvky, které jsem hodnotil
- `false`: Zobrazí všechny příspěvky bez ohledu na mé hodnocení

## Poznámky k implementaci

- Všechny endpointy vyžadují autentifikaci
- Příspěvky jsou řazeny podle času vložení (nejnovější první)
- `preview` označuje zkrácené zobrazení obsahu
- `rating_friends` obsahuje seznam přátel, kteří příspěvek hodnotili
- `ignored_domains` obsahuje kategorie, které uživatel ignoruje
- `ignored_discussions` obsahuje konkrétní diskuze, které uživatel ignoruje
- Filtry lze kombinovat pro přesnější výsledky
- API respektuje uživatelská nastavení pro ignorované obsahy

## Chybové stavy

- **400 Bad Request**: Neplatné parametry nebo chyba v požadavku
- **401 Unauthorized**: Chybí nebo neplatný autentifikační token
- **404 Not Found**: Požadovaný zdroj neexistuje
- **500 Internal Server Error**: Vnitřní chyba serveru

## Příklady použití

### Načtení všech nejnovějších příspěvků
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/last
```

### Příspěvky z konkrétní kategorie
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/last?domain=1"
```

### Příspěvky s vysokým hodnocením
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/last?min_rating=10"
```

### Příspěvky hodnocené přáteli
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/last?rated_by_friends=true"
```

### Příspěvky, které jsem hodnotil
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/last?rated_by_me=true"
```

### Kombinace filtrů
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/last?domain=1&min_rating=5&rated_by_friends=true"
```

### Pouze vysoce hodnocené příspěvky od přátel
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://nyx.cz/api/last?min_rating=15&rated_by_friends=true"
```

## Tipy pro použití

- Použijte `min_rating` pro filtrování kvalitního obsahu
- Kombinujte `rated_by_friends` s `min_rating` pro objevování zajímavého obsahu
- `domain` filtr je užitečný pro sledování konkrétních témat
- `rated_by_me` pomáhá najít příspěvky, se kterými jste interagovali
- Ignorované obsahy se automaticky nezobrazují v seznamu
