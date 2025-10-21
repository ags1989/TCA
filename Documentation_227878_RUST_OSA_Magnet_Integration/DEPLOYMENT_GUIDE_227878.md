# Руководство по развертыванию: РУСТ. Разворачивание интеграции с ОСА Магнит

## Обзор развертывания

### Цель
Обеспечить корректное развертывание интеграции с OSA Магнит на проекте РУСТ в производственной среде.

### Компоненты для развертывания
1. **OSA.MagnitPlugin** - основной плагин интеграции
2. **Функциональные флаги** - включение поддержки API
3. **База данных** - создание таблиц и импорт данных
4. **Дополнительные атрибуты** - настройка атрибутов для кодов ТТ
5. **Расписание джобов** - настройка автоматических задач

## Предварительные требования

### Системные требования
- **.NET Framework**: 4.7.2 или выше
- **SQL Server**: 2016 или выше
- **Память**: Минимум 8 GB RAM
- **Дисковое пространство**: 20 GB свободного места
- **Сеть**: Доступ к API OSA Магнит

### Доступы и права
- **Администратор БД**: Для создания таблиц и импорта данных
- **Администратор серверов**: Для настройки плагина
- **Администратор МТ**: Для обновления мобильных терминалов
- **API доступ**: Доступ к тестовому и продакшн API

### Резервное копирование
- Создать полную резервную копию БД
- Сохранить текущие конфигурации
- Создать точку восстановления системы
- Сохранить текущие функциональные флаги

## Этапы развертывания

### Этап 1: Создание файла конфигурации деплоя

#### 1.1 Создание файла конфигурации
Создать файл: `ansible/vars/ROUST/ST-HOUSTON/OSA.MagnitPlugin.yml`

```yaml
# Конфигурация OSA.MagnitPlugin для РУСТ
osa_magnit_plugin:
  enabled: true
  project_name: "ROUST"
  api_version: "v2"
  base_url: "https://api.magnet.ru/osa/v2/"
  timeout: 30000
  retry_attempts: 3
  certificate_path: "/certs/rust_magnet_client.p12"
  certificate_password: "encrypted_password"
  client_id: "rust_client_id"
  client_secret: "encrypted_client_secret"
  
  # Настройки расписания
  schedules:
    signals_import:
      enabled: true
      cron: "0 0 6 * * ?"  # Ежедневно в 6:00
      timeout: 300000
    schedules_export:
      enabled: true
      cron: "0 0 8 * * ?"  # Ежедневно в 8:00
      timeout: 300000
    feedback_export:
      enabled: true
      cron: "0 0 18 * * ?"  # Ежедневно в 18:00
      timeout: 300000
  
  # Настройки уведомлений
  notifications:
    email_enabled: true
    smtp_server: "smtp.rust.ru"
    smtp_port: 587
    smtp_username: "noreply@rust.ru"
    smtp_password: "encrypted_password"
    recipients: ["admin@rust.ru", "support@rust.ru"]
    missing_signals_check: true
```

#### 1.2 Проверка конфигурации
```bash
# Проверка синтаксиса YAML
yamllint ansible/vars/ROUST/ST-HOUSTON/OSA.MagnitPlugin.yml

# Проверка доступности сертификатов
ls -la /certs/rust_magnet_client.p12
```

### Этап 2: Включение функциональных флагов

#### 2.1 Включение флагов в БД
```sql
-- Включение функциональных флагов для РУСТ
UPDATE FeatureFlags 
SET IsEnabled = 1, 
    UpdatedDate = GETDATE()
WHERE FlagName IN ('UseMagnitApiClientV2', 'UseMagnitSignalsByApi')
  AND ProjectId = 'ROUST';

-- Если флаги не существуют, создать их
INSERT INTO FeatureFlags (FlagName, IsEnabled, ProjectId, CreatedDate, UpdatedDate, Deleted)
SELECT 'UseMagnitApiClientV2', 1, 'ROUST', GETDATE(), GETDATE(), 0
WHERE NOT EXISTS (SELECT 1 FROM FeatureFlags WHERE FlagName = 'UseMagnitApiClientV2' AND ProjectId = 'ROUST');

INSERT INTO FeatureFlags (FlagName, IsEnabled, ProjectId, CreatedDate, UpdatedDate, Deleted)
SELECT 'UseMagnitSignalsByApi', 1, 'ROUST', GETDATE(), GETDATE(), 0
WHERE NOT EXISTS (SELECT 1 FROM FeatureFlags WHERE FlagName = 'UseMagnitSignalsByApi' AND ProjectId = 'ROUST');
```

