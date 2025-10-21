# Техническое решение: АкваТрейд. В МТ разделить долги ТТ по маршрутам

## Обзор решения

### Цель
Реализовать разделение долгов торговых точек по маршрутам в мобильном терминале с учетом фокусных групп агентов.

### Архитектура системы
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   УС (Учетная   │───▶│   Чикаго (БД)   │───▶│   МТ (Мобильный │
│    система)     │    │                 │    │    терминал)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
   Выгрузка данных        Репликация данных      Отображение долгов
   с idRoute             в разрезе ФГ           в разрезе маршрута
```

## Компоненты решения

### 1. База данных Чикаго

#### Новая таблица: `refOutletFocusGroups`
```sql
CREATE TABLE refOutletFocusGroups (
    id INT IDENTITY(1,1) PRIMARY KEY,
    outercode NVARCHAR(50) NOT NULL,           -- Внешний код для репликации
    Outlet INT NOT NULL,                       -- ID торговой точки
    FG NVARCHAR(50) NOT NULL,                  -- Код фокусной группы
    CreditLimit DECIMAL(18,2),                 -- Лимит кредита
    IsInStopList BIT DEFAULT 0,                -- Признак стоп-листа
    CreditDeadLine INT,                        -- Срок кредита (дней)
    classifier6code NVARCHAR(50),              -- Код классификатора 6
    deleted BIT DEFAULT 0,                     -- Признак удаления
    verstamp TIMESTAMP,                        -- Версионность
    created_date DATETIME DEFAULT GETDATE(),
    updated_date DATETIME DEFAULT GETDATE()
);
```

#### Модификация регистра задолженностей
Добавлено поле `idRoute` в таблицу `rgReceivables` для связи долгов с маршрутами.

### 2. Репликация данных

#### Конфигурационные файлы
1. **BusinessObjects.xml** - описание бизнес-объектов
2. **ReplicationRules.xml** - правила репликации
3. **SyncProtocolRules_1_2_1.xml** - протокол синхронизации
4. **MappingRule_1_2_1.xml** - правила маппинга данных

#### Формат данных из УС
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

### 3. Выгрузка в МТ

#### Модификация серийной таблицы `refOutlets`
Добавлены поля для работы с фокусными группами:
- `LimitCredit` - лимит кредита
- `IsInStopList` - признак стоп-листа
- `CreditDeadline` - срок кредита
- `idClassifier6` - код классификатора 6

#### Логика выгрузки
```sql
-- Выборка данных в разрезе фокусной группы агента
SELECT 
    o.Outlet,
    fg.CreditLimit,
    fg.IsInStopList,
    fg.CreditDeadLine,
    fg.classifier6code
FROM refOutlets o
LEFT JOIN refOutletFocusGroups fg ON o.Outlet = fg.Outlet
WHERE fg.FG = @AgentFocusGroup
```

### 4. Мобильный терминал

#### Новые поля в БД МТ
- `refOutlets.LimitCredit` - лимит кредита
- `refOutlets.IsInStopList` - признак стоп-листа
- `refOutlets.CreditDeadline` - срок кредита
- `refOutlets.idClassifier6` - код классификатора 6

#### Логика проверки лимитов
```csharp
// Проверка превышения лимита кредита
if (currentDebt > creditLimit && !allowExceedCredit)
{
    ShowMessage("Превышена сумма кредита");
    return false;
}

// Проверка стоп-листа
if (isInStopList)
{
    ShowMessage("ТТ находится в стоп-листе");
    return false;
}
```

## Алгоритм работы

### 1. Загрузка данных из УС
1. УС формирует файл с данными о лимитах по фокусным группам
2. Репликация загружает данные в таблицу `refOutletFocusGroups`
3. Данные обновляются по полю `outercode`

### 2. Выгрузка в МТ
1. При обмене данными агент получает лимиты только своей фокусной группы
2. Данные записываются в серийную таблицу `refOutlets`
3. При изменении в МТ данные возвращаются в Чикаго

### 3. Работа в МТ
1. При создании заказа проверяется лимит кредита в разрезе ФГ
2. При превышении лимита выводится сообщение и запрещается создание заказа
3. В карточке ТТ отображается причина постановки в стоп-лист

## Обработка данных

### Триггер для предотвращения перезаписи
```sql
CREATE TRIGGER tr_refOutlets_PreventOverwrite
ON refOutlets
FOR UPDATE
AS
BEGIN
    -- Если изменения из МТ (app_name = 'ST-Replication' и context_info содержит код маршрута)
    IF APP_NAME() = 'ST-Replication' 
       AND CONTEXT_INFO() LIKE '%маршрут%'
    BEGIN
        -- Откатываем изменения полей фокусных групп
        UPDATE refOutlets 
        SET CreditLimit = d.CreditLimit,
            IsInStopList = d.IsInStopList,
            CreditDeadline = d.CreditDeadline,
            idClassifier6 = d.idClassifier6
        FROM refOutlets o
        INNER JOIN deleted d ON o.Outlet = d.Outlet
        WHERE o.Outlet IN (SELECT Outlet FROM inserted);
    END
