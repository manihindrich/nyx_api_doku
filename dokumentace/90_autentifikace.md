# Autentifikace

Tento dokument popisuje způsoby autentifikace a autorizace v NYX.CZ API.

## Přehled

NYX.CZ API používá Bearer token autentifikaci. Všechny API endpointy vyžadují platný autentifikační token v Authorization hlavičce.

## Získání tokenu

Token získáte prostřednictvím webového rozhraní Nyx.cz nebo jiného autorizovaného klienta. API samo neposkytuje endpoint pro přihlášení - token musí být získán externě.

### Webové rozhraní

1. Přihlaste se na https://nyx.cz
2. Přejděte do nastavení účtu
3. Vygenerujte nebo zkopírujte API token

## Použití tokenu

### Authorization hlavička

Token se odesílá v HTTP hlavičce `Authorization` s prefixem `Bearer`:

```http
Authorization: Bearer YOUR_TOKEN_HERE
```

### Příklad požadavku

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     https://nyx.cz/api/notepad
```

### JavaScript/Fetch

```javascript
const response = await fetch('https://nyx.cz/api/notepad', {
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  }
});
```

### Python/Requests

```python
import requests

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

response = requests.get('https://nyx.cz/api/notepad', headers=headers)
```

## Formát tokenu

Token je alfanumerický řetězec s následujícími charakteristikami:

- **Délka**: Variabilní (obvykle 32-64 znaků)
- **Znaky**: [A-Za-z0-9] a speciální znaky
- **Citlivost**: Case-sensitive
- **Platnost**: Dlouhodobá (nevypršuje automaticky)

**Příklad tokenu**: `abc123def456ghi789jkl012mno345pqr678`

## Bezpečnost

### Ochrana tokenu

- **Nikdy nesdílejte** token s neautorizovanými osobami
- **Neukládejte** token v kódu nebo veřejných repozitářích
- **Používejte** proměnné prostředí nebo bezpečné úložiště
- **Regenerujte** token při podezření na kompromitaci

### Doporučené postupy

#### Proměnné prostředí

```bash
export NYX_API_TOKEN="your_token_here"
```

```javascript
const token = process.env.NYX_API_TOKEN;
```

#### Konfigurační soubory

Vytvořte konfigurační soubor mimo veřejný adresář:

```json
{
  "api_token": "your_token_here"
}
```

Přidejte do `.gitignore`:
```
config.json
.env
```

#### Rotace tokenů

Pravidelně regenerujte tokeny:
- Při podezření na kompromitaci
- Při změně týmu
- Preventivně každých 6-12 měsíců

## Chybové stavy

### 401 Unauthorized

Chybí nebo je neplatný token:

```json
{
  "error": true,
  "code": "UNAUTHORIZED",
  "message": "Chybí nebo neplatný autentifikační token"
}
```

**Možné příčiny:**
- Chybí Authorization hlavička
- Nesprávný formát hlavičky
- Neplatný token
- Vypršelý token

**Řešení:**
1. Zkontrolujte formát hlavičky
2. Ověřte platnost tokenu
3. Regenerujte token pokud je potřeba

### 403 Forbidden

Token je platný, ale nemáte oprávnění:

```json
{
  "error": true,
  "code": "INSUFFICIENT_PERMISSIONS",
  "message": "Nedostatečná oprávnění"
}
```

## Testování autentifikace

### Základní test

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/notepad
```

**Očekávaná odpověď (200 OK):**
```json
{
  "context": {
    "user": {
      "username": "YOUR_USERNAME",
      ...
    }
  },
  ...
}
```

### Test neplatného tokenu

```bash
curl -H "Authorization: Bearer invalid_token" \
     https://nyx.cz/api/notepad
```

**Očekávaná odpověď (401 Unauthorized):**
```json
{
  "error": true,
  "code": "UNAUTHORIZED",
  "message": "Chybí nebo neplatný autentifikační token"
}
```

## Implementace v různých jazycích

### JavaScript (Node.js)

```javascript
class NyxApiClient {
  constructor(token) {
    this.token = token;
    this.baseUrl = 'https://nyx.cz/api';
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json',
      ...options.headers
    };

    const response = await fetch(url, {
      ...options,
      headers
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`API Error: ${error.message}`);
    }

    return response.json();
  }

  async getNotepad() {
    return this.request('/notepad');
  }
}

// Použití
const client = new NyxApiClient(process.env.NYX_API_TOKEN);
const notepad = await client.getNotepad();
```

### Python

```python
import requests
import os

class NyxApiClient:
    def __init__(self, token):
        self.token = token
        self.base_url = 'https://nyx.cz/api'
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })

    def request(self, endpoint, method='GET', **kwargs):
        url = f'{self.base_url}{endpoint}'
        response = self.session.request(method, url, **kwargs)
        
        if not response.ok:
            error = response.json()
            raise Exception(f"API Error: {error['message']}")
        
        return response.json()

    def get_notepad(self):
        return self.request('/notepad')

# Použití
client = NyxApiClient(os.environ['NYX_API_TOKEN'])
notepad = client.get_notepad()
```

### PHP

```php
<?php

class NyxApiClient {
    private $token;
    private $baseUrl = 'https://nyx.cz/api';

    public function __construct($token) {
        $this->token = $token;
    }

    public function request($endpoint, $method = 'GET', $data = null) {
        $url = $this->baseUrl . $endpoint;
        
        $headers = [
            'Authorization: Bearer ' . $this->token,
            'Content-Type: application/json'
        ];

        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
        
        if ($data) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        $decoded = json_decode($response, true);
        
        if ($httpCode >= 400) {
            throw new Exception('API Error: ' . $decoded['message']);
        }

        return $decoded;
    }

    public function getNotepad() {
        return $this->request('/notepad');
    }
}

// Použití
$client = new NyxApiClient($_ENV['NYX_API_TOKEN']);
$notepad = $client->getNotepad();
?>
```

## Časté problémy

### Chybný formát hlavičky

❌ **Špatně:**
```http
Authorization: YOUR_TOKEN
Authorization: Token YOUR_TOKEN
Authorization: Bearer: YOUR_TOKEN
```

✅ **Správně:**
```http
Authorization: Bearer YOUR_TOKEN
```

### Mezery v tokenu

Token nesmí obsahovat mezery na začátku ani na konci:

```javascript
// Odstraňte mezery
const token = rawToken.trim();
```

### Kódování znaků

Token používejte v původním formátu bez URL encoding nebo jiných úprav.

## Monitoring a logování

### Logování požadavků

```javascript
const response = await fetch(url, {
  headers: {
    'Authorization': `Bearer ${token.substring(0, 8)}...` // Log pouze část tokenu
  }
});

console.log(`API Request: ${method} ${url} - ${response.status}`);
```

### Sledování chyb

```javascript
if (response.status === 401) {
  console.error('Token expired or invalid - regeneration needed');
  // Implementovat automatickou regeneraci nebo upozornění
}
```

## Migrace a aktualizace

Při změně tokenů:

1. **Vygenerujte** nový token
2. **Aktualizujte** všechny klienty
3. **Otestujte** funkcionalitu
4. **Zrušte** starý token
5. **Dokumentujte** změnu

Doporučujeme postupnou migraci s překryvem tokenů pro minimalizaci výpadků.
