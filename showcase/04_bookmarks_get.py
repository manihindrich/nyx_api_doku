#!/usr/bin/env python3

"""
NYX.CZ API - Načtení záložek podle nastavení
GET /api/bookmarks
"""

import os
import sys
import json
import requests
from pathlib import Path

def load_config():
    """Načte konfiguraci ze secret.txt"""
    config_file = Path(__file__).parent / "secret.txt"
    
    if not config_file.exists():
        print("Chyba: Soubor secret.txt nenalezen!")
        print("Zkopírujte dummy-secret.txt jako secret.txt a vyplňte hodnoty.")
        sys.exit(1)
    
    config = {}
    with open(config_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                config[key] = value.strip('"')
    
    return config

def main():
    """Hlavní funkce"""
    print("=== NYX.CZ API - Načtení záložek podle nastavení ===")
    
    # Načtení konfigurace
    config = load_config()
    
    api_token = config.get('NYX_API_TOKEN')
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    
    # Kontrola API tokenu
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    # Příprava požadavku
    url = f"{base_url}/bookmarks"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    print(f"URL: {url}")
    print()
    
    try:
        # API požadavek
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"HTTP Status: {response.status_code}")
        print()
        
        # Výpis odpovědi
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Statistiky záložek
            if response.status_code == 200:
                print()
                print("=== Statistiky záložek ===")
                
                bookmarks = data.get('bookmarks', [])
                bookmarks_count = len(bookmarks)
                print(f"Počet záložek: {bookmarks_count}")
                
                if bookmarks_count > 0:
                    print()
                    print("Přehled záložek:")
                    for bookmark in bookmarks:
                        name = bookmark.get('name', 'Bez názvu')
                        bookmark_id = bookmark.get('id', 'N/A')
                        bookmark_type = bookmark.get('type', 'neznámý')
                        print(f"  - {name} (ID: {bookmark_id}, Typ: {bookmark_type})")
                        
                        # Pokud má záložka diskuze, zobraz jejich počet
                        discussions = bookmark.get('discussions', [])
                        if discussions:
                            print(f"    Diskuze: {len(discussions)}")
        else:
            print(response.text)
        
        # Kontrola chyb
        if response.status_code != 200:
            print()
            print("Chyba v požadavku! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- Připojení k internetu")
            print("- Platnost tokenu")
            
            if response.status_code == 401:
                print("- Token je neplatný nebo vypršel")
            elif response.status_code == 403:
                print("- Nedostatečná oprávnění")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při požadavku: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Chyba při parsování JSON: {e}")
        print("Odpověď serveru:")
        print(response.text)
        sys.exit(1)
    
    print()
    print("Tip: Pro zobrazení všech kategorií použijte bookmarks_all.py")

if __name__ == "__main__":
    main()
