# РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ СЃРёСЃС‚РµРјС‹

## РћР±Р·РѕСЂ РєРѕРЅС„РёРіСѓСЂР°С†РёРё

РЎРёСЃС‚РµРјР° РёРЅС‚РµРіСЂР°С†РёРё РњРў СЃ Track and Trace С‚СЂРµР±СѓРµС‚ РЅР°СЃС‚СЂРѕР№РєРё СЂР°Р·Р»РёС‡РЅС‹С… РєРѕРјРїРѕРЅРµРЅС‚РѕРІ РґР»СЏ РєРѕСЂСЂРµРєС‚РЅРѕР№ СЂР°Р±РѕС‚С‹.

## API РЅР°СЃС‚СЂРѕР№РєРё

### Track and Trace API

#### Р‘Р°Р·РѕРІС‹Рµ РїР°СЂР°РјРµС‚СЂС‹:
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

#### РђРІС‚РѕСЂРёР·Р°С†РёСЏ:
`json
{
  "TnTAuth": {
    "Username": "9941234567",
    "Password": "encrypted_password",
    "TokenExpiryMinutes": 60,
    "RefreshTokenBeforeExpiryMinutes": 10
  }
}
`

#### Р—Р°РіРѕР»РѕРІРєРё Р·Р°РїСЂРѕСЃРѕРІ:
`json
{
  "TnTHeaders": {
    "ContentType": "application/json; charset=utf-8",
    "RequestedWith": "XMLHttpRequest",
    "Language": "en",
    "SignatureRequired": true
  }
}
`

### Miami API

#### РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ СЃРµСЂРІРµСЂР°:
`json
{
  "MiamiApi": {
    "BaseUrl": "https://api.miami.local",
    "ApiKey": "your_api_key_here",
    "TimeoutSeconds": 30,
    "MaxConcurrentRequests": 100
  }
}
`

## Р‘Р°Р·Р° РґР°РЅРЅС‹С…

### РЎС‚СЂРѕРєР° РїРѕРґРєР»СЋС‡РµРЅРёСЏ:
`json
{
  "ConnectionStrings": {
    "Chicago": "Server=localhost;Database=Chicago;Trusted_Connection=true;MultipleActiveResultSets=true;",
    "ChicagoReadOnly": "Server=readonly-server;Database=Chicago;Trusted_Connection=true;ApplicationIntent=ReadOnly;"
  }
}
`

### РџР°СЂР°РјРµС‚СЂС‹ РїРѕРґРєР»СЋС‡РµРЅРёСЏ:
`json
{
  "Database": {
    "CommandTimeout": 30,
    "ConnectionTimeout": 15,
    "MaxPoolSize": 100,
    "MinPoolSize": 5,
    "EnableRetryOnFailure": true,
    "MaxRetryCount": 3
  }
}
`

## РџРµСЂРµРјРµРЅРЅС‹Рµ РѕРєСЂСѓР¶РµРЅРёСЏ

### РћР±СЏР·Р°С‚РµР»СЊРЅС‹Рµ РїРµСЂРµРјРµРЅРЅС‹Рµ:
`ash
# T&T API
TNT_API_BASE_URL=https://api.trackandtrace.az
TNT_API_USERNAME=your_username
TNT_API_PASSWORD=your_password

# Р‘Р°Р·Р° РґР°РЅРЅС‹С…
CONNECTION_STRING=Server=localhost;Database=Chicago;Trusted_Connection=true;

# Miami API
MIAMI_API_BASE_URL=https://api.miami.local
MIAMI_API_KEY=your_api_key

# Р›РѕРіРёСЂРѕРІР°РЅРёРµ
LOG_LEVEL=Information
LOG_FILE_PATH=/logs/mt-tnt-integration.log
`

