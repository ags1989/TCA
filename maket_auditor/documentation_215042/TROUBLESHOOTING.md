# Р РµС€РµРЅРёРµ РїСЂРѕР±Р»РµРј

## РћР±Р·РѕСЂ РґРёР°РіРЅРѕСЃС‚РёРєРё

Р”Р°РЅРЅС‹Р№ СЂР°Р·РґРµР» СЃРѕРґРµСЂР¶РёС‚ РёРЅС„РѕСЂРјР°С†РёСЋ Рѕ РґРёР°РіРЅРѕСЃС‚РёРєРµ Рё СЂРµС€РµРЅРёРё РїСЂРѕР±Р»РµРј, РІРѕР·РЅРёРєР°СЋС‰РёС… РІ СЃРёСЃС‚РµРјРµ РёРЅС‚РµРіСЂР°С†РёРё РњРў СЃ Track and Trace.

## Р§Р°СЃС‚С‹Рµ РїСЂРѕР±Р»РµРјС‹

### 1. РћС€РёР±РєРё Р°РІС‚РѕСЂРёР·Р°С†РёРё РІ T&T

#### РЎРёРјРїС‚РѕРјС‹
- РЎРѕРѕР±С‰РµРЅРёРµ "РќРµ СѓРґР°РµС‚СЃСЏ Р°РІС‚РѕСЂРёР·РѕРІР°С‚СЊСЃСЏ РІ T&T"
- HTTP 401 Unauthorized
- РћС€РёР±РєР° "Token expired"

#### Р”РёР°РіРЅРѕСЃС‚РёРєР°
`ash
# РџСЂРѕРІРµСЂРєР° РїРѕРґРєР»СЋС‡РµРЅРёСЏ Рє T&T API
curl -X POST https://api.trackandtrace.az/alive \
  -H "Content-Type: application/json" \
  -d "{}"

# РџСЂРѕРІРµСЂРєР° Р°РІС‚РѕСЂРёР·Р°С†РёРё
curl -X POST https://api.trackandtrace.az/login_api \
  -H "Content-Type: application/json" \
  -d '{"username":"9941234567","password":"qwerty"}'
`

#### Р РµС€РµРЅРёСЏ
1. **РџСЂРѕРІРµСЂРёС‚СЊ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ:**
   `csharp
   // РџСЂРѕРІРµСЂРєР° РІ РєРѕРЅС„РёРіСѓСЂР°С†РёРё
   var username = _configuration["TnTAuth:Username"];
   var password = _configuration["TnTAuth:Password"];
   `

2. **РћР±РЅРѕРІРёС‚СЊ С‚РѕРєРµРЅ:**
   `csharp
   public async Task<string> RefreshTokenAsync()
   {
       var authRequest = new { username = _username, password = _password };
       var response = await _httpClient.PostAsJsonAsync("/login_api", authRequest);
       var result = await response.Content.ReadFromJsonAsync<AuthResponse>();
       return result.Token;
   }
   `

3. **РџСЂРѕРІРµСЂРёС‚СЊ РёСЃС‚РµС‡РµРЅРёРµ С‚РѕРєРµРЅР°:**
   `csharp
   if (DateTime.UtcNow > _tokenExpiryTime.AddMinutes(-10))
   {
       await RefreshTokenAsync();
   }
   `

### 2. QR-РєРѕРґС‹ РЅРµ РґРѕР±Р°РІР»СЏСЋС‚СЃСЏ РІ СЃРїРёСЃРѕРє

#### РЎРёРјРїС‚РѕРјС‹
- РћС‚СЃРєР°РЅРёСЂРѕРІР°РЅРЅС‹Рµ QR-РєРѕРґС‹ РЅРµ РѕС‚РѕР±СЂР°Р¶Р°СЋС‚СЃСЏ РІ СЃРїРёСЃРєРµ
- РўРѕРІР°СЂС‹ СЃ РѕС€РёР±РєР°РјРё РЅРµ РїРѕРїР°РґР°СЋС‚ РІ СЃРїРёСЃРѕРє РѕС€РёР±РѕРє

#### Р”РёР°РіРЅРѕСЃС‚РёРєР°
`javascript
// РџСЂРѕРІРµСЂРєР° СѓСЃР»РѕРІРёСЏ РґРѕР±Р°РІР»РµРЅРёСЏ РІ СЃРїРёСЃРѕРє
if (!validatinResult.success && skuData === null) {
    addToErrorList(qrCode, validationResult);
} else if (validatinResult.success) {
    addToScanList(validationResult);
}
`

