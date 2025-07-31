#!/bin/bash

# NYX.CZ API - Úprava položky na nástěnce
# POST /api/discussion/{discussionId}/content/{contentId}/save

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

if [ -z "$CONTENT_ID" ] || [ "$CONTENT_ID" = "67890" ]; then
    echo "Chyba: Nastavte CONTENT_ID v secret.txt"
    echo "Příklad: CONTENT_ID=789012"
    exit 1
fi

if [ -z "$CONTENT_TEXT" ]; then
    echo "Chyba: Nastavte CONTENT_TEXT v secret.txt"
    echo "Příklad: CONTENT_TEXT='Upravený obsah nástěnky'"
    exit 1
fi

echo "=== NYX.CZ API - Úprava položky na nástěnce ==="
echo "URL: ${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/content/${CONTENT_ID}/save"
echo "Diskuze ID: $DISCUSSION_ID"
echo "Obsah ID: $CONTENT_ID"
echo "Obsah: $CONTENT_TEXT"
echo

# Příprava dat pro POST
post_data="content=$(echo "$CONTENT_TEXT" | sed 's/ /%20/g' | sed 's/&/%26/g')"

# Přidání formátu pokud je nastaven
if [ -n "$CONTENT_FORMAT" ]; then
    post_data="${post_data}&format=${CONTENT_FORMAT}"
    echo "Formát: $CONTENT_FORMAT"
fi

echo

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "$post_data" \
    "${NYX_API_BASE_URL}/discussion/${DISCUSSION_ID}/content/${CONTENT_ID}/save")

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
        echo "=== Analýza úpravy obsahu ==="
        
        # Základní informace o úpravě
        content_id=$(echo "$http_body" | jq -r '.content_id // .id // "neznámé"')
        updated_at=$(echo "$http_body" | jq -r '.updated_at // .modified_at // "neznámé"')
        version=$(echo "$http_body" | jq -r '.version // "neznámá"')
        
        echo "ID obsahu: $content_id"
        echo "Aktualizováno: $updated_at"
        echo "Verze: $version"
        
        # Informace o obsahu
        if echo "$http_body" | jq -e '.content' >/dev/null 2>&1; then
            echo
            echo "=== Informace o obsahu ==="
            
            content_length=$(echo "$http_body" | jq -r '.content | length')
            content_format=$(echo "$http_body" | jq -r '.format // "text"')
            
            echo "Délka obsahu: $content_length znaků"
            echo "Formát: $content_format"
            
            # Náhled obsahu
            content_preview=$(echo "$http_body" | jq -r '.content' | head -c 100)
            echo "Náhled: ${content_preview}..."
        fi
        
        # Historie změn
        if echo "$http_body" | jq -e '.revision_info' >/dev/null 2>&1; then
            echo
            echo "=== Historie změn ==="
            
            revision_number=$(echo "$http_body" | jq -r '.revision_info.number // 1')
            previous_version=$(echo "$http_body" | jq -r '.revision_info.previous_version // "žádná"')
            editor=$(echo "$http_body" | jq -r '.revision_info.editor // "neznámý"')
            
            echo "Číslo revize: $revision_number"
            echo "Předchozí verze: $previous_version"
            echo "Editor: $editor"
        fi
        
        # Statistiky úprav
        if echo "$http_body" | jq -e '.edit_stats' >/dev/null 2>&1; then
            echo
            echo "=== Statistiky úprav ==="
            
            chars_added=$(echo "$http_body" | jq -r '.edit_stats.chars_added // 0')
            chars_removed=$(echo "$http_body" | jq -r '.edit_stats.chars_removed // 0')
            lines_changed=$(echo "$http_body" | jq -r '.edit_stats.lines_changed // 0')
            
            echo "Přidáno znaků: $chars_added"
            echo "Odebráno znaků: $chars_removed"
            echo "Změněno řádků: $lines_changed"
            
            # Typ změny
            if [ "$chars_added" -gt "$chars_removed" ]; then
                echo "Typ změny: Rozšíření obsahu"
            elif [ "$chars_removed" -gt "$chars_added" ]; then
                echo "Typ změny: Zkrácení obsahu"
            else
                echo "Typ změny: Úprava obsahu"
            fi
        fi
        
        # Oprávnění a omezení
        if echo "$http_body" | jq -e '.permissions' >/dev/null 2>&1; then
            echo
            echo "=== Oprávnění ==="
            
            can_edit=$(echo "$http_body" | jq -r '.permissions.can_edit // false')
            can_delete=$(echo "$http_body" | jq -r '.permissions.can_delete // false')
            can_restore=$(echo "$http_body" | jq -r '.permissions.can_restore // false')
            
            echo "Může upravovat: $can_edit"
            echo "Může mazat: $can_delete"
            echo "Může obnovit: $can_restore"
        fi
        
        # Validace obsahu
        if echo "$http_body" | jq -e '.validation' >/dev/null 2>&1; then
            echo
            echo "=== Validace obsahu ==="
            
            is_valid=$(echo "$http_body" | jq -r '.validation.is_valid // true')
            warnings=$(echo "$http_body" | jq -r '.validation.warnings[]?' 2>/dev/null)
            
            if [ "$is_valid" = "true" ]; then
                echo "✅ Obsah je validní"
            else
                echo "⚠️ Obsah má problémy"
            fi
            
            if [ -n "$warnings" ]; then
                echo "Varování:"
                echo "$warnings" | while read warning; do
                    echo "  - $warning"
                done
            fi
        fi
        
        # Doporučení pro další úpravy
        echo
        echo "=== Doporučení ==="
        echo "- Zkontrolujte zobrazení obsahu v diskuzi"
        echo "- Ověřte formátování a odkazy"
        echo "- Zvažte přidání dalších informací"
        echo "- Sledujte reakce ostatních uživatelů"
        
        # Tipy pro správu obsahu
        echo
        echo "=== Tipy pro správu obsahu ==="
        echo "- Používejte jasné a srozumitelné formátování"
        echo "- Pravidelně aktualizujte zastaralé informace"
        echo "- Přidávejte relevantní odkazy a zdroje"
        echo "- Udržujte obsah aktuální a užitečný"
        
        # Další akce
        echo
        echo "=== Další akce ==="
        echo "- Zobrazit diskuzi: discussion_get.sh"
        echo "- Zkontrolovat oprávnění: discussion_access_rights_get.sh"
        echo "- Přidat do bookmarků: discussion_bookmark.sh"
        echo "- Sledovat reakce na změny"
    fi
