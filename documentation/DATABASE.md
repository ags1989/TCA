# Модель данных

## Обзор

Данный документ описывает модель данных системы разделения долгов ТТ по маршрутам в проекте АкваТрейд.

## Основные таблицы

### 1. rgReceivables (Регистр задолженностей)

**Назначение:** Хранение данных о задолженностях торговых точек

```sql
CREATE TABLE rgReceivables (
    id INT IDENTITY(1,1) PRIMARY KEY,
    idroute INT NOT NULL,                    -- Идентификатор маршрута
    OutletCode NVARCHAR(50) NOT NULL,       -- Код торговой точки
    DebtAmount DECIMAL(18,2) NOT NULL,      -- Сумма задолженности
    CurrencyCode NVARCHAR(3) DEFAULT 'RUB', -- Код валюты
    CreatedDate DATETIME2 DEFAULT GETDATE(), -- Дата создания записи
    UpdatedDate DATETIME2 DEFAULT GETDATE(), -- Дата обновления записи
    deleted BIT DEFAULT 0,                   -- Признак удаления
    verstamp TIMESTAMP                       -- Версионность
);
```

**Индексы:**
```sql
CREATE INDEX IX_rgReceivables_idroute ON rgReceivables(idroute);
CREATE INDEX IX_rgReceivables_OutletCode ON rgReceivables(OutletCode);
CREATE INDEX IX_rgReceivables_CreatedDate ON rgReceivables(CreatedDate);
```

### 2. refOutletFocusGroups (Индивидуальная таблица лимитов по фокусным группам)

**Назначение:** Хранение лимитов кредита и настроек стоп-листа в разрезе фокусных групп

```sql
CREATE TABLE refOutletFocusGroups (
    id INT IDENTITY(1,1) PRIMARY KEY,
    outercode NVARCHAR(100) NOT NULL,       -- Внешний код (Outlet_FG)
    Outlet INT NOT NULL,                    -- ID торговой точки
    FG NVARCHAR(50) NOT NULL,              -- Код фокусной группы
    CreditLimit DECIMAL(18,2) NOT NULL,     -- Лимит кредита
    IsInStopList BIT NOT NULL DEFAULT 0,    -- Признак нахождения в стоп-листе
    CreditDeadLine INT NOT NULL,           -- Срок кредита в днях
    classifier6code NVARCHAR(100),          -- Код классификатора №6 (причина стоп-листа)
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    UpdatedDate DATETIME2 DEFAULT GETDATE(),
    deleted BIT DEFAULT 0,
    verstamp TIMESTAMP
);
```

**Индексы:**
```sql
CREATE UNIQUE INDEX IX_refOutletFocusGroups_outercode ON refOutletFocusGroups(outercode);
CREATE INDEX IX_refOutletFocusGroups_Outlet ON refOutletFocusGroups(Outlet);
CREATE INDEX IX_refOutletFocusGroups_FG ON refOutletFocusGroups(FG);
```

### 3. refOutlets (Серийная таблица торговых точек)

**Назначение:** Основная таблица торговых точек с серийными настройками

```sql
CREATE TABLE refOutlets (
    id INT IDENTITY(1,1) PRIMARY KEY,
    OutletCode NVARCHAR(50) NOT NULL,       -- Код торговой точки
    OutletName NVARCHAR(255) NOT NULL,      -- Название торговой точки
    LimitCredit DECIMAL(18,2),              -- Лимит кредита (серийный)
    IsInStopList BIT DEFAULT 0,             -- Признак стоп-листа (серийный)
    idClassifier6 INT,                      -- ID классификатора №6
    CreditDeadline INT,                     -- Срок кредита в днях
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    UpdatedDate DATETIME2 DEFAULT GETDATE(),
    deleted BIT DEFAULT 0,
    verstamp TIMESTAMP
);
```

**Индексы:**
```sql
CREATE UNIQUE INDEX IX_refOutlets_OutletCode ON refOutlets(OutletCode);
CREATE INDEX IX_refOutlets_IsInStopList ON refOutlets(IsInStopList);
```

### 4. refOutercodes (Внешние коды)

**Назначение:** Связь между внешними кодами из УС и внутренними ID

```sql
CREATE TABLE refOutercodes (
    id INT IDENTITY(1,1) PRIMARY KEY,
    outercode NVARCHAR(100) NOT NULL,       -- Внешний код
    TableName NVARCHAR(100) NOT NULL,       -- Имя таблицы
    InternalId INT NOT NULL,                -- Внутренний ID
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    UpdatedDate DATETIME2 DEFAULT GETDATE(),
    deleted BIT DEFAULT 0,
    verstamp TIMESTAMP
);
```

**Индексы:**
```sql
CREATE UNIQUE INDEX IX_refOutercodes_outercode_table ON refOutercodes(outercode, TableName);
CREATE INDEX IX_refOutercodes_InternalId ON refOutercodes(InternalId);
```

