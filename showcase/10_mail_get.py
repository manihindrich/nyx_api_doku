#!/usr/bin/env python3
"""
NYX.CZ API - Získání seznamu zpráv
GET /api/mail
"""

import requests
import json
import sys
from datetime import datetime
from collections import Counter

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

def analyze_messages(messages):
    """Analyzuje zprávy a vrátí statistiky"""
    if not messages:
        return {}
    
    total = len(messages)
    unread = sum(1 for msg in messages if not msg.get('read', True))
    read = total - unread
    
    # Analýza odesílatelů
    senders = [msg.get('from', {}).get('username', 'Neznámý') for msg in messages]
    sender_counts = Counter(senders)
    
    # Nejnovější zpráva
    latest = messages[0] if messages else None
    
    return {
        'total': total,
        'unread': unread,
        'read': read,
        'latest': latest,
        'senders': sender_counts
    }

def main():
    print("=== NYX.CZ API - Seznam zpráv ===")
    
    # Načtení konfigurace
    config = load_config()
    
    api_token = config.get('NYX_API_TOKEN')
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    
    # Kontrola API tokenu
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    url = f"{base_url}/mail"
    print(f"URL: {url}")
    print()
    
    # Hlavičky
    headers = {
        'Authorization': f'Bearer {api_token}'
    }
    
    try:
        # API požadavek
        response = requests.get(url, headers=headers)
        
        print(f"HTTP Status: {response.status_code}")
        print()
        
        # Výpis odpovědi
        if response.text:
            try:
                response_data = response.json()
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
                
                # Dodatečné analýzy
                if response.status_code == 200 and 'data' in response_data:
                    messages = response_data['data']
                    stats = analyze_messages(messages)
                    
                    print()
                    print("=== Statistiky zpráv ===")
                    print(f"Celkem zpráv: {stats['total']}")
                    
                    if stats['total'] > 0:
                        print(f"Nepřečtené: {stats['unread']}")
                        print(f"Přečtené: {stats['read']}")
                        
                        if stats['latest']:
                            latest_subject = stats['latest'].get('subject', 'N/A')
                            print(f"Nejnovější zpráva: {latest_subject}")
                        
                        print()
                        print("Odesílatelé:")
                        for sender, count in stats['senders'].most_common():
                            print(f"  {count:3d} {sender}")
                        
                        # Analýza podle data
                        print()
                        print("=== Dodatečné analýzy ===")
                        print(f"Průměrná délka předmětu: {sum(len(msg.get('subject', '')) for msg in messages) / len(messages):.1f} znaků")
                        
                        # Nejaktivnější odesílatel
                        if stats['senders']:
                            top_sender = stats['senders'].most_common(1)[0]
                            print(f"Nejaktivnější odesílatel: {top_sender[0]} ({top_sender[1]} zpráv)")
                
            except json.JSONDecodeError:
                print(response.text)
        
        # Kontrola chyb
        if response.status_code != 200:
            print()
            print("Chyba v požadavku! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- Připojení k internetu")
            
            if response.status_code == 401:
                print("- Neplatný nebo vypršelý API token")
            elif response.status_code == 403:
                print("- Nedostatečná oprávnění")
        else:
            print()
            print("✓ Seznam zpráv byl úspěšně načten!")
            print()
            print("Tip: Pro odeslání zprávy použijte: python3 mail_send.py")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
