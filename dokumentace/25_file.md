# File API

File API umožňuje správu souborů a příloh. Poskytuje funkcionalitu pro nahrávání, mazání a správu souborů v různých kontextech platformy.

## Endpoints

### PUT /api/file/upload

Upload souboru.

**Popis**: Upload souboru

**Parametry**:
- `file` (multipart/form-data, required): Binární data souboru (binary)
- `file_type` (multipart/form-data, required): Typ souboru (FileTypeEnum)
- `id_specific` (multipart/form-data, optional): Podle typu souboru - ID diskuze, 0 pro N/A (pošta) (integer)

**Odpověď**:
- **200 OK**: Nahraný soubor
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -X PUT \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@/path/to/file.jpg" \
     -F "file_type=discussion_attachment" \
     -F "id_specific=123" \
     https://nyx.cz/api/file/upload
```

**Příklad odpovědi**:
```json
{
  "id": 456,
  "file_type": "discussion_attachment",
  "id_specific": 123,
  "id_specific2": null,
  "filename": "file.jpg",
  "size": 102400,
  "uploaded_at": "2024-01-31T20:39:42+02:00",
  "mimetype": "image/jpeg",
  "image_width": 800,
  "image_height": 600,
  "image_avg_color_hex": "#3366cc",
  "image_embed": true,
  "url": "https://nyx.cz/files/456/file.jpg",
  "thumb_url": "https://nyx.cz/files/456/thumb.jpg"
}
```

### DELETE /api/file/delete/{id}

Smaže soubor.

**Popis**: Smaže soubor

**Parametry**:
- `id` (path, required): ID souboru ke smazání (integer)

**Odpověď**:
- **200 OK**: Úspěch
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -X DELETE \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/file/delete/456
```

### POST /api/file/embed/{id}/{state}

Přepne jestli se soubor má ukládat jako odkaz nebo embedovat jako obrázek.

**Popis**: Přepne jestli se soubor má ukládat jako odkaz nebo embedovat jako obrázek

**Parametry**:
- `id` (path, required): ID souboru (integer)
- `state` (path, required): true = embedovat (boolean)

**Odpověď**:
- **200 OK**: Úspěch
- **400 Bad Request**: Chyba v požadavku

**Příklad požadavku**:
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/file/embed/456/true
```

## Datové struktury

### FileWithUrl

Kompletní informace o souboru s URL.

```json
{
  "id": "integer",
  "file_type": "FileTypeEnum",
  "id_specific": "integer | null",
  "id_specific2": "integer | null",
  "filename": "string",
  "size": "integer",
  "uploaded_at": "string (date-time)",
  "mimetype": "FileMimeTypeEnum",
  "image_width": "integer | null",
  "image_height": "integer | null",
  "image_avg_color_hex": "string | null",
  "image_embed": "boolean",
  "url": "string",
  "thumb_url": "string"
}
```

### FileTypeEnum

Typy souborů:
- `free_file` - Volný soubor
- `mail_attachment` - Příloha k poště
- `mail_backup` - Záloha pošty
- `discussion_attachment` - Příloha k diskuzi
- `discussion_backup` - Záloha diskuze
- `market_attachment` - Příloha k inzerátu
- `event_attachment` - Příloha k události

### FileMimeTypeEnum

Podporované MIME typy:
- `image/gif` - GIF obrázek
- `image/jpeg` - JPEG obrázek
- `image/png` - PNG obrázek
- `text/html` - HTML soubor
- `octet/stream` - Binární soubor

## Poznámky k implementaci

- Všechny endpointy vyžadují autentifikaci
- Upload používá PUT metodu s multipart/form-data
- `id_specific` má různý význam podle `file_type`:
  - Pro `discussion_attachment`: ID diskuze
  - Pro `mail_attachment`: 0 nebo ID konverzace
  - Pro `event_attachment`: ID události
  - Pro `market_attachment`: ID inzerátu
- `id_specific2` poskytuje dodatečný kontext pro umístění
- `image_embed` určuje, zda se obrázek zobrazí inline nebo jako odkaz
- `image_*` pole jsou vyplněna pouze pro obrázky
- `thumb_url` obsahuje URL náhledu pro obrázky
- `size` je v bajtech
- Podporované jsou především obrázky a HTML soubory

## Chybové stavy

- **400 Bad Request**: Neplatné parametry, nepodporovaný typ souboru nebo chyba v požadavku
- **401 Unauthorized**: Chybí nebo neplatný autentifikační token
- **403 Forbidden**: Nedostatečná oprávnění pro upload/mazání
- **404 Not Found**: Soubor neexistuje
- **413 Payload Too Large**: Soubor je příliš velký
- **415 Unsupported Media Type**: Nepodporovaný typ souboru
- **500 Internal Server Error**: Vnitřní chyba serveru

## Příklady použití

### Nahrání obrázku k diskuzi
```bash
curl -X PUT \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@image.jpg" \
     -F "file_type=discussion_attachment" \
     -F "id_specific=123" \
     https://nyx.cz/api/file/upload
```

### Nahrání přílohy k poště
```bash
curl -X PUT \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@document.pdf" \
     -F "file_type=mail_attachment" \
     -F "id_specific=0" \
     https://nyx.cz/api/file/upload
```

### Nahrání přílohy k události
```bash
curl -X PUT \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@poster.png" \
     -F "file_type=event_attachment" \
     -F "id_specific=456" \
     https://nyx.cz/api/file/upload
```

### Smazání souboru
```bash
curl -X DELETE \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/file/delete/456
```

### Nastavení embedování obrázku
```bash
# Zapnout embedování (zobrazit inline)
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/file/embed/456/true

# Vypnout embedování (zobrazit jako odkaz)
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://nyx.cz/api/file/embed/456/false
```

## Bezpečnostní poznámky

- Ověřte vždy typ a velikost nahrávaných souborů
- Používejte pouze důvěryhodné soubory
- Respektujte limity velikosti souborů
- Kontrolujte oprávnění před nahráváním do konkrétních kontextů
- Soubory jsou automaticky skenovány na malware
