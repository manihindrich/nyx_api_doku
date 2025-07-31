# Přehled dokumentace NYX.CZ API

Tento dokument poskytuje stručný přehled všech částí dokumentace NYX.CZ API.

## Struktura dokumentace

### 📋 [README.md](./README.md)
**Hlavní vstupní bod dokumentace**
- Základní informace o API (verze 0.0.1, base URL, autentifikace)
- Rychlý start s příklady
- Obecné konvence (HTTP metody, formáty odpovědí, časové formáty)
- Odkazy na všechny ostatní části dokumentace

### 🔐 [autentifikace.md](./autentifikace.md)
**Kompletní průvodce autentifikací**
- Bearer token autentifikace
- Získání a použití tokenu
- Bezpečnostní doporučení a ochrana tokenu
- Implementace v JavaScript, Python, PHP
- Testování a řešení problémů s autentifikací

### 📝 [notepad.md](./notepad.md)
**Správa poznámkového bloku**
- `GET /api/notepad` - seznam poznámek
- `GET /api/notepad/{entry_id}` - konkrétní poznámka
- Datové struktury: NotepadEntry, NotepadEntryMinimal
- Práce s kategoriemi a veřejnými poznámkami

### 🔖 [bookmarks.md](./bookmarks.md)
**Záložky a historie diskuzí**
- `GET /api/bookmarks` - záložky podle nastavení
- `GET /api/bookmarks/all` - všechny kategorie rozbalené
- `GET /api/bookmarks/history` - historie navštívených diskuzí
- `POST` operace pro správu historie (odebrání, označení jako přečtené)

### 📧 [mail.md](./mail.md)
**Poštovní systém a konverzace**
- `GET /api/mail` - načtení pošty s filtry
- `POST /api/mail/send` - odeslání zprávy
- `POST /api/mail/reminder/{id}/{newState}` - správa upomínek
- Konverzace, aktivity uživatelů, formáty zpráv

### 💬 [discussion.md](./discussion.md)
**Diskuze a příspěvky (nejrozsáhlejší část)**
- `GET /api/discussion/{discussionId}` - načtení diskuze
- `POST /api/discussion/{discussionId}/send/text` - odeslání příspěvku
- Hodnocení příspěvků (positive/negative/negative_visible)
- Správa upomínek a bookmarků
- Mazání příspěvků a správa přístupových práv
- Úprava obsahu na nástěnce

### 🔍 [search.md](./search.md)
**Vyhledávání v obsahu**
- `GET /api/search/username/{username}` - vyhledání uživatelů
- `GET /api/search-v2` - vyhledávání příspěvků (nová verze)
- `GET /api/search/unified` - jednotné vyhledávání
- Pokročilé vyhledávací výrazy (=foo, "phrase", @username)
- Zvýrazňování výsledků

### 📎 [file.md](./file.md)
**Správa souborů a příloh**
- `PUT /api/file/upload` - nahrání souboru
- `DELETE /api/file/delete/{id}` - smazání souboru
- `POST /api/file/embed/{id}/{state}` - nastavení embedování
- Typy souborů (discussion_attachment, mail_attachment, event_attachment)
- Podporované formáty (obrázky, HTML, binární soubory)

### 🔔 [notifications.md](./notifications.md)
**Notifikace a push zprávy**
- `GET /api/notifications` - seznam notifikací
- `POST /api/register_for_notifications` - registrace zařízení
- Podporované klienty (nyx, fyx, nyxdroid)
- Typy notifikací (thumbs_up, replies)
- Firebase a APNS tokeny

### 📰 [last.md](./last.md)
**Nejnovější příspěvky**
- `GET /api/last` - seznam posledních příspěvků
- Filtry: domain, min_rating, rated_by_friends, rated_by_me
- Ignorované domény a diskuze
- Kombinace filtrů pro personalizaci obsahu

### 🏗️ [modely.md](./modely.md)
**Kompletní datové struktury**
- Základní typy (Username, SearchExpression)
- Uživatelské struktury (User, Activity, Context)
- Diskuzní struktury (Discussion, TemplatePost, PostContent)
- Souborové struktury (FileWithUrl, FileTypeEnum)
- Enum hodnoty a union typy
- Formáty dat a konvence

### ⚠️ [chyby.md](./chyby.md)
**Chybové stavy a jejich řešení**
- HTTP status kódy (400, 401, 403, 404, 413, 415, 429, 500)
- Specifické chybové kódy (VALIDATION_ERROR, UNAUTHORIZED, NeedsConfirmation)
- Struktura chybových odpovědí
- Doporučené postupy pro zpracování chyb
- Retry logika a exponential backoff

## Rychlá navigace podle funkcí

### 👤 **Uživatelské funkce**
- Autentifikace → [autentifikace.md](./autentifikace.md)
- Vyhledání uživatelů → [search.md](./search.md)
- Notifikace → [notifications.md](./notifications.md)

### 📝 **Obsah a příspěvky**
- Poznámky → [notepad.md](./notepad.md)
- Diskuze → [discussion.md](./discussion.md)
- Nejnovější příspěvky → [last.md](./last.md)
- Vyhledávání → [search.md](./search.md)

### 📁 **Organizace obsahu**
- Záložky → [bookmarks.md](./bookmarks.md)
- Soubory → [file.md](./file.md)
- Pošta → [mail.md](./mail.md)

### 🔧 **Technické informace**
- Datové modely → [modely.md](./modely.md)
- Chybové kódy → [chyby.md](./chyby.md)
- Obecné konvence → [README.md](./README.md)

## Statistiky dokumentace

| Soubor | Velikost | Endpointy | Hlavní funkce |
|--------|----------|-----------|---------------|
| README.md | 2.3KB | - | Přehled a rychlý start |
| autentifikace.md | 7.9KB | - | Bearer token autentifikace |
| notepad.md | 3.9KB | 2 | Správa poznámek |
| bookmarks.md | 6.2KB | 5 | Záložky a historie |
| mail.md | 6.0KB | 3 | Poštovní systém |
| discussion.md | 10.7KB | 11 | Diskuze a příspěvky |
| search.md | 9.1KB | 4 | Vyhledávání |
| file.md | 5.9KB | 3 | Správa souborů |
| notifications.md | 5.9KB | 2 | Push notifikace |
| last.md | 5.8KB | 1 | Nejnovější příspěvky |
| modely.md | 8.5KB | - | Datové struktury |
| chyby.md | 6.7KB | - | Chybové stavy |

**Celkem:** 13 souborů, ~83KB, 31 API endpointů

## Doporučené pořadí čtení

### Pro začátečníky:
1. [README.md](./README.md) - základní přehled
2. [autentifikace.md](./autentifikace.md) - jak se připojit
3. [notepad.md](./notepad.md) - jednoduchý začátek
4. [chyby.md](./chyby.md) - řešení problémů

### Pro pokročilé:
1. [modely.md](./modely.md) - pochopení datových struktur
2. [discussion.md](./discussion.md) - nejkomplexnější funkcionalita
3. [search.md](./search.md) - pokročilé vyhledávání
4. Ostatní podle potřeby

### Pro integraci:
1. [autentifikace.md](./autentifikace.md) - implementace autentifikace
2. Konkrétní API podle požadavků aplikace
3. [chyby.md](./chyby.md) - robustní error handling
4. [modely.md](./modely.md) - validace dat
