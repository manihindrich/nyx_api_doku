#!/usr/bin/env python3
"""
NYX.CZ API - Úprava položky na nástěnce
POST /api/discussion/{discussionId}/content/{contentId}/save
"""

import requests
import json
import sys
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

def analyze_content_update(data):
    """Analyzuje výsledek úpravy obsahu"""
    analysis = {
        'content_id': data.get('content_id', data.get('id', 'neznámé')),
        'updated_at': data.get('updated_at', data.get('modified_at')),
        'version': data.get('version', 'neznámá'),
        'content_info': {},
        'revision_info': data.get('revision_info', {}),
        'edit_stats': data.get('edit_stats', {}),
        'permissions': data.get('permissions', {}),
        'validation': data.get('validation', {}),
        'change_type': 'unknown',
        'quality_metrics': {}
    }
    
    # Analýza obsahu
    if 'content' in data:
        content = data['content']
        analysis['content_info'] = {
            'length': len(content),
            'format': data.get('format', 'text'),
            'preview': content[:100] + '...' if len(content) > 100 else content,
            'word_count': len(content.split()),
            'line_count': content.count('\n') + 1
        }
    
    # Určení typu změny
    if analysis['edit_stats']:
        chars_added = analysis['edit_stats'].get('chars_added', 0)
        chars_removed = analysis['edit_stats'].get('chars_removed', 0)
        
        if chars_added > chars_removed:
            analysis['change_type'] = 'expansion'
        elif chars_removed > chars_added:
            analysis['change_type'] = 'reduction'
        else:
            analysis['change_type'] = 'modification'
    
    # Metriky kvality
    if analysis['content_info']:
        content_length = analysis['content_info']['length']
        word_count = analysis['content_info']['word_count']
        
        analysis['quality_metrics'] = {
            'readability': 'good' if 50 <= word_count <= 500 else 'needs_attention',
            'length_category': get_length_category(content_length),
            'structure_score': calculate_structure_score(data.get('content', ''))
        }
    
    return analysis

def get_length_category(length):
    """Určí kategorii délky obsahu"""
    if length < 50:
        return 'very_short'
    elif length < 200:
        return 'short'
    elif length < 1000:
        return 'medium'
    elif length < 5000:
        return 'long'
    else:
        return 'very_long'

def calculate_structure_score(content):
    """Vypočítá skóre struktury obsahu"""
    if not content:
        return 0
    
    score = 0
    
    # Bodování za různé strukturální prvky
    if '\n\n' in content:  # Odstavce
        score += 2
    if any(line.strip().startswith('#') for line in content.split('\n')):  # Nadpisy
        score += 3
    if any(line.strip().startswith('-') or line.strip().startswith('*') for line in content.split('\n')):  # Seznamy
        score += 2
    if 'http' in content.lower():  # Odkazy
        score += 1
    
    return min(score, 10)  # Maximum 10 bodů

def get_content_recommendations(analysis):
    """Generuje doporučení pro obsah"""
    recommendations = []
    
    # Doporučení podle délky
    length_cat = analysis['quality_metrics'].get('length_category', 'medium')
    if length_cat == 'very_short':
        recommendations.append("💡 Zvažte rozšíření obsahu pro lepší informativnost")
    elif length_cat == 'very_long':
        recommendations.append("✂️ Zvažte rozdělení dlouhého obsahu na sekce")
    
    # Doporučení podle struktury
    structure_score = analysis['quality_metrics'].get('structure_score', 0)
    if structure_score < 3:
        recommendations.extend([
            "📝 Přidejte nadpisy pro lepší strukturu",
            "📋 Použijte seznamy pro přehlednost",
            "🔗 Přidejte relevantní odkazy"
        ])
    
    # Doporučení podle typu změny
    change_type = analysis['change_type']
    if change_type == 'expansion':
        recommendations.append("📈 Obsah byl rozšířen - zkontrolujte konzistenci")
    elif change_type == 'reduction':
        recommendations.append("📉 Obsah byl zkrácen - ověřte úplnost informací")
    
    # Obecná doporučení
    recommendations.extend([
        "👀 Zkontrolujte zobrazení v diskuzi",
        "🔍 Ověřte správnost odkazů a formátování",
        "📊 Sledujte reakce ostatních uživatelů",
        "🔄 Pravidelně aktualizujte zastaralé informace"
    ])
    
    return recommendations

def format_edit_statistics(edit_stats):
    """Formátuje statistiky úprav"""
    if not edit_stats:
        return []
    
    stats = []
    chars_added = edit_stats.get('chars_added', 0)
    chars_removed = edit_stats.get('chars_removed', 0)
    lines_changed = edit_stats.get('lines_changed', 0)
    
    stats.append(f"➕ Přidáno znaků: {chars_added}")
    stats.append(f"➖ Odebráno znaků: {chars_removed}")
    stats.append(f"📝 Změněno řádků: {lines_changed}")
    
    # Čistá změna
    net_change = chars_added - chars_removed
    if net_change > 0:
        stats.append(f"📈 Čistý přírůstek: +{net_change} znaků")
    elif net_change < 0:
        stats.append(f"📉 Čistý úbytek: {net_change} znaků")
    else:
        stats.append("⚖️ Vyrovnaná změna")
    
    return stats

