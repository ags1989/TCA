# Техническое решение: РУСТ. Разворачивание интеграции с ОСА Магнит

## Обзор решения

### Цель
Развернуть стандартную интеграцию с OSA Магнит на проекте РУСТ для обеспечения автоматизированного взаимодействия с сетью "Магнит" через API.

### Архитектура системы
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   РУСТ Система  │◄──►│  OSA Магнит API │    │   Мобильный     │
│                 │    │                 │    │   терминал      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
   Обработка сигналов      Получение/отправка      Отображение
   и данных               данных через API         данных
```

## Компоненты решения

### 1. OSA.MagnitPlugin

#### Назначение
Стандартный плагин для интеграции с OSA Магнит, обеспечивающий:
- Получение сигналов от Магнит
- Отправку графиков работы мерчандайзеров
- Отправку ответов на сигналы
- Загрузку справочников проблем

#### Конфигурация
```yaml
# ansible/vars/ROUST/ST-HOUSTON/OSA.MagnitPlugin.yml
osa_magnit_plugin:
  enabled: true
  api_version: "v2"
  base_url: "https://api.magnet.ru/osa/v2/"
  timeout: 30000
  retry_attempts: 3
  certificate_path: "/certs/magnet_client.p12"
  certificate_password: "encrypted_password"
```

### 2. Функциональные флаги

#### Включение интеграции
```sql
-- Включение флагов для РУСТ
UPDATE FeatureFlags 
SET IsEnabled = 1 
WHERE FlagName IN ('UseMagnitApiClientV2', 'UseMagnitSignalsByApi')
AND ProjectId = 'ROUST';
```

#### Проверка статуса
```sql
-- Проверка статуса функциональных флагов
SELECT FlagName, IsEnabled, ProjectId 
FROM FeatureFlags 
WHERE FlagName IN ('UseMagnitApiClientV2', 'UseMagnitSignalsByApi')
AND ProjectId = 'ROUST';
```

### 3. База данных

#### Таблица кодов товаров
```sql
-- Таблица для сопоставления кодов товаров
CREATE TABLE osa.ProductCodes (
    id INT IDENTITY(1,1) PRIMARY KEY,
    product_code NVARCHAR(50) NOT NULL,  -- Код от Магнит
    chicago_code NVARCHAR(50) NOT NULL,  -- Код в БД Чикаго
    product_name NVARCHAR(255),
    is_active BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);

-- Индексы для производительности
CREATE INDEX IX_osa_ProductCodes_product_code ON osa.ProductCodes(product_code);
CREATE INDEX IX_osa_ProductCodes_chicago_code ON osa.ProductCodes(chicago_code);
```

#### Таблица сигналов
```sql
-- Таблица для хранения сигналов от Магнит
CREATE TABLE osa.MagnitSignals (
    id INT IDENTITY(1,1) PRIMARY KEY,
    signal_id NVARCHAR(50) NOT NULL,
    outlet_code NVARCHAR(50),
    sku_code NVARCHAR(50),
    signal_type NVARCHAR(50),
    description NVARCHAR(MAX),
    priority NVARCHAR(20),
    status NVARCHAR(20) DEFAULT 'pending',
    created_at DATETIME2,
    processed_at DATETIME2,
    ImportDate DATETIME2 DEFAULT GETDATE()
);

-- Индексы для производительности
CREATE INDEX IX_osa_MagnitSignals_signal_id ON osa.MagnitSignals(signal_id);
CREATE INDEX IX_osa_MagnitSignals_outlet_code ON osa.MagnitSignals(outlet_code);
CREATE INDEX IX_osa_MagnitSignals_status ON osa.MagnitSignals(status);
```

### 4. Дополнительные атрибуты

#### Код ТТ Магнит
```sql
-- Создание дополнительного атрибута для кодов ТТ Магнит
INSERT INTO refAttributesBase (
    Code, Name, Description, idBaseObject, 
    DataType, IsRequired, IsSystem, Deleted
) VALUES (
    'MagnitOutletCode', 
    'Код ТТ Магнит', 
    'Код торговой точки в системе Магнит',
    10, -- refOutlets
    1,  -- String
    0,  -- Not required
    0,  -- Not system
    0   -- Not deleted
);
```

#### Атрибуты для промо-данных
```sql
-- Тип ценника
INSERT INTO refAttributesBase (Code, Name, Description, idBaseObject, DataType, IsRequired, IsSystem, Deleted)
VALUES ('PriceTagType', 'Тип ценника', 'Тип ценника от Магнит', 5, 1, 0, 0, 0);

