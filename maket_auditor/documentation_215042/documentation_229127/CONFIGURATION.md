# РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ СЃРёСЃС‚РµРјС‹

## РћР±Р·РѕСЂ РєРѕРЅС„РёРіСѓСЂР°С†РёРё

Р”Р°РЅРЅС‹Р№ СЂР°Р·РґРµР» СЃРѕРґРµСЂР¶РёС‚ РёРЅС„РѕСЂРјР°С†РёСЋ Рѕ РєРѕРЅС„РёРіСѓСЂР°С†РёРё СЃРёСЃС‚РµРјС‹ РёРЅС‚РµРіСЂР°С†РёРё РњРў СЃ Track and Trace, РІРєР»СЋС‡Р°СЏ РЅР°СЃС‚СЂРѕР№РєРё РїСЂРёР»РѕР¶РµРЅРёСЏ, Р±Р°Р·С‹ РґР°РЅРЅС‹С… Рё РІРЅРµС€РЅРёС… РёРЅС‚РµРіСЂР°С†РёР№.

## РљРѕРЅС„РёРіСѓСЂР°С†РёРѕРЅРЅС‹Рµ С„Р°Р№Р»С‹

### 1. appsettings.json (API Miami)

#### РћСЃРЅРѕРІРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё
`json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning",
      "Microsoft.EntityFrameworkCore": "Warning"
    }
  },
  "AllowedHosts": "*",
  "ConnectionStrings": {
    "DefaultConnection": "Server=chicago-server;Database=Chicago;Trusted_Connection=true;TrustServerCertificate=true;",
    "TnTCache": "Server=redis-server:6379"
  },
  "JwtSettings": {
    "SecretKey": "your-secret-key-here-minimum-32-characters",
    "Issuer": "Miami-API",
    "Audience": "MT-Mobile",
    "ExpiryMinutes": 60
  },
  "TnTApi": {
    "BaseUrl": "https://api.trackandtrace.az",
    "Username": "9941234567",
    "Password": "your-tnt-password",
    "TimeoutSeconds": 30,
    "RetryCount": 3,
    "RateLimit": {
      "MaxRequestsPerSecond": 2,
      "BurstLimit": 5
    }
  },
  "SapReplication": {
    "ConnectionString": "Server=sap-server;Database=Replication;Trusted_Connection=true;",
    "SyncIntervalMinutes": 15,
    "BatchSize": 1000,
    "RetryCount": 3
  },
  "Caching": {
    "TnTTokenExpiryMinutes": 60,
    "ProductCacheExpiryMinutes": 30,
    "LocationCacheExpiryMinutes": 60
  }
}
`

#### РќР°СЃС‚СЂРѕР№РєРё РґР»СЏ СЂР°Р·РЅС‹С… СЃСЂРµРґ

**Development (appsettings.Development.json):**
`json
{
  "Logging": {
    "LogLevel": {
      "Default": "Debug",
      "Microsoft.AspNetCore": "Information"
    }
  },
  "ConnectionStrings": {
    "DefaultConnection": "Server=localhost;Database=Chicago_Dev;Trusted_Connection=true;TrustServerCertificate=true;"
  },
  "TnTApi": {
    "BaseUrl": "https://api-dev.trackandtrace.az",
    "Username": "dev_user",
    "Password": "dev_password"
  }
}
`

**Production (appsettings.Production.json):**
`json
{
  "Logging": {
    "LogLevel": {
      "Default": "Warning",
      "Microsoft.AspNetCore": "Error"
    }
  },
  "ConnectionStrings": {
    "DefaultConnection": "Server=prod-chicago-server;Database=Chicago;User Id=mt_user;Password=secure_password;TrustServerCertificate=true;"
  },
  "TnTApi": {
    "BaseUrl": "https://api.trackandtrace.az",
    "Username": "prod_user",
    "Password": "prod_password"
  }
}
`

### 2. РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ РјРѕР±РёР»СЊРЅРѕРіРѕ РїСЂРёР»РѕР¶РµРЅРёСЏ

