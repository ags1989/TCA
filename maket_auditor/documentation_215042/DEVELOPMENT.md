# Р СѓРєРѕРІРѕРґСЃС‚РІРѕ РґР»СЏ СЂР°Р·СЂР°Р±РѕС‚С‡РёРєРѕРІ

## РћР±Р·РѕСЂ СЃРёСЃС‚РµРјС‹

РЎРёСЃС‚РµРјР° РёРЅС‚РµРіСЂР°С†РёРё РњРў СЃ Track and Trace СЃРѕСЃС‚РѕРёС‚ РёР· РЅРµСЃРєРѕР»СЊРєРёС… РєРѕРјРїРѕРЅРµРЅС‚РѕРІ, СЂР°Р±РѕС‚Р°СЋС‰РёС… РІ СЃРІСЏР·РєРµ РґР»СЏ РѕР±РµСЃРїРµС‡РµРЅРёСЏ СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ QR-РєРѕРґРѕРІ Рё РїРµСЂРµРґР°С‡Рё РґР°РЅРЅС‹С… РѕР± РѕС‚РіСЂСѓР·РєР°С….

## РљРѕРјРїРѕРЅРµРЅС‚С‹ СЃРёСЃС‚РµРјС‹

### 1. РњРѕР±РёР»СЊРЅРѕРµ РїСЂРёР»РѕР¶РµРЅРёРµ РњРў (Frontend)

**РўРµС…РЅРѕР»РѕРіРёРё:** JavaScript, HTML5, CSS3, Cordova

**РћСЃРЅРѕРІРЅС‹Рµ РјРѕРґСѓР»Рё:**
- scanner.js - РњРѕРґСѓР»СЊ СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ QR-РєРѕРґРѕРІ
- alidation.js - Р’Р°Р»РёРґР°С†РёСЏ РґР°РЅРЅС‹С…
- pi-client.js - РљР»РёРµРЅС‚ РґР»СЏ СЂР°Р±РѕС‚С‹ СЃ API
- ui-components.js - UI РєРѕРјРїРѕРЅРµРЅС‚С‹

**РљР»СЋС‡РµРІС‹Рµ С„СѓРЅРєС†РёРё:**
`javascript
// РЎРєР°РЅРёСЂРѕРІР°РЅРёРµ QR-РєРѕРґР°
function scanQRCode() {
    cordova.plugins.barcodeScanner.scan(
        function(result) {
            validateQRCode(result.text);
        },
        function(error) {
            showError('РћС€РёР±РєР° СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ: ' + error);
        }
    );
}

// Р’Р°Р»РёРґР°С†РёСЏ QR-РєРѕРґР° С‡РµСЂРµР· API
async function validateQRCode(code) {
    try {
        const response = await apiClient.post('/code_info', { code: code });
        if (response.data.status === 'success') {
            addToScanList(response.data);
        } else {
            addToErrorList(code, response.data.code);
        }
    } catch (error) {
        showError('РћС€РёР±РєР° РІР°Р»РёРґР°С†РёРё: ' + error.message);
    }
}
`

### 2. API Miami (Backend)

**РўРµС…РЅРѕР»РѕРіРёРё:** C# (.NET), ASP.NET Web API, Entity Framework

**РћСЃРЅРѕРІРЅС‹Рµ РєРѕРЅС‚СЂРѕР»Р»РµСЂС‹:**
- QRCodeController - Р’Р°Р»РёРґР°С†РёСЏ QR-РєРѕРґРѕРІ
- ShipmentController - РЎРѕР·РґР°РЅРёРµ РѕС‚РіСЂСѓР·РѕРє
- TnTController - РРЅС‚РµРіСЂР°С†РёСЏ СЃ T&T