END
```

### Логика разделения долгов
```sql
-- Получение долгов в разрезе маршрута агента
SELECT 
    r.Outlet,
    r.Amount,
    r.idRoute
FROM rgReceivables r
WHERE r.idRoute = @AgentRouteId
  AND r.Outlet IN (
      SELECT o.Outlet 
      FROM refOutlets o 
      WHERE o.FocusGroup = @AgentFocusGroup
  )
```

## Конфигурация

### Настройки репликации
- **Путь к конфигам**: `C:\Application\REPLICATION\AquaTrade\Replication.Shuttle\UAT\3.6.178.1`
- **UI для настройки**: `C:\Ansible\Applications\AquaTrade\UAT\Replication.Shuttle\3.6.178.1\release\rpl_GUI.exe`
- **Служба**: `Replication.Shuttle.AquaTrade.UAT`

### Параметры запуска
```bash
-action=get -det=synchronization -group=ImportRefs -contextNodeID=2
```

### Настройки формата данных
- **XML формат**: `DataFormat = 'XML'` (по умолчанию)
- **TXT формат**: `DataFormat = 'TXT'` (для текстовых файлов)
- **Заголовки в TXT**: `ExportTXTFields = true`

## Мониторинг и логирование

### Логи репликации
- **Путь**: `Logs\Rpl_{NodeID}_STRplShuttle-Test_rpl_Core.utf8.dll.txt`
- **Содержание**: Процесс загрузки, ошибки, статистика

### Проверка данных
```sql
-- Проверка загруженных данных
SELECT * FROM refOutletFocusGroups;

-- Проверка изменений
SELECT * FROM dbo.v_LogDataChange 
WHERE ChangeDate >= '20250911' 
  AND AppName = 'ST-Replication' 
ORDER BY ChangeDate;
```

## Требования к окружению

### Минимальные версии
- **МТ**: 3.6.205.4 или выше
- **Чикаго**: текущая версия
- **Репликация**: 3.6.178.1

### Зависимости
- SQL Server (для Чикаго)
- .NET Framework (для репликации)
- Мобильная платформа (для МТ)

## Безопасность

### Разграничение доступа
- Агенты видят только данные своей фокусной группы
- Данные фильтруются по `idRoute` агента
- Проверка прав доступа на уровне БД

### Аудит изменений
- Логирование всех изменений в `v_LogDataChange`
- Отслеживание источника изменений (УС/МТ)
- Версионность данных через `verstamp`

## Производительность

### Оптимизации
- Индексы на ключевые поля (`Outlet`, `FG`, `idRoute`)
- Пакетная обработка данных
- Кэширование лимитов в МТ

### Мониторинг
- Время выполнения репликации
- Объем передаваемых данных
- Частота обновлений

## Обработка ошибок

### Типичные ошибки
1. **Ошибка загрузки данных**: Проверка формата файла и структуры
2. **Ошибка репликации**: Проверка конфигурации и доступности сервисов
3. **Ошибка выгрузки в МТ**: Проверка версии МТ и совместимости

### Восстановление
- Автоматический откат при критических ошибках
- Ручное восстановление через административные процедуры
- Резервное копирование конфигураций

## Тестирование

### Автоматические тесты
- Проверка корректности загрузки данных
- Валидация бизнес-логики
- Тестирование производительности

### Ручное тестирование
- Сценарии работы агентов
- Проверка граничных условий
- Тестирование интеграции

## Развертывание

### Этапы развертывания
1. **Подготовка БД**: Создание таблиц и индексов
2. **Настройка репликации**: Конфигурация файлов
3. **Обновление МТ**: Установка новой версии
4. **Тестирование**: Проверка функционала
5. **Продакшен**: Переключение на новую версию

### Откат
- Возможность отката к предыдущей версии
- Сохранение совместимости с старыми данными
- План восстановления в случае проблем

---
*Документ создан: 26.09.2025*  
*Версия: 1.0*  
*Статус: Готово к реализации*