#### Р РµС€РµРЅРёСЏ
1. **РСЃРїСЂР°РІРёС‚СЊ СѓСЃР»РѕРІРёРµ РІР°Р»РёРґР°С†РёРё:**
   `javascript
   // РЎС‚Р°СЂРѕРµ (РЅРµРїСЂР°РІРёР»СЊРЅРѕРµ) СѓСЃР»РѕРІРёРµ
   if (!validatinResult.success && 'errorCode' in validatinResult) {
       // РЅРµ РґРѕР±Р°РІР»СЏС‚СЊ РІ СЃРїРёСЃРѕРє
   }
   
   // РќРѕРІРѕРµ (РёСЃРїСЂР°РІР»РµРЅРЅРѕРµ) СѓСЃР»РѕРІРёРµ
   if (!validatinResult.success && skuData === null) {
       addToErrorList(qrCode, validationResult);
   }
   `

2. **РџСЂРѕРІРµСЂРёС‚СЊ РґР°РЅРЅС‹Рµ РІР°Р»РёРґР°С†РёРё:**
   `javascript
   console.log('Validation result:', validatinResult);
   console.log('SKU data:', skuData);
   `

### 3. РћС€РёР±РєРё СЃРѕС…СЂР°РЅРµРЅРёСЏ РґРѕРєСѓРјРµРЅС‚РѕРІ

#### РЎРёРјРїС‚РѕРјС‹
- Р”РѕРєСѓРјРµРЅС‚ РѕС‚РіСЂСѓР·РєРё РЅРµ СЃРѕС…СЂР°РЅСЏРµС‚СЃСЏ
- РћС€РёР±РєР° "РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РґРѕРєСѓРјРµРЅС‚Р° РѕС‚РіСЂСѓР·РєРё РїСЂРё РѕРїР»Р°С‚Рµ С‚РёРїР° coldSale"

#### Р”РёР°РіРЅРѕСЃС‚РёРєР°
`csharp
// РџСЂРѕРІРµСЂРєР° С‚РёРїР° РѕС‚РіСЂСѓР·РєРё
if (orderType == 0) // Cold Sale
{
    result.Immediate = true; // РќРµ РѕРїСЂР°С€РёРІР°С‚СЊ СЃС‚Р°С‚СѓСЃ РѕРїР»Р°С‚С‹
}
else
{
    result.Immediate = false; // РћРїСЂР°С€РёРІР°С‚СЊ СЃС‚Р°С‚СѓСЃ РѕРїР»Р°С‚С‹
}
`

#### Р РµС€РµРЅРёСЏ
1. **РСЃРїСЂР°РІРёС‚СЊ Р»РѕРіРёРєСѓ РґР»СЏ Cold Sale:**
   `csharp
   public class ShipmentService
   {
       public async Task<ShipmentResult> CreateShipmentAsync(ShipmentRequest request)
       {
           var result = new ShipmentResult();
           
           // Р”Р»СЏ Cold Sale РЅРµ РѕРїСЂР°С€РёРІР°РµРј СЃС‚Р°С‚СѓСЃ РѕРїР»Р°С‚С‹
           if (request.OrderType == 0) // Cold Sale
           {
               result.Immediate = true;
           }
           else
           {
               result.Immediate = false;
           }
           
           return result;
       }
   }
   `

2. **РџСЂРѕРІРµСЂРёС‚СЊ РєРѕРЅС„РёРіСѓСЂР°С†РёСЋ С‚РёРїРѕРІ РѕРїР»Р°С‚С‹:**
   `json
   {
     "OrderTypes": {
       "ColdSale": 0,
       "Ecomm": 1,
       "BonusSale": 2
     }
   }
   `

## Р”РёР°РіРЅРѕСЃС‚РёС‡РµСЃРєРёРµ РёРЅСЃС‚СЂСѓРјРµРЅС‚С‹

### 1. Р›РѕРіРё СЃРёСЃС‚РµРјС‹

#### РџСЂРѕСЃРјРѕС‚СЂ Р»РѕРіРѕРІ
`ash
# Р›РѕРіРё РїСЂРёР»РѕР¶РµРЅРёСЏ
tail -f /logs/mt-tnt-integration.log

# Р›РѕРіРё Р±Р°Р·С‹ РґР°РЅРЅС‹С…
tail -f /var/log/mssql/errorlog

# Р›РѕРіРё РІРµР±-СЃРµСЂРІРµСЂР°
tail -f /var/log/nginx/error.log
`

#### РЈСЂРѕРІРЅРё Р»РѕРіРёСЂРѕРІР°РЅРёСЏ
- **Debug** - РґРµС‚Р°Р»СЊРЅР°СЏ РёРЅС„РѕСЂРјР°С†РёСЏ РґР»СЏ РѕС‚Р»Р°РґРєРё
- **Information** - РѕР±С‰Р°СЏ РёРЅС„РѕСЂРјР°С†РёСЏ Рѕ СЂР°Р±РѕС‚Рµ
- **Warning** - РїСЂРµРґСѓРїСЂРµР¶РґРµРЅРёСЏ Рѕ РїРѕС‚РµРЅС†РёР°Р»СЊРЅС‹С… РїСЂРѕР±Р»РµРјР°С…
- **Error** - РѕС€РёР±РєРё, РЅРµ РѕСЃС‚Р°РЅР°РІР»РёРІР°СЋС‰РёРµ СЂР°Р±РѕС‚Сѓ
- **Critical** - РєСЂРёС‚РёС‡РµСЃРєРёРµ РѕС€РёР±РєРё

