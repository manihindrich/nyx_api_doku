#!/usr/bin/env python3
"""
NYX.CZ API - Načtení hodnocení příspěvku
GET /api/discussion/{discussion_id}/rating/{id}
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
                    config[key.strip()] = value.strip()
    except FileNotFoundError:
        print("Chyba: Soubor secret.txt nenalezen!")
        print("Zkopírujte dummy-secret.txt jako secret.txt a vyplňte hodnoty.")
        sys.exit(1)
    return config

def analyze_rating_data(data):
    """Analyzuje data hodnocení"""
    analysis = {
        'total_rating': data.get('rating', 0),
        'positive_count': data.get('positive_count', 0),
        'negative_count': data.get('negative_count', 0),
        'my_rating': data.get('my_rating', 'none'),
        'raters': data.get('raters', []),
        'friends_rating': data.get('friends_rating', {}),
        'last_rated_at': data.get('last_rated_at'),
        'rating_distribution': {},
        'quality_assessment': '',
        'engagement_metrics': {}
    }
    
    # Analýza distribuce hodnocení
    if analysis['raters']:
        rating_types = [rater.get('rating_type', 'unknown') for rater in analysis['raters']]
        analysis['rating_distribution'] = dict(Counter(rating_types))
    
    # Hodnocení kvality
    total_rating = analysis['total_rating']
    if total_rating > 5:
        analysis['quality_assessment'] = 'Velmi dobré hodnocení'
    elif total_rating > 0:
        analysis['quality_assessment'] = 'Pozitivní hodnocení'
    elif total_rating == 0:
        analysis['quality_assessment'] = 'Neutrální hodnocení'
    else:
        analysis['quality_assessment'] = 'Negativní hodnocení'
    
    # Metriky zapojení
    total_votes = analysis['positive_count'] + analysis['negative_count']
    if total_votes > 0:
        analysis['engagement_metrics'] = {
            'total_votes': total_votes,
            'positive_ratio': (analysis['positive_count'] / total_votes) * 100,
            'engagement_level': 'Vysoké' if total_votes > 20 else 'Střední' if total_votes > 5 else 'Nízké'
        }
    
    return analysis

def get_rating_recommendations(analysis):
    """Generuje doporučení na základě hodnocení"""
    recommendations = []
    
    my_rating = analysis['my_rating']
    total_rating = analysis['total_rating']
    
    # Doporučení podle mého hodnocení
    if my_rating == 'none':
        recommendations.extend([
            "💡 Můžete příspěvek ohodnotit",
            "👍 Použijte RATE_ACTION=positive pro kladné hodnocení",
            "👎 Použijte RATE_ACTION=negative pro záporné hodnocení"
        ])
    elif my_rating == 'positive':
        recommendations.extend([
            "✅ Máte kladné hodnocení",
            "🔄 Můžete hodnocení odebrat (RATE_ACTION=remove)"
        ])
    elif my_rating in ['negative', 'negative_visible']:
        recommendations.extend([
            "❌ Máte záporné hodnocení",
            "🔄 Můžete hodnocení odebrat (RATE_ACTION=remove)"
        ])
    
    # Doporučení podle kvality příspěvku
    if total_rating > 10:
        recommendations.append("⭐ Vysoce hodnocený příspěvek - zvažte sdílení")
    elif total_rating < -5:
        recommendations.append("⚠️ Kontroverzní příspěvek - buďte opatrní")
    
    # Obecná doporučení
    recommendations.extend([
        "📌 Přidat do upomínek (discussion_reminder.py)",
        "💬 Zobrazit celou diskuzi (discussion_get.py)",
        "🔍 Analyzovat další příspěvky v diskuzi"
    ])
    
    return recommendations

def format_raters_summary(raters, rating_type, limit=5):
    """Formátuje seznam hodnotitelů podle typu"""
    filtered_raters = [
        rater for rater in raters 
        if rater.get('rating_type') == rating_type
    ]
    
    if not filtered_raters:
        return []
    
    summary = []
    for rater in filtered_raters[:limit]:
        username = rater.get('username', 'Neznámý')
        rated_at = rater.get('rated_at', 'Neznámé datum')
        summary.append(f"  - {username} ({rated_at})")
    
    if len(filtered_raters) > limit:
        remaining = len(filtered_raters) - limit
        summary.append(f"  ... a dalších {remaining} hodnotitelů")
    
    return summary

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
    
    post_id = config.get('POST_ID')
    if not post_id or post_id == '67890':
        print("Chyba: Nastavte POST_ID v secret.txt")
        print("Příklad: POST_ID=789012")
        sys.exit(1)
    
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    
    print("=== NYX.CZ API - Načtení hodnocení příspěvku ===")
    print(f"URL: {base_url}/discussion/{discussion_id}/rating/{post_id}")
    print(f"Diskuze ID: {discussion_id}")
    print(f"Příspěvek ID: {post_id}")
    print()
    
    # Příprava požadavku
    url = f"{base_url}/discussion/{discussion_id}/rating/{post_id}"
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
                    analysis = analyze_rating_data(data)
                    
                    print()
                    print("=== Analýza hodnocení ===")
                    print(f"Celkové hodnocení: {analysis['total_rating']}")
                    print(f"Kladná hodnocení: {analysis['positive_count']}")
                    print(f"Záporná hodnocení: {analysis['negative_count']}")
                    print(f"Moje hodnocení: {analysis['my_rating']}")
                    
                    # Hodnotitelé
                    if analysis['raters']:
                        print()
                        print("=== Hodnotitelé ===")
                        print(f"Celkem hodnotitelů: {len(analysis['raters'])}")
                        
                        # Distribuce hodnocení
                        if analysis['rating_distribution']:
                            print()
                            print("=== Distribuce hodnocení ===")
                            rating_icons = {
                                'positive': '👍',
                                'negative': '👎',
                                'negative_visible': '👎',
                                'unknown': '❓'
                            }
                            
                            for rating_type, count in analysis['rating_distribution'].items():
                                icon = rating_icons.get(rating_type, '❓')
                                type_name = {
                                    'positive': 'Kladné',
                                    'negative': 'Záporné',
                                    'negative_visible': 'Záporné (viditelné)',
                                    'unknown': 'Neznámé'
                                }.get(rating_type, rating_type)
                                print(f"{icon} {type_name}: {count}")
                        
                        # Seznam hodnotitelů podle typu
                        print()
                        print("=== Hodnotitelé podle typu ===")
                        
                        # Kladní hodnotitelé
                        positive_summary = format_raters_summary(analysis['raters'], 'positive')
                        if positive_summary:
                            print("👍 Kladně hodnotili:")
                            for line in positive_summary:
                                print(line)
                        
                        # Záporní hodnotitelé
                        negative_summary = format_raters_summary(analysis['raters'], 'negative') + \
                                         format_raters_summary(analysis['raters'], 'negative_visible')
                        if negative_summary:
                            print("👎 Záporně hodnotili:")
                            for line in negative_summary:
                                print(line)
                    
                    # Hodnocení přátel
                    if analysis['friends_rating']:
                        print()
                        print("=== Hodnocení přátel ===")
                        friends = analysis['friends_rating']
                        
                        friends_positive = friends.get('positive', 0)
                        friends_negative = friends.get('negative', 0)
                        friends_total = friends.get('total', 0)
                        
                        print(f"Přátelé - kladné: {friends_positive}")
                        print(f"Přátelé - záporné: {friends_negative}")
                        print(f"Přátelé - celkem: {friends_total}")
                        
                        if friends_total > 0:
                            friends_ratio = (friends_positive / friends_total) * 100
                            print(f"Poměr kladných u přátel: {friends_ratio:.1f}%")
                    
                    # Časové informace
                    if analysis['last_rated_at']:
                        print()
                        print("=== Časové informace ===")
                        print(f"Naposledy hodnoceno: {analysis['last_rated_at']}")
                    
                    # Statistiky hodnocení
                    print()
                    print("=== Statistiky hodnocení ===")
                    print(f"Kvalita: {analysis['quality_assessment']}")
                    
                    if analysis['engagement_metrics']:
                        metrics = analysis['engagement_metrics']
                        print(f"Celkem hlasů: {metrics['total_votes']}")
                        print(f"Poměr kladných: {metrics['positive_ratio']:.1f}%")
                        print(f"Úroveň zapojení: {metrics['engagement_level']}")
                    else:
                        print("📊 Příspěvek zatím nebyl hodnocen")
                    
                    # Pokročilé analýzy
                    print()
                    print("=== Pokročilé analýzy ===")
                    
                    # Analýza kontroverznosti
                    if analysis['positive_count'] > 0 and analysis['negative_count'] > 0:
                        controversy_ratio = min(analysis['positive_count'], analysis['negative_count']) / \
                                          max(analysis['positive_count'], analysis['negative_count'])
                        if controversy_ratio > 0.7:
                            print("🔥 Vysoce kontroverzní příspěvek")
                        elif controversy_ratio > 0.3:
                            print("⚖️ Mírně kontroverzní příspěvek")
                        else:
                            print("📊 Jednoznačné hodnocení")
                    
                    # Analýza trendů
                    if len(analysis['raters']) > 5:
                        recent_ratings = analysis['raters'][-5:]  # Posledních 5 hodnocení
                        recent_positive = sum(1 for r in recent_ratings if r.get('rating_type') == 'positive')
                        if recent_positive >= 4:
                            print("📈 Rostoucí pozitivní trend")
                        elif recent_positive <= 1:
                            print("📉 Klesající trend")
                        else:
                            print("📊 Stabilní trend")
                    
                    # Doporučení
                    recommendations = get_rating_recommendations(analysis)
                    if recommendations:
                        print()
                        print("=== Doporučení ===")
                        for rec in recommendations:
                            print(f"- {rec}")
                    
                    # Možné akce
                    print()
                    print("=== Možné akce ===")
                    actions = [
                        "🎯 Ohodnotit příspěvek (discussion_rate.py)",
                        "💬 Zobrazit diskuzi (discussion_get.py)",
                        "📌 Přidat do upomínek (discussion_reminder.py)",
                        "🔍 Analyzovat další příspěvky autora"
                    ]
                    
                    for action in actions:
                        print(f"- {action}")
                        
            except json.JSONDecodeError:
                print(response.text)
        
        # Kontrola chyb
        if response.status_code != 200:
            print()
            print("Chyba v požadavku! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- DISCUSSION_ID v secret.txt")
            print("- POST_ID v secret.txt")
            
            error_messages = {
                400: "Neplatné ID diskuze nebo příspěvku",
                401: "Neplatný nebo chybějící API token",
                403: "Nedostatečná oprávnění pro čtení hodnocení",
                404: "Diskuze nebo příspěvek neexistuje"
            }
            
            if response.status_code in error_messages:
                print(f"- {error_messages[response.status_code]}")
        else:
            print()
            print("✓ Hodnocení úspěšně načteno!")
            
            # Související akce
            print()
            print("=== Související akce ===")
            related_actions = [
                "📊 Ohodnotit příspěvek: discussion_rate.py",
                "💬 Zobrazit diskuzi: discussion_get.py",
                "📌 Přidat do upomínek: discussion_reminder.py",
                "🔍 Analyzovat celou diskuzi"
            ]
            
            for action in related_actions:
                print(f"- {action}")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)
    
    print()
    print("Tip: Pro hodnocení příspěvku použijte discussion_rate.py")

if __name__ == "__main__":
    main()