#### App.xaml.cs
`csharp
public partial class App : Application
{
    public App()
    {
        InitializeComponent();
        
        // РќР°СЃС‚СЂРѕР№РєР° API РєР»РёРµРЅС‚Р°
        var apiBaseUrl = DeviceInfo.Platform == DevicePlatform.Android 
            ? "https://api-miami.company.com/v2"
            : "https://api-miami.company.com/v2";
            
        DependencyService.RegisterSingleton<IApiService>(
            new ApiService(apiBaseUrl));
            
        MainPage = new AppShell();
    }
}
`

#### Constants.cs
`csharp
public static class Constants
{
    // API РЅР°СЃС‚СЂРѕР№РєРё
    public const string ApiBaseUrl = "https://api-miami.company.com/v2";
    public const int ApiTimeoutSeconds = 30;
    public const int MaxRetryAttempts = 3;
    
    // QR Scanner РЅР°СЃС‚СЂРѕР№РєРё
    public const int QRScanTimeoutSeconds = 30;
    public const int QRScanQuality = 80; // 0-100
    
    // РљСЌС€РёСЂРѕРІР°РЅРёРµ
    public const int CacheExpiryMinutes = 15;
    public const int MaxCacheSizeMB = 100;
    
    // РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ
    public const int SyncIntervalMinutes = 15;
    public const int MaxOfflineItems = 1000;
    
    // T&T РЅР°СЃС‚СЂРѕР№РєРё
    public const string TnTDepartToExtId = "1000002";
    public const string TnTPartnerFiscalId = "9871000002";
}
`

### 3. РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ Р±Р°Р·С‹ РґР°РЅРЅС‹С…

#### Entity Framework Configuration
`csharp
public class ApplicationDbContext : DbContext
{
    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
    {
        if (!optionsBuilder.IsConfigured)
        {
            var connectionString = Environment.GetEnvironmentVariable("CONNECTION_STRING") 
                ?? "Server=localhost;Database=Chicago;Trusted_Connection=true;TrustServerCertificate=true;";
                
            optionsBuilder.UseSqlServer(connectionString, options =>
            {
                options.CommandTimeout(30);
                options.EnableRetryOnFailure(3);
                options.EnableSensitiveDataLogging(false);
            });
        }
    }
    
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ СЃСѓС‰РЅРѕСЃС‚РµР№
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(ApplicationDbContext).Assembly);
        
        // Р“Р»РѕР±Р°Р»СЊРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё
        modelBuilder.ConfigureGlobalFilters();
    }
}
`

#### SQL Server Configuration
`sql
-- РќР°СЃС‚СЂРѕР№РєРё Р±Р°Р·С‹ РґР°РЅРЅС‹С…
ALTER DATABASE [Chicago] SET COMPATIBILITY_LEVEL = 150;
ALTER DATABASE [Chicago] SET AUTO_CLOSE OFF;
ALTER DATABASE [Chicago] SET AUTO_SHRINK OFF;
ALTER DATABASE [Chicago] SET RECOVERY SIMPLE;

-- РќР°СЃС‚СЂРѕР№РєРё РїСЂРѕРёР·РІРѕРґРёС‚РµР»СЊРЅРѕСЃС‚Рё
ALTER DATABASE [Chicago] SET MAXDOP = 4;
ALTER DATABASE [Chicago] SET MAX_SERVER_MEMORY = 8192;

-- РќР°СЃС‚СЂРѕР№РєРё Р»РѕРіРёСЂРѕРІР°РЅРёСЏ
ALTER DATABASE [Chicago] SET LOG_BACKUP_INTERVAL = 15;
`

## РџРµСЂРµРјРµРЅРЅС‹Рµ РѕРєСЂСѓР¶РµРЅРёСЏ

### РћР±СЏР·Р°С‚РµР»СЊРЅС‹Рµ РїРµСЂРµРјРµРЅРЅС‹Рµ

