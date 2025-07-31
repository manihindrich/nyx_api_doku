#!/usr/bin/env python3
"""
NYX.CZ API - Získání diskuze
GET /api/discussion/{discussionId}
"""

import requests
import json
import sys
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

def analyze_discussion(discussion_data):
    """Analyzuje data diskuze a vrátí statistiky"""
    if not discussion_data or 'posts' not in discussion_data:
        return {}
    
    posts = discussion_data['posts']
    if not posts:
        return {'posts_count': 0}
    
    # Základní statistiky
    posts_count = len(posts)
    
    # Analýza autorů
    authors = [post.get('author', {}).get('username', 'Neznámý') for post in posts]
    author_counts = Counter(authors)
    
    # Rating statistiky
    ratings = [post.get('rating', 0) for post in posts]
    total_rating = sum(ratings)
    avg_rating = total_rating / len(ratings) if ratings else 0
    
    # Nejnovější příspěvek
    latest_post = posts[0] if posts else None
    
    return {
        'posts_count': posts_count,
        'authors': author_counts,
        'total_rating': total_rating,
        'avg_rating': avg_rating,
        'latest_post': latest_post
    }

def main():
    print("=== NYX.CZ API - Získání diskuze ===")
    
    # Načtení konfigurace
    config = load_config()
    
    api_token = config.get('NYX_API_TOKEN')
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    discussion_id = config.get('DISCUSSION_ID')
    
    # Kontrola API tokenu
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    # Kontrola DISCUSSION_ID
    if not discussion_id:
        print("Chyba: Nastavte DISCUSSION_ID v secret.txt")
        sys.exit(1)
    
    url = f"{base_url}/discussion/{discussion_id}"
    print(f"URL: {url}")
    print(f"Discussion ID: {discussion_id}")
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
                    discussion_data = response_data['data']
                    stats = analyze_discussion(discussion_data)
                    
                    print()
                    print("=== Statistiky diskuze ===")
                    
                    title = discussion_data.get('title', 'N/A')
                    print(f"Název: {title}")
                    print(f"Počet příspěvků: {stats['posts_count']}")
                    
                    if stats['posts_count'] > 0:
                        print()
                        print("Autoři příspěvků:")
                        for author, count in stats['authors'].most_common():
                            print(f"  {count:3d} {author}")
                        
                        if stats['latest_post']:
                            latest_content = stats['latest_post'].get('content', 'N/A')[:100]
                            print()
                            print("Nejnovější příspěvek (prvních 100 znaků):")
                            print(f"{latest_content}...")
                        
                        print()
                        print(f"Celkový rating: {stats['total_rating']}")
                        print(f"Průměrný rating: {stats['avg_rating']:.2f}")
                        
                        # Dodatečné analýzy
                        print()
                        print("=== Dodatečné analýzy ===")
                        print(f"Nejaktivnější autor: {stats['authors'].most_common(1)[0][0]} ({stats['authors'].most_common(1)[0][1]} příspěvků)")
                        print(f"Průměrná délka příspěvku: {sum(len(post.get('content', '')) for post in discussion_data['posts']) / len(discussion_data['posts']):.1f} znaků")
                
            except json.JSONDecodeError:
                print(response.text)
        
        # Kontrola chyb
        if response.status_code != 200:
            print()
            print("Chyba v požadavku! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- DISCUSSION_ID v secret.txt")
            print("- Existenci diskuze s daným ID")
            
            if response.status_code == 404:
                print(f"- Diskuze s ID {discussion_id} neexistuje")
            elif response.status_code == 403:
                print("- Nedostatečná oprávnění pro přístup k diskuzi")
        else:
            print()
            print("✓ Diskuze byla úspěšně načtena!")
            print()
            print("Tip: Pro odeslání příspěvku použijte: python3 discussion_send.py")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