-- Дата смены ценника
INSERT INTO refAttributesBase (Code, Name, Description, idBaseObject, DataType, IsRequired, IsSystem, Deleted)
VALUES ('PriceTagChangeDate', 'Дата смены ценника', 'Дата смены ценника от Магнит', 5, 3, 0, 0, 0);

-- Цена Магнит
INSERT INTO refAttributesBase (Code, Name, Description, idBaseObject, DataType, IsRequired, IsSystem, Deleted)
VALUES ('MagnitPrice', 'Цена (Магнит)', 'Цена товара от Магнит', 5, 2, 0, 0, 0);
```

### 5. Импорт данных

#### Сводный отчет "Импорт ProductCodes"
```sql
-- Процедура для импорта кодов товаров
CREATE PROCEDURE sp_ImportProductCodes
    @ProductCode NVARCHAR(50),
    @ChicagoCode NVARCHAR(50),
    @ProductName NVARCHAR(255) = NULL
AS
BEGIN
    -- Проверка существования записи
    IF EXISTS (SELECT 1 FROM osa.ProductCodes WHERE product_code = @ProductCode)
    BEGIN
        -- Обновление существующей записи
        UPDATE osa.ProductCodes 
        SET chicago_code = @ChicagoCode,
            product_name = ISNULL(@ProductName, product_name),
            updated_at = GETDATE()
        WHERE product_code = @ProductCode;
    END
    ELSE
    BEGIN
        -- Создание новой записи
        INSERT INTO osa.ProductCodes (product_code, chicago_code, product_name)
        VALUES (@ProductCode, @ChicagoCode, @ProductName);
    END
END;
```

#### Серийный импорт ТТ
```sql
-- Процедура для обновления кодов ТТ Магнит
CREATE PROCEDURE sp_UpdateMagnitOutletCodes
    @OutletId INT,
    @MagnitCode NVARCHAR(50)
AS
BEGIN
    -- Обновление или создание значения атрибута
    IF EXISTS (SELECT 1 FROM refAttributesValues WHERE idElement = @OutletId AND idAttribute = @MagnitOutletCodeAttributeId)
    BEGIN
        UPDATE refAttributesValues 
        SET Value = @MagnitCode,
            UpdatedDate = GETDATE()
        WHERE idElement = @OutletId AND idAttribute = @MagnitOutletCodeAttributeId;
    END
    ELSE
    BEGIN
        INSERT INTO refAttributesValues (idElement, idAttribute, Value, CreatedDate, UpdatedDate, Deleted)
        VALUES (@OutletId, @MagnitOutletCodeAttributeId, @MagnitCode, GETDATE(), GETDATE(), 0);
    END
END;
```

### 6. API интеграция

#### Получение сигналов
```csharp
public class MagnitSignalsService
{
    public async Task<List<MagnitSignal>> GetSignalsAsync()
    {
        var client = new HttpClient();
        client.DefaultRequestHeaders.Authorization = 
            new AuthenticationHeaderValue("Bearer", await GetAccessTokenAsync());
        
        var response = await client.GetAsync($"{_baseUrl}/signals");
        var content = await response.Content.ReadAsStringAsync();
        
        return JsonSerializer.Deserialize<List<MagnitSignal>>(content);
    }
}
```

#### Отправка графиков
```csharp
public class MagnitSchedulesService
{
    public async Task<bool> SendScheduleAsync(ScheduleData schedule)
    {
        var client = new HttpClient();
        client.DefaultRequestHeaders.Authorization = 
            new AuthenticationHeaderValue("Bearer", await GetAccessTokenAsync());
        
        var json = JsonSerializer.Serialize(schedule);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        var response = await client.PostAsync($"{_baseUrl}/schedules", content);
        return response.IsSuccessStatusCode;
    }
}
```

### 7. Формирование договоров

#### Алгоритм поиска договора
```csharp
public class AgreementService
{
    public Agreement FindOrCreateAgreement(int outletId, int distributorId)
    {
        // Поиск существующего договора
        var existingAgreement = FindExistingAgreement(outletId, distributorId);
        
        if (existingAgreement != null)
        {
            return existingAgreement;
        }
        
        // Создание нового договора
        return CreateNewAgreement(outletId, distributorId);
    }
    
