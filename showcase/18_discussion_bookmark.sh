#!/bin/bash

# NYX.CZ API - Nastavení záložky diskuze
# POST /api/discussion/{discussionId}/bookmark/{newState}

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

if [ -z "$BOOKMARK_STATE" ]; then
    echo "Chyba: Nastavte BOOKMARK_STATE v secret.txt (true/false)"
    exit 1
fi

echo "=== NYX.CZ API - Nastavení záložky diskuze ==="
echo "URL: ${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/bookmark/${BOOKMARK_STATE}"
echo "Discussion ID: $DISCUSSION_ID"
echo "Nový stav: $BOOKMARK_STATE"
echo

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    "${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/bookmark/${BOOKMARK_STATE}")

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
    echo "- BOOKMARK_STATE v secret.txt (true/false)"
    
    if [ "$http_status" -eq 404 ]; then
        echo "- Diskuze neexistuje"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění"
    elif [ "$http_status" -eq 400 ]; then
        echo "- Neplatný formát parametrů"
    fi
else
    echo
    if [ "$BOOKMARK_STATE" = "true" ]; then
        echo "✓ Diskuze byla úspěšně přidána do záložek!"
    else
        echo "✓ Diskuze byla úspěšně odebrána ze záložek!"
    fi
fi

echo
echo "Tip: Pro zobrazení záložek použijte bookmarks_get.sh"
