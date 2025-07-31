#!/bin/bash

# NYX.CZ API - Označení diskuze v historii jako přečtené
# POST /api/bookmarks/history/mark_read

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

# Kontrola DISCUSSION_ID
if [ -z "$DISCUSSION_ID" ]; then
    echo "Chyba: Nastavte DISCUSSION_ID v secret.txt"
    exit 1
fi

echo "=== NYX.CZ API - Označení diskuze jako přečtené ==="
echo "URL: ${NYX_API_BASE_URL}/bookmarks/history/mark_read"
echo "Discussion ID: $DISCUSSION_ID"
echo

# Příprava JSON dat
json_data=$(cat <<EOF
{
  "discussionId": $DISCUSSION_ID
}
EOF
)

echo "JSON data:"
echo "$json_data"
echo

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$json_data" \
    "${NYX_API_BASE_URL}/bookmarks/history/mark_read")

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
    echo "- Existenci diskuze s daným ID"
    echo "- Zda je diskuze v historii"
    
    if [ "$http_status" -eq 404 ]; then
        echo "- Diskuze s ID $DISCUSSION_ID neexistuje nebo není v historii"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění"
    fi
else
    echo
    echo "✓ Diskuze byla úspěšně označena jako přečtená!"
fi

echo
echo "Tip: Pro zobrazení historie použijte bookmarks_history.sh"
