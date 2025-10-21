# Руководство по развертыванию: АкваТрейд. В МТ разделить долги ТТ по маршрутам

## Обзор развертывания

### Цель
Обеспечить корректное развертывание функционала разделения долгов по маршрутам в производственной среде.

### Компоненты для развертывания
1. **База данных Чикаго** - создание таблиц и индексов
2. **Репликация** - настройка конфигурационных файлов
3. **Мобильный терминал** - обновление до версии 3.6.205.4+
4. **Функциональные флаги** - включение нового функционала

## Предварительные требования

### Системные требования
- **SQL Server**: Версия 2016 или выше
- **.NET Framework**: 4.7.2 или выше
- **Память**: Минимум 4 GB RAM
- **Дисковое пространство**: 10 GB свободного места

### Доступы и права
- **Администратор БД**: Для создания таблиц и индексов
- **Администратор репликации**: Для настройки конфигураций
- **Администратор МТ**: Для обновления мобильных терминалов
- **Пользователь УС**: Для настройки выгрузки данных

### Резервное копирование
- Создать полную резервную копию БД Чикаго
- Сохранить текущие конфигурации репликации
- Создать точку восстановления системы

## Этапы развертывания

### Этап 1: Подготовка базы данных

#### 1.1 Создание таблицы refOutletFocusGroups
```sql
-- Создание таблицы для хранения лимитов по фокусным группам
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

-- Создание индексов для оптимизации
CREATE INDEX IX_refOutletFocusGroups_Outlet ON refOutletFocusGroups(Outlet);
CREATE INDEX IX_refOutletFocusGroups_FG ON refOutletFocusGroups(FG);
CREATE INDEX IX_refOutletFocusGroups_outercode ON refOutletFocusGroups(outercode);
```

#### 1.2 Модификация таблицы rgReceivables
```sql
-- Добавление поля idRoute в регистр задолженностей
ALTER TABLE rgReceivables 
ADD idRoute INT NULL;

-- Создание индекса для оптимизации
CREATE INDEX IX_rgReceivables_idRoute ON rgReceivables(idRoute);
```

#### 1.3 Создание триггера для предотвращения перезаписи
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

### Этап 2: Настройка репликации

#### 2.1 Подготовка конфигурационных файлов

**Путь к конфигурациям**: `C:\Application\REPLICATION\AquaTrade\Replication.Shuttle\UAT\3.6.178.1`

##### BusinessObjects.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<BusinessObjects>
  <BusinessObject Name="FocusGroups" TableName="refOutletFocusGroups">
    <Fields>
      <Field Name="id" Type="Int32" IsPrimaryKey="true" />
      <Field Name="outercode" Type="String" Length="50" />
      <Field Name="Outlet" Type="Int32" />
      <Field Name="FG" Type="String" Length="50" />
      <Field Name="CreditLimit" Type="Decimal" />
      <Field Name="IsInStopList" Type="Boolean" />
      <Field Name="CreditDeadLine" Type="Int32" />
      <Field Name="classifier6code" Type="String" Length="50" />
      <Field Name="deleted" Type="Boolean" />
      <Field Name="verstamp" Type="Timestamp" />
    </Fields>
  </BusinessObject>
</BusinessObjects>
```

##### ReplicationRules.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<ReplicationRules>
  <Rule Name="ImportRefs" Group="ImportRefs">
    <BusinessObject Name="FocusGroups" />
  </Rule>
</ReplicationRules>
```

##### SyncProtocolRules_1_2_1.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<SyncProtocolRules>
  <Rule Name="FocusGroups" 
        BusinessObject="FocusGroups" 
        Action="Import" 
        Group="ImportRefs" />
</SyncProtocolRules>
```

##### MappingRule_1_2_1.xml
```xml
<?xml version="1.0" encoding="utf-8"?>
<MappingRules>
  <Rule SourceTable="refOutletFocusGroups" 
        TargetTable="refOutletFocusGroups" 
        BusinessObject="FocusGroups" />
</MappingRules>
```

#### 2.2 Настройка через UI
1. Запустить `rpl_GUI.exe`
2. Открыть файл `ReplicationRules.xml`
3. Настроить правила репликации
4. Сохранить конфигурацию

#### 2.3 Настройка параметров
**Файл**: `rpl_SyncTransport.dll.config`
```xml
<configuration>
  <appSettings>
    <add key="DataFormat" value="XML" />
    <add key="ExportTXTFields" value="false" />
    <add key="Path" value="d:\Sync.UAT\{NodeID}_Aquatrade_Balti\" />
  </appSettings>