**РџСЂРёРјРµСЂ РєРѕРЅС‚СЂРѕР»Р»РµСЂР°:**
`csharp
[ApiController]
[Route("api/[controller]")]
public class QRCodeController : ControllerBase
{
    private readonly ITnTService _tnTService;
    private readonly IQRCodeRepository _qrCodeRepository;

    [HttpPost("validate")]
    public async Task<IActionResult> ValidateQRCode([FromBody] QRCodeRequest request)
    {
        try
        {
            var validationResult = await _tnTService.ValidateCodeAsync(request.Code);
            
            if (validationResult.Success)
            {
                await _qrCodeRepository.SaveValidationResultAsync(validationResult);
                return Ok(validationResult);
            }
            else
            {
                return BadRequest(new { 
                    success = false, 
                    errorCode = validationResult.ErrorCode,
                    message = validationResult.ErrorMessage 
                });
            }
        }
        catch (Exception ex)
        {
            return StatusCode(500, new { message = ex.Message });
        }
    }
}
`

### 3. РЎРµСЂРІРёСЃ РёРЅС‚РµРіСЂР°С†РёРё СЃ T&T

**РћСЃРЅРѕРІРЅС‹Рµ РјРµС‚РѕРґС‹:**
`csharp
public class TnTService : ITnTService
{
    private readonly HttpClient _httpClient;
    private readonly IConfiguration _configuration;

    public async Task<ValidationResult> ValidateCodeAsync(string code)
    {
        var request = new
        {
            code = code
        };

        var response = await _httpClient.PostAsJsonAsync("/code_info", request);
        var content = await response.Content.ReadAsStringAsync();
        
        return JsonSerializer.Deserialize<ValidationResult>(content);
    }

    public async Task<ShipmentResult> CreateShipmentAsync(ShipmentRequest request)
    {
        var response = await _httpClient.PostAsJsonAsync("/make_shipping", request);
        var content = await response.Content.ReadAsStringAsync();
        
        return JsonSerializer.Deserialize<ShipmentResult>(content);
    }
}
`

## РўРµС…РЅРёС‡РµСЃРєРёРµ С‚СЂРµР±РѕРІР°РЅРёСЏ

### РР· User Story 225877 - РџРѕРґРєР»СЋС‡РµРЅРёРµ РґСЂ. С‚РёРїРѕРІ РѕРїР»Р°С‚С‹:

**РўСЂРµР±РѕРІР°РЅРёСЏ Рє РёРЅС‚РµСЂС„РµР№СЃСѓ:**
- Р’РѕР·РјРѕР¶РЅРѕСЃС‚СЊ РІС‹Р±РѕСЂР° С‚РёРїР° РѕРїР»Р°С‚С‹ РїСЂРё СЃРѕР·РґР°РЅРёРё РѕС‚РіСЂСѓР·РєРё
- РџРѕРґРґРµСЂР¶РєР° С‚РёРїРѕРІ: Cold Sale, Ecomm, Bonus Sale
- Р’Р°Р»РёРґР°С†РёСЏ РІС‹Р±СЂР°РЅРЅРѕРіРѕ С‚РёРїР° РѕРїР»Р°С‚С‹

**Р РµР°Р»РёР·Р°С†РёСЏ:**
`javascript
// РўРёРїС‹ РѕРїР»Р°С‚С‹
const PAYMENT_TYPES = {
    COLD_SALE: 0,
    ECOMM: 1,
    BONUS_SALE: 2
};

// РЎРѕР·РґР°РЅРёРµ РѕС‚РіСЂСѓР·РєРё СЃ С‚РёРїРѕРј РѕРїР»Р°С‚С‹
function createShipment(paymentType) {
    const shipmentData = {
        orderType: paymentType,
        items: getScannedItems(),
        // ... РґСЂСѓРіРёРµ РґР°РЅРЅС‹Рµ
    };
    
    return apiClient.post('/shipment/create', shipmentData);
}
`

### РР· RnD Backlog Item 224168 - РСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ API T&T:

