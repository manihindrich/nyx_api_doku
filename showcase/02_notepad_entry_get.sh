#!/bin/bash

# NYX.CZ API - Načtení konkrétní poznámky
# GET /api/notepad/{entry_id}

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

# Kontrola ENTRY_ID
if [ -z "$ENTRY_ID" ]; then
    echo "Chyba: Nastavte ENTRY_ID v secret.txt"
    exit 1
fi

echo "=== NYX.CZ API - Načtení konkrétní poznámky ==="
echo "URL: ${NYX_API_BASE_URL}/notepad/${ENTRY_ID}"
echo "Entry ID: $ENTRY_ID"
echo

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    -H "Content-Type: application/json" \
    "${NYX_API_BASE_URL}/notepad/${ENTRY_ID}")

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
    echo "- ENTRY_ID v secret.txt"
    echo "- Existenci poznámky s daným ID"
    echo "- Oprávnění k poznámce"
fi