#### API Miami
`ash
# Р‘Р°Р·Р° РґР°РЅРЅС‹С…
CONNECTION_STRING="Server=chicago-server;Database=Chicago;User Id=mt_user;Password=secure_password;TrustServerCertificate=true;"

# JWT РЅР°СЃС‚СЂРѕР№РєРё
JWT_SECRET_KEY="your-secret-key-here-minimum-32-characters"
JWT_ISSUER="Miami-API"
JWT_AUDIENCE="MT-Mobile"
JWT_EXPIRY_MINUTES="60"

# T&T API
TNT_API_URL="https://api.trackandtrace.az"
TNT_USERNAME="9941234567"
TNT_PASSWORD="your-tnt-password"
TNT_TIMEOUT_SECONDS="30"

# SAP Р РµРїР»РёРєР°С†РёСЏ
SAP_CONNECTION_STRING="Server=sap-server;Database=Replication;Trusted_Connection=true;"
SAP_SYNC_INTERVAL_MINUTES="15"

# РљСЌС€РёСЂРѕРІР°РЅРёРµ
REDIS_CONNECTION_STRING="redis-server:6379"
CACHE_EXPIRY_MINUTES="15"
`

#### РњРѕР±РёР»СЊРЅРѕРµ РїСЂРёР»РѕР¶РµРЅРёРµ
`ash
# API РЅР°СЃС‚СЂРѕР№РєРё
API_BASE_URL="https://api-miami.company.com/v2"
API_TIMEOUT_SECONDS="30"

# QR Scanner
QR_SCAN_QUALITY="80"
QR_SCAN_TIMEOUT_SECONDS="30"

# РЎРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ
SYNC_INTERVAL_MINUTES="15"
MAX_OFFLINE_ITEMS="1000"
`

### РћРїС†РёРѕРЅР°Р»СЊРЅС‹Рµ РїРµСЂРµРјРµРЅРЅС‹Рµ

#### Р›РѕРіРёСЂРѕРІР°РЅРёРµ
`ash
# РЈСЂРѕРІРµРЅСЊ Р»РѕРіРёСЂРѕРІР°РЅРёСЏ
LOG_LEVEL="Information"
LOG_FILE_PATH="/logs/mt-tnt-integration.log"
LOG_MAX_FILE_SIZE_MB="100"
LOG_MAX_FILES="10"

# Р”РµС‚Р°Р»РёР·Р°С†РёСЏ Р»РѕРіРѕРІ
ENABLE_SENSITIVE_DATA_LOGGING="false"
ENABLE_SQL_LOGGING="false"
`

#### РњРѕРЅРёС‚РѕСЂРёРЅРі
`ash
# Prometheus
PROMETHEUS_ENABLED="true"
PROMETHEUS_PORT="9090"

# Health Checks
HEALTH_CHECK_INTERVAL_SECONDS="30"
HEALTH_CHECK_TIMEOUT_SECONDS="10"
`

## Docker РєРѕРЅС„РёРіСѓСЂР°С†РёСЏ

### docker-compose.yml
`yaml
version: '3.8'

services:
  miami-api:
    build: .
    ports:
      - "5000:80"
    environment:
      - CONNECTION_STRING=Server=mssql;Database=Chicago;User Id=sa;Password=YourStrong@Passw0rd;TrustServerCertificate=true;
      - TNT_API_URL=https://api.trackandtrace.az
      - TNT_USERNAME=9941234567
      - TNT_PASSWORD=your-tnt-password
    depends_on:
      - mssql
      - redis
    networks:
      - mt-network

  mssql:
    image: mcr.microsoft.com/mssql/server:2019-latest
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=YourStrong@Passw0rd
    ports:
      - "1433:1433"
    volumes:
      - mssql_data:/var/opt/mssql
    networks:
      - mt-network

  redis:
    image: redis:6.2-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - mt-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - miami-api
    networks:
      - mt-network

volumes:
  mssql_data:
  redis_data:

networks:
  mt-network:
    driver: bridge
`

