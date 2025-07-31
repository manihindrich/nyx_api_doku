#!/bin/bash

# NYX.CZ API - Vyhledání uživatele
# GET /api/search/username/{username}

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

# Kontrola SEARCH_USERNAME
if [ -z "$SEARCH_USERNAME" ]; then
    echo "Chyba: Nastavte SEARCH_USERNAME v secret.txt"
    exit 1
fi

echo "=== NYX.CZ API - Vyhledání uživatele ==="
echo "URL: ${NYX_API_BASE_URL}/search/username/${SEARCH_USERNAME}"
echo "Hledaný uživatel: $SEARCH_USERNAME"
echo

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    -H "Content-Type: application/json" \
    "${NYX_API_BASE_URL}/search/username/${SEARCH_USERNAME}")

# Rozdělení odpovědi a status kódu
http_body=$(echo "$response" | sed '$d')
http_status=$(echo "$response" | tail -n1 | sed 's/HTTP_STATUS://')

echo "HTTP Status: $http_status"
echo

# Formátování JSON výstupu
if command -v jq >/dev/null 2>&1; then
    echo "$http_body" | jq '.'
    
    # Statistiky výsledků
    if [ "$http_status" -eq 200 ]; then
        echo
        echo "=== Statistiky výsledků ==="
        exact_count=$(echo "$http_body" | jq '.exact | length' 2>/dev/null || echo "0")
        friends_count=$(echo "$http_body" | jq '.friends | length' 2>/dev/null || echo "0")
        others_count=$(echo "$http_body" | jq '.others | length' 2>/dev/null || echo "0")
        
        echo "Přesné shody: $exact_count"
        echo "Přátelé: $friends_count"
        echo "Ostatní: $others_count"
        echo "Celkem: $((exact_count + friends_count + others_count))"
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
    echo "- SEARCH_USERNAME v secret.txt"
    echo "- Formát uživatelského jména (3-15 znaků, A-Z0-9_)"
    
    if [ "$http_status" -eq 404 ]; then
        echo "- Uživatel '$SEARCH_USERNAME' nebyl nalezen"
    fi
fi

echo
echo "Tip: Změňte SEARCH_USERNAME v secret.txt pro vyhledání jiného uživatele"
