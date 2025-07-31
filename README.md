# NYX.CZ API - Kompletní dokumentace a showcase

Tento repozitář obsahuje kompletní dokumentaci a funkční ukázky pro všech 32 endpointů NYX.CZ API.

## 📁 Struktura repozitáře

```
nyx_api/
├── dokumentace/          # Detailní API dokumentace
│   ├── 00_overview.md     # Kompletní přehled všech endpointů
│   ├── 01_notepad.md      # Notepad API (2 endpointy)
│   ├── 04_bookmarks.md    # Bookmarks API (5 endpointů)
│   ├── 10_mail.md         # Mail API (3 endpointy)
│   ├── 13_discussion.md   # Discussion API (12 endpointů)
│   ├── 23_last.md         # Last Posts API (1 endpoint)
│   ├── 24_notifications.md # Notifications API (2 endpointy)
│   ├── 25_file.md         # File API (3 endpointy)
│   ├── 28_search.md       # Search API (4 endpointy)
│   ├── 90_autentifikace.md # Autentifikace a tokeny
│   ├── 95_modely.md       # Datové modely
│   └── 99_chyby.md        # Error handling
│
└── showcase/             # Funkční ukázky všech endpointů
    ├── 00_dummy-secret.txt # Konfigurační šablona
    ├── 00_overview.md     # Přehled showcase souborů
    ├── 01_notepad_get.sh/py
    ├── 02_notepad_entry_get.sh/py
    ├── 03_notifications_register.sh/py
    ├── 04-09_bookmarks_*.sh/py
    ├── 10-12_mail_*.sh/py
    ├── 13-22_discussion_*.sh/py
    ├── 23_last_posts.sh/py
    ├── 24_notifications_get.sh/py
    ├── 25-27_file_*.sh/py
    ├── 28-31_search_*.sh/py
    └── 32-34_extra_*.sh/py
```

## 🚀 Rychlý start

### 1. Konfigurace
```bash
# Zkopírujte konfigurační šablonu
cp showcase/00_dummy-secret.txt showcase/secret.txt

# Vyplňte skutečné API hodnoty
nano showcase/secret.txt
```

### 2. Spuštění ukázek
```bash
# Bash verze
./showcase/01_notepad_get.sh

# Python verze
python3 showcase/01_notepad_get.py
```

## 📊 Pokrytí API

| Kategorie | Endpointy | Soubory | Status |
|-----------|-----------|---------|--------|
| 📝 Notepad | 2/2 | 4 | ✅ 100% |
| 📰 Last Posts | 1/1 | 2 | ✅ 100% |
| 🔍 Search | 4/4 | 8 | ✅ 100% |
| 🔖 Bookmarks | 5/5 | 10 | ✅ 100% |
| 📧 Mail | 3/3 | 6 | ✅ 100% |
| 💬 Discussion | 12/12 | 24 | ✅ 100% |
| 📎 File | 3/3 | 6 | ✅ 100% |
| 🔔 Notifications | 2/2 | 4 | ✅ 100% |
| **CELKEM** | **32/32** | **66** | **✅ 100%** |

## 🔢 Číslování souborů

Všechny soubory jsou chronologicky očíslovány podle pořadí v oficiální API dokumentaci:

- **01-02**: Notepad API
- **03**: Notifications register
- **04-09**: Bookmarks API  
- **10-12**: Mail API
- **13-22**: Discussion API
- **23**: Last Posts API
- **24**: Notifications get
- **25-27**: File API
- **28-31**: Search API
- **32-34**: Extra endpointy
- **90+**: Obecná dokumentace (autentifikace, modely, chyby)

## 📚 Dokumentace

### Hlavní přehledy
- [`dokumentace/00_overview.md`](dokumentace/00_overview.md) - Kompletní přehled všech endpointů
- [`showcase/00_overview.md`](showcase/00_overview.md) - Přehled showcase souborů

### API kategorie
- [`dokumentace/01_notepad.md`](dokumentace/01_notepad.md) - Notepad API
- [`dokumentace/04_bookmarks.md`](dokumentace/04_bookmarks.md) - Bookmarks API
- [`dokumentace/10_mail.md`](dokumentace/10_mail.md) - Mail API
- [`dokumentace/13_discussion.md`](dokumentace/13_discussion.md) - Discussion API
- [`dokumentace/23_last.md`](dokumentace/23_last.md) - Last Posts API
- [`dokumentace/24_notifications.md`](dokumentace/24_notifications.md) - Notifications API
- [`dokumentace/25_file.md`](dokumentace/25_file.md) - File API
- [`dokumentace/28_search.md`](dokumentace/28_search.md) - Search API

### Technické detaily
- [`dokumentace/90_autentifikace.md`](dokumentace/90_autentifikace.md) - Autentifikace a tokeny
- [`dokumentace/95_modely.md`](dokumentace/95_modely.md) - Datové modely
- [`dokumentace/99_chyby.md`](dokumentace/99_chyby.md) - Error handling

