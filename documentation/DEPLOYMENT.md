# Развертывание и настройка

## Обзор

Данный документ содержит инструкции по развертыванию и настройке системы разделения долгов ТТ по маршрутам в проекте АкваТрейд.

## Требования к системе

### 1. Аппаратные требования

#### Сервер базы данных (Чикаго)
- **CPU**: 8+ ядер
- **RAM**: 32+ GB
- **Диск**: SSD 500+ GB
- **Сеть**: 1 Gbps

#### Сервер репликации
- **CPU**: 4+ ядер
- **RAM**: 16+ GB
- **Диск**: SSD 200+ GB
- **Сеть**: 1 Gbps

#### Мобильные терминалы
- **CPU**: 2+ ядер
- **RAM**: 4+ GB
- **Диск**: 32+ GB
- **Сеть**: 4G/WiFi

### 2. Программные требования

#### База данных
- **SQL Server**: 2019 или выше
- **Версия**: Enterprise/Standard
- **Совместимость**: 150+

#### Репликация
- **Replication.Shuttle**: 3.6.205.4
- **.NET Framework**: 4.8+
- **Windows Server**: 2019 или выше

#### Мобильные терминалы
- **Windows**: 10 или выше
- **.NET Framework**: 4.8+
- **Версия МТ**: 3.6.205.4+

## Установка компонентов

### 1. Установка Replication.Shuttle

#### Шаг 1: Подготовка директорий
```powershell
# Создание основных директорий
New-Item -ItemType Directory -Path "C:\Application\REPLICATION\AquaTrade\Replication.Shuttle\UAT\3.6.205.4" -Force
New-Item -ItemType Directory -Path "C:\Ansible\Applications\AquaTrade\UAT\Replication.Shuttle\3.6.205.4\release" -Force
New-Item -ItemType Directory -Path "C:\Sync.UAT\11_Aquatrade_Balti" -Force
```

#### Шаг 2: Копирование файлов
```powershell
# Копирование исполняемых файлов
Copy-Item -Path "\\server\replication\3.6.205.4\*" -Destination "C:\Application\REPLICATION\AquaTrade\Replication.Shuttle\UAT\3.6.205.4\" -Recurse
Copy-Item -Path "\\server\replication\3.6.205.4\release\*" -Destination "C:\Ansible\Applications\AquaTrade\UAT\Replication.Shuttle\3.6.205.4\release\" -Recurse
```

#### Шаг 3: Установка службы
```powershell
# Установка службы репликации
sc.exe create "Replication.Shuttle.AquaTrade.UAT" binPath="C:\Application\REPLICATION\AquaTrade\Replication.Shuttle\UAT\3.6.205.4\rpl_client.exe" start=auto
```

### 2. Настройка базы данных

#### Шаг 1: Создание базы данных
```sql
-- Создание базы данных
CREATE DATABASE [AquaTrade_UAT]
ON (NAME = 'AquaTrade_UAT', FILENAME = 'C:\Data\AquaTrade_UAT.mdf')
LOG ON (NAME = 'AquaTrade_UAT_Log', FILENAME = 'C:\Data\AquaTrade_UAT_Log.ldf');
```

#### Шаг 2: Выполнение скриптов создания таблиц
```sql
-- Выполнение скриптов из DATABASE.md
-- Создание таблиц, индексов, триггеров, хранимых процедур
```

#### Шаг 3: Настройка пользователей
```sql
-- Создание пользователя для репликации
CREATE LOGIN [STRplShuttle-Test] WITH PASSWORD = 'SecurePassword123!';
USE [AquaTrade_UAT];
CREATE USER [STRplShuttle-Test] FOR LOGIN [STRplShuttle-Test];
ALTER ROLE [db_datareader] ADD MEMBER [STRplShuttle-Test];
ALTER ROLE [db_datawriter] ADD MEMBER [STRplShuttle-Test];
```

## Конфигурация репликации