#### 2.2 Проверка включения флагов
```sql
-- Проверка статуса функциональных флагов
SELECT FlagName, IsEnabled, ProjectId, UpdatedDate
FROM FeatureFlags 
WHERE FlagName IN ('UseMagnitApiClientV2', 'UseMagnitSignalsByApi')
  AND ProjectId = 'ROUST';
```

### Этап 3: Создание таблиц БД

#### 3.1 Создание таблицы кодов товаров
```sql
-- Создание таблицы для сопоставления кодов товаров
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[osa].[ProductCodes]') AND type in (N'U'))
BEGIN
    CREATE TABLE [osa].[ProductCodes] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [product_code] NVARCHAR(50) NOT NULL,
        [chicago_code] NVARCHAR(50) NOT NULL,
        [product_name] NVARCHAR(255),
        [is_active] BIT DEFAULT 1,
        [created_at] DATETIME2 DEFAULT GETDATE(),
        [updated_at] DATETIME2 DEFAULT GETDATE()
    );
    
    -- Создание индексов
    CREATE INDEX IX_osa_ProductCodes_product_code ON [osa].[ProductCodes](product_code);
    CREATE INDEX IX_osa_ProductCodes_chicago_code ON [osa].[ProductCodes](chicago_code);
    CREATE INDEX IX_osa_ProductCodes_is_active ON [osa].[ProductCodes](is_active);
END
```

#### 3.2 Создание таблицы сигналов
```sql
-- Создание таблицы для хранения сигналов от Магнит
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[osa].[MagnitSignals]') AND type in (N'U'))
BEGIN
    CREATE TABLE [osa].[MagnitSignals] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [signal_id] NVARCHAR(50) NOT NULL,
        [outlet_code] NVARCHAR(50),
        [sku_code] NVARCHAR(50),
        [signal_type] NVARCHAR(50),
        [description] NVARCHAR(MAX),
        [priority] NVARCHAR(20),
        [status] NVARCHAR(20) DEFAULT 'pending',
        [created_at] DATETIME2,
        [processed_at] DATETIME2,
        [ImportDate] DATETIME2 DEFAULT GETDATE()
    );
    
    -- Создание индексов
    CREATE INDEX IX_osa_MagnitSignals_signal_id ON [osa].[MagnitSignals](signal_id);
    CREATE INDEX IX_osa_MagnitSignals_outlet_code ON [osa].[MagnitSignals](outlet_code);
    CREATE INDEX IX_osa_MagnitSignals_status ON [osa].[MagnitSignals](status);
    CREATE INDEX IX_osa_MagnitSignals_ImportDate ON [osa].[MagnitSignals](ImportDate);
END
```

#### 3.3 Создание хранимых процедур
```sql
-- Процедура для импорта кодов товаров
CREATE OR ALTER PROCEDURE [osa].[sp_ImportProductCodes]
    @ProductCode NVARCHAR(50),
    @ChicagoCode NVARCHAR(50),
    @ProductName NVARCHAR(255) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- Проверка существования записи
        IF EXISTS (SELECT 1 FROM [osa].[ProductCodes] WHERE product_code = @ProductCode)
        BEGIN
            -- Обновление существующей записи
            UPDATE [osa].[ProductCodes] 
            SET chicago_code = @ChicagoCode,
                product_name = ISNULL(@ProductName, product_name),
                updated_at = GETDATE()
            WHERE product_code = @ProductCode;
        END
        ELSE
        BEGIN
            -- Создание новой записи
            INSERT INTO [osa].[ProductCodes] (product_code, chicago_code, product_name)
            VALUES (@ProductCode, @ChicagoCode, @ProductName);
        END
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END;
```

### Этап 4: Создание дополнительных атрибутов