### 5. refClassifiers (Классификаторы)

**Назначение:** Справочник классификаторов

```sql
CREATE TABLE refClassifiers (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ClassifierCode NVARCHAR(50) NOT NULL,   -- Код классификатора
    ClassifierName NVARCHAR(255) NOT NULL,  -- Название классификатора
    ClassifierType INT NOT NULL,            -- Тип классификатора (6 - причины стоп-листа)
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    UpdatedDate DATETIME2 DEFAULT GETDATE(),
    deleted BIT DEFAULT 0,
    verstamp TIMESTAMP
);
```

## Связи между таблицами

### 1. Связь rgReceivables → refOutlets
```sql
-- Связь по коду торговой точки
rgReceivables.OutletCode = refOutlets.OutletCode
```

### 2. Связь refOutletFocusGroups → refOutlets
```sql
-- Связь через внешний код
refOutletFocusGroups.outercode = refOutlets.OutletCode + '_' + refOutletFocusGroups.FG
```

### 3. Связь refOutlets → refClassifiers
```sql
-- Связь по классификатору №6
refOutlets.idClassifier6 = refClassifiers.id
WHERE refClassifiers.ClassifierType = 6
```

## Представления (Views)

### 1. v_OutletDebtsByRoute (Задолженности по маршрутам)

```sql
CREATE VIEW v_OutletDebtsByRoute AS
SELECT 
    r.idroute,
    r.OutletCode,
    o.OutletName,
    SUM(r.DebtAmount) as TotalDebt,
    fg.CreditLimit,
    fg.IsInStopList,
    fg.CreditDeadLine,
    c.ClassifierName as StopListReason
FROM rgReceivables r
INNER JOIN refOutlets o ON r.OutletCode = o.OutletCode
LEFT JOIN refOutletFocusGroups fg ON o.OutletCode + '_' + @focusGroup = fg.outercode
LEFT JOIN refClassifiers c ON o.idClassifier6 = c.id AND c.ClassifierType = 6
WHERE r.deleted = 0
GROUP BY r.idroute, r.OutletCode, o.OutletName, fg.CreditLimit, fg.IsInStopList, fg.CreditDeadLine, c.ClassifierName;
```

### 2. v_LogDataChange (Лог изменений данных)

```sql
CREATE VIEW v_LogDataChange AS
SELECT 
    ChangeDate,
    AppName,
    TableName,
    OperationType,
    RecordId,
    OldValues,
    NewValues
FROM dbo.DataChangeLog
WHERE ChangeDate >= DATEADD(day, -30, GETDATE());
```

## Хранимые процедуры

### 1. sp_GetOutletDebtsByRoute

```sql
CREATE PROCEDURE sp_GetOutletDebtsByRoute
    @RouteId INT,
    @FocusGroup NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        r.OutletCode,
        o.OutletName,
        SUM(r.DebtAmount) as TotalDebt,
        fg.CreditLimit,
        fg.IsInStopList,
        fg.CreditDeadLine,
        CASE 
            WHEN fg.IsInStopList = 1 THEN 'ТТ находится в стоп-листе'
            WHEN SUM(r.DebtAmount) > fg.CreditLimit THEN 'Превышена сумма кредита на ' + CAST(SUM(r.DebtAmount) - fg.CreditLimit AS NVARCHAR(20)) + ' руб.'
            ELSE NULL
        END as StatusMessage
    FROM rgReceivables r
    INNER JOIN refOutlets o ON r.OutletCode = o.OutletCode
    LEFT JOIN refOutletFocusGroups fg ON o.OutletCode + '_' + ISNULL(@FocusGroup, 'DEFAULT') = fg.outercode
    WHERE r.idroute = @RouteId
        AND r.deleted = 0
    GROUP BY r.OutletCode, o.OutletName, fg.CreditLimit, fg.IsInStopList, fg.CreditDeadLine;
END
```

### 2. sp_UpdateOutletFocusGroupSettings

```sql
CREATE PROCEDURE sp_UpdateOutletFocusGroupSettings
    @OutletCode NVARCHAR(50),
    @FocusGroup NVARCHAR(50),
    @CreditLimit DECIMAL(18,2),
    @IsInStopList BIT,
    @CreditDeadLine INT,
    @Classifier6Code NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @OuterCode NVARCHAR(100) = @OutletCode + '_' + @FocusGroup;
    
    -- Обновление или создание записи в refOutletFocusGroups
    MERGE refOutletFocusGroups AS target
    USING (SELECT @OuterCode as outercode, @OutletCode as Outlet, @FocusGroup as FG) AS source
    ON target.outercode = source.outercode
    WHEN MATCHED THEN
        UPDATE SET 
            CreditLimit = @CreditLimit,
            IsInStopList = @IsInStopList,
            CreditDeadLine = @CreditDeadLine,
            classifier6code = @Classifier6Code,
            UpdatedDate = GETDATE()
    WHEN NOT MATCHED THEN
        INSERT (outercode, Outlet, FG, CreditLimit, IsInStopList, CreditDeadLine, classifier6code)
        VALUES (@OuterCode, @OutletCode, @FocusGroup, @CreditLimit, @IsInStopList, @CreditDeadLine, @Classifier6Code);
END
```

