# Руководство по развертыванию: KA_NAME ТТ - Исправление отображения названий торговых точек

## Обзор развертывания

### Цель
Обеспечить корректное развертывание исправления проблемы отображения названий торговых точек в системе репликации с минимальным влиянием на работу системы.

### Компоненты для развертывания
1. **Обновленный код** - модифицированные классы для работы с названиями ТТ
2. **SQL скрипты** - создание хранимых процедур и индексов
3. **Конфигурация** - обновление настроек системы
4. **Тестирование** - проверка корректности работы после развертывания

## Предварительные требования

### Системные требования
- **.NET Framework**: 4.7.2 или выше
- **SQL Server**: 2016 или выше
- **Память**: Минимум 4 GB RAM
- **Дисковое пространство**: 1 GB свободного места
- **Сеть**: Стабильное подключение к БД

### Доступы и права
- **Администратор БД**: Для выполнения SQL скриптов
- **Администратор серверов**: Для обновления приложения
- **Разработчик**: Для проверки корректности развертывания
- **Тестировщик**: Для валидации функциональности

### Резервное копирование
- Создать полную резервную копию БД
- Сохранить текущие файлы приложения
- Создать точку восстановления системы
- Сохранить текущие конфигурации

## Этапы развертывания

### Этап 1: Подготовка к развертыванию

#### 1.1 Создание резервных копий
```sql
-- Создание полной резервной копии БД
BACKUP DATABASE [ReplicationDB] 
TO DISK = 'C:\Backups\ReplicationDB_Before_KA_NAME_Fix.bak'
WITH FORMAT, INIT, NAME = 'ReplicationDB Full Backup Before KA_NAME Fix';
```

#### 1.2 Проверка текущего состояния
```sql
-- Проверка текущих данных
SELECT 
    COUNT(*) as TotalTradingPoints,
    SUM(CASE WHEN c.KA_NAME IS NOT NULL AND c.KA_NAME != '' THEN 1 ELSE 0 END) as WithKAName,
    SUM(CASE WHEN c.KA_NAME IS NULL OR c.KA_NAME = '' THEN 1 ELSE 0 END) as WithoutKAName
FROM refOutlets tt
LEFT JOIN refClients c ON tt.idClient = c.id;
```

#### 1.3 Остановка служб
```powershell
# Остановка службы репликации
Stop-Service -Name "ReplicationService" -Force

# Проверка остановки
Get-Service -Name "ReplicationService"
```

### Этап 2: Развертывание SQL компонентов

#### 2.1 Создание хранимой процедуры
```sql
-- Создание хранимой процедуры для получения названий ТТ
USE [ReplicationDB]
GO

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
GO
```

#### 2.2 Создание индексов для производительности
```sql
-- Создание индекса для поля KA_NAME
CREATE INDEX IX_refClients_KA_NAME 
ON refClients(KA_NAME) 
WHERE KA_NAME IS NOT NULL AND KA_NAME != '';

-- Создание индекса для связи ТТ-Клиент
CREATE INDEX IX_refOutlets_idClient 
ON refOutlets(idClient);

-- Создание индекса для связи ТТ-Юридическое лицо
CREATE INDEX IX_refOutlets_idLegalEntity 
ON refOutlets(idLegalEntity);
```

#### 2.3 Проверка создания объектов
```sql
-- Проверка создания хранимой процедуры
SELECT name, type_desc 
FROM sys.procedures 
WHERE name = 'sp_GetTradingPointDisplayName';

-- Проверка создания индексов
SELECT 
    i.name as IndexName,
    t.name as TableName,
    i.type_desc as IndexType
FROM sys.indexes i
JOIN sys.tables t ON i.object_id = t.object_id
WHERE i.name IN ('IX_refClients_KA_NAME', 'IX_refOutlets_idClient', 'IX_refOutlets_idLegalEntity');
```

### Этап 3: Развертывание приложения

#### 3.1 Обновление файлов приложения
```powershell
# Создание резервной копии текущих файлов
Copy-Item -Path "C:\Replication\bin" -Destination "C:\Backups\Replication_bin_backup" -Recurse

# Остановка приложения
Stop-Process -Name "ReplicationApp" -Force -ErrorAction SilentlyContinue

# Обновление файлов
Copy-Item -Path "C:\Deploy\Replication\*" -Destination "C:\Replication\" -Recurse -Force
```

