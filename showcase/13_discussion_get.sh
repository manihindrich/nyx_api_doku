#!/bin/bash

# NYX.CZ API - Získání diskuze
# GET /api/discussion/{discussionId}

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

echo "=== NYX.CZ API - Získání diskuze ==="
echo "URL: ${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}"
echo "Discussion ID: $DISCUSSION_ID"
echo

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    "${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}")

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
        echo "=== Statistiky diskuze ==="
        
        title=$(echo "$http_body" | jq -r '.data.title // "N/A"')
        echo "Název: $title"
        
        posts_count=$(echo "$http_body" | jq '.data.posts | length // 0')
        echo "Počet příspěvků: $posts_count"
        
        if [ "$posts_count" -gt 0 ]; then
            # Analýza autorů
            echo
            echo "Autoři příspěvků:"
            echo "$http_body" | jq -r '.data.posts[] | .author.username' | sort | uniq -c | sort -nr
            
            # Nejnovější příspěvek
            latest_post=$(echo "$http_body" | jq -r '.data.posts[0].content // "N/A"' | head -c 100)
            echo
            echo "Nejnovější příspěvek (prvních 100 znaků):"
            echo "$latest_post..."
            
            # Rating statistiky
            total_rating=$(echo "$http_body" | jq '[.data.posts[] | .rating // 0] | add // 0')
            avg_rating=$(echo "$http_body" | jq '[.data.posts[] | .rating // 0] | add / length')
            echo
            echo "Celkový rating: $total_rating"
            echo "Průměrný rating: $avg_rating"
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
    echo "- DISCUSSION_ID v secret.txt"
    echo "- Existenci diskuze s daným ID"
    
    if [ "$http_status" -eq 404 ]; then
        echo "- Diskuze s ID $DISCUSSION_ID neexistuje"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění pro přístup k diskuzi"
    fi
else
    echo
    echo "✓ Diskuze byla úspěšně načtena!"
fi

echo
echo "Tip: Pro odeslání příspěvku použijte discussion_send.sh"
