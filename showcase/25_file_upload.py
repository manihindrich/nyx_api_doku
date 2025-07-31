#!/usr/bin/env python3
"""
NYX.CZ API - Nahrání souboru
PUT /api/file/upload
"""

import requests
import json
import sys
import os
import mimetypes
from pathlib import Path
from datetime import datetime

def load_config():
    """Načte konfiguraci ze secret.txt"""
    config = {}
    try:
        with open('secret.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    except FileNotFoundError:
        print("Chyba: Soubor secret.txt nenalezen!")
        print("Zkopírujte dummy-secret.txt jako secret.txt a vyplňte hodnoty.")
        sys.exit(1)
    return config

def analyze_file(file_path):
    """Analyzuje soubor před nahráním"""
    file_info = {
        'path': file_path,
        'name': os.path.basename(file_path),
        'size': 0,
        'mime_type': 'application/octet-stream',
        'extension': '',
        'category': 'other',
        'is_safe': True,
        'recommendations': []
    }
    
    try:
        # Základní informace
        stat = os.stat(file_path)
        file_info['size'] = stat.st_size
        file_info['modified'] = datetime.fromtimestamp(stat.st_mtime)
        
        # MIME typ
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            file_info['mime_type'] = mime_type
        
        # Přípona
        file_info['extension'] = Path(file_path).suffix.lower()
        
        # Kategorie podle MIME typu
        if file_info['mime_type'].startswith('image/'):
            file_info['category'] = 'image'
        elif file_info['mime_type'].startswith('video/'):
            file_info['category'] = 'video'
        elif file_info['mime_type'].startswith('audio/'):
            file_info['category'] = 'audio'
        elif file_info['mime_type'].startswith('text/'):
            file_info['category'] = 'text'
        elif file_info['mime_type'] == 'application/pdf':
            file_info['category'] = 'document'
        elif file_info['mime_type'].startswith('application/'):
            file_info['category'] = 'application'
        
        # Bezpečnostní kontroly
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com']
        if file_info['extension'] in dangerous_extensions:
            file_info['is_safe'] = False
            file_info['recommendations'].append("⚠️ Potenciálně nebezpečný typ souboru")
        
        # Doporučení podle velikosti
        size_mb = file_info['size'] / (1024 * 1024)
        if size_mb > 100:
            file_info['recommendations'].append(f"📦 Velký soubor ({size_mb:.1f} MB) - zvažte kompresi")
        elif size_mb > 10 and file_info['category'] == 'image':
            file_info['recommendations'].append(f"🖼️ Velký obrázek ({size_mb:.1f} MB) - zvažte optimalizaci")
        
        # Doporučení podle typu
        if file_info['category'] == 'image':
            file_info['recommendations'].append("🎨 Zkontrolujte rozlišení a kvalitu obrázku")
        elif file_info['category'] == 'video':
            file_info['recommendations'].append("🎬 Video může vyžadovat delší zpracování")
        elif file_info['category'] == 'document':
            file_info['recommendations'].append("📄 Ověřte čitelnost dokumentu")
        
    except OSError as e:
        print(f"Chyba při analýze souboru: {e}")
        sys.exit(1)
    
    return file_info

def format_file_size(size_bytes):
    """Formátuje velikost souboru do čitelného formátu"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def main():
    # Načtení konfigurace
    config = load_config()
    
    # Kontrola API tokenu
    api_token = config.get('NYX_API_TOKEN')
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    # Kontrola cesty k souboru
    file_path = config.get('FILE_PATH')
    if not file_path:
        print("Chyba: Nastavte FILE_PATH v secret.txt")
        print("Příklad: FILE_PATH=/path/to/your/file.jpg")
        sys.exit(1)
    
    # Kontrola existence souboru
    if not os.path.isfile(file_path):
        print(f"Chyba: Soubor '{file_path}' neexistuje!")
        sys.exit(1)
    
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    
    # Analýza souboru
    file_info = analyze_file(file_path)
    
    print("=== NYX.CZ API - Nahrání souboru ===")
    print(f"URL: {base_url}/file/upload")
    print(f"Soubor: {file_info['name']}")
    print(f"Velikost: {format_file_size(file_info['size'])}")
    print(f"MIME typ: {file_info['mime_type']}")
    print(f"Kategorie: {file_info['category']}")
    print()
    
    # Zobrazení doporučení
    if file_info['recommendations']:
        print("=== Doporučení před nahráním ===")
        for rec in file_info['recommendations']:
            print(rec)
        print()
    
    # Bezpečnostní varování
    if not file_info['is_safe']:
        print("🚨 BEZPEČNOSTNÍ VAROVÁNÍ: Soubor může být nebezpečný!")
        print()
    
    # Varování před nahráním
    print("⚠️  VAROVÁNÍ: Nahráváte soubor na server!")
    print(f"Soubor: {file_path}")
    confirmation = input("Pokračovat? (y/N): ").strip().lower()
    if confirmation not in ['y', 'yes']:
        print("Operace zrušena.")
        sys.exit(0)
    
    # Příprava požadavku
    url = f"{base_url}/file/upload"
    headers = {
        'Authorization': f'Bearer {api_token}'
    }
    
    # Příprava souborů a dat
    files = {
        'file': (file_info['name'], open(file_path, 'rb'), file_info['mime_type'])
    }
    
    data = {}
    
    # Přidání volitelných parametrů
    if config.get('FILE_DESCRIPTION'):
        data['description'] = config.get('FILE_DESCRIPTION')
    
    if config.get('FILE_CATEGORY'):
        data['category'] = config.get('FILE_CATEGORY')
    
    if config.get('FILE_TAGS'):
        data['tags'] = config.get('FILE_TAGS')
    
    if config.get('FILE_PUBLIC'):
        data['public'] = config.get('FILE_PUBLIC')
    
    try:
        print("Nahrávání souboru...")
        
        # API požadavek
        response = requests.put(url, headers=headers, files=files, data=data)
        
        # Zavření souboru
        files['file'][1].close()
        
        print(f"HTTP Status: {response.status_code}")
        print()
        
        # Výpis odpovědi
        if response.text:
            try:
                response_data = response.json()
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
                
                # Dodatečné analýzy
                if response.status_code in [200, 201]:
                    print()
                    print("=== Analýza nahraného souboru ===")
                    
                    # Základní informace
                    file_id = response_data.get('id', response_data.get('fileId', 'neznámé'))
                    uploaded_name = response_data.get('filename', response_data.get('name', 'neznámý'))
                    uploaded_size = response_data.get('size', 'neznámá')
                    uploaded_url = response_data.get('url', response_data.get('downloadUrl'))
                    
                    print(f"ID souboru: {file_id}")
                    print(f"Název: {uploaded_name}")
                    
                    if uploaded_size != 'neznámá':
                        print(f"Velikost: {format_file_size(int(uploaded_size))}")
                    
                    if uploaded_url:
                        print(f"URL: {uploaded_url}")
                    
                    # Metadata
                    mime_type = response_data.get('mimeType', response_data.get('contentType', 'neznámý'))
                    upload_date = response_data.get('uploadedAt', response_data.get('createdAt'))
                    
                    print(f"MIME typ: {mime_type}")
                    if upload_date:
                        print(f"Datum nahrání: {upload_date}")
                    
                    # Kontrola integrity
                    if uploaded_size != 'neznámá':
                        if int(uploaded_size) == file_info['size']:
                            print("✓ Velikost souboru se shoduje")
                        else:
                            print(f"⚠️ Velikost souboru se neshoduje! (místní: {file_info['size']}, server: {uploaded_size})")
                    
                    # Bezpečnostní informace
                    print()
                    print("=== Bezpečnostní informace ===")
                    is_public = response_data.get('public', response_data.get('isPublic'))
                    if is_public is True:
                        print("🔓 Soubor je veřejně přístupný")
                    elif is_public is False:
                        print("🔒 Soubor je privátní")
                    
                    # Doporučení podle kategorie
                    print()
                    print("=== Doporučení po nahrání ===")
                    category_tips = {
                        'image': [
                            "🖼️ Zkontrolujte kvalitu a rozlišení obrázku",
                            "🎨 Ověřte správné zobrazení v různých prohlížečích"
                        ],
                        'video': [
                            "🎬 Video může vyžadovat čas na zpracování",
                            "📱 Zkontrolujte kompatibilitu s mobilními zařízeními"
                        ],
                        'document': [
                            "📄 Ověřte čitelnost a formátování dokumentu",
                            "🔍 Zkontrolujte, zda jsou všechny stránky správně"
                        ],
                        'audio': [
                            "🎵 Zkontrolujte kvalitu zvuku",
                            "🔊 Ověřte kompatibilitu s různými přehrávači"
                        ]
                    }
                    
                    tips = category_tips.get(file_info['category'], [
                        "📁 Soubor byl úspěšně nahrán",
                        "✅ Ověřte funkčnost v cílovém prostředí"
                    ])
                    
                    for tip in tips:
                        print(tip)
                    
                    # Statistiky nahrávání
                    print()
                    print("=== Statistiky nahrávání ===")
                    print(f"Místní soubor: {file_path}")
                    print(f"Velikost: {format_file_size(file_info['size'])}")
                    print(f"MIME typ: {file_info['mime_type']}")
                    print(f"Čas nahrání: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Další kroky
                    print()
                    print("=== Další kroky ===")
                    print("- Použijte file_delete.py pro smazání souboru")
                    print("- Použijte file_embed.py pro vložení do obsahu")
                    if uploaded_url:
                        print("- Zkontrolujte dostupnost přes URL")
                        
            except json.JSONDecodeError:
                print(response.text)
        
        # Kontrola chyb
        if response.status_code not in [200, 201]:
            print()
            print("Chyba při nahrávání! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- FILE_PATH v secret.txt")
            print("- Existenci a čitelnost souboru")
            
            error_messages = {
                400: "Neplatný formát souboru nebo parametrů / Velikost souboru",
                401: "Neplatný nebo chybějící API token",
                403: "Nedostatečná oprávnění pro nahrávání",
                413: "Soubor je příliš velký",
                415: "Nepodporovaný typ souboru",
                507: "Nedostatek místa na serveru"
            }
            
            if response.status_code in error_messages:
                print(f"- {error_messages[response.status_code]}")
        else:
            print()
            print("✓ Soubor byl úspěšně nahrán!")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)
    except IOError as e:
        print(f"Chyba při čtení souboru: {e}")
        sys.exit(1)
    
    print()
    print("Tip: Pro správu souborů použijte file_delete.py nebo file_embed.py")

if __name__ == "__main__":
    main()