### РћРїС†РёРѕРЅР°Р»СЊРЅС‹Рµ РїРµСЂРµРјРµРЅРЅС‹Рµ:
`ash
# РљСЌС€РёСЂРѕРІР°РЅРёРµ
REDIS_CONNECTION_STRING=localhost:6379
CACHE_TTL_SECONDS=3600

# РњРѕРЅРёС‚РѕСЂРёРЅРі
ENABLE_METRICS=true
METRICS_ENDPOINT=/metrics

# РћС‚Р»Р°РґРєР°
DEBUG_MODE=false
VERBOSE_LOGGING=false
`

## РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ РїСЂРёР»РѕР¶РµРЅРёСЏ

### appsettings.json:
`json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft": "Warning",
      "Microsoft.Hosting.Lifetime": "Information"
    },
    "File": {
      "Path": "/logs/mt-tnt-integration.log",
      "MaxFileSize": "10MB",
      "MaxFiles": 5
    }
  },
  "AllowedHosts": "*",
  "TnTApi": {
    "BaseUrl": "https://api.trackandtrace.az",
    "TimeoutSeconds": 30,
    "RetryCount": 3,
    "RateLimit": {
      "MaxRequestsPerSecond": 2,
      "BurstLimit": 5
    }
  },
  "Database": {
    "ConnectionString": "Server=localhost;Database=Chicago;Trusted_Connection=true;",
    "CommandTimeout": 30,
    "EnableRetryOnFailure": true,
    "MaxRetryCount": 3
  },
  "MiamiApi": {
    "BaseUrl": "https://api.miami.local",
    "ApiKey": "your_api_key_here",
    "TimeoutSeconds": 30
  },
  "Security": {
    "JwtSecret": "your_jwt_secret_key",
    "TokenExpiryMinutes": 60,
    "RequireHttps": true
  }
}
`

## РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ РјРѕР±РёР»СЊРЅРѕРіРѕ РїСЂРёР»РѕР¶РµРЅРёСЏ

### config.js:
`javascript
const CONFIG = {
  // API РЅР°СЃС‚СЂРѕР№РєРё
  API: {
    BASE_URL: 'https://api.miami.local',
    TIMEOUT: 30000,
    RETRY_COUNT: 3
  },
  
  // T&T РЅР°СЃС‚СЂРѕР№РєРё
  TNT: {
    BASE_URL: 'https://api.trackandtrace.az',
    TIMEOUT: 30000,
    RATE_LIMIT: 2000 // 2 СЃРµРєСѓРЅРґС‹ РјРµР¶РґСѓ Р·Р°РїСЂРѕСЃР°РјРё
  },
  
  // РЎРєР°РЅРёСЂРѕРІР°РЅРёРµ
  SCANNER: {
    PREFERRED_CAMERA: 'back',
    SCAN_DURATION: 3000,
    ENABLE_SOUND: true,
    ENABLE_VIBRATION: true
  },
  
  // UI РЅР°СЃС‚СЂРѕР№РєРё
  UI: {
    THEME: 'light',
    LANGUAGE: 'ru',
    AUTO_SAVE_INTERVAL: 30000
  }
};
`

## РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ Р±РµР·РѕРїР°СЃРЅРѕСЃС‚Рё

### SSL/TLS:
`json
{
  "Security": {
    "RequireHttps": true,
    "TlsVersion": "1.2",
    "CipherSuites": [
      "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
      "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"
    ]
  }
}
`

### РђСѓС‚РµРЅС‚РёС„РёРєР°С†РёСЏ:
`json
{
  "Authentication": {
    "JwtSecret": "your_super_secret_jwt_key_minimum_32_characters",
    "TokenExpiryMinutes": 60,
    "RefreshTokenExpiryDays": 7,
    "RequireStrongPasswords": true
  }
}
`

## РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ Р»РѕРіРёСЂРѕРІР°РЅРёСЏ