### 1. Настройка BusinessObjects.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<BusinessObjects>
  <BusinessObject name="FocusGroups">
    <Table name="refOutletFocusGroups">
      <Field name="id" type="int" isIdentity="true" />
      <Field name="outercode" type="string" length="100" />
      <Field name="Outlet" type="int" />
      <Field name="FG" type="string" length="50" />
      <Field name="CreditLimit" type="decimal" precision="18" scale="2" />
      <Field name="IsInStopList" type="bit" />
      <Field name="CreditDeadLine" type="int" />
      <Field name="classifier6code" type="string" length="100" />
      <Field name="CreatedDate" type="datetime2" />
      <Field name="UpdatedDate" type="datetime2" />
      <Field name="deleted" type="bit" />
      <Field name="verstamp" type="timestamp" />
    </Table>
  </BusinessObject>
  
  <BusinessObject name="Receivables">
    <Table name="rgReceivables">
      <Field name="id" type="int" isIdentity="true" />
      <Field name="idroute" type="int" />
      <Field name="OutletCode" type="string" length="50" />
      <Field name="DebtAmount" type="decimal" precision="18" scale="2" />
      <Field name="CurrencyCode" type="string" length="3" />
      <Field name="CreatedDate" type="datetime2" />
      <Field name="UpdatedDate" type="datetime2" />
      <Field name="deleted" type="bit" />
      <Field name="verstamp" type="timestamp" />
    </Table>
  </BusinessObject>
</BusinessObjects>
```

### 2. Настройка ReplicationRules.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<ReplicationRules>
  <!-- Загрузка данных из УС -->
  <Rule name="ImportFromUS">
    <Source type="File" path="C:\Sync.UAT\11_Aquatrade_Balti" />
    <Target type="Database" connectionString="Data Source=localhost;Initial Catalog=AquaTrade_UAT;Integrated Security=true" />
    <BusinessObjects>
      <BusinessObject name="FocusGroups" />
      <BusinessObject name="Receivables" />
    </BusinessObjects>
    <Schedule>0 2 * * *</Schedule> <!-- Ежедневно в 2:00 -->
  </Rule>
  
  <!-- Выгрузка данных в МТ -->
  <Rule name="ExportToMT">
    <Source type="Database" connectionString="Data Source=localhost;Initial Catalog=AquaTrade_UAT;Integrated Security=true" />
    <Target type="File" path="C:\Sync.UAT\11_Aquatrade_Balti\MT" />
    <BusinessObjects>
      <BusinessObject name="FocusGroups" />
      <BusinessObject name="Receivables" />
    </BusinessObjects>
    <Filter>idroute = @agentRoute</Filter>
  </Rule>
</ReplicationRules>
```

### 3. Настройка SyncProtocolRules_1_2_1.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<SyncProtocolRules version="1.2.1">
  <Rule name="FocusGroupsSync">
    <Source>US</Source>
    <Target>Chicago</Target>
    <Protocol>XML</Protocol>
    <Mapping>MappingRule_1_2_1.xml</Mapping>
    <Schedule>0 2 * * *</Schedule>
  </Rule>
  
  <Rule name="ReceivablesSync">
    <Source>US</Source>
    <Target>Chicago</Target>
    <Protocol>XML</Protocol>
    <Filter>idroute IS NOT NULL</Filter>
    <Schedule>0 2 * * *</Schedule>
  </Rule>
  
  <Rule name="MTDataSync">
    <Source>Chicago</Source>
    <Target>MT</Target>
    <Protocol>XML</Protocol>
    <Filter>idroute = @agentRoute</Filter>
    <Schedule>0 */4 * * *</Schedule> <!-- Каждые 4 часа -->
  </Rule>
