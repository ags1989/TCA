# РњРѕРґРµР»СЊ РґР°РЅРЅС‹С…

## РћР±Р·РѕСЂ Р±Р°Р·С‹ РґР°РЅРЅС‹С…

РЎРёСЃС‚РµРјР° РёСЃРїРѕР»СЊР·СѓРµС‚ Р±Р°Р·Сѓ РґР°РЅРЅС‹С… Р§РёРєР°РіРѕ РґР»СЏ С…СЂР°РЅРµРЅРёСЏ РёРЅС„РѕСЂРјР°С†РёРё Рѕ С‚РѕРІР°СЂР°С…, РѕС‚РіСЂСѓР·РєР°С… Рё РёРЅС‚РµРіСЂР°С†РёРё СЃ SAP С‡РµСЂРµР· ST Р РµРїР»РёРєР°С†РёСЋ.

## РћСЃРЅРѕРІРЅС‹Рµ С‚Р°Р±Р»РёС†С‹

### 1. РўР°Р±Р»РёС†Р° С‚РѕРІР°СЂРѕРІ (Products)

`sql
CREATE TABLE Products (
    Id INT PRIMARY KEY IDENTITY(1,1),
    ExternalId NVARCHAR(50) NOT NULL,
    Name NVARCHAR(255) NOT NULL,
    Barcode NVARCHAR(50),
    AssortCode NVARCHAR(50),
    AssortName NVARCHAR(255),
    GroupId INT,
    IsActive BIT DEFAULT 1,
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    ModifiedDate DATETIME2 DEFAULT GETDATE()
);
`

**РћРїРёСЃР°РЅРёРµ РїРѕР»РµР№:**
- Id - РЈРЅРёРєР°Р»СЊРЅС‹Р№ РёРґРµРЅС‚РёС„РёРєР°С‚РѕСЂ
- ExternalId - Р’РЅРµС€РЅРёР№ ID С‚РѕРІР°СЂР° РІ T&T
- Name - РќР°Р·РІР°РЅРёРµ С‚РѕРІР°СЂР°
- Barcode - РЁС‚СЂРёС…-РєРѕРґ С‚РѕРІР°СЂР°
- AssortCode - РљРѕРґ Р°СЃСЃРѕСЂС‚РёРјРµРЅС‚Р°
- AssortName - РќР°Р·РІР°РЅРёРµ Р°СЃСЃРѕСЂС‚РёРјРµРЅС‚Р°
- GroupId - ID РіСЂСѓРїРїС‹ С‚РѕРІР°СЂРѕРІ
- IsActive - Р¤Р»Р°Рі Р°РєС‚РёРІРЅРѕСЃС‚Рё

### 2. РўР°Р±Р»РёС†Р° QR-РєРѕРґРѕРІ (QRCodes)

`sql
CREATE TABLE QRCodes (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Code NVARCHAR(100) NOT NULL UNIQUE,
    ProductId INT NOT NULL,
    Barcode NVARCHAR(50),
    UnitName NVARCHAR(50),
    Activated BIT DEFAULT 0,
    WithdrawType INT DEFAULT 0,
    ValidUntil DATETIME2,
    ProductDate DATETIME2,
    FiscalId NVARCHAR(50),
    BatchNum NVARCHAR(50),
    DepartId INT,
    ObjectName NVARCHAR(255),
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    ModifiedDate DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (ProductId) REFERENCES Products(Id)
);
`

**РћРїРёСЃР°РЅРёРµ РїРѕР»РµР№:**
- Code - QR-РєРѕРґ С‚РѕРІР°СЂР°
- ProductId - РЎСЃС‹Р»РєР° РЅР° С‚РѕРІР°СЂ
- Activated - РЎС‚Р°С‚СѓСЃ Р°РєС‚РёРІР°С†РёРё (РёР· T&T)
- WithdrawType - РўРёРї РёР·СЉСЏС‚РёСЏ (0 - Р°РєС‚РёРІРµРЅ, 1 - РёР·СЉСЏС‚)
- ValidUntil - РЎСЂРѕРє РґРµР№СЃС‚РІРёСЏ
- FiscalId - Р¤РёСЃРєР°Р»СЊРЅС‹Р№ ID

### 3. РўР°Р±Р»РёС†Р° РѕС‚РіСЂСѓР·РѕРє (Shipments)

`sql
CREATE TABLE Shipments (
    Id INT PRIMARY KEY IDENTITY(1,1),
    ExternalId NVARCHAR(50) NOT NULL,
    DocumentNumber NVARCHAR(50) NOT NULL,
    ShipmentDate DATETIME2 NOT NULL,
    DepartFromExtId NVARCHAR(50),
    DepartToExtId NVARCHAR(50),
    PartnerFiscalId NVARCHAR(50),
    OrderType INT NOT NULL, -- 0 = Cold Sale, 1 = Ecomm, 2 = Bonus Sale
    Status NVARCHAR(50) DEFAULT 'Pending',
    TnTDocumentId INT,
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    ModifiedDate DATETIME2 DEFAULT GETDATE()
);
`

