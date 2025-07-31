#!/usr/bin/env python3
"""
NYX.CZ API - Nastavení připomínky zprávy
POST /api/mail/reminder/{id}/{newState}
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
    print("=== NYX.CZ API - Nastavení připomínky zprávy ===")
    
    # Načtení konfigurace
    config = load_config()
    
    api_token = config.get('NYX_API_TOKEN')
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    mail_id = config.get('MAIL_REMINDER_ID')
    new_state = config.get('MAIL_REMINDER_STATE')
    
    # Kontrola API tokenu
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    # Kontrola povinných parametrů
    if not mail_id:
        print("Chyba: Nastavte MAIL_REMINDER_ID v secret.txt")
        sys.exit(1)
    
    if not new_state:
        print("Chyba: Nastavte MAIL_REMINDER_STATE v secret.txt (true/false)")
        sys.exit(1)
    
    # Validace stavu
    if new_state.lower() not in ['true', 'false']:
        print("Chyba: MAIL_REMINDER_STATE musí být 'true' nebo 'false'")
        sys.exit(1)
    
    url = f"{base_url}/mail/reminder/{mail_id}/{new_state}"
    print(f"URL: {url}")
    print(f"Mail ID: {mail_id}")
    print(f"Nový stav: {new_state}")
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
            print("- MAIL_REMINDER_ID v secret.txt (existuje zpráva?)")
            print("- MAIL_REMINDER_STATE v secret.txt (true/false)")
            
            if response.status_code == 400:
                print("- Neplatný formát parametrů")
            elif response.status_code == 404:
                print(f"- Zpráva s ID {mail_id} neexistuje")
            elif response.status_code == 403:
                print("- Nedostatečná oprávnění")
        else:
            print()
            if new_state.lower() == 'true':
                print("✓ Připomínka byla úspěšně zapnuta!")
            else:
                print("✓ Připomínka byla úspěšně vypnuta!")
            print(f"Mail ID: {mail_id}")
            
            # Dodatečné informace
            print()
            print("=== Dodatečné informace ===")
            print(f"Stav připomínky: {'Zapnuto' if new_state.lower() == 'true' else 'Vypnuto'}")
            print("Pro zobrazení zpráv použijte: python3 mail_get.py")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
