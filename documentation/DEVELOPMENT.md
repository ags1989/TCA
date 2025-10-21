# Руководство разработчика

## Обзор

Данный документ предназначен для разработчиков, работающих с системой разделения долгов ТТ по маршрутам в проекте АкваТрейд.

## Настройка среды разработки

### 1. Требования к системе

#### Минимальные требования:
- **OS**: Windows 10/11 или Windows Server 2019+
- **RAM**: 16+ GB
- **Диск**: 100+ GB свободного места
- **CPU**: 4+ ядер

#### Программное обеспечение:
- **Visual Studio**: 2022 или выше
- **.NET Framework**: 4.8+
- **SQL Server**: 2019 Developer Edition или выше
- **Git**: 2.30+
- **Replication.Shuttle**: 3.6.205.4

### 2. Установка зависимостей

#### Установка SQL Server:
```powershell
# Скачивание SQL Server Developer Edition
# https://www.microsoft.com/en-us/sql-server/sql-server-downloads

# Установка с помощью Chocolatey
choco install sql-server-2019-developer
```

#### Установка Visual Studio:
```powershell
# Установка Visual Studio Community
choco install visualstudio2022community

# Установка необходимых компонентов
choco install visualstudio2022-workload-data
choco install visualstudio2022-workload-netcoretools
```

#### Установка Git:
```powershell
# Установка Git
choco install git

# Настройка Git
git config --global user.name "Your Name"
git config --global user.email "your.email@company.com"
```

### 3. Клонирование репозитория

```bash
# Клонирование репозитория
git clone https://tfssrv.systtech.ru/tfs/DefaultCollection/_git/Houston
cd Houston

# Переключение на ветку с изменениями
git checkout feature/aquatrade-debts-by-routes

# Установка зависимостей
dotnet restore
```

## Структура проекта

### 1. Основные компоненты

```
Houston/
├── src/
│   ├── Replication.Shuttle/          # Система репликации
│   │   ├── Core/                     # Основная логика
│   │   ├── Transport/                # Транспортный слой
│   │   └── UI/                       # Пользовательский интерфейс
│   ├── Database/                     # Скрипты БД
│   │   ├── Tables/                   # Создание таблиц
│   │   ├── Procedures/               # Хранимые процедуры
│   │   ├── Triggers/                 # Триггеры
│   │   └── Views/                    # Представления
│   └── MobileTerminal/               # Мобильный терминал
│       ├── UI/                       # Пользовательский интерфейс
│       ├── Services/                 # Бизнес-логика
│       └── Data/                     # Модели данных
├── tests/                            # Тесты
│   ├── Unit/                         # Unit тесты
│   ├── Integration/                  # Интеграционные тесты
│   └── UI/                           # UI тесты
├── docs/                            # Документация
└── scripts/                         # Скрипты развертывания
```

### 2. Ключевые файлы

#### Конфигурация репликации:
- `BusinessObjects.xml` - Определение бизнес-объектов
- `ReplicationRules.xml` - Правила репликации
- `SyncProtocolRules_1_2_1.xml` - Протокол синхронизации
- `MappingRule_1_2_1.xml` - Правила сопоставления

#### Скрипты БД:
- `CreateTables.sql` - Создание таблиц
- `CreateProcedures.sql` - Хранимые процедуры
- `CreateTriggers.sql` - Триггеры
- `CreateIndexes.sql` - Индексы

## Разработка

### 1. Стиль кода

#### C# (.NET Framework):
```csharp
// Использование PascalCase для методов и свойств
public class DebtCalculationService
{
    private readonly ILogger _logger;
    
    // Использование camelCase для локальных переменных
    public List<DebtInfo> GetDebtsByRoute(int agentRoute, string focusGroup)
    {
        var debts = new List<DebtInfo>();
        
        try
        {
            // Логика получения долгов
            debts = _repository.GetDebtsByRoute(agentRoute, focusGroup);
        }
        catch (Exception ex)
        {
            _logger.Error($"Ошибка получения долгов для маршрута {agentRoute}: {ex.Message}");
            throw;
        }
        
        return debts;
    }
}
```

