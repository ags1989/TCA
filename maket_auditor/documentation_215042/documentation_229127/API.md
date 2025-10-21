# API Р”РѕРєСѓРјРµРЅС‚Р°С†РёСЏ

## РћР±Р·РѕСЂ API

API Miami РїСЂРµРґРѕСЃС‚Р°РІР»СЏРµС‚ RESTful РёРЅС‚РµСЂС„РµР№СЃ РґР»СЏ РёРЅС‚РµРіСЂР°С†РёРё РјРѕР±РёР»СЊРЅРѕРіРѕ РїСЂРёР»РѕР¶РµРЅРёСЏ РњРў СЃ СЃРёСЃС‚РµРјРѕР№ Track and Trace.

## Р‘Р°Р·РѕРІС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё

### Р‘Р°Р·РѕРІС‹Р№ URL
`
https://api-miami.company.com/v2
`

### РђСѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ
Р’СЃРµ Р·Р°РїСЂРѕСЃС‹ С‚СЂРµР±СѓСЋС‚ JWT С‚РѕРєРµРЅ РІ Р·Р°РіРѕР»РѕРІРєРµ Authorization:
`
Authorization: Bearer {jwt_token}
`

### Р¤РѕСЂРјР°С‚ РґР°РЅРЅС‹С…
- **Content-Type:** application/json
- **Accept:** application/json
- **Charset:** UTF-8

## РћСЃРЅРѕРІРЅС‹Рµ РјРµС‚РѕРґС‹ API

### 1. РђРІС‚РѕСЂРёР·Р°С†РёСЏ

#### POST /auth/login
РђРІС‚РѕСЂРёР·Р°С†РёСЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РІ СЃРёСЃС‚РµРјРµ.

**Р—Р°РїСЂРѕСЃ:**
`json
{
  "username": "agent001",
  "password": "password123",
  "deviceId": "device-uuid"
}
`

**РћС‚РІРµС‚:**
`json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": 3600,
  "user": {
    "id": 12345,
    "username": "agent001",
    "role": "agent",
    "permissions": ["scan_qr", "create_shipment"]
  }
}
`

**РљРѕРґС‹ РѕС€РёР±РѕРє:**
- 400 - РќРµРІРµСЂРЅС‹Рµ РїР°СЂР°РјРµС‚СЂС‹
- 401 - РќРµРІРµСЂРЅС‹Рµ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ
- 429 - РЎР»РёС€РєРѕРј РјРЅРѕРіРѕ РїРѕРїС‹С‚РѕРє

### 2. Р’Р°Р»РёРґР°С†РёСЏ QR-РєРѕРґРѕРІ

#### POST /qr/validate
Р’Р°Р»РёРґР°С†РёСЏ QR-РєРѕРґР° С‚РѕРІР°СЂР° С‡РµСЂРµР· T&T API.

**Р—Р°РїСЂРѕСЃ:**
`json
{
  "qrCode": "10000001",
  "locationId": "1000001"
}
`

**РћС‚РІРµС‚ (СѓСЃРїРµС…):**
`json
{
  "success": true,
  "data": {
    "qrCode": "10000001",
    "productId": "PROD001",
    "productName": "Cigarettes Brand A",
    "quantity": 1,
    "unitPrice": 5.50,
    "isValid": true,
    "tntResponse": {
      "code": "10000001",
      "status": "valid",
      "productInfo": {
        "name": "Cigarettes Brand A",
        "manufacturer": "Tobacco Corp",
        "barcode": "1234567890123"
      }
    }
  }
}
`

**РћС‚РІРµС‚ (РѕС€РёР±РєР°):**
`json
{
  "success": false,
  "error": {
    "code": "INVALID_QR_CODE",
    "message": "QR РєРѕРґ РЅРµ РЅР°Р№РґРµРЅ РІ СЃРёСЃС‚РµРјРµ T&T",
    "details": {
      "qrCode": "10000001",
      "tntError": "Code not found"
    }
  }
}
`

**РљРѕРґС‹ РѕС€РёР±РѕРє:**
- 400 - РќРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚ QR-РєРѕРґР°
- 404 - QR-РєРѕРґ РЅРµ РЅР°Р№РґРµРЅ
- 422 - РўРѕРІР°СЂ РЅРµРґРѕСЃС‚СѓРїРµРЅ РґР»СЏ РїСЂРѕРґР°Р¶Рё
- 503 - T&T API РЅРµРґРѕСЃС‚СѓРїРµРЅ

### 3. РЈРїСЂР°РІР»РµРЅРёРµ РѕС‚РіСЂСѓР·РєР°РјРё

#### POST /shipments
РЎРѕР·РґР°РЅРёРµ РЅРѕРІРѕР№ РѕС‚РіСЂСѓР·РєРё.

