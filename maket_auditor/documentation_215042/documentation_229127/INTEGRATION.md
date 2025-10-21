# РРЅС‚РµРіСЂР°С†РёСЏ СЃ РІРЅРµС€РЅРёРјРё СЃРёСЃС‚РµРјР°РјРё

## РћР±Р·РѕСЂ РёРЅС‚РµРіСЂР°С†РёР№

РЎРёСЃС‚РµРјР° РёРЅС‚РµРіСЂР°С†РёРё РњРў СЃ Track and Trace РІР·Р°РёРјРѕРґРµР№СЃС‚РІСѓРµС‚ СЃ РЅРµСЃРєРѕР»СЊРєРёРјРё РІРЅРµС€РЅРёРјРё СЃРёСЃС‚РµРјР°РјРё РґР»СЏ РѕР±РµСЃРїРµС‡РµРЅРёСЏ РїРѕР»РЅРѕРіРѕ С†РёРєР»Р° РѕР±СЂР°Р±РѕС‚РєРё С‚РѕРІР°СЂРѕРІ РѕС‚ СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ РґРѕ РїРµСЂРµРґР°С‡Рё РґР°РЅРЅС‹С… РІ РєРѕСЂРїРѕСЂР°С‚РёРІРЅС‹Рµ СЃРёСЃС‚РµРјС‹.

## Track and Trace API

### РћРїРёСЃР°РЅРёРµ РёРЅС‚РµРіСЂР°С†РёРё
Track and Trace (T&T) - РІРЅРµС€РЅСЏСЏ СЃРёСЃС‚РµРјР° РґР»СЏ РІР°Р»РёРґР°С†РёРё QR-РєРѕРґРѕРІ С‚РѕРІР°СЂРѕРІ Рё РѕР±СЂР°Р±РѕС‚РєРё РѕС‚РіСЂСѓР·РѕРє. РРЅС‚РµРіСЂР°С†РёСЏ РѕСЃСѓС‰РµСЃС‚РІР»СЏРµС‚СЃСЏ С‡РµСЂРµР· REST API.

### РўРµС…РЅРёС‡РµСЃРєРёРµ РґРµС‚Р°Р»Рё
- **РџСЂРѕС‚РѕРєРѕР»:** HTTPS
- **Р¤РѕСЂРјР°С‚ РґР°РЅРЅС‹С…:** JSON
- **РђСѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ:** Bearer Token
- **Р›РёРјРёС‚С‹:** 2 Р·Р°РїСЂРѕСЃР° РІ СЃРµРєСѓРЅРґСѓ
- **РўР°Р№РјР°СѓС‚:** 30 СЃРµРєСѓРЅРґ

### РћСЃРЅРѕРІРЅС‹Рµ РјРµС‚РѕРґС‹ API

#### 1. РђРІС‚РѕСЂРёР·Р°С†РёСЏ
`http
POST https://api.trackandtrace.az/login_api
Content-Type: application/json

{
  "username": "9941234567",
  "password": "qwerty"
}
`

**РћС‚РІРµС‚:**
`json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
`

#### 2. Р’Р°Р»РёРґР°С†РёСЏ QR-РєРѕРґР°
`http
POST https://api.trackandtrace.az/code_info
Authorization: Bearer {token}
Content-Type: application/json

{
  "code": "10000001"
}
`

**РћС‚РІРµС‚ (СѓСЃРїРµС…):**
`json
{
  "success": true,
  "data": {
    "code": "10000001",
    "status": "valid",
    "product_info": {
      "name": "Cigarettes Brand A",
      "manufacturer": "Tobacco Corp",
      "barcode": "1234567890123"
    }
  }
}
`

**РћС‚РІРµС‚ (РѕС€РёР±РєР°):**
`json
{
  "success": false,
  "error": {
    "code": "CODE_NOT_FOUND",
    "message": "QR РєРѕРґ РЅРµ РЅР°Р№РґРµРЅ РІ СЃРёСЃС‚РµРјРµ"
  }
}
`

#### 3. РЎРѕР·РґР°РЅРёРµ РѕС‚РіСЂСѓР·РєРё
`http
POST https://api.trackandtrace.az/make_shipping
Authorization: Bearer {token}
Content-Type: application/json

{
  "doc_ext_id": "1000001",
  "dat": "2025-01-01",
  "num": "12345",
  "depart_from_ext_id": "1000001",
  "depart_to_ext_id": "1000002",
  "partner_fiscal_id": "9871000002",
  "items": [
    {
      "code": "10000001",
      "quantity": 1,
      "price": 5.50
    }
  ]
}
`

