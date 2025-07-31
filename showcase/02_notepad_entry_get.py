#!/usr/bin/env python3

"""
NYX.CZ API - Načtení konkrétní poznámky
GET /api/notepad/{entry_id}
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
    print("=== NYX.CZ API - Načtení konkrétní poznámky ===")
    
    # Načtení konfigurace
    config = load_config()
    
    api_token = config.get('NYX_API_TOKEN')
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    entry_id = config.get('ENTRY_ID')
    
    # Kontrola API tokenu
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    # Kontrola ENTRY_ID
    if not entry_id:
        print("Chyba: Nastavte ENTRY_ID v secret.txt")
        sys.exit(1)
    
    # Příprava požadavku
    url = f"{base_url}/notepad/{entry_id}"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    print(f"URL: {url}")
    print(f"Entry ID: {entry_id}")
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
        else:
            print(response.text)
        
        # Kontrola chyb
        if response.status_code != 200:
            print()
            print("Chyba v požadavku! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- ENTRY_ID v secret.txt")
            print("- Existenci poznámky s daným ID")
            print("- Oprávnění k poznámce")
            
            if response.status_code == 401:
                print("- Token je neplatný nebo vypršel")
            elif response.status_code == 403:
                print("- Nedostatečná oprávnění")
            elif response.status_code == 404:
                print("- Poznámka s daným ID neexistuje")
    
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