**Р—Р°РїСЂРѕСЃ:**
`json
{
  "orderId": "ORD-2024-001",
  "orderType": 0,
  "customerId": "CUST001",
  "locationId": "1000001",
  "items": [
    {
      "qrCode": "10000001",
      "productId": "PROD001",
      "quantity": 1,
      "unitPrice": 5.50
    }
  ],
  "paymentType": "cold_sale",
  "notes": "Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅР°СЏ РёРЅС„РѕСЂРјР°С†РёСЏ"
}
`

**РћС‚РІРµС‚:**
`json
{
  "success": true,
  "data": {
    "shipmentId": "SHIP-2024-001",
    "orderId": "ORD-2024-001",
    "status": "created",
    "tntStatus": "sent",
    "createdAt": "2024-01-01T10:00:00Z",
    "items": [
      {
        "qrCode": "10000001",
        "productId": "PROD001",
        "quantity": 1,
        "unitPrice": 5.50,
        "totalPrice": 5.50
      }
    ],
    "totalAmount": 5.50
  }
}
`

#### GET /shipments/{shipmentId}
РџРѕР»СѓС‡РµРЅРёРµ РёРЅС„РѕСЂРјР°С†РёРё РѕР± РѕС‚РіСЂСѓР·РєРµ.

**РћС‚РІРµС‚:**
`json
{
  "success": true,
  "data": {
    "shipmentId": "SHIP-2024-001",
    "orderId": "ORD-2024-001",
    "status": "completed",
    "tntStatus": "processed",
    "createdAt": "2024-01-01T10:00:00Z",
    "completedAt": "2024-01-01T10:05:00Z",
    "items": [...],
    "totalAmount": 5.50,
    "tntResponse": {
      "documentId": "TNT-DOC-001",
      "status": "accepted",
      "processedAt": "2024-01-01T10:03:00Z"
    }
  }
}
`

### 4. РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РґР°РЅРЅС‹С…

#### GET /products
РџРѕР»СѓС‡РµРЅРёРµ СЃРїРёСЃРєР° С‚РѕРІР°СЂРѕРІ.

**РџР°СЂР°РјРµС‚СЂС‹ Р·Р°РїСЂРѕСЃР°:**
- page (int, optional) - РќРѕРјРµСЂ СЃС‚СЂР°РЅРёС†С‹ (РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ 1)
- limit (int, optional) - РљРѕР»РёС‡РµСЃС‚РІРѕ Р·Р°РїРёСЃРµР№ (РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ 100)
- search (string, optional) - РџРѕРёСЃРє РїРѕ РЅР°Р·РІР°РЅРёСЋ
- category (string, optional) - Р¤РёР»СЊС‚СЂ РїРѕ РєР°С‚РµРіРѕСЂРёРё

**РћС‚РІРµС‚:**
`json
{
  "success": true,
  "data": {
    "products": [
      {
        "id": "PROD001",
        "name": "Cigarettes Brand A",
        "category": "tobacco",
        "unitPrice": 5.50,
        "isActive": true,
        "qrCodes": ["10000001", "10000002"]
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 100,
      "total": 1500,
      "pages": 15
    }
  }
}
`

#### GET /locations
РџРѕР»СѓС‡РµРЅРёРµ СЃРїРёСЃРєР° С‚РѕСЂРіРѕРІС‹С… С‚РѕС‡РµРє.

**РћС‚РІРµС‚:**
`json
{
  "success": true,
  "data": [
    {
      "id": "1000001",
      "name": "РўРѕСЂРіРѕРІР°СЏ С‚РѕС‡РєР° 1",
      "address": "СѓР». РџСЂРёРјРµСЂРЅР°СЏ, 1",
      "isActive": true,
      "tntConfig": {
        "departFromExtId": "1000001",
        "partnerFiscalId": "9871000001"
      }
    }
  ]
}
`

## РћР±СЂР°Р±РѕС‚РєР° РѕС€РёР±РѕРє

### РЎС‚Р°РЅРґР°СЂС‚РЅС‹Р№ С„РѕСЂРјР°С‚ РѕС€РёР±РєРё
`json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Р§РµР»РѕРІРµРєРѕС‡РёС‚Р°РµРјРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ",
    "details": {
      "field": "Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅР°СЏ РёРЅС„РѕСЂРјР°С†РёСЏ"
    },
    "timestamp": "2024-01-01T10:00:00Z",
    "requestId": "req-uuid"
  }
}
`

### РљРѕРґС‹ РѕС€РёР±РѕРє

#### РљР»РёРµРЅС‚СЃРєРёРµ РѕС€РёР±РєРё (4xx)
- 400 Bad Request - РќРµРІРµСЂРЅС‹Р№ С„РѕСЂРјР°С‚ Р·Р°РїСЂРѕСЃР°
- 401 Unauthorized - РћС‚СЃСѓС‚СЃС‚РІСѓРµС‚ РёР»Рё РЅРµРІРµСЂРЅС‹Р№ С‚РѕРєРµРЅ
- 403 Forbidden - РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ
- 404 Not Found - Р РµСЃСѓСЂСЃ РЅРµ РЅР°Р№РґРµРЅ
- 422 Unprocessable Entity - РћС€РёР±РєР° РІР°Р»РёРґР°С†РёРё РґР°РЅРЅС‹С…
- 429 Too Many Requests - РџСЂРµРІС‹С€РµРЅ Р»РёРјРёС‚ Р·Р°РїСЂРѕСЃРѕРІ

