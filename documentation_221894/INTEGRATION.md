# Интеграция "Транзитные заказы"

## Обзор

Данный документ описывает интеграцию системы "Транзитные заказы" с внешними системами, в первую очередь с учетной системой 1С.

## Интеграция с 1С (из TFS)

### Передача параметров транзитного заказа

**Параметры для передачи** (из основного запроса 221894):
- Тип лицензии (оптовая/розничная)
- Выбранный магазин (для розничных магазинов)
- Префикс заказа
- Признак "Это розница" (для розничной лицензии ЛД)
- Дата отгрузки (минус один день от даты отгрузки товара клиенту)

### Структура данных для передачи

**Формат JSON**:
```json
{
  "orderId": "12345",
  "isTransitOrder": true,
  "transitOrderData": {
    "licenseType": "Розничная ЛД",
    "storeName": null,
    "prefix": "V",
    "isRetail": true,
    "shipmentDate": "2025-09-26T10:30:00Z"
  },
  "orderDate": "2025-09-27T10:30:00Z"
}
```

### API endpoints для 1С

**Основной endpoint**:
```
POST /api/orders/transit
Content-Type: application/json
Authorization: Bearer {token}
```

**Endpoint валидации**:
```
POST /api/orders/validate-prefix
Content-Type: application/json
Authorization: Bearer {token}
```

### Обработка ответов от 1С

**Успешная обработка**:
```json
{
  "success": true,
  "orderId": "12345",
  "externalOrderId": "1C-ORDER-789",
  "message": "Order processed successfully",
  "processedAt": "2025-09-27T10:35:00Z"
}
```

**Ошибка обработки**:
```json
{
  "success": false,
  "orderId": "12345",
  "error": {
    "code": "INVALID_PREFIX",
    "message": "Invalid prefix for selected license type",
    "details": "Prefix 'V' is not valid for retail license type"
  }
}
```

## Интеграция с Replication.Shuttle (из TFS)

### Синхронизация справочников

**Источник**: Chicago DB (SQL Server)
**Назначение**: МТ DB (SQLite)

**Таблица**: `nsf.refTransitOrdersExtendedAttributes` → `nsfrefTransitOrdersExtendedAttributes`

### Конфигурация репликации

**BusinessObjects.xml**:
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

**ReplicationRules.xml**:
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

### Маппинг полей

**MappingRule_1_2_1.xml**:
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

## Обработка ошибок интеграции (из TFS)

### Исправленные проблемы

**Ошибка 231484** - Лишняя строка с нулями:
- **Проблема**: В выгрузке ХП появляется лишняя строка с нулевыми значениями
- **Решение**: Добавлена фильтрация в выгрузку ХП для исключения нулевых значений
- **SQL фильтр**: `WHERE isActive = 1 AND id > 0 AND name IS NOT NULL`

### Коды ошибок интеграции

| Код | Описание | Действие |
|-----|----------|----------|
| `SYNC_ERROR` | Ошибка синхронизации с 1С | Повторить синхронизацию |
| `INVALID_PREFIX` | Некорректный префикс для типа лицензии | Проверить соответствие префикса и типа |
| `MISSING_STORE` | Не выбран магазин для розничной монополи | Обязательно выбрать магазин |
| `VALIDATION_ERROR` | Ошибка валидации данных | Проверить заполнение всех полей |
| `API_TIMEOUT` | Таймаут API вызова | Повторить запрос |

### Логирование интеграции

**Файл логов**: `C:\Logs\TransitOrders_Integration.log`

**Формат записи**:
```
[2025-09-27 10:30:00] INFO: Transit order 12345 sent to 1C successfully
[2025-09-27 10:30:05] ERROR: 1C API timeout for order 12346
[2025-09-27 10:30:10] WARN: Invalid prefix 'X' for license type 'Розничная ЛД'
```

## Мониторинг интеграции

### Метрики производительности

- **Время синхронизации**: Среднее время передачи данных в 1С
- **Успешность передачи**: Процент успешно переданных заказов
- **Частота ошибок**: Количество ошибок в единицу времени
- **Время отклика API**: Время ответа от 1С

### Алерты

- **Критический**: Ошибки синхронизации > 5% за час
- **Предупреждение**: Время отклика API > 30 секунд
- **Информационный**: Успешная синхронизация 100% заказов

## Тестирование интеграции

### Тестовые сценарии

1. **Успешная передача заказа**:
   - Создать транзитный заказ с корректными данными
   - Проверить передачу в 1С
   - Убедиться в получении подтверждения

2. **Обработка ошибок**:
   - Передать заказ с некорректными данными
   - Проверить обработку ошибки
   - Убедиться в корректном сообщении об ошибке

3. **Синхронизация справочников**:
   - Изменить справочник в Chicago
   - Проверить синхронизацию с МТ
   - Убедиться в обновлении данных

### Тестовые данные

**Тестовый заказ**:
```json
{
  "orderId": "TEST-001",
  "isTransitOrder": true,
  "transitOrderData": {
    "licenseType": "Розничная ЛД",
    "prefix": "V",
    "isRetail": true
  }
}
```

## Резервное копирование и восстановление

### Резервное копирование данных интеграции

**Chicago DB**:
```sql
-- Создание резервной копии таблицы атрибутов
BACKUP TABLE nsf.refTransitOrdersExtendedAttributes 
TO 'C:\Backups\TransitOrderAttributes.bak'
```

**МТ DB**:
```bash
# Копирование локальной базы МТ
copy "C:\MT\Data\stmobile.db3" "C:\Backups\stmobile_backup.db3"
```

### Восстановление после сбоя

1. **Восстановление справочника**:
   - Восстановить таблицу из резервной копии
   - Запустить синхронизацию с МТ
   - Проверить корректность данных

2. **Восстановление интеграции с 1С**:
   - Проверить доступность API 1С
   - Повторить неудачные передачи
   - Синхронизировать состояние заказов
