# API и интерфейсы

## Обзор

Данный документ описывает API и интерфейсы системы разделения долгов ТТ по маршрутам в проекте АкваТрейд.

## Интерфейсы репликации

### 1. Загрузка данных из УС

#### Формат файла references.xml

```xml
<?xml version="1.0"?>
<REFERENCES xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <FocusGroups>
    <Group>
      <outercode>13783_FG1234</outercode>
      <Outlet>13783</Outlet>
      <FG>FG1234</FG>
      <CreditLimit>100000</CreditLimit>
      <IsInStopList>0</IsInStopList>
      <CreditDeadLine>20</CreditDeadLine>
      <classifier6code></classifier6code>
    </Group>
  </FocusGroups>
</REFERENCES>
```

#### Параметры запуска репликации

```bash
-action=get -det=synchronization -group=ImportRefs -contextNodeID=2
```

**Параметры:**
- `action`: get - получение данных
- `det`: synchronization - тип синхронизации
- `group`: ImportRefs - группа импорта
- `contextNodeID`: ID ноды дистрибьютора

### 2. Выгрузка данных в МТ

#### Серийные таблицы МТ

**refOutlets:**
- `LimitCredit` - Лимит кредита
- `IsInStopList` - Признак "Стоп-лист"
- `idClassifier6` - Причина постановки в стоп-лист
- `CreditDeadline` - Срок кредита (дней)

#### Регистр задолженностей

Данные выгружаются в серийный регистр задолженностей с фильтрацией по `idroute` агента.

## Конфигурационные файлы

### 1. BusinessObjects.xml

Определяет бизнес-объекты для репликации:

```xml
<!-- Пример конфигурации для FocusGroups -->
<BusinessObject name="FocusGroups">
  <Table name="refOutletFocusGroups">
    <Field name="outercode" type="string" />
    <Field name="Outlet" type="int" />
    <Field name="FG" type="string" />
    <Field name="CreditLimit" type="decimal" />
    <Field name="IsInStopList" type="bit" />
    <Field name="CreditDeadLine" type="int" />
    <Field name="classifier6code" type="string" />
  </Table>
</BusinessObject>
```

### 2. ReplicationRules.xml

Правила репликации данных:

```xml
<!-- Правила для загрузки данных из УС -->
<ReplicationRule source="US" target="Chicago">
  <Table name="refOutletFocusGroups" />
  <Table name="refOutercodes" />
</ReplicationRule>

<!-- Правила для выгрузки в МТ -->
<ReplicationRule source="Chicago" target="MT">
  <Table name="refOutlets" />
  <Table name="rgReceivables" />
</ReplicationRule>
```

### 3. SyncProtocolRules_1_2_1.xml

Протокол синхронизации:

```xml
<SyncProtocol version="1.2.1">
  <Rule name="FocusGroupsSync">
    <Source>US</Source>
    <Target>Chicago</Target>
    <Filter>idroute = @agentRoute</Filter>
  </Rule>
</SyncProtocol>
```

### 4. MappingRule_1_2_1.xml

Правила сопоставления данных:

```xml
<MappingRule>
  <Source name="US_FocusGroups">
    <Field name="outercode" mapTo="refOutletFocusGroups.outercode" />
    <Field name="CreditLimit" mapTo="refOutletFocusGroups.CreditLimit" />
  </Source>
  <Target name="Chicago_FocusGroups">
    <Table name="refOutletFocusGroups" />
  </Target>
</MappingRule>
```

## API базы данных

### 1. Хранимые процедуры

#### sp_rpl_getContextCondition
- **Назначение**: Получение условий контекста для репликации
- **Параметры**: contextNodeID
- **Возвращает**: Условия фильтрации данных

#### sp_rpl_getSyncData
- **Назначение**: Получение данных для синхронизации
- **Параметры**: contextNodeID, group
- **Возвращает**: Набор данных для выгрузки

#### sp_rpl_searchValues
- **Назначение**: Поиск значений в реплицируемых таблицах
- **Параметры**: tableName, searchCriteria
- **Возвращает**: Найденные записи

### 2. Триггеры

#### Триггер для refOutlets
```sql
CREATE TRIGGER tr_refOutlets_Update
ON refOutlets
FOR UPDATE
AS
BEGIN
    -- Предотвращение перезаписи индивидуальных данных из МТ
    IF APP_NAME() = 'ST-Replication' 
       AND CONTEXT_INFO() = @agentRouteCode
    BEGIN
        -- Откат изменений индивидуальных полей
        UPDATE refOutlets 
        SET CreditLimit = d.CreditLimit,
            IsInStopList = d.IsInStopList,
            idClassifier6 = d.idClassifier6,
            CreditDeadline = d.CreditDeadline
        FROM refOutlets o
        INNER JOIN deleted d ON o.id = d.id
        WHERE o.id IN (SELECT id FROM inserted);
    END
END
```

## Интерфейсы МТ

### 1. Отображение данных

#### Карточка ТТ
- **Вкладка "Лимиты"**: Отображение лимитов в разрезе фокусной группы
- **Причина стоп-листа**: Значение классификатора №6

#### Отчет "Долги"
- Фильтрация по маршруту агента
- Отображение только релевантных задолженностей

#### Отчет "Взаиморасчеты"
- Формирование документа ПКО только с документами агента

### 2. Сообщения пользователю

#### Превышение лимита кредита
```
"Превышена сумма кредита на N руб."
```

#### ТТ в стоп-листе
```
"ТТ находится в стоп-листе"
```

## Настройки репликации

### 1. Конфигурационные параметры

#### rpl_SyncTransport.dll.config
```xml
<configuration>
  <appSettings>
    <add key="DataFormat" value="XML" />
    <add key="ExportTXTFields" value="true" />
    <add key="Path" value="C:\Sync.UAT\11_Aquatrade_Balti\" />
  </appSettings>
</configuration>
```

### 2. Переключение формата данных

Для переключения на загрузку TXT-файлов:
1. Установить `DataFormat = 'TXT'`
2. Установить `ExportTXTFields = true` (если файл с заголовками)
3. Перезапустить репликацию
4. TXT-файлы размещать в папке `client`

## Мониторинг и логирование

### 1. Логи репликации

**Расположение:** `Logs\Rpl_{NodeID}_{AppName}_rpl_Core.utf8.dll.txt`

**Ключевые события:**
- Старт/финиш репликации
- Загрузка пакетов данных
- Ошибки синхронизации
- Статистика обработанных записей

### 2. Мониторинг изменений

**Таблица:** `dbo.v_LogDataChange`
- Отслеживание всех изменений данных
- Фильтр по `AppName = 'ST-Replication'`
- Временные метки изменений

## Обработка ошибок

### 1. Типы ошибок

#### Ошибки загрузки данных
- Неверный формат файла
- Отсутствие обязательных полей
- Нарушение ограничений целостности

#### Ошибки синхронизации
- Проблемы с подключением к БД
- Таймауты операций
- Конфликты данных

### 2. Стратегии восстановления

#### Автоматическое восстановление
- Повторные попытки при временных сбоях
- Валидация данных перед загрузкой

#### Ручное восстановление
- Анализ логов для диагностики
- Восстановление из резервных копий
- Ручная корректировка данных
