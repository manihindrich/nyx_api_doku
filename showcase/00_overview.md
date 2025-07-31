# NYX.CZ API Showcase - Přehled souborů

Tento dokument poskytuje kompletní přehled všech showcase souborů pro NYX.CZ API.

## Statistiky

- **Celkem souborů**: 67
- **API endpointy**: 31 (100% pokrytí)
- **Bash skripty**: 32 (.sh)
- **Python skripty**: 32 (.py)
- **Dokumentační soubory**: 3 (.md + .txt)

## Struktura podle API kategorií

### 📝 Notepad API (2 endpointy - 4 soubory)
- `notepad_get.sh/py` - GET /api/notepad
- `notepad_entry_get.sh/py` - GET /api/notepad/{entry_id}

### 📰 Last Posts API (1 endpoint - 2 soubory)
- `last_posts.sh/py` - GET /api/last

### 🔍 Search API (4 endpointy - 8 souborů)
- `search_username.sh/py` - GET /api/search/username/{username}
- `search_v2.sh/py` - GET /api/search-v2
- `search_unified.sh/py` - GET /api/search/unified
- `search_highlight.sh/py` - GET /api/search/highlight

### 🔖 Bookmarks API (5 endpointů - 10 souborů)
- `bookmarks_get.sh/py` - GET /api/bookmarks
- `bookmarks_all.sh/py` - GET /api/bookmarks/all
- `bookmarks_history.sh/py` - GET /api/bookmarks/history
- `bookmarks_history_remove.sh/py` - POST /api/bookmarks/history/remove
- `bookmarks_history_mark_read.sh/py` - POST /api/bookmarks/history/mark_read

### 📧 Mail API (3 endpointy - 6 souborů)
- `mail_get.sh/py` - GET /api/mail
- `mail_send.sh/py` - POST /api/mail/send
- `mail_reminder.sh/py` - POST /api/mail/reminder/{id}/{newState}

### 💬 Discussion API (12 endpointů - 24 souborů)
- `discussion_get.sh/py` - GET /api/discussion/{discussionId}
- `discussion_send.sh/py` - POST /api/discussion/{discussionId}/send/text
- `discussion_rating_get.sh/py` - GET /api/discussion/{discussion_id}/rating/{id}
- `discussion_rate.sh/py` - POST /api/discussion/{discussion_id}/rating/{id}/{action}
- `discussion_reminder.sh/py` - POST /api/discussion/{discussion_id}/reminder/{id}/{new_state}
- `discussion_bookmark.sh/py` - POST /api/discussion/{discussion_id}/bookmark
- `discussion_delete.sh/py` - DELETE /api/discussion/{discussion_id}/delete/{id}
- `discussion_access_rights_get.sh/py` - GET /api/discussion/rights (add endpoint)
- `discussion_access_rights_post.sh/py` - POST /api/discussion/rights
- `discussion_home_get.sh/py` - GET /api/discussion/{discussionId}/home
- `discussion_home_post.sh/py` - POST /api/discussion/{discussionId}/home
- `discussion_content_save.sh/py` - POST /api/discussion/{discussionId}/content/{contentId}/save

### 📎 File API (3 endpointy - 6 souborů)
- `file_upload.sh/py` - PUT /api/file/upload
- `file_delete.sh/py` - DELETE /api/file/delete/{id}
- `file_embed.sh/py` - POST /api/file/embed/{id}/{state}

### 🔔 Notifications API (2 endpointy - 4 soubory)
- `notifications_get.sh/py` - GET /api/notifications
- `notifications_register.sh/py` - POST /api/register_for_notifications

## Dokumentační soubory

### README.md
Hlavní návod k použití showcase souborů s příklady konfigurace a spuštění.

### overview.md (tento soubor)
Kompletní přehled všech showcase souborů a jejich účelu.

### dummy-secret.txt
Konfigurační šablona se všemi potřebnými proměnnými pro testování API.

## Funkce showcase souborů

### Bash skripty (.sh)
- **Curl-based implementace** s detailním error handlingem
- **jq formátování** pro čitelný JSON výstup
- **Pokročilé analýzy** s barevným výstupem
- **Statistiky a metriky** pro každý endpoint
- **Doporučení a tipy** pro další použití
- **Executable práva** nastavena automaticky

### Python skripty (.py)
- **Requests knihovna** pro HTTP komunikaci
- **JSON analýzy** s dodatečnými metrikami
- **Objektově orientované** zpracování dat
- **Pokročilé algoritmy** pro analýzu obsahu
- **Detailní error handling** s kontextovými zprávami
- **Modulární struktura** s helper funkcemi

