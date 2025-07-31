#!/usr/bin/env python3

"""
NYX.CZ API - Vyhledání uživatele
GET /api/search/username/{username}
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
    print("=== NYX.CZ API - Vyhledání uživatele ===")
    
    # Načtení konfigurace
    config = load_config()
    
    api_token = config.get('NYX_API_TOKEN')
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    search_username = config.get('SEARCH_USERNAME')
    
    # Kontrola API tokenu
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    # Kontrola SEARCH_USERNAME
    if not search_username:
        print("Chyba: Nastavte SEARCH_USERNAME v secret.txt")
        sys.exit(1)
    
    # Příprava požadavku
    url = f"{base_url}/search/username/{search_username}"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    print(f"URL: {url}")
    print(f"Hledaný uživatel: {search_username}")
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
            
            # Statistiky výsledků
            if response.status_code == 200:
                print()
                print("=== Statistiky výsledků ===")
                
                exact_count = len(data.get('exact', []))
                friends_count = len(data.get('friends', []))
                others_count = len(data.get('others', []))
                total_count = exact_count + friends_count + others_count
                
                print(f"Přesné shody: {exact_count}")
                print(f"Přátelé: {friends_count}")
                print(f"Ostatní: {others_count}")
                print(f"Celkem: {total_count}")
                
                # Výpis prvních výsledků
                if exact_count > 0:
                    print(f"\nPřesné shody:")
                    for user in data['exact'][:3]:  # Prvních 3
                        username = user['user']['username']
                        activity = user['activity']
                        status = activity.get('status_details', 'Neznámý')
                        location = activity.get('location', 'Neznámá')
                        print(f"  - {username} ({status}) - {location}")
                
                if friends_count > 0:
                    print(f"\nPřátelé:")
                    for user in data['friends'][:3]:  # Prvních 3
                        username = user['user']['username']
                        activity = user['activity']
                        status = activity.get('status_details', 'Neznámý')
                        print(f"  - {username} ({status})")
                
                if others_count > 0:
                    print(f"\nOstatní:")
                    for user in data['others'][:3]:  # Prvních 3
                        username = user['user']['username']
                        activity = user['activity']
                        status = activity.get('status_details', 'Neznámý')
                        print(f"  - {username} ({status})")
        else:
            print(response.text)
        
        # Kontrola chyb
        if response.status_code != 200:
            print()
            print("Chyba v požadavku! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- SEARCH_USERNAME v secret.txt")
            print("- Formát uživatelského jména (3-15 znaků, A-Z0-9_)")
            
            if response.status_code == 401:
                print("- Token je neplatný nebo vypršel")
            elif response.status_code == 404:
                print(f"- Uživatel '{search_username}' nebyl nalezen")
            elif response.status_code == 400:
                print("- Neplatný formát uživatelského jména")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při požadavku: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Chyba při parsování JSON: {e}")
        print("Odpověď serveru:")
        print(response.text)
        sys.exit(1)
    
    print()
    print("Tip: Změňte SEARCH_USERNAME v secret.txt pro vyhledání jiného uživatele")

if __name__ == "__main__":
    main()