    private Agreement FindExistingAgreement(int outletId, int distributorId)
    {
        // Поиск по торговой точке
        var outletAgreements = GetAgreementsByOutlet(outletId);
        if (outletAgreements.Count == 1)
        {
            return outletAgreements.First();
        }
        
        // Поиск по дистрибьютору
        var distributorAgreements = GetAgreementsByDistributor(distributorId);
        if (distributorAgreements.Count == 1)
        {
            return distributorAgreements.First();
        }
        
        // Если найдено несколько договоров - ошибка
        if (outletAgreements.Count > 1 || distributorAgreements.Count > 1)
        {
            throw new InvalidOperationException(
                "Не удалось обновить договор на ТТ, т.к. найдено несколько договоров с загружаемой ТТ");
        }
        
        return null;
    }
}
```

### 8. Расписание джобов

#### Настройка расписания
```xml
<!-- Конфигурация расписания для ежедневного выполнения -->
<ScheduleConfig>
    <Job Name="MagnitSignalsImport">
        <Schedule>0 0 6 * * ?</Schedule> <!-- Ежедневно в 6:00 -->
        <Enabled>true</Enabled>
    </Job>
    
    <Job Name="MagnitSchedulesExport">
        <Schedule>0 0 8 * * ?</Schedule> <!-- Ежедневно в 8:00 -->
        <Enabled>true</Enabled>
    </Job>
    
    <Job Name="MagnitFeedbackExport">
        <Schedule>0 0 18 * * ?</Schedule> <!-- Ежедневно в 18:00 -->
        <Enabled>true</Enabled>
    </Job>
