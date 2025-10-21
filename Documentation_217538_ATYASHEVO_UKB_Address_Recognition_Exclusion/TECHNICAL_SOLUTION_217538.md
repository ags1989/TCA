# Техническое решение: ATYASHEVO Сервис УКБ. Инд. критерий для исключения повторного распознавания адреса

## Архитектура решения

### Общая схема
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Чикаго        │    │   Сервис РиГ    │    │   База данных   │
│                 │    │                 │    │                 │
│ - Управление ТТ │───►│ - Распознавание │───►│ - Классификаторы│
│ - Классификатор │    │ - Геокодирование│    │ - Торговые точки│
│ - Интерфейс     │    │ - Обработка     │    │ - Статусы       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Компоненты системы

#### 1. Чикаго (Frontend + Backend)
- **Интерфейс управления ТТ**: Создание, редактирование, импорт
- **Управление классификатором**: Установка значений "0", "1", "2"
- **API**: Обработка запросов и интеграция с сервисом РиГ
- **Валидация**: Проверка корректности значений классификатора

#### 2. Сервис РиГ (Распознавание и Геокодирование)
- **Обработка ТТ**: Проверка классификатора перед распознаванием
- **Логика исключения**: Игнорирование ТТ с определенными статусами
- **Интеграция**: Связь с внешними сервисами распознавания
- **Логирование**: Отслеживание отправки/игнорирования ТТ

#### 3. База данных
- **Классификаторы**: Хранение значений для ТТ
- **Торговые точки**: Основные данные ТТ
- **Статусы**: Отслеживание изменений статусов
- **Логи**: Аудит операций с классификаторами

## Модель данных

### Таблица классификаторов
```sql
CREATE TABLE [dbo].[refOutletClassifiers] (
    [Id] INT IDENTITY(1,1) PRIMARY KEY,
    [OutletId] INT NOT NULL,
    [ClassifierCode] NVARCHAR(50) NOT NULL,
    [ClassifierValue] NVARCHAR(10) NULL,
    [CreatedDate] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [ModifiedDate] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [CreatedBy] NVARCHAR(100) NULL,
    [ModifiedBy] NVARCHAR(100) NULL,
    
    CONSTRAINT [FK_refOutletClassifiers_Outlets] 
        FOREIGN KEY ([OutletId]) REFERENCES [dbo].[refOutlets]([Id]),
    CONSTRAINT [FK_refOutletClassifiers_Classifiers] 
        FOREIGN KEY ([ClassifierCode]) REFERENCES [dbo].[refClassifiers]([Code])
);

-- Индексы для производительности
CREATE INDEX IX_refOutletClassifiers_OutletId ON [dbo].[refOutletClassifiers] ([OutletId]);
CREATE INDEX IX_refOutletClassifiers_ClassifierCode ON [dbo].[refOutletClassifiers] ([ClassifierCode]);
CREATE INDEX IX_refOutletClassifiers_Value ON [dbo].[refOutletClassifiers] ([ClassifierValue]);
```

### Таблица справочника классификаторов
```sql
CREATE TABLE [dbo].[refClassifiers] (
    [Id] INT IDENTITY(1,1) PRIMARY KEY,
    [Code] NVARCHAR(50) NOT NULL UNIQUE,
    [Name] NVARCHAR(255) NOT NULL,
    [Description] NVARCHAR(500) NULL,
    [IsActive] BIT NOT NULL DEFAULT 1,
    [CreatedDate] DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);

-- Вставка классификатора "Отправлять на распознавание"
INSERT INTO [dbo].[refClassifiers] ([Code], [Name], [Description])
VALUES ('SEND_FOR_RECOGNITION', 'Отправлять на распознавание', 
        'Классификатор для управления отправкой торговых точек на распознавание адресов');
```

### Таблица торговых точек (расширение)
```sql
-- Добавление поля для быстрого доступа к классификатору
ALTER TABLE [dbo].[refOutlets] 
ADD [SendForRecognition] NVARCHAR(10) NULL;

-- Индекс для производительности
CREATE INDEX IX_refOutlets_SendForRecognition ON [dbo].[refOutlets] ([SendForRecognition]);
```

