# Р СѓРєРѕРІРѕРґСЃС‚РІРѕ РґР»СЏ СЂР°Р·СЂР°Р±РѕС‚С‡РёРєРѕРІ

## РћР±Р·РѕСЂ СЂР°Р·СЂР°Р±РѕС‚РєРё

Р”Р°РЅРЅС‹Р№ СЂР°Р·РґРµР» СЃРѕРґРµСЂР¶РёС‚ РёРЅС„РѕСЂРјР°С†РёСЋ РґР»СЏ СЂР°Р·СЂР°Р±РѕС‚С‡РёРєРѕРІ, СЂР°Р±РѕС‚Р°СЋС‰РёС… СЃ СЃРёСЃС‚РµРјРѕР№ РёРЅС‚РµРіСЂР°С†РёРё РњРў СЃ Track and Trace.

## РљРѕРјРїРѕРЅРµРЅС‚С‹ СЃРёСЃС‚РµРјС‹

### 1. РњРѕР±РёР»СЊРЅРѕРµ РїСЂРёР»РѕР¶РµРЅРёРµ РњРў (Frontend)

#### РўРµС…РЅРѕР»РѕРіРёРё
- **Framework:** Xamarin.Forms 5.0
- **Platform:** iOS 12+, Android 8.0+
- **Language:** C# 9.0
- **UI:** XAML + Code-behind

#### РЎС‚СЂСѓРєС‚СѓСЂР° РїСЂРѕРµРєС‚Р°
`
MT.Mobile/
в”њв”Ђв”Ђ Views/
в”‚   в”њв”Ђв”Ђ ShipmentPage.xaml
в”‚   в”њв”Ђв”Ђ QRScannerPage.xaml
в”‚   в””в”Ђв”Ђ OrderListPage.xaml
в”њв”Ђв”Ђ ViewModels/
в”‚   в”њв”Ђв”Ђ ShipmentViewModel.cs
в”‚   в”њв”Ђв”Ђ QRScannerViewModel.cs
в”‚   в””в”Ђв”Ђ OrderListViewModel.cs
в”њв”Ђв”Ђ Services/
в”‚   в”њв”Ђв”Ђ ApiService.cs
в”‚   в”њв”Ђв”Ђ QRScannerService.cs
в”‚   в””в”Ђв”Ђ NavigationService.cs
в”њв”Ђв”Ђ Models/
в”‚   в”њв”Ђв”Ђ Shipment.cs
в”‚   в”њв”Ђв”Ђ QRCode.cs
в”‚   в””в”Ђв”Ђ Order.cs
в””в”Ђв”Ђ Utils/
    в”њв”Ђв”Ђ Constants.cs
    в””в”Ђв”Ђ Extensions.cs
`

#### РљР»СЋС‡РµРІС‹Рµ РєР»Р°СЃСЃС‹

##### ShipmentViewModel
`csharp
public class ShipmentViewModel : BaseViewModel
{
    private readonly IApiService _apiService;
    private readonly IQRScannerService _qrScannerService;
    
    public ObservableCollection<QRCodeItem> ScannedItems { get; set; }
    public ObservableCollection<QRCodeItem> ErrorItems { get; set; }
    
    public ICommand ScanQRCommand { get; set; }
    public ICommand SaveShipmentCommand { get; set; }
    public ICommand RemoveItemCommand { get; set; }
    
    public async Task ScanQRCode()
    {
        try
        {
            var result = await _qrScannerService.ScanAsync();
            if (result.Success)
            {
                await ValidateQRCode(result.QRCode);
            }
        }
        catch (Exception ex)
        {
            await ShowErrorAsync($"РћС€РёР±РєР° СЃРєР°РЅРёСЂРѕРІР°РЅРёСЏ: {ex.Message}");
        }
    }
    
    private async Task ValidateQRCode(string qrCode)
    {
        var request = new QRValidationRequest { QRCode = qrCode };
        var response = await _apiService.ValidateQRAsync(request);
        
        if (response.Success)
        {
            ScannedItems.Add(new QRCodeItem
            {
                QRCode = qrCode,
                ProductName = response.Data.ProductName,
                UnitPrice = response.Data.UnitPrice
            });
        }
        else
        {
            ErrorItems.Add(new QRCodeItem
            {
                QRCode = qrCode,
                ErrorMessage = response.Error.Message
            });
        }
    }
}
`