**РСЃРїРѕР»СЊР·СѓРµРјС‹Рµ API РјРµС‚РѕРґС‹:**
1. POST /login_api - РђРІС‚РѕСЂРёР·Р°С†РёСЏ
2. POST /code_info - Р’Р°Р»РёРґР°С†РёСЏ QR-РєРѕРґРѕРІ
3. POST /make_shipping - РЎРѕР·РґР°РЅРёРµ РѕС‚РіСЂСѓР·РєРё
4. POST /departments/ - РџРѕР»СѓС‡РµРЅРёРµ РґРµРїР°СЂС‚Р°РјРµРЅС‚РѕРІ
5. POST /products/ - РџРѕР»СѓС‡РµРЅРёРµ С‚РѕРІР°СЂРѕРІ

**РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ API:**
`csharp
public class TnTApiConfig
{
    public string BaseUrl { get; set; }
    public string Username { get; set; }
    public string Password { get; set; }
    public int TimeoutSeconds { get; set; } = 30;
    public int RetryCount { get; set; } = 3;
}
`

## РСЃРїСЂР°РІР»РµРЅРЅС‹Рµ РѕС€РёР±РєРё

### РР· РѕС€РёР±РєРё 232620 - Р­Р»РµРјРµРЅС‚С‹ РЅРµ РїСЂРѕС€РµРґС€РёРµ РІР°Р»РёРґР°С†РёСЋ:

**РџСЂРѕР±Р»РµРјР°:** РўРѕРІР°СЂС‹ СЃ РѕС€РёР±РѕС‡РЅС‹Рј СЃС‚Р°С‚СѓСЃРѕРј РЅРµ РґРѕР±Р°РІР»СЏР»РёСЃСЊ РІ СЃРїРёСЃРѕРє РѕС‚СЃРєР°РЅРёСЂРѕРІР°РЅРЅС‹С… С‚РѕРІР°СЂРѕРІ.

**РСЃРїСЂР°РІР»РµРЅРёРµ:**
`javascript
// РЎС‚Р°СЂРѕРµ СѓСЃР»РѕРІРёРµ (РЅРµРїСЂР°РІРёР»СЊРЅРѕРµ)
if (!validatinResult.success && 'errorCode' in validatinResult) {
    // РЅРµ РґРѕР±Р°РІР»СЏС‚СЊ РІ СЃРїРёСЃРѕРє
}

// РќРѕРІРѕРµ СѓСЃР»РѕРІРёРµ (РёСЃРїСЂР°РІР»РµРЅРЅРѕРµ)
if (!validatinResult.success && skuData === null) {
    // РґРѕР±Р°РІРёС‚СЊ РІ СЃРїРёСЃРѕРє СЃ РѕС€РёР±РѕС‡РЅС‹Рј СЃС‚Р°С‚СѓСЃРѕРј
    addToErrorList(qrCode, validationResult);
}
`

### РР· РѕС€РёР±РєРё 234424 - РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РїСЂРё coldSale:

**РџСЂРѕР±Р»РµРјР°:** РњРў РѕС‚РїСЂР°РІР»СЏР»Р° Р·Р°РїСЂРѕСЃС‹ РЅР° СЃС‚Р°С‚СѓСЃ РѕРїР»Р°С‚С‹ РґР»СЏ С‚РёРїР° coldSale, РіРґРµ СЌС‚Рѕ РЅРµ С‚СЂРµР±СѓРµС‚СЃСЏ.

**РСЃРїСЂР°РІР»РµРЅРёРµ:**
`csharp
// Р”РѕР±Р°РІР»РµРЅРѕ СѓСЃР»РѕРІРёРµ РґР»СЏ cold sale
if (orderType == 0) // Cold Sale
{
    result.Immediate = true; // РќРµ РѕРїСЂР°С€РёРІР°С‚СЊ СЃС‚Р°С‚СѓСЃ РѕРїР»Р°С‚С‹
}
else
{
    result.Immediate = false; // РћРїСЂР°С€РёРІР°С‚СЊ СЃС‚Р°С‚СѓСЃ РѕРїР»Р°С‚С‹
}
`

## РЎРІСЏР·Р°РЅРЅС‹Рµ С‚РёРєРµС‚С‹

