# РњРѕРґРµР»СЊ РґР°РЅРЅС‹С…

## РћР±Р·РѕСЂ Р±Р°Р·С‹ РґР°РЅРЅС‹С…

Р‘Р°Р·Р° РґР°РЅРЅС‹С… Р§РёРєР°РіРѕ СЃР»СѓР¶РёС‚ С†РµРЅС‚СЂР°Р»СЊРЅС‹Рј С…СЂР°РЅРёР»РёС‰РµРј РґР»СЏ СЃРёСЃС‚РµРјС‹ РёРЅС‚РµРіСЂР°С†РёРё РњРў СЃ Track and Trace. РСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ Microsoft SQL Server 2019.

## РћСЃРЅРѕРІРЅС‹Рµ С‚Р°Р±Р»РёС†С‹

### 1. РџРѕР»СЊР·РѕРІР°С‚РµР»Рё Рё Р°РІС‚РѕСЂРёР·Р°С†РёСЏ

#### Users
`sql
CREATE TABLE Users (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Username NVARCHAR(50) NOT NULL UNIQUE,
    PasswordHash NVARCHAR(255) NOT NULL,
    Role NVARCHAR(20) NOT NULL DEFAULT 'agent',
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);

CREATE INDEX IX_Users_Username ON Users(Username);
CREATE INDEX IX_Users_Role ON Users(Role);
`

#### UserSessions
`sql
CREATE TABLE UserSessions (
    Id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    UserId INT NOT NULL,
    DeviceId NVARCHAR(100) NOT NULL,
    Token NVARCHAR(500) NOT NULL,
    ExpiresAt DATETIME2 NOT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    IsActive BIT NOT NULL DEFAULT 1,
    
    FOREIGN KEY (UserId) REFERENCES Users(Id)
);

CREATE INDEX IX_UserSessions_UserId ON UserSessions(UserId);
CREATE INDEX IX_UserSessions_Token ON UserSessions(Token);
CREATE INDEX IX_UserSessions_ExpiresAt ON UserSessions(ExpiresAt);
`

### 2. РўРѕРІР°СЂС‹ Рё QR-РєРѕРґС‹

#### Products
`sql
CREATE TABLE Products (
    Id NVARCHAR(50) PRIMARY KEY,
    Name NVARCHAR(200) NOT NULL,
    Category NVARCHAR(50) NOT NULL,
    UnitPrice DECIMAL(10,2) NOT NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);

CREATE INDEX IX_Products_Category ON Products(Category);
CREATE INDEX IX_Products_IsActive ON Products(IsActive);
`

#### QRCodes
`sql
CREATE TABLE QRCodes (
    Id BIGINT IDENTITY(1,1) PRIMARY KEY,
    QRCode NVARCHAR(50) NOT NULL UNIQUE,
    ProductId NVARCHAR(50) NOT NULL,
    IsValid BIT NOT NULL DEFAULT 1,
    TnTStatus NVARCHAR(20) NULL,
    LastValidatedAt DATETIME2 NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    
    FOREIGN KEY (ProductId) REFERENCES Products(Id)
);

CREATE INDEX IX_QRCodes_QRCode ON QRCodes(QRCode);
CREATE INDEX IX_QRCodes_ProductId ON QRCodes(ProductId);
CREATE INDEX IX_QRCodes_IsValid ON QRCodes(IsValid);
`

### 3. РўРѕСЂРіРѕРІС‹Рµ С‚РѕС‡РєРё

#### Locations
`sql
CREATE TABLE Locations (
    Id NVARCHAR(20) PRIMARY KEY,
    Name NVARCHAR(200) NOT NULL,
    Address NVARCHAR(500) NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    TnTDepartFromExtId NVARCHAR(20) NULL,
    TnTPartnerFiscalId NVARCHAR(20) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);

CREATE INDEX IX_Locations_IsActive ON Locations(IsActive);
`

### 4. Р—Р°РєР°Р·С‹ Рё РѕС‚РіСЂСѓР·РєРё