</SyncProtocolRules>
```

### 4. Настройка MappingRule_1_2_1.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<MappingRules version="1.2.1">
  <Mapping name="US_FocusGroups_to_Chicago">
    <Source>
      <Table name="FocusGroups" />
      <Field name="outercode" />
      <Field name="Outlet" />
      <Field name="FG" />
      <Field name="CreditLimit" />
      <Field name="IsInStopList" />
      <Field name="CreditDeadLine" />
      <Field name="classifier6code" />
    </Source>
    <Target>
      <Table name="refOutletFocusGroups" />
      <Field name="outercode" />
      <Field name="Outlet" />
      <Field name="FG" />
      <Field name="CreditLimit" />
      <Field name="IsInStopList" />
      <Field name="CreditDeadLine" />
      <Field name="classifier6code" />
    </Target>
    <Key>outercode</Key>
  </Mapping>
  
  <Mapping name="US_Receivables_to_Chicago">
    <Source>
      <Table name="Receivables" />
      <Field name="idroute" />
      <Field name="OutletCode" />
      <Field name="DebtAmount" />
      <Field name="CurrencyCode" />
    </Source>
    <Target>
      <Table name="rgReceivables" />
      <Field name="idroute" />
      <Field name="OutletCode" />
      <Field name="DebtAmount" />
      <Field name="CurrencyCode" />
    </Target>
    <Key>idroute, OutletCode</Key>
  </Mapping>
</MappingRules>
```

### 5. Настройка rpl_SyncTransport.dll.config

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <appSettings>
    <!-- Формат данных -->
    <add key="DataFormat" value="XML" />
    <add key="ExportTXTFields" value="true" />
    
    <!-- Пути -->
    <add key="Path" value="C:\Sync.UAT\11_Aquatrade_Balti\" />
    <add key="LogPath" value="C:\Application\REPLICATION\AquaTrade\Replication.Shuttle\UAT\3.6.205.4\Logs\" />
    
    <!-- Настройки подключения -->
    <add key="ConnectionString" value="Data Source=localhost;Initial Catalog=AquaTrade_UAT;Integrated Security=true" />
    
    <!-- Настройки производительности -->
    <add key="BatchSize" value="1000" />
    <add key="Timeout" value="300" />
    <add key="RetryCount" value="3" />
  </appSettings>
  
  <connectionStrings>
    <add name="DefaultConnection" 
         connectionString="Data Source=localhost;Initial Catalog=AquaTrade_UAT;Integrated Security=true" 
         providerName="System.Data.SqlClient" />
  </connectionStrings>
</configuration>
```

## Настройка функциональных флагов

### 1. Включение ФФ через UI

```powershell
# Запуск UI для настройки
Start-Process "C:\Ansible\Applications\AquaTrade\UAT\Replication.Shuttle\3.6.205.4\release\rpl_GUI.exe"
```

### 2. Включение ФФ через конфигурацию

```xml
<!-- В ReplicationRules.xml -->
<Rule name="FocusGroupsFeature">
  <FeatureFlag name="FocusGroupsDebtsByRoute" value="true" />
  <FeatureFlag name="StopListByFocusGroup" value="true" />
</Rule>
```

## Развертывание на МТ

### 1. Подготовка МТ

```powershell
# Создание директории для данных МТ
New-Item -ItemType Directory -Path "C:\MT\Data" -Force
New-Item -ItemType Directory -Path "C:\MT\Logs" -Force
```

### 2. Настройка подключения к репликации

```xml
<!-- В конфигурации МТ -->
<configuration>
  <appSettings>
    <add key="ReplicationServer" value="replication-server.company.com" />
    <add key="AgentRoute" value="1000001" />
    <add key="FocusGroup" value="FG1234" />
    <add key="SyncInterval" value="240" /> <!-- 4 часа в минутах -->
  </appSettings>
</configuration>
```

### 3. Первоначальная загрузка данных

```powershell
# Выполнение полной загрузки
& "C:\MT\Replication\rpl_client.exe" -action=get -det=synchronization -group=Ref_AQ_Only -contextNodeID=11
```

## Мониторинг и обслуживание

### 1. Настройка мониторинга

```powershell
# Создание задачи для мониторинга логов
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\Scripts\MonitorReplication.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM
Register-ScheduledTask -TaskName "MonitorReplication" -Action $action -Trigger $trigger
```

### 2. Скрипт мониторинга

```powershell
# MonitorReplication.ps1
$logFile = "C:\Application\REPLICATION\AquaTrade\Replication.Shuttle\UAT\3.6.205.4\Logs\Rpl_11_STRplShuttle-Test_rpl_Core.utf8.dll.txt"
$errorPattern = "ERROR|FATAL|EXCEPTION"