#### 4.1 Создание атрибута "Код ТТ Магнит"
```sql
-- Создание дополнительного атрибута для кодов ТТ Магнит
DECLARE @AttributeId INT;

-- Проверка существования атрибута
SELECT @AttributeId = id FROM refAttributesBase 
WHERE Code = 'MagnitOutletCode' AND idBaseObject = 10 AND Deleted = 0;

IF @AttributeId IS NULL
BEGIN
    INSERT INTO refAttributesBase (
        Code, Name, Description, idBaseObject, 
        DataType, IsRequired, IsSystem, Deleted, CreatedDate, UpdatedDate
    ) VALUES (
        'MagnitOutletCode', 
        'Код ТТ Магнит', 
        'Код торговой точки в системе Магнит',
        10, -- refOutlets
        1,  -- String
        0,  -- Not required
        0,  -- Not system
        0,  -- Not deleted
        GETDATE(),
        GETDATE()
    );
    
    SET @AttributeId = SCOPE_IDENTITY();
END

PRINT 'Attribute ID: ' + CAST(@AttributeId AS VARCHAR(10));
```

#### 4.2 Создание атрибутов для промо-данных
```sql
-- Тип ценника
IF NOT EXISTS (SELECT 1 FROM refAttributesBase WHERE Code = 'PriceTagType' AND idBaseObject = 5)
BEGIN
    INSERT INTO refAttributesBase (Code, Name, Description, idBaseObject, DataType, IsRequired, IsSystem, Deleted, CreatedDate, UpdatedDate)
    VALUES ('PriceTagType', 'Тип ценника', 'Тип ценника от Магнит', 5, 1, 0, 0, 0, GETDATE(), GETDATE());
END

-- Дата смены ценника
IF NOT EXISTS (SELECT 1 FROM refAttributesBase WHERE Code = 'PriceTagChangeDate' AND idBaseObject = 5)
BEGIN
    INSERT INTO refAttributesBase (Code, Name, Description, idBaseObject, DataType, IsRequired, IsSystem, Deleted, CreatedDate, UpdatedDate)
    VALUES ('PriceTagChangeDate', 'Дата смены ценника', 'Дата смены ценника от Магнит', 5, 3, 0, 0, 0, GETDATE(), GETDATE());
END

-- Цена Магнит
IF NOT EXISTS (SELECT 1 FROM refAttributesBase WHERE Code = 'MagnitPrice' AND idBaseObject = 5)
BEGIN
    INSERT INTO refAttributesBase (Code, Name, Description, idBaseObject, DataType, IsRequired, IsSystem, Deleted, CreatedDate, UpdatedDate)
    VALUES ('MagnitPrice', 'Цена (Магнит)', 'Цена товара от Магнит', 5, 2, 0, 0, 0, GETDATE(), GETDATE());
END
```

### Этап 5: Импорт данных

#### 5.1 Импорт кодов товаров
```sql
-- Пример импорта кодов товаров через сводный отчет
-- Использовать отчет "Импорт ProductCodes" в системе

-- Ручной импорт для тестирования
EXEC [osa].[sp_ImportProductCodes] 'MAG001', 'CHI001', 'Товар 1';
EXEC [osa].[sp_ImportProductCodes] 'MAG002', 'CHI002', 'Товар 2';
EXEC [osa].[sp_ImportProductCodes] 'MAG003', 'CHI003', 'Товар 3';

-- Проверка импортированных данных
SELECT * FROM [osa].[ProductCodes] ORDER BY created_at DESC;
```