def get_next_actions(analysis):
    """Navrhuje další akce"""
    actions = []
    
    # Akce podle oprávnění
    permissions = analysis.get('permissions', {})
    if permissions.get('can_edit', False):
        actions.append("✏️ Další úpravy obsahu")
    if permissions.get('can_delete', False):
        actions.append("🗑️ Smazání obsahu (discussion_delete.py)")
    if permissions.get('can_restore', False):
        actions.append("🔄 Obnovení předchozí verze")
    
    # Obecné akce
    actions.extend([
        "💬 Zobrazit diskuzi (discussion_get.py)",
        "🔍 Zkontrolovat oprávnění (discussion_access_rights_get.py)",
        "📌 Přidat do bookmarků (discussion_bookmark.py)",
        "📊 Sledovat reakce na změny"
    ])
    
    return actions

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
    if not discussion_id or discussion_id == '12345':
        print("Chyba: Nastavte DISCUSSION_ID v secret.txt")
        print("Příklad: DISCUSSION_ID=123456")
        sys.exit(1)
    
    content_id = config.get('CONTENT_ID')
    if not content_id or content_id == '67890':
        print("Chyba: Nastavte CONTENT_ID v secret.txt")
        print("Příklad: CONTENT_ID=789012")
        sys.exit(1)
    
    content_text = config.get('CONTENT_TEXT')
    if not content_text:
        print("Chyba: Nastavte CONTENT_TEXT v secret.txt")
        print("Příklad: CONTENT_TEXT='Upravený obsah nástěnky'")
        sys.exit(1)
    
    content_format = config.get('CONTENT_FORMAT', 'text')
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    
    print("=== NYX.CZ API - Úprava položky na nástěnce ===")
    print(f"URL: {base_url}/discussion/{discussion_id}/content/{content_id}/save")
    print(f"Diskuze ID: {discussion_id}")
    print(f"Obsah ID: {content_id}")
    print(f"Obsah: {content_text}")
    if content_format != 'text':
        print(f"Formát: {content_format}")
    print()
    
    # Příprava požadavku
    url = f"{base_url}/discussion/{discussion_id}/content/{content_id}/save"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Příprava dat
    data = {
        'content': content_text
    }
    
    if content_format and content_format != 'text':
        data['format'] = content_format
    
    try:
        # API požadavek
        response = requests.post(url, headers=headers, data=data)
        
        print(f"HTTP Status: {response.status_code}")
        print()
        
        # Výpis odpovědi
        if response.text:
            try:
                response_data = response.json()
                print(json.dumps(response_data, indent=2, ensure_ascii=False))
                
                # Dodatečné analýzy
                if response.status_code == 200:
                    analysis = analyze_content_update(response_data)
                    
                    print()
                    print("=== Analýza úpravy obsahu ===")
                    print(f"ID obsahu: {analysis['content_id']}")
                    if analysis['updated_at']:
                        print(f"Aktualizováno: {analysis['updated_at']}")
                    print(f"Verze: {analysis['version']}")
                    
                    # Informace o obsahu
                    if analysis['content_info']:
                        print()
                        print("=== Informace o obsahu ===")
                        info = analysis['content_info']
                        print(f"Délka obsahu: {info['length']} znaků")
                        print(f"Počet slov: {info['word_count']}")
                        print(f"Počet řádků: {info['line_count']}")
                        print(f"Formát: {info['format']}")
                        print(f"Náhled: {info['preview']}")
                    
                    # Historie změn
                    if analysis['revision_info']:
                        print()
                        print("=== Historie změn ===")
                        revision = analysis['revision_info']
                        
                        revision_number = revision.get('number', 1)
                        previous_version = revision.get('previous_version', 'žádná')
                        editor = revision.get('editor', 'neznámý')
                        
                        print(f"Číslo revize: {revision_number}")
                        print(f"Předchozí verze: {previous_version}")
                        print(f"Editor: {editor}")
                    
                    # Statistiky úprav
                    if analysis['edit_stats']:
                        print()
                        print("=== Statistiky úprav ===")
                        edit_stats = format_edit_statistics(analysis['edit_stats'])
                        for stat in edit_stats:
                            print(stat)
                        
                        # Typ změny
                        change_types = {
                            'expansion': 'Rozšíření obsahu',
                            'reduction': 'Zkrácení obsahu',
                            'modification': 'Úprava obsahu',
                            'unknown': 'Neznámý typ změny'
                        }
                        change_type = change_types.get(analysis['change_type'], 'Neznámý')
                        print(f"🔄 Typ změny: {change_type}")
                    
                    # Oprávnění
                    if analysis['permissions']:
                        print()
                        print("=== Oprávnění ===")
                        permissions = analysis['permissions']
                        
                        can_edit = permissions.get('can_edit', False)
                        can_delete = permissions.get('can_delete', False)
                        can_restore = permissions.get('can_restore', False)
                        
                        print(f"✏️ Může upravovat: {'Ano' if can_edit else 'Ne'}")
                        print(f"🗑️ Může mazat: {'Ano' if can_delete else 'Ne'}")
                        print(f"🔄 Může obnovit: {'Ano' if can_restore else 'Ne'}")
                    
                    # Validace obsahu
                    if analysis['validation']:
                        print()
                        print("=== Validace obsahu ===")
                        validation = analysis['validation']
                        
                        is_valid = validation.get('is_valid', True)
                        warnings = validation.get('warnings', [])
                        
                        if is_valid:
                            print("✅ Obsah je validní")
                        else:
                            print("⚠️ Obsah má problémy")
                        
                        if warnings:
                            print("Varování:")
                            for warning in warnings:
                                print(f"  - {warning}")
                    
                    # Metriky kvality
                    if analysis['quality_metrics']:
                        print()
                        print("=== Metriky kvality ===")
                        metrics = analysis['quality_metrics']
                        
                        readability = metrics.get('readability', 'unknown')
                        length_cat = metrics.get('length_category', 'unknown')
                        structure_score = metrics.get('structure_score', 0)
                        
                        readability_labels = {
                            'good': 'Dobrá čitelnost',
                            'needs_attention': 'Potřebuje pozornost',
                            'unknown': 'Neznámá'
                        }
                        
                        length_labels = {
                            'very_short': 'Velmi krátký',
                            'short': 'Krátký',
                            'medium': 'Střední',
                            'long': 'Dlouhý',
                            'very_long': 'Velmi dlouhý',
                            'unknown': 'Neznámá'
                        }
                        
                        print(f"📖 Čitelnost: {readability_labels.get(readability, readability)}")
                        print(f"📏 Kategorie délky: {length_labels.get(length_cat, length_cat)}")
                        print(f"🏗️ Skóre struktury: {structure_score}/10")
                    
                    # Doporučení
                    recommendations = get_content_recommendations(analysis)
                    if recommendations:
                        print()
                        print("=== Doporučení ===")
                        for rec in recommendations:
                            print(f"- {rec}")
                    
                    # Tipy pro správu obsahu
                    print()
                    print("=== Tipy pro správu obsahu ===")
                    content_tips = [
                        "📝 Používejte jasné a srozumitelné formátování",
                        "🔄 Pravidelně aktualizujte zastaralé informace",
                        "🔗 Přidávejte relevantní odkazy a zdroje",
                        "📊 Udržujte obsah aktuální a užitečný",
                        "👥 Zohledňujte potřeby čtenářů"
                    ]
                    
                    for tip in content_tips:
                        print(f"- {tip}")
                    
                    # Další akce
                    next_actions = get_next_actions(analysis)
                    if next_actions:
                        print()
                        print("=== Další akce ===")
                        for action in next_actions:
                            print(f"- {action}")
                        
            except json.JSONDecodeError:
                print(response.text)
        
        # Kontrola chyb
        if response.status_code != 200:
            print()
            print("Chyba při úpravě obsahu! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- DISCUSSION_ID v secret.txt")
            print("- CONTENT_ID v secret.txt")
            print("- CONTENT_TEXT v secret.txt")
            
            error_messages = {
                400: "Neplatné ID diskuze nebo obsahu / Neplatný formát obsahu",
                401: "Neplatný nebo chybějící API token",
                403: "Nedostatečná oprávnění pro úpravu obsahu",
                404: "Diskuze nebo obsah neexistuje",
                413: "Obsah je příliš dlouhý",
                422: "Neplatný obsah nebo formát"
            }
            
            if response.status_code in error_messages:
                print(f"- {error_messages[response.status_code]}")
        else:
            print()
            print("✅ Obsah byl úspěšně upraven!")
            
            # Další kroky
            print()
            print("=== Další kroky ===")
            next_steps = [
                "1. 👀 Zkontrolujte zobrazení v diskuzi",
                "2. ✅ Ověřte správnost formátování",
                "3. 👥 Sledujte reakce ostatních uživatelů",
                "4. 🔄 Zvažte další úpravy podle potřeby"
            ]
            
            for step in next_steps:
                print(step)
            
            # Bezpečnostní tipy
            print()
            print("=== Bezpečnostní tipy ===")
            security_tips = [
                "💾 Zálohujte důležitý obsah před úpravami",
                "🔒 Používejte pouze důvěryhodné zdroje",
                "🔍 Ověřujte odkazy před jejich přidáním",
                "©️ Respektujte autorská práva"
            ]
            
            for tip in security_tips:
                print(f"- {tip}")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)
    
    print()
    print("Tip: Pro zobrazení diskuze použijte discussion_get.py")

if __name__ == "__main__":
    main()