</ScheduleConfig>
```

### 9. Мобильный терминал

#### Отображение сигналов
```csharp
public class MerchandisingController
{
    public ActionResult ShowMagnitSignals(int outletId)
    {
        // Проверка наличия сигналов для ТТ
        var hasSignals = _signalsService.HasSignalsForOutlet(outletId);
        
        if (!hasSignals)
        {
            return View("NoSignals");
        }
        
        // Получение сигналов для ТТ
        var signals = _signalsService.GetSignalsForOutlet(outletId);
        
        return View("MagnitSignals", signals);
    }
}
```

#### Валидация при закрытии визита
```csharp
public class VisitValidationService
{
    public ValidationResult ValidateVisitClosing(int visitId)
    {
        var result = new ValidationResult();
        
        // Проверка заполнения всех сигналов
        var unprocessedSignals = _signalsService.GetUnprocessedSignals(visitId);
        
        if (unprocessedSignals.Any())
        {
            result.AddError("Не все сигналы Магнит обработаны. " +
                           "Пожалуйста, заполните ответы на все сигналы перед закрытием визита.");
        }
        
        return result;
    }
}
```

### 10. Уведомления

#### Отправка уведомлений на почту
```csharp
public class NotificationService
{
    public async Task SendMissingSignalsNotificationAsync(List<ScheduleData> schedules)
    {
        var missingSignals = new List<ScheduleData>();
        
        foreach (var schedule in schedules)
        {
            var signals = await _signalsService.GetSignalsForSchedule(schedule);
            if (!signals.Any())
            {
                missingSignals.Add(schedule);
            }
        }
        
        if (missingSignals.Any())
        {
            await _emailService.SendAsync(
                "admin@rust.ru",
                "Отсутствие сигналов по отправленным графикам",
                GenerateMissingSignalsReport(missingSignals)
            );
        }
    }
}
```

## Алгоритм работы

### 1. Инициализация системы
1. Подключение плагина OSA.MagnitPlugin
2. Включение функциональных флагов
3. Настройка API подключения
4. Загрузка кодов товаров и ТТ

### 2. Получение сигналов
1. Ежедневный запуск джоба в 6:00
2. Получение сигналов от API Магнит
3. Сохранение в таблицу osa.MagnitSignals
4. Формирование/обновление договоров
5. Синхронизация с мобильными терминалами

### 3. Отправка графиков
1. Ежедневный запуск джоба в 8:00
2. Формирование графиков работы мерчандайзеров
3. Отправка через API Магнит
4. Логирование результатов

### 4. Обработка в МТ
1. Отображение сигналов для ТТ Магнит
2. Заполнение ответов мерчандайзерами
3. Валидация при закрытии визита
4. Сохранение ответов

### 5. Отправка ответов
1. Ежедневный запуск джоба в 18:00
2. Получение ответов от мерчандайзеров
3. Отправка через API Магнит
4. Обновление статусов сигналов

## Конфигурация

### Настройки плагина
```json
{
  "osa_magnit_plugin": {
    "enabled": true,
    "api_version": "v2",
    "base_url": "https://api.magnet.ru/osa/v2/",
    "timeout": 30000,
    "retry_attempts": 3,
    "certificate_path": "/certs/magnet_client.p12",
    "certificate_password": "encrypted_password",
    "client_id": "rust_client_id",
    "client_secret": "encrypted_client_secret"
  }
}
```

### Настройки расписания
```json
{
  "schedules": {
    "signals_import": {
      "enabled": true,
      "cron": "0 0 6 * * ?",
      "timeout": 300000
    },
    "schedules_export": {
      "enabled": true,
      "cron": "0 0 8 * * ?",
      "timeout": 300000
    },
    "feedback_export": {
      "enabled": true,
      "cron": "0 0 18 * * ?",
      "timeout": 300000
    }
  }
}
```

### Настройки уведомлений
```json
{
  "notifications": {
    "email_enabled": true,
    "smtp_server": "smtp.rust.ru",
    "smtp_port": 587,
    "smtp_username": "noreply@rust.ru",
    "smtp_password": "encrypted_password",
    "recipients": ["admin@rust.ru", "support@rust.ru"],
    "missing_signals_check": true
  }
}
```

## Мониторинг и логирование

### Метрики для отслеживания
- **Количество полученных сигналов**: В день, в час
- **Время обработки**: Среднее время от получения до ответа
- **Успешность отправки**: Процент успешных отправок графиков и ответов
- **Ошибки API**: Количество и типы ошибок
- **Формирование договоров**: Количество созданных/обновленных договоров

### Логирование
```csharp
public class MagnitIntegrationLogger
{
    public void LogSignalProcessing(string signalId, string outletCode, TimeSpan duration)
    {
        var logEntry = new
        {
            Timestamp = DateTime.UtcNow,
            SignalId = signalId,
            OutletCode = outletCode,
            Duration = duration.TotalMilliseconds,
            Status = "Processed"
        };
        
        _logger.LogInformation("Signal processed: {LogEntry}", JsonSerializer.Serialize(logEntry));
    }
}
```

## Тестирование

### Автоматические тесты
1. **Unit тесты**: Тестирование отдельных компонентов
2. **Integration тесты**: Тестирование взаимодействия с API
3. **E2E тесты**: Полный цикл от получения до отправки
4. **Performance тесты**: Нагрузочное тестирование

### Тестовые сценарии
1. **US1**: Работа с проблемами товаров
2. **US2**: Работа с проблемами магазинов
3. **US3**: Получение промо от Магнит
4. **US4**: Получение ассортиментных матриц

## Развертывание

### Требования к окружению
- **.NET Framework**: 4.7.2 или выше
- **SQL Server**: 2016 или выше
- **Сертификаты**: X.509 сертификаты для аутентификации
- **Сеть**: Доступ к API OSA Магнит

### Этапы развертывания
1. **Подготовка**: Создание файла конфигурации деплоя
2. **Настройка**: Включение функциональных флагов
3. **Импорт данных**: Загрузка кодов товаров и ТТ
4. **Тестирование**: Проверка работы на Development/UAT
5. **Запуск**: Включение интеграции на Production

## Безопасность

### Защита данных
- **Шифрование**: Все данные передаются по HTTPS
- **Сертификаты**: Двусторонняя аутентификация
- **Токены**: Временные access_token с ограниченным сроком действия
- **Логирование**: Безопасное логирование без чувствительных данных

### Аудит
- **Логи доступа**: Все обращения к API логируются
- **Мониторинг**: Отслеживание подозрительной активности
- **Резервное копирование**: Регулярное создание резервных копий

---
*Документ создан: 27.09.2025*  
*Версия: 1.0*  
*Статус: Готов к реализации*
