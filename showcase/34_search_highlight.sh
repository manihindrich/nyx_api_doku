#!/bin/bash

# NYX.CZ API - Vyhledávání se zvýrazněním
# GET /api/search/highlight

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
url="${NYX_API_BASE_URL}/search/highlight?q=${SEARCH_QUERY}"

# Přidání volitelných parametrů
if [ -n "$SEARCH_LIMIT" ]; then
    url="${url}&limit=${SEARCH_LIMIT}"
fi

if [ -n "$SEARCH_OFFSET" ]; then
    url="${url}&offset=${SEARCH_OFFSET}"
fi

if [ -n "$SEARCH_FRAGMENT_SIZE" ]; then
    url="${url}&fragmentSize=${SEARCH_FRAGMENT_SIZE}"
fi

if [ -n "$SEARCH_MAX_FRAGMENTS" ]; then
    url="${url}&maxFragments=${SEARCH_MAX_FRAGMENTS}"
fi

if [ -n "$SEARCH_PRE_TAG" ]; then
    url="${url}&preTag=${SEARCH_PRE_TAG}"
fi

if [ -n "$SEARCH_POST_TAG" ]; then
    url="${url}&postTag=${SEARCH_POST_TAG}"
fi

echo "=== NYX.CZ API - Vyhledávání se zvýrazněním ==="
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
        echo "=== Analýza zvýrazněného vyhledávání ==="
        
        # Celkový počet výsledků
        total=$(echo "$http_body" | jq -r '.total // 0')
        count=$(echo "$http_body" | jq -r '.results | length // 0')
        
        echo "Celkem nalezeno: $total výsledků"
        echo "Zobrazeno: $count výsledků"
        
        # Analýza fragmentů
        if [ "$count" -gt 0 ]; then
            echo
            echo "=== Analýza fragmentů ==="
            
            # Počet výsledků s fragmenty
            fragments_count=$(echo "$http_body" | jq -r '[.results[] | select(.fragments)] | length')
            echo "Výsledky s fragmenty: $fragments_count"
            
            # Celkový počet fragmentů
            total_fragments=$(echo "$http_body" | jq -r '[.results[].fragments[]?] | length')
            echo "Celkový počet fragmentů: $total_fragments"
            
            # Průměrná délka fragmentů
            if [ "$total_fragments" -gt 0 ]; then
                avg_length=$(echo "$http_body" | jq -r '[.results[].fragments[]? | length] | add / length')
                echo "Průměrná délka fragmentu: ${avg_length} znaků"
            fi
            
            # Top výsledky s fragmenty
            echo
            echo "=== Top výsledky s fragmenty ==="
            echo "$http_body" | jq -r '.results[0:3][] | select(.fragments) | "- " + (.title // "Bez názvu") + " (" + (.fragments | length | tostring) + " fragmentů)"'
            
            # Ukázka fragmentů
            echo
            echo "=== Ukázka zvýrazněných fragmentů ==="
            echo "$http_body" | jq -r '.results[0:2][] | .fragments[0:2][]?' | head -5 | while read fragment; do
                # Odstranění HTML tagů pro čitelnější výpis v terminálu
                clean_fragment=$(echo "$fragment" | sed 's/<[^>]*>//g')
                echo "- $clean_fragment"
            done
            
            # Analýza zvýrazněných termínů
            echo
            echo "=== Analýza zvýrazněných termínů ==="
            
            # Extrakce termínů mezi tagy (defaultně <em> a </em>)
            highlighted_terms=$(echo "$http_body" | jq -r '.results[].fragments[]?' | grep -o '<em>[^<]*</em>' | sed 's/<[^>]*>//g' | sort | uniq -c | sort -nr | head -5)
            
            if [ -n "$highlighted_terms" ]; then
                echo "Nejčastější zvýrazněné termíny:"
                echo "$highlighted_terms" | while read count term; do
                    echo "- $term: $count výskytů"
                done
            fi
        fi
        
        # Konfigurace zvýrazňování
        echo
        echo "=== Konfigurace zvýrazňování ==="
        pre_tag=$(echo "$http_body" | jq -r '.highlightConfig.preTag // "<em>"')
        post_tag=$(echo "$http_body" | jq -r '.highlightConfig.postTag // "</em>"')
        fragment_size=$(echo "$http_body" | jq -r '.highlightConfig.fragmentSize // "neznámá"')
        max_fragments=$(echo "$http_body" | jq -r '.highlightConfig.maxFragments // "neznámý"')
        
        echo "Počáteční tag: $pre_tag"
        echo "Koncový tag: $post_tag"
        echo "Velikost fragmentu: $fragment_size"
        echo "Max fragmentů: $max_fragments"
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
        echo "- Zkontrolujte SEARCH_FRAGMENT_SIZE a SEARCH_MAX_FRAGMENTS"
    elif [ "$http_status" -eq 401 ]; then
        echo "- Neplatný nebo chybějící API token"
    elif [ "$http_status" -eq 429 ]; then
        echo "- Příliš mnoho požadavků - zkuste později"
    fi
else
    echo
    echo "✓ Vyhledávání se zvýrazněním úspěšně dokončeno!"
    
    # Doporučení pro optimalizaci
    echo
    echo "=== Tipy pro zvýrazněné vyhledávání ==="
    echo "- Upravte SEARCH_FRAGMENT_SIZE pro delší/kratší úryvky"
    echo "- Nastavte SEARCH_MAX_FRAGMENTS pro více úryvků na výsledek"
    echo "- Použijte vlastní SEARCH_PRE_TAG a SEARCH_POST_TAG pro styling"
    echo "- Kombinujte s dalšími vyhledávacími endpointy"
fi

echo
echo "Tip: Pro jiné typy vyhledávání použijte search_v2.sh nebo search_unified.sh"