### Dockerfile
`dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:6.0 AS base
WORKDIR /app
EXPOSE 80
EXPOSE 443

FROM mcr.microsoft.com/dotnet/sdk:6.0 AS build
WORKDIR /src
COPY ["Miami.API/Miami.API.csproj", "Miami.API/"]
RUN dotnet restore "Miami.API/Miami.API.csproj"
COPY . .
WORKDIR "/src/Miami.API"
RUN dotnet build "Miami.API.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "Miami.API.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "Miami.API.dll"]
`

## Nginx РєРѕРЅС„РёРіСѓСЂР°С†РёСЏ

### nginx.conf
`
ginx
events {
    worker_connections 1024;
}

http {
    upstream miami-api {
        server miami-api:80;
    }

    server {
        listen 80;
        server_name api-miami.company.com;

        location / {
            proxy_pass http://miami-api;
            proxy_set_header Host System.Management.Automation.Internal.Host.InternalHost;
            proxy_set_header X-Real-IP ;
            proxy_set_header X-Forwarded-For ;
            proxy_set_header X-Forwarded-Proto ;
            
            # РўР°Р№РјР°СѓС‚С‹
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
            
            # Р‘СѓС„РµСЂРёР·Р°С†РёСЏ
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }

    # HTTPS РєРѕРЅС„РёРіСѓСЂР°С†РёСЏ
    server {
        listen 443 ssl http2;
        server_name api-miami.company.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        location / {
            proxy_pass http://miami-api;
            proxy_set_header Host System.Management.Automation.Internal.Host.InternalHost;
            proxy_set_header X-Real-IP ;
            proxy_set_header X-Forwarded-For ;
            proxy_set_header X-Forwarded-Proto ;
        }
    }
}
`

## РњРѕРЅРёС‚РѕСЂРёРЅРі Рё Р»РѕРіРёСЂРѕРІР°РЅРёРµ

### Serilog РєРѕРЅС„РёРіСѓСЂР°С†РёСЏ
`json
{
  "Serilog": {
    "Using": ["Serilog.Sinks.Console", "Serilog.Sinks.File", "Serilog.Sinks.Seq"],
    "MinimumLevel": {
      "Default": "Information",
      "Override": {
        "Microsoft": "Warning",
        "System": "Warning"
      }
    },
    "WriteTo": [
      {
        "Name": "Console",
        "Args": {
          "outputTemplate": "{Timestamp:yyyy-MM-dd HH:mm:ss.fff zzz} [{Level:u3}] {Message:lj}{NewLine}{Exception}"
        }
      },
      {
        "Name": "File",
        "Args": {
          "path": "/logs/mt-tnt-integration-.log",
          "rollingInterval": "Day",
          "retainedFileCountLimit": 10,
          "fileSizeLimitBytes": 10485760,
          "outputTemplate": "{Timestamp:yyyy-MM-dd HH:mm:ss.fff zzz} [{Level:u3}] {Message:lj}{NewLine}{Exception}"
        }
      },
      {
        "Name": "Seq",
        "Args": {
          "serverUrl": "http://seq:5341",
          "apiKey": "your-seq-api-key"
        }
      }
    ],
    "Enrich": ["FromLogContext", "WithMachineName", "WithThreadId"]
  }
}
`

### Prometheus РєРѕРЅС„РёРіСѓСЂР°С†РёСЏ
`yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'miami-api'
    static_configs:
      - targets: ['miami-api:80']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'mssql'
    static_configs:
      - targets: ['mssql:1433']
    scrape_interval: 60s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 60s
`

## Р‘РµР·РѕРїР°СЃРЅРѕСЃС‚СЊ

### РЁРёС„СЂРѕРІР°РЅРёРµ РїР°СЂРѕР»РµР№
`csharp
public class PasswordHasher
{
    public string HashPassword(string password)
    {
        return BCrypt.Net.BCrypt.HashPassword(password, BCrypt.Net.BCrypt.GenerateSalt(12));
    }
    
    public bool VerifyPassword(string password, string hash)
    {
        return BCrypt.Net.BCrypt.Verify(password, hash);
    }
}
`

