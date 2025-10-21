# Руководство по развертыванию: Атяшево. ТМА. Выгрузка документов оснований для бонусов в УС

## Обзор развертывания

### Цель развертывания
Развертывание функциональности связывания документов "Начисление бонуса" с документами-основаниями "Заказ" и выгрузки связанных документов в УС дистрибьютора на продуктивном окружении.

### Область развертывания
- База данных Чикаго
- Процедуры связывания документов
- Джоб для связывания документов
- Feature Flag для управления выгрузкой
- Система выгрузки через erwin

## Предварительные требования

### Системные требования
- **SQL Server**: 2016 или выше
- **Память**: Минимум 8 GB RAM
- **Диск**: 50 GB свободного места
- **Сеть**: Стабильное соединение с УС

### Программные требования
- **.NET Framework**: 4.7.2 или выше
- **SQL Server Management Studio**: 18.0 или выше
- **Система erwin**: Для выгрузки файлов

### Доступы и права
- **Администратор БД**: Полные права на базу данных
- **Администратор системы**: Права на установку ПО
- **Администратор erwin**: Права на настройку выгрузки

## Подготовка к развертыванию

### 1. Резервное копирование

#### Создание резервной копии базы данных
```sql
-- Создание полной резервной копии
BACKUP DATABASE ChicagoDB 
TO DISK = 'C:\Backup\ChicagoDB_PreDeployment_' + 
         FORMAT(GETDATE(), 'yyyyMMdd_HHmmss') + '.bak'
WITH FORMAT, INIT, 
     NAME = 'ChicagoDB Pre-Deployment Backup',
     DESCRIPTION = 'Резервная копия перед развертыванием проекта 230345';

-- Создание резервной копии логов
BACKUP LOG ChicagoDB 
TO DISK = 'C:\Backup\ChicagoDB_Log_PreDeployment_' + 
         FORMAT(GETDATE(), 'yyyyMMdd_HHmmss') + '.trn'
WITH FORMAT, INIT,
     NAME = 'ChicagoDB Log Pre-Deployment Backup';
```

#### Проверка целостности резервной копии
```sql
-- Проверка целостности
RESTORE VERIFYONLY 
FROM DISK = 'C:\Backup\ChicagoDB_PreDeployment_[timestamp].bak';
```

### 2. Подготовка скриптов развертывания

**Внимание**: Детальные скрипты развертывания находятся в Pull Request'ах. Для получения реальных скриптов обратитесь к команде разработки.

#### Основные компоненты для развертывания:
1. **Процедуры связывания документов**
2. **Джоб для автоматического связывания**
3. **Настройки Feature Flag**
4. **Конфигурация выгрузки через erwin**

### 3. Подготовка конфигурации

#### Feature Flag
```xml
<!-- Включение выгрузки бонусов в УС -->
<add key="ErwinExportedFileConfigurationByDistributorSettings" value="true" />
```

#### Настройки выгрузки
- **Интервал связывания**: До 10 минут после создания документа
- **Условия выгрузки**: Документы без внешнего кода, с проставленной связью
- **Задержка выгрузки**: 10 минут с момента создания заказа

## Процесс развертывания

### Этап 1: Подготовка окружения

#### 1.1 Проверка системы
```powershell
# Проверка версии SQL Server
sqlcmd -S [SERVER] -Q "SELECT @@VERSION"

# Проверка доступного места на диске
Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, @{Name="Size(GB)";Expression={[math]::Round($_.Size/1GB,2)}}, @{Name="FreeSpace(GB)";Expression={[math]::Round($_.FreeSpace/1GB,2)}}

# Проверка памяти
Get-WmiObject -Class Win32_ComputerSystem | Select-Object TotalPhysicalMemory, @{Name="RAM(GB)";Expression={[math]::Round($_.TotalPhysicalMemory/1GB,2)}}
```