## Бизнес-логика

### Класс управления классификаторами
```csharp
public class OutletClassifierService
{
    private readonly IDbContext _context;
    private readonly ILogger<OutletClassifierService> _logger;
    
    public async Task<string> GetClassifierValueAsync(int outletId, string classifierCode)
    {
        var classifier = await _context.OutletClassifiers
            .FirstOrDefaultAsync(oc => oc.OutletId == outletId && 
                                      oc.ClassifierCode == classifierCode);
        
        return classifier?.ClassifierValue;
    }
    
    public async Task SetClassifierValueAsync(int outletId, string classifierCode, 
                                            string value, string userId)
    {
        var existing = await _context.OutletClassifiers
            .FirstOrDefaultAsync(oc => oc.OutletId == outletId && 
                                      oc.ClassifierCode == classifierCode);
        
        if (existing != null)
        {
            existing.ClassifierValue = value;
            existing.ModifiedDate = DateTime.UtcNow;
            existing.ModifiedBy = userId;
        }
        else
        {
            var classifier = new OutletClassifier
            {
                OutletId = outletId,
                ClassifierCode = classifierCode,
                ClassifierValue = value,
                CreatedBy = userId,
                ModifiedBy = userId
            };
            _context.OutletClassifiers.Add(classifier);
        }
        
        // Обновляем кэшированное значение в таблице ТТ
        await UpdateOutletCachedValueAsync(outletId, value);
        
        await _context.SaveChangesAsync();
    }
    
    private async Task UpdateOutletCachedValueAsync(int outletId, string value)
    {
        var outlet = await _context.Outlets.FindAsync(outletId);
        if (outlet != null)
        {
            outlet.SendForRecognition = value;
        }
    }
}
```

### Класс сервиса распознавания
```csharp
public class AddressRecognitionService
{
    private readonly OutletClassifierService _classifierService;
    private readonly ILogger<AddressRecognitionService> _logger;
    
    public async Task<bool> ShouldSendForRecognitionAsync(int outletId)
    {
        var classifierValue = await _classifierService
            .GetClassifierValueAsync(outletId, "SEND_FOR_RECOGNITION");
        
        var shouldSend = DetermineRecognitionStatus(classifierValue);
        
        _logger.LogInformation("Outlet {OutletId} with classifier '{Value}' " +
                             "should be sent for recognition: {ShouldSend}", 
                             outletId, classifierValue, shouldSend);
        
        return shouldSend;
    }
    
    private bool DetermineRecognitionStatus(string classifierValue)
    {
        if (string.IsNullOrEmpty(classifierValue))
        {
            // Пустое значение - срабатывает серийный механизм
            return true;
        }
        
        switch (classifierValue)
        {
            case "0":
                // Нейтральный статус - не отправляем
                return false;
            case "1":
                // Отправляем на распознавание
                return true;
            case "2":
                // Не отправляем, сервис игнорирует
                return false;
            default:
                // Неизвестное значение - отправляем по умолчанию
                return true;
        }
    }
    
    public async Task ProcessOutletForRecognitionAsync(int outletId)
    {
        var shouldSend = await ShouldSendForRecognitionAsync(outletId);
        
        if (shouldSend)
        {
            await SendToRecognitionServiceAsync(outletId);
        }
        else
        {
            _logger.LogInformation("Outlet {OutletId} skipped for recognition " +
                                 "due to classifier settings", outletId);
        }
    }
    
    private async Task SendToRecognitionServiceAsync(int outletId)
    {
        // Логика отправки на внешний сервис распознавания
        // ...
    }
}
```

