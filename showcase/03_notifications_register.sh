#!/bin/bash

# NYX.CZ API - Registrace pro notifikace
# POST /api/register_for_notifications

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

echo "=== NYX.CZ API - Registrace pro notifikace ==="
echo "URL: ${NYX_API_BASE_URL}/register_for_notifications"
echo

# Příprava dat pro POST
post_data="{}"

# Přidání povinných parametrů
if [ -n "$NOTIFICATION_ENDPOINT" ]; then
    post_data=$(echo "$post_data" | jq --arg endpoint "$NOTIFICATION_ENDPOINT" '. + {endpoint: $endpoint}')
else
    echo "Chyba: Nastavte NOTIFICATION_ENDPOINT v secret.txt"
    echo "Příklad: NOTIFICATION_ENDPOINT=https://your-app.com/webhook"
    exit 1
fi

# Přidání volitelných parametrů
if [ -n "$NOTIFICATION_TYPES" ]; then
    # Převod čárkami oddělených hodnot na JSON array
    types_array=$(echo "$NOTIFICATION_TYPES" | jq -R 'split(",") | map(gsub("^\\s+|\\s+$"; ""))')
    post_data=$(echo "$post_data" | jq --argjson types "$types_array" '. + {types: $types}')
fi

if [ -n "$NOTIFICATION_SECRET" ]; then
    post_data=$(echo "$post_data" | jq --arg secret "$NOTIFICATION_SECRET" '. + {secret: $secret}')
fi

if [ -n "$NOTIFICATION_FORMAT" ]; then
    post_data=$(echo "$post_data" | jq --arg format "$NOTIFICATION_FORMAT" '. + {format: $format}')
fi

if [ -n "$NOTIFICATION_ENABLED" ]; then
    post_data=$(echo "$post_data" | jq --argjson enabled "$NOTIFICATION_ENABLED" '. + {enabled: $enabled}')
fi

echo "Registrace notifikačního endpointu..."
echo "Endpoint: $NOTIFICATION_ENDPOINT"

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$post_data" \
    "${NYX_API_BASE_URL}/register_for_notifications")

# Rozdělení odpovědi a status kódu
http_body=$(echo "$response" | sed '$d')
http_status=$(echo "$response" | tail -n1 | sed 's/HTTP_STATUS://')

echo "HTTP Status: $http_status"
echo