### JWT РЅР°СЃС‚СЂРѕР№РєРё
`csharp
public class JwtSettings
{
    public string SecretKey { get; set; }
    public string Issuer { get; set; }
    public string Audience { get; set; }
    public int ExpiryMinutes { get; set; }
    
    public SymmetricSecurityKey GetSymmetricSecurityKey()
    {
        return new SymmetricSecurityKey(Encoding.UTF8.GetBytes(SecretKey));
    }
}
`

### CORS РЅР°СЃС‚СЂРѕР№РєРё
`csharp
services.AddCors(options =>
{
    options.AddPolicy("AllowMobileApp", builder =>
    {
        builder
            .WithOrigins("https://mt.company.com")
            .AllowAnyMethod()
            .AllowAnyHeader()
            .AllowCredentials();
    });
});
`

## РџСЂРѕРІРµСЂРєР° РєРѕРЅС„РёРіСѓСЂР°С†РёРё

### РЎРєСЂРёРїС‚ РїСЂРѕРІРµСЂРєРё
`ash
#!/bin/bash
# check-config.sh

echo "РџСЂРѕРІРµСЂРєР° РєРѕРЅС„РёРіСѓСЂР°С†РёРё СЃРёСЃС‚РµРјС‹..."

# РџСЂРѕРІРµСЂРєР° РїРµСЂРµРјРµРЅРЅС‹С… РѕРєСЂСѓР¶РµРЅРёСЏ
echo "РџСЂРѕРІРµСЂРєР° РїРµСЂРµРјРµРЅРЅС‹С… РѕРєСЂСѓР¶РµРЅРёСЏ..."
required_vars=("CONNECTION_STRING" "JWT_SECRET_KEY" "TNT_API_URL" "TNT_USERNAME" "TNT_PASSWORD")
for var in ""; do
    if [ -z "" ]; then
        echo "вќЊ РџРµСЂРµРјРµРЅРЅР°СЏ  РЅРµ СѓСЃС‚Р°РЅРѕРІР»РµРЅР°"
        exit 1
    else
        echo "вњ…  СѓСЃС‚Р°РЅРѕРІР»РµРЅР°"
    fi
done

# РџСЂРѕРІРµСЂРєР° РїРѕРґРєР»СЋС‡РµРЅРёСЏ Рє Р±Р°Р·Рµ РґР°РЅРЅС‹С…
echo "РџСЂРѕРІРµСЂРєР° РїРѕРґРєР»СЋС‡РµРЅРёСЏ Рє Р±Р°Р·Рµ РґР°РЅРЅС‹С…..."
if sqlcmd -S chicago-server -d Chicago -E -Q "SELECT 1" > /dev/null 2>&1; then
    echo "вњ… РџРѕРґРєР»СЋС‡РµРЅРёРµ Рє Р±Р°Р·Рµ РґР°РЅРЅС‹С… СѓСЃРїРµС€РЅРѕ"
else
    echo "вќЊ РќРµ СѓРґР°РµС‚СЃСЏ РїРѕРґРєР»СЋС‡РёС‚СЊСЃСЏ Рє Р±Р°Р·Рµ РґР°РЅРЅС‹С…"
    exit 1
fi

# РџСЂРѕРІРµСЂРєР° T&T API
echo "РџСЂРѕРІРµСЂРєР° T&T API..."
if curl -s -o /dev/null -w "%{http_code}" "/alive" | grep -q "200"; then
    echo "вњ… T&T API РґРѕСЃС‚СѓРїРµРЅ"
else
    echo "вќЊ T&T API РЅРµРґРѕСЃС‚СѓРїРµРЅ"
    exit 1
fi

echo "вњ… Р’СЃРµ РїСЂРѕРІРµСЂРєРё РїСЂРѕР№РґРµРЅС‹ СѓСЃРїРµС€РЅРѕ"
`

---
*РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ РѕСЃРЅРѕРІР°РЅР° РЅР° С‚СЂРµР±РѕРІР°РЅРёСЏС… РёР· Р·Р°РїСЂРѕСЃР° 229127*
