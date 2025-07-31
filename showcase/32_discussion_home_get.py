#!/usr/bin/env python3
"""
NYX.CZ API - Získání domovské stránky diskuze
GET /api/discussion/{discussionId}/home
"""

import requests
import json
import sys
import os
import re
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

def analyze_content(content):
    """Analyzuje obsah domovské stránky"""
    if not content or content == "null":
        return {
            'type': 'empty',
            'length': 0,
            'lines': 0,
            'html_tags': 0,
            'has_images': False,
            'has_links': False
        }
    
    analysis = {
        'type': 'text',
        'length': len(content),
        'lines': content.count('\n') + 1,
        'html_tags': 0,
        'has_images': False,
        'has_links': False
    }
    
    # Kontrola HTML obsahu
    if '<' in content and '>' in content:
        analysis['type'] = 'html'
        analysis['html_tags'] = len(re.findall(r'<[^>]+>', content))
        analysis['has_images'] = bool(re.search(r'<img[^>]*>', content, re.IGNORECASE))
        analysis['has_links'] = bool(re.search(r'<a[^>]*>', content, re.IGNORECASE))
    
    return analysis

def format_datetime(dt_str):
    """Formátuje datetime string do čitelného formátu"""
    if not dt_str or dt_str == "null":
        return "neznámé"
    
    try:
        # Pokus o parsování ISO formátu
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%d.%m.%Y %H:%M:%S')
    except:
        return dt_str

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
    
    print("=== NYX.CZ API - Domovská stránka diskuze ===")
    print(f"URL: {base_url}/discussion/{discussion_id}/home")
    print(f"Discussion ID: {discussion_id}")
    print()
    
    # Příprava požadavku
    url = f"{base_url}/discussion/{discussion_id}/home"
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
                    print()
                    print("=== Analýza domovské stránky ===")
                    
                    # Základní informace
                    title = data.get('title', 'Bez názvu')
                    description = data.get('description', 'Bez popisu')
                    content = data.get('content', '')
                    
                    print(f"Název: {title}")
                    print(f"Popis: {description}")
                    
                    # Analýza obsahu
                    content_analysis = analyze_content(content)
                    print(f"Délka obsahu: {content_analysis['length']} znaků")
                    print(f"Počet řádků: {content_analysis['lines']}")
                    
                    if content_analysis['type'] == 'html':
                        print("Typ obsahu: HTML")
                        print(f"Počet HTML tagů: {content_analysis['html_tags']}")
                        if content_analysis['has_images']:
                            print("✓ Obsahuje obrázky")
                        if content_analysis['has_links']:
                            print("✓ Obsahuje odkazy")
                    elif content_analysis['type'] == 'text':
                        print("Typ obsahu: Prostý text")
                    else:
                        print("Typ obsahu: Prázdný")
                    
                    # Metadata
                    created_at = format_datetime(data.get('createdAt'))
                    updated_at = format_datetime(data.get('updatedAt'))
                    
                    author_info = data.get('author', {})
                    if isinstance(author_info, dict):
                        author = author_info.get('username', 'neznámý')
                    else:
                        author = str(author_info) if author_info else 'neznámý'
                    
                    print(f"Vytvořeno: {created_at}")
                    print(f"Aktualizováno: {updated_at}")
                    print(f"Autor: {author}")
                    
                    # Statistiky
                    print()
                    print("=== Statistiky ===")
                    print(f"- Celková velikost odpovědi: {len(response.text)} znaků")
                    print(f"- Počet polí v odpovědi: {len(data)}")
                    
                    # Hodnocení obsahu
                    print()
                    print("=== Hodnocení obsahu ===")
                    if content_analysis['type'] == 'empty':
                        print("⚠️  Domovská stránka nemá nastavený obsah")
                        print("💡 Doporučení: Přidejte obsah pomocí discussion_home_post.py")
                    else:
                        print("✓ Domovská stránka obsahuje data")
                        
                        if content_analysis['length'] < 100:
                            print("💡 Obsah je velmi krátký, zvažte jeho rozšíření")
                        elif content_analysis['length'] > 5000:
                            print("💡 Obsah je velmi dlouhý, zvažte jeho rozdělení")
                        
                        if content_analysis['type'] == 'html' and content_analysis['html_tags'] > 50:
                            print("💡 Vysoký počet HTML tagů - zkontrolujte strukturu")
                    
                    # Doporučení pro SEO
                    if title and len(title) > 60:
                        print("💡 SEO: Název je příliš dlouhý (>60 znaků)")
                    if description and len(description) > 160:
                        print("💡 SEO: Popis je příliš dlouhý (>160 znaků)")
                        
            except json.JSONDecodeError:
                print(response.text)
        
        # Kontrola chyb
        if response.status_code != 200:
            print()
            print("Chyba v požadavku! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- DISCUSSION_ID v secret.txt")
            
            if response.status_code == 404:
                print("- Diskuze neexistuje nebo nemá domovskou stránku")
            elif response.status_code == 403:
                print("- Nedostatečná oprávnění pro zobrazení domovské stránky")
            elif response.status_code == 401:
                print("- Neplatný nebo chybějící API token")
        else:
            print()
            print("✓ Domovská stránka diskuze úspěšně načtena!")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)
    
    print()
    print("Tip: Pro úpravu domovské stránky použijte discussion_home_post.py")

if __name__ == "__main__":
    main()
