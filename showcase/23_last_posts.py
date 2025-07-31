#!/usr/bin/env python3

"""
NYX.CZ API - Nejnovější příspěvky
GET /api/last
"""

import os
import sys
import json
import requests
from pathlib import Path
from urllib.parse import urlencode

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
    print("=== NYX.CZ API - Nejnovější příspěvky ===")
    
    # Načtení konfigurace
    config = load_config()
    
    api_token = config.get('NYX_API_TOKEN')
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    domain_id = config.get('DOMAIN_ID')
    min_rating = config.get('MIN_RATING')
    
    # Kontrola API tokenu
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    # Sestavení parametrů
    params = {}
    
    if domain_id and domain_id != "1":
        params['domain'] = domain_id
    
    if min_rating and min_rating != "5":
        params['min_rating'] = min_rating
    
    # Boolean parametry
    params['rated_by_friends'] = 'false'
    params['rated_by_me'] = 'false'
    
    # Příprava požadavku
    url = f"{base_url}/last"
    if params:
        url += "?" + urlencode(params)
    
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    print(f"URL: {url}")
    print("Parametry:")
    print(f"  - domain: {domain_id or 'všechny'}")
    print(f"  - min_rating: {min_rating or 'bez omezení'}")
    print(f"  - rated_by_friends: false")
    print(f"  - rated_by_me: false")
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
            
            # Statistiky
            if 'posts' in data:
                posts_count = len(data['posts'])
                print(f"\nNačteno {posts_count} příspěvků")
                
                if posts_count > 0:
                    print("\nPřehled příspěvků:")
                    for i, post in enumerate(data['posts'][:5], 1):  # Prvních 5
                        print(f"  {i}. ID: {post.get('id')}, "
                              f"Autor: {post.get('username')}, "
                              f"Rating: {post.get('rating', 0)}")
                    
                    if posts_count > 5:
                        print(f"  ... a dalších {posts_count - 5} příspěvků")
        else:
            print(response.text)
        
        # Kontrola chyb
        if response.status_code != 200:
            print()
            print("Chyba v požadavku! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- Připojení k internetu")
            print("- Platnost tokenu")
            print("- Parametry v secret.txt (DOMAIN_ID, MIN_RATING)")
            
            if response.status_code == 401:
                print("- Token je neplatný nebo vypršel")
            elif response.status_code == 403:
                print("- Nedostatečná oprávnění")
            elif response.status_code == 400:
                print("- Neplatné parametry")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při požadavku: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Chyba při parsování JSON: {e}")
        print("Odpověď serveru:")
        print(response.text)
        sys.exit(1)
    
    print()
    print("Tip: Upravte DOMAIN_ID a MIN_RATING v secret.txt pro filtrování")

if __name__ == "__main__":
    main()
