#!/usr/bin/env python3

"""
NYX.CZ API - Odeslání textového příspěvku do diskuze
POST /api/discussion/{discussionId}/send/text
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
    print("=== NYX.CZ API - Odeslání textového příspěvku ===")
    
    # Načtení konfigurace
    config = load_config()
    
    api_token = config.get('NYX_API_TOKEN')
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    discussion_id = config.get('DISCUSSION_ID')
    test_content = config.get('TEST_CONTENT')
    
    # Kontrola API tokenu
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    # Kontrola DISCUSSION_ID
    if not discussion_id:
        print("Chyba: Nastavte DISCUSSION_ID v secret.txt")
        sys.exit(1)
    
    # Kontrola TEST_CONTENT
    if not test_content:
        print("Chyba: Nastavte TEST_CONTENT v secret.txt")
        sys.exit(1)
    
    # Příprava požadavku
    url = f"{base_url}/discussion/{discussion_id}/send/text"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    # Data pro odeslání
    data = {
        'content': test_content,
        'format': 'html'
    }
    
    print(f"URL: {url}")
    print(f"Discussion ID: {discussion_id}")
    print(f"Obsah: {test_content}")
    print()
    print("JSON data:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print()
    
    try:
        # API požadavek
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"HTTP Status: {response.status_code}")
        print()
        
        # Výpis odpovědi
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            # Extrakce informací o vytvořeném příspěvku
            if response.status_code == 200 and 'post' in response_data:
                post = response_data['post']
                print(f"\n✓ Příspěvek byl úspěšně odeslán!")
                print(f"  - ID příspěvku: {post.get('id')}")
                print(f"  - Autor: {post.get('username')}")
                print(f"  - Čas: {post.get('inserted_at')}")
                print(f"  - Typ: {post.get('post_type')}")
        else:
            print(response.text)
        
        # Kontrola chyb
        if response.status_code != 200:
            print()
            print("Chyba v požadavku! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- DISCUSSION_ID v secret.txt")
            print("- Existenci diskuze s daným ID")
            print("- Oprávnění k zápisu do diskuze")
            print("- TEST_CONTENT v secret.txt")
            
            if response.status_code == 401:
                print("- Token je neplatný nebo vypršel")
            elif response.status_code == 403:
                print("- Nedostatečná oprávnění nebo nemáte právo psát do této diskuze")
            elif response.status_code == 404:
                print(f"- Diskuze s ID {discussion_id} neexistuje")
            elif response.status_code == 400:
                print("- Neplatný obsah nebo formát příspěvku")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při požadavku: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Chyba při parsování JSON: {e}")
        print("Odpověď serveru:")
        print(response.text)
        sys.exit(1)

if __name__ == "__main__":
    main()