#### Orders
`sql
CREATE TABLE Orders (
    Id NVARCHAR(50) PRIMARY KEY,
    CustomerId NVARCHAR(50) NOT NULL,
    LocationId NVARCHAR(20) NOT NULL,
    OrderType INT NOT NULL, -- 0: Cold Sale, 1: Ecomm, 2: Bonus Sale
    Status NVARCHAR(20) NOT NULL DEFAULT 'pending',
    TotalAmount DECIMAL(10,2) NOT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    
    FOREIGN KEY (LocationId) REFERENCES Locations(Id)
);

CREATE INDEX IX_Orders_CustomerId ON Orders(CustomerId);
CREATE INDEX IX_Orders_LocationId ON Orders(LocationId);
CREATE INDEX IX_Orders_OrderType ON Orders(OrderType);
CREATE INDEX IX_Orders_Status ON Orders(Status);
`

#### Shipments
`sql
CREATE TABLE Shipments (
    Id NVARCHAR(50) PRIMARY KEY,
    OrderId NVARCHAR(50) NOT NULL,
    LocationId NVARCHAR(20) NOT NULL,
    Status NVARCHAR(20) NOT NULL DEFAULT 'created',
    TnTStatus NVARCHAR(20) NULL,
    TnTDocumentId NVARCHAR(50) NULL,
    TotalAmount DECIMAL(10,2) NOT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CompletedAt DATETIME2 NULL,
    
    FOREIGN KEY (OrderId) REFERENCES Orders(Id),
    FOREIGN KEY (LocationId) REFERENCES Locations(Id)
);

CREATE INDEX IX_Shipments_OrderId ON Shipments(OrderId);
CREATE INDEX IX_Shipments_LocationId ON Shipments(LocationId);
CREATE INDEX IX_Shipments_Status ON Shipments(Status);
CREATE INDEX IX_Shipments_TnTStatus ON Shipments(TnTStatus);
`

#### ShipmentItems
`sql
CREATE TABLE ShipmentItems (
    Id BIGINT IDENTITY(1,1) PRIMARY KEY,
    ShipmentId NVARCHAR(50) NOT NULL,
    QRCode NVARCHAR(50) NOT NULL,
    ProductId NVARCHAR(50) NOT NULL,
    Quantity INT NOT NULL DEFAULT 1,
    UnitPrice DECIMAL(10,2) NOT NULL,
    TotalPrice DECIMAL(10,2) NOT NULL,
    
    FOREIGN KEY (ShipmentId) REFERENCES Shipments(Id),
    FOREIGN KEY (QRCode) REFERENCES QRCodes(QRCode),
    FOREIGN KEY (ProductId) REFERENCES Products(Id)
);

CREATE INDEX IX_ShipmentItems_ShipmentId ON ShipmentItems(ShipmentId);
CREATE INDEX IX_ShipmentItems_QRCode ON ShipmentItems(QRCode);
CREATE INDEX IX_ShipmentItems_ProductId ON ShipmentItems(ProductId);
`

### 5. РРЅС‚РµРіСЂР°С†РёСЏ СЃ T&T

#### TnTApiLogs
`sql
CREATE TABLE TnTApiLogs (
    Id BIGINT IDENTITY(1,1) PRIMARY KEY,
    RequestId UNIQUEIDENTIFIER NOT NULL,
    Method NVARCHAR(10) NOT NULL,
    Endpoint NVARCHAR(200) NOT NULL,
    RequestData NVARCHAR(MAX) NULL,
    ResponseData NVARCHAR(MAX) NULL,
    StatusCode INT NULL,
    ResponseTime INT NULL, -- РІ РјРёР»Р»РёСЃРµРєСѓРЅРґР°С…
    ErrorMessage NVARCHAR(500) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);

CREATE INDEX IX_TnTApiLogs_RequestId ON TnTApiLogs(RequestId);
CREATE INDEX IX_TnTApiLogs_CreatedAt ON TnTApiLogs(CreatedAt);
CREATE INDEX IX_TnTApiLogs_StatusCode ON TnTApiLogs(StatusCode);
`