else
    echo "$http_body"
    echo
    echo "Tip: Nainstalujte 'jq' pro lepší formátování JSON: sudo apt install jq"
fi

# Kontrola chyb
if [ "$http_status" -ne 200 ]; then
    echo
    echo "Chyba při úpravě obsahu! Zkontrolujte:"
    echo "- API token v secret.txt"
    echo "- DISCUSSION_ID v secret.txt"
    echo "- CONTENT_ID v secret.txt"
    echo "- CONTENT_TEXT v secret.txt"
    
    if [ "$http_status" -eq 400 ]; then
        echo "- Neplatné ID diskuze nebo obsahu"
        echo "- Neplatný formát obsahu"
        echo "- Chybějící povinné parametry"
    elif [ "$http_status" -eq 401 ]; then
        echo "- Neplatný nebo chybějící API token"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění pro úpravu obsahu"
        echo "- Obsah může být uzamčen"
    elif [ "$http_status" -eq 404 ]; then
        echo "- Diskuze nebo obsah neexistuje"
    elif [ "$http_status" -eq 413 ]; then
        echo "- Obsah je příliš dlouhý"
    elif [ "$http_status" -eq 422 ]; then
        echo "- Neplatný obsah nebo formát"
    fi
else
    echo
    echo "✅ Obsah byl úspěšně upraven!"
    
    # Další kroky
    echo
    echo "=== Další kroky ==="
    echo "1. Zkontrolujte zobrazení v diskuzi"
    echo "2. Ověřte správnost formátování"
    echo "3. Sledujte reakce ostatních uživatelů"
    echo "4. Zvažte další úpravy podle potřeby"
    
    # Bezpečnostní tipy
    echo
    echo "=== Bezpečnostní tipy ==="
    echo "- Zálohujte důležitý obsah před úpravami"
    echo "- Používejte pouze důvěryhodné zdroje"
    echo "- Ověřujte odkazy před jejich přidáním"
    echo "- Respektujte autorská práva"
fi

echo
echo "Tip: Pro zobrazení diskuze použijte discussion_get.sh"
