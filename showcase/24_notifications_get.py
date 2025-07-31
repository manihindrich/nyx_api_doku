#!/usr/bin/env python3
"""
NYX.CZ API - Získání notifikací
GET /api/notifications
"""

import requests
import json
import sys
import os
from urllib.parse import urlencode
from collections import Counter
from datetime import datetime, date

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

def analyze_notifications(data):
    """Analyzuje notifikace"""
    notifications = data.get('notifications', [])
    total = data.get('total', 0)
    unread_count = data.get('unreadCount', 0)
    
    analysis = {
        'total': total,
        'shown': len(notifications),
        'unread_count': unread_count,
        'types': {},
        'priorities': {},
        'categories': {},
        'unread_notifications': [],
        'action_required': [],
        'today_count': 0,
        'recent_notifications': [],
        'time_distribution': {},
        'read_percentage': 0
    }
    
    if not notifications:
        return analysis
    
    # Analýza typů
    types = [notif.get('type', 'neznámý') for notif in notifications]
    analysis['types'] = dict(Counter(types))
    
    # Analýza priorit
    priorities = [notif.get('priority', 'normal') for notif in notifications]
    analysis['priorities'] = dict(Counter(priorities))
    
    # Analýza kategorií
    categories = [notif.get('category', 'nezařazeno') for notif in notifications if notif.get('category')]
    if categories:
        analysis['categories'] = dict(Counter(categories))
    
    # Nepřečtené notifikace
    analysis['unread_notifications'] = [
        notif for notif in notifications if not notif.get('read', True)
    ]
    
    # Notifikace vyžadující akci
    analysis['action_required'] = [
        notif for notif in notifications if notif.get('actionRequired', False)
    ]
    
    # Dnešní notifikace
    today_str = date.today().strftime('%Y-%m-%d')
    analysis['today_count'] = len([
        notif for notif in notifications 
        if notif.get('createdAt', '').startswith(today_str)
    ])
    
    # Nejnovější notifikace
    analysis['recent_notifications'] = notifications[:5]
    
    # Časové rozložení
    time_periods = {'today': 0, 'yesterday': 0, 'this_week': 0, 'older': 0}
    today = date.today()
    
    for notif in notifications:
        created_at = notif.get('createdAt', '')
        if created_at.startswith(today.strftime('%Y-%m-%d')):
            time_periods['today'] += 1
        elif created_at.startswith((today.replace(day=today.day-1)).strftime('%Y-%m-%d')):
            time_periods['yesterday'] += 1
        # Zjednodušená logika pro týden
        elif created_at >= (today.replace(day=today.day-7)).strftime('%Y-%m-%d'):
            time_periods['this_week'] += 1
        else:
            time_periods['older'] += 1
    
    analysis['time_distribution'] = time_periods
    
    # Procento přečtených
    if total > 0:
        read_count = total - unread_count
        analysis['read_percentage'] = (read_count / total) * 100
    
    return analysis

def format_notification_summary(notif):
    """Formátuje shrnutí notifikace"""
    title = notif.get('title', 'Bez názvu')
    notif_type = notif.get('type', 'neznámý')
    created_at = notif.get('createdAt', 'neznámé datum')
    priority = notif.get('priority', 'normal')
    is_read = notif.get('read', True)
    
    status = "✓" if is_read else "●"
    priority_icon = "🔴" if priority == "high" else "🟡" if priority == "medium" else "⚪"
    
    return f"{status} {priority_icon} {title} [{notif_type}] ({created_at})"