##### ApiService
`csharp
public class ApiService : IApiService
{
    private readonly HttpClient _httpClient;
    private readonly string _baseUrl = "https://api-miami.company.com/v2";
    
    public async Task<QRValidationResponse> ValidateQRAsync(QRValidationRequest request)
    {
        var response = await _httpClient.PostAsJsonAsync($"{_baseUrl}/qr/validate", request);
        return await response.Content.ReadFromJsonAsync<QRValidationResponse>();
    }
    
    public async Task<ShipmentResponse> CreateShipmentAsync(ShipmentRequest request)
    {
        var response = await _httpClient.PostAsJsonAsync($"{_baseUrl}/shipments", request);
        return await response.Content.ReadFromJsonAsync<ShipmentResponse>();
    }
}
`

### 2. API Miami (Backend)

#### РўРµС…РЅРѕР»РѕРіРёРё
- **Framework:** ASP.NET Core 6.0
- **Language:** C# 10.0
- **ORM:** Entity Framework Core 6.0
- **Database:** SQL Server 2019
- **Authentication:** JWT Bearer

#### РЎС‚СЂСѓРєС‚СѓСЂР° РїСЂРѕРµРєС‚Р°
`
Miami.API/
в”њв”Ђв”Ђ Controllers/
в”‚   в”њв”Ђв”Ђ AuthController.cs
в”‚   в”њв”Ђв”Ђ QRController.cs
в”‚   в”њв”Ђв”Ђ ShipmentController.cs
в”‚   в””в”Ђв”Ђ ProductController.cs
в”њв”Ђв”Ђ Services/
в”‚   в”њв”Ђв”Ђ TnTApiService.cs
в”‚   в”њв”Ђв”Ђ ShipmentService.cs
в”‚   в”њв”Ђв”Ђ QRValidationService.cs
в”‚   в””в”Ђв”Ђ UserService.cs
в”њв”Ђв”Ђ Models/
в”‚   в”њв”Ђв”Ђ Requests/
в”‚   в”‚   в”њв”Ђв”Ђ QRValidationRequest.cs
в”‚   в”‚   в””в”Ђв”Ђ ShipmentRequest.cs
в”‚   в”њв”Ђв”Ђ Responses/
в”‚   в”‚   в”њв”Ђв”Ђ QRValidationResponse.cs
в”‚   в”‚   в””в”Ђв”Ђ ShipmentResponse.cs
в”‚   в””в”Ђв”Ђ Entities/
в”‚       в”њв”Ђв”Ђ User.cs
в”‚       в”њв”Ђв”Ђ Shipment.cs
в”‚       в””в”Ђв”Ђ QRCode.cs
в”њв”Ђв”Ђ Data/
в”‚   в”њв”Ђв”Ђ ApplicationDbContext.cs
в”‚   в””в”Ђв”Ђ Repositories/
в”‚       в”њв”Ђв”Ђ UserRepository.cs
в”‚       в””в”Ђв”Ђ ShipmentRepository.cs
в””в”Ђв”Ђ Middleware/
    в”њв”Ђв”Ђ ErrorHandlingMiddleware.cs
    в””в”Ђв”Ђ LoggingMiddleware.cs
`

#### РљР»СЋС‡РµРІС‹Рµ СЃРµСЂРІРёСЃС‹

