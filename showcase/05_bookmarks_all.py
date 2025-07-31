#!/usr/bin/env python3

"""
NYX.CZ API - Načtení všech kategorií záložek rozbalených
GET /api/bookmarks/all
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
    print("=== NYX.CZ API - Všechny kategorie záložek rozbalené ===")
    
    # Načtení konfigurace
    config = load_config()
    
    api_token = config.get('NYX_API_TOKEN')
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    
    # Kontrola API tokenu
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    # Příprava požadavku
    url = f"{base_url}/bookmarks/all"
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
            
            # Detailní statistiky
            if response.status_code == 200:
                print()
                print("=== Detailní statistiky záložek ===")
                
                bookmarks = data.get('bookmarks', [])
                bookmarks_count = len(bookmarks)
                
                # Spočítání celkového počtu diskuzí
                total_discussions = sum(len(bookmark.get('discussions', [])) for bookmark in bookmarks)
                
                print(f"Počet kategorií: {bookmarks_count}")
                print(f"Celkem diskuzí: {total_discussions}")
                
                if bookmarks_count > 0:
                    print()
                    print("Přehled kategorií s diskuzemi:")
                    for bookmark in bookmarks:
                        name = bookmark.get('name', 'Bez názvu')
                        discussions = bookmark.get('discussions', [])
                        discussions_count = len(discussions)
                        print(f"  📁 {name} ({discussions_count} diskuzí)")
                    
                    print()
                    print("Nejnovější diskuze v kategoriích:")
                    shown_discussions = 0
                    for bookmark in bookmarks:
                        if shown_discussions >= 10:  # Omezit na 10 diskuzí
                            break
                        
                        name = bookmark.get('name', 'Bez názvu')
                        discussions = bookmark.get('discussions', [])
                        
                        if discussions:
                            print(f"  📁 {name}:")
                            for discussion in discussions[:3]:  # Prvních 3 diskuze z kategorie
                                if shown_discussions >= 10:
                                    break
                                discussion_name = discussion.get('name', 'Bez názvu')
                                discussion_id = discussion.get('id', 'N/A')
                                print(f"    - {discussion_name} (ID: {discussion_id})")
                                shown_discussions += 1
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
    print("Tip: Pro záložky podle nastavení použijte bookmarks_get.py")

if __name__ == "__main__":
    main()
