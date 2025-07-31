#!/bin/bash

# NYX.CZ API - Vložení/odebrání souboru do obsahu
# POST /api/file/embed/{id}/{state}

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

# Kontrola ID souboru
if [ -z "$FILE_ID" ]; then
    echo "Chyba: Nastavte FILE_ID v secret.txt"
    echo "Příklad: FILE_ID=12345"
    exit 1
fi

# Kontrola stavu vložení
if [ -z "$FILE_EMBED_STATE" ]; then
    echo "Chyba: Nastavte FILE_EMBED_STATE v secret.txt"
    echo "Možné hodnoty: embed, remove, toggle"
    exit 1
fi

# Validace stavu
case "$FILE_EMBED_STATE" in
    embed|remove|toggle)
        ;;
    *)
        echo "Chyba: Neplatný FILE_EMBED_STATE '$FILE_EMBED_STATE'"
        echo "Povolené hodnoty: embed, remove, toggle"
        exit 1
        ;;
esac

echo "=== NYX.CZ API - Vložení/odebrání souboru ==="
echo "URL: ${NYX_API_BASE_URL}/file/embed/${FILE_ID}/${FILE_EMBED_STATE}"
echo "ID souboru: $FILE_ID"
echo "Akce: $FILE_EMBED_STATE"
echo

# Příprava dat pro POST
post_data="{}"

# Přidání volitelných parametrů
if [ -n "$FILE_CONTENT_ID" ]; then
    post_data=$(echo "$post_data" | jq --arg content_id "$FILE_CONTENT_ID" '. + {contentId: $content_id}')
fi

if [ -n "$FILE_POSITION" ]; then
    post_data=$(echo "$post_data" | jq --arg position "$FILE_POSITION" '. + {position: $position}')
fi

if [ -n "$FILE_CAPTION" ]; then
    post_data=$(echo "$post_data" | jq --arg caption "$FILE_CAPTION" '. + {caption: $caption}')
fi

if [ -n "$FILE_ALT_TEXT" ]; then
    post_data=$(echo "$post_data" | jq --arg alt_text "$FILE_ALT_TEXT" '. + {altText: $alt_text}')
fi

# Zobrazení akce
case "$FILE_EMBED_STATE" in
    embed)
        echo "📎 Vkládání souboru do obsahu..."
        ;;
    remove)
        echo "🗑️  Odebírání souboru z obsahu..."
        ;;
    toggle)
        echo "🔄 Přepínání stavu vložení souboru..."
        ;;
esac

