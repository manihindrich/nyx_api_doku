#!/bin/bash

# NYX.CZ API - Nastavení přístupových práv diskuze
# POST /api/discussion/{discussionId}/access_rights

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

# Kontrola dat pro nastavení práv
if [ -z "$ACCESS_RIGHTS_DATA" ]; then
    echo "Chyba: Nastavte ACCESS_RIGHTS_DATA v secret.txt"
    echo "Příklad: ACCESS_RIGHTS_DATA='{\"userId\":123,\"canRead\":true,\"canWrite\":true}'"
    exit 1
fi

echo "=== NYX.CZ API - Nastavení přístupových práv diskuze ==="
echo "URL: ${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/access_rights"
echo "Discussion ID: $DISCUSSION_ID"
echo "Data práv: $ACCESS_RIGHTS_DATA"
echo

# Varování před změnou práv
echo "⚠️  VAROVÁNÍ: Měníte přístupová práva diskuze!"
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
    -d "$ACCESS_RIGHTS_DATA" \
    "${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/access_rights")

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
        echo "=== Analýza nastavených práv ==="
        
        # Pokus o parsování původních dat
        user_id=$(echo "$ACCESS_RIGHTS_DATA" | jq -r '.userId // .username // "neznámý"' 2>/dev/null)
        can_read=$(echo "$ACCESS_RIGHTS_DATA" | jq -r '.canRead // "nezměněno"' 2>/dev/null)
        can_write=$(echo "$ACCESS_RIGHTS_DATA" | jq -r '.canWrite // "nezměněno"' 2>/dev/null)
        can_moderate=$(echo "$ACCESS_RIGHTS_DATA" | jq -r '.canModerate // "nezměněno"' 2>/dev/null)
        can_admin=$(echo "$ACCESS_RIGHTS_DATA" | jq -r '.canAdmin // "nezměněno"' 2>/dev/null)
        
        echo "Uživatel: $user_id"
        echo "Práva čtení: $can_read"
        echo "Práva zápisu: $can_write"
        echo "Práva moderování: $can_moderate"
        echo "Administrátorská práva: $can_admin"
        
        # Určení úrovně přístupu
        echo
        echo "=== Nová úroveň přístupu ==="
        if [ "$can_admin" = "true" ]; then
            echo "🔑 Administrátor - plná práva"
        elif [ "$can_moderate" = "true" ]; then
            echo "🛡️  Moderátor - rozšířená práva"
        elif [ "$can_write" = "true" ]; then
            echo "✏️  Uživatel - práva zápisu"
        elif [ "$can_read" = "true" ]; then
            echo "👁️  Čtenář - pouze čtení"
        else
            echo "🚫 Bez přístupu"
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
    echo "- ACCESS_RIGHTS_DATA v secret.txt (platný JSON)"
    
    if [ "$http_status" -eq 404 ]; then
        echo "- Diskuze nebo uživatel neexistuje"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění pro změnu práv"
    elif [ "$http_status" -eq 400 ]; then
        echo "- Neplatný formát dat nebo parametrů"
    elif [ "$http_status" -eq 401 ]; then
        echo "- Neplatný nebo chybějící API token"
    fi
else
    echo
    echo "✓ Přístupová práva byla úspěšně změněna!"
    echo
    echo "Statistiky:"
    echo "- Discussion ID: $DISCUSSION_ID"
    echo "- Čas změny: $(date)"
    echo "- Změněná data: $ACCESS_RIGHTS_DATA"
fi

echo
echo "Tip: Pro zobrazení aktuálních práv použijte discussion_access_rights_get.sh"