**РћС‚РІРµС‚:**
`json
{
  "success": true,
  "data": {
    "document_id": "TNT-DOC-001",
    "status": "accepted",
    "processed_at": "2025-01-01T10:00:00Z"
  }
}
`

### РћР±СЂР°Р±РѕС‚РєР° РѕС€РёР±РѕРє
- **Retry РјРµС…Р°РЅРёР·Рј:** 3 РїРѕРїС‹С‚РєРё СЃ СЌРєСЃРїРѕРЅРµРЅС†РёР°Р»СЊРЅРѕР№ Р·Р°РґРµСЂР¶РєРѕР№
- **РљСЌС€РёСЂРѕРІР°РЅРёРµ:** РўРѕРєРµРЅС‹ Р°РІС‚РѕСЂРёР·Р°С†РёРё РєСЌС€РёСЂСѓСЋС‚СЃСЏ РЅР° 1 С‡Р°СЃ
- **Р›РѕРіРёСЂРѕРІР°РЅРёРµ:** Р’СЃРµ Р·Р°РїСЂРѕСЃС‹ Рё РѕС‚РІРµС‚С‹ Р»РѕРіРёСЂСѓСЋС‚СЃСЏ

## SAP (С‡РµСЂРµР· ST Р РµРїР»РёРєР°С†РёСЋ)

### РћРїРёСЃР°РЅРёРµ РёРЅС‚РµРіСЂР°С†РёРё
SAP - РєРѕСЂРїРѕСЂР°С‚РёРІРЅР°СЏ СЃРёСЃС‚РµРјР° РґР»СЏ СѓРїСЂР°РІР»РµРЅРёСЏ С‚РѕРІР°СЂР°РјРё Рё РѕС‚РіСЂСѓР·РєР°РјРё. РРЅС‚РµРіСЂР°С†РёСЏ РѕСЃСѓС‰РµСЃС‚РІР»СЏРµС‚СЃСЏ С‡РµСЂРµР· ST Р РµРїР»РёРєР°С†РёСЋ.

### РќР°РїСЂР°РІР»РµРЅРёСЏ РґР°РЅРЅС‹С…

#### Р’С…РѕРґСЏС‰РёРµ РґР°РЅРЅС‹Рµ (SAP в†’ Р§РёРєР°РіРѕ)
- **РЎРїСЂР°РІРѕС‡РЅРёРє С‚РѕРІР°СЂРѕРІ** - РЅРѕРјРµРЅРєР»Р°С‚СѓСЂР°, С…Р°СЂР°РєС‚РµСЂРёСЃС‚РёРєРё
- **РћСЃС‚Р°С‚РєРё С‚РѕРІР°СЂРѕРІ** - С‚РµРєСѓС‰РёРµ РѕСЃС‚Р°С‚РєРё РЅР° СЃРєР»Р°РґР°С…
- **РЎРїСЂР°РІРѕС‡РЅРёРєРё** - РєР»РёРµРЅС‚С‹, РґРµРїР°СЂС‚Р°РјРµРЅС‚С‹, РµРґРёРЅРёС†С‹ РёР·РјРµСЂРµРЅРёСЏ

#### РСЃС…РѕРґСЏС‰РёРµ РґР°РЅРЅС‹Рµ (Р§РёРєР°РіРѕ в†’ SAP)
- **Р”РѕРєСѓРјРµРЅС‚С‹ РѕС‚РіСЂСѓР·РєРё** - РёРЅС„РѕСЂРјР°С†РёСЏ РѕР± РѕС‚РіСЂСѓР¶РµРЅРЅС‹С… С‚РѕРІР°СЂР°С…
- **QR-РєРѕРґС‹ С‚РѕРІР°СЂРѕРІ** - РїСЂРёРІСЏР·РєР° РєРѕРґРѕРІ Рє С‚РѕРІР°СЂР°Рј
- **РЎС‚Р°С‚СѓСЃС‹ РѕРїРµСЂР°С†РёР№** - СЂРµР·СѓР»СЊС‚Р°С‚С‹ РѕР±СЂР°Р±РѕС‚РєРё