### NLog.config:
`xml
<?xml version="1.0" encoding="utf-8" ?>
<nlog xmlns="http://www.nlog-project.org/schemas/NLog.xsd"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      autoReload="true"
      internalLogLevel="Info"
      internalLogFile="c:\temp\internal-nlog-AspNetCore.txt">

  <targets>
    <target xsi:type="File" name="allfile" fileName="c:\temp\nlog-AspNetCore-all-.log"
            layout="|||| " />

    <target xsi:type="File" name="ownFile-web" fileName="c:\temp\nlog-AspNetCore-own-.log"
            layout="|||| " />

    <target xsi:type="Console" name="console" layout="||| " />
  </targets>

  <rules>
    <logger name="*" minlevel="Trace" writeTo="allfile" />
    <logger name="Microsoft.*" maxlevel="Info" final="true" />
    <logger name="Microsoft.Hosting.Lifetime" minlevel="Trace" writeTo="ownFile-web" final="true" />
    <logger name="*" minlevel="Trace" writeTo="console" />
  </rules>
</nlog>
`

## РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР°

### Health Checks:
`csharp
services.AddHealthChecks()
    .AddSqlServer(connectionString)
    .AddUrlGroup(new Uri("https://api.trackandtrace.az/alive"), "tnt-api")
    .AddCheck<MiamiApiHealthCheck>("miami-api");
`

### РњРµС‚СЂРёРєРё:
`json
{
  "Metrics": {
    "Enabled": true,
    "Endpoint": "/metrics",
    "Port": 9090,
    "IncludeSystemMetrics": true
  }
}
`

## РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ РґР»СЏ СЂР°Р·РЅС‹С… РѕРєСЂСѓР¶РµРЅРёР№

### Development:
`json
{
  "Environment": "Development",
  "TnTApi": {
    "BaseUrl": "https://dev-api.trackandtrace.az",
    "TimeoutSeconds": 60
  },
  "Database": {
    "ConnectionString": "Server=dev-server;Database=Chicago_Dev;Trusted_Connection=true;"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Debug"
    }
  }
}
`

### UAT:
`json
{
  "Environment": "UAT",
  "TnTApi": {
    "BaseUrl": "https://uat-api.trackandtrace.az",
    "TimeoutSeconds": 30
  },
  "Database": {
    "ConnectionString": "Server=uat-server;Database=Chicago_UAT;Trusted_Connection=true;"
  }
}
`

### Production:
`json
{
  "Environment": "Production",
  "TnTApi": {
    "BaseUrl": "https://api.trackandtrace.az",
    "TimeoutSeconds": 30
  },
  "Database": {
    "ConnectionString": "Server=prod-server;Database=Chicago;Trusted_Connection=true;"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Warning"
    }
  }
}
`

## РџСЂРѕРІРµСЂРєР° РєРѕРЅС„РёРіСѓСЂР°С†РёРё

### РЎРєСЂРёРїС‚ РїСЂРѕРІРµСЂРєРё:
`powershell
# РџСЂРѕРІРµСЂРєР° РїРµСЂРµРјРµРЅРЅС‹С… РѕРєСЂСѓР¶РµРЅРёСЏ
Write-Host "Checking environment variables..."
 = @("TNT_API_BASE_URL", "TNT_API_USERNAME", "CONNECTION_STRING")
foreach ( in ) {
    if (-not (Get-Item "env:" -ErrorAction SilentlyContinue)) {
        Write-Error "Missing required environment variable: "
    } else {
        Write-Host "вњ“  is set"
    }
}

# РџСЂРѕРІРµСЂРєР° РїРѕРґРєР»СЋС‡РµРЅРёСЏ Рє API
Write-Host "Testing T&T API connection..."
try {
     = Invoke-RestMethod -Uri "/alive" -Method Post
    Write-Host "вњ“ T&T API is accessible"
} catch {
    Write-Error "вњ— T&T API is not accessible: "
}
`

---
*РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ РѕСЃРЅРѕРІР°РЅР° РЅР° С‚СЂРµР±РѕРІР°РЅРёСЏС… РёР· Р·Р°РїСЂРѕСЃР° 215042 Рё СЃРІСЏР·Р°РЅРЅС‹С… РєРѕРјРїРѕРЅРµРЅС‚РѕРІ*