#### 5.2 Импорт кодов ТТ
```sql
-- Процедура для обновления кодов ТТ Магнит
CREATE OR ALTER PROCEDURE [osa].[sp_UpdateMagnitOutletCodes]
    @OutletId INT,
    @MagnitCode NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @AttributeId INT;
    SELECT @AttributeId = id FROM refAttributesBase 
    WHERE Code = 'MagnitOutletCode' AND idBaseObject = 10 AND Deleted = 0;
    
    IF @AttributeId IS NULL
    BEGIN
        RAISERROR('Attribute MagnitOutletCode not found', 16, 1);
        RETURN;
    END
    
    -- Обновление или создание значения атрибута
    IF EXISTS (SELECT 1 FROM refAttributesValues WHERE idElement = @OutletId AND idAttribute = @AttributeId AND Deleted = 0)
    BEGIN
        UPDATE refAttributesValues 
        SET Value = @MagnitCode,
            UpdatedDate = GETDATE()
        WHERE idElement = @OutletId AND idAttribute = @AttributeId AND Deleted = 0;
    END
    ELSE
    BEGIN
        INSERT INTO refAttributesValues (idElement, idAttribute, Value, CreatedDate, UpdatedDate, Deleted)
        VALUES (@OutletId, @AttributeId, @MagnitCode, GETDATE(), GETDATE(), 0);
    END
END;

-- Пример использования
EXEC [osa].[sp_UpdateMagnitOutletCodes] 12345, 'MAG_TT_001';
EXEC [osa].[sp_UpdateMagnitOutletCodes] 12346, 'MAG_TT_002';

-- Проверка обновленных данных
SELECT o.Code, o.Name, av.Value as MagnitCode
FROM refOutlets o
LEFT JOIN refAttributesValues av ON o.id = av.idElement AND av.Deleted = 0
LEFT JOIN refAttributesBase ab ON av.idAttribute = ab.id AND ab.Code = 'MagnitOutletCode'
WHERE o.Deleted = 0;
```

### Этап 6: Настройка расписания джобов

#### 6.1 Создание джобов
```sql
-- Создание джоба для импорта сигналов
IF NOT EXISTS (SELECT 1 FROM sysjobs WHERE name = 'MagnitSignalsImport')
BEGIN
    EXEC dbo.sp_add_job
        @job_name = 'MagnitSignalsImport',
        @enabled = 1,
        @description = 'Импорт сигналов от Магнит';
    
    EXEC dbo.sp_add_jobstep
        @job_name = 'MagnitSignalsImport',
        @step_name = 'ImportSignals',
        @command = 'EXEC [osa].[up_ImportSignals]',
        @database_name = 'Houston';
    
    EXEC dbo.sp_add_schedule
        @schedule_name = 'MagnitSignalsImportSchedule',
        @freq_type = 4, -- Daily
        @freq_interval = 1,
        @active_start_time = 060000; -- 6:00 AM
    
    EXEC dbo.sp_attach_schedule
        @job_name = 'MagnitSignalsImport',
        @schedule_name = 'MagnitSignalsImportSchedule';
END
```

#### 6.2 Проверка расписания
```sql
-- Проверка созданных джобов
SELECT 
    j.name as JobName,
    j.enabled,
    s.name as ScheduleName,
    s.freq_type,
    s.freq_interval,
    s.active_start_time
FROM msdb.dbo.sysjobs j
LEFT JOIN msdb.dbo.sysjobschedules js ON j.job_id = js.job_id
LEFT JOIN msdb.dbo.sysschedules s ON js.schedule_id = s.schedule_id
WHERE j.name LIKE '%Magnit%';
```

### Этап 7: Тестирование интеграции

#### 7.1 Проверка подключения к API
```bash
# Тест подключения к API
curl -X GET "https://api.magnet.ru/osa/v2/health" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json"

# Ожидаемый ответ
{
  "status": "ok",
  "version": "2.0",
  "timestamp": "2025-09-27T10:00:00Z"
}
```

#### 7.2 Тест получения сигналов
```sql
-- Запуск импорта сигналов вручную
EXEC [osa].[up_ImportSignals];

-- Проверка полученных сигналов
SELECT TOP 10 * FROM [osa].[MagnitSignals] 
ORDER BY ImportDate DESC;
```

#### 7.3 Тест отправки графиков
```sql
-- Запуск экспорта графиков вручную
EXEC [osa].[up_ExportSchedules];

-- Проверка логов отправки
SELECT TOP 10 * FROM [osa].[MagnitExportLogs] 
WHERE ExportType = 'Schedules'
ORDER BY ExportDate DESC;
```

### Этап 8: Мониторинг и логирование

#### 8.1 Настройка мониторинга
```sql
-- Создание таблицы для логов
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[osa].[MagnitExportLogs]') AND type in (N'U'))
BEGIN
    CREATE TABLE [osa].[MagnitExportLogs] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [ExportType] NVARCHAR(50) NOT NULL,
        [Status] NVARCHAR(20) NOT NULL,
        [Message] NVARCHAR(MAX),
        [ExportDate] DATETIME2 DEFAULT GETDATE(),
        [RecordsCount] INT DEFAULT 0
    );
END
```

