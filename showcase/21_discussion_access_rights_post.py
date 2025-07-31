#!/usr/bin/env python3
"""
NYX.CZ API - Nastavení přístupových práv diskuze
POST /api/discussion/{discussionId}/access_rights
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

def analyze_access_rights_data(data_str):
    """Analyzuje data přístupových práv"""
    try:
        data = json.loads(data_str)
        analysis = {
            'user_id': data.get('userId', data.get('username', 'neznámý')),
            'rights': {},
            'access_level': 'unknown'
        }
        
        # Základní práva
        rights = ['canRead', 'canWrite', 'canModerate', 'canAdmin']
        for right in rights:
            if right in data:
                analysis['rights'][right] = data[right]
        
        # Určení úrovně přístupu
        if analysis['rights'].get('canAdmin'):
            analysis['access_level'] = 'admin'
        elif analysis['rights'].get('canModerate'):
            analysis['access_level'] = 'moderator'
        elif analysis['rights'].get('canWrite'):
            analysis['access_level'] = 'user'
        elif analysis['rights'].get('canRead'):
            analysis['access_level'] = 'reader'
        else:
            analysis['access_level'] = 'none'
        
        return analysis
    except json.JSONDecodeError:
        return None

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
    
    access_rights_data = config.get('ACCESS_RIGHTS_DATA')
    if not access_rights_data:
        print("Chyba: Nastavte ACCESS_RIGHTS_DATA v secret.txt")
        print('Příklad: ACCESS_RIGHTS_DATA={"userId":123,"canRead":true,"canWrite":true}')
        sys.exit(1)
    
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    
    print("=== NYX.CZ API - Nastavení přístupových práv diskuze ===")
    print(f"URL: {base_url}/discussion/{discussion_id}/access_rights")
    print(f"Discussion ID: {discussion_id}")
    print(f"Data práv: {access_rights_data}")
    print()
    
    # Varování před změnou práv
    print("⚠️  VAROVÁNÍ: Měníte přístupová práva diskuze!")
    confirmation = input("Pokračovat? (y/N): ").strip().lower()
    if confirmation not in ['y', 'yes']:
        print("Operace zrušena.")
        sys.exit(0)
    
    # Příprava požadavku
    url = f"{base_url}/discussion/{discussion_id}/access_rights"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    # Parsování JSON dat
    try:
        data = json.loads(access_rights_data)
    except json.JSONDecodeError:
        print("Chyba: ACCESS_RIGHTS_DATA není platný JSON!")
        sys.exit(1)
    
    try:
        # API požadavek
        response = requests.post(url, headers=headers, json=data)
        
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
            print("- ACCESS_RIGHTS_DATA v secret.txt (platný JSON)")
            
            if response.status_code == 404:
                print("- Diskuze nebo uživatel neexistuje")
            elif response.status_code == 403:
                print("- Nedostatečná oprávnění pro změnu práv")
            elif response.status_code == 400:
                print("- Neplatný formát dat nebo parametrů")
            elif response.status_code == 401:
                print("- Neplatný nebo chybějící API token")
        else:
            print()
            print("✓ Přístupová práva byla úspěšně změněna!")
            
            # Dodatečné analýzy
            analysis = analyze_access_rights_data(access_rights_data)
            if analysis:
                print()
                print("=== Analýza nastavených práv ===")
                print(f"Uživatel: {analysis['user_id']}")
                
                czech_names = {
                    'canRead': 'Práva čtení',
                    'canWrite': 'Práva zápisu',
                    'canModerate': 'Práva moderování',
                    'canAdmin': 'Administrátorská práva'
                }
                
                for right, value in analysis['rights'].items():
                    print(f"{czech_names.get(right, right)}: {value}")
                
                print()
                print("=== Nová úroveň přístupu ===")
                access_levels = {
                    'admin': "🔑 Administrátor - plná práva",
                    'moderator': "🛡️  Moderátor - rozšířená práva",
                    'user': "✏️  Uživatel - práva zápisu",
                    'reader': "👁️  Čtenář - pouze čtení",
                    'none': "🚫 Bez přístupu"
                }
                print(access_levels.get(analysis['access_level'], "❓ Neznámá úroveň"))
                
                # Bezpečnostní doporučení
                print()
                print("=== Bezpečnostní doporučení ===")
                if analysis['access_level'] == 'admin':
                    print("- Administrátorská práva udělujte pouze důvěryhodným uživatelům")
                    print("- Pravidelně kontrolujte seznam administrátorů")
                elif analysis['access_level'] == 'moderator':
                    print("- Moderátoři mohou mazat a upravovat příspěvky")
                    print("- Ujistěte se, že rozumí pravidlům komunity")
                
                # Statistiky
                print()
                print("=== Statistiky změny ===")
                print(f"Discussion ID: {discussion_id}")
                print(f"Čas změny: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Počet změněných práv: {len(analysis['rights'])}")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)
    
    print()
    print("Tip: Pro zobrazení aktuálních práv použijte discussion_access_rights_get.py")

if __name__ == "__main__":
    main()
