#!/usr/bin/env python3
"""
NYX.CZ API - Nastavení připomínky příspěvku
POST /api/discussion/{discussionId}/reminder/{postId}/{newState}
"""

import requests
import json
import sys

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
    print("=== NYX.CZ API - Nastavení připomínky příspěvku ===")
    
    # Načtení konfigurace
    config = load_config()
    
    api_token = config.get('NYX_API_TOKEN')
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    discussion_id = config.get('DISCUSSION_ID')
    post_id = config.get('POST_ID')
    reminder_state = config.get('REMINDER_STATE')
    
    # Kontrola API tokenu
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    # Kontrola povinných parametrů
    if not discussion_id:
        print("Chyba: Nastavte DISCUSSION_ID v secret.txt")
        sys.exit(1)
    
    if not post_id:
        print("Chyba: Nastavte POST_ID v secret.txt")
        sys.exit(1)
    
    if not reminder_state:
        print("Chyba: Nastavte REMINDER_STATE v secret.txt (true/false)")
        sys.exit(1)
    
    # Validace stavu
    if reminder_state.lower() not in ['true', 'false']:
        print("Chyba: REMINDER_STATE musí být 'true' nebo 'false'")
        sys.exit(1)
    
    url = f"{base_url}/discussion/{discussion_id}/reminder/{post_id}/{reminder_state}"
    print(f"URL: {url}")
    print(f"Discussion ID: {discussion_id}")
    print(f"Post ID: {post_id}")
    print(f"Nový stav: {reminder_state}")
    print()
    
    # Hlavičky
    headers = {
        'Authorization': f'Bearer {api_token}'
    }
    
    try:
        # API požadavek
        response = requests.post(url, headers=headers)
        
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
            print("- POST_ID v secret.txt")
            print("- REMINDER_STATE v secret.txt (true/false)")
            
            if response.status_code == 404:
                print("- Diskuze nebo příspěvek neexistuje")
            elif response.status_code == 403:
                print("- Nedostatečná oprávnění")
            elif response.status_code == 400:
                print("- Neplatný formát parametrů")
        else:
            print()
            if reminder_state.lower() == 'true':
                print("✓ Připomínka příspěvku byla úspěšně zapnuta!")
            else:
                print("✓ Připomínka příspěvku byla úspěšně vypnuta!")
            print(f"Post ID: {post_id}")
            
            # Dodatečné informace
            print()
            print("=== Dodatečné informace ===")
            print(f"Stav připomínky: {'Zapnuto' if reminder_state.lower() == 'true' else 'Vypnuto'}")
            print("Pro zobrazení diskuze použijte: python3 discussion_get.py")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