## Триггеры

### 1. tr_refOutlets_PreventIndividualDataOverwrite

```sql
CREATE TRIGGER tr_refOutlets_PreventIndividualDataOverwrite
ON refOutlets
FOR UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Предотвращение перезаписи индивидуальных данных из МТ
    IF APP_NAME() = 'ST-Replication' 
       AND CONTEXT_INFO() LIKE '%Route%'  -- Проверка, что изменения из МТ
    BEGIN
        -- Откат изменений индивидуальных полей
        UPDATE o
        SET CreditLimit = d.CreditLimit,
            IsInStopList = d.IsInStopList,
            idClassifier6 = d.idClassifier6,
            CreditDeadline = d.CreditDeadline
        FROM refOutlets o
        INNER JOIN deleted d ON o.id = d.id
        INNER JOIN inserted i ON o.id = i.id
        WHERE o.id IN (SELECT id FROM inserted)
          AND (i.CreditLimit != d.CreditLimit 
               OR i.IsInStopList != d.IsInStopList 
               OR i.idClassifier6 != d.idClassifier6 
               OR i.CreditDeadline != d.CreditDeadline);
    END
END
```

## Индексы для производительности

### 1. Составные индексы

```sql
-- Для быстрого поиска задолженностей по маршруту и торговой точке
CREATE INDEX IX_rgReceivables_Route_Outlet ON rgReceivables(idroute, OutletCode) 
INCLUDE (DebtAmount, CreatedDate);

-- Для поиска настроек фокусных групп
CREATE INDEX IX_refOutletFocusGroups_Outlet_FG ON refOutletFocusGroups(Outlet, FG) 
INCLUDE (CreditLimit, IsInStopList, CreditDeadLine);

-- Для поиска внешних кодов
CREATE INDEX IX_refOutercodes_Table_Internal ON refOutercodes(TableName, InternalId) 
INCLUDE (outercode);
```

### 2. Покрывающие индексы

```sql
-- Для запросов отчета "Долги"
CREATE INDEX IX_rgReceivables_Covering ON rgReceivables(idroute, OutletCode, deleted) 
INCLUDE (DebtAmount, CurrencyCode, CreatedDate);

-- Для запросов карточки ТТ
CREATE INDEX IX_refOutletFocusGroups_Covering ON refOutletFocusGroups(outercode, deleted) 
INCLUDE (CreditLimit, IsInStopList, CreditDeadLine, classifier6code);
```

## Ограничения целостности

### 1. Проверочные ограничения

```sql
-- Проверка положительности суммы задолженности
ALTER TABLE rgReceivables 
ADD CONSTRAINT CK_rgReceivables_DebtAmount CHECK (DebtAmount >= 0);

-- Проверка положительности лимита кредита
ALTER TABLE refOutletFocusGroups 
ADD CONSTRAINT CK_refOutletFocusGroups_CreditLimit CHECK (CreditLimit >= 0);

-- Проверка положительности срока кредита
ALTER TABLE refOutletFocusGroups 
ADD CONSTRAINT CK_refOutletFocusGroups_CreditDeadLine CHECK (CreditDeadLine > 0);
```

### 2. Внешние ключи

```sql
-- Связь с классификаторами
ALTER TABLE refOutlets 
ADD CONSTRAINT FK_refOutlets_refClassifiers 
FOREIGN KEY (idClassifier6) REFERENCES refClassifiers(id);
```

## Партиционирование

### 1. Партиционирование по дате (rgReceivables)

```sql
-- Создание функции партиционирования
CREATE PARTITION FUNCTION PF_rgReceivables_Date (DATETIME2)
AS RANGE RIGHT FOR VALUES 
('2025-01-01', '2025-04-01', '2025-07-01', '2025-10-01', '2026-01-01');

-- Создание схемы партиционирования
CREATE PARTITION SCHEME PS_rgReceivables_Date
AS PARTITION PF_rgReceivables_Date
TO ([PRIMARY], [PRIMARY], [PRIMARY], [PRIMARY], [PRIMARY]);
```

## Резервное копирование

### 1. Стратегия резервного копирования

- **Полное резервное копирование**: Еженедельно
- **Дифференциальное резервное копирование**: Ежедневно
- **Резервное копирование журналов транзакций**: Каждые 15 минут

### 2. Критичные таблицы для резервного копирования

1. `rgReceivables` - основная бизнес-логика
2. `refOutletFocusGroups` - индивидуальные настройки
3. `refOutlets` - справочник торговых точек
4. `refOutercodes` - связи с УС