## 🛠️ Technické vlastnosti

### Showcase skripty
- **Bash verze**: Používá `curl` a `jq` pro JSON formátování
- **Python verze**: Používá `requests` knihovnu
- **Konfigurace**: Centralizované načítání z `secret.txt`
- **Error handling**: Kompletní validace a error handling
- **Executable práva**: Všechny `.sh` soubory mají nastavená práva

### Struktura skriptů
```bash
# Každý skript obsahuje:
- Načtení konfigurace ze secret.txt
- Validaci povinných parametrů
- HTTP request s proper headers
- JSON formátování výstupu
- Error handling a statistiky
- Detailní komentáře
```

## 📋 Požadavky

### Pro Bash skripty
```bash
# Ubuntu/Debian
sudo apt install curl jq

# macOS
brew install curl jq
```

### Pro Python skripty
```bash
pip install requests
```

## 🔧 Konfigurace

Soubor `showcase/secret.txt` obsahuje:
```bash
NYX_TOKEN="your_api_token_here"
NYX_USERNAME="your_username"
NYX_MAIL_FROM="your_email@example.com"
NYX_MAIL_TO="recipient@example.com"
NYX_MAIL_SUBJECT="Test subject"
NYX_MAIL_BODY="Test message body"
RATE_ACTION="up"  # up/down pro rating
BOOKMARK_STATE="1"  # 0/1 pro bookmark
REMINDER_STATE="1"  # 0/1 pro reminder
```

## 🎯 Použití

### Základní workflow
1. Prostudujte dokumentaci v `dokumentace/`
2. Nakonfigurujte `showcase/secret.txt`
3. Spusťte příslušný showcase skript
4. Analyzujte výstup a response

### Příklady
```bash
# Získání notepad dat
./showcase/01_notepad_get.sh

# Odeslání mailu
./showcase/11_mail_send.sh

# Vyhledávání
./showcase/28_search_username.sh

# Python verze
python3 showcase/01_notepad_get.py
```

## 🏆 Výhody

- ✅ **100% pokrytí** všech 32 API endpointů
- 🔢 **Chronologické číslování** pro snadnou navigaci
- 📚 **Kompletní dokumentace** s příklady
- 🛠️ **Funkční skripty** v Bash i Python
- 🔧 **Centralizovaná konfigurace**
- 📊 **Detailní error handling**
- 🚀 **Okamžitě použitelné** ukázky

---

## 📋 Oficiální informace o NYX.CZ API

### 🏢 O platformě NYX.CZ
- **Název**: Nyx.cz
- **URL**: https://nyx.cz/
- **Typ**: Česká diskusní platforma a komunita

### 🔧 API specifikace
- **OpenAPI verze**: 3.0.0
- **API verze**: 0.0.1
- **Base URL**: https://nyx.cz/
- **Formát**: REST API s JSON responses
- **Autentifikace**: Bearer token (Authorization header)

### 📊 Technické detaily
- **Celkem endpointů**: 32 (100% pokrytí v tomto repozitáři)
- **Podporované formáty**: JSON, HTML, Text, Markdown
- **Podporované HTTP metody**: GET, POST, PUT, DELETE
- **Response formáty**: application/json, multipart/form-data
- **Error handling**: Standardizované JSON error responses

### 🎯 Hlavní funkcionality API
- **Notepad**: Správa osobních poznámek a zápisků
- **Bookmarks**: Sledování a organizace diskusí
- **Mail**: Interní poštovní systém
- **Discussion**: Diskusní fóra s pokročilými funkcemi
- **Search**: Vyhledávání uživatelů, diskusí a příspěvků
- **File**: Upload a správa souborů a příloh
- **Notifications**: Push notifikace pro mobilní aplikace
- **Last Posts**: Přehled nejnovějších příspěvků

### 🔐 Bezpečnost
- **Autentifikace**: Token-based authentication
- **Autorizace**: Role-based access control
- **Rate limiting**: Implementováno pro ochranu API
- **HTTPS**: Povinné šifrované spojení

### 📱 Podporované klienty
- **Web**: Hlavní webové rozhraní
- **API**: Přímý přístup přes REST API
- **Mobilní aplikace**: 
  - nyx (iOS/Android)
  - fyx (alternativní klient)
  - nyxdroid (Android)

### 🌐 Kompatibilita
- **OpenAPI**: 3.0.0 standard
- **JSON Schema**: Plná podpora
- **REST**: RESTful API design
- **HTTP**: Standard HTTP status codes

---

**Vytvořeno**: 2025-01-31  
**Verze repozitáře**: 1.0  
**API verze**: 0.0.1  
**Pokrytí**: 32/32 endpointů (100%)  
**Platforma**: NYX.CZ (https://nyx.cz/)