#### TnTSessions
`sql
CREATE TABLE TnTSessions (
    Id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Username NVARCHAR(50) NOT NULL,
    Token NVARCHAR(500) NOT NULL,
    ExpiresAt DATETIME2 NOT NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);

CREATE INDEX IX_TnTSessions_Username ON TnTSessions(Username);
CREATE INDEX IX_TnTSessions_Token ON TnTSessions(Token);
CREATE INDEX IX_TnTSessions_ExpiresAt ON TnTSessions(ExpiresAt);
`

### 6. Р РµРїР»РёРєР°С†РёСЏ СЃ SAP

#### SAP_Products
`sql
CREATE TABLE SAP_Products (
    Id NVARCHAR(50) PRIMARY KEY,
    Name NVARCHAR(200) NOT NULL,
    Category NVARCHAR(50) NOT NULL,
    UnitPrice DECIMAL(10,2) NOT NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    LastSyncAt DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);

CREATE INDEX IX_SAP_Products_Category ON SAP_Products(Category);
CREATE INDEX IX_SAP_Products_LastSyncAt ON SAP_Products(LastSyncAt);
`

#### SAP_Customers
`sql
CREATE TABLE SAP_Customers (
    Id NVARCHAR(50) PRIMARY KEY,
    Name NVARCHAR(200) NOT NULL,
    Address NVARCHAR(500) NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    LastSyncAt DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);

CREATE INDEX IX_SAP_Customers_IsActive ON SAP_Customers(IsActive);
CREATE INDEX IX_SAP_Customers_LastSyncAt ON SAP_Customers(LastSyncAt);
`

## РЎРІСЏР·Рё РјРµР¶РґСѓ С‚Р°Р±Р»РёС†Р°РјРё

### Р”РёР°РіСЂР°РјРјР° СЃРІСЏР·РµР№
`
Users (1) в†ђв†’ (N) UserSessions
Users (1) в†ђв†’ (N) Orders
Locations (1) в†ђв†’ (N) Orders
Locations (1) в†ђв†’ (N) Shipments
Orders (1) в†ђв†’ (N) Shipments
Shipments (1) в†ђв†’ (N) ShipmentItems
Products (1) в†ђв†’ (N) QRCodes
Products (1) в†ђв†’ (N) ShipmentItems
QRCodes (1) в†ђв†’ (N) ShipmentItems
`

## РРЅРґРµРєСЃС‹ РґР»СЏ РїСЂРѕРёР·РІРѕРґРёС‚РµР»СЊРЅРѕСЃС‚Рё

### РЎРѕСЃС‚Р°РІРЅС‹Рµ РёРЅРґРµРєСЃС‹
`sql
-- Р”Р»СЏ РїРѕРёСЃРєР° РѕС‚РіСЂСѓР·РѕРє РїРѕ РїРµСЂРёРѕРґСѓ Рё СЃС‚Р°С‚СѓСЃСѓ
CREATE INDEX IX_Shipments_Status_CreatedAt 
ON Shipments(Status, CreatedAt);

-- Р”Р»СЏ РїРѕРёСЃРєР° QR-РєРѕРґРѕРІ РїРѕ С‚РѕРІР°СЂСѓ Рё РІР°Р»РёРґРЅРѕСЃС‚Рё
CREATE INDEX IX_QRCodes_ProductId_IsValid 
ON QRCodes(ProductId, IsValid);

-- Р”Р»СЏ РїРѕРёСЃРєР° С‚РѕРІР°СЂРѕРІ РїРѕ РєР°С‚РµРіРѕСЂРёРё Рё Р°РєС‚РёРІРЅРѕСЃС‚Рё
CREATE INDEX IX_Products_Category_IsActive 
ON Products(Category, IsActive);
`