## Konfigurace

Všechny skripty používají centralizovanou konfiguraci ze souboru `secret.txt`:

```bash
# Zkopírujte dummy-secret.txt jako secret.txt
cp dummy-secret.txt secret.txt

# Vyplňte skutečné hodnoty
nano secret.txt
```

### Klíčové konfigurační proměnné

```bash
# Základní konfigurace
NYX_API_TOKEN="your_api_token_here"
NYX_API_BASE_URL="https://nyx.cz/api"

# ID pro testování
DISCUSSION_ID="123"
POST_ID="456"
ENTRY_ID="789"
FILE_ID="101112"

# Textové obsahy
TEST_MESSAGE="Testovací zpráva"
MAIL_CONTENT="Obsah zprávy"
CONTENT_TEXT="Obsah pro úpravu"

# Akce a stavy
RATE_ACTION="positive"
BOOKMARK_STATE="true"
REMINDER_STATE="true"
```

## Použití

### Spuštění bash skriptu
```bash
cd showcase
./notepad_get.sh
```

### Spuštění Python skriptu
```bash
cd showcase
python3 notepad_get.py
```

### Hromadné testování
```bash
# Testování všech GET endpointů
for script in showcase/*_get.sh; do
    echo "=== Testování $script ==="
    ./"$script"
    echo
done
```

## Pokročilé funkce

### Analýzy a metriky
- **Statistiky API odpovědí** (velikost, čas odezvy)
- **Analýza obsahu** (délka, struktura, kvalita)
- **Hodnocení trendů** (pozitivní/negativní směr)
- **Doporučení akcí** na základě dat
- **Kontextové tipy** pro optimalizaci

### Error handling
- **HTTP status kódy** s vysvětlením
- **API error kódy** s kontextovými radami
- **Validace parametrů** před odesláním
- **Fallback mechanismy** při chybách
- **Debugging informace** pro řešení problémů

### Bezpečnost
- **Token validace** před každým požadavkem
- **Parametr sanitizace** pro bezpečnost
- **Rate limiting** respektování
- **Secure defaults** v konfiguraci
- **Privacy protection** v log výstupech

## Rozšíření a customizace

### Přidání nového endpointu
1. Vytvořte `new_endpoint.sh` a `new_endpoint.py`
2. Implementujte podle vzoru existujících souborů
3. Přidejte potřebné proměnné do `dummy-secret.txt`
4. Aktualizujte dokumentaci

### Customizace výstupů
- Upravte formátování v sekcích s `jq` (bash)
- Modifikujte analýzy v helper funkcích (Python)
- Přidejte vlastní metriky a doporučení
- Rozšiřte error handling o specifické případy

## Troubleshooting

### Časté problémy

**401 Unauthorized**
- Zkontrolujte `NYX_API_TOKEN` v `secret.txt`
- Ověřte platnost tokenu ve webovém rozhraní

**400 Bad Request**
- Zkontrolujte formát parametrů
- Ověřte povinné hodnoty v `secret.txt`

**403 Forbidden**
- Zkontrolujte oprávnění k endpointu
- Ověřte přístupová práva k diskuzi/obsahu

**404 Not Found**
- Zkontrolujte existenci ID v parametrech
- Ověřte správnost URL endpointu

### Debug režim
```bash
# Bash - verbose curl
export CURL_VERBOSE=1
./script.sh

# Python - debug logging
export DEBUG=1
python3 script.py
```

## Vývojové poznámky

### Konvence názvů
- `{category}_{action}.sh/py` pro základní operace
- `{category}_{resource}_{action}.sh/py` pro specifické zdroje
- Konzistentní naming napříč všemi soubory

### Kódové standardy
- **Bash**: POSIX kompatibilita, error handling, dokumentace
- **Python**: PEP 8, type hints, docstrings
- **JSON**: Konzistentní formátování s jq/json.dumps
- **Dokumentace**: Markdown s emoji pro lepší čitelnost

### Testování
- Všechny skripty testovány s dummy daty
- Error handling ověřen pro všechny HTTP kódy
- Cross-platform kompatibilita (Linux, macOS, WSL)

## Licence a použití

Tyto showcase soubory jsou určeny pro:
- **Vývojáře** integrující NYX.CZ API
- **Testování** API funkcionalit
- **Dokumentaci** použití endpointů
- **Vzdělávací účely** a příklady

Respektujte API rate limity a terms of service NYX.CZ při použití.

---

**Poslední aktualizace**: 31.7.2025  
**Verze showcase**: 1.0.0  
**Pokrytí API**: 31/31 endpointů (100%)