#### 1.2 Создание пользователей и ролей
```sql
-- Создание роли для процедур связывания
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'BonusLinkingRole')
BEGIN
    CREATE ROLE [BonusLinkingRole];
END
GO

-- Предоставление прав на выполнение процедур
GRANT EXECUTE ON [dbo].[sp_LinkBonusToOrder] TO [BonusLinkingRole];
GRANT EXECUTE ON [dbo].[sp_ExportBonusToUS] TO [BonusLinkingRole];

-- Предоставление прав на чтение таблиц
GRANT SELECT ON [dbo].[Orders] TO [BonusLinkingRole];
GRANT SELECT ON [dbo].[BonusIssued] TO [BonusLinkingRole];
GRANT SELECT ON [dbo].[rgPromoGoods] TO [BonusLinkingRole];
```

### Этап 2: Развертывание базы данных

#### 2.1 Выполнение скриптов БД
**Внимание**: Реальные скрипты находятся в Pull Request'ах. Используйте скрипты из PR.

```powershell
# Выполнение скрипта создания процедур
sqlcmd -S [SERVER] -d ChicagoDB -i ".\Scripts\CreateProcedures.sql" -o ".\Logs\CreateProcedures.log"

# Выполнение скрипта создания джоба
sqlcmd -S [SERVER] -d ChicagoDB -i ".\Scripts\CreateJob.sql" -o ".\Logs\CreateJob.log"
```

#### 2.2 Проверка развертывания БД
```sql
-- Проверка создания процедур
SELECT ROUTINE_NAME 
FROM INFORMATION_SCHEMA.ROUTINES 
WHERE ROUTINE_NAME IN ('sp_LinkBonusToOrder', 'sp_ExportBonusToUS');

-- Проверка создания джоба
SELECT name, enabled, description 
FROM msdb.dbo.sysjobs 
WHERE name LIKE '%Bonus%';
```

### Этап 3: Настройка джоба

#### 3.1 Создание джоба SQL Server Agent
**Внимание**: Детальная настройка джоба находится в Pull Request'ах.

```sql
-- Создание задания для связывания документов
EXEC dbo.sp_add_job
    @job_name = 'LinkBonusToOrder_Job',
    @enabled = 1,
    @description = 'Автоматическое связывание бонусных документов с заказами',
    @owner_login_name = 'sa';

-- Добавление шага задания
EXEC dbo.sp_add_jobstep
    @job_name = 'LinkBonusToOrder_Job',
    @step_name = 'LinkBonusStep',
    @command = 'EXEC sp_LinkBonusToOrder',
    @database_name = 'ChicagoDB',
    @on_success_action = 1,
    @on_fail_action = 2;

-- Настройка расписания (каждые 5 минут)
EXEC dbo.sp_add_schedule
    @schedule_name = 'LinkBonusSchedule',
    @freq_type = 4, -- Ежедневно
    @freq_interval = 1,
    @freq_subday_type = 4, -- Минуты
    @freq_subday_interval = 5,
    @active_start_time = 000000;

-- Привязка расписания к заданию
EXEC dbo.sp_attach_schedule
    @job_name = 'LinkBonusToOrder_Job',
    @schedule_name = 'LinkBonusSchedule';
```

### Этап 4: Настройка Feature Flag

#### 4.1 Включение Feature Flag
```xml
<!-- app.config или web.config -->
<appSettings>
  <add key="ErwinExportedFileConfigurationByDistributorSettings" value="true" />
</appSettings>
```

#### 4.2 Проверка работы Feature Flag
```sql
-- Проверка настроек Feature Flag
SELECT * FROM Settings WHERE Key = 'ErwinExportedFileConfigurationByDistributorSettings';
```

### Этап 5: Настройка выгрузки через erwin

#### 5.1 Настройка папки erwin
- Создать папку для выгрузки файлов
- Настроить права доступа
- Проверить доступность папки

#### 5.2 Настройка интеграции с УС
- Настроить подключение к УС
- Проверить доступность УС
- Настроить формат выгружаемых файлов

## Тестирование развертывания

### 1. Функциональное тестирование

#### Тест 1: Проверка процедур
```sql
-- Тест процедуры связывания
EXEC sp_LinkBonusToOrder;

-- Проверка результатов
SELECT COUNT(*) as ProcessedCount
FROM LinkBonusLog 
WHERE ProcessDate >= DATEADD(hour, -1, GETDATE());
```

