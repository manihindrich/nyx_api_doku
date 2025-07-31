#!/bin/bash

# NYX.CZ API - Pokročilé vyhledávání v2
# GET /api/search-v2

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

# Kontrola vyhledávacího dotazu
if [ -z "$SEARCH_QUERY" ]; then
    echo "Chyba: Nastavte SEARCH_QUERY v secret.txt"
    exit 1
fi

# Sestavení URL s parametry
url="${NYX_API_BASE_URL}/search-v2?q=${SEARCH_QUERY}"

# Přidání volitelných parametrů
if [ -n "$SEARCH_TYPE" ]; then
    url="${url}&type=${SEARCH_TYPE}"
fi

if [ -n "$SEARCH_LIMIT" ]; then
    url="${url}&limit=${SEARCH_LIMIT}"
fi

if [ -n "$SEARCH_OFFSET" ]; then
    url="${url}&offset=${SEARCH_OFFSET}"
fi

if [ -n "$SEARCH_SORT" ]; then
    url="${url}&sort=${SEARCH_SORT}"
fi

if [ -n "$SEARCH_CATEGORY" ]; then
    url="${url}&category=${SEARCH_CATEGORY}"
fi

echo "=== NYX.CZ API - Pokročilé vyhledávání v2 ==="
echo "URL: $url"
echo "Dotaz: $SEARCH_QUERY"
echo

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    "$url")

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
        echo "=== Analýza výsledků vyhledávání ==="
        
        # Celkový počet výsledků
        total=$(echo "$http_body" | jq -r '.total // 0')
        count=$(echo "$http_body" | jq -r '.results | length // 0')
        
        echo "Celkem nalezeno: $total výsledků"
        echo "Zobrazeno: $count výsledků"
        
        # Analýza typů výsledků
        if [ "$count" -gt 0 ]; then
            echo
            echo "=== Typy výsledků ==="
            echo "$http_body" | jq -r '.results[] | .type // "neznámý"' | sort | uniq -c | while read count type; do
                echo "- $type: $count výsledků"
            done
            
            # Top výsledky
            echo
            echo "=== Top 5 výsledků ==="
            echo "$http_body" | jq -r '.results[0:5][] | "- " + (.title // .name // "Bez názvu") + " (" + (.type // "neznámý") + ")"'
            
            # Statistiky skóre
            echo
            echo "=== Statistiky relevance ==="
            max_score=$(echo "$http_body" | jq -r '[.results[].score // 0] | max')
            min_score=$(echo "$http_body" | jq -r '[.results[].score // 0] | min')
            avg_score=$(echo "$http_body" | jq -r '[.results[].score // 0] | add / length')
            
            if [ "$max_score" != "null" ] && [ "$max_score" != "0" ]; then
                echo "Nejvyšší skóre: $max_score"
                echo "Nejnižší skóre: $min_score"
                echo "Průměrné skóre: $avg_score"
            fi
        fi
        
        # Informace o stránkování
        if echo "$http_body" | jq -e '.pagination' >/dev/null 2>&1; then
            echo
            echo "=== Stránkování ==="
            current_page=$(echo "$http_body" | jq -r '.pagination.currentPage // 1')
            total_pages=$(echo "$http_body" | jq -r '.pagination.totalPages // 1')
            echo "Aktuální stránka: $current_page z $total_pages"
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
    echo "- SEARCH_QUERY v secret.txt"
    
    if [ "$http_status" -eq 400 ]; then
        echo "- Neplatný formát dotazu nebo parametrů"
    elif [ "$http_status" -eq 401 ]; then
        echo "- Neplatný nebo chybějící API token"
    elif [ "$http_status" -eq 429 ]; then
        echo "- Příliš mnoho požadavků - zkuste později"
    fi
else
    echo
    echo "✓ Vyhledávání úspěšně dokončeno!"
    
    # Doporučení pro optimalizaci
    echo
    echo "=== Tipy pro lepší vyhledávání ==="
    echo "- Použijte specifičtější klíčová slova"
    echo "- Zkuste různé typy vyhledávání (type parameter)"
    echo "- Využijte filtrování podle kategorií"
    echo "- Pro velké množství výsledků použijte stránkování"
fi

echo
echo "Tip: Pro jiné typy vyhledávání použijte search_unified.sh nebo search_highlight.sh"
