#!/usr/bin/env python3
"""
NYX.CZ API - Pokročilé vyhledávání v2
GET /api/search-v2
"""

import requests
import json
import sys
import os
from urllib.parse import urlencode
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
                    config[key.strip()] = value.strip()
    except FileNotFoundError:
        print("Chyba: Soubor secret.txt nenalezen!")
        print("Zkopírujte dummy-secret.txt jako secret.txt a vyplňte hodnoty.")
        sys.exit(1)
    return config

def analyze_search_results(data):
    """Analyzuje výsledky vyhledávání"""
    results = data.get('results', [])
    total = data.get('total', 0)
    
    analysis = {
        'total_found': total,
        'results_shown': len(results),
        'types': {},
        'scores': [],
        'top_results': [],
        'categories': {},
        'avg_score': 0,
        'max_score': 0,
        'min_score': 0
    }
    
    if not results:
        return analysis
    
    # Analýza typů
    types = [result.get('type', 'neznámý') for result in results]
    analysis['types'] = dict(Counter(types))
    
    # Analýza skóre
    scores = [result.get('score', 0) for result in results if result.get('score') is not None]
    if scores:
        analysis['scores'] = scores
        analysis['avg_score'] = sum(scores) / len(scores)
        analysis['max_score'] = max(scores)
        analysis['min_score'] = min(scores)
    
    # Top výsledky
    analysis['top_results'] = [
        {
            'title': result.get('title', result.get('name', 'Bez názvu')),
            'type': result.get('type', 'neznámý'),
            'score': result.get('score', 0),
            'url': result.get('url', ''),
            'description': result.get('description', '')[:100] + '...' if result.get('description') else ''
        }
        for result in results[:5]
    ]
    
    # Analýza kategorií
    categories = [result.get('category', 'nezařazeno') for result in results if result.get('category')]
    if categories:
        analysis['categories'] = dict(Counter(categories))
    
    return analysis

def format_search_tips(query, results_count):
    """Generuje tipy pro lepší vyhledávání"""
    tips = []
    
    if results_count == 0:
        tips.extend([
            "Zkuste kratší nebo obecnější klíčová slova",
            "Ověřte překlepy v dotazu",
            "Použijte synonyma nebo související termíny",
            "Zkuste vyhledávání bez diakritiky"
        ])
    elif results_count < 5:
        tips.extend([
            "Zkuste obecnější termíny pro více výsledků",
            "Použijte méně specifické filtry",
            "Zkombinujte různé klíčová slova"
        ])
    elif results_count > 100:
        tips.extend([
            "Použijte specifičtější klíčová slova",
            "Přidejte filtry pro zúžení výsledků",
            "Využijte pokročilé vyhledávací operátory"
        ])
    
    # Obecné tipy
    tips.extend([
        "Použijte různé typy vyhledávání (type parameter)",
        "Využijte filtrování podle kategorií",
        "Pro velké množství výsledků použijte stránkování"
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
        'type': config.get('SEARCH_TYPE'),
        'limit': config.get('SEARCH_LIMIT'),
        'offset': config.get('SEARCH_OFFSET'),
        'sort': config.get('SEARCH_SORT'),
        'category': config.get('SEARCH_CATEGORY')
    }
    
    for key, value in optional_params.items():
        if value:
            params[key] = value
    
    # Sestavení URL
    url = f"{base_url}/search-v2"
    query_string = urlencode(params)
    full_url = f"{url}?{query_string}"
    
    print("=== NYX.CZ API - Pokročilé vyhledávání v2 ===")
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
                    analysis = analyze_search_results(data)
                    
                    print()
                    print("=== Analýza výsledků vyhledávání ===")
                    print(f"Celkem nalezeno: {analysis['total_found']} výsledků")
                    print(f"Zobrazeno: {analysis['results_shown']} výsledků")
                    
                    # Typy výsledků
                    if analysis['types']:
                        print()
                        print("=== Typy výsledků ===")
                        for result_type, count in analysis['types'].items():
                            print(f"- {result_type}: {count} výsledků")
                    
                    # Top výsledky
                    if analysis['top_results']:
                        print()
                        print("=== Top 5 výsledků ===")
                        for i, result in enumerate(analysis['top_results'], 1):
                            print(f"{i}. {result['title']} ({result['type']})")
                            if result['score']:
                                print(f"   Skóre: {result['score']}")
                            if result['description']:
                                print(f"   Popis: {result['description']}")
                    
                    # Statistiky skóre
                    if analysis['scores']:
                        print()
                        print("=== Statistiky relevance ===")
                        print(f"Nejvyšší skóre: {analysis['max_score']:.2f}")
                        print(f"Nejnižší skóre: {analysis['min_score']:.2f}")
                        print(f"Průměrné skóre: {analysis['avg_score']:.2f}")
                    
                    # Kategorie
                    if analysis['categories']:
                        print()
                        print("=== Kategorie ===")
                        for category, count in analysis['categories'].items():
                            print(f"- {category}: {count} výsledků")
                    
                    # Stránkování
                    pagination = data.get('pagination', {})
                    if pagination:
                        print()
                        print("=== Stránkování ===")
                        current_page = pagination.get('currentPage', 1)
                        total_pages = pagination.get('totalPages', 1)
                        print(f"Aktuální stránka: {current_page} z {total_pages}")
                        
                        if current_page < total_pages:
                            print(f"💡 Pro další výsledky nastavte SEARCH_OFFSET={analysis['results_shown']}")
                    
                    # Doporučení
                    tips = format_search_tips(search_query, analysis['total_found'])
                    if tips:
                        print()
                        print("=== Tipy pro lepší vyhledávání ===")
                        for tip in tips[:5]:  # Zobraz max 5 tipů
                            print(f"- {tip}")
                    
                    # Výkonnostní metriky
                    print()
                    print("=== Výkonnostní metriky ===")
                    print(f"Počet parametrů: {len(params)}")
                    print(f"Délka dotazu: {len(search_query)} znaků")
                    print(f"Efektivita: {(analysis['results_shown']/max(analysis['total_found'], 1)*100):.1f}% zobrazeno")
                        
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
            print("✓ Vyhledávání úspěšně dokončeno!")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)
    
    print()
    print("Tip: Pro jiné typy vyhledávání použijte search_unified.py nebo search_highlight.py")

if __name__ == "__main__":
    main()
