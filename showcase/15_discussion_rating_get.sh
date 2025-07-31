#!/bin/bash

# NYX.CZ API - Načtení hodnocení příspěvku
# GET /api/discussion/{discussion_id}/rating/{id}

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
if [ -z "$DISCUSSION_ID" ] || [ "$DISCUSSION_ID" = "12345" ]; then
    echo "Chyba: Nastavte DISCUSSION_ID v secret.txt"
    echo "Příklad: DISCUSSION_ID=123456"
    exit 1
fi

if [ -z "$POST_ID" ] || [ "$POST_ID" = "67890" ]; then
    echo "Chyba: Nastavte POST_ID v secret.txt"
    echo "Příklad: POST_ID=789012"
    exit 1
fi

echo "=== NYX.CZ API - Načtení hodnocení příspěvku ==="
echo "URL: ${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/rating/${POST_ID}"
echo "Diskuze ID: $DISCUSSION_ID"
echo "Příspěvek ID: $POST_ID"
echo

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    "${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/rating/${POST_ID}")

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
        echo "=== Analýza hodnocení ==="
        
        # Základní informace o hodnocení
        total_rating=$(echo "$http_body" | jq -r '.rating // 0')
        positive_count=$(echo "$http_body" | jq -r '.positive_count // 0')
        negative_count=$(echo "$http_body" | jq -r '.negative_count // 0')
        my_rating=$(echo "$http_body" | jq -r '.my_rating // "none"')
        
        echo "Celkové hodnocení: $total_rating"
        echo "Kladná hodnocení: $positive_count"
        echo "Záporná hodnocení: $negative_count"
        echo "Moje hodnocení: $my_rating"
        
        # Analýza hodnotitelů
        if echo "$http_body" | jq -e '.raters' >/dev/null 2>&1; then
            echo
            echo "=== Hodnotitelé ==="
            
            # Počet hodnotitelů
            raters_count=$(echo "$http_body" | jq -r '.raters | length')
            echo "Celkem hodnotitelů: $raters_count"
            
            # Rozdělení podle typu hodnocení
            if [ "$raters_count" -gt 0 ]; then
                echo
                echo "=== Rozdělení hodnocení ==="
                echo "$http_body" | jq -r '.raters[] | .rating_type' | sort | uniq -c | while read count type; do
                    case $type in
                        "positive") echo "👍 Kladné: $count" ;;
                        "negative") echo "👎 Záporné: $count" ;;
                        "negative_visible") echo "👎 Záporné (viditelné): $count" ;;
                        *) echo "❓ $type: $count" ;;
                    esac
                done
                
                # Seznam hodnotitelů podle typu
                echo
                echo "=== Hodnotitelé podle typu ==="
                
                # Kladní hodnotitelé
                positive_raters=$(echo "$http_body" | jq -r '.raters[] | select(.rating_type == "positive") | .username' | head -5)
                if [ -n "$positive_raters" ]; then
                    echo "👍 Kladně hodnotili:"
                    echo "$positive_raters" | while read username; do
                        echo "  - $username"
                    done
                fi
                
                # Záporní hodnotitelé
                negative_raters=$(echo "$http_body" | jq -r '.raters[] | select(.rating_type == "negative" or .rating_type == "negative_visible") | .username' | head -5)
                if [ -n "$negative_raters" ]; then
                    echo "👎 Záporně hodnotili:"
                    echo "$negative_raters" | while read username; do
                        echo "  - $username"
                    done
                fi
            fi
        fi
        
        # Analýza přátel
        if echo "$http_body" | jq -e '.friends_rating' >/dev/null 2>&1; then
            echo
            echo "=== Hodnocení přátel ==="
            
            friends_positive=$(echo "$http_body" | jq -r '.friends_rating.positive // 0')
            friends_negative=$(echo "$http_body" | jq -r '.friends_rating.negative // 0')
            friends_total=$(echo "$http_body" | jq -r '.friends_rating.total // 0')
            
            echo "Přátelé - kladné: $friends_positive"
            echo "Přátelé - záporné: $friends_negative"
            echo "Přátelé - celkem: $friends_total"
            
            if [ "$friends_total" -gt 0 ]; then
                friends_ratio=$(echo "scale=1; $friends_positive * 100 / $friends_total" | bc 2>/dev/null || echo "N/A")
                echo "Poměr kladných u přátel: $friends_ratio%"
            fi
        fi
        
        # Časové informace
        if echo "$http_body" | jq -e '.last_rated_at' >/dev/null 2>&1; then
            echo
            echo "=== Časové informace ==="
            last_rated=$(echo "$http_body" | jq -r '.last_rated_at')
            echo "Naposledy hodnoceno: $last_rated"
        fi
        
        # Statistiky hodnocení
        echo
        echo "=== Statistiky hodnocení ==="
        
        if [ "$positive_count" -gt 0 ] || [ "$negative_count" -gt 0 ]; then
            total_votes=$((positive_count + negative_count))
            if [ "$total_votes" -gt 0 ]; then
                positive_ratio=$(echo "scale=1; $positive_count * 100 / $total_votes" | bc 2>/dev/null || echo "N/A")
                echo "Poměr kladných hodnocení: $positive_ratio%"
                
                # Hodnocení kvality
                if [ "$total_rating" -gt 5 ]; then
                    echo "📈 Kvalita: Velmi dobré hodnocení"
                elif [ "$total_rating" -gt 0 ]; then
                    echo "📊 Kvalita: Pozitivní hodnocení"
                elif [ "$total_rating" -eq 0 ]; then
                    echo "📊 Kvalita: Neutrální hodnocení"
                else
                    echo "📉 Kvalita: Negativní hodnocení"
                fi
            fi
        else
            echo "📊 Příspěvek zatím nebyl hodnocen"
        fi
        
        # Doporučení pro akce
        echo
        echo "=== Možné akce ==="
        
        case $my_rating in
            "none")
                echo "- Můžete příspěvek ohodnotit (discussion_rate.sh)"
                echo "- Použijte RATE_ACTION=positive nebo negative"
                ;;
            "positive")
                echo "- Máte kladné hodnocení"
                echo "- Můžete hodnocení odebrat (RATE_ACTION=remove)"
                ;;
            "negative"|"negative_visible")
                echo "- Máte záporné hodnocení"
                echo "- Můžete hodnocení odebrat (RATE_ACTION=remove)"
                ;;
        esac
        
        echo "- Přidat do upomínek (discussion_reminder.sh)"
        echo "- Zobrazit celou diskuzi (discussion_get.sh)"
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
    echo "- POST_ID v secret.txt"
    
    if [ "$http_status" -eq 400 ]; then
        echo "- Neplatné ID diskuze nebo příspěvku"
    elif [ "$http_status" -eq 401 ]; then
        echo "- Neplatný nebo chybějící API token"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění pro čtení hodnocení"
    elif [ "$http_status" -eq 404 ]; then
        echo "- Diskuze nebo příspěvek neexistuje"
    fi
else
    echo
    echo "✓ Hodnocení úspěšně načteno!"
    
    # Další akce
    echo
    echo "=== Související akce ==="
    echo "- Ohodnotit příspěvek: discussion_rate.sh"
    echo "- Zobrazit diskuzi: discussion_get.sh"
    echo "- Přidat do upomínek: discussion_reminder.sh"
fi

echo
echo "Tip: Pro hodnocení příspěvku použijte discussion_rate.sh"