### РЎС…РµРјР° СЂРµРїР»РёРєР°С†РёРё
`
SAP в†’ ST Р РµРїР»РёРєР°С†РёСЏ в†’ Р§РёРєР°РіРѕ в†’ API Miami в†’ РњРў
`

### РўР°Р±Р»РёС†С‹ СЂРµРїР»РёРєР°С†РёРё

#### Р’С…РѕРґСЏС‰РёРµ С‚Р°Р±Р»РёС†С‹:
- SAP_Products - С‚РѕРІР°СЂС‹ РёР· SAP
- SAP_Customers - РєР»РёРµРЅС‚С‹ РёР· SAP
- SAP_Departments - РґРµРїР°СЂС‚Р°РјРµРЅС‚С‹ РёР· SAP

#### РСЃС…РѕРґСЏС‰РёРµ С‚Р°Р±Р»РёС†С‹:
- SAP_Shipments - РѕС‚РіСЂСѓР·РєРё РІ SAP
- SAP_QRCodeMapping - РїСЂРёРІСЏР·РєР° QR-РєРѕРґРѕРІ Рє С‚РѕРІР°СЂР°Рј

## Р‘Р°Р·Р° РґР°РЅРЅС‹С… Р§РёРєР°РіРѕ

### Р РѕР»СЊ РІ РёРЅС‚РµРіСЂР°С†РёРё
Р§РёРєР°РіРѕ СЃР»СѓР¶РёС‚ С†РµРЅС‚СЂР°Р»СЊРЅРѕР№ Р±Р°Р·РѕР№ РґР°РЅРЅС‹С… РґР»СЏ С…СЂР°РЅРµРЅРёСЏ РёРЅС„РѕСЂРјР°С†РёРё Рѕ С‚РѕРІР°СЂР°С…, QR-РєРѕРґР°С… Рё РѕС‚РіСЂСѓР·РєР°С….

### РћСЃРЅРѕРІРЅС‹Рµ С„СѓРЅРєС†РёРё
- **РљСЌС€РёСЂРѕРІР°РЅРёРµ РґР°РЅРЅС‹С… T&T** - РґР»СЏ СѓСЃРєРѕСЂРµРЅРёСЏ СЂР°Р±РѕС‚С‹
- **РҐСЂР°РЅРµРЅРёРµ РёСЃС‚РѕСЂРёРё РѕРїРµСЂР°С†РёР№** - РґР»СЏ Р°СѓРґРёС‚Р° Рё РѕС‚Р»Р°РґРєРё
- **РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ СЃ SAP** - С‡РµСЂРµР· ST Р РµРїР»РёРєР°С†РёСЋ
- **РЈРїСЂР°РІР»РµРЅРёРµ СЃРµСЃСЃРёСЏРјРё** - РґР»СЏ РїРѕР»СЊР·РѕРІР°С‚РµР»РµР№ РњРў

### РЎС…РµРјР° РґР°РЅРЅС‹С…
`sql
-- РћСЃРЅРѕРІРЅС‹Рµ С‚Р°Р±Р»РёС†С‹
Products (С‚РѕРІР°СЂС‹)
в”њв”Ђв”Ђ QRCodes (QR-РєРѕРґС‹)
в”њв”Ђв”Ђ Shipments (РѕС‚РіСЂСѓР·РєРё)
в”‚   в”њв”Ђв”Ђ ShipmentItems (РїРѕР·РёС†РёРё РѕС‚РіСЂСѓР·РєРё)
в”‚   в””в”Ђв”Ђ ShipmentQRCodes (QR-РєРѕРґС‹ РІ РѕС‚РіСЂСѓР·РєРµ)
в””в”Ђв”Ђ SAP_* (С‚Р°Р±Р»РёС†С‹ СЂРµРїР»РёРєР°С†РёРё)
`

## РњРѕР±РёР»СЊРЅРѕРµ РїСЂРёР»РѕР¶РµРЅРёРµ РњРў

### РРЅС‚РµРіСЂР°С†РёСЏ СЃ API Miami
РњРѕР±РёР»СЊРЅРѕРµ РїСЂРёР»РѕР¶РµРЅРёРµ РІР·Р°РёРјРѕРґРµР№СЃС‚РІСѓРµС‚ СЃ API Miami РґР»СЏ РІСЃРµС… РѕРїРµСЂР°С†РёР№ СЃ С‚РѕРІР°СЂР°РјРё Рё РѕС‚РіСЂСѓР·РєР°РјРё.

