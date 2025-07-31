#!/bin/bash

# NYX.CZ API - Odeslání zprávy
# POST /api/mail/send

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
if [ -z "$MAIL_TO_USERNAME" ]; then
    echo "Chyba: Nastavte MAIL_TO_USERNAME v secret.txt"
    exit 1
fi

if [ -z "$MAIL_SUBJECT" ]; then
    echo "Chyba: Nastavte MAIL_SUBJECT v secret.txt"
    exit 1
fi

if [ -z "$MAIL_CONTENT" ]; then
    echo "Chyba: Nastavte MAIL_CONTENT v secret.txt"
    exit 1
fi

echo "=== NYX.CZ API - Odeslání zprávy ==="
echo "URL: ${NYX_API_BASE_URL}/mail/send"
echo "Příjemce: $MAIL_TO_USERNAME"
echo "Předmět: $MAIL_SUBJECT"
echo

# Příprava JSON dat
json_data=$(cat <<EOF
{
  "to": "$MAIL_TO_USERNAME",
  "subject": "$MAIL_SUBJECT",
  "content": "$MAIL_CONTENT"
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
    "${NYX_API_BASE_URL}/mail/send")

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
    echo "- MAIL_TO_USERNAME v secret.txt (existuje uživatel?)"
    echo "- MAIL_SUBJECT v secret.txt (není prázdný?)"
    echo "- MAIL_CONTENT v secret.txt (není prázdný?)"
    
    if [ "$http_status" -eq 400 ]; then
        echo "- Neplatná data (zkontrolujte formát)"
    elif [ "$http_status" -eq 404 ]; then
        echo "- Uživatel '$MAIL_TO_USERNAME' neexistuje"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění"
    fi
else
    echo
    echo "✓ Zpráva byla úspěšně odeslána!"
    echo "Příjemce: $MAIL_TO_USERNAME"
    echo "Předmět: $MAIL_SUBJECT"
fi

echo
echo "Tip: Pro zobrazení odeslaných zpráv použijte mail_get.sh"
