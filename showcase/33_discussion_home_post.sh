#!/bin/bash

# NYX.CZ API - Nastavení domovské stránky diskuze
# POST /api/discussion/{discussionId}/home

# Načtení konfigurace
source ./secret.txt 2>/dev/null || {
    echo "Chyba: Soubor secret.txt nenalezen!"
    echo "Zkopírujte dummy-secret.txt jako secret.txt a vyplňte hodnoty."
    exit 1
}

# Kontrola API tokenu
if [ -z "$NYX_API_TOKEN" ] || [ "$NYX_API_TOKEN" = "your_api_token_here" ]; then
    echo "Chyba: Nastavte NYX_API_TOKEN v secret.txt"
    exit 1
fi

# Kontrola povinných parametrů
if [ -z "$DISCUSSION_ID" ]; then
    echo "Chyba: Nastavte DISCUSSION_ID v secret.txt"
    exit 1
fi

# Kontrola dat pro domovskou stránku
if [ -z "$HOME_PAGE_DATA" ]; then
    echo "Chyba: Nastavte HOME_PAGE_DATA v secret.txt"
    echo "Příklad: HOME_PAGE_DATA='{\"title\":\"Název\",\"content\":\"Obsah stránky\"}'"
    exit 1
fi

echo "=== NYX.CZ API - Nastavení domovské stránky diskuze ==="
echo "URL: ${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/home"
echo "Discussion ID: $DISCUSSION_ID"
echo "Data stránky: $HOME_PAGE_DATA"
echo

# Varování před změnou
echo "⚠️  VAROVÁNÍ: Měníte domovskou stránku diskuze!"
echo "Pokračovat? (y/N)"
read -r confirmation
if [[ ! "$confirmation" =~ ^[Yy]$ ]]; then
    echo "Operace zrušena."
    exit 0
fi

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$HOME_PAGE_DATA" \
    "${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/home")

# Rozdělení odpovědi a status kódu
http_body=$(echo "$response" | sed '$d')
http_status=$(echo "$response" | tail -n1 | sed 's/HTTP_STATUS://')

echo "HTTP Status: $http_status"
echo

# Formátování JSON výstupu
if command -v jq >/dev/null 2>&1; then
    echo "$http_body" | jq '.'
    
    # Dodatečné analýzy s jq
    if [ "$http_status" -eq 200 ]; then
        echo
        echo "=== Analýza nastavené stránky ==="
        
        # Pokus o parsování původních dat
        title=$(echo "$HOME_PAGE_DATA" | jq -r '.title // "nezměněno"' 2>/dev/null)
        content=$(echo "$HOME_PAGE_DATA" | jq -r '.content // "nezměněno"' 2>/dev/null)
        description=$(echo "$HOME_PAGE_DATA" | jq -r '.description // "nezměněno"' 2>/dev/null)
        
        echo "Název: $title"
        if [ "$description" != "null" ] && [ "$description" != "nezměněno" ]; then
            echo "Popis: $description"
        fi
        
        # Analýza obsahu
        if [ "$content" != "null" ] && [ "$content" != "nezměněno" ]; then
            content_length=$(echo "$content" | wc -c)
            echo "Délka obsahu: $content_length znaků"
            
            # Kontrola HTML obsahu
            if echo "$content" | grep -q "<"; then
                echo "Typ obsahu: HTML"
                html_tags=$(echo "$content" | grep -o '<[^>]*>' | wc -l)
                echo "Počet HTML tagů: $html_tags"
            else
                echo "Typ obsahu: Prostý text"
            fi
        fi
        
        # Kontrola odpovědi API
        if echo "$http_body" | jq -e '.success' >/dev/null 2>&1; then
            success=$(echo "$http_body" | jq -r '.success')
            echo "Stav operace: $success"
        fi
        
        if echo "$http_body" | jq -e '.id' >/dev/null 2>&1; then
            page_id=$(echo "$http_body" | jq -r '.id')
            echo "ID stránky: $page_id"
        fi
    fi
else
    echo "$http_body"
    echo
    echo "Tip: Nainstalujte 'jq' pro lepší formátování JSON: sudo apt install jq"
fi

# Kontrola chyb
if [ "$http_status" -ne 200 ]; then
    echo
    echo "Chyba v požadavku! Zkontrolujte:"
    echo "- API token v secret.txt"
    echo "- DISCUSSION_ID v secret.txt"
    echo "- HOME_PAGE_DATA v secret.txt (platný JSON)"
    
    if [ "$http_status" -eq 404 ]; then
        echo "- Diskuze neexistuje"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění pro úpravu domovské stránky"
    elif [ "$http_status" -eq 400 ]; then
        echo "- Neplatný formát dat nebo parametrů"
    elif [ "$http_status" -eq 401 ]; then
        echo "- Neplatný nebo chybějící API token"
    fi
else
    echo
    echo "✓ Domovská stránka byla úspěšně nastavena!"
    echo
    echo "Statistiky:"
    echo "- Discussion ID: $DISCUSSION_ID"
    echo "- Čas změny: $(date)"
    echo "- Velikost dat: $(echo "$HOME_PAGE_DATA" | wc -c) znaků"
    
    # Doporučení
    echo
    echo "=== Doporučení ==="
    echo "- Zkontrolujte výsledek pomocí discussion_home_get.sh"
    echo "- Ujistěte se, že obsah je správně formátován"
    echo "- Pro HTML obsah ověřte validitu tagů"
fi

echo
echo "Tip: Pro zobrazení domovské stránky použijte discussion_home_get.sh"