# API požadavek
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$post_data" \
    "${NYX_API_BASE_URL}/file/embed/${FILE_ID}/${FILE_EMBED_STATE}")

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
        echo "=== Analýza vložení souboru ==="
        
        # Základní informace
        file_id=$(echo "$http_body" | jq -r '.fileId // .id // "neznámé"')
        file_name=$(echo "$http_body" | jq -r '.filename // .name // "neznámý"')
        embed_status=$(echo "$http_body" | jq -r '.embedded // .isEmbedded // "neznámé"')
        
        echo "ID souboru: $file_id"
        echo "Název souboru: $file_name"
        
        # Stav vložení
        if [ "$embed_status" = "true" ]; then
            echo "✅ Soubor je vložen do obsahu"
        elif [ "$embed_status" = "false" ]; then
            echo "❌ Soubor není vložen do obsahu"
        fi
        
        # Informace o vložení
        content_id=$(echo "$http_body" | jq -r '.contentId // "neznámé"')
        position=$(echo "$http_body" | jq -r '.position // "neznámé"')
        embed_type=$(echo "$http_body" | jq -r '.embedType // "neznámý"')
        
        if [ "$content_id" != "null" ] && [ "$content_id" != "neznámé" ]; then
            echo "ID obsahu: $content_id"
        fi
        
        if [ "$position" != "null" ] && [ "$position" != "neznámé" ]; then
            echo "Pozice: $position"
        fi
        
        if [ "$embed_type" != "null" ] && [ "$embed_type" != "neznámý" ]; then
            echo "Typ vložení: $embed_type"
        fi
        
        # Metadata vložení
        echo
        echo "=== Metadata vložení ==="
        
        caption=$(echo "$http_body" | jq -r '.caption // "žádný"')
        alt_text=$(echo "$http_body" | jq -r '.altText // "žádný"')
        embed_date=$(echo "$http_body" | jq -r '.embeddedAt // .createdAt // "neznámé"')
        
        echo "Popisek: $caption"
        echo "Alt text: $alt_text"
        
        if [ "$embed_date" != "null" ] && [ "$embed_date" != "neznámé" ]; then
            echo "Datum vložení: $embed_date"
        fi
        
        # Statistiky použití
        usage_count=$(echo "$http_body" | jq -r '.usageCount // 0')
        total_embeds=$(echo "$http_body" | jq -r '.totalEmbeds // 0')
        
        if [ "$usage_count" -gt 0 ]; then
            echo
            echo "=== Statistiky použití ==="
            echo "Počet použití: $usage_count"
            echo "Celkem vložení: $total_embeds"
        fi
        
        # Seznam obsahů s vložením
        if echo "$http_body" | jq -e '.embeddedIn' >/dev/null 2>&1; then
            echo
            echo "=== Obsahy s vložením ==="
            echo "$http_body" | jq -r '.embeddedIn[]? | "- " + (.title // "Bez názvu") + " (ID: " + (.id // "neznámé" | tostring) + ")"' | head -5
            
            embed_count=$(echo "$http_body" | jq -r '.embeddedIn | length')
            if [ "$embed_count" -gt 5 ]; then
                echo "... a dalších $((embed_count - 5)) obsahů"
            fi
        fi
        
        # Doporučení podle typu souboru
        file_type=$(echo "$http_body" | jq -r '.mimeType // .contentType // "neznámý"')
        echo
        echo "=== Doporučení pro typ souboru ==="
        
        case "$file_type" in
            image/*)
                echo "🖼️  Obrázek:"
                echo "- Zkontrolujte rozlišení a velikost"
                echo "- Nastavte vhodný alt text pro přístupnost"
                echo "- Zvažte responzivní zobrazení"
                ;;
            video/*)
                echo "🎬 Video:"
                echo "- Ověřte kompatibilitu s různými prohlížeči"
                echo "- Nastavte náhledový obrázek"
                echo "- Zvažte titulky pro přístupnost"
                ;;
            audio/*)
                echo "🎵 Audio:"
                echo "- Poskytněte ovládací prvky"
                echo "- Zvažte transkript pro přístupnost"
                ;;
            application/pdf)
                echo "📄 PDF dokument:"
                echo "- Ověřte čitelnost na mobilních zařízeních"
                echo "- Zvažte alternativní formáty"
                ;;
            *)
                echo "📁 Obecný soubor:"
                echo "- Ověřte správné zobrazení odkazu"
                echo "- Nastavte popisný text"
                ;;
        esac
    fi
else
    echo "$http_body"
    echo
    echo "Tip: Nainstalujte 'jq' pro lepší formátování JSON: sudo apt install jq"
fi

# Kontrola chyb
if [ "$http_status" -ne 200 ]; then
    echo
    echo "Chyba při operaci! Zkontrolujte:"
    echo "- API token v secret.txt"
    echo "- FILE_ID v secret.txt"
    echo "- FILE_EMBED_STATE v secret.txt"
    
    if [ "$http_status" -eq 400 ]; then
        echo "- Neplatné ID souboru nebo stav"
        echo "- Neplatné parametry (contentId, position)"
    elif [ "$http_status" -eq 401 ]; then
        echo "- Neplatný nebo chybějící API token"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění pro úpravu"
    elif [ "$http_status" -eq 404 ]; then
        echo "- Soubor s ID '$FILE_ID' neexistuje"
        echo "- Obsah s daným ID neexistuje"
    elif [ "$http_status" -eq 409 ]; then
        echo "- Konflikt při vkládání (soubor již vložen)"
        echo "- Neplatná pozice v obsahu"
    fi
else
    echo
    case "$FILE_EMBED_STATE" in
        embed)
            echo "✅ Soubor byl úspěšně vložen do obsahu!"
            ;;
        remove)
            echo "✅ Soubor byl úspěšně odebrán z obsahu!"
            ;;
        toggle)
            echo "✅ Stav vložení souboru byl úspěšně přepnut!"
            ;;
    esac
    
    # Další kroky
    echo
    echo "=== Další kroky ==="
    echo "- Zkontrolujte zobrazení v cílovém obsahu"
    echo "- Ověřte funkčnost na různých zařízeních"
    echo "- Otestujte přístupnost (alt text, titulky)"
    echo "- Použijte file_delete.sh pro smazání nepotřebných souborů"
fi

echo
echo "Tip: Pro správu souborů použijte file_upload.sh nebo file_delete.sh"