### 2. РњРѕРЅРёС‚РѕСЂРёРЅРі API

#### РџСЂРѕРІРµСЂРєР° РґРѕСЃС‚СѓРїРЅРѕСЃС‚Рё T&T API
`ash
#!/bin/bash
# health-check.sh

TNT_API_URL="https://api.trackandtrace.az"
RESPONSE=

if [  -eq 200 ]; then
    echo "T&T API is UP"
else
    echo "T&T API is DOWN (HTTP )"
fi
`

#### РџСЂРѕРІРµСЂРєР° РїСЂРѕРёР·РІРѕРґРёС‚РµР»СЊРЅРѕСЃС‚Рё
`ash
# РўРµСЃС‚ РїСЂРѕРёР·РІРѕРґРёС‚РµР»СЊРЅРѕСЃС‚Рё API
ab -n 100 -c 10 -H "Authorization: Bearer " \
   https://api.trackandtrace.az/code_info
`

### 3. Р”РёР°РіРЅРѕСЃС‚РёРєР° Р±Р°Р·С‹ РґР°РЅРЅС‹С…

#### РџСЂРѕРІРµСЂРєР° РїРѕРґРєР»СЋС‡РµРЅРёСЏ
`sql
-- РџСЂРѕРІРµСЂРєР° РїРѕРґРєР»СЋС‡РµРЅРёСЏ Рє Р±Р°Р·Рµ РґР°РЅРЅС‹С…
SELECT @@SERVERNAME, DB_NAME(), USER_NAME()

-- РџСЂРѕРІРµСЂРєР° Р°РєС‚РёРІРЅС‹С… СЃРѕРµРґРёРЅРµРЅРёР№
SELECT 
    session_id,
    login_name,
    program_name,
    status,
    cpu_time,
    memory_usage
FROM sys.dm_exec_sessions
WHERE is_user_process = 1
`

#### РџСЂРѕРІРµСЂРєР° РїСЂРѕРёР·РІРѕРґРёС‚РµР»СЊРЅРѕСЃС‚Рё
`sql
-- РўРѕРї Р·Р°РїСЂРѕСЃРѕРІ РїРѕ РІСЂРµРјРµРЅРё РІС‹РїРѕР»РЅРµРЅРёСЏ
SELECT TOP 10
    query_hash,
    total_elapsed_time,
    execution_count,
    total_elapsed_time / execution_count AS avg_elapsed_time
FROM sys.dm_exec_query_stats
ORDER BY total_elapsed_time DESC
`

## РџСЂРѕС„РёР»Р°РєС‚РёС‡РµСЃРєРёРµ РјРµСЂС‹

### 1. РњРѕРЅРёС‚РѕСЂРёРЅРі

#### РљР»СЋС‡РµРІС‹Рµ РјРµС‚СЂРёРєРё
- **Р’СЂРµРјСЏ РѕС‚РІРµС‚Р° API** < 30 СЃРµРєСѓРЅРґ
- **Р”РѕСЃС‚СѓРїРЅРѕСЃС‚СЊ СЃРµСЂРІРёСЃРѕРІ** > 99.5%
- **РљРѕР»РёС‡РµСЃС‚РІРѕ РѕС€РёР±РѕРє** < 1%
- **РСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ РїР°РјСЏС‚Рё** < 80%

#### РќР°СЃС‚СЂРѕР№РєР° Р°Р»РµСЂС‚РѕРІ
`yaml
# prometheus-alerts.yml
groups:
- name: mt-tnt-integration
  rules:
  - alert: TnTApiDown
    expr: up{job="tnt-api"} == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "T&T API is down"
      
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
`

### 2. Р РµР·РµСЂРІРЅРѕРµ РєРѕРїРёСЂРѕРІР°РЅРёРµ

#### РЎС‚СЂР°С‚РµРіРёСЏ Р±СЌРєР°РїР°
- **РџРѕР»РЅРѕРµ СЂРµР·РµСЂРІРЅРѕРµ РєРѕРїРёСЂРѕРІР°РЅРёРµ:** РµР¶РµРґРЅРµРІРЅРѕ РІ 02:00
- **РРЅРєСЂРµРјРµРЅС‚Р°Р»СЊРЅРѕРµ РєРѕРїРёСЂРѕРІР°РЅРёРµ:** РєР°Р¶РґС‹Рµ 4 С‡Р°СЃР°
- **Р›РѕРіРё С‚СЂР°РЅР·Р°РєС†РёР№:** РєР°Р¶РґС‹Рµ 15 РјРёРЅСѓС‚
- **РҐСЂР°РЅРµРЅРёРµ Р±СЌРєР°РїРѕРІ:** 30 РґРЅРµР№