# Formátování JSON výstupu
if command -v jq >/dev/null 2>&1; then
    echo "$http_body" | jq '.'
    
    # Dodatečné analýzy s jq
    if [ "$http_status" -eq 200 ] || [ "$http_status" -eq 201 ]; then
        echo
        echo "=== Analýza registrace ==="
        
        # Základní informace
        registration_id=$(echo "$http_body" | jq -r '.id // .registrationId // "neznámé"')
        endpoint=$(echo "$http_body" | jq -r '.endpoint // "neznámý"')
        status=$(echo "$http_body" | jq -r '.status // "neznámý"')
        
        echo "ID registrace: $registration_id"
        echo "Endpoint: $endpoint"
        echo "Stav: $status"
        
        # Registrované typy notifikací
        if echo "$http_body" | jq -e '.types' >/dev/null 2>&1; then
            echo
            echo "=== Registrované typy notifikací ==="
            echo "$http_body" | jq -r '.types[]?' | while read type; do
                echo "- $type"
            done
        fi
        
        # Nastavení
        echo
        echo "=== Nastavení notifikací ==="
        
        format=$(echo "$http_body" | jq -r '.format // "json"')
        enabled=$(echo "$http_body" | jq -r '.enabled // true')
        
        echo "Formát: $format"
        echo "Povoleno: $enabled"
        
        # Bezpečnostní informace
        has_secret=$(echo "$http_body" | jq -r '.hasSecret // false')
        if [ "$has_secret" = "true" ]; then
            echo "Webhook secret: ✓ nastaven"
        else
            echo "Webhook secret: ⚠️  nenastaven"
        fi
        
        # Testovací informace
        test_url=$(echo "$http_body" | jq -r '.testUrl // "nedostupné"')
        if [ "$test_url" != "null" ] && [ "$test_url" != "nedostupné" ]; then
            echo
            echo "=== Testování ==="
            echo "Test URL: $test_url"
            echo "💡 Použijte tuto URL pro test notifikací"
        fi
        
        # Statistiky
        if echo "$http_body" | jq -e '.stats' >/dev/null 2>&1; then
            echo
            echo "=== Statistiky ==="
            
            total_sent=$(echo "$http_body" | jq -r '.stats.totalSent // 0')
            successful=$(echo "$http_body" | jq -r '.stats.successful // 0')
            failed=$(echo "$http_body" | jq -r '.stats.failed // 0')
            
            echo "Celkem odesláno: $total_sent"
            echo "Úspěšné: $successful"
            echo "Neúspěšné: $failed"
            
            if [ "$total_sent" -gt 0 ]; then
                success_rate=$(echo "scale=1; $successful * 100 / $total_sent" | bc 2>/dev/null || echo "N/A")
                echo "Úspěšnost: $success_rate%"
            fi
        fi
        
        # Doporučení pro webhook
        echo
        echo "=== Doporučení pro webhook ==="
        echo "- Implementujte správné HTTP status kódy (200-299)"
        echo "- Ověřujte webhook secret pro bezpečnost"
        echo "- Logujte příchozí notifikace pro debugging"
        echo "- Implementujte retry logiku pro chyby"
        echo "- Používejte HTTPS pro bezpečný přenos"
        
        # Příklad webhook implementace
        echo
        echo "=== Příklad webhook endpointu ==="
        echo "POST $endpoint"
        echo "Headers:"
        echo "  Content-Type: application/json"
        if [ "$has_secret" = "true" ]; then
            echo "  X-NYX-Signature: sha256=<signature>"
        fi
        echo "Body:"
        echo "  {"
        echo "    \"type\": \"discussion_reply\","
        echo "    \"data\": { ... },"
        echo "    \"timestamp\": \"2024-01-01T12:00:00Z\""
        echo "  }"
    fi
else
    echo "$http_body"
    echo
    echo "Tip: Nainstalujte 'jq' pro lepší formátování JSON: sudo apt install jq"
fi

# Kontrola chyb
if [ "$http_status" -ne 200 ] && [ "$http_status" -ne 201 ]; then
    echo
    echo "Chyba při registraci! Zkontrolujte:"
    echo "- API token v secret.txt"
    echo "- NOTIFICATION_ENDPOINT v secret.txt"
    
    if [ "$http_status" -eq 400 ]; then
        echo "- Neplatný endpoint URL"
        echo "- Neplatné typy notifikací"
        echo "- Neplatný formát dat"
    elif [ "$http_status" -eq 401 ]; then
        echo "- Neplatný nebo chybějící API token"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění pro registraci"
    elif [ "$http_status" -eq 409 ]; then
        echo "- Endpoint již je registrován"
        echo "- Použijte jiný endpoint nebo aktualizujte existující"
    elif [ "$http_status" -eq 422 ]; then
        echo "- Endpoint není dostupný"
        echo "- Zkontrolujte, že endpoint odpovídá na HTTP požadavky"
    fi
else
    echo
    echo "✅ Registrace pro notifikace byla úspěšná!"
    
    # Další kroky
    echo
    echo "=== Další kroky ==="
    echo "1. Implementujte webhook endpoint na vaší aplikaci"
    echo "2. Otestujte příjem notifikací"
    echo "3. Nastavte monitoring a logování"
    echo "4. Použijte notifications_get.sh pro kontrolu notifikací"
    
    # Bezpečnostní tipy
    echo
    echo "=== Bezpečnostní tipy ==="
    echo "- Vždy ověřujte webhook signature"
    echo "- Používejte HTTPS pro webhook endpoint"
    echo "- Implementujte rate limiting"
    echo "- Logujte všechny příchozí požadavky"
    echo "- Pravidelně rotujte webhook secret"
fi

echo
echo "Tip: Pro kontrolu notifikací použijte notifications_get.sh"