#### 3.2 Обновление конфигурации
```xml
<!-- Обновление app.config -->
<configuration>
  <appSettings>
    <!-- Включение использования KA_NAME для отображения ТТ -->
    <add key="UseKANameForTradingPoints" value="true" />
    
    <!-- Fallback на юридическое лицо если KA_NAME пустое -->
    <add key="FallbackToLegalEntity" value="true" />
    
    <!-- Значение по умолчанию для неизвестных ТТ -->
    <add key="DefaultTradingPointName" value="Неизвестная ТТ" />
    
    <!-- Включение кэширования названий ТТ -->
    <add key="EnableTradingPointNameCaching" value="true" />
    
    <!-- Время жизни кэша в минутах -->
    <add key="TradingPointNameCacheExpirationMinutes" value="30" />
  </appSettings>
  
  <connectionStrings>
    <add name="ReplicationDB" 
         connectionString="Data Source=SQLSERVER;Initial Catalog=ReplicationDB;Integrated Security=True" 
         providerName="System.Data.SqlClient" />
  </connectionStrings>
</configuration>
```

#### 3.3 Проверка обновления
```powershell
# Проверка версии приложения
Get-ItemProperty -Path "C:\Replication\ReplicationApp.exe" | Select-Object VersionInfo

# Проверка конфигурации
Test-Path "C:\Replication\app.config"
```

### Этап 4: Запуск и проверка

#### 4.1 Запуск служб
```powershell
# Запуск службы репликации
Start-Service -Name "ReplicationService"

# Проверка запуска
Get-Service -Name "ReplicationService"
```

#### 4.2 Проверка работы хранимой процедуры
```sql
-- Тестирование хранимой процедуры
EXEC sp_GetTradingPointDisplayName @TradingPointId = 460011;

-- Ожидаемый результат:
-- TradingPointId: 460011
-- DisplayName: "Шах" (если KA_NAME заполнено)
-- NameSource: "KA_NAME"
```

#### 4.3 Проверка логов
```powershell
# Проверка логов приложения
Get-Content "C:\Replication\Logs\app.log" -Tail 50

# Проверка логов службы
Get-EventLog -LogName Application -Source "ReplicationService" -Newest 10
```

### Этап 5: Тестирование функциональности

#### 5.1 Тестирование отображения названий
```sql
-- Тест 1: ТТ с заполненным KA_NAME
SELECT 
    tt.id,
    c.KA_NAME,
    le.name as LegalEntityName,
    CASE 
        WHEN c.KA_NAME IS NOT NULL AND c.KA_NAME != '' 
        THEN c.KA_NAME
        ELSE le.name
    END as DisplayName
FROM refOutlets tt
LEFT JOIN refClients c ON tt.idClient = c.id
LEFT JOIN refLegalEntities le ON tt.idLegalEntity = le.id
WHERE c.KA_NAME IS NOT NULL AND c.KA_NAME != ''
LIMIT 5;

-- Тест 2: ТТ без KA_NAME
SELECT 
    tt.id,
    c.KA_NAME,
    le.name as LegalEntityName,
    CASE 
        WHEN c.KA_NAME IS NOT NULL AND c.KA_NAME != '' 
        THEN c.KA_NAME
        ELSE le.name
    END as DisplayName
FROM refOutlets tt
LEFT JOIN refClients c ON tt.idClient = c.id
LEFT JOIN refLegalEntities le ON tt.idLegalEntity = le.id
WHERE c.KA_NAME IS NULL OR c.KA_NAME = ''
LIMIT 5;
```

#### 5.2 Генерация тестового отчета
```powershell
# Запуск генерации тестового отчета
& "C:\Replication\ReportGenerator.exe" -ClientId 1 -OutputFile "C:\Temp\test_report.xml"

# Проверка содержимого отчета
Get-Content "C:\Temp\test_report.xml" | Select-String "name="
```

#### 5.3 Проверка производительности
```sql
-- Проверка времени выполнения запросов
SET STATISTICS TIME ON;

EXEC sp_GetTradingPointDisplayName @TradingPointId = 460011;

SET STATISTICS TIME OFF;
```

### Этап 6: Мониторинг и валидация

#### 6.1 Мониторинг производительности
```sql
-- Создание представления для мониторинга
CREATE VIEW vw_TradingPointNameUsage AS
SELECT 
    COUNT(*) as TotalTradingPoints,
    SUM(CASE WHEN c.KA_NAME IS NOT NULL AND c.KA_NAME != '' THEN 1 ELSE 0 END) as UsingKAName,
    SUM(CASE WHEN c.KA_NAME IS NULL OR c.KA_NAME = '' THEN 1 ELSE 0 END) as UsingLegalEntity,
    GETDATE() as CheckTime
FROM refOutlets tt
LEFT JOIN refClients c ON tt.idClient = c.id;

-- Запрос для мониторинга
SELECT * FROM vw_TradingPointNameUsage;
```

