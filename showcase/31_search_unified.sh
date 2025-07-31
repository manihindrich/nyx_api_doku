#!/bin/bash

# NYX.CZ API - Sjednocené vyhledávání
# GET /api/search/unified

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
url="${NYX_API_BASE_URL}/search/unified?q=${SEARCH_QUERY}"

# Přidání volitelných parametrů
if [ -n "$SEARCH_LIMIT" ]; then
    url="${url}&limit=${SEARCH_LIMIT}"
fi

if [ -n "$SEARCH_OFFSET" ]; then
    url="${url}&offset=${SEARCH_OFFSET}"
fi

if [ -n "$SEARCH_INCLUDE_CONTENT" ]; then
    url="${url}&includeContent=${SEARCH_INCLUDE_CONTENT}"
fi

if [ -n "$SEARCH_HIGHLIGHT" ]; then
    url="${url}&highlight=${SEARCH_HIGHLIGHT}"
fi

echo "=== NYX.CZ API - Sjednocené vyhledávání ==="
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
        echo "=== Analýza sjednoceného vyhledávání ==="
        
        # Celkový počet výsledků
        total=$(echo "$http_body" | jq -r '.total // 0')
        count=$(echo "$http_body" | jq -r '.results | length // 0')
        
        echo "Celkem nalezeno: $total výsledků"
        echo "Zobrazeno: $count výsledků"
        
        # Analýza zdrojů
        if [ "$count" -gt 0 ]; then
            echo
            echo "=== Zdroje výsledků ==="
            echo "$http_body" | jq -r '.results[] | .source // "neznámý"' | sort | uniq -c | while read count source; do
                echo "- $source: $count výsledků"
            done
            
            # Analýza typů obsahu
            echo
            echo "=== Typy obsahu ==="
            echo "$http_body" | jq -r '.results[] | .contentType // "neznámý"' | sort | uniq -c | while read count type; do
                echo "- $type: $count výsledků"
            done
            
            # Top výsledky s relevancí
            echo
            echo "=== Top 5 výsledků ==="
            echo "$http_body" | jq -r '.results[0:5][] | "- " + (.title // "Bez názvu") + " [" + (.source // "neznámý") + "] (relevance: " + (.relevance // "0" | tostring) + ")"'
            
            # Kontrola zvýrazněných úryvků
            highlights_count=$(echo "$http_body" | jq -r '[.results[] | select(.highlights)] | length')
            if [ "$highlights_count" -gt 0 ]; then
                echo
                echo "=== Zvýrazněné úryvky ==="
                echo "Počet výsledků se zvýrazněním: $highlights_count"
                echo "$http_body" | jq -r '.results[] | select(.highlights) | .highlights[]?' | head -3 | while read highlight; do
                    echo "- $highlight"
                done
            fi
            
            # Statistiky relevance
            echo
            echo "=== Statistiky relevance ==="
            max_relevance=$(echo "$http_body" | jq -r '[.results[].relevance // 0] | max')
            min_relevance=$(echo "$http_body" | jq -r '[.results[].relevance // 0] | min')
            avg_relevance=$(echo "$http_body" | jq -r '[.results[].relevance // 0] | add / length')
            
            if [ "$max_relevance" != "null" ] && [ "$max_relevance" != "0" ]; then
                echo "Nejvyšší relevance: $max_relevance"
                echo "Nejnižší relevance: $min_relevance"
                echo "Průměrná relevance: $avg_relevance"
            fi
        fi
        
        # Informace o výkonu
        if echo "$http_body" | jq -e '.searchTime' >/dev/null 2>&1; then
            search_time=$(echo "$http_body" | jq -r '.searchTime')
            echo
            echo "=== Výkon vyhledávání ==="
            echo "Čas vyhledávání: ${search_time}ms"
        fi
        
        # Návrhy pro zlepšení dotazu
        if echo "$http_body" | jq -e '.suggestions' >/dev/null 2>&1; then
            echo
            echo "=== Návrhy pro zlepšení ==="
            echo "$http_body" | jq -r '.suggestions[]?' | while read suggestion; do
                echo "- $suggestion"
            done
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
    echo "✓ Sjednocené vyhledávání úspěšně dokončeno!"
    
    # Doporučení pro optimalizaci
    echo
    echo "=== Výhody sjednoceného vyhledávání ==="
    echo "- Prohledává všechny dostupné zdroje současně"
    echo "- Poskytuje jednotný formát výsledků"
    echo "- Automaticky řadí podle relevance"
    echo "- Podporuje zvýrazňování nalezených termínů"
fi

echo
echo "Tip: Pro specifické vyhledávání použijte search_v2.sh nebo search_highlight.sh"