### User Stories:
- **225877** - РљСЂРѕРєСѓСЃ. РџРѕРґРєР»СЋС‡РµРЅРёРµ РґСЂ. С‚РёРїРѕРІ РѕРїР»Р°С‚С‹
- **224168** - RnD: РљСЂРѕРєСѓСЃ. РСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ API T&T
- **218645** - РљСЂРѕРєСѓСЃ. РЎРєР°РЅРёСЂРѕРІР°РЅРёРµ QR-РєРѕРґРѕРІ Рё TnT - РѕС†РµРЅРєР°

### Backlog Items:
- **215405** - РЎРІСЏР·Р°РЅРЅС‹Р№ backlog item (РєРѕРїРёСЏ 218645)

### Bug tickets:
- **232817** - РљСЂРѕРєСѓСЃ. MT. РќРµ РїСЂРѕС…РѕРґРёС‚ Р°РІС‚РѕСЂРёР·Р°С†РёСЏ РІ T&T
- **232620** - РљСЂРѕРєСѓСЃ. РџСЂРё СЃРєР°РЅРёСЂРѕРІР°РЅРёРµ РЅРµ РґРѕР±Р°РІР»СЏРµС‚СЃСЏ РІ СЃРїРёСЃРѕРє СЌР»РµРјРµРЅС‚С‹ РЅРµ РїСЂРѕС€РµРґС€РёРµ РІР°Р»РёРґР°С†РёСЋ
- **234424** - РћС€РёР±РєР°. РљСЂРѕРєСѓСЃ. РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РґРѕРєСѓРјРµРЅС‚Р° РѕС‚РіСЂСѓР·РєРё РїСЂРё РѕРїР»Р°С‚Рµ С‚РёРїР° coldSale

## РќР°СЃС‚СЂРѕР№РєР° РѕРєСЂСѓР¶РµРЅРёСЏ

### РџРµСЂРµРјРµРЅРЅС‹Рµ РѕРєСЂСѓР¶РµРЅРёСЏ:
`ash
# T&T API
TNT_API_BASE_URL=https://api.trackandtrace.az
TNT_API_USERNAME=your_username
TNT_API_PASSWORD=your_password

# Р‘Р°Р·Р° РґР°РЅРЅС‹С…
CONNECTION_STRING=Server=localhost;Database=Chicago;Trusted_Connection=true;

# РњРў API
MT_API_BASE_URL=https://api.miami.local
MT_API_KEY=your_api_key
`

### РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ РїСЂРёР»РѕР¶РµРЅРёСЏ:
`json
{
  "TnTApi": {
    "BaseUrl": "https://api.trackandtrace.az",
    "TimeoutSeconds": 30,
    "RetryCount": 3
  },
  "Database": {
    "ConnectionString": "Server=localhost;Database=Chicago;Trusted_Connection=true;"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft": "Warning"
    }
  }
}
`

## РўРµСЃС‚РёСЂРѕРІР°РЅРёРµ

### Unit С‚РµСЃС‚С‹:
`csharp
[Test]
public async Task ValidateQRCode_ValidCode_ReturnsSuccess()
{
    // Arrange
    var code = "10000001";
    var expectedResult = new ValidationResult { Success = true };
    
    // Act
    var result = await _qrCodeService.ValidateCodeAsync(code);
    
    // Assert
    Assert.IsTrue(result.Success);
}
`

### Integration С‚РµСЃС‚С‹:
`csharp
[Test]
public async Task CreateShipment_ColdSale_DoesNotPollPaymentStatus()
{
    // Arrange
    var shipment = new ShipmentRequest 
    { 
        OrderType = 0, // Cold Sale
        Items = new List<ShipmentItem>()
    };
    
    // Act
    var result = await _shipmentService.CreateShipmentAsync(shipment);
    
    // Assert
    Assert.IsTrue(result.Immediate);
}
`

---
*Р”Р°РЅРЅС‹Рµ РІР·СЏС‚С‹ РёР· Р·Р°РїСЂРѕСЃР° 215042, User Stories 225877, 224168, 218645 Рё РѕС€РёР±РѕРє 232817, 232620, 234424*