##### TnTApiService
`csharp
public class TnTApiService : ITnTApiService
{
    private readonly HttpClient _httpClient;
    private readonly IConfiguration _configuration;
    private readonly ILogger<TnTApiService> _logger;
    
    private string _token;
    private DateTime _tokenExpiry;
    
    public async Task<TnTValidationResult> ValidateQRCodeAsync(string qrCode)
    {
        await EnsureValidTokenAsync();
        
        var request = new TnTValidationRequest
        {
            Code = qrCode
        };
        
        var response = await _httpClient.PostAsJsonAsync("/code_info", request);
        
        if (response.IsSuccessStatusCode)
        {
            var result = await response.Content.ReadFromJsonAsync<TnTValidationResponse>();
            return new TnTValidationResult
            {
                Success = true,
                Data = result
            };
        }
        else
        {
            var error = await response.Content.ReadFromJsonAsync<TnTErrorResponse>();
            return new TnTValidationResult
            {
                Success = false,
                Error = error
            };
        }
    }
    
    private async Task EnsureValidTokenAsync()
    {
        if (string.IsNullOrEmpty(_token) || DateTime.UtcNow >= _tokenExpiry)
        {
            await RefreshTokenAsync();
        }
    }
    
    private async Task RefreshTokenAsync()
    {
        var authRequest = new TnTAuthRequest
        {
            Username = _configuration["TnTAuth:Username"],
            Password = _configuration["TnTAuth:Password"]
        };
        
        var response = await _httpClient.PostAsJsonAsync("/login_api", authRequest);
        var result = await response.Content.ReadFromJsonAsync<TnTAuthResponse>();
        
        _token = result.Token;
        _tokenExpiry = DateTime.UtcNow.AddSeconds(result.ExpiresIn - 60);
        
        _httpClient.DefaultRequestHeaders.Authorization = 
            new AuthenticationHeaderValue("Bearer", _token);
    }
}
`

##### ShipmentService
`csharp
public class ShipmentService : IShipmentService
{
    private readonly ApplicationDbContext _context;
    private readonly ITnTApiService _tnTApiService;
    private readonly ILogger<ShipmentService> _logger;
    
    public async Task<ShipmentResult> CreateShipmentAsync(ShipmentRequest request)
    {
        using var transaction = await _context.Database.BeginTransactionAsync();
        
        try
        {
            // РЎРѕР·РґР°РЅРёРµ РѕС‚РіСЂСѓР·РєРё
            var shipment = new Shipment
            {
                Id = GenerateShipmentId(),
                OrderId = request.OrderId,
                LocationId = request.LocationId,
                Status = "created",
                TotalAmount = request.Items.Sum(i => i.TotalPrice),
                CreatedAt = DateTime.UtcNow
            };
            
            _context.Shipments.Add(shipment);
            
            // Р”РѕР±Р°РІР»РµРЅРёРµ РїРѕР·РёС†РёР№ РѕС‚РіСЂСѓР·РєРё
            foreach (var item in request.Items)
            {
                var shipmentItem = new ShipmentItem
                {
                    ShipmentId = shipment.Id,
                    QRCode = item.QRCode,
                    ProductId = item.ProductId,
                    Quantity = item.Quantity,
                    UnitPrice = item.UnitPrice,
                    TotalPrice = item.TotalPrice
                };
                
                _context.ShipmentItems.Add(shipmentItem);
            }
            
            await _context.SaveChangesAsync();
            
            // РћС‚РїСЂР°РІРєР° РІ T&T РґР»СЏ Cold Sale Рё Ecomm
            if (request.OrderType == 0 || request.OrderType == 1) // Cold Sale РёР»Рё Ecomm
            {
                var tntResult = await SendToTnTAsync(shipment, request.Items);
                if (tntResult.Success)
                {
                    shipment.TnTStatus = "sent";
                    shipment.TnTDocumentId = tntResult.DocumentId;
                }
                else
                {
                    shipment.TnTStatus = "error";
                    _logger.LogError("Failed to send shipment to T&T: {Error}", tntResult.Error);
                }
            }
            
            shipment.Status = "completed";
            await _context.SaveChangesAsync();
            
            await transaction.CommitAsync();
            
            return new ShipmentResult
            {
                Success = true,
                ShipmentId = shipment.Id,
                TnTStatus = shipment.TnTStatus
            };
        }
        catch (Exception ex)
        {
            await transaction.RollbackAsync();
            _logger.LogError(ex, "Error creating shipment");
            throw;
        }
    }
    
    private async Task<TnTShipmentResult> SendToTnTAsync(Shipment shipment, List<ShipmentItemRequest> items)
    {
        var tntRequest = new TnTShipmentRequest
        {
            DocExtId = shipment.Id,
            Dat = shipment.CreatedAt.ToString("yyyy-MM-dd"),
            Num = shipment.Id,
            DepartFromExtId = shipment.LocationId,
            DepartToExtId = "1000002", // РљРѕРЅСЃС‚Р°РЅС‚Р° РґР»СЏ РєР»РёРµРЅС‚Р°
            PartnerFiscalId = "9871000002", // РљРѕРЅСЃС‚Р°РЅС‚Р° РґР»СЏ РєР»РёРµРЅС‚Р°
            Items = items.Select(i => new TnTShipmentItem
            {
                Code = i.QRCode,
                Quantity = i.Quantity,
                Price = i.UnitPrice
            }).ToList()
        };
        
        return await _tnTApiService.CreateShipmentAsync(tntRequest);
    }
}
`

