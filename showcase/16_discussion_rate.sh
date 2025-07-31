#!/bin/bash

# NYX.CZ API - Hodnocení příspěvku v diskuzi
# POST /api/discussion/{discussionId}/rate/{postId}/{action}

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

if [ -z "$POST_ID" ]; then
    echo "Chyba: Nastavte POST_ID v secret.txt"
    exit 1
fi

if [ -z "$RATE_ACTION" ]; then
    echo "Chyba: Nastavte RATE_ACTION v secret.txt (positive/negative/negative_visible)"
    exit 1
fi

echo "=== NYX.CZ API - Hodnocení příspěvku ==="
echo "URL: ${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/rate/${POST_ID}/${RATE_ACTION}"
echo "Discussion ID: $DISCUSSION_ID"
echo "Post ID: $POST_ID"
echo "Akce: $RATE_ACTION"
echo

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    "${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/rate/${POST_ID}/${RATE_ACTION}")

# Rozdělení odpovědi a status kódu
http_body=$(echo "$response" | sed '$d')
http_status=$(echo "$response" | tail -n1 | sed 's/HTTP_STATUS://')

echo "HTTP Status: $http_status"
echo

# Formátování JSON výstupu
if command -v jq >/dev/null 2>&1; then
    echo "$http_body" | jq '.'
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
    echo "- POST_ID v secret.txt"
    echo "- RATE_ACTION v secret.txt (positive/negative/negative_visible)"
    
    if [ "$http_status" -eq 404 ]; then
        echo "- Diskuze nebo příspěvek neexistuje"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění"
    elif [ "$http_status" -eq 400 ]; then
        echo "- Neplatná akce hodnocení"
    fi
else
    echo
    case "$RATE_ACTION" in
        "positive")
            echo "✓ Příspěvek byl kladně ohodnocen!"
            ;;
        "negative")
            echo "✓ Příspěvek byl záporně ohodnocen (skrytě)!"
            ;;
        "negative_visible")
            echo "✓ Příspěvek byl záporně ohodnocen (viditelně)!"
            ;;
    esac
fi

echo
echo "Tip: Pro zobrazení diskuze použijte discussion_get.sh"
