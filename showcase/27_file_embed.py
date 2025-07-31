#!/usr/bin/env python3
"""
NYX.CZ API - Vložení/odebrání souboru do obsahu
POST /api/file/embed/{id}/{state}
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

def analyze_embed_operation(data, state):
    """Analyzuje výsledek operace vložení"""
    analysis = {
        'file_id': data.get('fileId', data.get('id', 'neznámé')),
        'file_name': data.get('filename', data.get('name', 'neznámý')),
        'is_embedded': data.get('embedded', data.get('isEmbedded', False)),
        'content_id': data.get('contentId'),
        'position': data.get('position'),
        'embed_type': data.get('embedType', 'neznámý'),
        'caption': data.get('caption'),
        'alt_text': data.get('altText'),
        'embed_date': data.get('embeddedAt', data.get('createdAt')),
        'usage_count': data.get('usageCount', 0),
        'total_embeds': data.get('totalEmbeds', 0),
        'embedded_in': data.get('embeddedIn', []),
        'mime_type': data.get('mimeType', data.get('contentType', 'neznámý')),
        'operation': state
    }
    
    return analysis

def get_file_type_recommendations(mime_type):
    """Vrací doporučení podle typu souboru"""
    recommendations = {
        'image': [
            "🖼️ Zkontrolujte rozlišení a velikost",
            "🎨 Nastavte vhodný alt text pro přístupnost",
            "📱 Zvažte responzivní zobrazení",
            "🔍 Optimalizujte pro rychlé načítání"
        ],
        'video': [
            "🎬 Ověřte kompatibilitu s různými prohlížeči",
            "🖼️ Nastavte náhledový obrázek",
            "📝 Zvažte titulky pro přístupnost",
            "⚡ Optimalizujte velikost souboru"
        ],
        'audio': [
            "🎵 Poskytněte ovládací prvky",
            "📝 Zvažte transkript pro přístupnost",
            "🔊 Zkontrolujte kvalitu zvuku",
            "📱 Otestujte na mobilních zařízeních"
        ],
        'document': [
            "📄 Ověřte čitelnost na mobilních zařízeních",
            "🔄 Zvažte alternativní formáty",
            "🔍 Zkontrolujte velikost souboru",
            "📋 Poskytněte popis obsahu"
        ],
        'other': [
            "📁 Ověřte správné zobrazení odkazu",
            "📝 Nastavte popisný text",
            "🔍 Zkontrolujte dostupnost souboru",
            "💾 Ověřte kompatibilitu"
        ]
    }
    
    if mime_type.startswith('image/'):
        return recommendations['image']
    elif mime_type.startswith('video/'):
        return recommendations['video']
    elif mime_type.startswith('audio/'):
        return recommendations['audio']
    elif mime_type == 'application/pdf' or mime_type.startswith('application/'):
        return recommendations['document']
    else:
        return recommendations['other']

def format_embed_tips(analysis):
    """Generuje tipy pro vložení souboru"""
    tips = []
    
    # Tipy podle operace
    if analysis['operation'] == 'embed' and analysis['is_embedded']:
        tips.append("✅ Soubor byl úspěšně vložen")
    elif analysis['operation'] == 'remove' and not analysis['is_embedded']:
        tips.append("✅ Soubor byl úspěšně odebrán")
    elif analysis['operation'] == 'toggle':
        status = "vložen" if analysis['is_embedded'] else "odebrán"
        tips.append(f"✅ Stav souboru byl přepnut na: {status}")
    
    # Tipy podle použití
    if analysis['usage_count'] > 5:
        tips.append("📊 Soubor je často používán - buďte opatrní při změnách")
    elif analysis['usage_count'] == 0:
        tips.append("💡 Soubor zatím není nikde použit")
    
    # Tipy podle typu
    if analysis['mime_type'].startswith('image/') and not analysis['alt_text']:
        tips.append("⚠️ Doporučujeme nastavit alt text pro obrázky")
    
    if analysis['embed_type'] == 'inline' and analysis['mime_type'].startswith('video/'):
        tips.append("🎬 Video vložené inline může ovlivnit rychlost stránky")
    
    return tips

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
    
    # Kontrola stavu vložení
    embed_state = config.get('FILE_EMBED_STATE')
    if not embed_state:
        print("Chyba: Nastavte FILE_EMBED_STATE v secret.txt")
        print("Možné hodnoty: embed, remove, toggle")
        sys.exit(1)
    
    # Validace stavu
    valid_states = ['embed', 'remove', 'toggle']
    if embed_state not in valid_states:
        print(f"Chyba: Neplatný FILE_EMBED_STATE '{embed_state}'")
        print(f"Povolené hodnoty: {', '.join(valid_states)}")
        sys.exit(1)
    
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    
    print("=== NYX.CZ API - Vložení/odebrání souboru ===")
    print(f"URL: {base_url}/file/embed/{file_id}/{embed_state}")
    print(f"ID souboru: {file_id}")
    print(f"Akce: {embed_state}")
    print()
    
    # Zobrazení akce
    action_messages = {
        'embed': "📎 Vkládání souboru do obsahu...",
        'remove': "🗑️ Odebírání souboru z obsahu...",
        'toggle': "🔄 Přepínání stavu vložení souboru..."
    }
    print(action_messages.get(embed_state, "🔧 Provádění operace..."))
    
    # Příprava požadavku
    url = f"{base_url}/file/embed/{file_id}/{embed_state}"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    # Příprava dat
    data = {}
    
    # Přidání volitelných parametrů
    optional_params = {
        'contentId': config.get('FILE_CONTENT_ID'),
        'position': config.get('FILE_POSITION'),
        'caption': config.get('FILE_CAPTION'),
        'altText': config.get('FILE_ALT_TEXT')
    }
    
    for key, value in optional_params.items():
        if value:
            data[key] = value
    
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
                
                # Dodatečné analýzy
                if response.status_code == 200:
                    analysis = analyze_embed_operation(response_data, embed_state)
                    
                    print()
                    print("=== Analýza vložení souboru ===")
                    print(f"ID souboru: {analysis['file_id']}")
                    print(f"Název souboru: {analysis['file_name']}")
                    
                    # Stav vložení
                    if analysis['is_embedded']:
                        print("✅ Soubor je vložen do obsahu")
                    else:
                        print("❌ Soubor není vložen do obsahu")
                    
                    # Informace o vložení
                    if analysis['content_id']:
                        print(f"ID obsahu: {analysis['content_id']}")
                    
                    if analysis['position']:
                        print(f"Pozice: {analysis['position']}")
                    
                    if analysis['embed_type'] != 'neznámý':
                        print(f"Typ vložení: {analysis['embed_type']}")
                    
                    # Metadata vložení
                    print()
                    print("=== Metadata vložení ===")
                    print(f"Popisek: {analysis['caption'] or 'žádný'}")
                    print(f"Alt text: {analysis['alt_text'] or 'žádný'}")
                    
                    if analysis['embed_date']:
                        print(f"Datum vložení: {analysis['embed_date']}")
                    
                    # Statistiky použití
                    if analysis['usage_count'] > 0 or analysis['total_embeds'] > 0:
                        print()
                        print("=== Statistiky použití ===")
                        print(f"Počet použití: {analysis['usage_count']}")
                        print(f"Celkem vložení: {analysis['total_embeds']}")
                    
                    # Seznam obsahů s vložením
                    if analysis['embedded_in']:
                        print()
                        print("=== Obsahy s vložením ===")
                        for i, content in enumerate(analysis['embedded_in'][:5], 1):
                            title = content.get('title', 'Bez názvu')
                            content_id = content.get('id', 'neznámé')
                            print(f"{i}. {title} (ID: {content_id})")
                        
                        if len(analysis['embedded_in']) > 5:
                            remaining = len(analysis['embedded_in']) - 5
                            print(f"... a dalších {remaining} obsahů")
                    
                    # Doporučení podle typu souboru
                    recommendations = get_file_type_recommendations(analysis['mime_type'])
                    if recommendations:
                        print()
                        print("=== Doporučení pro typ souboru ===")
                        file_category = "Obrázek" if analysis['mime_type'].startswith('image/') else \
                                      "Video" if analysis['mime_type'].startswith('video/') else \
                                      "Audio" if analysis['mime_type'].startswith('audio/') else \
                                      "Dokument" if analysis['mime_type'] == 'application/pdf' else \
                                      "Soubor"
                        print(f"{file_category}:")
                        for rec in recommendations:
                            print(f"- {rec}")
                    
                    # Tipy pro optimalizaci
                    tips = format_embed_tips(analysis)
                    if tips:
                        print()
                        print("=== Tipy pro optimalizaci ===")
                        for tip in tips:
                            print(f"- {tip}")
                    
                    # Další kroky
                    print()
                    print("=== Další kroky ===")
                    next_steps = [
                        "🔍 Zkontrolujte zobrazení v cílovém obsahu",
                        "📱 Ověřte funkčnost na různých zařízeních",
                        "♿ Otestujte přístupnost (alt text, titulky)",
                        "🗑️ Použijte file_delete.py pro smazání nepotřebných souborů"
                    ]
                    
                    for step in next_steps:
                        print(f"- {step}")
                        
            except json.JSONDecodeError:
                print(response.text)
        
        # Kontrola chyb
        if response.status_code != 200:
            print()
            print("Chyba při operaci! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- FILE_ID v secret.txt")
            print("- FILE_EMBED_STATE v secret.txt")
            
            error_messages = {
                400: "Neplatné ID souboru nebo stav / Neplatné parametry",
                401: "Neplatný nebo chybějící API token",
                403: "Nedostatečná oprávnění pro úpravu",
                404: f"Soubor s ID '{file_id}' neexistuje nebo obsah neexistuje",
                409: "Konflikt při vkládání (soubor již vložen) / Neplatná pozice"
            }
            
            if response.status_code in error_messages:
                print(f"- {error_messages[response.status_code]}")
        else:
            # Zpráva o úspěchu
            success_messages = {
                'embed': "✅ Soubor byl úspěšně vložen do obsahu!",
                'remove': "✅ Soubor byl úspěšně odebrán z obsahu!",
                'toggle': "✅ Stav vložení souboru byl úspěšně přepnut!"
            }
            print()
            print(success_messages.get(embed_state, "✅ Operace byla úspěšně dokončena!"))
            
            # Statistiky operace
            print()
            print("=== Statistiky operace ===")
            print(f"ID souboru: {file_id}")
            print(f"Provedená akce: {embed_state}")
            print(f"Čas operace: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)
    
    print()
    print("Tip: Pro správu souborů použijte file_upload.py nebo file_delete.py")

if __name__ == "__main__":
    main()