#### 8.2 Проверка работы джобов
```sql
-- Проверка последних запусков джобов
SELECT 
    j.name as JobName,
    h.run_date,
    h.run_time,
    h.run_duration,
    h.run_status,
    h.message
FROM msdb.dbo.sysjobhistory h
JOIN msdb.dbo.sysjobs j ON h.job_id = j.job_id
WHERE j.name LIKE '%Magnit%'
ORDER BY h.run_date DESC, h.run_time DESC;
```

## Откат изменений

### Процедура отката
1. **Отключение функциональных флагов**:
   ```sql
   UPDATE FeatureFlags 
   SET IsEnabled = 0, UpdatedDate = GETDATE()
   WHERE FlagName IN ('UseMagnitApiClientV2', 'UseMagnitSignalsByApi')
     AND ProjectId = 'ROUST';
   ```

2. **Отключение джобов**:
   ```sql
   EXEC dbo.sp_update_job @job_name = 'MagnitSignalsImport', @enabled = 0;
   EXEC dbo.sp_update_job @job_name = 'MagnitSchedulesExport', @enabled = 0;
   EXEC dbo.sp_update_job @job_name = 'MagnitFeedbackExport', @enabled = 0;
   ```

3. **Откат БД**:
   - Восстановить из резервной копии
   - Проверить целостность данных

4. **Откат конфигурации**:
   - Удалить файл конфигурации плагина
   - Восстановить предыдущие настройки

### Критерии для отката
- Критические ошибки в работе API
- Потеря данных
- Неприемлемая производительность
- Проблемы с безопасностью

## План развертывания

### Подготовительный этап (1 день)
- [ ] Создание резервных копий
- [ ] Подготовка файла конфигурации
- [ ] Тестирование на тестовом окружении
- [ ] Уведомление пользователей

### Основной этап (4 часа)
- [ ] Создание файла конфигурации (30 мин)
- [ ] Включение функциональных флагов (15 мин)
- [ ] Создание таблиц БД (1 час)
- [ ] Создание дополнительных атрибутов (30 мин)
- [ ] Импорт данных (1 час)
- [ ] Настройка расписания (30 мин)

### Контрольный этап (2 часа)
- [ ] Тестирование интеграции
- [ ] Проверка работы джобов
- [ ] Мониторинг логов
- [ ] Документирование результатов

## Контакты и поддержка

### Команда развертывания
- **Руководитель**: Оздоган Татьяна
- **Разработчик**: Ярочкин Артем
- **Тестировщик**: Макаренко Илья
- **Администратор БД**: [Имя администратора БД]
- **Администратор серверов**: [Имя администратора серверов]

### Экстренные контакты
- **Техническая поддержка**: +7-XXX-XXX-XXXX
- **Горячая линия**: support@rust.ru
- **Чат поддержки**: [Ссылка на чат]

### Документация для справки
- [Техническое решение](TECHNICAL_SOLUTION_227878.md)
- [Руководство по тестированию](TESTING_GUIDE_227878.md)
- [Пользовательская документация](USER_GUIDE_227878.md)
- [Руководство по настройке](CONFIGURATION_GUIDE_227878.md)

## Чек-лист развертывания

### Предварительные проверки
- [ ] Резервные копии созданы
- [ ] Тестовое окружение проверено
- [ ] Файл конфигурации подготовлен
- [ ] Пользователи уведомлены
- [ ] План отката подготовлен

### Развертывание
- [ ] Файл конфигурации создан
- [ ] Функциональные флаги включены
- [ ] Таблицы БД созданы
- [ ] Дополнительные атрибуты созданы
- [ ] Данные импортированы
- [ ] Расписание настроено

### Проверки после развертывания
- [ ] Логи не содержат критических ошибок
- [ ] API подключение работает
- [ ] Джобы запускаются по расписанию
- [ ] Сигналы получаются корректно
- [ ] Графики отправляются успешно
- [ ] Производительность в пределах нормы

### Завершение
- [ ] Документация обновлена
- [ ] Пользователи обучены
- [ ] Мониторинг настроен
- [ ] План поддержки активирован

---
*Документ создан: 27.09.2025*  
*Версия: 1.0*  
*Статус: Готов к использованию*
