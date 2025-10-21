# Конфигурация "Транзитные заказы"

## Обзор

Данный документ содержит конфигурационные файлы и настройки для системы "Транзитные заказы" в мобильном терминале (МТ) системы Ладога.

## Конфигурация Replication.Shuttle (из TFS)

### BusinessObjects.xml

**Назначение**: Определение бизнес-объектов для репликации

```xml
<BusinessObjects>
  <BusinessObject name="TransitOrderAttributes">
    <Table>nsf.refTransitOrdersExtendedAttributes</Table>
    <KeyField>id</KeyField>
    <Filter>isActive = 1 AND id > 0</Filter>
    <SyncType>Full</SyncType>
  </BusinessObject>
</BusinessObjects>
```

### ReplicationRules.xml

**Назначение**: Правила синхронизации данных между Chicago и МТ

```xml
<ReplicationRules>
  <Rule>
    <Source>nsf.refTransitOrdersExtendedAttributes</Source>
    <Target>nsfrefTransitOrdersExtendedAttributes</Target>
    <Filter>isActive = 1 AND id > 0</Filter>
    <SyncType>Full</SyncType>
    <Schedule>0 0 * * *</Schedule>
  </Rule>
</ReplicationRules>
```

### MappingRule_1_2_1.xml

**Назначение**: Маппинг полей при синхронизации

```xml
<MappingRules>
  <Mapping>
    <SourceField>id</SourceField>
    <TargetField>id</TargetField>
    <DataType>INT</DataType>
    <IsKey>true</IsKey>
  </Mapping>
  <Mapping>
    <SourceField>parentId</SourceField>
    <TargetField>parentId</TargetField>
    <DataType>INT</DataType>
  </Mapping>
  <Mapping>
    <SourceField>name</SourceField>
    <TargetField>name</TargetField>
    <DataType>NVARCHAR</DataType>
  </Mapping>
  <Mapping>
    <SourceField>description</SourceField>
    <TargetField>description</TargetField>
    <DataType>NVARCHAR</DataType>
  </Mapping>
  <Mapping>
    <SourceField>level</SourceField>
    <TargetField>level</TargetField>
    <DataType>INT</DataType>
  </Mapping>
  <Mapping>
    <SourceField>isActive</SourceField>
    <TargetField>isActive</TargetField>
    <DataType>BIT</DataType>
  </Mapping>
</MappingRules>
```

## Конфигурация мобильного терминала (из TFS)

### Настройки компонентов

**Component-libs** (из Backlog Item 229881):
- Создание обработчика для правил в компоненте
- Добавление обработчика для типа

**Shared-libs** (из Backlog Item 229881):
- FormRulesFactory - Фабрика правил
- FormRulesService - Сервис по работе с правилами
- TreeToConstructorAdapter - Модель представления зависимых полей

### Конфигурация репликации в МТ

**Файл**: `rpl_SyncTransport.dll.config`

```xml
<configuration>
  <appSettings>
    <add key="ImportPath" value="C:\MT\Data\Import"/>
    <add key="DataFormat" value="TXT"/>
    <add key="SyncInterval" value="3600"/>
    <add key="TransitOrderAttributes" value="nsfrefTransitOrdersExtendedAttributes"/>
  </appSettings>
</configuration>
```

## Интеграция с 1С (из TFS)

### Параметры передачи

**Конфигурация полей** (из основного запроса 221894):

```json
{
  "transitOrderConfig": {
    "fields": {
      "orderId": "id",
      "isTransitOrder": "isTransit",
      "licenseType": "licenseType",
      "storeName": "storeName",
      "prefix": "prefix",
      "isRetail": "isRetail",
      "shipmentDate": "shipmentDate"
    },
    "mapping": {
      "Розничная ЛД": {
        "isRetail": true,
        "storeName": null
      },
      "Розничная монополь": {
        "isRetail": false,
        "storeName": "selectedStore"
      }
    }
  }
}
```

### API endpoints для 1С

```json
{
  "api": {
    "baseUrl": "https://1c-server.company.com/api",
    "endpoints": {
      "transitOrders": "/orders/transit",
      "validatePrefix": "/orders/validate-prefix"
    },
    "authentication": {
      "type": "Bearer",
      "token": "your-api-token"
    }
  }
}
```

## Настройки базы данных (из TFS)

### Chicago DB (SQL Server)

**Таблица**: `nsf.refTransitOrdersExtendedAttributes`

**Конфигурация репликации**:
- Источник данных для синхронизации с МТ
- Фильтрация активных записей
- Иерархическая структура атрибутов

### МТ DB (SQLite)

**Таблица**: `nsfrefTransitOrdersExtendedAttributes`

**Конфигурация**:
- Локальная копия справочника
- Синхронизация через Replication.Shuttle
- Поддержка офлайн режима

## Обработка ошибок (из TFS)

### Конфигурация валидации

**Ошибка 231567** - Кнопка "Сохранить":
```javascript
const validationConfig = {
  requiredFields: ['licenseType', 'prefix'],
  defaultValues: {
    licenseType: 'Оптовая',
    prefix: null,
    storeName: null
  },
  saveButtonLogic: {
    enabled: 'allFieldsFilled && valuesChanged',
    disabled: 'valuesMatchDefault'
  }
};
```

**Ошибка 231570** - Возврат значений:
```javascript
const resetConfig = {
  onTransitChange: {
    from: 'Да',
    to: 'Нет',
    action: 'resetToDefault'
  }
};
```

**Ошибка 231484** - Фильтрация нулевых значений:
```sql
-- Фильтр для выгрузки ХП
WHERE isActive = 1 AND id > 0 AND name IS NOT NULL
```

## Мониторинг и логирование

### Настройки логирования

```xml
<configuration>
  <system.diagnostics>
    <trace autoflush="true">
      <listeners>
        <add name="TransitOrdersLog" 
             type="System.Diagnostics.TextWriterTraceListener" 
             initializeData="C:\Logs\TransitOrders.log"/>
      </listeners>
    </trace>
  </system.diagnostics>
</configuration>
```

### Метрики производительности

```json
{
  "metrics": {
    "syncInterval": 3600,
    "maxRetries": 3,
    "timeout": 30000,
    "batchSize": 1000
  }
}
```

## Проверка конфигурации

### Скрипт проверки

```sql
-- Проверка таблицы в Chicago
SELECT COUNT(*) as TotalRecords 
FROM nsf.refTransitOrdersExtendedAttributes 
WHERE isActive = 1;

-- Проверка иерархии
WITH Hierarchy AS (
    SELECT id, parentId, name, level, 0 as depth
    FROM nsf.refTransitOrdersExtendedAttributes 
    WHERE parentId IS NULL
    UNION ALL
    SELECT h.id, h.parentId, h.name, h.level, p.depth + 1
    FROM nsf.refTransitOrdersExtendedAttributes h
    INNER JOIN Hierarchy p ON h.parentId = p.id
)
SELECT * FROM Hierarchy ORDER BY depth, name;
```

### Проверка синхронизации

```bash
# Проверка статуса сервиса репликации
sc query "Replication.Shuttle.AquaTrade.UAT"

# Проверка логов
tail -f "C:\Replication\Logs\replication.log"
```