### 3. Р‘Р°Р·Р° РґР°РЅРЅС‹С… (Entity Framework)

#### ApplicationDbContext
`csharp
public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options) : base(options)
    {
    }
    
    public DbSet<User> Users { get; set; }
    public DbSet<UserSession> UserSessions { get; set; }
    public DbSet<Product> Products { get; set; }
    public DbSet<QRCode> QRCodes { get; set; }
    public DbSet<Location> Locations { get; set; }
    public DbSet<Order> Orders { get; set; }
    public DbSet<Shipment> Shipments { get; set; }
    public DbSet<ShipmentItem> ShipmentItems { get; set; }
    public DbSet<TnTApiLog> TnTApiLogs { get; set; }
    public DbSet<TnTSession> TnTSessions { get; set; }
    
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ User
        modelBuilder.Entity<User>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Username).HasMaxLength(50).IsRequired();
            entity.Property(e => e.PasswordHash).HasMaxLength(255).IsRequired();
            entity.Property(e => e.Role).HasMaxLength(20).IsRequired();
            entity.HasIndex(e => e.Username).IsUnique();
        });
        
        // РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ QRCode
        modelBuilder.Entity<QRCode>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.QRCode).HasMaxLength(50).IsRequired();
            entity.Property(e => e.ProductId).HasMaxLength(50).IsRequired();
            entity.HasIndex(e => e.QRCode).IsUnique();
            entity.HasOne(e => e.Product)
                  .WithMany(p => p.QRCodes)
                  .HasForeignKey(e => e.ProductId);
        });
        
        // РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ Shipment
        modelBuilder.Entity<Shipment>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasMaxLength(50).IsRequired();
            entity.Property(e => e.OrderId).HasMaxLength(50).IsRequired();
            entity.Property(e => e.LocationId).HasMaxLength(20).IsRequired();
            entity.Property(e => e.Status).HasMaxLength(20).IsRequired();
            entity.Property(e => e.TotalAmount).HasColumnType("decimal(10,2)");
            
            entity.HasOne(e => e.Order)
                  .WithMany(o => o.Shipments)
                  .HasForeignKey(e => e.OrderId);
                  
            entity.HasOne(e => e.Location)
                  .WithMany(l => l.Shipments)
                  .HasForeignKey(e => e.LocationId);
        });
        
        // РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ ShipmentItem
        modelBuilder.Entity<ShipmentItem>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.ShipmentId).HasMaxLength(50).IsRequired();
            entity.Property(e => e.QRCode).HasMaxLength(50).IsRequired();
            entity.Property(e => e.ProductId).HasMaxLength(50).IsRequired();
            entity.Property(e => e.UnitPrice).HasColumnType("decimal(10,2)");
            entity.Property(e => e.TotalPrice).HasColumnType("decimal(10,2)");
            
            entity.HasOne(e => e.Shipment)
                  .WithMany(s => s.Items)
                  .HasForeignKey(e => e.ShipmentId);
                  
            entity.HasOne(e => e.QRCodeEntity)
                  .WithMany()
                  .HasForeignKey(e => e.QRCode);
                  
            entity.HasOne(e => e.Product)
                  .WithMany()
                  .HasForeignKey(e => e.ProductId);
        });
    }
}
`

## РўРµС…РЅРёС‡РµСЃРєРёРµ С‚СЂРµР±РѕРІР°РЅРёСЏ

### РЎРёСЃС‚РµРјРЅС‹Рµ С‚СЂРµР±РѕРІР°РЅРёСЏ