### Класс автоматической смены статусов
```csharp
public class ClassifierStatusManager
{
    private readonly OutletClassifierService _classifierService;
    private readonly ILogger<ClassifierStatusManager> _logger;
    
    public async Task HandleRecognitionResultAsync(int outletId, 
                                                 RecognitionResult result)
    {
        var currentValue = await _classifierService
            .GetClassifierValueAsync(outletId, "SEND_FOR_RECOGNITION");
        
        if (currentValue != "1")
        {
            // Статус не "1" - не обрабатываем
            return;
        }
        
        string newValue;
        switch (result.Status)
        {
            case RecognitionStatus.Success:
                // Успешное распознавание - переводим в "2"
                newValue = "2";
                break;
            case RecognitionStatus.RequiresDistributorCheck:
            case RecognitionStatus.RequiresCheck:
                // Неудачное распознавание - переводим в "0"
                newValue = "0";
                break;
            default:
                // Оставляем текущий статус
                return;
        }
        
        await _classifierService.SetClassifierValueAsync(
            outletId, "SEND_FOR_RECOGNITION", newValue, "SYSTEM");
        
        _logger.LogInformation("Outlet {OutletId} classifier changed from '1' to '{NewValue}' " +
                             "due to recognition result: {Result}", 
                             outletId, newValue, result.Status);
    }
}
```

## API для управления классификаторами

### Контроллер классификаторов
```csharp
[ApiController]
[Route("api/outlets/{outletId}/classifiers")]
public class OutletClassifiersController : ControllerBase
{
    private readonly OutletClassifierService _classifierService;
    
    [HttpGet("{classifierCode}")]
    public async Task<ActionResult<string>> GetClassifierValue(
        int outletId, string classifierCode)
    {
        var value = await _classifierService
            .GetClassifierValueAsync(outletId, classifierCode);
        
        return Ok(new { Value = value });
    }
    
    [HttpPut("{classifierCode}")]
    public async Task<ActionResult> SetClassifierValue(
        int outletId, string classifierCode, 
        [FromBody] SetClassifierRequest request)
    {
        await _classifierService.SetClassifierValueAsync(
            outletId, classifierCode, request.Value, 
            User.Identity.Name);
        
        return Ok();
    }
    
    [HttpGet]
    public async Task<ActionResult<IEnumerable<ClassifierInfo>>> GetClassifiers(
        int outletId)
    {
        var classifiers = await _classifierService
            .GetAllClassifiersAsync(outletId);
        
        return Ok(classifiers);
    }
}

public class SetClassifierRequest
{
    public string Value { get; set; }
}

public class ClassifierInfo
{
    public string Code { get; set; }
    public string Name { get; set; }
    public string Value { get; set; }
    public DateTime? ModifiedDate { get; set; }
    public string ModifiedBy { get; set; }
}
```

## Интеграция с существующими процессами

### Обработка создания ТТ
```csharp
public class OutletCreationService
{
    private readonly OutletClassifierService _classifierService;
    
    public async Task<Outlet> CreateOutletAsync(CreateOutletRequest request)
    {
        var outlet = new Outlet
        {
            Name = request.Name,
            Address = request.Address,
            // ... другие поля
        };
        
        _context.Outlets.Add(outlet);
        await _context.SaveChangesAsync();
        
        // Устанавливаем классификатор по умолчанию
        var defaultClassifierValue = request.SendForRecognition ?? "0";
        await _classifierService.SetClassifierValueAsync(
            outlet.Id, "SEND_FOR_RECOGNITION", 
            defaultClassifierValue, request.CreatedBy);
        
        return outlet;
    }
}
```

### Обработка импорта из Excel
```csharp
public class ExcelImportService
{
    private readonly OutletClassifierService _classifierService;
    
    public async Task ImportOutletsFromExcelAsync(Stream excelStream, string userId)
    {
        var outlets = ParseExcelFile(excelStream);
        
        foreach (var outletData in outlets)
        {
            var outlet = await CreateOutletFromExcelDataAsync(outletData);
            
            // Устанавливаем классификатор из Excel или по умолчанию
            var classifierValue = outletData.SendForRecognition ?? "0";
            await _classifierService.SetClassifierValueAsync(
                outlet.Id, "SEND_FOR_RECOGNITION", 
                classifierValue, userId);
        }
    }
}
```

### Обработка импорта из УС дистрибьютора
```csharp
public class DistributorImportService
{
    private readonly OutletClassifierService _classifierService;
    
    public async Task ImportFromDistributorAsync(DistributorData data, string userId)
    {
        foreach (var outletData in data.Outlets)
        {
            var outlet = await ProcessOutletFromDistributorAsync(outletData);
            
            // Все ТТ от дистрибьютора получают статус "0"
            await _classifierService.SetClassifierValueAsync(
                outlet.Id, "SEND_FOR_RECOGNITION", "0", userId);
        }
    }
}
```

