# База данных "Транзитные заказы"

## Обзор

Система использует базу данных Chicago (SQL Server) для хранения справочников и логики транзитных заказов, а также локальную базу данных МТ (SQLite) для кэширования данных.

## Основные таблицы (из TFS)

### 1. Chicago DB (SQL Server)

**Таблица**: `nsf.refTransitOrdersExtendedAttributes`

**Назначение**: Справочник расширенных атрибутов для транзитных заказов

**Структура таблицы**:
```sql
CREATE TABLE nsf.refTransitOrdersExtendedAttributes (
    id INT IDENTITY(1,1) PRIMARY KEY,
    parentId INT NULL,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(500) NULL,
    level INT NOT NULL,
    isActive BIT NOT NULL DEFAULT 1,
    orderIndex INT NULL,
    createdDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    modifiedDate DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT FK_refTransitOrdersExtendedAttributes_parent 
        FOREIGN KEY (parentId) REFERENCES nsf.refTransitOrdersExtendedAttributes(id)
);
```

**Поля таблицы**:
- `id` - Уникальный идентификатор записи (первичный ключ)
- `parentId` - Ссылка на родительскую запись (для иерархии)
- `name` - Название атрибута
- `description` - Описание атрибута
- `level` - Уровень в иерархии (0 - корень, 1 - лицензия, 2 - магазин, 3 - префикс)
- `isActive` - Признак активности записи
- `orderIndex` - Порядок сортировки
- `createdDate` - Дата создания записи
- `modifiedDate` - Дата последнего изменения

**Индексы**:
```sql
-- Индекс по parentId для быстрого поиска дочерних элементов
CREATE INDEX IX_refTransitOrdersExtendedAttributes_parentId 
ON nsf.refTransitOrdersExtendedAttributes(parentId);

-- Индекс по level для фильтрации по уровням
CREATE INDEX IX_refTransitOrdersExtendedAttributes_level 
ON nsf.refTransitOrdersExtendedAttributes(level);

-- Составной индекс для оптимизации запросов иерархии
CREATE INDEX IX_refTransitOrdersExtendedAttributes_parent_level 
ON nsf.refTransitOrdersExtendedAttributes(parentId, level, isActive);
```

### 2. МТ DB (SQLite)

**Таблица**: `nsfrefTransitOrdersExtendedAttributes`

**Назначение**: Локальная копия справочника атрибутов в мобильном терминале

**Структура таблицы**:
```sql
CREATE TABLE nsfrefTransitOrdersExtendedAttributes (
    id INTEGER PRIMARY KEY,
    parentId INTEGER NULL,
    name TEXT NOT NULL,
    description TEXT NULL,
    level INTEGER NOT NULL,
    isActive INTEGER NOT NULL DEFAULT 1,
    orderIndex INTEGER NULL,
    lastSync DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parentId) REFERENCES nsfrefTransitOrdersExtendedAttributes(id)
);
```

**Поля таблицы**:
- `id` - Уникальный идентификатор записи (первичный ключ)
- `parentId` - Ссылка на родительскую запись (для иерархии)
- `name` - Название атрибута
- `description` - Описание атрибута
- `level` - Уровень в иерархии
- `isActive` - Признак активности записи (1 - активна, 0 - неактивна)
- `orderIndex` - Порядок сортировки
- `lastSync` - Время последней синхронизации

**Индексы**:
```sql
-- Индекс по parentId
CREATE INDEX idx_parentId ON nsfrefTransitOrdersExtendedAttributes(parentId);

-- Индекс по level
CREATE INDEX idx_level ON nsfrefTransitOrdersExtendedAttributes(level);

-- Индекс по isActive
CREATE INDEX idx_isActive ON nsfrefTransitOrdersExtendedAttributes(isActive);
```

## Иерархическая структура данных (из TFS)

### Обработка иерархии

**Логика** (из User Story 227560):
- Инди-таблица со списком атрибутов и их иерархической связью
- При выборе значения ("Да") запускается логика смены отображаемого списка
- Каждый новый шаг отображает следующую группу атрибутов
- Циклическая итерация по шагам до достижения конечного значения

## Интеграция с 1С (из TFS)

### Передача параметров

**Параметры** (из основного запроса 221894):
- Тип лицензии (оптовая/розничная)
- Выбранный магазин (для розничных магазинов)
- Префикс заказа
- Признак "Это розница" (для розничной лицензии ЛД)
- Дата отгрузки (минус один день от даты отгрузки товара клиенту)

## Обработка ошибок (из TFS)

### Исправленные проблемы

**Ошибка 231484** - Лишняя строка с нулями:
- Добавлена фильтрация в выгрузку ХП для исключения нулевых значений
