# Техническое решение: KA_NAME ТТ - Исправление отображения названий торговых точек

## Обзор решения

### Проблема
Система репликации неправильно отображает названия торговых точек в отчетах, используя данные из юридических лиц вместо поля `KA_NAME` из справочника клиентов.

### Цель решения
Исправить логику отображения названий торговых точек, чтобы система приоритетно использовала поле `KA_NAME` из справочника клиентов.

## Архитектура решения

### Компоненты системы
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Справочник    │    │   Логика        │    │   XML Отчеты    │
│   клиентов      │    │   отображения   │    │                 │
│                 │    │                 │    │                 │
│ - ТТ ID         │───►│ - Проверка      │───►│ - Название ТТ   │
│ - KA_NAME       │    │   KA_NAME       │    │ - Корректное    │
│ - Юр. лица      │    │ - Fallback      │    │   отображение   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Алгоритм решения
1. **Проверка наличия KA_NAME**: Проверить, заполнено ли поле KA_NAME для торговой точки
2. **Приоритетное использование**: Если KA_NAME заполнено, использовать его для отображения
3. **Fallback логика**: Если KA_NAME пустое, использовать название из юридического лица
4. **Валидация**: Проверить корректность полученного названия

## Детальная реализация

### 1. SQL запрос для получения названия ТТ

#### Исходный запрос (проблемный)
```sql
-- Старая логика - всегда использует юридическое лицо
SELECT 
    tt.id as tt_id,
    le.name as display_name
FROM refOutlets tt
LEFT JOIN refLegalEntities le ON tt.idLegalEntity = le.id
WHERE tt.id = @tt_id
```

#### Исправленный запрос
```sql
-- Новая логика - приоритет KA_NAME
SELECT 
    tt.id as tt_id,
    CASE 
        WHEN c.KA_NAME IS NOT NULL AND c.KA_NAME != '' 
        THEN c.KA_NAME
        ELSE le.name
    END as display_name
FROM refOutlets tt
LEFT JOIN refClients c ON tt.idClient = c.id
LEFT JOIN refLegalEntities le ON tt.idLegalEntity = le.id
WHERE tt.id = @tt_id
```

### 2. C# код для обработки названий

#### Класс для работы с названиями ТТ
```csharp
public class TradingPointNameResolver
{
    private readonly string _connectionString;
    
    public TradingPointNameResolver(string connectionString)
    {
        _connectionString = connectionString;
    }
    
    /// <summary>
    /// Получает отображаемое название торговой точки
    /// </summary>
    /// <param name="ttId">ID торговой точки</param>
    /// <returns>Название для отображения</returns>
    public string GetDisplayName(int ttId)
    {
        using (var connection = new SqlConnection(_connectionString))
        {
            var query = @"
                SELECT 
                    CASE 
                        WHEN c.KA_NAME IS NOT NULL AND c.KA_NAME != '' 
                        THEN c.KA_NAME
                        ELSE le.name
                    END as display_name
                FROM refOutlets tt
                LEFT JOIN refClients c ON tt.idClient = c.id
                LEFT JOIN refLegalEntities le ON tt.idLegalEntity = le.id
                WHERE tt.id = @tt_id";
                
            using (var command = new SqlCommand(query, connection))
            {
                command.Parameters.AddWithValue("@tt_id", ttId);
                connection.Open();
                
                var result = command.ExecuteScalar();
                return result?.ToString() ?? "Неизвестная ТТ";
            }
        }
    }
    
    /// <summary>
    /// Получает названия для множества торговых точек
    /// </summary>
    /// <param name="ttIds">Список ID торговых точек</param>
    /// <returns>Словарь ID -> название</returns>
    public Dictionary<int, string> GetDisplayNames(IEnumerable<int> ttIds)
    {
        var result = new Dictionary<int, string>();
        
        if (!ttIds.Any()) return result;
        
        using (var connection = new SqlConnection(_connectionString))
        {
            var query = @"
                SELECT 
                    tt.id as tt_id,
                    CASE 
                        WHEN c.KA_NAME IS NOT NULL AND c.KA_NAME != '' 
                        THEN c.KA_NAME
                        ELSE le.name
                    END as display_name
                FROM refOutlets tt
                LEFT JOIN refClients c ON tt.idClient = c.id
                LEFT JOIN refLegalEntities le ON tt.idLegalEntity = le.id
                WHERE tt.id IN (" + string.Join(",", ttIds) + ")";
                
            using (var command = new SqlCommand(query, connection))
            {
                connection.Open();
                using (var reader = command.ExecuteReader())
                {
                    while (reader.Read())
                    {
                        var ttId = reader.GetInt32("tt_id");
                        var displayName = reader.GetString("display_name");
                        result[ttId] = displayName;
                    }
                }
            }
        }
        
        return result;
    }
}
```