$errors = Select-String -Path $logFile -Pattern $errorPattern -SimpleMatch
if ($errors) {
    # Отправка уведомления об ошибках
    Send-MailMessage -To "admin@company.com" -Subject "Replication Errors" -Body $errors
}
```

### 3. Очистка старых логов

```powershell
# CleanupLogs.ps1
$logPath = "C:\Application\REPLICATION\AquaTrade\Replication.Shuttle\UAT\3.6.205.4\Logs\"
$cutoffDate = (Get-Date).AddDays(-30)

Get-ChildItem -Path $logPath -Filter "*.txt" | Where-Object { $_.LastWriteTime -lt $cutoffDate } | Remove-Item -Force
```

## Устранение неполадок

### 1. Проблемы с подключением к БД

```sql
-- Проверка подключения
SELECT @@SERVERNAME, DB_NAME(), USER_NAME();

-- Проверка прав пользователя
SELECT 
    p.state_desc,
    p.permission_name,
    s.name as principal_name
FROM sys.database_permissions p
JOIN sys.database_principals s ON p.grantee_principal_id = s.principal_id
WHERE s.name = 'STRplShuttle-Test';
```

### 2. Проблемы с репликацией

```powershell
# Проверка статуса службы
Get-Service "Replication.Shuttle.AquaTrade.UAT"

# Просмотр логов
Get-Content "C:\Application\REPLICATION\AquaTrade\Replication.Shuttle\UAT\3.6.205.4\Logs\Rpl_11_STRplShuttle-Test_rpl_Core.utf8.dll.txt" -Tail 100
```

### 3. Проблемы с данными

```sql
-- Проверка целостности данных
SELECT COUNT(*) FROM rgReceivables WHERE idroute IS NULL;
SELECT COUNT(*) FROM refOutletFocusGroups WHERE outercode IS NULL;

-- Проверка дубликатов
SELECT outercode, COUNT(*) 
FROM refOutletFocusGroups 
GROUP BY outercode 
HAVING COUNT(*) > 1;
```

## Резервное копирование

### 1. Автоматическое резервное копирование

```sql
-- Создание плана обслуживания
USE msdb;
EXEC dbo.sp_add_maintenance_plan
    @plan_name = 'AquaTrade_Backup_Plan',
    @description = 'Backup plan for AquaTrade UAT database';
```

### 2. Ручное резервное копирование

```sql
-- Полное резервное копирование
BACKUP DATABASE [AquaTrade_UAT] 
TO DISK = 'C:\Backup\AquaTrade_UAT_Full.bak'
WITH FORMAT, INIT, COMPRESSION;

-- Резервное копирование журналов
BACKUP LOG [AquaTrade_UAT] 
TO DISK = 'C:\Backup\AquaTrade_UAT_Log.trn'
WITH FORMAT, INIT, COMPRESSION;
```

## Обновление системы

### 1. Обновление Replication.Shuttle

```powershell
# Остановка службы
Stop-Service "Replication.Shuttle.AquaTrade.UAT"

# Создание резервной копии
Copy-Item -Path "C:\Application\REPLICATION\AquaTrade\Replication.Shuttle\UAT\3.6.205.4" -Destination "C:\Backup\Replication_Backup" -Recurse

# Установка новой версии
# ... копирование новых файлов ...

# Запуск службы
Start-Service "Replication.Shuttle.AquaTrade.UAT"
```

### 2. Обновление базы данных

```sql
-- Выполнение скриптов обновления
-- Проверка версии схемы
SELECT * FROM sys.extended_properties WHERE name = 'SchemaVersion';
```