#### РЎРµСЂРІРµСЂРЅС‹Рµ РѕС€РёР±РєРё (5xx)
- 500 Internal Server Error - Р’РЅСѓС‚СЂРµРЅРЅСЏСЏ РѕС€РёР±РєР° СЃРµСЂРІРµСЂР°
- 502 Bad Gateway - РћС€РёР±РєР° РІРЅРµС€РЅРµРіРѕ СЃРµСЂРІРёСЃР°
- 503 Service Unavailable - РЎРµСЂРІРёСЃ РІСЂРµРјРµРЅРЅРѕ РЅРµРґРѕСЃС‚СѓРїРµРЅ
- 504 Gateway Timeout - РўР°Р№РјР°СѓС‚ РІРЅРµС€РЅРµРіРѕ СЃРµСЂРІРёСЃР°

## Rate Limiting

### Р›РёРјРёС‚С‹ Р·Р°РїСЂРѕСЃРѕРІ
- **РћР±С‰РёРµ Р·Р°РїСЂРѕСЃС‹:** 1000 Р·Р°РїСЂРѕСЃРѕРІ РІ С‡Р°СЃ
- **QR РІР°Р»РёРґР°С†РёСЏ:** 100 Р·Р°РїСЂРѕСЃРѕРІ РІ РјРёРЅСѓС‚Сѓ
- **РЎРѕР·РґР°РЅРёРµ РѕС‚РіСЂСѓР·РѕРє:** 50 Р·Р°РїСЂРѕСЃРѕРІ РІ РјРёРЅСѓС‚Сѓ

### Р—Р°РіРѕР»РѕРІРєРё РѕС‚РІРµС‚Р°
`
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
`

## Р’РµСЂСЃРёРѕРЅРёСЂРѕРІР°РЅРёРµ

### РџРѕРґРґРµСЂР¶РёРІР°РµРјС‹Рµ РІРµСЂСЃРёРё
- **v2.0** (С‚РµРєСѓС‰Р°СЏ) - РџРѕР»РЅР°СЏ С„СѓРЅРєС†РёРѕРЅР°Р»СЊРЅРѕСЃС‚СЊ T&T
- **v1.0** (deprecated) - Р‘Р°Р·РѕРІР°СЏ С„СѓРЅРєС†РёРѕРЅР°Р»СЊРЅРѕСЃС‚СЊ

### РњРёРіСЂР°С†РёСЏ РІРµСЂСЃРёР№
РџСЂРё РёР·РјРµРЅРµРЅРёРё РІРµСЂСЃРёРё API:
1. РЈРІРµРґРѕРјР»РµРЅРёРµ Р·Р° 30 РґРЅРµР№
2. РџРѕРґРґРµСЂР¶РєР° СЃС‚Р°СЂРѕР№ РІРµСЂСЃРёРё 90 РґРЅРµР№
3. РђРІС‚РѕРјР°С‚РёС‡РµСЃРєРѕРµ РїРµСЂРµРЅР°РїСЂР°РІР»РµРЅРёРµ РЅР° РЅРѕРІСѓСЋ РІРµСЂСЃРёСЋ

## РџСЂРёРјРµСЂС‹ РёСЃРїРѕР»СЊР·РѕРІР°РЅРёСЏ

### JavaScript/TypeScript
`	ypescript
class MiamiApiClient {
  private baseUrl = 'https://api-miami.company.com/v2';
  private token: string;

  async validateQR(qrCode: string): Promise<QRValidationResult> {
    const response = await fetch(${this.baseUrl}/qr/validate, {
      method: 'POST',
      headers: {
        'Authorization': Bearer ,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ qrCode })
    });
    
    return await response.json();
  }
}
`

### C# (.NET)
`csharp
public class MiamiApiClient
{
    private readonly HttpClient _httpClient;
    private readonly string _baseUrl = "https://api-miami.company.com/v2";

    public async Task<QRValidationResult> ValidateQRAsync(string qrCode)
    {
        var request = new { qrCode };
        var response = await _httpClient.PostAsJsonAsync($"{_baseUrl}/qr/validate", request);
        return await response.Content.ReadFromJsonAsync<QRValidationResult>();
    }
}
`

---
*API РґРѕРєСѓРјРµРЅС‚Р°С†РёСЏ РѕСЃРЅРѕРІР°РЅР° РЅР° РґР°РЅРЅС‹С… РёР· Р·Р°РїСЂРѕСЃР° 229127*
