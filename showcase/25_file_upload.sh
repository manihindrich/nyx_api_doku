#!/bin/bash

# NYX.CZ API - Nahrání souboru
# PUT /api/file/upload

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

# Kontrola cesty k souboru
if [ -z "$FILE_PATH" ]; then
    echo "Chyba: Nastavte FILE_PATH v secret.txt"
    echo "Příklad: FILE_PATH=/path/to/your/file.jpg"
    exit 1
fi

# Kontrola existence souboru
if [ ! -f "$FILE_PATH" ]; then
    echo "Chyba: Soubor '$FILE_PATH' neexistuje!"
    exit 1
fi

# Získání informací o souboru
file_name=$(basename "$FILE_PATH")
file_size=$(stat -c%s "$FILE_PATH" 2>/dev/null || stat -f%z "$FILE_PATH" 2>/dev/null)
file_type=$(file -b --mime-type "$FILE_PATH" 2>/dev/null || echo "application/octet-stream")

echo "=== NYX.CZ API - Nahrání souboru ==="
echo "URL: ${NYX_API_BASE_URL}/file/upload"
echo "Soubor: $file_name"
echo "Velikost: $file_size bytů"
echo "MIME typ: $file_type"
echo

# Varování před nahráním
echo "⚠️  VAROVÁNÍ: Nahráváte soubor na server!"
echo "Soubor: $FILE_PATH"
echo "Pokračovat? (y/N)"
read -r confirmation
if [[ ! "$confirmation" =~ ^[Yy]$ ]]; then
    echo "Operace zrušena."
    exit 0
fi

# Příprava dodatečných parametrů
upload_params=""

if [ -n "$FILE_DESCRIPTION" ]; then
    upload_params="$upload_params -F description=\"$FILE_DESCRIPTION\""
fi

if [ -n "$FILE_CATEGORY" ]; then
    upload_params="$upload_params -F category=\"$FILE_CATEGORY\""
fi

if [ -n "$FILE_TAGS" ]; then
    upload_params="$upload_params -F tags=\"$FILE_TAGS\""
fi

if [ -n "$FILE_PUBLIC" ]; then
    upload_params="$upload_params -F public=\"$FILE_PUBLIC\""
fi

# API požadavek
echo "Nahrávání souboru..."
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X PUT \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    -F "file=@$FILE_PATH" \
    $upload_params \
    "${NYX_API_BASE_URL}/file/upload")

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
        echo "=== Analýza nahraného souboru ==="
        
        # Základní informace
        file_id=$(echo "$http_body" | jq -r '.id // .fileId // "neznámé"')
        uploaded_name=$(echo "$http_body" | jq -r '.filename // .name // "neznámý"')
        uploaded_size=$(echo "$http_body" | jq -r '.size // "neznámá"')
        uploaded_url=$(echo "$http_body" | jq -r '.url // .downloadUrl // "neznámá"')
        
        echo "ID souboru: $file_id"
        echo "Název: $uploaded_name"
        echo "Velikost: $uploaded_size bytů"
        
        if [ "$uploaded_url" != "null" ] && [ "$uploaded_url" != "neznámá" ]; then
            echo "URL: $uploaded_url"
        fi
        
        # Metadata
        mime_type=$(echo "$http_body" | jq -r '.mimeType // .contentType // "neznámý"')
        upload_date=$(echo "$http_body" | jq -r '.uploadedAt // .createdAt // "neznámé"')
        
        echo "MIME typ: $mime_type"
        if [ "$upload_date" != "null" ] && [ "$upload_date" != "neznámé" ]; then
            echo "Datum nahrání: $upload_date"
        fi
        
        # Kontrola integrity
        if [ "$uploaded_size" != "null" ] && [ "$uploaded_size" != "neznámá" ]; then
            if [ "$uploaded_size" -eq "$file_size" ]; then
                echo "✓ Velikost souboru se shoduje"
            else
                echo "⚠️  Velikost souboru se neshoduje! (místní: $file_size, server: $uploaded_size)"
            fi
        fi
        
        # Bezpečnostní informace
        echo
        echo "=== Bezpečnostní informace ==="
        is_public=$(echo "$http_body" | jq -r '.public // .isPublic // "neznámé"')
        if [ "$is_public" = "true" ]; then
            echo "🔓 Soubor je veřejně přístupný"
        elif [ "$is_public" = "false" ]; then
            echo "🔒 Soubor je privátní"
        fi
        
        # Doporučení podle typu souboru
        echo
        echo "=== Doporučení ==="
        case "$file_type" in
            image/*)
                echo "- Obrázek nahrán - zvažte optimalizaci velikosti"
                echo "- Zkontrolujte rozlišení a kvalitu"
                ;;
            video/*)
                echo "- Video nahrán - může trvat zpracování"
                echo "- Zkontrolujte formát a kompresi"
                ;;
            application/pdf)
                echo "- PDF dokument nahrán"
                echo "- Ověřte čitelnost a velikost"
                ;;
            text/*)
                echo "- Textový soubor nahrán"
                echo "- Zkontrolujte kódování znaků"
                ;;
            *)
                echo "- Soubor nahrán úspěšně"
                echo "- Ověřte kompatibilitu s cílovým systémem"
                ;;
        esac
    fi
else
    echo "$http_body"
    echo
    echo "Tip: Nainstalujte 'jq' pro lepší formátování JSON: sudo apt install jq"
fi

# Kontrola chyb
if [ "$http_status" -ne 200 ] && [ "$http_status" -ne 201 ]; then
    echo
    echo "Chyba při nahrávání! Zkontrolujte:"
    echo "- API token v secret.txt"
    echo "- FILE_PATH v secret.txt"
    echo "- Existenci a čitelnost souboru"
    
    if [ "$http_status" -eq 400 ]; then
        echo "- Neplatný formát souboru nebo parametrů"
        echo "- Velikost souboru (možná příliš velký)"
    elif [ "$http_status" -eq 401 ]; then
        echo "- Neplatný nebo chybějící API token"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění pro nahrávání"
    elif [ "$http_status" -eq 413 ]; then
        echo "- Soubor je příliš velký"
    elif [ "$http_status" -eq 415 ]; then
        echo "- Nepodporovaný typ souboru"
    elif [ "$http_status" -eq 507 ]; then
        echo "- Nedostatek místa na serveru"
    fi
else
    echo
    echo "✓ Soubor byl úspěšně nahrán!"
    
    # Statistiky nahrávání
    echo
    echo "=== Statistiky nahrávání ==="
    echo "- Místní soubor: $FILE_PATH"
    echo "- Velikost: $file_size bytů"
    echo "- MIME typ: $file_type"
    echo "- Čas nahrání: $(date)"
    
    # Další kroky
    echo
    echo "=== Další kroky ==="
    echo "- Použijte file_delete.sh pro smazání souboru"
    echo "- Použijte file_embed.sh pro vložení do obsahu"
    echo "- Zkontrolujte dostupnost přes URL (pokud je veřejný)"
fi

echo
echo "Tip: Pro správu souborů použijte file_delete.sh nebo file_embed.sh"