#### SQL:
```sql
-- Использование UPPER_CASE для ключевых слов
-- Использование PascalCase для имен объектов
CREATE PROCEDURE sp_GetOutletDebtsByRoute
    @RouteId INT,
    @FocusGroup NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Комментарии на русском языке
    SELECT 
        r.OutletCode,
        o.OutletName,
        SUM(r.DebtAmount) as TotalDebt
    FROM rgReceivables r
    INNER JOIN refOutlets o ON r.OutletCode = o.OutletCode
    WHERE r.idroute = @RouteId
        AND r.deleted = 0
    GROUP BY r.OutletCode, o.OutletName;
END
```

### 2. Принципы разработки

#### SOLID принципы:
- **S** - Single Responsibility: Каждый класс имеет одну ответственность
- **O** - Open/Closed: Открыт для расширения, закрыт для модификации
- **L** - Liskov Substitution: Подклассы должны заменять базовые классы
- **I** - Interface Segregation: Клиенты не должны зависеть от неиспользуемых интерфейсов
- **D** - Dependency Inversion: Зависимость от абстракций, а не от конкретных реализаций

#### DRY (Don't Repeat Yourself):
- Избегайте дублирования кода
- Выносите общую логику в отдельные методы
- Используйте наследование и композицию

#### YAGNI (You Aren't Gonna Need It):
- Не реализуйте функционал "на будущее"
- Добавляйте функциональность только когда она действительно нужна

### 3. Обработка ошибок

#### C#:
```csharp
public class DebtService
{
    public async Task<DebtResult> CalculateDebtsAsync(int routeId)
    {
        try
        {
            // Основная логика
            var debts = await _repository.GetDebtsAsync(routeId);
            return new DebtResult { Success = true, Data = debts };
        }
        catch (SqlException ex)
        {
            _logger.Error($"Ошибка БД при получении долгов для маршрута {routeId}: {ex.Message}");
            return new DebtResult { Success = false, Error = "Ошибка базы данных" };
        }
        catch (Exception ex)
        {
            _logger.Error($"Неожиданная ошибка при получении долгов для маршрута {routeId}: {ex.Message}");
            return new DebtResult { Success = false, Error = "Внутренняя ошибка системы" };
        }
    }
}
```

#### SQL:
```sql
CREATE PROCEDURE sp_UpdateDebtInfo
    @RouteId INT,
    @OutletCode NVARCHAR(50),
    @DebtAmount DECIMAL(18,2)
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Проверка входных параметров
        IF @RouteId IS NULL OR @OutletCode IS NULL
        BEGIN
            RAISERROR('Параметры RouteId и OutletCode не могут быть NULL', 16, 1);
            RETURN;
        END
        
        -- Обновление данных
        UPDATE rgReceivables 
        SET DebtAmount = @DebtAmount,
            UpdatedDate = GETDATE()
        WHERE idroute = @RouteId 
            AND OutletCode = @OutletCode;
        
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        -- Логирование ошибки
        INSERT INTO ErrorLog (ErrorNumber, ErrorMessage, ErrorTime)
        VALUES (ERROR_NUMBER(), ERROR_MESSAGE(), GETDATE());
        
        -- Повторное возбуждение ошибки
        THROW;
    END CATCH
END
```

## Тестирование

### 1. Unit тесты

