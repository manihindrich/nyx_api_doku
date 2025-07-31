#!/bin/bash

# NYX.CZ API - Získání domovské stránky diskuze
# GET /api/discussion/{discussionId}/home

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
if [ -z "$DISCUSSION_ID" ]; then
    echo "Chyba: Nastavte DISCUSSION_ID v secret.txt"
    exit 1
fi

echo "=== NYX.CZ API - Domovská stránka diskuze ==="
echo "URL: ${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/home"
echo "Discussion ID: $DISCUSSION_ID"
echo

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    "${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/home")

# Rozdělení odpovědi a status kódu
http_body=$(echo "$response" | sed '$d')
http_status=$(echo "$response" | tail -n1 | sed 's/HTTP_STATUS://')

echo "HTTP Status: $http_status"
echo

# Formátování JSON výstupu
if command -v jq >/dev/null 2>&1; then
    echo "$http_body" | jq '.'
    
    # Dodatečné analýzy s jq
    if [ "$http_status" -eq 200 ]; then
        echo
        echo "=== Analýza domovské stránky ==="
        
        # Základní informace
        title=$(echo "$http_body" | jq -r '.title // "Bez názvu"')
        description=$(echo "$http_body" | jq -r '.description // "Bez popisu"')
        content=$(echo "$http_body" | jq -r '.content // "Bez obsahu"')
        
        echo "Název: $title"
        echo "Popis: $description"
        
        # Délka obsahu
        content_length=$(echo "$content" | wc -c)
        echo "Délka obsahu: $content_length znaků"
        
        # Kontrola HTML obsahu
        if echo "$content" | grep -q "<"; then
            echo "Typ obsahu: HTML"
            # Počet HTML tagů
            html_tags=$(echo "$content" | grep -o '<[^>]*>' | wc -l)
            echo "Počet HTML tagů: $html_tags"
        else
            echo "Typ obsahu: Prostý text"
        fi
        
        # Metadata
        created_at=$(echo "$http_body" | jq -r '.createdAt // "neznámé"')
        updated_at=$(echo "$http_body" | jq -r '.updatedAt // "neznámé"')
        author=$(echo "$http_body" | jq -r '.author.username // .author // "neznámý"')
        
        if [ "$created_at" != "null" ] && [ "$created_at" != "neznámé" ]; then
            echo "Vytvořeno: $created_at"
        fi
        if [ "$updated_at" != "null" ] && [ "$updated_at" != "neznámé" ]; then
            echo "Aktualizováno: $updated_at"
        fi
        if [ "$author" != "null" ] && [ "$author" != "neznámý" ]; then
            echo "Autor: $author"
        fi
        
        # Statistiky
        echo
        echo "=== Statistiky ==="
        echo "- Celková velikost odpovědi: $(echo "$http_body" | wc -c) znaků"
        echo "- Počet řádků obsahu: $(echo "$content" | wc -l)"
        
        # Kontrola prázdného obsahu
        if [ "$content" = "null" ] || [ -z "$content" ] || [ "$content" = "Bez obsahu" ]; then
            echo "⚠️  Domovská stránka nemá nastavený obsah"
        else
            echo "✓ Domovská stránka obsahuje data"
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
    
    if [ "$http_status" -eq 404 ]; then
        echo "- Diskuze neexistuje nebo nemá domovskou stránku"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění pro zobrazení domovské stránky"
    elif [ "$http_status" -eq 401 ]; then
        echo "- Neplatný nebo chybějící API token"
    fi
else
    echo
    echo "✓ Domovská stránka diskuze úspěšně načtena!"
fi

echo
echo "Tip: Pro úpravu domovské stránky použijte discussion_home_post.sh"