#### Р Р°Р·СЂР°Р±РѕС‚РєР°
- **OS:** Windows 10/11, macOS 10.15+, Ubuntu 20.04+
- **IDE:** Visual Studio 2022, Visual Studio for Mac, VS Code
- **SDK:** .NET 6.0 SDK
- **Database:** SQL Server 2019 Developer Edition
- **Mobile:** Xamarin Workload РґР»СЏ Visual Studio

#### РџСЂРѕРґСѓРєС‚РёРІРЅР°СЏ СЃСЂРµРґР°
- **OS:** Windows Server 2019/2022, Ubuntu 20.04 LTS
- **Runtime:** .NET 6.0 Runtime
- **Database:** SQL Server 2019 Standard/Enterprise
- **Memory:** 8+ GB RAM
- **Storage:** 100+ GB SSD

### Р—Р°РІРёСЃРёРјРѕСЃС‚Рё

#### NuGet РїР°РєРµС‚С‹ (Backend)
`xml
<PackageReference Include="Microsoft.AspNetCore.Authentication.JwtBearer" Version="6.0.0" />
<PackageReference Include="Microsoft.EntityFrameworkCore.SqlServer" Version="6.0.0" />
<PackageReference Include="Microsoft.EntityFrameworkCore.Tools" Version="6.0.0" />
<PackageReference Include="Serilog.AspNetCore" Version="6.0.0" />
<PackageReference Include="Serilog.Sinks.File" Version="5.0.0" />
<PackageReference Include="Swashbuckle.AspNetCore" Version="6.0.0" />
<PackageReference Include="AutoMapper" Version="12.0.0" />
<PackageReference Include="FluentValidation.AspNetCore" Version="11.0.0" />
`

#### NuGet РїР°РєРµС‚С‹ (Mobile)
`xml
<PackageReference Include="Xamarin.Forms" Version="5.0.0.2012" />
<PackageReference Include="Xamarin.Essentials" Version="1.7.0" />
<PackageReference Include="ZXing.Net.Mobile" Version="3.1.0-beta2" />
<PackageReference Include="ZXing.Net.Mobile.Forms" Version="3.1.0-beta2" />
<PackageReference Include="Newtonsoft.Json" Version="13.0.1" />
<PackageReference Include="Refit" Version="6.3.0" />
<PackageReference Include="Prism.Unity.Forms" Version="8.1.97" />
`

## Р РµР°Р»РёР·РѕРІР°РЅРЅС‹Рµ РґРѕСЂР°Р±РѕС‚РєРё

### 1. РСЃРїСЂР°РІР»РµРЅРёРµ РѕС€РёР±РєРё 232817
**РџСЂРѕР±Р»РµРјР°:** QR-РєРѕРґС‹ СЃ РѕС€РёР±РєР°РјРё РЅРµ РґРѕР±Р°РІР»СЏР»РёСЃСЊ РІ СЃРїРёСЃРѕРє РѕС€РёР±РѕРє.

**Р РµС€РµРЅРёРµ:**
`javascript
// РЎС‚Р°СЂРѕРµ СѓСЃР»РѕРІРёРµ (РЅРµРїСЂР°РІРёР»СЊРЅРѕРµ)
if (!validatinResult.success && 'errorCode' in validatinResult) {
    // РЅРµ РґРѕР±Р°РІР»СЏС‚СЊ РІ СЃРїРёСЃРѕРє
}

// РќРѕРІРѕРµ СѓСЃР»РѕРІРёРµ (РёСЃРїСЂР°РІР»РµРЅРЅРѕРµ)
if (!validatinResult.success && skuData === null) {
    addToErrorList(qrCode, validationResult);
}
`

### 2. РСЃРїСЂР°РІР»РµРЅРёРµ РѕС€РёР±РєРё 232620
**РџСЂРѕР±Р»РµРјР°:** РќРµРїСЂР°РІРёР»СЊРЅР°СЏ РѕР±СЂР°Р±РѕС‚РєР° С‚РёРїРѕРІ РѕРїР»Р°С‚С‹ Cold Sale Рё Ecomm.