#### Структура тестов:
```csharp
[TestFixture]
public class DebtCalculationServiceTests
{
    private DebtCalculationService _service;
    private Mock<IDebtRepository> _mockRepository;
    private Mock<ILogger> _mockLogger;
    
    [SetUp]
    public void Setup()
    {
        _mockRepository = new Mock<IDebtRepository>();
        _mockLogger = new Mock<ILogger>();
        _service = new DebtCalculationService(_mockRepository.Object, _mockLogger.Object);
    }
    
    [Test]
    public void GetDebtsByRoute_ValidRoute_ReturnsDebts()
    {
        // Arrange
        var routeId = 1000001;
        var focusGroup = "FG1234";
        var expectedDebts = new List<DebtInfo>
        {
            new DebtInfo { OutletCode = "13783", DebtAmount = 50000 }
        };
        
        _mockRepository.Setup(r => r.GetDebtsByRoute(routeId, focusGroup))
                      .Returns(expectedDebts);
        
        // Act
        var result = _service.GetDebtsByRoute(routeId, focusGroup);
        
        // Assert
        Assert.That(result, Is.Not.Null);
        Assert.That(result.Count, Is.EqualTo(1));
        Assert.That(result[0].OutletCode, Is.EqualTo("13783"));
    }
    
    [Test]
    public void GetDebtsByRoute_InvalidRoute_ThrowsException()
    {
        // Arrange
        var routeId = -1;
        var focusGroup = "FG1234";
        
        _mockRepository.Setup(r => r.GetDebtsByRoute(routeId, focusGroup))
                      .Throws(new ArgumentException("Invalid route ID"));
        
        // Act & Assert
        Assert.Throws<ArgumentException>(() => 
            _service.GetDebtsByRoute(routeId, focusGroup));
    }
}
```

### 2. Интеграционные тесты

```csharp
[TestFixture]
public class ReplicationIntegrationTests
{
    private string _connectionString;
    private ReplicationService _service;
    
    [SetUp]
    public void Setup()
    {
        _connectionString = ConfigurationManager.ConnectionStrings["TestDB"].ConnectionString;
        _service = new ReplicationService(_connectionString);
    }
    
    [Test]
    public async Task ImportFromUS_ValidData_ImportsSuccessfully()
    {
        // Arrange
        var testData = CreateTestData();
        
        // Act
        var result = await _service.ImportFromUSAsync(testData);
        
        // Assert
        Assert.That(result.Success, Is.True);
        
        // Проверка данных в БД
        using (var connection = new SqlConnection(_connectionString))
        {
            var count = await connection.QuerySingleAsync<int>(
                "SELECT COUNT(*) FROM refOutletFocusGroups WHERE FG = @FocusGroup",
                new { FocusGroup = "FG1234" });
            
            Assert.That(count, Is.EqualTo(1));
        }
    }
}
```

### 3. UI тесты

```csharp
[TestFixture]
public class MobileTerminalUITests
{
    private MobileTerminalApp _app;
    
    [SetUp]
    public void Setup()
    {
        _app = new MobileTerminalApp();
        _app.Start();
    }
    
    [TearDown]
    public void TearDown()
    {
        _app?.Close();
    }
    
    [Test]
    public void OpenDebtsReport_DisplaysCorrectData()
    {
        // Arrange
        _app.Login("test_agent", "password");
        
        // Act
        _app.OpenDebtsReport();
        
        // Assert
        var debts = _app.GetDisplayedDebts();
        Assert.That(debts.Count, Is.EqualTo(2));
        Assert.That(debts.All(d => d.AgentRoute == 1000001), Is.True);
    }
}
```

## Отладка

### 1. Логирование

#### Настройка логгера:
```csharp
public class DebtCalculationService
{
    private readonly ILogger _logger;
    
    public DebtCalculationService(ILogger logger)
    {
        _logger = logger;
    }
    
    public List<DebtInfo> GetDebtsByRoute(int agentRoute, string focusGroup)
    {
        _logger.Info($"Начало получения долгов для маршрута {agentRoute}, ФГ {focusGroup}");
        
        try
        {
            var debts = _repository.GetDebtsByRoute(agentRoute, focusGroup);
            _logger.Info($"Получено {debts.Count} записей о долгах");
            return debts;
        }
        catch (Exception ex)
        {
            _logger.Error($"Ошибка при получении долгов: {ex.Message}", ex);
            throw;
        }
    }
}
```

#### Конфигурация логирования:
```xml
<configuration>
  <log4net>
    <appender name="FileAppender" type="log4net.Appender.FileAppender">
      <file value="logs/debt-service.log" />
      <appendToFile value="true" />
      <layout type="log4net.Layout.PatternLayout">
        <conversionPattern value="%date [%thread] %-5level %logger - %message%newline" />
      </layout>
    </appender>
    
    <root>
      <level value="INFO" />
      <appender-ref ref="FileAppender" />
    </root>
  </log4net>
</configuration>
```