### РћСЃРЅРѕРІРЅС‹Рµ С„СѓРЅРєС†РёРё
- **РЎРєР°РЅРёСЂРѕРІР°РЅРёРµ QR-РєРѕРґРѕРІ** - С‡РµСЂРµР· РєР°РјРµСЂСѓ СѓСЃС‚СЂРѕР№СЃС‚РІР°
- **Р’Р°Р»РёРґР°С†РёСЏ С‚РѕРІР°СЂРѕРІ** - С‡РµСЂРµР· API Miami в†’ T&T
- **РЎРѕР·РґР°РЅРёРµ РѕС‚РіСЂСѓР·РѕРє** - СЃ СЂР°Р·Р»РёС‡РЅС‹РјРё С‚РёРїР°РјРё РѕРїР»Р°С‚С‹
- **РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РґР°РЅРЅС‹С…** - СЃ СЃРµСЂРІРµСЂРѕРј

### РЎС…РµРјР° РІР·Р°РёРјРѕРґРµР№СЃС‚РІРёСЏ
`
РњРў в†’ API Miami в†’ T&T API
  в†“
Р§РёРєР°РіРѕ в†ђ ST Р РµРїР»РёРєР°С†РёСЏ в†ђ SAP
`

## РћР±СЂР°Р±РѕС‚РєР° РѕС€РёР±РѕРє РёРЅС‚РµРіСЂР°С†РёРё

### РўРёРїС‹ РѕС€РёР±РѕРє

#### 1. РћС€РёР±РєРё СЃРµС‚Рё
- **РЎРёРјРїС‚РѕРјС‹:** РўР°Р№РјР°СѓС‚С‹, РЅРµРґРѕСЃС‚СѓРїРЅРѕСЃС‚СЊ СЃРµСЂРІРёСЃРѕРІ
- **РћР±СЂР°Р±РѕС‚РєР°:** Retry РјРµС…Р°РЅРёР·Рј, РєСЌС€РёСЂРѕРІР°РЅРёРµ
- **Р›РѕРіРёСЂРѕРІР°РЅРёРµ:** РЈСЂРѕРІРµРЅСЊ Warning

#### 2. РћС€РёР±РєРё Р°РІС‚РѕСЂРёР·Р°С†РёРё
- **РЎРёРјРїС‚РѕРјС‹:** 401 Unauthorized, РёСЃС‚РµРєС€РёР№ С‚РѕРєРµРЅ
- **РћР±СЂР°Р±РѕС‚РєР°:** РћР±РЅРѕРІР»РµРЅРёРµ С‚РѕРєРµРЅР°, РїРѕРІС‚РѕСЂРЅР°СЏ Р°РІС‚РѕСЂРёР·Р°С†РёСЏ
- **Р›РѕРіРёСЂРѕРІР°РЅРёРµ:** РЈСЂРѕРІРµРЅСЊ Error

#### 3. РћС€РёР±РєРё РІР°Р»РёРґР°С†РёРё
- **РЎРёРјРїС‚РѕРјС‹:** РќРµРІР°Р»РёРґРЅС‹Рµ QR-РєРѕРґС‹, РѕС€РёР±РєРё РґР°РЅРЅС‹С…
- **РћР±СЂР°Р±РѕС‚РєР°:** Р”РѕР±Р°РІР»РµРЅРёРµ РІ СЃРїРёСЃРѕРє РѕС€РёР±РѕРє, СѓРІРµРґРѕРјР»РµРЅРёРµ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ
- **Р›РѕРіРёСЂРѕРІР°РЅРёРµ:** РЈСЂРѕРІРµРЅСЊ Information

### РЎС‚СЂР°С‚РµРіРёРё РІРѕСЃСЃС‚Р°РЅРѕРІР»РµРЅРёСЏ

#### 1. Retry РјРµС…Р°РЅРёР·Рј
`csharp
public async Task<T> ExecuteWithRetry<T>(Func<Task<T>> operation, int maxRetries = 3)
{
    for (int i = 0; i < maxRetries; i++)
    {
        try
        {
            return await operation();
        }
        catch (Exception ex) when (i < maxRetries - 1)
        {
            await Task.Delay(TimeSpan.FromSeconds(Math.Pow(2, i)));
            _logger.LogWarning($"Retry {i + 1} for operation failed: {ex.Message}");
        }
    }
    throw new Exception("Operation failed after all retries");
}
`

