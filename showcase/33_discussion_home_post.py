#!/usr/bin/env python3
"""
NYX.CZ API - Nastavení domovské stránky diskuze
POST /api/discussion/{discussionId}/home
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

def analyze_home_page_data(data_str):
    """Analyzuje data domovské stránky"""
    try:
        data = json.loads(data_str)
        analysis = {
            'title': data.get('title', ''),
            'content': data.get('content', ''),
            'description': data.get('description', ''),
            'content_type': 'text',
            'content_length': 0,
            'html_tags': 0,
            'has_images': False,
            'has_links': False,
            'seo_score': 0
        }
        
        # Analýza obsahu
        content = analysis['content']
        if content:
            analysis['content_length'] = len(content)
            
            # Kontrola HTML obsahu
            if '<' in content and '>' in content:
                analysis['content_type'] = 'html'
                analysis['html_tags'] = len(re.findall(r'<[^>]+>', content))
                analysis['has_images'] = bool(re.search(r'<img[^>]*>', content, re.IGNORECASE))
                analysis['has_links'] = bool(re.search(r'<a[^>]*>', content, re.IGNORECASE))
        
        # SEO skóre
        seo_score = 0
        title = analysis['title']
        description = analysis['description']
        
        if title and 10 <= len(title) <= 60:
            seo_score += 25
        if description and 50 <= len(description) <= 160:
            seo_score += 25
        if content and len(content) >= 100:
            seo_score += 25
        if content and not re.search(r'<script|<iframe', content, re.IGNORECASE):
            seo_score += 25
        
        analysis['seo_score'] = seo_score
        
        return analysis
    except json.JSONDecodeError:
        return None

def validate_html(content):
    """Základní validace HTML obsahu"""
    issues = []
    
    # Kontrola párových tagů
    opening_tags = re.findall(r'<([a-zA-Z][^>]*)>', content)
    closing_tags = re.findall(r'</([a-zA-Z][^>]*)>', content)
    
    for tag in opening_tags:
        tag_name = tag.split()[0].lower()
        if tag_name not in ['img', 'br', 'hr', 'input', 'meta', 'link']:
            if tag_name not in [t.lower() for t in closing_tags]:
                issues.append(f"Nepárový tag: <{tag_name}>")
    
    # Kontrola základních atributů
    if re.search(r'<img[^>]*(?!alt=)', content, re.IGNORECASE):
        issues.append("Obrázky bez alt atributu")
    
    if re.search(r'<a[^>]*(?!href=)', content, re.IGNORECASE):
        issues.append("Odkazy bez href atributu")
    
    return issues

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
    
    home_page_data = config.get('HOME_PAGE_DATA')
    if not home_page_data:
        print("Chyba: Nastavte HOME_PAGE_DATA v secret.txt")
        print('Příklad: HOME_PAGE_DATA={"title":"Název","content":"Obsah stránky"}')
        sys.exit(1)
    
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    
    print("=== NYX.CZ API - Nastavení domovské stránky diskuze ===")
    print(f"URL: {base_url}/discussion/{discussion_id}/home")
    print(f"Discussion ID: {discussion_id}")
    print(f"Data stránky: {home_page_data}")
    print()
    
    # Varování před změnou
    print("⚠️  VAROVÁNÍ: Měníte domovskou stránku diskuze!")
    confirmation = input("Pokračovat? (y/N): ").strip().lower()
    if confirmation not in ['y', 'yes']:
        print("Operace zrušena.")
        sys.exit(0)
    
    # Příprava požadavku
    url = f"{base_url}/discussion/{discussion_id}/home"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    # Parsování JSON dat
    try:
        data = json.loads(home_page_data)
    except json.JSONDecodeError:
        print("Chyba: HOME_PAGE_DATA není platný JSON!")
        sys.exit(1)
    
    # Předběžná analýza dat
    analysis = analyze_home_page_data(home_page_data)
    if analysis:
        print()
        print("=== Předběžná analýza dat ===")
        print(f"Název: {analysis['title']}")
        print(f"Délka obsahu: {analysis['content_length']} znaků")
        print(f"Typ obsahu: {analysis['content_type']}")
        print(f"SEO skóre: {analysis['seo_score']}/100")
        
        if analysis['content_type'] == 'html':
            print(f"HTML tagů: {analysis['html_tags']}")
            
            # Validace HTML
            html_issues = validate_html(analysis['content'])
            if html_issues:
                print("⚠️  HTML problémy:")
                for issue in html_issues:
                    print(f"  - {issue}")
    
    try:
        # API požadavek
        response = requests.post(url, headers=headers, json=data)
        
        print(f"\nHTTP Status: {response.status_code}")
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
            print("- HOME_PAGE_DATA v secret.txt (platný JSON)")
            
            if response.status_code == 404:
                print("- Diskuze neexistuje")
            elif response.status_code == 403:
                print("- Nedostatečná oprávnění pro úpravu domovské stránky")
            elif response.status_code == 400:
                print("- Neplatný formát dat nebo parametrů")
            elif response.status_code == 401:
                print("- Neplatný nebo chybějící API token")
        else:
            print()
            print("✓ Domovská stránka byla úspěšně nastavena!")
            
            # Dodatečné analýzy
            if analysis:
                print()
                print("=== Analýza nastavené stránky ===")
                print(f"Název: {analysis['title']}")
                if analysis['description']:
                    print(f"Popis: {analysis['description']}")
                
                print(f"Délka obsahu: {analysis['content_length']} znaků")
                print(f"Typ obsahu: {analysis['content_type']}")
                
                if analysis['content_type'] == 'html':
                    print(f"Počet HTML tagů: {analysis['html_tags']}")
                    if analysis['has_images']:
                        print("✓ Obsahuje obrázky")
                    if analysis['has_links']:
                        print("✓ Obsahuje odkazy")
                
                # SEO hodnocení
                print()
                print("=== SEO hodnocení ===")
                print(f"Celkové skóre: {analysis['seo_score']}/100")
                
                if analysis['seo_score'] >= 75:
                    print("🟢 Výborné SEO")
                elif analysis['seo_score'] >= 50:
                    print("🟡 Dobré SEO")
                else:
                    print("🔴 Slabé SEO")
                
                # Doporučení
                print()
                print("=== Doporučení ===")
                if not analysis['title'] or len(analysis['title']) < 10:
                    print("💡 Přidejte výstižný název (10-60 znaků)")
                elif len(analysis['title']) > 60:
                    print("💡 Zkraťte název (max 60 znaků)")
                
                if not analysis['description'] or len(analysis['description']) < 50:
                    print("💡 Přidejte popis (50-160 znaků)")
                elif len(analysis['description']) > 160:
                    print("💡 Zkraťte popis (max 160 znaků)")
                
                if analysis['content_length'] < 100:
                    print("💡 Rozšiřte obsah pro lepší SEO")
                
                # Statistiky
                print()
                print("=== Statistiky změny ===")
                print(f"Discussion ID: {discussion_id}")
                print(f"Čas změny: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Velikost dat: {len(home_page_data)} znaků")
                
                print()
                print("=== Další kroky ===")
                print("- Zkontrolujte výsledek pomocí discussion_home_get.py")
                print("- Ujistěte se, že obsah je správně formátován")
                if analysis['content_type'] == 'html':
                    print("- Pro HTML obsah ověřte validitu tagů")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)
    
    print()
    print("Tip: Pro zobrazení domovské stránky použijte discussion_home_get.py")

if __name__ == "__main__":
    main()