#### 6.2 Проверка корректности данных
```sql
-- Проверка на наличие некорректных названий
SELECT 
    tt.id,
    c.KA_NAME,
    le.name as LegalEntityName,
    CASE 
        WHEN c.KA_NAME IS NOT NULL AND c.KA_NAME != '' 
        THEN c.KA_NAME
        ELSE le.name
    END as DisplayName
FROM refOutlets tt
LEFT JOIN refClients c ON tt.idClient = c.id
LEFT JOIN refLegalEntities le ON tt.idLegalEntity = le.id
WHERE (c.KA_NAME IS NOT NULL AND c.KA_NAME != '' AND le.name IS NULL)
   OR (c.KA_NAME IS NULL OR c.KA_NAME = '') AND le.name IS NULL;
```

## Откат изменений

### Процедура отката
1. **Остановка служб**:
   ```powershell
   Stop-Service -Name "ReplicationService" -Force
   ```

2. **Восстановление БД**:
   ```sql
   -- Восстановление из резервной копии
   RESTORE DATABASE [ReplicationDB] 
   FROM DISK = 'C:\Backups\ReplicationDB_Before_KA_NAME_Fix.bak'
   WITH REPLACE;
   ```

3. **Восстановление файлов**:
   ```powershell
   # Остановка приложения
   Stop-Process -Name "ReplicationApp" -Force -ErrorAction SilentlyContinue
   
   # Восстановление файлов
   Copy-Item -Path "C:\Backups\Replication_bin_backup\*" -Destination "C:\Replication\" -Recurse -Force
   ```

4. **Запуск служб**:
   ```powershell
   Start-Service -Name "ReplicationService"
   ```

### Критерии для отката
- Критические ошибки в работе системы
- Потеря данных
- Неприемлемая производительность
- Проблемы с совместимостью

## План развертывания

### Подготовительный этап (2 часа)
- [ ] Создание резервных копий
- [ ] Проверка текущего состояния
- [ ] Подготовка файлов для развертывания
- [ ] Уведомление пользователей

### Основной этап (1 час)
- [ ] Остановка служб (15 мин)
- [ ] Развертывание SQL компонентов (20 мин)
- [ ] Обновление приложения (15 мин)
- [ ] Запуск служб (10 мин)

### Контрольный этап (1 час)
- [ ] Тестирование функциональности
- [ ] Проверка производительности
- [ ] Мониторинг логов
- [ ] Документирование результатов

## Чек-лист развертывания

### Предварительные проверки
- [ ] Резервные копии созданы
- [ ] Тестовое окружение проверено
- [ ] Файлы для развертывания подготовлены
- [ ] Пользователи уведомлены
- [ ] План отката подготовлен

### Развертывание
- [ ] Службы остановлены
- [ ] SQL скрипты выполнены
- [ ] Приложение обновлено
- [ ] Конфигурация обновлена
- [ ] Службы запущены

### Проверки после развертывания
- [ ] Логи не содержат критических ошибок
- [ ] Хранимая процедура работает
- [ ] Отчеты генерируются корректно
- [ ] Производительность в пределах нормы
- [ ] Мониторинг настроен

### Завершение
- [ ] Документация обновлена
- [ ] Пользователи уведомлены
- [ ] Мониторинг активирован
- [ ] План поддержки обновлен

## Контакты и поддержка

### Команда развертывания
- **Руководитель развертывания**: [Имя руководителя]
- **Администратор БД**: [Имя администратора БД]
- **Администратор серверов**: [Имя администратора серверов]
- **Разработчик**: [Имя разработчика]

### Экстренные контакты
- **Техническая поддержка**: +7-XXX-XXX-XXXX
- **Горячая линия**: support@company.ru
- **Чат поддержки**: [Ссылка на чат]

### Документация для справки
- [Техническое решение](TECHNICAL_SOLUTION_22963.md)
- [Руководство по тестированию](TESTING_GUIDE_22963.md)
- [Основной документ проекта](PROJECT_22963_KA_NAME_TT_Display_Issue.md)

## Мониторинг после развертывания

### Ключевые метрики
- **Количество ТТ с KA_NAME**: Отслеживание использования нового функционала
- **Время выполнения запросов**: Контроль производительности
- **Ошибки в логах**: Мониторинг стабильности
- **Использование кэша**: Эффективность кэширования

### Алерты
- **Критические ошибки**: Немедленно
- **Снижение производительности**: В течение 1 часа
- **Проблемы с данными**: В течение 30 минут
- **Ошибки в логах**: В течение 2 часов

---
*Документ создан: 27.09.2025*  
*Версия: 1.0*  
*Статус: Готов к использованию*