def get_notification_management_tips(analysis):
    """Generuje tipy pro správu notifikací"""
    tips = []
    
    unread = analysis['unread_count']
    
    if unread > 50:
        tips.extend([
            "🚨 KRITICKÉ: Máte velmi mnoho nepřečtených notifikací",
            "📋 Zvažte hromadné označení starších jako přečtené",
            "🔧 Nastavte filtry pro důležité typy notifikací",
            "⏰ Naplánujte si pravidelné čištění notifikací"
        ])
    elif unread > 20:
        tips.extend([
            "⚠️ Máte mnoho nepřečtených notifikací",
            "📝 Projděte si nejdůležitější notifikace",
            "🎯 Zaměřte se na notifikace vyžadující akci"
        ])
    elif unread > 0:
        tips.extend([
            "📬 Máte několik nepřečtených notifikací",
            "👀 Projděte si nejnovější notifikace"
        ])
    else:
        tips.append("✅ Výborně! Všechny notifikace jsou přečtené")
    
    # Tipy podle typů
    if analysis['action_required']:
        tips.append(f"⚡ {len(analysis['action_required'])} notifikací vyžaduje vaši akci")
    
    if analysis['priorities'].get('high', 0) > 0:
        tips.append(f"🔴 {analysis['priorities']['high']} vysokoprioritních notifikací")
    
    # Obecné tipy
    tips.extend([
        "🔍 Použijte filtry pro lepší přehled",
        "📱 Nastavte si push notifikace pro důležité typy",
        "🗂️ Organizujte notifikace podle kategorií"
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
    
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    
    # Sestavení parametrů
    params = {}
    
    # Přidání volitelných parametrů
    optional_params = {
        'limit': config.get('NOTIFICATIONS_LIMIT'),
        'offset': config.get('NOTIFICATIONS_OFFSET'),
        'type': config.get('NOTIFICATIONS_TYPE'),
        'read': config.get('NOTIFICATIONS_READ'),
        'since': config.get('NOTIFICATIONS_SINCE')
    }
    
    for key, value in optional_params.items():
        if value:
            params[key] = value
    
    # Sestavení URL
    url = f"{base_url}/notifications"
    if params:
        query_string = urlencode(params)
        full_url = f"{url}?{query_string}"
    else:
        full_url = url
    
    print("=== NYX.CZ API - Získání notifikací ===")
    print(f"URL: {full_url}")
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
                    analysis = analyze_notifications(data)
                    
                    print()
                    print("=== Analýza notifikací ===")
                    print(f"Celkem notifikací: {analysis['total']}")
                    print(f"Zobrazeno: {analysis['shown']}")
                    print(f"Nepřečtené: {analysis['unread_count']}")
                    print(f"Přečteno: {analysis['read_percentage']:.1f}%")
                    
                    # Typy notifikací
                    if analysis['types']:
                        print()
                        print("=== Typy notifikací ===")
                        for notif_type, count in analysis['types'].items():
                            print(f"- {notif_type}: {count} notifikací")
                    
                    # Priority notifikací
                    if analysis['priorities']:
                        print()
                        print("=== Priority notifikací ===")
                        priority_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢', 'normal': '⚪'}
                        for priority, count in analysis['priorities'].items():
                            icon = priority_icons.get(priority, '⚪')
                            print(f"- {icon} {priority}: {count} notifikací")
                    
                    # Kategorie
                    if analysis['categories']:
                        print()
                        print("=== Kategorie notifikací ===")
                        for category, count in analysis['categories'].items():
                            print(f"- {category}: {count} notifikací")
                    
                    # Nejnovější notifikace
                    if analysis['recent_notifications']:
                        print()
                        print("=== Nejnovější notifikace ===")
                        for notif in analysis['recent_notifications']:
                            print(format_notification_summary(notif))
                    
                    # Nepřečtené notifikace
                    if analysis['unread_notifications']:
                        print()
                        print("=== Nepřečtené notifikace ===")
                        print(f"Počet nepřečtených: {len(analysis['unread_notifications'])}")
                        for notif in analysis['unread_notifications'][:3]:
                            print(format_notification_summary(notif))
                        
                        if len(analysis['unread_notifications']) > 3:
                            remaining = len(analysis['unread_notifications']) - 3
                            print(f"... a dalších {remaining} nepřečtených")
                    
                    # Notifikace vyžadující akci
                    if analysis['action_required']:
                        print()
                        print("=== Notifikace vyžadující akci ===")
                        for notif in analysis['action_required']:
                            action_type = notif.get('actionType', 'neznámá akce')
                            print(f"⚡ {notif.get('title', 'Bez názvu')} - {action_type}")
                    
                    # Časové statistiky
                    print()
                    print("=== Časové statistiky ===")
                    time_dist = analysis['time_distribution']
                    print(f"Dnes: {time_dist['today']} notifikací")
                    print(f"Včera: {time_dist['yesterday']} notifikací")
                    print(f"Tento týden: {time_dist['this_week']} notifikací")
                    print(f"Starší: {time_dist['older']} notifikací")
                    
                    # Stránkování
                    pagination = data.get('pagination', {})
                    if pagination:
                        print()
                        print("=== Stránkování ===")
                        current_page = pagination.get('currentPage', 1)
                        total_pages = pagination.get('totalPages', 1)
                        print(f"Aktuální stránka: {current_page} z {total_pages}")
                        
                        if current_page < total_pages:
                            next_offset = analysis['shown'] + int(config.get('NOTIFICATIONS_OFFSET', 0))
                            print(f"💡 Pro další notifikace nastavte NOTIFICATIONS_OFFSET={next_offset}")
                    
                    # Doporučení pro správu
                    tips = get_notification_management_tips(analysis)
                    if tips:
                        print()
                        print("=== Doporučení pro správu notifikací ===")
                        for tip in tips:
                            print(f"- {tip}")
                    
                    # Tipy pro filtrování
                    print()
                    print("=== Tipy pro filtrování ===")
                    filter_tips = [
                        "🎯 Použijte NOTIFICATIONS_TYPE pro konkrétní typ",
                        "📋 Nastavte NOTIFICATIONS_READ=false pro nepřečtené",
                        "📅 Využijte NOTIFICATIONS_SINCE pro novější notifikace",
                        "📄 Kombinujte s NOTIFICATIONS_LIMIT pro stránkování"
                    ]
                    
                    for tip in filter_tips:
                        print(f"- {tip}")
                    
                    # Výkonnostní metriky
                    print()
                    print("=== Výkonnostní metriky ===")
                    print(f"Efektivita čtení: {analysis['read_percentage']:.1f}%")
                    if analysis['unread_count'] > 0:
                        urgency = "Vysoká" if analysis['unread_count'] > 20 else "Střední" if analysis['unread_count'] > 5 else "Nízká"
                        print(f"Naléhavost správy: {urgency}")
                    
                    # Další akce
                    print()
                    print("=== Další akce ===")
                    actions = [
                        "📝 Označte důležité notifikace jako přečtené",
                        "🔔 Použijte notifications_register.py pro nastavení",
                        "🎛️ Nastavte filtry pro lepší správu",
                        "⏰ Pravidelně kontrolujte nepřečtené notifikace"
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
            
            error_messages = {
                400: "Neplatné parametry (limit, offset, type, read, since)",
                401: "Neplatný nebo chybějící API token",
                403: "Nedostatečná oprávnění pro čtení notifikací",
                429: "Příliš mnoho požadavků - zkuste později"
            }
            
            if response.status_code in error_messages:
                print(f"- {error_messages[response.status_code]}")
        else:
            print()
            print("✓ Notifikace úspěšně načteny!")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)
    
    print()
    print("Tip: Pro registraci notifikací použijte notifications_register.py")

if __name__ == "__main__":
    main()
