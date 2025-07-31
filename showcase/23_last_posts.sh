#!/bin/bash

# NYX.CZ API - Nejnovější příspěvky
# GET /api/last

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

echo "=== NYX.CZ API - Nejnovější příspěvky ==="

# Sestavení URL s parametry
url="${NYX_API_BASE_URL}/last"
params=""

# Přidání parametrů pokud jsou nastaveny
if [ -n "$DOMAIN_ID" ] && [ "$DOMAIN_ID" != "1" ]; then
    params="${params}&domain=${DOMAIN_ID}"
fi

if [ -n "$MIN_RATING" ] && [ "$MIN_RATING" != "5" ]; then
    params="${params}&min_rating=${MIN_RATING}"
fi

# Přidání boolean parametrů
params="${params}&rated_by_friends=false"
params="${params}&rated_by_me=false"

# Odstranění prvního & znaku
if [ -n "$params" ]; then
    params="?${params#&}"
    url="${url}${params}"
fi

echo "URL: $url"
echo "Parametry:"
echo "  - domain: ${DOMAIN_ID:-všechny}"
echo "  - min_rating: ${MIN_RATING:-bez omezení}"
echo "  - rated_by_friends: false"
echo "  - rated_by_me: false"
echo

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    -H "Content-Type: application/json" \
    "$url")

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
    echo "- Připojení k internetu"
    echo "- Platnost tokenu"
    echo "- Parametry v secret.txt (DOMAIN_ID, MIN_RATING)"
fi

echo
echo "Tip: Upravte DOMAIN_ID a MIN_RATING v secret.txt pro filtrování"