#### 2. Circuit Breaker
`csharp
public class CircuitBreaker
{
    private int _failureCount = 0;
    private DateTime _lastFailureTime = DateTime.MinValue;
    private readonly int _threshold = 5;
    private readonly TimeSpan _timeout = TimeSpan.FromMinutes(1);

    public bool IsOpen => _failureCount >= _threshold && 
                         DateTime.UtcNow - _lastFailureTime < _timeout;
}
`

## РњРѕРЅРёС‚РѕСЂРёРЅРі РёРЅС‚РµРіСЂР°С†РёР№

### РњРµС‚СЂРёРєРё
- **РљРѕР»РёС‡РµСЃС‚РІРѕ Р·Р°РїСЂРѕСЃРѕРІ** Рє T&T API
- **Р’СЂРµРјСЏ РѕС‚РІРµС‚Р°** РІРЅРµС€РЅРёС… СЃРµСЂРІРёСЃРѕРІ
- **РљРѕР»РёС‡РµСЃС‚РІРѕ РѕС€РёР±РѕРє** РїРѕ С‚РёРїР°Рј
- **РЎС‚Р°С‚СѓСЃ РёРЅС‚РµРіСЂР°С†РёР№** (UP/DOWN)

### Health Checks
`csharp
services.AddHealthChecks()
    .AddCheck<TnTApiHealthCheck>("tnt-api")
    .AddCheck<SapReplicationHealthCheck>("sap-replication")
    .AddCheck<ChicagoDatabaseHealthCheck>("chicago-db");
`

### РђР»РµСЂС‚С‹
- **РќРµРґРѕСЃС‚СѓРїРЅРѕСЃС‚СЊ T&T API** > 5 РјРёРЅСѓС‚
- **Р’С‹СЃРѕРєРёР№ РїСЂРѕС†РµРЅС‚ РѕС€РёР±РѕРє** > 10%
- **РњРµРґР»РµРЅРЅС‹Рµ РѕС‚РІРµС‚С‹** > 30 СЃРµРєСѓРЅРґ
- **РџСЂРѕР±Р»РµРјС‹ СЃ СЂРµРїР»РёРєР°С†РёРµР№ SAP** > 1 С‡Р°СЃ

## Р‘РµР·РѕРїР°СЃРЅРѕСЃС‚СЊ РёРЅС‚РµРіСЂР°С†РёР№

### РђСѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ
- **T&T API:** Bearer Token СЃ РёСЃС‚РµС‡РµРЅРёРµРј
- **SAP:** РЎРµСЂС‚РёС„РёРєР°С‚С‹ РєР»РёРµРЅС‚Р°
- **РњРў:** JWT С‚РѕРєРµРЅС‹

### РЁРёС„СЂРѕРІР°РЅРёРµ
- **HTTPS** РґР»СЏ РІСЃРµС… РІРЅРµС€РЅРёС… СЃРѕРµРґРёРЅРµРЅРёР№
- **TLS 1.2+** РґР»СЏ Р·Р°С‰РёС‚С‹ РґР°РЅРЅС‹С…
- **РЁРёС„СЂРѕРІР°РЅРёРµ РїР°СЂРѕР»РµР№** РІ РєРѕРЅС„РёРіСѓСЂР°С†РёРё

### РђСѓРґРёС‚
- **Р›РѕРіРёСЂРѕРІР°РЅРёРµ РІСЃРµС… Р·Р°РїСЂРѕСЃРѕРІ** Рє РІРЅРµС€РЅРёРј API
- **РћС‚СЃР»РµР¶РёРІР°РЅРёРµ РёР·РјРµРЅРµРЅРёР№** РІ РєСЂРёС‚РёС‡РµСЃРєРёС… РґР°РЅРЅС‹С…
- **РњРѕРЅРёС‚РѕСЂРёРЅРі РґРѕСЃС‚СѓРїР°** Рє СЃРёСЃС‚РµРјР°Рј

## РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ РёРЅС‚РµРіСЂР°С†РёР№

### T&T API
`json
{
  "TnTApi": {
    "BaseUrl": "https://api.trackandtrace.az",
    "TimeoutSeconds": 30,
    "RetryCount": 3,
    "RateLimit": {
      "MaxRequestsPerSecond": 2,
      "BurstLimit": 5
    }
  }
}
`