#### РЎРєСЂРёРїС‚ СЂРµР·РµСЂРІРЅРѕРіРѕ РєРѕРїРёСЂРѕРІР°РЅРёСЏ
`sql
-- backup-database.sql
BACKUP DATABASE [Chicago] 
TO DISK = 'C:\Backup\Chicago_Full.bak'
WITH FORMAT, INIT, COMPRESSION;

BACKUP LOG [Chicago] 
TO DISK = 'C:\Backup\Chicago_Log.trn'
WITH FORMAT, INIT, COMPRESSION;
`

### 3. РћР±РЅРѕРІР»РµРЅРёСЏ Рё РїР°С‚С‡Рё

#### РџР»Р°РЅ РѕР±РЅРѕРІР»РµРЅРёР№
- **РљСЂРёС‚РёС‡РµСЃРєРёРµ РѕР±РЅРѕРІР»РµРЅРёСЏ:** РІ С‚РµС‡РµРЅРёРµ 24 С‡Р°СЃРѕРІ
- **РћР±РЅРѕРІР»РµРЅРёСЏ Р±РµР·РѕРїР°СЃРЅРѕСЃС‚Рё:** РІ С‚РµС‡РµРЅРёРµ 7 РґРЅРµР№
- **Р¤СѓРЅРєС†РёРѕРЅР°Р»СЊРЅС‹Рµ РѕР±РЅРѕРІР»РµРЅРёСЏ:** РїРѕ СЂР°СЃРїРёСЃР°РЅРёСЋ СЂРµР»РёР·РѕРІ

#### РџСЂРѕС†РµРґСѓСЂР° РѕР±РЅРѕРІР»РµРЅРёСЏ
1. РЎРѕР·РґР°РЅРёРµ СЂРµР·РµСЂРІРЅРѕР№ РєРѕРїРёРё
2. РўРµСЃС‚РёСЂРѕРІР°РЅРёРµ РЅР° UAT
3. РџР»Р°РЅРёСЂРѕРІР°РЅРёРµ РѕРєРЅР° РѕР±СЃР»СѓР¶РёРІР°РЅРёСЏ
4. РџСЂРёРјРµРЅРµРЅРёРµ РѕР±РЅРѕРІР»РµРЅРёСЏ
5. РџСЂРѕРІРµСЂРєР° СЂР°Р±РѕС‚РѕСЃРїРѕСЃРѕР±РЅРѕСЃС‚Рё
6. РћС‚РєР°С‚ РїСЂРё РЅРµРѕР±С…РѕРґРёРјРѕСЃС‚Рё

## РљРѕРЅС‚Р°РєС‚С‹ РїРѕРґРґРµСЂР¶РєРё

### Р’РЅСѓС‚СЂРµРЅРЅСЏСЏ РїРѕРґРґРµСЂР¶РєР°
- **РўРµС…РЅРёС‡РµСЃРєР°СЏ РїРѕРґРґРµСЂР¶РєР°:** support@company.com
- **РўРµР»РµС„РѕРЅ:** +7 (XXX) XXX-XX-XX
- **Slack:** #mt-tnt-support

### Р’РЅРµС€РЅРёРµ РїРѕСЃС‚Р°РІС‰РёРєРё
- **T&T Support:** support@trackandtrace.az
- **SAP Support:** sap-support@company.com
- **Microsoft Support:** С‡РµСЂРµР· РїРѕСЂС‚Р°Р» Azure

### Р­СЃРєР°Р»Р°С†РёСЏ РїСЂРѕР±Р»РµРј
1. **РЈСЂРѕРІРµРЅСЊ 1:** Р’РЅСѓС‚СЂРµРЅРЅСЏСЏ РїРѕРґРґРµСЂР¶РєР° (2 С‡Р°СЃР°)
2. **РЈСЂРѕРІРµРЅСЊ 2:** РђСЂС…РёС‚РµРєС‚РѕСЂС‹ (4 С‡Р°СЃР°)
3. **РЈСЂРѕРІРµРЅСЊ 3:** Р’РЅРµС€РЅРёРµ РїРѕСЃС‚Р°РІС‰РёРєРё (8 С‡Р°СЃРѕРІ)

---
*Р”РёР°РіРЅРѕСЃС‚РёРєР° РѕСЃРЅРѕРІР°РЅР° РЅР° РёСЃРїСЂР°РІР»РµРЅРЅС‹С… РѕС€РёР±РєР°С… 232817, 232620, 234424*
