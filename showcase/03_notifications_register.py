#!/usr/bin/env python3
"""
NYX.CZ API - Registrace pro notifikace
POST /api/register_for_notifications
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

def analyze_registration(data):
    """Analyzuje výsledek registrace"""
    analysis = {
        'registration_id': data.get('id', data.get('registrationId', 'neznámé')),
        'endpoint': data.get('endpoint', 'neznámý'),
        'status': data.get('status', 'neznámý'),
        'types': data.get('types', []),
        'format': data.get('format', 'json'),
        'enabled': data.get('enabled', True),
        'has_secret': data.get('hasSecret', False),
        'test_url': data.get('testUrl'),
        'stats': data.get('stats', {}),
        'created_at': data.get('createdAt'),
        'updated_at': data.get('updatedAt')
    }
    
    return analysis

def validate_endpoint_url(url):
    """Validuje URL endpointu"""
    issues = []
    
    if not url.startswith(('http://', 'https://')):
        issues.append("URL musí začínat http:// nebo https://")
    
    if url.startswith('http://'):
        issues.append("Doporučujeme používat HTTPS pro bezpečnost")
    
    if 'localhost' in url or '127.0.0.1' in url:
        issues.append("Localhost URL nebude dostupná z internetu")
    
    if not url.endswith('/webhook') and not url.endswith('/notifications'):
        issues.append("Zvažte použití specifické cesty jako /webhook nebo /notifications")
    
    return issues

def get_webhook_implementation_example(endpoint, has_secret=False):
    """Generuje příklad implementace webhook endpointu"""
    examples = {
        'python_flask': f'''
# Python Flask příklad
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Ověření signature (pokud je nastaven secret)
    {f"""
    signature = request.headers.get('X-NYX-Signature', '')
    if not verify_signature(request.data, signature):
        return 'Unauthorized', 401
    """ if has_secret else "# Bez signature ověření"}
    
    # Zpracování notifikace
    data = request.get_json()
    notification_type = data.get('type')
    
    if notification_type == 'discussion_reply':
        handle_discussion_reply(data)
    elif notification_type == 'mail_received':
        handle_mail_received(data)
    
    return jsonify({{"status": "ok"}})

{f"""
def verify_signature(payload, signature):
    expected = hmac.new(
        b'your_webhook_secret',
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f'sha256={{expected}}', signature)
""" if has_secret else ""}
''',
        'node_express': f'''
// Node.js Express příklad
const express = require('express');
const crypto = require('crypto');

const app = express();
app.use(express.json());

app.post('/webhook', (req, res) => {{
    {f"""
    // Ověření signature
    const signature = req.headers['x-nyx-signature'];
    if (!verifySignature(req.body, signature)) {{
        return res.status(401).send('Unauthorized');
    }}
    """ if has_secret else "// Bez signature ověření"}
    
    const {{ type, data }} = req.body;
    
    switch (type) {{
        case 'discussion_reply':
            handleDiscussionReply(data);
            break;
        case 'mail_received':
            handleMailReceived(data);
            break;
    }}
    
    res.json({{ status: 'ok' }});
}});

{f"""
function verifySignature(payload, signature) {{
    const expected = crypto
        .createHmac('sha256', 'your_webhook_secret')
        .update(JSON.stringify(payload))
        .digest('hex');
    return crypto.timingSafeEqual(
        Buffer.from(`sha256=${{expected}}`),
        Buffer.from(signature)
    );
}}
""" if has_secret else ""}
'''
    }
    
    return examples

def format_registration_tips(analysis):
    """Generuje tipy pro registraci"""
    tips = []
    
    # Tipy podle stavu
    if analysis['status'] == 'active':
        tips.append("✅ Registrace je aktivní a funkční")
    elif analysis['status'] == 'pending':
        tips.append("⏳ Registrace čeká na ověření")
    elif analysis['status'] == 'failed':
        tips.append("❌ Registrace selhala - zkontrolujte endpoint")
    
    # Tipy podle nastavení
    if not analysis['has_secret']:
        tips.append("🔒 Doporučujeme nastavit webhook secret pro bezpečnost")
    
    if not analysis['enabled']:
        tips.append("⚠️ Notifikace jsou zakázané - povolte je pro příjem")
    
    # Tipy podle typů
    if not analysis['types']:
        tips.append("📋 Nejsou nastaveny žádné typy notifikací")
    elif len(analysis['types']) > 10:
        tips.append("📊 Máte mnoho typů notifikací - zvažte filtrování")
    
    # Tipy podle statistik
    stats = analysis['stats']
    if stats:
        total_sent = stats.get('totalSent', 0)
        failed = stats.get('failed', 0)
        
        if total_sent > 0:
            failure_rate = (failed / total_sent) * 100
            if failure_rate > 20:
                tips.append(f"⚠️ Vysoká chybovost ({failure_rate:.1f}%) - zkontrolujte endpoint")
            elif failure_rate > 5:
                tips.append(f"📊 Mírná chybovost ({failure_rate:.1f}%) - monitorujte endpoint")
    
    return tips

def main():
    # Načtení konfigurace
    config = load_config()
    
    # Kontrola API tokenu
    api_token = config.get('NYX_API_TOKEN')
    if not api_token or api_token == 'your_api_token_here':
        print("Chyba: Nastavte NYX_API_TOKEN v secret.txt")
        sys.exit(1)
    
    # Kontrola endpointu
    endpoint = config.get('NOTIFICATION_ENDPOINT')
    if not endpoint:
        print("Chyba: Nastavte NOTIFICATION_ENDPOINT v secret.txt")
        print("Příklad: NOTIFICATION_ENDPOINT=https://your-app.com/webhook")
        sys.exit(1)
    
    base_url = config.get('NYX_API_BASE_URL', 'https://nyx.cz/api')
    
    print("=== NYX.CZ API - Registrace pro notifikace ===")
    print(f"URL: {base_url}/register_for_notifications")
    print(f"Endpoint: {endpoint}")
    print()
    
    # Validace endpointu
    endpoint_issues = validate_endpoint_url(endpoint)
    if endpoint_issues:
        print("⚠️ Potenciální problémy s endpointem:")
        for issue in endpoint_issues:
            print(f"- {issue}")
        print()
    
    # Příprava dat
    data = {
        'endpoint': endpoint
    }
    
    # Přidání volitelných parametrů
    notification_types = config.get('NOTIFICATION_TYPES')
    if notification_types:
        # Převod čárkami oddělených hodnot na seznam
        types_list = [t.strip() for t in notification_types.split(',') if t.strip()]
        data['types'] = types_list
    
    notification_secret = config.get('NOTIFICATION_SECRET')
    if notification_secret:
        data['secret'] = notification_secret
    
    notification_format = config.get('NOTIFICATION_FORMAT')
    if notification_format:
        data['format'] = notification_format
    
    notification_enabled = config.get('NOTIFICATION_ENABLED')
    if notification_enabled:
        data['enabled'] = notification_enabled.lower() in ('true', '1', 'yes')
    
    print("Registrace notifikačního endpointu...")
    
    # Příprava požadavku
    url = f"{base_url}/register_for_notifications"
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
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
                if response.status_code in [200, 201]:
                    analysis = analyze_registration(response_data)
                    
                    print()
                    print("=== Analýza registrace ===")
                    print(f"ID registrace: {analysis['registration_id']}")
                    print(f"Endpoint: {analysis['endpoint']}")
                    print(f"Stav: {analysis['status']}")
                    
                    # Registrované typy
                    if analysis['types']:
                        print()
                        print("=== Registrované typy notifikací ===")
                        for i, notif_type in enumerate(analysis['types'], 1):
                            print(f"{i}. {notif_type}")
                    
                    # Nastavení
                    print()
                    print("=== Nastavení notifikací ===")
                    print(f"Formát: {analysis['format']}")
                    print(f"Povoleno: {'Ano' if analysis['enabled'] else 'Ne'}")
                    print(f"Webhook secret: {'✓ nastaven' if analysis['has_secret'] else '⚠️ nenastaven'}")
                    
                    # Testovací URL
                    if analysis['test_url']:
                        print()
                        print("=== Testování ===")
                        print(f"Test URL: {analysis['test_url']}")
                        print("💡 Použijte tuto URL pro test notifikací")
                    
                    # Statistiky
                    if analysis['stats']:
                        print()
                        print("=== Statistiky ===")
                        stats = analysis['stats']
                        total_sent = stats.get('totalSent', 0)
                        successful = stats.get('successful', 0)
                        failed = stats.get('failed', 0)
                        
                        print(f"Celkem odesláno: {total_sent}")
                        print(f"Úspěšné: {successful}")
                        print(f"Neúspěšné: {failed}")
                        
                        if total_sent > 0:
                            success_rate = (successful / total_sent) * 100
                            print(f"Úspěšnost: {success_rate:.1f}%")
                    
                    # Časové informace
                    if analysis['created_at']:
                        print()
                        print("=== Časové informace ===")
                        print(f"Vytvořeno: {analysis['created_at']}")
                        if analysis['updated_at']:
                            print(f"Aktualizováno: {analysis['updated_at']}")
                    
                    # Tipy pro registraci
                    tips = format_registration_tips(analysis)
                    if tips:
                        print()
                        print("=== Tipy pro optimalizaci ===")
                        for tip in tips:
                            print(f"- {tip}")
                    
                    # Doporučení pro webhook
                    print()
                    print("=== Doporučení pro webhook ===")
                    webhook_tips = [
                        "🔧 Implementujte správné HTTP status kódy (200-299)",
                        "🔒 Ověřujte webhook secret pro bezpečnost",
                        "📝 Logujte příchozí notifikace pro debugging",
                        "🔄 Implementujte retry logiku pro chyby",
                        "🌐 Používejte HTTPS pro bezpečný přenos",
                        "⚡ Odpovídejte rychle (< 5 sekund)",
                        "📊 Monitorujte výkon a chybovost"
                    ]
                    
                    for tip in webhook_tips:
                        print(f"- {tip}")
                    
                    # Příklad implementace
                    examples = get_webhook_implementation_example(
                        analysis['endpoint'], 
                        analysis['has_secret']
                    )
                    
                    print()
                    print("=== Příklad webhook endpointu ===")
                    print("Python Flask implementace:")
                    print(examples['python_flask'])
                    
                    # Další kroky
                    print()
                    print("=== Další kroky ===")
                    next_steps = [
                        "🔧 Implementujte webhook endpoint na vaší aplikaci",
                        "🧪 Otestujte příjem notifikací",
                        "📊 Nastavte monitoring a logování",
                        "📋 Použijte notifications_get.py pro kontrolu notifikací",
                        "🔄 Pravidelně kontrolujte statistiky úspěšnosti"
                    ]
                    
                    for step in next_steps:
                        print(f"- {step}")
                        
            except json.JSONDecodeError:
                print(response.text)
        
        # Kontrola chyb
        if response.status_code not in [200, 201]:
            print()
            print("Chyba při registraci! Zkontrolujte:")
            print("- API token v secret.txt")
            print("- NOTIFICATION_ENDPOINT v secret.txt")
            
            error_messages = {
                400: "Neplatný endpoint URL / Neplatné typy notifikací / Neplatný formát",
                401: "Neplatný nebo chybějící API token",
                403: "Nedostatečná oprávnění pro registraci",
                409: "Endpoint již je registrován - použijte jiný nebo aktualizujte",
                422: "Endpoint není dostupný - zkontrolujte HTTP odpovědi"
            }
            
            if response.status_code in error_messages:
                print(f"- {error_messages[response.status_code]}")
        else:
            print()
            print("✅ Registrace pro notifikace byla úspěšná!")
            
            # Bezpečnostní tipy
            print()
            print("=== Bezpečnostní tipy ===")
            security_tips = [
                "🔐 Vždy ověřujte webhook signature",
                "🌐 Používejte HTTPS pro webhook endpoint",
                "🚦 Implementujte rate limiting",
                "📝 Logujte všechny příchozí požadavky",
                "🔄 Pravidelně rotujte webhook secret",
                "🛡️ Validujte všechna příchozí data",
                "⏰ Nastavte timeouty pro zpracování"
            ]
            
            for tip in security_tips:
                print(f"- {tip}")
    
    except requests.exceptions.RequestException as e:
        print(f"Chyba při komunikaci s API: {e}")
        sys.exit(1)
    
    print()
    print("Tip: Pro kontrolu notifikací použijte notifications_get.py")

if __name__ == "__main__":
    main()