## Конфигурация системы

### Настройки классификатора
```json
{
  "classifiers": {
    "sendForRecognition": {
      "code": "SEND_FOR_RECOGNITION",
      "name": "Отправлять на распознавание",
      "defaultValue": "0",
      "allowedValues": ["0", "1", "2"],
      "descriptions": {
        "0": "Нейтральный статус - не отправлять на распознавание",
        "1": "Отправлять на распознавание",
        "2": "Не отправлять - сервис игнорирует"
      }
    }
  }
}
```

### Настройки сервиса РиГ
```json
{
  "recognitionService": {
    "enabled": true,
    "checkClassifier": true,
    "classifierCode": "SEND_FOR_RECOGNITION",
    "autoStatusChange": true,
    "logLevel": "Information"
  }
}
```

## Производительность и масштабируемость

### Оптимизации
1. **Кэширование**: Кэширование значений классификаторов
2. **Индексы**: Оптимизированные индексы для быстрого поиска
3. **Пакетная обработка**: Группировка операций с классификаторами
4. **Асинхронность**: Асинхронная обработка запросов

### Мониторинг производительности
```csharp
public class ClassifierMetrics
{
    public int TotalClassifiers { get; set; }
    public int ClassifiersWithValue0 { get; set; }
    public int ClassifiersWithValue1 { get; set; }
    public int ClassifiersWithValue2 { get; set; }
    public int EmptyClassifiers { get; set; }
    public TimeSpan AverageProcessingTime { get; set; }
    
    public void RecordClassifierUpdate(string oldValue, string newValue, 
                                     TimeSpan processingTime)
    {
        // Обновление метрик
        AverageProcessingTime = CalculateAverage(processingTime);
    }
}
```

## Безопасность

### Валидация данных
```csharp
public class ClassifierValidator
{
    private static readonly string[] AllowedValues = { "0", "1", "2" };
    
    public ValidationResult ValidateClassifierValue(string value)
    {
        var result = new ValidationResult();
        
        if (!string.IsNullOrEmpty(value) && !AllowedValues.Contains(value))
        {
            result.AddError($"Недопустимое значение классификатора: {value}. " +
                          $"Разрешены только: {string.Join(", ", AllowedValues)}");
        }
        
        return result;
    }
}
```

### Аудит операций
```csharp
public class ClassifierAuditService
{
    public async Task LogClassifierChangeAsync(int outletId, string classifierCode,
                                             string oldValue, string newValue, 
                                             string userId)
    {
        var auditEntry = new ClassifierAuditEntry
        {
            OutletId = outletId,
            ClassifierCode = classifierCode,
            OldValue = oldValue,
            NewValue = newValue,
            UserId = userId,
            Timestamp = DateTime.UtcNow,
            Action = "UPDATE"
        };
        
        await _auditService.LogAsync(auditEntry);
    }
}
```

## Заключение

### Реализованные возможности
- ✅ Классификатор "Отправлять на распознавание" с тремя значениями
- ✅ Логика обработки статусов в сервисе РиГ
- ✅ Автоматическая смена статусов после распознавания
- ✅ Интеграция с процессами создания и импорта ТТ
- ✅ API для управления классификаторами
- ✅ Аудит и мониторинг операций

### Технические преимущества
- **Гибкость**: Возможность управления распознаванием для каждой ТТ
- **Производительность**: Оптимизированная обработка с кэшированием
- **Масштабируемость**: Поддержка большого количества ТТ
- **Надежность**: Валидация и обработка ошибок

### Следующие шаги
1. **Пилотное тестирование**: Запуск на ограниченной группе ТТ
2. **Мониторинг**: Отслеживание производительности и использования
3. **Оптимизация**: Улучшение на основе обратной связи
4. **Расширение**: Добавление новых типов классификаторов при необходимости

---
*Документ создан: 27.09.2025*  
*Версия: 1.0*  
*Статус: Реализовано*