#### Тест 2: Проверка джоба
```sql
-- Запуск джоба связывания
EXEC msdb.dbo.sp_start_job 'LinkBonusToOrder_Job';

-- Проверка статуса джоба
SELECT 
    j.name as JobName,
    ja.run_requested_date,
    ja.run_requested_source,
    ja.last_run_outcome
FROM msdb.dbo.sysjobs j
LEFT JOIN msdb.dbo.sysjobactivity ja ON j.job_id = ja.job_id
WHERE j.name = 'LinkBonusToOrder_Job';
```

### 2. Тестирование Feature Flag

#### Тест 3: Проверка выключения ФФ
1. Выключить Feature Flag
2. Создать тестовые документы
3. Проверить, что выгрузка не происходит
4. Включить Feature Flag
5. Проверить, что выгрузка возобновилась

### 3. Интеграционное тестирование

#### Тест 4: Полный цикл
1. Создать заказ в МТ
2. Дождаться создания начисления бонуса
3. Выполнить обмен данными
4. Дождаться срабатывания джоба
5. Проверить выгрузку в папку erwin
6. Проверить отправку в УС

## Мониторинг и поддержка

### Ключевые метрики для мониторинга

#### 1. Производительность
- Время выполнения процедур связывания
- Количество обработанных документов
- Процент успешных операций

#### 2. Качество данных
- Процент связанных документов
- Количество ошибок связывания
- Целостность данных

#### 3. Системные ресурсы
- Использование CPU
- Использование памяти
- Использование диска

### Алерты и уведомления

#### Настройка алертов
```sql
-- Создание алерта на ошибки
EXEC msdb.dbo.sp_add_alert
    @name = 'BonusLinking_Error_Alert',
    @enabled = 1,
    @delay_between_responses = 60,
    @include_event_description_in = 1;

-- Создание оператора для уведомлений
EXEC msdb.dbo.sp_add_operator
    @name = 'DBA_Team',
    @email_address = 'dba@company.com',
    @enabled = 1;

-- Привязка алерта к оператору
EXEC msdb.dbo.sp_add_notification
    @alert_name = 'BonusLinking_Error_Alert',
    @operator_name = 'DBA_Team',
    @notification_method = 1; -- Email
```

## Откат изменений

### План отката

#### 1. Остановка джоба
```sql
-- Остановка джоба связывания
EXEC msdb.dbo.sp_stop_job 'LinkBonusToOrder_Job';
```

#### 2. Выключение Feature Flag
```xml
<!-- Выключение выгрузки бонусов в УС -->
<add key="ErwinExportedFileConfigurationByDistributorSettings" value="false" />
```

#### 3. Удаление объектов БД
```sql
-- Удаление джоба
EXEC msdb.dbo.sp_delete_job @job_name = 'LinkBonusToOrder_Job';

-- Удаление процедур
DROP PROCEDURE IF EXISTS [dbo].[sp_LinkBonusToOrder];
DROP PROCEDURE IF EXISTS [dbo].[sp_ExportBonusToUS];
```

#### 4. Восстановление из резервной копии
```sql
-- Восстановление базы данных
RESTORE DATABASE ChicagoDB 
FROM DISK = 'C:\Backup\ChicagoDB_PreDeployment_[timestamp].bak'
WITH REPLACE, RECOVERY;
```

## Контакты и поддержка

### Команда развертывания
- **Руководитель развертывания**: [имя, контакты]
- **Администратор БД**: [имя, контакты]
- **Администратор системы**: [имя, контакты]

### Эскалация проблем
- **Критические проблемы**: [контакты]
- **Обычные проблемы**: [контакты]
- **Вопросы**: [контакты]

### Документация
- **Техническая документация**: [ссылка на PR]
- **Руководство пользователя**: [ссылка]
- **FAQ**: [ссылка]

---
**Важное замечание**: Данное руководство основано на информации из TFS. Для получения детальных скриптов развертывания обратитесь к Pull Request'ам в репозитории кода.

*Документ создан: 27.09.2025*  
*Версия: 1.0*  
*Статус: Готово к проду*
