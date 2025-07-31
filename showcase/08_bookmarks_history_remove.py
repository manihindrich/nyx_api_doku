#!/usr/bin/env python3
"""
NYX.CZ API - Odebrání diskuze z historie
POST /api/bookmarks/history/remove
"""

import requests
import json
import sys
import os

def load_config():
    """Načte konfiguraci ze secret.txt"""
    config = {}
    try:
        with open('secret.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"\'')
        return config
    except FileNotFoundError:
        print("Chyba: Soubor secret.txt nenalezen!")
        print("Zkopírujte dummy-secret.txt jako secret.txt a vyplňte hodnoty.")
        sys.exit(1)

def main():
    print("=== NYX.CZ API - Odebrání diskuze z historie ===")
    
    # Načtení konfigurace
    config = load_config()
    
    api_token = config.get('NYX_API_TOKEN')
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    discussion_id = config.get('DISCUSSION_ID')
    
    # Kontrola API tokenu
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    # Kontrola DISCUSSION_ID
    if not discussion_id:
        print("Chyba: Nastavte DISCUSSION_ID v secret.txt")
        sys.exit(1)
    
    url = f"{base_url}/bookmarks/history/remove"
    print(f"URL: {url}")
    print(f"Discussion ID: {discussion_id}")
    print()
    
    # Příprava dat
    data = {
        "discussionId": int(discussion_id)
    }
    
    print("JSON data:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print()
    
    # Hlavičky
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # API požadavek
        response = requests.post(url, json=data, headers=headers)
        
        print(f"HTTP Status: {response.status_code}")
        print()
        
        # Výpis odpovědi
        if response.text:
            try:
                response_data = response.json()
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print(response.text)
        
        # Kontrola chyb
        if response.status_code != 200:
            print()
            print("Chyba v požadavku! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- DISCUSSION_ID v secret.txt")
            print("- Existenci diskuze s daným ID")
            print("- Zda je diskuze v historii")
            
            if response.status_code == 404:
                print(f"- Diskuze s ID {discussion_id} neexistuje nebo není v historii")
            elif response.status_code == 403:
                print("- Nedostatečná oprávnění")
        else:
            print()
            print("✓ Diskuze byla úspěšně odebrána z historie!")
            
            # Dodatečné analýzy
            print()
            print("=== Dodatečné informace ===")
            print(f"Odebraná diskuze ID: {discussion_id}")
            print("Pro zobrazení aktuální historie použijte: python3 bookmarks_history.py")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
