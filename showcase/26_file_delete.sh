#!/bin/bash

# NYX.CZ API - Smazání souboru
# DELETE /api/file/delete/{id}

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

echo "=== NYX.CZ API - Smazání souboru ==="
echo "URL: ${NYX_API_BASE_URL}/file/delete/${FILE_ID}"
echo "ID souboru: $FILE_ID"
echo

# Varování před smazáním
echo "⚠️  VAROVÁNÍ: Chystáte se TRVALE smazat soubor!"
echo "ID souboru: $FILE_ID"
echo "Tato operace je NEVRATNÁ!"
echo "Pokračovat? (y/N)"
read -r confirmation
if [[ ! "$confirmation" =~ ^[Yy]$ ]]; then
    echo "Operace zrušena."
    exit 0
fi

# API požadavek
echo "Mazání souboru..."
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X DELETE \
    -H "Authorization: Bearer $NYX_API_TOKEN" \
    "${NYX_API_BASE_URL}/file/delete/${FILE_ID}")

# Rozdělení odpovědi a status kódu
http_body=$(echo "$response" | sed '$d')
http_status=$(echo "$response" | tail -n1 | sed 's/HTTP_STATUS://')

echo "HTTP Status: $http_status"
echo

# Formátování JSON výstupu
if command -v jq >/dev/null 2>&1; then
    echo "$http_body" | jq '.'
    
    # Dodatečné analýzy s jq
    if [ "$http_status" -eq 200 ] || [ "$http_status" -eq 204 ]; then
        echo
        echo "=== Analýza smazání souboru ==="
        
        # Informace o smazaném souboru
        deleted_id=$(echo "$http_body" | jq -r '.id // .fileId // "neznámé"')
        deleted_name=$(echo "$http_body" | jq -r '.filename // .name // "neznámý"')
        deletion_time=$(echo "$http_body" | jq -r '.deletedAt // "neznámé"')
        
        if [ "$deleted_id" != "null" ] && [ "$deleted_id" != "neznámé" ]; then
            echo "Smazané ID: $deleted_id"
        fi
        
        if [ "$deleted_name" != "null" ] && [ "$deleted_name" != "neznámý" ]; then
            echo "Smazaný soubor: $deleted_name"
        fi
        
        if [ "$deletion_time" != "null" ] && [ "$deletion_time" != "neznámé" ]; then
            echo "Čas smazání: $deletion_time"
        fi
        
        # Kontrola souvisejících dat
        echo
        echo "=== Kontrola souvisejících dat ==="
        
        # Odkazy a reference
        references=$(echo "$http_body" | jq -r '.references // 0')
        if [ "$references" != "null" ] && [ "$references" -gt 0 ]; then
            echo "⚠️  Soubor měl $references odkazů - mohou být poškozeny"
        else
            echo "✓ Žádné známé odkazy na soubor"
        fi
        
        # Embedded použití
        embedded_count=$(echo "$http_body" | jq -r '.embeddedIn // 0')
        if [ "$embedded_count" != "null" ] && [ "$embedded_count" -gt 0 ]; then
            echo "⚠️  Soubor byl vložen do $embedded_count obsahů"
        fi
        
        # Backup informace
        backup_available=$(echo "$http_body" | jq -r '.backupAvailable // false')
        if [ "$backup_available" = "true" ]; then
            echo "💾 Backup souboru je k dispozici"
            backup_until=$(echo "$http_body" | jq -r '.backupUntil // "neznámé"')
            if [ "$backup_until" != "null" ] && [ "$backup_until" != "neznámé" ]; then
                echo "   Backup dostupný do: $backup_until"
            fi
        fi
    fi
else
    echo "$http_body"
    echo
    echo "Tip: Nainstalujte 'jq' pro lepší formátování JSON: sudo apt install jq"
fi

# Kontrola chyb
if [ "$http_status" -ne 200 ] && [ "$http_status" -ne 204 ]; then
    echo
    echo "Chyba při mazání! Zkontrolujte:"
    echo "- API token v secret.txt"
    echo "- FILE_ID v secret.txt"
    echo "- Existenci souboru s daným ID"
    
    if [ "$http_status" -eq 400 ]; then
        echo "- Neplatné ID souboru"
    elif [ "$http_status" -eq 401 ]; then
        echo "- Neplatný nebo chybějící API token"
    elif [ "$http_status" -eq 403 ]; then
        echo "- Nedostatečná oprávnění pro smazání"
        echo "- Soubor může být chráněný proti smazání"
    elif [ "$http_status" -eq 404 ]; then
        echo "- Soubor s ID '$FILE_ID' neexistuje"
        echo "- Soubor již byl smazán"
    elif [ "$http_status" -eq 409 ]; then
        echo "- Soubor je používán a nelze jej smazat"
        echo "- Odstraňte nejprve všechny odkazy na soubor"
    fi
else
    echo
    echo "✓ Soubor byl úspěšně smazán!"
    
    # Doporučení po smazání
    echo
    echo "=== Doporučení po smazání ==="
    echo "- Zkontrolujte obsahy, které mohly odkazovat na soubor"
    echo "- Ověřte, že se nepoškodily žádné stránky nebo příspěvky"
    echo "- Zvažte aktualizaci odkazů na alternativní soubory"
    echo "- Zkontrolujte logy pro případné chyby 404"
    
    # Bezpečnostní tipy
    echo
    echo "=== Bezpečnostní tipy ==="
    echo "- Soubor je trvale smazán a nelze jej obnovit"
    echo "- Ujistěte se, že máte zálohu důležitých souborů"
    echo "- Používejte file_embed.sh pro kontrolu použití před smazáním"
    echo "- Zvažte deaktivaci místo smazání u důležitých souborů"
fi

echo
echo "Tip: Pro nahrání nového souboru použijte file_upload.sh"
