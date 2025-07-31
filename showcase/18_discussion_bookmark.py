#!/usr/bin/env python3
"""
NYX.CZ API - Nastavení záložky diskuze
POST /api/discussion/{discussionId}/bookmark/{newState}
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
                    config[key.strip()] = value.strip()
    except FileNotFoundError:
        print("Chyba: Soubor secret.txt nenalezen!")
        print("Zkopírujte dummy-secret.txt jako secret.txt a vyplňte hodnoty.")
        sys.exit(1)
    return config

def main():
    # Načtení konfigurace
    config = load_config()
    
    # Kontrola API tokenu
    api_token = config.get('NYX_API_TOKEN')
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    # Kontrola povinných parametrů
    discussion_id = config.get('DISCUSSION_ID')
    if not discussion_id:
        print("Chyba: Nastavte DISCUSSION_ID v secret.txt")
        sys.exit(1)
    
    bookmark_state = config.get('BOOKMARK_STATE')
    if not bookmark_state:
        print("Chyba: Nastavte BOOKMARK_STATE v secret.txt (true/false)")
        sys.exit(1)
    
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    
    print("=== NYX.CZ API - Nastavení záložky diskuze ===")
    print(f"URL: {base_url}/discussion/{discussion_id}/bookmark/{bookmark_state}")
    print(f"Discussion ID: {discussion_id}")
    print(f"Nový stav: {bookmark_state}")
    print()
    
    # Příprava požadavku
    url = f"{base_url}/discussion/{discussion_id}/bookmark/{bookmark_state}"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # API požadavek
        response = requests.post(url, headers=headers)
        
        print(f"HTTP Status: {response.status_code}")
        print()
        
        # Výpis odpovědi
        if response.text:
            try:
                data = response.json()
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print(response.text)
        
        # Kontrola chyb
        if response.status_code != 200:
            print()
            print("Chyba v požadavku! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- DISCUSSION_ID v secret.txt")
            print("- BOOKMARK_STATE v secret.txt (true/false)")
            
            if response.status_code == 404:
                print("- Diskuze neexistuje")
            elif response.status_code == 403:
                print("- Nedostatečná oprávnění")
            elif response.status_code == 400:
                print("- Neplatný formát parametrů")
        else:
            print()
            if bookmark_state.lower() == 'true':
                print("✓ Diskuze byla úspěšně přidána do záložek!")
            else:
                print("✓ Diskuze byla úspěšně odebrána ze záložek!")
            
            # Dodatečné analýzy
            print()
            print("=== Dodatečné informace ===")
            print(f"Akce: {'Přidání do záložek' if bookmark_state.lower() == 'true' else 'Odebrání ze záložek'}")
            print(f"Discussion ID: {discussion_id}")
            print(f"Timestamp: {requests.utils.default_headers()}")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)
    
    print()
    print("Tip: Pro zobrazení záložek použijte bookmarks_get.py")

if __name__ == "__main__":
    main()