### 3. Интеграция в систему репликации

#### Модификация класса формирования отчетов
```csharp
public class ReportGenerator
{
    private readonly TradingPointNameResolver _nameResolver;
    
    public ReportGenerator(string connectionString)
    {
        _nameResolver = new TradingPointNameResolver(connectionString);
    }
    
    /// <summary>
    /// Генерирует XML отчет с корректными названиями ТТ
    /// </summary>
    public string GenerateClientReport(int clientId)
    {
        var outlets = GetClientOutlets(clientId);
        var outletNames = _nameResolver.GetDisplayNames(outlets.Select(o => o.Id));
        
        var xml = new StringBuilder();
        xml.AppendLine("<?xml version=\"1.0\" encoding=\"utf-8\"?>");
        xml.AppendLine("<clients>");
        
        foreach (var outlet in outlets)
        {
            var displayName = outletNames.ContainsKey(outlet.Id) 
                ? outletNames[outlet.Id] 
                : "Неизвестная ТТ";
                
            xml.AppendLine($"  <client id=\"{outlet.Id}\" name=\"{EscapeXml(displayName)}\" />");
        }
        
        xml.AppendLine("</clients>");
        return xml.ToString();
    }
    
    private string EscapeXml(string input)
    {
        return input
            .Replace("&", "&amp;")
            .Replace("<", "&lt;")
            .Replace(">", "&gt;")
            .Replace("\"", "&quot;")
            .Replace("'", "&apos;");
    }
}
```

### 4. Хранимая процедура для получения названий

#### Создание хранимой процедуры
```sql
CREATE PROCEDURE sp_GetTradingPointDisplayName
    @TradingPointId INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        tt.id as TradingPointId,
        CASE 
            WHEN c.KA_NAME IS NOT NULL AND c.KA_NAME != '' 
            THEN c.KA_NAME
            ELSE ISNULL(le.name, 'Неизвестная ТТ')
        END as DisplayName,
        CASE 
            WHEN c.KA_NAME IS NOT NULL AND c.KA_NAME != '' 
            THEN 'KA_NAME'
            ELSE 'LegalEntity'
        END as NameSource
    FROM refOutlets tt
    LEFT JOIN refClients c ON tt.idClient = c.id
    LEFT JOIN refLegalEntities le ON tt.idLegalEntity = le.id
    WHERE tt.id = @TradingPointId;
END
```

#### Использование хранимой процедуры
```csharp
public TradingPointInfo GetTradingPointInfo(int ttId)
{
    using (var connection = new SqlConnection(_connectionString))
    using (var command = new SqlCommand("sp_GetTradingPointDisplayName", connection))
    {
        command.CommandType = CommandType.StoredProcedure;
        command.Parameters.AddWithValue("@TradingPointId", ttId);
        
        connection.Open();
        using (var reader = command.ExecuteReader())
        {
            if (reader.Read())
            {
                return new TradingPointInfo
                {
                    Id = reader.GetInt32("TradingPointId"),
                    DisplayName = reader.GetString("DisplayName"),
                    NameSource = reader.GetString("NameSource")
                };
            }
        }
    }
    
    return null;
}
```

## Конфигурация