**Р РµС€РµРЅРёРµ:**
`csharp
// Р”Р»СЏ Cold Sale Рё Ecomm РЅРµ РѕРїСЂР°С€РёРІР°РµРј СЃС‚Р°С‚СѓСЃ РѕРїР»Р°С‚С‹
if (orderType == 0 || orderType == 1) // Cold Sale РёР»Рё Ecomm
{
    result.Immediate = true; // РќРµ РѕРїСЂР°С€РёРІР°С‚СЊ СЃС‚Р°С‚СѓСЃ РѕРїР»Р°С‚С‹
}
else
{
    result.Immediate = false; // РћРїСЂР°С€РёРІР°С‚СЊ СЃС‚Р°С‚СѓСЃ РѕРїР»Р°С‚С‹
}
`

### 3. РСЃРїСЂР°РІР»РµРЅРёРµ РѕС€РёР±РєРё 234424
**РџСЂРѕР±Р»РµРјР°:** РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РґРѕРєСѓРјРµРЅС‚Р° РѕС‚РіСЂСѓР·РєРё РїСЂРё РѕРїР»Р°С‚Рµ С‚РёРїР° coldSale.

**Р РµС€РµРЅРёРµ:**
`csharp
// Р”РѕР±Р°РІР»РµРЅР° РїСЂРѕРІРµСЂРєР° С‚РёРїР° РѕС‚РіСЂСѓР·РєРё РїРµСЂРµРґ СЃРѕС…СЂР°РЅРµРЅРёРµРј
if (request.OrderType == 0) // Cold Sale
{
    // РЎРїРµС†РёР°Р»СЊРЅР°СЏ Р»РѕРіРёРєР° РґР»СЏ Cold Sale
    await ProcessColdSaleShipmentAsync(request);
}
else
{
    // РЎС‚Р°РЅРґР°СЂС‚РЅР°СЏ Р»РѕРіРёРєР° РґР»СЏ РґСЂСѓРіРёС… С‚РёРїРѕРІ
    await ProcessStandardShipmentAsync(request);
}
`

## РСЃРїСЂР°РІР»РµРЅРЅС‹Рµ РѕС€РёР±РєРё

### Backlog Items
- **224168:** RnD: РљСЂРѕРєСѓСЃ. РСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ API T&T
- **218645:** РљСЂРѕРєСѓСЃ. РЎРєР°РЅРёСЂРѕРІР°РЅРёРµ QR-РєРѕРґРѕРІ Рё TnT (РЅРѕРІР°СЏ СЃС…РµРјР° РІР·Р°РёРјРѕРґРµР№СЃС‚РІРёСЏ) - РѕС†РµРЅРєР°

### Bug Tickets
- **232817:** QR-РєРѕРґС‹ СЃ РѕС€РёР±РєР°РјРё РЅРµ РґРѕР±Р°РІР»СЏСЋС‚СЃСЏ РІ СЃРїРёСЃРѕРє РѕС€РёР±РѕРє
- **232620:** РќРµРїСЂР°РІРёР»СЊРЅР°СЏ РѕР±СЂР°Р±РѕС‚РєР° С‚РёРїРѕРІ РѕРїР»Р°С‚С‹ Cold Sale Рё Ecomm
- **234424:** РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РґРѕРєСѓРјРµРЅС‚Р° РѕС‚РіСЂСѓР·РєРё РїСЂРё РѕРїР»Р°С‚Рµ С‚РёРїР° coldSale

## РЎРІСЏР·Р°РЅРЅС‹Рµ С‚РёРєРµС‚С‹

### User Stories
- **225877:** РљСЂРѕРєСѓСЃ. РџРѕРґРєР»СЋС‡РµРЅРёРµ РґСЂ. С‚РёРїРѕРІ РѕРїР»Р°С‚С‹

### Backlog Items
- **224168:** RnD: РљСЂРѕРєСѓСЃ. РСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ API T&T
- **218645:** РљСЂРѕРєСѓСЃ. РЎРєР°РЅРёСЂРѕРІР°РЅРёРµ QR-РєРѕРґРѕРІ Рё TnT (РЅРѕРІР°СЏ СЃС…РµРјР° РІР·Р°РёРјРѕРґРµР№СЃС‚РІРёСЏ) - РѕС†РµРЅРєР°

