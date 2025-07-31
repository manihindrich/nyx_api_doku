#!/usr/bin/env python3
"""
NYX.CZ API - Smazání příspěvku v diskuzi
DELETE /api/discussion/{discussionId}/delete/{postId}
"""

import requests
import json
import sys
import os
from datetime import datetime

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
    
    post_id = config.get('POST_ID')
    if not post_id:
        print("Chyba: Nastavte POST_ID v secret.txt")
        sys.exit(1)
    
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    
    print("=== NYX.CZ API - Smazání příspěvku v diskuzi ===")
    print(f"URL: {base_url}/discussion/{discussion_id}/delete/{post_id}")
    print(f"Discussion ID: {discussion_id}")
    print(f"Post ID: {post_id}")
    print()
    
    # Varování před smazáním
    print("⚠️  VAROVÁNÍ: Tato operace NEVRATNĚ smaže příspěvek!")
    confirmation = input("Pokračovat? (y/N): ").strip().lower()
    if confirmation not in ['y', 'yes']:
        print("Operace zrušena.")
        sys.exit(0)
    
    # Příprava požadavku
    url = f"{base_url}/discussion/{discussion_id}/delete/{post_id}"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # API požadavek
        response = requests.delete(url, headers=headers)
        
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
            print("- POST_ID v secret.txt")
            
            if response.status_code == 404:
                print("- Diskuze nebo příspěvek neexistuje")
            elif response.status_code == 403:
                print("- Nedostatečná oprávnění (můžete mazat pouze své příspěvky)")
            elif response.status_code == 400:
                print("- Neplatný formát parametrů")
        else:
            print()
            print("✓ Příspěvek byl úspěšně smazán!")
            
            # Dodatečné analýzy
            print()
            print("=== Statistiky smazání ===")
            print(f"Discussion ID: {discussion_id}")
            print(f"Smazaný Post ID: {post_id}")
            print(f"Čas smazání: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Status kód: {response.status_code}")
            
            # Bezpečnostní informace
            print()
            print("=== Bezpečnostní informace ===")
            print("- Příspěvek byl trvale smazán")
            print("- Operace je nevratná")
            print("- Můžete mazat pouze své vlastní příspěvky")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)
    
    print()
    print("Tip: Pro zobrazení diskuze použijte discussion_get.py")

if __name__ == "__main__":
    main()