### Настройки в конфигурационном файле
```xml
<!-- app.config или web.config -->
<configuration>
  <appSettings>
    <!-- Включение использования KA_NAME для отображения ТТ -->
    <add key="UseKANameForTradingPoints" value="true" />
    
    <!-- Fallback на юридическое лицо если KA_NAME пустое -->
    <add key="FallbackToLegalEntity" value="true" />
    
    <!-- Значение по умолчанию для неизвестных ТТ -->
    <add key="DefaultTradingPointName" value="Неизвестная ТТ" />
  </appSettings>
</configuration>
```

### Чтение конфигурации
```csharp
public class TradingPointConfig
{
    public bool UseKANameForTradingPoints { get; set; }
    public bool FallbackToLegalEntity { get; set; }
    public string DefaultTradingPointName { get; set; }
    
    public static TradingPointConfig Load()
    {
        return new TradingPointConfig
        {
            UseKANameForTradingPoints = bool.Parse(
                ConfigurationManager.AppSettings["UseKANameForTradingPoints"] ?? "true"),
            FallbackToLegalEntity = bool.Parse(
                ConfigurationManager.AppSettings["FallbackToLegalEntity"] ?? "true"),
            DefaultTradingPointName = ConfigurationManager.AppSettings["DefaultTradingPointName"] 
                ?? "Неизвестная ТТ"
        };
    }
}
```

## Обработка ошибок

### Валидация данных
```csharp
public class TradingPointNameValidator
{
    public ValidationResult ValidateDisplayName(string displayName)
    {
        var result = new ValidationResult();
        
        if (string.IsNullOrWhiteSpace(displayName))
        {
            result.AddError("Название торговой точки не может быть пустым");
        }
        
        if (displayName.Length > 255)
        {
            result.AddError("Название торговой точки слишком длинное (максимум 255 символов)");
        }
        
        if (ContainsInvalidCharacters(displayName))
        {
            result.AddError("Название торговой точки содержит недопустимые символы");
        }
        
        return result;
    }
    
    private bool ContainsInvalidCharacters(string input)
    {
        var invalidChars = new[] { '<', '>', '&', '"', '\'' };
        return invalidChars.Any(c => input.Contains(c));
    }
}
```

### Логирование
```csharp
public class TradingPointNameLogger
{
    private readonly ILogger _logger;
    
    public TradingPointNameLogger(ILogger logger)
    {
        _logger = logger;
    }
    
    public void LogNameResolution(int ttId, string displayName, string source)
    {
        _logger.LogInformation(
            "Resolved trading point name: TT={TradingPointId}, Name={DisplayName}, Source={Source}",
            ttId, displayName, source);
    }
    
    public void LogNameResolutionError(int ttId, Exception ex)
    {
        _logger.LogError(ex,
            "Error resolving trading point name for TT={TradingPointId}",
            ttId);
    }
}
```

## Тестирование

### Unit тесты
```csharp
[TestClass]
public class TradingPointNameResolverTests
{
    [TestMethod]
    public void GetDisplayName_WithKAName_ShouldReturnKAName()
    {
        // Arrange
        var resolver = new TradingPointNameResolver(connectionString);
        var ttId = 460011; // ТТ с KA_NAME = "Шах"
        
        // Act
        var result = resolver.GetDisplayName(ttId);
        
        // Assert
        Assert.AreEqual("Шах", result);
    }
    
    [TestMethod]
    public void GetDisplayName_WithoutKAName_ShouldReturnLegalEntityName()
    {
        // Arrange
        var resolver = new TradingPointNameResolver(connectionString);
        var ttId = 12345; // ТТ без KA_NAME
        
        // Act
        var result = resolver.GetDisplayName(ttId);
        
        // Assert
        Assert.AreEqual("Шахабасова З.У. ИП", result);
    }
    
    [TestMethod]
    public void GetDisplayName_WithEmptyKAName_ShouldReturnLegalEntityName()
    {
        // Arrange
        var resolver = new TradingPointNameResolver(connectionString);
        var ttId = 67890; // ТТ с пустым KA_NAME
        
        // Act
        var result = resolver.GetDisplayName(ttId);
        
        // Assert
        Assert.AreEqual("ООО Тест", result);
    }
}
```

