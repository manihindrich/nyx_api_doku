#!/bin/bash

# NYX.CZ API - Získání notifikací
# GET /api/notifications

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

# Sestavení URL s parametry
url="${NYX_API_BASE_URL}/notifications"

# Přidání volitelných parametrů
params=""

if [ -n "$NOTIFICATIONS_LIMIT" ]; then
    params="${params}&limit=${NOTIFICATIONS_LIMIT}"
fi

if [ -n "$NOTIFICATIONS_OFFSET" ]; then
    params="${params}&offset=${NOTIFICATIONS_OFFSET}"
fi

if [ -n "$NOTIFICATIONS_TYPE" ]; then
    params="${params}&type=${NOTIFICATIONS_TYPE}"
fi

if [ -n "$NOTIFICATIONS_READ" ]; then
    params="${params}&read=${NOTIFICATIONS_READ}"
fi

if [ -n "$NOTIFICATIONS_SINCE" ]; then
    params="${params}&since=${NOTIFICATIONS_SINCE}"
fi

# Přidání parametrů k URL
if [ -n "$params" ]; then
    url="${url}?${params:1}"  # Odstraní první &
fi

echo "=== NYX.CZ API - Získání notifikací ==="
echo "URL: $url"
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
        echo "=== Analýza notifikací ==="
        
        # Celkový počet notifikací
        total=$(echo "$http_body" | jq -r '.total // 0')
        count=$(echo "$http_body" | jq -r '.notifications | length // 0')
        unread_count=$(echo "$http_body" | jq -r '.unreadCount // 0')
        
        echo "Celkem notifikací: $total"
        echo "Zobrazeno: $count"
        echo "Nepřečtené: $unread_count"
        
        # Analýza typů notifikací
        if [ "$count" -gt 0 ]; then
            echo
            echo "=== Typy notifikací ==="
            echo "$http_body" | jq -r '.notifications[] | .type // "neznámý"' | sort | uniq -c | while read count type; do
                echo "- $type: $count notifikací"
            done
            
            # Analýza priorit
            echo
            echo "=== Priority notifikací ==="
            echo "$http_body" | jq -r '.notifications[] | .priority // "normal"' | sort | uniq -c | while read count priority; do
                echo "- $priority: $count notifikací"
            done
            
            # Nejnovější notifikace
            echo
            echo "=== Nejnovější notifikace ==="
            echo "$http_body" | jq -r '.notifications[0:5][] | "- " + (.title // "Bez názvu") + " [" + (.type // "neznámý") + "] (" + (.createdAt // "neznámé datum") + ")"'
            
            # Nepřečtené notifikace
            unread_notifications=$(echo "$http_body" | jq -r '[.notifications[] | select(.read == false)] | length')
            if [ "$unread_notifications" -gt 0 ]; then
                echo
                echo "=== Nepřečtené notifikace ==="
                echo "Počet nepřečtených: $unread_notifications"
                echo "$http_body" | jq -r '.notifications[] | select(.read == false) | "- " + (.title // "Bez názvu") + " [" + (.type // "neznámý") + "]"' | head -3
            fi
            
            # Statistiky podle času
            echo
            echo "=== Časové statistiky ==="
            today_count=$(echo "$http_body" | jq -r '[.notifications[] | select(.createdAt | startswith("'$(date +%Y-%m-%d)'"))] | length')
            echo "Dnes: $today_count notifikací"
            
            # Akční notifikace
            action_notifications=$(echo "$http_body" | jq -r '[.notifications[] | select(.actionRequired == true)] | length')
            if [ "$action_notifications" -gt 0 ]; then
                echo "Vyžadují akci: $action_notifications notifikací"
            fi
            
            # Skupiny notifikací
            if echo "$http_body" | jq -e '.notifications[0].category' >/dev/null 2>&1; then
                echo
                echo "=== Kategorie notifikací ==="
                echo "$http_body" | jq -r '.notifications[] | .category // "nezařazeno"' | sort | uniq -c | while read count category; do
                    echo "- $category: $count notifikací"
                done
            fi
        fi
        
        # Informace o stránkování
        if echo "$http_body" | jq -e '.pagination' >/dev/null 2>&1; then
            echo
            echo "=== Stránkování ==="
            current_page=$(echo "$http_body" | jq -r '.pagination.currentPage // 1')
            total_pages=$(echo "$http_body" | jq -r '.pagination.totalPages // 1')
            echo "Aktuální stránka: $current_page z $total_pages"
            
            if [ "$current_page" -lt "$total_pages" ]; then
                next_offset=$((count + ${NOTIFICATIONS_OFFSET:-0}))
                echo "💡 Pro další notifikace nastavte NOTIFICATIONS_OFFSET=$next_offset"
            fi
        fi
        
        # Doporučení pro správu notifikací
        echo
        echo "=== Doporučení pro správu ==="
        if [ "$unread_count" -gt 20 ]; then
            echo "⚠️  Máte mnoho nepřečtených notifikací ($unread_count)"
            echo "- Zvažte označení starších jako přečtené"
            echo "- Nastavte filtry pro důležité typy"
        elif [ "$unread_count" -gt 0 ]; then
            echo "📬 Máte $unread_count nepřečtených notifikací"
            echo "- Projděte si nejnovější notifikace"
        else
            echo "✅ Všechny notifikace jsou přečtené"
        fi
        
        # Tipy pro filtrování
        echo
        echo "=== Tipy pro filtrování ==="
        echo "- Použijte NOTIFICATIONS_TYPE pro konkrétní typ"
        echo "- Nastavte NOTIFICATIONS_READ=false pro nepřečtené"
        echo "- Využijte NOTIFICATIONS_SINCE pro novější notifikace"
        echo "- Kombinujte s NOTIFICATIONS_LIMIT pro stránkování"
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
    
    if [ "$http_status" -eq 400 ]; then
        echo "- Neplatné parametry (limit, offset, type, read, since)"
    elif [ "$http_status" -eq 401 ]; then
        echo "- Neplatný nebo chybějící API token"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění pro čtení notifikací"
    elif [ "$http_status" -eq 429 ]; then
        echo "- Příliš mnoho požadavků - zkuste později"
    fi
else
    echo
    echo "✓ Notifikace úspěšně načteny!"
    
    # Další akce
    echo
    echo "=== Další akce ==="
    echo "- Označte důležité notifikace jako přečtené"
    echo "- Použijte notifications_register.sh pro nastavení notifikací"
    echo "- Nastavte filtry pro lepší správu notifikací"
    echo "- Pravidelně kontrolujte nepřečtené notifikace"
fi

echo
echo "Tip: Pro registraci notifikací použijte notifications_register.sh"
