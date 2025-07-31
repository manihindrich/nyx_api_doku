#!/usr/bin/env python3
"""
NYX.CZ API - Získání přístupových práv diskuze
GET /api/discussion/{discussionId}/access_rights
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

def analyze_access_rights(data):
    """Analyzuje přístupová práva a vrátí detailní informace"""
    analysis = {
        'basic_rights': {},
        'special_rights': {},
        'access_level': 'unknown',
        'summary': []
    }
    
    # Základní práva
    basic_rights = ['canRead', 'canWrite', 'canModerate', 'canAdmin']
    for right in basic_rights:
        analysis['basic_rights'][right] = data.get(right, False)
    
    # Speciální práva
    special_rights = ['canDelete', 'canEdit', 'canPin', 'canLock', 'canMove']
    for right in special_rights:
        if right in data:
            analysis['special_rights'][right] = data.get(right, False)
    
    # Určení úrovně přístupu
    if analysis['basic_rights'].get('canAdmin'):
        analysis['access_level'] = 'admin'
        analysis['summary'].append("🔑 Administrátor - plná práva")
    elif analysis['basic_rights'].get('canModerate'):
        analysis['access_level'] = 'moderator'
        analysis['summary'].append("🛡️  Moderátor - rozšířená práva")
    elif analysis['basic_rights'].get('canWrite'):
        analysis['access_level'] = 'user'
        analysis['summary'].append("✏️  Uživatel - práva zápisu")
    elif analysis['basic_rights'].get('canRead'):
        analysis['access_level'] = 'reader'
        analysis['summary'].append("👁️  Čtenář - pouze čtení")
    else:
        analysis['access_level'] = 'none'
        analysis['summary'].append("🚫 Bez přístupu")
    
    return analysis

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
    
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    
    print("=== NYX.CZ API - Přístupová práva diskuze ===")
    print(f"URL: {base_url}/discussion/{discussion_id}/access_rights")
    print(f"Discussion ID: {discussion_id}")
    print()
    
    # Příprava požadavku
    url = f"{base_url}/discussion/{discussion_id}/access_rights"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # API požadavek
        response = requests.get(url, headers=headers)
        
        print(f"HTTP Status: {response.status_code}")
        print()
        
        # Výpis odpovědi
        if response.text:
            try:
                data = response.json()
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # Dodatečné analýzy
                if response.status_code == 200:
                    analysis = analyze_access_rights(data)
                    
                    print()
                    print("=== Analýza přístupových práv ===")
                    
                    # Základní práva
                    print("Základní práva:")
                    for right, value in analysis['basic_rights'].items():
                        czech_names = {
                            'canRead': 'Práva čtení',
                            'canWrite': 'Práva zápisu',
                            'canModerate': 'Práva moderování',
                            'canAdmin': 'Administrátorská práva'
                        }
                        print(f"  {czech_names.get(right, right)}: {value}")
                    
                    # Speciální práva
                    if analysis['special_rights']:
                        print("\nSpeciální práva:")
                        czech_special = {
                            'canDelete': 'Práva mazání',
                            'canEdit': 'Práva editace',
                            'canPin': 'Práva připínání',
                            'canLock': 'Práva uzamykání',
                            'canMove': 'Práva přesouvání'
                        }
                        for right, value in analysis['special_rights'].items():
                            print(f"  {czech_special.get(right, right)}: {value}")
                    
                    # Úroveň přístupu
                    print()
                    print("=== Úroveň přístupu ===")
                    for summary in analysis['summary']:
                        print(summary)
                    
                    # Doporučení
                    print()
                    print("=== Doporučení ===")
                    if analysis['access_level'] == 'admin':
                        print("- Máte plná práva k této diskuzi")
                        print("- Můžete spravovat všechny aspekty diskuze")
                    elif analysis['access_level'] == 'moderator':
                        print("- Můžete moderovat příspěvky")
                        print("- Máte rozšířená práva správy")
                    elif analysis['access_level'] == 'user':
                        print("- Můžete přispívat do diskuze")
                        print("- Můžete editovat své příspěvky")
                    elif analysis['access_level'] == 'reader':
                        print("- Můžete pouze číst diskuzi")
                        print("- Pro přispívání potřebujete vyšší oprávnění")
                    else:
                        print("- Nemáte přístup k této diskuzi")
                        print("- Kontaktujte administrátora pro udělení přístupu")
                        
            except json.JSONDecodeError:
                print(response.text)
        
        # Kontrola chyb
        if response.status_code != 200:
            print()
            print("Chyba v požadavku! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- DISCUSSION_ID v secret.txt")
            
            if response.status_code == 404:
                print("- Diskuze neexistuje")
            elif response.status_code == 403:
                print("- Nedostatečná oprávnění pro zobrazení práv")
            elif response.status_code == 401:
                print("- Neplatný nebo chybějící API token")
        else:
            print()
            print("✓ Přístupová práva úspěšně načtena!")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)
    
    print()
    print("Tip: Pro úpravu práv použijte discussion_access_rights_post.py")

if __name__ == "__main__":
    main()