</configuration>
```

### Этап 3: Обновление мобильного терминала

#### 3.1 Требования к версии
- **Минимальная версия**: 3.6.205.4
- **Рекомендуемая версия**: Последняя стабильная

#### 3.2 Процедура обновления
1. **Подготовка**:
   - Создать резервную копию текущей версии МТ
   - Сохранить пользовательские настройки
   - Проверить совместимость с ОС

2. **Установка**:
   - Запустить установщик новой версии
   - Следовать инструкциям мастера установки
   - Проверить корректность установки

3. **Настройка**:
   - Настроить подключение к серверу
   - Проверить права доступа
   - Выполнить первичную синхронизацию

#### 3.3 Проверка обновления
```sql
-- Проверка версии МТ в БД
SELECT TOP 1 Version FROM MobileTerminalInfo 
ORDER BY LastSyncDate DESC;
```

### Этап 4: Включение функционального флага

#### 4.1 Настройка в УС
1. Войти в систему управления функциональными флагами
2. Найти флаг "Задолженности, лимиты и срок кредита в разрезах фокусных групп"
3. Установить значение "Включен"
4. Сохранить изменения

#### 4.2 Проверка активации
```sql
-- Проверка статуса функционального флага
SELECT * FROM FunctionalFlags 
WHERE FlagName = 'Задолженности, лимиты и срок кредита в разрезах фокусных групп';
```

### Этап 5: Настройка выгрузки данных из УС

#### 5.1 Формат выгружаемых данных
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
      <classifier6code>Причина постановки в стоп-лист</classifier6code>
    </Group>
  </FocusGroups>
</REFERENCES>
```

#### 5.2 Настройка расписания выгрузки
- **Частота**: Ежедневно в 02:00
- **Формат файла**: XML
- **Путь выгрузки**: `d:\Sync.UAT\{NodeID}_Aquatrade_Balti\`
- **Имя файла**: `references.xml`

## Мониторинг развертывания

### Логи для отслеживания
1. **Логи репликации**: `Logs\Rpl_{NodeID}_STRplShuttle-Test_rpl_Core.utf8.dll.txt`
2. **Логи МТ**: `logs\app.log`
3. **Логи БД**: `dbo.v_LogDataChange`

### Ключевые метрики
- **Время загрузки данных**: < 5 минут
- **Количество обработанных записей**: Соответствует выгруженным данным
- **Ошибки в логах**: Отсутствие критических ошибок
- **Производительность МТ**: Время отклика < 2 секунд

### Команды для проверки
```sql
-- Проверка загруженных данных
SELECT COUNT(*) as total_records FROM refOutletFocusGroups;

-- Проверка последних изменений
SELECT TOP 10 * FROM dbo.v_LogDataChange 
WHERE AppName = 'ST-Replication' 
ORDER BY ChangeDate DESC;

-- Проверка ошибок
SELECT * FROM ErrorLog 
WHERE LogDate >= DATEADD(day, -1, GETDATE())
ORDER BY LogDate DESC;
```

## Откат изменений

### Процедура отката
1. **Отключение функционального флага**:
   - Установить значение "Отключен"
   - Перезапустить репликацию

2. **Откат БД**:
   - Восстановить из резервной копии
   - Проверить целостность данных

3. **Откат МТ**:
   - Установить предыдущую версию
   - Восстановить настройки

4. **Откат конфигураций**:
   - Восстановить старые файлы конфигурации
   - Перезапустить службы

### Критерии для отката
- Критические ошибки в работе системы
- Потеря данных
- Неприемлемая производительность
- Несовместимость с существующими процессами

## План развертывания

### Подготовительный этап (1 день)
- [ ] Создание резервных копий
- [ ] Подготовка конфигурационных файлов
- [ ] Тестирование на тестовом окружении
- [ ] Уведомление пользователей

### Основной этап (4 часа)
- [ ] Создание таблиц в БД (30 мин)
- [ ] Настройка репликации (1 час)
- [ ] Обновление МТ (1 час)
- [ ] Включение функционального флага (30 мин)
- [ ] Первичная загрузка данных (1 час)

### Контрольный этап (2 часа)
- [ ] Проверка работы всех компонентов
- [ ] Мониторинг логов
- [ ] Тестирование ключевых сценариев
- [ ] Документирование результатов

## Контакты и поддержка

### Команда развертывания
- **Руководитель**: Авдеева Галина
- **Администратор БД**: [Имя администратора БД]
- **Администратор репликации**: Сунко Марина
- **Администратор МТ**: [Имя администратора МТ]

### Экстренные контакты
- **Техническая поддержка**: +7-XXX-XXX-XXXX
- **Горячая линия**: support@company.com
- **Чат поддержки**: [Ссылка на чат]

### Документация для справки
- [Техническое решение](TECHNICAL_SOLUTION_219908.md)
- [Руководство по тестированию](TESTING_GUIDE_219908.md)
- [Пользовательская документация](USER_GUIDE_219908.md)

## Чек-лист развертывания

### Предварительные проверки
- [ ] Резервные копии созданы
- [ ] Тестовое окружение проверено
- [ ] Все компоненты совместимы
- [ ] Пользователи уведомлены
- [ ] План отката подготовлен

### Развертывание
- [ ] Таблицы БД созданы
- [ ] Индексы созданы
- [ ] Триггеры установлены
- [ ] Конфигурации репликации настроены
- [ ] МТ обновлен
- [ ] Функциональный флаг включен
- [ ] Первичная загрузка выполнена

### Проверки после развертывания
- [ ] Логи не содержат критических ошибок
- [ ] Данные загружаются корректно
- [ ] МТ работает стабильно
- [ ] Функционал работает согласно требованиям
- [ ] Производительность в пределах нормы

### Завершение
- [ ] Документация обновлена
- [ ] Пользователи обучены
- [ ] Мониторинг настроен
- [ ] План поддержки активирован

---
*Документ создан: 26.09.2025*  
*Версия: 1.0*  
*Статус: Готов к использованию*