### ST Р РµРїР»РёРєР°С†РёСЏ
`json
{
  "SapReplication": {
    "ConnectionString": "Server=sap-server;Database=Replication;Trusted_Connection=true;",
    "SyncIntervalMinutes": 15,
    "BatchSize": 1000,
    "RetryCount": 3
  }
}
`

## РўРµСЃС‚РёСЂРѕРІР°РЅРёРµ РёРЅС‚РµРіСЂР°С†РёР№

### Unit Tests
`csharp
[Test]
public async Task TnTApiService_ValidateQRCode_ValidCode_ReturnsSuccess()
{
    // Arrange
    var qrCode = "10000001";
    var expectedResponse = new TnTValidationResponse { Success = true };
    
    _mockHttpClient
        .Setup(x => x.PostAsJsonAsync(It.IsAny<string>(), It.IsAny<object>()))
        .ReturnsAsync(new HttpResponseMessage
        {
            StatusCode = HttpStatusCode.OK,
            Content = new StringContent(JsonSerializer.Serialize(expectedResponse))
        });
    
    // Act
    var result = await _tnTApiService.ValidateQRCodeAsync(qrCode);
    
    // Assert
    Assert.IsTrue(result.Success);
}
`

### Integration Tests
`csharp
[Test]
public async Task EndToEnd_ShipmentCreation_WithTnTIntegration()
{
    // Arrange
    var shipmentRequest = new ShipmentRequest
    {
        OrderId = "ORD-001",
        LocationId = "1000001",
        OrderType = 0, // Cold Sale
        Items = new List<ShipmentItemRequest>
        {
            new() { QRCode = "10000001", Quantity = 1, UnitPrice = 5.50 }
        }
    };
    
    // Act
    var result = await _shipmentService.CreateShipmentAsync(shipmentRequest);
    
    // Assert
    Assert.IsTrue(result.Success);
    Assert.IsNotNull(result.ShipmentId);
    
    // РџСЂРѕРІРµСЂРєР° РѕС‚РїСЂР°РІРєРё РІ T&T
    var tntLogs = await _context.TnTApiLogs
        .Where(x => x.Endpoint.Contains("make_shipping"))
        .ToListAsync();
    
    Assert.IsTrue(tntLogs.Any());
}
`

## РџСЂРѕРёР·РІРѕРґРёС‚РµР»СЊРЅРѕСЃС‚СЊ РёРЅС‚РµРіСЂР°С†РёР№

### РћРїС‚РёРјРёР·Р°С†РёСЏ Р·Р°РїСЂРѕСЃРѕРІ
- **РџР°РєРµС‚РЅР°СЏ РѕР±СЂР°Р±РѕС‚РєР°** - РіСЂСѓРїРїРёСЂРѕРІРєР° Р·Р°РїСЂРѕСЃРѕРІ
- **РљСЌС€РёСЂРѕРІР°РЅРёРµ** - РєСЌС€ С‡Р°СЃС‚Рѕ РёСЃРїРѕР»СЊР·СѓРµРјС‹С… РґР°РЅРЅС‹С…
- **РђСЃРёРЅС…СЂРѕРЅРЅР°СЏ РѕР±СЂР°Р±РѕС‚РєР°** - РЅРµР±Р»РѕРєРёСЂСѓСЋС‰РёРµ РѕРїРµСЂР°С†РёРё

### РњРѕРЅРёС‚РѕСЂРёРЅРі РїСЂРѕРёР·РІРѕРґРёС‚РµР»СЊРЅРѕСЃС‚Рё
`csharp
public class PerformanceMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<PerformanceMiddleware> _logger;

    public async Task InvokeAsync(HttpContext context)
    {
        var stopwatch = Stopwatch.StartNew();
        
        await _next(context);
        
        stopwatch.Stop();
        
        if (stopwatch.ElapsedMilliseconds > 1000)
        {
            _logger.LogWarning("Slow request: {Method} {Path} took {ElapsedMs}ms",
                context.Request.Method,
                context.Request.Path,
                stopwatch.ElapsedMilliseconds);
        }
    }
}
`

---
*РРЅС‚РµРіСЂР°С†РёРё РѕСЃРЅРѕРІР°РЅС‹ РЅР° РґР°РЅРЅС‹С… РёР· Р·Р°РїСЂРѕСЃР° 229127 Рё RnD Backlog Item 224168*
