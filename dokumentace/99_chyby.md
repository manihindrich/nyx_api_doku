# Chybové kódy

Tento dokument popisuje všechny možné chybové stavy a kódy v NYX.CZ API.

## HTTP Status kódy

### 200 OK
Požadavek byl úspěšně zpracován.

```json
{
  "context": {...},
  "data": {...}
}
```

### 400 Bad Request
Chyba v požadavku - neplatné parametry, chybějící povinná pole nebo nesprávný formát dat.

```json
{
  "error": true,
  "code": "VALIDATION_ERROR",
  "message": "Neplatné parametry požadavku"
}
```

**Časté příčiny:**
- Chybějící povinné parametry
- Neplatný formát dat
- Nesprávné hodnoty enum
- Překročení limitů (velikost souboru, délka textu)

### 401 Unauthorized
Chybí nebo je neplatný autentifikační token.

```json
{
  "error": true,
  "code": "UNAUTHORIZED",
  "message": "Chybí nebo neplatný autentifikační token"
}
```

**Řešení:**
- Zkontrolujte přítomnost Authorization hlavičky
- Ověřte platnost Bearer tokenu
- Obnovte token pokud vypršel

### 403 Forbidden
Nedostatečná oprávnění pro provedení akce.

```json
{
  "error": true,
  "code": "INSUFFICIENT_PERMISSIONS",
  "message": "Nedostatečná oprávnění"
}
```

**Speciální případy:**

#### NeedsConfirmation
Uživatel si nepřeje dostávat anonymní hlasy.

```json
{
  "error": true,
  "code": "NeedsConfirmation",
  "message": "Uživatel si nepreje dostavat anonymni hlasy - pokud ho chcete udelit i tak, je potreba poslat action = negative_visible"
}
```

**Řešení:** Použijte `action=negative_visible` pro potvrzení záporného hodnocení.

### 404 Not Found
Požadovaný zdroj neexistuje.

```json
{
  "error": true,
  "code": "NOT_FOUND",
  "message": "Požadovaný zdroj neexistuje"
}
```

**Časté příčiny:**
- Neexistující ID diskuze/příspěvku/souboru
- Smazaný obsah
- Nesprávná URL

### 413 Payload Too Large
Nahrávaný soubor je příliš velký.

```json
{
  "error": true,
  "code": "FILE_TOO_LARGE",
  "message": "Soubor je příliš velký"
}
```

### 415 Unsupported Media Type
Nepodporovaný typ souboru.

```json
{
  "error": true,
  "code": "UNSUPPORTED_FILE_TYPE",
  "message": "Nepodporovaný typ souboru"
}
```

### 429 Too Many Requests
Překročen limit požadavků (rate limiting).

```json
{
  "error": true,
  "code": "RATE_LIMIT_EXCEEDED",
  "message": "Překročen limit požadavků"
}
```

### 500 Internal Server Error
Vnitřní chyba serveru.

```json
{
  "error": true,
  "code": "INTERNAL_ERROR",
  "message": "Vnitřní chyba serveru"
}
```

## Specifické chybové kódy

### VALIDATION_ERROR
Chyba validace vstupních dat.

**Příčiny:**
- Neplatný formát uživatelského jména
- Příliš dlouhý text
- Neplatné ID
- Chybějící povinná pole

### UNAUTHORIZED
Problém s autentifikací.

**Příčiny:**
- Chybí Authorization hlavička
- Neplatný Bearer token
- Vypršelý token

### INSUFFICIENT_PERMISSIONS
Nedostatečná oprávnění.

**Příčiny:**
- Pokus o úpravu cizího obsahu
- Přístup k privátní diskuzi
- Nedostatečná práva pro akci

### NOT_FOUND
Zdroj neexistuje.

**Příčiny:**
- Neexistující ID
- Smazaný obsah
- Nesprávná URL

### FILE_TOO_LARGE
Soubor překračuje povolený limit.

### UNSUPPORTED_FILE_TYPE
Nepodporovaný typ souboru.

### RATE_LIMIT_EXCEEDED
Překročen limit požadavků.

### NeedsConfirmation
Speciální případ pro hodnocení.

### INTERNAL_ERROR
Vnitřní chyba serveru.

## Struktura chybové odpovědi

Všechny chybové odpovědi mají jednotnou strukturu:

```json
{
  "error": true,
  "code": "ERROR_CODE",
  "message": "Popis chyby v češtině"
}
```

### Pole

- **error**: Vždy `true` pro chybové odpovědi
- **code**: Specifický kód chyby (string)
- **message**: Lidsky čitelný popis chyby

## Doporučené postupy

### Zpracování chyb

```javascript
try {
  const response = await fetch('/api/endpoint', {
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    }
  });
  
  if (!response.ok) {
    const error = await response.json();
    
    switch (response.status) {
      case 400:
        console.error('Chyba v požadavku:', error.message);
        break;
      case 401:
        console.error('Neautorizován:', error.message);
        // Přesměrovat na přihlášení
        break;
      case 403:
        if (error.code === 'NeedsConfirmation') {
          // Speciální zpracování pro potvrzení
          console.log('Vyžaduje potvrzení');
        } else {
          console.error('Nedostatečná oprávnění:', error.message);
        }
        break;
      case 404:
        console.error('Nenalezeno:', error.message);
        break;
      case 429:
        console.error('Příliš mnoho požadavků:', error.message);
        // Implementovat exponential backoff
        break;
      case 500:
        console.error('Chyba serveru:', error.message);
        break;
      default:
        console.error('Neočekávaná chyba:', error.message);
    }
    
    return null;
  }
  
  return await response.json();
} catch (error) {
  console.error('Síťová chyba:', error);
  return null;
}
```

### Retry logika

Pro některé chyby je vhodné implementovat opakování:

```javascript
async function apiCallWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      
      if (response.status === 429) {
        // Rate limiting - čekat před dalším pokusem
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
        continue;
      }
      
      if (response.status >= 500) {
        // Server error - zkusit znovu
        if (i === maxRetries - 1) throw new Error('Server error');
        await new Promise(resolve => setTimeout(resolve, 1000));
        continue;
      }
      
      return response;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
}
```

## Ladění chyb

### Logování

Vždy logujte:
- HTTP status kód
- Chybový kód z API
- Zprávu o chybě
- Kontext požadavku (URL, parametry)

### Časté problémy

1. **401 Unauthorized**
   - Zkontrolujte formát Authorization hlavičky
   - Ověřte platnost tokenu

2. **400 Bad Request**
   - Validujte vstupní data před odesláním
   - Zkontrolujte povinná pole

3. **403 Forbidden**
   - Ověřte oprávnění uživatele
   - Pro hodnocení zkontrolujte speciální případy

4. **404 Not Found**
   - Ověřte existenci zdrojů před přístupem
   - Zkontrolujte správnost ID

5. **429 Too Many Requests**
   - Implementujte rate limiting na klientské straně
   - Používejte exponential backoff