**РћРїРёСЃР°РЅРёРµ РїРѕР»РµР№:**
- ExternalId - Р’РЅРµС€РЅРёР№ ID РґРѕРєСѓРјРµРЅС‚Р°
- DocumentNumber - РќРѕРјРµСЂ РґРѕРєСѓРјРµРЅС‚Р°
- OrderType - РўРёРї Р·Р°РєР°Р·Р° (0=Cold Sale, 1=Ecomm, 2=Bonus Sale)
- Status - РЎС‚Р°С‚СѓСЃ РѕС‚РіСЂСѓР·РєРё
- TnTDocumentId - ID РґРѕРєСѓРјРµРЅС‚Р° РІ T&T

### 4. РўР°Р±Р»РёС†Р° РїРѕР·РёС†РёР№ РѕС‚РіСЂСѓР·РєРё (ShipmentItems)

`sql
CREATE TABLE ShipmentItems (
    Id INT PRIMARY KEY IDENTITY(1,1),
    ShipmentId INT NOT NULL,
    AssortExtId NVARCHAR(50) NOT NULL,
    UnitExtId NVARCHAR(50) NOT NULL,
    Quantity INT NOT NULL,
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (ShipmentId) REFERENCES Shipments(Id)
);
`

### 5. РўР°Р±Р»РёС†Р° QR-РєРѕРґРѕРІ РІ РѕС‚РіСЂСѓР·РєРµ (ShipmentQRCodes)

`sql
CREATE TABLE ShipmentQRCodes (
    Id INT PRIMARY KEY IDENTITY(1,1),
    ShipmentItemId INT NOT NULL,
    QRCodesId INT NOT NULL,
    ValidationStatus NVARCHAR(50) DEFAULT 'Pending',
    ValidationError NVARCHAR(500),
    CreatedDate DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (ShipmentItemId) REFERENCES ShipmentItems(Id),
    FOREIGN KEY (QRCodesId) REFERENCES QRCodes(Id)
);
`

## РРЅРґРµРєСЃС‹

### РћСЃРЅРѕРІРЅС‹Рµ РёРЅРґРµРєСЃС‹:

`sql
-- РРЅРґРµРєСЃ РґР»СЏ Р±С‹СЃС‚СЂРѕРіРѕ РїРѕРёСЃРєР° РїРѕ QR-РєРѕРґСѓ
CREATE INDEX IX_QRCodes_Code ON QRCodes(Code);

-- РРЅРґРµРєСЃ РґР»СЏ РїРѕРёСЃРєР° С‚РѕРІР°СЂРѕРІ РїРѕ РІРЅРµС€РЅРµРјСѓ ID
CREATE INDEX IX_Products_ExternalId ON Products(ExternalId);

-- РРЅРґРµРєСЃ РґР»СЏ РїРѕРёСЃРєР° РѕС‚РіСЂСѓР·РѕРє РїРѕ РґР°С‚Рµ
CREATE INDEX IX_Shipments_ShipmentDate ON Shipments(ShipmentDate);

-- РРЅРґРµРєСЃ РґР»СЏ РїРѕРёСЃРєР° РїРѕ С‚РёРїСѓ Р·Р°РєР°Р·Р°
CREATE INDEX IX_Shipments_OrderType ON Shipments(OrderType);

-- РРЅРґРµРєСЃ РґР»СЏ РїРѕРёСЃРєР° РїРѕ СЃС‚Р°С‚СѓСЃСѓ
CREATE INDEX IX_Shipments_Status ON Shipments(Status);
`

## ST Р РµРїР»РёРєР°С†РёСЏ СЃ SAP

### Р’С…РѕРґСЏС‰РёРµ РґР°РЅРЅС‹Рµ РёР· SAP:

`sql
-- РўР°Р±Р»РёС†Р° РґР»СЏ РїРѕР»СѓС‡РµРЅРёСЏ С‚РѕРІР°СЂРѕРІ РёР· SAP
CREATE TABLE SAP_Products (
    Id INT PRIMARY KEY IDENTITY(1,1),
    SAP_ProductId NVARCHAR(50) NOT NULL,
    TnT_ProductId NVARCHAR(50),
    ProductName NVARCHAR(255),
    Barcode NVARCHAR(50),
    IsActive BIT DEFAULT 1,
    LastSyncDate DATETIME2 DEFAULT GETDATE()
);
`

### РСЃС…РѕРґСЏС‰РёРµ РґР°РЅРЅС‹Рµ РІ SAP:

`sql
-- РўР°Р±Р»РёС†Р° РґР»СЏ РѕС‚РїСЂР°РІРєРё РѕС‚РіСЂСѓР·РѕРє РІ SAP
CREATE TABLE SAP_Shipments (
    Id INT PRIMARY KEY IDENTITY(1,1),
    ShipmentId INT NOT NULL,
    SAP_DocumentId NVARCHAR(50),
    Status NVARCHAR(50) DEFAULT 'Pending',
    LastSyncDate DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (ShipmentId) REFERENCES Shipments(Id)
);
`

