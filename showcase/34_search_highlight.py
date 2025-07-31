#!/usr/bin/env python3
"""
NYX.CZ API - Vyhledávání se zvýrazněním
GET /api/search/highlight
"""

import requests
import json
import sys
import os
from urllib.parse import urlencode
from collections import Counter
import re

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

def analyze_highlight_results(data):
    """Analyzuje výsledky zvýrazněného vyhledávání"""
    results = data.get('results', [])
    total = data.get('total', 0)
    highlight_config = data.get('highlightConfig', {})
    
    analysis = {
        'total_found': total,
        'results_shown': len(results),
        'results_with_fragments': 0,
        'total_fragments': 0,
        'avg_fragment_length': 0,
        'highlighted_terms': {},
        'top_results': [],
        'fragment_stats': {},
        'highlight_config': highlight_config
    }
    
    if not results:
        return analysis
    
    all_fragments = []
    highlighted_terms = []
    
    # Analýza fragmentů
    for result in results:
        fragments = result.get('fragments', [])
        if fragments:
            analysis['results_with_fragments'] += 1
            all_fragments.extend(fragments)
            
            # Extrakce zvýrazněných termínů
            for fragment in fragments:
                # Hledá text mezi tagy (defaultně <em> a </em>)
                pre_tag = highlight_config.get('preTag', '<em>')
                post_tag = highlight_config.get('postTag', '</em>')
                
                # Escapuje speciální znaky pro regex
                pre_escaped = re.escape(pre_tag)
                post_escaped = re.escape(post_tag)
                
                pattern = f'{pre_escaped}(.*?){post_escaped}'
                matches = re.findall(pattern, fragment, re.IGNORECASE)
                highlighted_terms.extend(matches)
    
    analysis['total_fragments'] = len(all_fragments)
    
    # Průměrná délka fragmentů
    if all_fragments:
        fragment_lengths = [len(fragment) for fragment in all_fragments]
        analysis['avg_fragment_length'] = sum(fragment_lengths) / len(fragment_lengths)
        
        # Statistiky fragmentů
        analysis['fragment_stats'] = {
            'min_length': min(fragment_lengths),
            'max_length': max(fragment_lengths),
            'median_length': sorted(fragment_lengths)[len(fragment_lengths)//2]
        }
    
    # Analýza zvýrazněných termínů
    if highlighted_terms:
        # Normalizace termínů (lowercase, strip)
        normalized_terms = [term.lower().strip() for term in highlighted_terms if term.strip()]
        analysis['highlighted_terms'] = dict(Counter(normalized_terms))
    
    # Top výsledky
    analysis['top_results'] = [
        {
            'title': result.get('title', 'Bez názvu'),
            'url': result.get('url', ''),
            'fragments_count': len(result.get('fragments', [])),
            'fragments': result.get('fragments', [])[:3],  # Max 3 fragmenty pro ukázku
            'score': result.get('score', 0)
        }
        for result in results[:5]
    ]
    
    return analysis

def extract_clean_text(html_text):
    """Odstraní HTML tagy z textu"""
    return re.sub(r'<[^>]+>', '', html_text)

def format_highlight_tips(analysis):
    """Generuje tipy pro zvýrazněné vyhledávání"""
    tips = []
    
    if analysis['total_found'] == 0:
        tips.extend([
            "Zkuste obecnější klíčová slova",
            "Ověřte překlepy v dotazu",
            "Použijte synonyma nebo související termíny"
        ])
    elif analysis['results_with_fragments'] == 0:
        tips.extend([
            "Žádné výsledky neobsahují fragmenty",
            "Zkuste jiný dotaz nebo upravte parametry fragmentů"
        ])
    
    # Tipy podle fragmentů
    if analysis['avg_fragment_length'] < 50:
        tips.append("Fragmenty jsou krátké - zvažte zvýšení SEARCH_FRAGMENT_SIZE")
    elif analysis['avg_fragment_length'] > 300:
        tips.append("Fragmenty jsou dlouhé - zvažte snížení SEARCH_FRAGMENT_SIZE")
    
    if analysis['total_fragments'] < 10:
        tips.append("Málo fragmentů - zvažte zvýšení SEARCH_MAX_FRAGMENTS")
    
    # Obecné tipy
    tips.extend([
        "Upravte SEARCH_PRE_TAG a SEARCH_POST_TAG pro vlastní styling",
        "Kombinujte s dalšími vyhledávacími endpointy",
        "Použijte fragmenty pro vytvoření náhledů výsledků"
    ])
    
    return tips

def main():
    # Načtení konfigurace
    config = load_config()
    
    # Kontrola API tokenu
    api_token = config.get('NYX_API_TOKEN')
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    # Kontrola vyhledávacího dotazu
    search_query = config.get('SEARCH_QUERY')
    if not search_query:
        print("Chyba: Nastavte SEARCH_QUERY v secret.txt")
        sys.exit(1)
    
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    
    # Sestavení parametrů
    params = {'q': search_query}
    
    # Přidání volitelných parametrů
    optional_params = {
        'limit': config.get('SEARCH_LIMIT'),
        'offset': config.get('SEARCH_OFFSET'),
        'fragmentSize': config.get('SEARCH_FRAGMENT_SIZE'),
        'maxFragments': config.get('SEARCH_MAX_FRAGMENTS'),
        'preTag': config.get('SEARCH_PRE_TAG'),
        'postTag': config.get('SEARCH_POST_TAG')
    }
    
    for key, value in optional_params.items():
        if value:
            params[key] = value
    
    # Sestavení URL
    url = f"{base_url}/search/highlight"
    query_string = urlencode(params)
    full_url = f"{url}?{query_string}"
    
    print("=== NYX.CZ API - Vyhledávání se zvýrazněním ===")
    print(f"URL: {full_url}")
    print(f"Dotaz: {search_query}")
    print()
    
    # Příprava požadavku
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # API požadavek
        response = requests.get(url, headers=headers, params=params)
        
        print(f"HTTP Status: {response.status_code}")
        print()
        
        # Výpis odpovědi
        if response.text:
            try:
                data = response.json()
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # Dodatečné analýzy
                if response.status_code == 200:
                    analysis = analyze_highlight_results(data)
                    
                    print()
                    print("=== Analýza zvýrazněného vyhledávání ===")
                    print(f"Celkem nalezeno: {analysis['total_found']} výsledků")
                    print(f"Zobrazeno: {analysis['results_shown']} výsledků")
                    
                    # Analýza fragmentů
                    print()
                    print("=== Analýza fragmentů ===")
                    print(f"Výsledky s fragmenty: {analysis['results_with_fragments']}")
                    print(f"Celkový počet fragmentů: {analysis['total_fragments']}")
                    
                    if analysis['avg_fragment_length'] > 0:
                        print(f"Průměrná délka fragmentu: {analysis['avg_fragment_length']:.1f} znaků")
                        
                        stats = analysis['fragment_stats']
                        print(f"Nejkratší fragment: {stats['min_length']} znaků")
                        print(f"Nejdelší fragment: {stats['max_length']} znaků")
                        print(f"Medián délky: {stats['median_length']} znaků")
                    
                    # Top výsledky s fragmenty
                    if analysis['top_results']:
                        print()
                        print("=== Top výsledky s fragmenty ===")
                        for i, result in enumerate(analysis['top_results'], 1):
                            if result['fragments_count'] > 0:
                                print(f"{i}. {result['title']} ({result['fragments_count']} fragmentů)")
                                if result['score']:
                                    print(f"   Skóre: {result['score']}")
                    
                    # Ukázka zvýrazněných fragmentů
                    if analysis['total_fragments'] > 0:
                        print()
                        print("=== Ukázka zvýrazněných fragmentů ===")
                        fragment_count = 0
                        for result in analysis['top_results'][:3]:
                            for fragment in result['fragments']:
                                if fragment_count >= 5:  # Max 5 fragmentů
                                    break
                                clean_fragment = extract_clean_text(fragment)
                                print(f"- {clean_fragment[:150]}...")
                                fragment_count += 1
                            if fragment_count >= 5:
                                break
                    
                    # Analýza zvýrazněných termínů
                    if analysis['highlighted_terms']:
                        print()
                        print("=== Analýza zvýrazněných termínů ===")
                        print("Nejčastější zvýrazněné termíny:")
                        
                        # Seřadí podle četnosti
                        sorted_terms = sorted(analysis['highlighted_terms'].items(), 
                                            key=lambda x: x[1], reverse=True)
                        
                        for term, count in sorted_terms[:10]:  # Top 10 termínů
                            print(f"- {term}: {count} výskytů")
                    
                    # Konfigurace zvýrazňování
                    config_info = analysis['highlight_config']
                    if config_info:
                        print()
                        print("=== Konfigurace zvýrazňování ===")
                        print(f"Počáteční tag: {config_info.get('preTag', '<em>')}")
                        print(f"Koncový tag: {config_info.get('postTag', '</em>')}")
                        print(f"Velikost fragmentu: {config_info.get('fragmentSize', 'výchozí')}")
                        print(f"Max fragmentů: {config_info.get('maxFragments', 'výchozí')}")
                    
                    # Tipy pro optimalizaci
                    tips = format_highlight_tips(analysis)
                    if tips:
                        print()
                        print("=== Tipy pro zvýrazněné vyhledávání ===")
                        for tip in tips[:6]:
                            print(f"- {tip}")
                    
                    # Hodnocení kvality zvýraznění
                    print()
                    print("=== Hodnocení kvality zvýraznění ===")
                    if analysis['results_with_fragments'] == 0:
                        print("🔴 Žádné fragmenty nenalezeny")
                    elif analysis['results_with_fragments'] / max(analysis['results_shown'], 1) > 0.8:
                        print("🟢 Vysoká kvalita zvýraznění")
                    elif analysis['results_with_fragments'] / max(analysis['results_shown'], 1) > 0.5:
                        print("🟡 Střední kvalita zvýraznění")
                    else:
                        print("🔴 Nízká kvalita zvýraznění")
                        
            except json.JSONDecodeError:
                print(response.text)
        
        # Kontrola chyb
        if response.status_code != 200:
            print()
            print("Chyba v požadavku! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- SEARCH_QUERY v secret.txt")
            
            if response.status_code == 400:
                print("- Neplatný formát dotazu nebo parametrů")
                print("- Zkontrolujte SEARCH_FRAGMENT_SIZE a SEARCH_MAX_FRAGMENTS")
            elif response.status_code == 401:
                print("- Neplatný nebo chybějící API token")
            elif response.status_code == 429:
                print("- Příliš mnoho požadavků - zkuste později")
        else:
            print()
            print("✓ Vyhledávání se zvýrazněním úspěšně dokončeno!")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)
    
    print()
    print("Tip: Pro jiné typy vyhledávání použijte search_v2.py nebo search_unified.py")

if __name__ == "__main__":
    main()
