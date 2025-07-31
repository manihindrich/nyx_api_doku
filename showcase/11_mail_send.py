#!/usr/bin/env python3
"""
NYX.CZ API - Odeslání zprávy
POST /api/mail/send
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
    print("=== NYX.CZ API - Odeslání zprávy ===")
    
    # Načtení konfigurace
    config = load_config()
    
    api_token = config.get('NYX_API_TOKEN')
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    to_username = config.get('MAIL_TO_USERNAME')
    subject = config.get('MAIL_SUBJECT')
    content = config.get('MAIL_CONTENT')
    
    # Kontrola API tokenu
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    # Kontrola povinných parametrů
    if not to_username:
        print("Chyba: Nastavte MAIL_TO_USERNAME v secret.txt")
        sys.exit(1)
    
    if not subject:
        print("Chyba: Nastavte MAIL_SUBJECT v secret.txt")
        sys.exit(1)
    
    if not content:
        print("Chyba: Nastavte MAIL_CONTENT v secret.txt")
        sys.exit(1)
    
    url = f"{base_url}/mail/send"
    print(f"URL: {url}")
    print(f"Příjemce: {to_username}")
    print(f"Předmět: {subject}")
    print()
    
    # Příprava dat
    data = {
        "to": to_username,
        "subject": subject,
        "content": content
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
            print("- MAIL_TO_USERNAME v secret.txt (existuje uživatel?)")
            print("- MAIL_SUBJECT v secret.txt (není prázdný?)")
            print("- MAIL_CONTENT v secret.txt (není prázdný?)")
            
            if response.status_code == 400:
                print("- Neplatná data (zkontrolujte formát)")
            elif response.status_code == 404:
                print(f"- Uživatel '{to_username}' neexistuje")
            elif response.status_code == 403:
                print("- Nedostatečná oprávnění")
        else:
            print()
            print("✓ Zpráva byla úspěšně odeslána!")
            print(f"Příjemce: {to_username}")
            print(f"Předmět: {subject}")
            
            # Dodatečné informace
            print()
            print("=== Dodatečné informace ===")
            print(f"Délka zprávy: {len(content)} znaků")
            print(f"Délka předmětu: {len(subject)} znaků")
            print("Pro zobrazení odeslaných zpráv použijte: python3 mail_get.py")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