### 2. Профилирование

#### Профилирование производительности:
```csharp
public class PerformanceProfiler
{
    private readonly ILogger _logger;
    
    public T ProfileMethod<T>(string methodName, Func<T> method)
    {
        var stopwatch = Stopwatch.StartNew();
        
        try
        {
            var result = method();
            return result;
        }
        finally
        {
            stopwatch.Stop();
            _logger.Info($"Метод {methodName} выполнен за {stopwatch.ElapsedMilliseconds} мс");
        }
    }
}
```

### 3. Отладка репликации

#### Включение детального логирования:
```xml
<configuration>
  <appSettings>
    <add key="LogLevel" value="DEBUG" />
    <add key="EnableDetailedLogging" value="true" />
    <add key="LogReplicationDetails" value="true" />
  </appSettings>
</configuration>
```

#### Анализ логов:
```powershell
# Поиск ошибок в логах
Select-String -Path "logs\replication.log" -Pattern "ERROR|FATAL" -Context 2

# Анализ производительности
Select-String -Path "logs\replication.log" -Pattern "время выполнения" | 
    ForEach-Object { 
        if ($_ -match "(\d+) мс") { 
            [int]$matches[1] 
        } 
    } | Measure-Object -Average -Maximum -Minimum
```

## Развертывание

### 1. Локальная разработка

#### Запуск в режиме разработки:
```powershell
# Запуск репликации в режиме отладки
dotnet run --project src/Replication.Shuttle --configuration Debug

# Запуск с дополнительными параметрами
dotnet run --project src/Replication.Shuttle -- --environment Development --log-level Debug
```

#### Настройка базы данных для разработки:
```sql
-- Создание тестовой БД
CREATE DATABASE [AquaTrade_Dev];

-- Настройка пользователя для разработки
CREATE LOGIN [DevUser] WITH PASSWORD = 'DevPassword123!';
USE [AquaTrade_Dev];
CREATE USER [DevUser] FOR LOGIN [DevUser];
ALTER ROLE [db_owner] ADD MEMBER [DevUser];
```

### 2. Тестовое развертывание

#### Скрипт развертывания:
```powershell
# Deploy-Test.ps1
param(
    [string]$Environment = "UAT",
    [string]$Version = "3.6.205.4"
)

Write-Host "Развертывание версии $Version в окружение $Environment"

# Остановка служб
Stop-Service "Replication.Shuttle.AquaTrade.$Environment" -Force

# Создание резервной копии
$backupPath = "C:\Backup\$Environment\$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupPath -Force
Copy-Item -Path "C:\Application\REPLICATION\AquaTrade\Replication.Shuttle\$Environment\$Version" -Destination $backupPath -Recurse

# Копирование новых файлов
Copy-Item -Path ".\build\$Version\*" -Destination "C:\Application\REPLICATION\AquaTrade\Replication.Shuttle\$Environment\$Version\" -Recurse -Force

# Обновление конфигурации
$configPath = "C:\Application\REPLICATION\AquaTrade\Replication.Shuttle\$Environment\$Version\rpl_SyncTransport.dll.config"
$config = [xml](Get-Content $configPath)
$config.configuration.appSettings.SetAttribute("Environment", $Environment)
$config.Save($configPath)

# Запуск служб
Start-Service "Replication.Shuttle.AquaTrade.$Environment"

Write-Host "Развертывание завершено"
```

### 3. Продуктивное развертывание

#### Процедура развертывания:
1. **Подготовка**:
   - Создание резервной копии
   - Тестирование на UAT
   - Подготовка плана отката

2. **Развертывание**:
   - Остановка служб
   - Копирование файлов
   - Обновление конфигурации
   - Запуск служб

3. **Проверка**:
   - Мониторинг логов
   - Проверка функциональности
   - Тестирование критических сценариев

## Мониторинг

### 1. Метрики производительности

