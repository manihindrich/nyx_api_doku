#!/usr/bin/env python3
"""
NYX.CZ API - Sjednocené vyhledávání
GET /api/search/unified
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

def analyze_unified_results(data):
    """Analyzuje výsledky sjednoceného vyhledávání"""
    results = data.get('results', [])
    total = data.get('total', 0)
    
    analysis = {
        'total_found': total,
        'results_shown': len(results),
        'sources': {},
        'content_types': {},
        'relevance_scores': [],
        'top_results': [],
        'highlights_count': 0,
        'avg_relevance': 0,
        'max_relevance': 0,
        'min_relevance': 0,
        'search_time': data.get('searchTime'),
        'suggestions': data.get('suggestions', [])
    }
    
    if not results:
        return analysis
    
    # Analýza zdrojů
    sources = [result.get('source', 'neznámý') for result in results]
    analysis['sources'] = dict(Counter(sources))
    
    # Analýza typů obsahu
    content_types = [result.get('contentType', 'neznámý') for result in results]
    analysis['content_types'] = dict(Counter(content_types))
    
    # Analýza relevance
    relevance_scores = [result.get('relevance', 0) for result in results if result.get('relevance') is not None]
    if relevance_scores:
        analysis['relevance_scores'] = relevance_scores
        analysis['avg_relevance'] = sum(relevance_scores) / len(relevance_scores)
        analysis['max_relevance'] = max(relevance_scores)
        analysis['min_relevance'] = min(relevance_scores)
    
    # Top výsledky
    analysis['top_results'] = [
        {
            'title': result.get('title', 'Bez názvu'),
            'source': result.get('source', 'neznámý'),
            'content_type': result.get('contentType', 'neznámý'),
            'relevance': result.get('relevance', 0),
            'url': result.get('url', ''),
            'description': result.get('description', '')[:150] + '...' if result.get('description') else '',
            'highlights': result.get('highlights', [])
        }
        for result in results[:5]
    ]
    
    # Počet výsledků se zvýrazněním
    analysis['highlights_count'] = len([r for r in results if r.get('highlights')])
    
    return analysis

def extract_highlight_terms(highlights):
    """Extrahuje zvýrazněné termíny z HTML"""
    terms = []
    for highlight in highlights:
        # Najde text mezi <mark> tagy nebo podobnými
        matches = re.findall(r'<(?:mark|em|strong)[^>]*>(.*?)</(?:mark|em|strong)>', highlight, re.IGNORECASE)
        terms.extend(matches)
    return list(set(terms))  # Unikátní termíny

def format_unified_tips(analysis):
    """Generuje tipy pro sjednocené vyhledávání"""
    tips = []
    
    if analysis['total_found'] == 0:
        tips.extend([
            "Zkuste obecnější klíčová slova",
            "Ověřte překlepy v dotazu",
            "Použijte synonyma nebo související termíny"
        ])
    elif analysis['total_found'] < 10:
        tips.extend([
            "Zkuste kratší nebo obecnější dotaz",
            "Použijte méně specifické filtry"
        ])
    
    # Tipy podle zdrojů
    if len(analysis['sources']) == 1:
        tips.append("Výsledky pocházejí pouze z jednoho zdroje - zkuste obecnější dotaz")
    elif len(analysis['sources']) > 5:
        tips.append("Výsledky z mnoha zdrojů - zvažte zúžení dotazu")
    
    # Tipy podle relevance
    if analysis['relevance_scores'] and analysis['max_relevance'] < 0.5:
        tips.append("Nízká relevance výsledků - zkuste přesnější klíčová slova")
    
    # Obecné tipy
    tips.extend([
        "Využijte zvýrazňování pro lepší orientaci",
        "Kombinujte s dalšími vyhledávacími endpointy",
        "Použijte stránkování pro procházení všech výsledků"
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
        'includeContent': config.get('SEARCH_INCLUDE_CONTENT'),
        'highlight': config.get('SEARCH_HIGHLIGHT')
    }
    
    for key, value in optional_params.items():
        if value:
            params[key] = value
    
    # Sestavení URL
    url = f"{base_url}/search/unified"
    query_string = urlencode(params)
    full_url = f"{url}?{query_string}"
    
    print("=== NYX.CZ API - Sjednocené vyhledávání ===")
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
                    analysis = analyze_unified_results(data)
                    
                    print()
                    print("=== Analýza sjednoceného vyhledávání ===")
                    print(f"Celkem nalezeno: {analysis['total_found']} výsledků")
                    print(f"Zobrazeno: {analysis['results_shown']} výsledků")
                    
                    # Zdroje výsledků
                    if analysis['sources']:
                        print()
                        print("=== Zdroje výsledků ===")
                        for source, count in analysis['sources'].items():
                            print(f"- {source}: {count} výsledků")
                    
                    # Typy obsahu
                    if analysis['content_types']:
                        print()
                        print("=== Typy obsahu ===")
                        for content_type, count in analysis['content_types'].items():
                            print(f"- {content_type}: {count} výsledků")
                    
                    # Top výsledky
                    if analysis['top_results']:
                        print()
                        print("=== Top 5 výsledků ===")
                        for i, result in enumerate(analysis['top_results'], 1):
                            print(f"{i}. {result['title']} [{result['source']}]")
                            print(f"   Relevance: {result['relevance']:.3f}")
                            if result['description']:
                                print(f"   Popis: {result['description']}")
                            if result['highlights']:
                                highlight_terms = extract_highlight_terms(result['highlights'])
                                if highlight_terms:
                                    print(f"   Zvýrazněné termíny: {', '.join(highlight_terms[:3])}")
                    
                    # Zvýrazněné úryvky
                    if analysis['highlights_count'] > 0:
                        print()
                        print("=== Zvýrazněné úryvky ===")
                        print(f"Počet výsledků se zvýrazněním: {analysis['highlights_count']}")
                        
                        # Ukázka prvních zvýraznění
                        sample_highlights = []
                        for result in analysis['top_results'][:3]:
                            if result['highlights']:
                                sample_highlights.extend(result['highlights'][:1])
                        
                        for highlight in sample_highlights:
                            # Odstraň HTML tagy pro čitelnější výpis
                            clean_highlight = re.sub(r'<[^>]+>', '', highlight)
                            print(f"- {clean_highlight[:100]}...")
                    
                    # Statistiky relevance
                    if analysis['relevance_scores']:
                        print()
                        print("=== Statistiky relevance ===")
                        print(f"Nejvyšší relevance: {analysis['max_relevance']:.3f}")
                        print(f"Nejnižší relevance: {analysis['min_relevance']:.3f}")
                        print(f"Průměrná relevance: {analysis['avg_relevance']:.3f}")
                        
                        # Hodnocení kvality výsledků
                        if analysis['avg_relevance'] > 0.8:
                            print("🟢 Vysoká kvalita výsledků")
                        elif analysis['avg_relevance'] > 0.5:
                            print("🟡 Střední kvalita výsledků")
                        else:
                            print("🔴 Nízká kvalita výsledků")
                    
                    # Výkon vyhledávání
                    if analysis['search_time']:
                        print()
                        print("=== Výkon vyhledávání ===")
                        print(f"Čas vyhledávání: {analysis['search_time']}ms")
                        
                        if analysis['search_time'] < 100:
                            print("⚡ Velmi rychlé vyhledávání")
                        elif analysis['search_time'] < 500:
                            print("🚀 Rychlé vyhledávání")
                        else:
                            print("🐌 Pomalé vyhledávání")
                    
                    # Návrhy pro zlepšení
                    if analysis['suggestions']:
                        print()
                        print("=== Návrhy pro zlepšení ===")
                        for suggestion in analysis['suggestions']:
                            print(f"- {suggestion}")
                    
                    # Tipy pro optimalizaci
                    tips = format_unified_tips(analysis)
                    if tips:
                        print()
                        print("=== Tipy pro optimalizaci ===")
                        for tip in tips[:5]:
                            print(f"- {tip}")
                    
                    # Výhody sjednoceného vyhledávání
                    print()
                    print("=== Výhody sjednoceného vyhledávání ===")
                    print("- Prohledává všechny dostupné zdroje současně")
                    print("- Poskytuje jednotný formát výsledků")
                    print("- Automaticky řadí podle relevance")
                    print("- Podporuje zvýrazňování nalezených termínů")
                        
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
            elif response.status_code == 401:
                print("- Neplatný nebo chybějící API token")
            elif response.status_code == 429:
                print("- Příliš mnoho požadavků - zkuste později")
        else:
            print()
            print("✓ Sjednocené vyhledávání úspěšně dokončeno!")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)
    
    print()
    print("Tip: Pro specifické vyhledávání použijte search_v2.py nebo search_highlight.py")

if __name__ == "__main__":
    main()
