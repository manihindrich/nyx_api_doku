#!/bin/bash

# NYX.CZ API - Získání seznamu zpráv
# GET /api/mail

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

echo "=== NYX.CZ API - Seznam zpráv ==="
echo "URL: ${NYX_API_BASE_URL}/mail"
echo

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    "${NYX_API_BASE_URL}/mail")

# Rozdělení odpovědi a status kódu
http_body=$(echo "$response" | sed '$d')
http_status=$(echo "$response" | tail -n1 | sed 's/HTTP_STATUS://')

echo "HTTP Status: $http_status"
echo

# Formátování JSON výstupu
if command -v jq >/dev/null 2>&1; then
    echo "$http_body" | jq '.'
    
    # Dodatečné statistiky
    if [ "$http_status" -eq 200 ]; then
        echo
        echo "=== Statistiky zpráv ==="
        
        total_messages=$(echo "$http_body" | jq '.data | length // 0')
        echo "Celkem zpráv: $total_messages"
        
        if [ "$total_messages" -gt 0 ]; then
            unread_count=$(echo "$http_body" | jq '[.data[] | select(.read == false)] | length // 0')
            read_count=$(echo "$http_body" | jq '[.data[] | select(.read == true)] | length // 0')
            
            echo "Nepřečtené: $unread_count"
            echo "Přečtené: $read_count"
            
            # Nejnovější zpráva
            latest_message=$(echo "$http_body" | jq -r '.data[0].subject // "N/A"')
            echo "Nejnovější zpráva: $latest_message"
            
            # Odesílatelé
            echo
            echo "Odesílatelé:"
            echo "$http_body" | jq -r '.data[] | .from.username' | sort | uniq -c | sort -nr
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
    echo "- Připojení k internetu"
    
    if [ "$http_status" -eq 401 ]; then
        echo "- Neplatný nebo vypršelý API token"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění"
    fi
else
    echo
    echo "✓ Seznam zpráv byl úspěšně načten!"
fi

echo
echo "Tip: Pro odeslání zprávy použijte mail_send.sh"
