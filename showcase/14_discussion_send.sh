#!/bin/bash

# NYX.CZ API - Odeslání textového příspěvku do diskuze
# POST /api/discussion/{discussionId}/send/text

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

# Kontrola TEST_CONTENT
if [ -z "$TEST_CONTENT" ]; then
    echo "Chyba: Nastavte TEST_CONTENT v secret.txt"
    exit 1
fi

echo "=== NYX.CZ API - Odeslání textového příspěvku ==="
echo "URL: ${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/send/text"
echo "Discussion ID: $DISCUSSION_ID"
echo "Obsah: $TEST_CONTENT"
echo

# Příprava JSON dat
json_data=$(cat <<EOF
{
  "content": "$TEST_CONTENT",
  "format": "html"
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
    "${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/send/text")

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
    echo "- Oprávnění k zápisu do diskuze"
    echo "- TEST_CONTENT v secret.txt"
    
    if [ "$http_status" -eq 403 ]; then
        echo "- Možná nemáte právo psát do této diskuze"
    elif [ "$http_status" -eq 404 ]; then
        echo "- Diskuze s ID $DISCUSSION_ID neexistuje"
    fi
else
    echo
    echo "✓ Příspěvek byl úspěšně odeslán!"
fi