### Интеграционные тесты
```csharp
[TestClass]
public class ReportGeneratorIntegrationTests
{
    [TestMethod]
    public void GenerateClientReport_ShouldUseCorrectTradingPointNames()
    {
        // Arrange
        var generator = new ReportGenerator(connectionString);
        var clientId = 1;
        
        // Act
        var report = generator.GenerateClientReport(clientId);
        
        // Assert
        Assert.IsTrue(report.Contains("name=\"Шах\"")); // KA_NAME
        Assert.IsTrue(report.Contains("name=\"ООО Тест\"")); // Legal Entity
    }
}
```

## Производительность

### Оптимизация запросов
```sql
-- Создание индекса для ускорения поиска
CREATE INDEX IX_refClients_KA_NAME 
ON refClients(KA_NAME) 
WHERE KA_NAME IS NOT NULL AND KA_NAME != '';

-- Создание индекса для связи ТТ-Клиент
CREATE INDEX IX_refOutlets_idClient 
ON refOutlets(idClient);
```

### Кэширование
```csharp
public class CachedTradingPointNameResolver
{
    private readonly TradingPointNameResolver _resolver;
    private readonly MemoryCache _cache;
    private readonly TimeSpan _cacheExpiration = TimeSpan.FromMinutes(30);
    
    public CachedTradingPointNameResolver(TradingPointNameResolver resolver)
    {
        _resolver = resolver;
        _cache = new MemoryCache(new MemoryCacheOptions());
    }
    
    public string GetDisplayName(int ttId)
    {
        var cacheKey = $"tp_name_{ttId}";
        
        if (_cache.TryGetValue(cacheKey, out string cachedName))
        {
            return cachedName;
        }
        
        var name = _resolver.GetDisplayName(ttId);
        _cache.Set(cacheKey, name, _cacheExpiration);
        
        return name;
    }
}
```

## Мониторинг

### Метрики для отслеживания
- Количество ТТ с заполненным KA_NAME
- Количество ТТ, использующих fallback на юридическое лицо
- Время выполнения запросов получения названий
- Ошибки при получении названий ТТ

### Дашборд мониторинга
```sql
-- Запрос для мониторинга использования KA_NAME
SELECT 
    COUNT(*) as TotalTradingPoints,
    SUM(CASE WHEN c.KA_NAME IS NOT NULL AND c.KA_NAME != '' THEN 1 ELSE 0 END) as UsingKAName,
    SUM(CASE WHEN c.KA_NAME IS NULL OR c.KA_NAME = '' THEN 1 ELSE 0 END) as UsingLegalEntity
FROM refOutlets tt
LEFT JOIN refClients c ON tt.idClient = c.id;
```

## Развертывание

### Скрипт развертывания
```sql
-- 1. Создание хранимой процедуры
-- (код хранимой процедуры из раздела выше)

-- 2. Создание индексов
CREATE INDEX IX_refClients_KA_NAME 
ON refClients(KA_NAME) 
WHERE KA_NAME IS NOT NULL AND KA_NAME != '';

CREATE INDEX IX_refOutlets_idClient 
ON refOutlets(idClient);

-- 3. Обновление конфигурации
-- (обновление app.config/web.config)
```

### Проверка развертывания
```sql
-- Проверка работы исправления
EXEC sp_GetTradingPointDisplayName @TradingPointId = 460011;
-- Ожидаемый результат: DisplayName = "Шах", NameSource = "KA_NAME"
```

## Заключение

Предложенное техническое решение обеспечивает:

1. **Корректное отображение**: Приоритетное использование поля KA_NAME для названий ТТ
2. **Обратную совместимость**: Fallback на юридическое лицо при отсутствии KA_NAME
3. **Производительность**: Оптимизированные запросы и кэширование
4. **Надежность**: Обработка ошибок и валидация данных
5. **Мониторинг**: Отслеживание использования различных источников названий

Решение полностью устраняет проблему, описанную в тикете 22963, и обеспечивает корректное отображение названий торговых точек в отчетах системы репликации.

---
*Документ создан: 27.09.2025*  
*Версия: 1.0*  
*Статус: Готов к реализации*
