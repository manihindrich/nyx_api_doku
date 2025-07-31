#!/bin/bash

# NYX.CZ API - Získání přístupových práv diskuze
# GET /api/discussion/{discussionId}/access_rights

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

echo "=== NYX.CZ API - Přístupová práva diskuze ==="
echo "URL: ${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/access_rights"
echo "Discussion ID: $DISCUSSION_ID"
echo

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
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
        echo "=== Analýza přístupových práv ==="
        
        # Kontrola základních práv
        can_read=$(echo "$http_body" | jq -r '.canRead // "neznámé"')
        can_write=$(echo "$http_body" | jq -r '.canWrite // "neznámé"')
        can_moderate=$(echo "$http_body" | jq -r '.canModerate // "neznámé"')
        can_admin=$(echo "$http_body" | jq -r '.canAdmin // "neznámé"')
        
        echo "Práva čtení: $can_read"
        echo "Práva zápisu: $can_write"
        echo "Práva moderování: $can_moderate"
        echo "Administrátorská práva: $can_admin"
        
        # Kontrola speciálních práv
        can_delete=$(echo "$http_body" | jq -r '.canDelete // "neznámé"')
        can_edit=$(echo "$http_body" | jq -r '.canEdit // "neznámé"')
        can_pin=$(echo "$http_body" | jq -r '.canPin // "neznámé"')
        
        if [ "$can_delete" != "null" ] && [ "$can_delete" != "neznámé" ]; then
            echo "Práva mazání: $can_delete"
        fi
        if [ "$can_edit" != "null" ] && [ "$can_edit" != "neznámé" ]; then
            echo "Práva editace: $can_edit"
        fi
        if [ "$can_pin" != "null" ] && [ "$can_pin" != "neznámé" ]; then
            echo "Práva připínání: $can_pin"
        fi
        
        # Souhrn úrovně přístupu
        echo
        echo "=== Úroveň přístupu ==="
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
    
    if [ "$http_status" -eq 404 ]; then
        echo "- Diskuze neexistuje"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění pro zobrazení práv"
    elif [ "$http_status" -eq 401 ]; then
        echo "- Neplatný nebo chybějící API token"
    fi
else
    echo
    echo "✓ Přístupová práva úspěšně načtena!"
fi

echo
echo "Tip: Pro úpravu práv použijte discussion_access_rights_post.sh"
