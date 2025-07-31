#!/usr/bin/env python3
"""
NYX.CZ API - Smazání souboru
DELETE /api/file/delete/{id}
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

def analyze_deletion_impact(data):
    """Analyzuje dopad smazání souboru"""
    impact = {
        'references': data.get('references', 0),
        'embedded_in': data.get('embeddedIn', 0),
        'backup_available': data.get('backupAvailable', False),
        'backup_until': data.get('backupUntil'),
        'deletion_time': data.get('deletedAt'),
        'affected_content': data.get('affectedContent', []),
        'broken_links': data.get('brokenLinks', []),
        'severity': 'low'
    }
    
    # Určení závažnosti dopadu
    total_impact = impact['references'] + impact['embedded_in']
    if total_impact > 10:
        impact['severity'] = 'high'
    elif total_impact > 3:
        impact['severity'] = 'medium'
    
    return impact

def format_deletion_warnings(impact):
    """Generuje varování o dopadu smazání"""
    warnings = []
    
    if impact['references'] > 0:
        warnings.append(f"⚠️ Soubor má {impact['references']} odkazů - mohou být poškozeny")
    
    if impact['embedded_in'] > 0:
        warnings.append(f"⚠️ Soubor je vložen do {impact['embedded_in']} obsahů")
    
    if impact['severity'] == 'high':
        warnings.append("🚨 VYSOKÝ DOPAD: Smazání ovlivní mnoho obsahů")
    elif impact['severity'] == 'medium':
        warnings.append("⚠️ STŘEDNÍ DOPAD: Smazání ovlivní několik obsahů")
    
    if impact['affected_content']:
        warnings.append(f"📄 Ovlivněné obsahy: {len(impact['affected_content'])}")
    
    if impact['broken_links']:
        warnings.append(f"🔗 Poškozené odkazy: {len(impact['broken_links'])}")
    
    return warnings

def main():
    # Načtení konfigurace
    config = load_config()
    
    # Kontrola API tokenu
    api_token = config.get('NYX_API_TOKEN')
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    # Kontrola ID souboru
    file_id = config.get('FILE_ID')
    if not file_id:
        print("Chyba: Nastavte FILE_ID v secret.txt")
        print("Příklad: FILE_ID=12345")
        sys.exit(1)
    
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    
    print("=== NYX.CZ API - Smazání souboru ===")
    print(f"URL: {base_url}/file/delete/{file_id}")
    print(f"ID souboru: {file_id}")
    print()
    
    # Varování před smazáním
    print("⚠️  VAROVÁNÍ: Chystáte se TRVALE smazat soubor!")
    print(f"ID souboru: {file_id}")
    print("Tato operace je NEVRATNÁ!")
    confirmation = input("Pokračovat? (y/N): ").strip().lower()
    if confirmation not in ['y', 'yes']:
        print("Operace zrušena.")
        sys.exit(0)
    
    # Příprava požadavku
    url = f"{base_url}/file/delete/{file_id}"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        print("Mazání souboru...")
        
        # API požadavek
        response = requests.delete(url, headers=headers)
        
        print(f"HTTP Status: {response.status_code}")
        print()
        
        # Výpis odpovědi
        if response.text:
            try:
                data = response.json()
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # Dodatečné analýzy
                if response.status_code in [200, 204]:
                    print()
                    print("=== Analýza smazání souboru ===")
                    
                    # Základní informace o smazání
                    deleted_id = data.get('id', data.get('fileId', 'neznámé'))
                    deleted_name = data.get('filename', data.get('name', 'neznámý'))
                    deletion_time = data.get('deletedAt')
                    
                    if deleted_id != 'neznámé':
                        print(f"Smazané ID: {deleted_id}")
                    
                    if deleted_name != 'neznámý':
                        print(f"Smazaný soubor: {deleted_name}")
                    
                    if deletion_time:
                        print(f"Čas smazání: {deletion_time}")
                    
                    # Analýza dopadu
                    impact = analyze_deletion_impact(data)
                    
                    print()
                    print("=== Kontrola souvisejících dat ===")
                    
                    if impact['references'] > 0:
                        print(f"⚠️ Soubor měl {impact['references']} odkazů - mohou být poškozeny")
                    else:
                        print("✓ Žádné známé odkazy na soubor")
                    
                    if impact['embedded_in'] > 0:
                        print(f"⚠️ Soubor byl vložen do {impact['embedded_in']} obsahů")
                    
                    # Backup informace
                    if impact['backup_available']:
                        print("💾 Backup souboru je k dispozici")
                        if impact['backup_until']:
                            print(f"   Backup dostupný do: {impact['backup_until']}")
                    
                    # Ovlivněné obsahy
                    if impact['affected_content']:
                        print()
                        print("=== Ovlivněné obsahy ===")
                        for content in impact['affected_content'][:5]:  # Max 5 položek
                            content_type = content.get('type', 'neznámý')
                            content_title = content.get('title', 'Bez názvu')
                            content_id = content.get('id', 'neznámé')
                            print(f"- {content_type}: {content_title} (ID: {content_id})")
                        
                        if len(impact['affected_content']) > 5:
                            print(f"... a dalších {len(impact['affected_content']) - 5} obsahů")
                    
                    # Poškozené odkazy
                    if impact['broken_links']:
                        print()
                        print("=== Poškozené odkazy ===")
                        for link in impact['broken_links'][:3]:  # Max 3 odkazy
                            print(f"- {link}")
                        
                        if len(impact['broken_links']) > 3:
                            print(f"... a dalších {len(impact['broken_links']) - 3} odkazů")
                    
                    # Hodnocení dopadu
                    print()
                    print("=== Hodnocení dopadu smazání ===")
                    severity_messages = {
                        'low': "🟢 NÍZKÝ DOPAD: Minimální vliv na ostatní obsahy",
                        'medium': "🟡 STŘEDNÍ DOPAD: Ovlivní několik obsahů",
                        'high': "🔴 VYSOKÝ DOPAD: Významně ovlivní mnoho obsahů"
                    }
                    print(severity_messages.get(impact['severity'], "Neznámý dopad"))
                    
                    # Varování
                    warnings = format_deletion_warnings(impact)
                    if warnings:
                        print()
                        print("=== Varování ===")
                        for warning in warnings:
                            print(warning)
                    
                    # Doporučení po smazání
                    print()
                    print("=== Doporučení po smazání ===")
                    recommendations = [
                        "📋 Zkontrolujte obsahy, které mohly odkazovat na soubor",
                        "🔍 Ověřte, že se nepoškodily žádné stránky nebo příspěvky",
                        "🔄 Zvažte aktualizaci odkazů na alternativní soubory",
                        "📊 Zkontrolujte logy pro případné chyby 404"
                    ]
                    
                    if impact['severity'] == 'high':
                        recommendations.insert(0, "🚨 URGENTNÍ: Okamžitě zkontrolujte všechny ovlivněné obsahy")
                    
                    for rec in recommendations:
                        print(rec)
                    
                    # Bezpečnostní tipy
                    print()
                    print("=== Bezpečnostní tipy ===")
                    security_tips = [
                        "🔒 Soubor je trvale smazán a nelze jej obnovit",
                        "💾 Ujistěte se, že máte zálohu důležitých souborů",
                        "🔍 Používejte file_embed.py pro kontrolu použití před smazáním",
                        "⚠️ Zvažte deaktivaci místo smazání u důležitých souborů"
                    ]
                    
                    for tip in security_tips:
                        print(tip)
                        
            except json.JSONDecodeError:
                print(response.text)
        
        # Kontrola chyb
        if response.status_code not in [200, 204]:
            print()
            print("Chyba při mazání! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- FILE_ID v secret.txt")
            print("- Existenci souboru s daným ID")
            
            error_messages = {
                400: "Neplatné ID souboru",
                401: "Neplatný nebo chybějící API token",
                403: "Nedostatečná oprávnění pro smazání / Soubor je chráněný",
                404: f"Soubor s ID '{file_id}' neexistuje nebo již byl smazán",
                409: "Soubor je používán a nelze jej smazat - odstraňte nejprve odkazy"
            }
            
            if response.status_code in error_messages:
                print(f"- {error_messages[response.status_code]}")
        else:
            print()
            print("✓ Soubor byl úspěšně smazán!")
            
            # Statistiky smazání
            print()
            print("=== Statistiky smazání ===")
            print(f"ID souboru: {file_id}")
            print(f"Čas smazání: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Operace provedena přes: NYX.CZ API")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)
    
    print()
    print("Tip: Pro nahrání nového souboru použijte file_upload.py")

if __name__ == "__main__":
    main()