### РџРѕРєСЂС‹РІР°СЋС‰РёРµ РёРЅРґРµРєСЃС‹
`sql
-- Р”Р»СЏ Р±С‹СЃС‚СЂРѕРіРѕ РїРѕР»СѓС‡РµРЅРёСЏ РёРЅС„РѕСЂРјР°С†РёРё РѕР± РѕС‚РіСЂСѓР·РєРµ
CREATE INDEX IX_Shipments_Cover 
ON Shipments(Id, OrderId, Status, TotalAmount, CreatedAt)
INCLUDE (TnTStatus, TnTDocumentId);

-- Р”Р»СЏ Р±С‹СЃС‚СЂРѕРіРѕ РїРѕРёСЃРєР° QR-РєРѕРґРѕРІ
CREATE INDEX IX_QRCodes_Cover 
ON QRCodes(QRCode, ProductId, IsValid)
INCLUDE (TnTStatus, LastValidatedAt);
`

## РҐСЂР°РЅРёРјС‹Рµ РїСЂРѕС†РµРґСѓСЂС‹

### 1. Р’Р°Р»РёРґР°С†РёСЏ QR-РєРѕРґР°
`sql
CREATE PROCEDURE sp_ValidateQRCode
    @QRCode NVARCHAR(50),
    @LocationId NVARCHAR(20),
    @IsValid BIT OUTPUT,
    @ProductId NVARCHAR(50) OUTPUT,
    @ErrorMessage NVARCHAR(500) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @ProductExists BIT = 0;
    DECLARE @QRExists BIT = 0;
    
    -- РџСЂРѕРІРµСЂРєР° СЃСѓС‰РµСЃС‚РІРѕРІР°РЅРёСЏ С‚РѕРІР°СЂР°
    SELECT @ProductExists = 1, @ProductId = ProductId
    FROM QRCodes 
    WHERE QRCode = @QRCode AND IsValid = 1;
    
    -- РџСЂРѕРІРµСЂРєР° СЃСѓС‰РµСЃС‚РІРѕРІР°РЅРёСЏ QR-РєРѕРґР°
    SELECT @QRExists = 1
    FROM QRCodes 
    WHERE QRCode = @QRCode;
    
    IF @QRExists = 0
    BEGIN
        SET @IsValid = 0;
        SET @ErrorMessage = 'QR-РєРѕРґ РЅРµ РЅР°Р№РґРµРЅ РІ СЃРёСЃС‚РµРјРµ';
        RETURN;
    END
    
    IF @ProductExists = 0
    BEGIN
        SET @IsValid = 0;
        SET @ErrorMessage = 'РўРѕРІР°СЂ РЅРµРґРѕСЃС‚СѓРїРµРЅ РґР»СЏ РїСЂРѕРґР°Р¶Рё';
        RETURN;
    END
    
    SET @IsValid = 1;
    SET @ErrorMessage = NULL;
END
`

### 2. РЎРѕР·РґР°РЅРёРµ РѕС‚РіСЂСѓР·РєРё
`sql
CREATE PROCEDURE sp_CreateShipment
    @OrderId NVARCHAR(50),
    @LocationId NVARCHAR(20),
    @OrderType INT,
    @TotalAmount DECIMAL(10,2),
    @ShipmentId NVARCHAR(50) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    SET @ShipmentId = 'SHIP-' + FORMAT(GETUTCDATE(), 'yyyyMMdd') + '-' + RIGHT('0000' + CAST(ABS(CHECKSUM(NEWID())) % 10000 AS VARCHAR), 4);
    
    INSERT INTO Shipments (Id, OrderId, LocationId, Status, TotalAmount)
    VALUES (@ShipmentId, @OrderId, @LocationId, 'created', @TotalAmount);
    
    -- РћР±РЅРѕРІР»РµРЅРёРµ СЃС‚Р°С‚СѓСЃР° Р·Р°РєР°Р·Р°
    UPDATE Orders 
    SET Status = 'processing', UpdatedAt = GETUTCDATE()
    WHERE Id = @OrderId;
END
`

## РўСЂРёРіРіРµСЂС‹

### 1. РћР±РЅРѕРІР»РµРЅРёРµ РІСЂРµРјРµРЅРё РёР·РјРµРЅРµРЅРёСЏ
`sql
CREATE TRIGGER tr_Users_UpdateTime
ON Users
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE Users 
    SET UpdatedAt = GETUTCDATE()
    FROM Users u
    INNER JOIN inserted i ON u.Id = i.Id
    WHERE u.UpdatedAt = i.UpdatedAt;
END
`