### Bug Tickets
- **232817:** QR-РєРѕРґС‹ СЃ РѕС€РёР±РєР°РјРё РЅРµ РґРѕР±Р°РІР»СЏСЋС‚СЃСЏ РІ СЃРїРёСЃРѕРє РѕС€РёР±РѕРє
- **232620:** РќРµРїСЂР°РІРёР»СЊРЅР°СЏ РѕР±СЂР°Р±РѕС‚РєР° С‚РёРїРѕРІ РѕРїР»Р°С‚С‹ Cold Sale Рё Ecomm
- **234424:** РћС€РёР±РєР° СЃРѕС…СЂР°РЅРµРЅРёСЏ РґРѕРєСѓРјРµРЅС‚Р° РѕС‚РіСЂСѓР·РєРё РїСЂРё РѕРїР»Р°С‚Рµ С‚РёРїР° coldSale

## РЎС‚Р°РЅРґР°СЂС‚С‹ РєРѕРґРёСЂРѕРІР°РЅРёСЏ

### C# Style Guide
`csharp
// РРјРµРЅРѕРІР°РЅРёРµ РєР»Р°СЃСЃРѕРІ - PascalCase
public class ShipmentService : IShipmentService
{
    // РџСЂРёРІР°С‚РЅС‹Рµ РїРѕР»СЏ - _camelCase
    private readonly ILogger<ShipmentService> _logger;
    
    // РџСѓР±Р»РёС‡РЅС‹Рµ СЃРІРѕР№СЃС‚РІР° - PascalCase
    public string ShipmentId { get; set; }
    
    // РњРµС‚РѕРґС‹ - PascalCase
    public async Task<ShipmentResult> CreateShipmentAsync(ShipmentRequest request)
    {
        // Р›РѕРєР°Р»СЊРЅС‹Рµ РїРµСЂРµРјРµРЅРЅС‹Рµ - camelCase
        var shipment = new Shipment();
        
        // РљРѕРЅСЃС‚Р°РЅС‚С‹ - UPPER_CASE
        const int MAX_RETRY_ATTEMPTS = 3;
    }
}
`

### JavaScript Style Guide
`javascript
// РџРµСЂРµРјРµРЅРЅС‹Рµ - camelCase
const qrCode = '10000001';
const validationResult = await validateQR(qrCode);

// Р¤СѓРЅРєС†РёРё - camelCase
function addToErrorList(qrCode, error) {
    // Р›РѕРіРёРєР° РґРѕР±Р°РІР»РµРЅРёСЏ РІ СЃРїРёСЃРѕРє РѕС€РёР±РѕРє
}

// РљРѕРЅСЃС‚Р°РЅС‚С‹ - UPPER_CASE
const MAX_QR_CODES = 100;
`

## РўРµСЃС‚РёСЂРѕРІР°РЅРёРµ

### Unit Tests
`csharp
[Test]
public async Task ValidateQRCode_ValidCode_ReturnsSuccess()
{
    // Arrange
    var qrCode = "10000001";
    var expectedResult = new QRValidationResult { Success = true };
    
    _mockTnTApiService
        .Setup(x => x.ValidateQRCodeAsync(qrCode))
        .ReturnsAsync(expectedResult);
    
    // Act
    var result = await _qrValidationService.ValidateQRCodeAsync(qrCode);
    
    // Assert
    Assert.IsTrue(result.Success);
    Assert.AreEqual(qrCode, result.Data.QRCode);
}
`

### Integration Tests
`csharp
[Test]
public async Task CreateShipment_ValidRequest_ReturnsShipmentId()
{
    // Arrange
    var request = new ShipmentRequest
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
    var result = await _shipmentService.CreateShipmentAsync(request);
    
    // Assert
    Assert.IsTrue(result.Success);
    Assert.IsNotNull(result.ShipmentId);
}
`

---
*Р СѓРєРѕРІРѕРґСЃС‚РІРѕ СЂР°Р·СЂР°Р±РѕС‚С‡РёРєР° РѕСЃРЅРѕРІР°РЅРѕ РЅР° РґР°РЅРЅС‹С… РёР· Р·Р°РїСЂРѕСЃР° 229127 Рё СЃРІСЏР·Р°РЅРЅС‹С… С‚РёРєРµС‚РѕРІ*
