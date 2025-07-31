# Přehled dokumentace NYX.CZ API

Tento dokument poskytuje stručný přehled všech částí dokumentace NYX.CZ API.

## Struktura dokumentace

### 📝 [01_notepad.md](./01_notepad.md)
**Správa poznámkového bloku**
- `GET /api/notepad` - seznam poznámek
- `GET /api/notepad/{entry_id}` - konkrétní poznámka
- Datové struktury: NotepadEntry, NotepadEntryMinimal
- Práce s kategoriemi a veřejnými poznámkami

### 🔖 [04_bookmarks.md](./04_bookmarks.md)
**Záložky a historie diskuzí**
- `GET /api/bookmarks` - záložky podle nastavení
- `GET /api/bookmarks/all` - všechny kategorie rozbalené
- `GET /api/bookmarks/history` - historie navštívených diskuzí
- `POST` operace pro správu historie (odebrání, označení jako přečtené)

### 📧 [10_mail.md](./10_mail.md)
**Poštovní systém a konverzace**
- `GET /api/mail` - načtení pošty s filtry
- `POST /api/mail/send` - odeslání zprávy
- `POST /api/mail/reminder/{id}/{newState}` - správa upomínek
- Konverzace, aktivity uživatelů, formáty zpráv

### 💬 [13_discussion.md](./13_discussion.md)
**Diskuze a příspěvky (nejrozsáhlejší část)**
- `GET /api/discussion/{discussionId}` - načtení diskuze
- `POST /api/discussion/{discussionId}/send/text` - odeslání příspěvku
- Hodnocení příspěvků (positive/negative/negative_visible)
- Správa upomínek a bookmarků
- Mazání příspěvků a správa přístupových práv
- Úprava obsahu na nástěnce

### 📰 [23_last.md](./23_last.md)
**Nejnovější příspěvky**
- `GET /api/last` - seznam posledních příspěvků
- Filtry: domain, min_rating, rated_by_friends, rated_by_me
- Ignorované domény a diskuze
- Kombinace filtrů pro personalizaci obsahu

### 🔔 [24_notifications.md](./24_notifications.md)
**Notifikace a push zprávy**
- `GET /api/notifications` - seznam notifikací
- `POST /api/register_for_notifications` - registrace zařízení
- Podporované klienty (nyx, fyx, nyxdroid)
- Typy notifikací (thumbs_up, replies)
- Firebase a APNS tokeny

### 📎 [25_file.md](./25_file.md)
**Správa souborů a příloh**
- `PUT /api/file/upload` - nahrání souboru
- `DELETE /api/file/delete/{id}` - smazání souboru
- `POST /api/file/embed/{id}/{state}` - nastavení embedování
- Typy souborů (discussion_attachment, mail_attachment, event_attachment)
- Podporované formáty (obrázky, HTML, binární soubory)

### 🔍 [28_search.md](./28_search.md)
**Vyhledávání v obsahu**
- `GET /api/search/username/{username}` - vyhledání uživatelů
- `GET /api/search-v2` - vyhledávání příspěvků (nová verze)
- `GET /api/search/unified` - jednotné vyhledávání
- Pokročilé vyhledávací výrazy (=foo, "phrase", @username)
- Zvýrazňování výsledků

### 🔐 [90_autentifikace.md](./90_autentifikace.md)
**Kompletní průvodce autentifikací**
- Bearer token autentifikace
- Získání a použití tokenu
- Bezpečnostní doporučení a ochrana tokenu
- Implementace v JavaScript, Python, PHP
- Testování a řešení problémů s autentifikací

### 🏗️ [95_modely.md](./95_modely.md)
**Kompletní datové struktury**
- Základní typy (Username, SearchExpression)
- Uživatelské struktury (User, Activity, Context)
- Diskuzní struktury (Discussion, TemplatePost, PostContent)
- Souborové struktury (FileWithUrl, FileTypeEnum)
- Enum hodnoty a union typy
- Formáty dat a konvence

### ⚠️ [99_chyby.md](./99_chyby.md)
**Chybové stavy a jejich řešení**
- HTTP status kódy (400, 401, 403, 404, 413, 415, 429, 500)
- Specifické chybové kódy (VALIDATION_ERROR, UNAUTHORIZED, NeedsConfirmation)
- Struktura chybových odpovědí
- Doporučené postupy pro zpracování chyb
- Retry logika a exponential backoff

## Rychlá navigace podle funkcí

### 👤 **Uživatelské funkce**
- Autentifikace → [90_autentifikace.md](./90_autentifikace.md)
- Vyhledání uživatelů → [28_search.md](./28_search.md)
- Notifikace → [24_notifications.md](./24_notifications.md)

### 📝 **Obsah a příspěvky**
- Poznámky → [01_notepad.md](./01_notepad.md)
- Diskuze → [13_discussion.md](./13_discussion.md)
- Nejnovější příspěvky → [23_last.md](./23_last.md)
- Vyhledávání → [28_search.md](./28_search.md)

### 📁 **Organizace obsahu**
- Záložky → [04_bookmarks.md](./04_bookmarks.md)
- Soubory → [25_file.md](./25_file.md)
- Pošta → [10_mail.md](./10_mail.md)

### 🔧 **Technické informace**
- Datové modely → [95_modely.md](./95_modely.md)
- Chybové kódy → [99_chyby.md](./99_chyby.md)
- Obecné konvence → [../README.md](../README.md)

## Statistiky dokumentace

| Soubor | Velikost | Endpointy | Hlavní funkce |
|--------|----------|-----------|---------------|
| ../README.md | 2.3KB | - | Přehled a rychlý start |
| 90_autentifikace.md | 7.9KB | - | Bearer token autentifikace |
| 01_notepad.md | 3.9KB | 2 | Správa poznámek |
| 04_bookmarks.md | 6.2KB | 5 | Záložky a historie |
| 10_mail.md | 6.0KB | 3 | Poštovní systém |
| 13_discussion.md | 10.7KB | 11 | Diskuze a příspěvky |
| 28_search.md | 9.1KB | 4 | Vyhledávání |
| 25_file.md | 5.9KB | 3 | Správa souborů |
| 24_notifications.md | 5.9KB | 2 | Push notifikace |
| 23_last.md | 5.8KB | 1 | Nejnovější příspěvky |
| 95_modely.md | 8.5KB | - | Datové struktury |
| 99_chyby.md | 6.7KB | - | Chybové stavy |

**Celkem:** 13 souborů, ~83KB, 31 API endpointů

## Doporučené pořadí čtení

### Pro začátečníky:
1. [../README.md](../README.md) - základní přehled
2. [90_autentifikace.md](./90_autentifikace.md) - jak se připojit
3. [01_notepad.md](./01_notepad.md) - jednoduchý začátek
4. [99_chyby.md](./99_chyby.md) - řešení problémů

### Pro pokročilé:
1. [95_modely.md](./95_modely.md) - pochopení datových struktur
2. [13_discussion.md](./13_discussion.md) - nejkomplexnější funkcionalita
3. [28_search.md](./28_search.md) - pokročilé vyhledávání
4. Ostatní podle potřeby

### Pro integraci:
1. [90_autentifikace.md](./90_autentifikace.md) - implementace autentifikace
2. Konkrétní API podle požadavků aplikace
3. [99_chyby.md](./99_chyby.md) - robustní error handling
4. [95_modely.md](./95_modely.md) - validace dat