### 2. Р›РѕРіРёСЂРѕРІР°РЅРёРµ РёР·РјРµРЅРµРЅРёР№ РѕС‚РіСЂСѓР·РѕРє
`sql
CREATE TRIGGER tr_Shipments_LogChanges
ON Shipments
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO ShipmentStatusLogs (ShipmentId, OldStatus, NewStatus, ChangedAt)
    SELECT 
        i.Id,
        d.Status,
        i.Status,
        GETUTCDATE()
    FROM inserted i
    INNER JOIN deleted d ON i.Id = d.Id
    WHERE i.Status != d.Status;
END
`

## Р РµР·РµСЂРІРЅРѕРµ РєРѕРїРёСЂРѕРІР°РЅРёРµ

### РЎС‚СЂР°С‚РµРіРёСЏ Р±СЌРєР°РїР°
`sql
-- РџРѕР»РЅРѕРµ СЂРµР·РµСЂРІРЅРѕРµ РєРѕРїРёСЂРѕРІР°РЅРёРµ (РµР¶РµРґРЅРµРІРЅРѕ)
BACKUP DATABASE [Chicago] 
TO DISK = 'C:\Backup\Chicago_Full.bak'
WITH FORMAT, INIT, COMPRESSION;

-- РРЅРєСЂРµРјРµРЅС‚Р°Р»СЊРЅРѕРµ РєРѕРїРёСЂРѕРІР°РЅРёРµ (РєР°Р¶РґС‹Рµ 4 С‡Р°СЃР°)
BACKUP DATABASE [Chicago] 
TO DISK = 'C:\Backup\Chicago_Diff.bak'
WITH DIFFERENTIAL, FORMAT, INIT, COMPRESSION;

-- РљРѕРїРёСЂРѕРІР°РЅРёРµ Р»РѕРіРѕРІ С‚СЂР°РЅР·Р°РєС†РёР№ (РєР°Р¶РґС‹Рµ 15 РјРёРЅСѓС‚)
BACKUP LOG [Chicago] 
TO DISK = 'C:\Backup\Chicago_Log.trn'
WITH FORMAT, INIT, COMPRESSION;
`

## РњРѕРЅРёС‚РѕСЂРёРЅРі РїСЂРѕРёР·РІРѕРґРёС‚РµР»СЊРЅРѕСЃС‚Рё

### Р—Р°РїСЂРѕСЃС‹ РґР»СЏ РјРѕРЅРёС‚РѕСЂРёРЅРіР°
`sql
-- РўРѕРї Р·Р°РїСЂРѕСЃРѕРІ РїРѕ РІСЂРµРјРµРЅРё РІС‹РїРѕР»РЅРµРЅРёСЏ
SELECT TOP 10
    query_hash,
    total_elapsed_time,
    execution_count,
    total_elapsed_time / execution_count AS avg_elapsed_time
FROM sys.dm_exec_query_stats
ORDER BY total_elapsed_time DESC;

-- РЎС‚Р°С‚РёСЃС‚РёРєР° РёСЃРїРѕР»СЊР·РѕРІР°РЅРёСЏ РёРЅРґРµРєСЃРѕРІ
SELECT 
    i.name AS IndexName,
    s.user_seeks,
    s.user_scans,
    s.user_lookups,
    s.user_updates
FROM sys.dm_db_index_usage_stats s
INNER JOIN sys.indexes i ON s.object_id = i.object_id AND s.index_id = i.index_id
WHERE s.database_id = DB_ID()
ORDER BY s.user_seeks + s.user_scans + s.user_lookups DESC;
`

---
*РњРѕРґРµР»СЊ РґР°РЅРЅС‹С… РѕСЃРЅРѕРІР°РЅР° РЅР° С‚СЂРµР±РѕРІР°РЅРёСЏС… РёР· Р·Р°РїСЂРѕСЃР° 229127*
