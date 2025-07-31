#!/bin/bash

# NYX.CZ API - Historie navštívených diskuzí
# GET /api/bookmarks/history

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

echo "=== NYX.CZ API - Historie navštívených diskuzí ==="
echo "URL: ${NYX_API_BASE_URL}/bookmarks/history"
echo

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    -H "Content-Type: application/json" \
    "${NYX_API_BASE_URL}/bookmarks/history")

# Rozdělení odpovědi a status kódu
http_body=$(echo "$response" | sed '$d')
http_status=$(echo "$response" | tail -n1 | sed 's/HTTP_STATUS://')

echo "HTTP Status: $http_status"
echo

# Formátování JSON výstupu
if command -v jq >/dev/null 2>&1; then
    echo "$http_body" | jq '.'
    
    # Statistiky historie
    if [ "$http_status" -eq 200 ]; then
        echo
        echo "=== Statistiky historie ==="
        history_count=$(echo "$http_body" | jq '.history | length' 2>/dev/null || echo "0")
        echo "Počet záznamů v historii: $history_count"
        
        if [ "$history_count" -gt 0 ]; then
            echo
            echo "Nejnovější záznamy v historii:"
            echo "$http_body" | jq -r '.history[0:10][] | "  📖 \(.discussion.name) (ID: \(.discussion.id))"' 2>/dev/null
            
            echo
            echo "Statistiky podle domén:"
            echo "$http_body" | jq -r '.history | group_by(.discussion.domain.name) | .[] | "\(.[0].discussion.domain.name): \(length) diskuzí"' 2>/dev/null | head -5
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
    echo "- Platnost tokenu"
    
    if [ "$http_status" -eq 401 ]; then
        echo "- Token je neplatný nebo vypršel"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění"
    fi
fi

echo
echo "Tip: Pro správu historie použijte bookmarks_history_remove.sh nebo bookmarks_history_mark_read.sh"