## РҐСЂР°РЅРёРјС‹Рµ РїСЂРѕС†РµРґСѓСЂС‹

### 1. Р’Р°Р»РёРґР°С†РёСЏ QR-РєРѕРґР°

`sql
CREATE PROCEDURE sp_ValidateQRCode
    @QRCode NVARCHAR(100),
    @IsValid BIT OUTPUT,
    @ProductId INT OUTPUT,
    @ErrorMessage NVARCHAR(500) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT @ProductId = qr.ProductId,
           @IsValid = CASE 
               WHEN qr.Activated = 1 AND qr.WithdrawType = 0 
               THEN 1 ELSE 0 
           END
    FROM QRCodes qr
    WHERE qr.Code = @QRCode;
    
    IF @ProductId IS NULL
    BEGIN
        SET @IsValid = 0;
        SET @ErrorMessage = 'QR-РєРѕРґ РЅРµ РЅР°Р№РґРµРЅ РІ Р±Р°Р·Рµ РґР°РЅРЅС‹С…';
    END
    ELSE IF @IsValid = 0
    BEGIN
        SET @ErrorMessage = 'QR-РєРѕРґ РЅРµ Р°РєС‚РёРІРёСЂРѕРІР°РЅ РёР»Рё РёР·СЉСЏС‚';
    END
END
`

### 2. РЎРѕР·РґР°РЅРёРµ РѕС‚РіСЂСѓР·РєРё

`sql
CREATE PROCEDURE sp_CreateShipment
    @ExternalId NVARCHAR(50),
    @DocumentNumber NVARCHAR(50),
    @ShipmentDate DATETIME2,
    @OrderType INT,
    @ShipmentId INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO Shipments (ExternalId, DocumentNumber, ShipmentDate, OrderType)
    VALUES (@ExternalId, @DocumentNumber, @ShipmentDate, @OrderType);
    
    SET @ShipmentId = SCOPE_IDENTITY();
END
`

## РћРіСЂР°РЅРёС‡РµРЅРёСЏ Рё РїСЂРѕРІРµСЂРєРё

### 1. РћРіСЂР°РЅРёС‡РµРЅРёСЏ С†РµР»РѕСЃС‚РЅРѕСЃС‚Рё:

`sql
-- РЈРЅРёРєР°Р»СЊРЅРѕСЃС‚СЊ QR-РєРѕРґРѕРІ
ALTER TABLE QRCodes ADD CONSTRAINT UK_QRCodes_Code UNIQUE (Code);

-- РЈРЅРёРєР°Р»СЊРЅРѕСЃС‚СЊ РІРЅРµС€РЅРёС… ID С‚РѕРІР°СЂРѕРІ
ALTER TABLE Products ADD CONSTRAINT UK_Products_ExternalId UNIQUE (ExternalId);

-- РџСЂРѕРІРµСЂРєР° С‚РёРїР° Р·Р°РєР°Р·Р°
ALTER TABLE Shipments ADD CONSTRAINT CK_Shipments_OrderType 
CHECK (OrderType IN (0, 1, 2));
`

### 2. РўСЂРёРіРіРµСЂС‹:

`sql
-- РўСЂРёРіРіРµСЂ РґР»СЏ РѕР±РЅРѕРІР»РµРЅРёСЏ ModifiedDate
CREATE TRIGGER tr_Products_UpdateModifiedDate
ON Products
AFTER UPDATE
AS
BEGIN
    UPDATE Products 
    SET ModifiedDate = GETDATE()
    WHERE Id IN (SELECT Id FROM inserted);
END
`

## Р РµР·РµСЂРІРЅРѕРµ РєРѕРїРёСЂРѕРІР°РЅРёРµ

### РЎС‚СЂР°С‚РµРіРёСЏ Р±СЌРєР°РїР°:
- РџРѕР»РЅРѕРµ СЂРµР·РµСЂРІРЅРѕРµ РєРѕРїРёСЂРѕРІР°РЅРёРµ: РµР¶РµРґРЅРµРІРЅРѕ РІ 02:00
- РРЅРєСЂРµРјРµРЅС‚Р°Р»СЊРЅРѕРµ РєРѕРїРёСЂРѕРІР°РЅРёРµ: РєР°Р¶РґС‹Рµ 4 С‡Р°СЃР°
- Р›РѕРіРё С‚СЂР°РЅР·Р°РєС†РёР№: РєР°Р¶РґС‹Рµ 15 РјРёРЅСѓС‚
- РҐСЂР°РЅРµРЅРёРµ Р±СЌРєР°РїРѕРІ: 30 РґРЅРµР№

---
*РЎС‚СЂСѓРєС‚СѓСЂР° Р±Р°Р·С‹ РґР°РЅРЅС‹С… РѕСЃРЅРѕРІР°РЅР° РЅР° РґР°РЅРЅС‹С… РёР· Р·Р°РїСЂРѕСЃР° 215042 Рё СЃРІСЏР·Р°РЅРЅС‹С… User Stories*