#### Ключевые метрики:
- Время выполнения запросов
- Использование памяти
- Количество обработанных записей
- Частота ошибок

#### Настройка мониторинга:
```csharp
public class MetricsCollector
{
    private readonly ILogger _logger;
    
    public void RecordQueryExecutionTime(string queryName, TimeSpan executionTime)
    {
        _logger.Info($"Query {queryName} executed in {executionTime.TotalMilliseconds} ms");
        
        // Отправка метрик в систему мониторинга
        if (executionTime.TotalMilliseconds > 5000)
        {
            _logger.Warning($"Slow query detected: {queryName} took {executionTime.TotalMilliseconds} ms");
        }
    }
}
```

### 2. Алерты

#### Настройка алертов:
```powershell
# Создание задачи для мониторинга
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\Scripts\MonitorReplication.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "MonitorReplication" -Action $action -Trigger $trigger -Settings $settings
```

## Лучшие практики

### 1. Управление кодом

#### Git workflow:
```bash
# Создание feature ветки
git checkout -b feature/debt-calculation-optimization

# Коммиты с описательными сообщениями
git commit -m "feat: оптимизация расчета долгов по маршрутам

- Добавлен индекс для ускорения запросов
- Улучшена логика кэширования
- Добавлены unit тесты"

# Push и создание Pull Request
git push origin feature/debt-calculation-optimization
```

#### Code Review:
- Проверка соответствия стандартам кодирования
- Анализ производительности
- Проверка покрытия тестами
- Валидация безопасности

### 2. Документация

#### Комментарии в коде:
```csharp
/// <summary>
/// Получает задолженности торговых точек по маршруту агента
/// </summary>
/// <param name="agentRoute">Идентификатор маршрута агента</param>
/// <param name="focusGroup">Код фокусной группы</param>
/// <returns>Список задолженностей по маршруту</returns>
/// <exception cref="ArgumentException">Выбрасывается при неверных параметрах</exception>
public List<DebtInfo> GetDebtsByRoute(int agentRoute, string focusGroup)
{
    // Проверка входных параметров
    if (agentRoute <= 0)
        throw new ArgumentException("Идентификатор маршрута должен быть положительным", nameof(agentRoute));
    
    if (string.IsNullOrEmpty(focusGroup))
        throw new ArgumentException("Код фокусной группы не может быть пустым", nameof(focusGroup));
    
    // Основная логика...
}
```

### 3. Безопасность

#### Валидация входных данных:
```csharp
public class InputValidator
{
    public static void ValidateRouteId(int routeId)
    {
        if (routeId <= 0)
            throw new ArgumentException("Идентификатор маршрута должен быть положительным");
    }
    
    public static void ValidateFocusGroup(string focusGroup)
    {
        if (string.IsNullOrWhiteSpace(focusGroup))
            throw new ArgumentException("Код фокусной группы не может быть пустым");
        
        if (!Regex.IsMatch(focusGroup, @"^[A-Z0-9_]+$"))
            throw new ArgumentException("Код фокусной группы содержит недопустимые символы");
    }
}
```

#### Защита от SQL-инъекций:
```csharp
// Использование параметризованных запросов
public List<DebtInfo> GetDebtsByRoute(int agentRoute, string focusGroup)
{
    const string query = @"
        SELECT OutletCode, DebtAmount, CreatedDate
        FROM rgReceivables 
        WHERE idroute = @RouteId 
            AND FocusGroup = @FocusGroup
            AND deleted = 0";
    
    using (var connection = new SqlConnection(_connectionString))
    {
        return connection.Query<DebtInfo>(query, new { RouteId = agentRoute, FocusGroup = focusGroup })
                         .ToList();
    }
}
```

## Заключение

Данное руководство покрывает основные аспекты разработки системы разделения долгов ТТ по маршрутам. Следуйте описанным практикам для обеспечения качества кода и эффективности разработки.

Для получения дополнительной информации обращайтесь к:
- [Архитектуре системы](ARCHITECTURE.md)
- [API документации](API.md)
- [Руководству по тестированию](TESTING.md)
