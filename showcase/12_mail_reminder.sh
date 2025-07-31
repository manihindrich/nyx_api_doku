#!/bin/bash

# NYX.CZ API - Nastavení připomínky zprávy
# POST /api/mail/reminder/{id}/{newState}

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
if [ -z "$MAIL_REMINDER_ID" ]; then
    echo "Chyba: Nastavte MAIL_REMINDER_ID v secret.txt"
    exit 1
fi

if [ -z "$MAIL_REMINDER_STATE" ]; then
    echo "Chyba: Nastavte MAIL_REMINDER_STATE v secret.txt (true/false)"
    exit 1
fi

echo "=== NYX.CZ API - Nastavení připomínky zprávy ==="
echo "URL: ${NYX_API_BASE_URL}/mail/reminder/${MAIL_REMINDER_ID}/${MAIL_REMINDER_STATE}"
echo "Mail ID: $MAIL_REMINDER_ID"
echo "Nový stav: $MAIL_REMINDER_STATE"
echo

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    "${NYX_API_BASE_URL}/mail/reminder/${MAIL_REMINDER_ID}/${MAIL_REMINDER_STATE}")

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
    echo "- MAIL_REMINDER_ID v secret.txt (existuje zpráva?)"
    echo "- MAIL_REMINDER_STATE v secret.txt (true/false)"
    
    if [ "$http_status" -eq 400 ]; then
        echo "- Neplatný formát parametrů"
    elif [ "$http_status" -eq 404 ]; then
        echo "- Zpráva s ID $MAIL_REMINDER_ID neexistuje"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění"
    fi
else
    echo
    if [ "$MAIL_REMINDER_STATE" = "true" ]; then
        echo "✓ Připomínka byla úspěšně zapnuta!"
    else
        echo "✓ Připomínka byla úspěšně vypnuta!"
    fi
    echo "Mail ID: $MAIL_REMINDER_ID"
fi

echo
echo "Tip: Pro zobrazení zpráv použijte mail_get.sh"
