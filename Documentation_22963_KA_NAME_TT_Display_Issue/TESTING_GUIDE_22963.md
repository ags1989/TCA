# Руководство по тестированию: KA_NAME ТТ - Исправление отображения названий торговых точек

## Обзор тестирования

### Цель
Обеспечить полное тестирование исправления проблемы отображения названий торговых точек в системе репликации, чтобы убедиться в корректной работе приоритетного использования поля KA_NAME.

### Области тестирования
1. **Функциональное тестирование** - проверка основной логики отображения
2. **Интеграционное тестирование** - проверка работы с системой репликации
3. **Регрессионное тестирование** - проверка отсутствия побочных эффектов
4. **Тестирование производительности** - проверка влияния на скорость работы
5. **Тестирование совместимости** - проверка работы с существующими данными

## Тестовые сценарии

### TC1: Торговые точки с заполненным KA_NAME

#### Тест-кейс TC1.1: Отображение KA_NAME в отчетах
**Цель**: Проверить, что торговые точки с заполненным KA_NAME отображаются с названием из этого поля

**Предусловия**:
- В БД есть торговые точки с заполненным полем KA_NAME
- Система репликации настроена и работает
- Исправление применено

**Тестовые данные**:
```sql
-- ТТ 460011 с KA_NAME = "Шах"
INSERT INTO refOutlets (id, idClient, idLegalEntity) VALUES (460011, 1001, 2001);
INSERT INTO refClients (id, KA_NAME) VALUES (1001, 'Шах');
INSERT INTO refLegalEntities (id, name) VALUES (2001, 'Шахабасова З.У. ИП');
```

**Шаги выполнения**:
1. Запустить генерацию отчета для клиента с ТТ 460011
2. Проверить содержимое XML отчета
3. Убедиться, что в отчете указано name="Шах"

**Ожидаемый результат**:
- В XML отчете для ТТ 460011 указано name="Шах"
- Название берется из поля KA_NAME, а не из юридического лица

**Критерии приемки**:
- ✅ XML содержит правильное название из KA_NAME
- ✅ Название из юридического лица не используется
- ✅ Формат XML корректен

#### Тест-кейс TC1.2: Множественные ТТ с KA_NAME
**Цель**: Проверить корректную обработку нескольких торговых точек с заполненным KA_NAME

**Шаги выполнения**:
1. Создать несколько ТТ с разными значениями KA_NAME
2. Сгенерировать отчет для всех ТТ
3. Проверить корректность отображения каждой ТТ

**Ожидаемый результат**:
- Все ТТ отображаются с названиями из KA_NAME
- Нет ошибок при обработке множественных записей

**Критерии приемки**:
- ✅ Все ТТ отображаются корректно
- ✅ Производительность в пределах нормы
- ✅ Ошибок нет

### TC2: Торговые точки без KA_NAME

#### Тест-кейс TC2.1: Fallback на юридическое лицо
**Цель**: Проверить, что ТТ без KA_NAME используют название из юридического лица

**Тестовые данные**:
```sql
-- ТТ 460012 без KA_NAME
INSERT INTO refOutlets (id, idClient, idLegalEntity) VALUES (460012, 1002, 2002);
INSERT INTO refClients (id, KA_NAME) VALUES (1002, NULL);
INSERT INTO refLegalEntities (id, name) VALUES (2002, 'ООО Тестовая компания');
```

**Шаги выполнения**:
1. Сгенерировать отчет для ТТ 460012
2. Проверить содержимое XML отчета
3. Убедиться, что используется название из юридического лица

**Ожидаемый результат**:
- В XML отчете указано name="ООО Тестовая компания"
- Система корректно использует fallback логику

**Критерии приемки**:
- ✅ Используется название из юридического лица
- ✅ Fallback логика работает корректно
- ✅ Нет ошибок при обработке NULL значений

#### Тест-кейс TC2.2: Пустое значение KA_NAME
**Цель**: Проверить обработку пустых строк в поле KA_NAME

**Тестовые данные**:
```sql
-- ТТ 460013 с пустым KA_NAME
INSERT INTO refOutlets (id, idClient, idLegalEntity) VALUES (460013, 1003, 2003);
INSERT INTO refClients (id, KA_NAME) VALUES (1003, '');
INSERT INTO refLegalEntities (id, name) VALUES (2003, 'ИП Иванов И.И.');
```

**Шаги выполнения**:
1. Сгенерировать отчет для ТТ 460013
2. Проверить, что используется название из юридического лица
3. Убедиться в отсутствии ошибок

**Ожидаемый результат**:
- Используется название "ИП Иванов И.И." из юридического лица
- Пустая строка обрабатывается как NULL

**Критерии приемки**:
- ✅ Пустые строки обрабатываются корректно
- ✅ Используется fallback логика
- ✅ Ошибок нет

### TC3: Граничные случаи

#### Тест-кейс TC3.1: Очень длинное KA_NAME
**Цель**: Проверить обработку длинных названий в поле KA_NAME

**Тестовые данные**:
```sql
-- ТТ с очень длинным KA_NAME (300 символов)
INSERT INTO refOutlets (id, idClient, idLegalEntity) VALUES (460014, 1004, 2004);
INSERT INTO refClients (id, KA_NAME) VALUES (1004, 'Очень длинное название торговой точки ' + REPLICATE('X', 250));
INSERT INTO refLegalEntities (id, name) VALUES (2004, 'Короткое название');
```

**Шаги выполнения**:
1. Сгенерировать отчет для ТТ 460014
2. Проверить, что длинное название корректно обрабатывается
3. Убедиться в отсутствии ошибок обрезания

**Ожидаемый результат**:
- Длинное название отображается полностью
- XML корректно экранирует специальные символы

**Критерии приемки**:
- ✅ Длинные названия обрабатываются корректно
- ✅ XML валиден
- ✅ Производительность не страдает

#### Тест-кейс TC3.2: Специальные символы в KA_NAME
**Цель**: Проверить обработку специальных символов в названиях

**Тестовые данные**:
```sql
-- ТТ с специальными символами
INSERT INTO refOutlets (id, idClient, idLegalEntity) VALUES (460015, 1005, 2005);
INSERT INTO refClients (id, KA_NAME) VALUES (1005, 'ТТ "Солнышко" & Ко <тест>');
INSERT INTO refLegalEntities (id, name) VALUES (2005, 'Обычное название');
```

**Шаги выполнения**:
1. Сгенерировать отчет для ТТ 460015
2. Проверить корректность экранирования в XML
3. Убедиться в валидности XML

**Ожидаемый результат**:
- Специальные символы корректно экранированы
- XML остается валидным

**Критерии приемки**:
- ✅ Специальные символы экранированы
- ✅ XML валиден
- ✅ Название читаемо

### TC4: Интеграционное тестирование

#### Тест-кейс TC4.1: Полный цикл генерации отчета
**Цель**: Проверить работу исправления в полном цикле генерации отчета

**Шаги выполнения**:
1. Подготовить тестовые данные с разными типами ТТ
2. Запустить полный цикл генерации отчета
3. Проверить корректность всех названий в отчете
4. Убедиться в отсутствии ошибок в логах

**Ожидаемый результат**:
- Все ТТ отображаются с правильными названиями
- Отчет генерируется без ошибок
- Производительность в пределах нормы

**Критерии приемки**:
- ✅ Полный цикл работает корректно
- ✅ Все названия правильные
- ✅ Ошибок в логах нет

#### Тест-кейс TC4.2: Работа с кэшированием
**Цель**: Проверить корректность работы кэширования названий ТТ

**Шаги выполнения**:
1. Включить кэширование названий ТТ
2. Сгенерировать отчет для группы ТТ
3. Повторно сгенерировать отчет для тех же ТТ
4. Проверить, что кэшированные данные используются корректно

**Ожидаемый результат**:
- Кэширование работает корректно
- Повторные запросы выполняются быстрее
- Данные остаются актуальными

**Критерии приемки**:
- ✅ Кэширование работает
- ✅ Производительность улучшена
- ✅ Данные актуальны

### TC5: Регрессионное тестирование

#### Тест-кейс TC5.1: Существующие отчеты
**Цель**: Проверить, что существующие отчеты продолжают работать корректно

**Шаги выполнения**:
1. Сгенерировать отчеты, которые работали до исправления
2. Сравнить результаты с эталонными данными
3. Убедиться в отсутствии изменений в структуре отчетов

**Ожидаемый результат**:
- Существующие отчеты работают как раньше
- Изменения только в названиях ТТ
- Структура отчетов не изменилась

**Критерии приемки**:
- ✅ Существующие отчеты работают
- ✅ Изменения только в названиях
- ✅ Обратная совместимость сохранена

#### Тест-кейс TC5.2: Производительность системы
**Цель**: Проверить, что исправление не ухудшило производительность

**Шаги выполнения**:
1. Измерить время генерации отчетов до исправления
2. Применить исправление
3. Измерить время генерации отчетов после исправления
4. Сравнить результаты

**Ожидаемый результат**:
- Производительность не ухудшилась значительно
- Время генерации в пределах допустимых значений

**Критерии приемки**:
- ✅ Производительность не пострадала
- ✅ Время генерации приемлемо
- ✅ Система остается стабильной

## Автоматизированное тестирование

### Unit тесты

#### Тест класса TradingPointNameResolver
```csharp
[TestClass]
public class TradingPointNameResolverTests
{
    private TradingPointNameResolver _resolver;
    private string _connectionString;
    
    [TestInitialize]
    public void Setup()
    {
        _connectionString = ConfigurationManager.ConnectionStrings["TestDB"].ConnectionString;
        _resolver = new TradingPointNameResolver(_connectionString);
    }
    
    [TestMethod]
    public void GetDisplayName_WithKAName_ShouldReturnKAName()
    {
        // Arrange
        var ttId = 460011;
        SetupTestData(ttId, "Шах", "Шахабасова З.У. ИП");
        
        // Act
        var result = _resolver.GetDisplayName(ttId);
        
        // Assert
        Assert.AreEqual("Шах", result);
    }
    
    [TestMethod]
    public void GetDisplayName_WithoutKAName_ShouldReturnLegalEntityName()
    {
        // Arrange
        var ttId = 460012;
        SetupTestData(ttId, null, "ООО Тест");
        
        // Act
        var result = _resolver.GetDisplayName(ttId);
        
        // Assert
        Assert.AreEqual("ООО Тест", result);
    }
    
    [TestMethod]
    public void GetDisplayName_WithEmptyKAName_ShouldReturnLegalEntityName()
    {
        // Arrange
        var ttId = 460013;
        SetupTestData(ttId, "", "ИП Иванов");
        
        // Act
        var result = _resolver.GetDisplayName(ttId);
        
        // Assert
        Assert.AreEqual("ИП Иванов", result);
    }
    
    [TestMethod]
    public void GetDisplayName_WithSpecialCharacters_ShouldEscapeCorrectly()
    {
        // Arrange
        var ttId = 460014;
        var kaName = "ТТ \"Солнышко\" & Ко <тест>";
        SetupTestData(ttId, kaName, "Обычное название");
        
        // Act
        var result = _resolver.GetDisplayName(ttId);
        
        // Assert
        Assert.AreEqual(kaName, result);
    }
    
    [TestMethod]
    public void GetDisplayName_NonExistentTradingPoint_ShouldReturnDefault()
    {
        // Arrange
        var ttId = 999999;
        
        // Act
        var result = _resolver.GetDisplayName(ttId);
        
        // Assert
        Assert.AreEqual("Неизвестная ТТ", result);
    }
    
    private void SetupTestData(int ttId, string kaName, string legalEntityName)
    {
        // Настройка тестовых данных в БД
        using (var connection = new SqlConnection(_connectionString))
        {
            connection.Open();
            
            // Очистка старых данных
            var deleteQuery = "DELETE FROM refOutlets WHERE id = @id";
            using (var command = new SqlCommand(deleteQuery, connection))
            {
                command.Parameters.AddWithValue("@id", ttId);
                command.ExecuteNonQuery();
            }
            
            // Вставка новых данных
            var insertQuery = @"
                INSERT INTO refOutlets (id, idClient, idLegalEntity) 
                VALUES (@ttId, @clientId, @legalEntityId);
                INSERT INTO refClients (id, KA_NAME) 
                VALUES (@clientId, @kaName);
                INSERT INTO refLegalEntities (id, name) 
                VALUES (@legalEntityId, @legalEntityName);";
                
            using (var command = new SqlCommand(insertQuery, connection))
            {
                command.Parameters.AddWithValue("@ttId", ttId);
                command.Parameters.AddWithValue("@clientId", ttId + 1000);
                command.Parameters.AddWithValue("@legalEntityId", ttId + 2000);
                command.Parameters.AddWithValue("@kaName", (object)kaName ?? DBNull.Value);
                command.Parameters.AddWithValue("@legalEntityName", legalEntityName);
                command.ExecuteNonQuery();
            }
        }
    }
}
```

#### Тест класса ReportGenerator
```csharp
[TestClass]
public class ReportGeneratorTests
{
    private ReportGenerator _generator;
    private string _connectionString;
    
    [TestInitialize]
    public void Setup()
    {
        _connectionString = ConfigurationManager.ConnectionStrings["TestDB"].ConnectionString;
        _generator = new ReportGenerator(_connectionString);
    }
    
    [TestMethod]
    public void GenerateClientReport_ShouldUseCorrectTradingPointNames()
    {
        // Arrange
        var clientId = 1;
        SetupTestClient(clientId);
        
        // Act
        var report = _generator.GenerateClientReport(clientId);
        
        // Assert
        Assert.IsTrue(report.Contains("name=\"Шах\"")); // KA_NAME
        Assert.IsTrue(report.Contains("name=\"ООО Тест\"")); // Legal Entity
        Assert.IsTrue(IsValidXml(report));
    }
    
    [TestMethod]
    public void GenerateClientReport_ShouldEscapeSpecialCharacters()
    {
        // Arrange
        var clientId = 2;
        SetupTestClientWithSpecialCharacters(clientId);
        
        // Act
        var report = _generator.GenerateClientReport(clientId);
        
        // Assert
        Assert.IsTrue(report.Contains("name=\"ТТ &quot;Солнышко&quot; &amp; Ко &lt;тест&gt;\""));
        Assert.IsTrue(IsValidXml(report));
    }
    
    private void SetupTestClient(int clientId)
    {
        // Настройка тестового клиента с разными типами ТТ
        // (реализация зависит от структуры БД)
    }
    
    private void SetupTestClientWithSpecialCharacters(int clientId)
    {
        // Настройка клиента с ТТ, содержащими специальные символы
    }
    
    private bool IsValidXml(string xml)
    {
        try
        {
            var doc = new XmlDocument();
            doc.LoadXml(xml);
            return true;
        }
        catch
        {
            return false;
        }
    }
}
```

### Интеграционные тесты

#### Тест полного цикла
```csharp
[TestClass]
public class IntegrationTests
{
    [TestMethod]
    public void FullReportGenerationCycle_ShouldWorkCorrectly()
    {
        // Arrange
        var testData = PrepareTestData();
        
        // Act
        var reports = GenerateAllReports(testData.ClientIds);
        
        // Assert
        foreach (var report in reports)
        {
            Assert.IsTrue(ValidateReport(report));
        }
    }
    
    private TestData PrepareTestData()
    {
        // Подготовка комплексных тестовых данных
        return new TestData
        {
            ClientIds = new[] { 1, 2, 3 },
            TradingPoints = new[]
            {
                new TradingPoint { Id = 460011, HasKAName = true, KAName = "Шах" },
                new TradingPoint { Id = 460012, HasKAName = false, LegalEntityName = "ООО Тест" },
                new TradingPoint { Id = 460013, HasKAName = true, KAName = "ТТ с символами & < >" }
            }
        };
    }
    
    private List<string> GenerateAllReports(int[] clientIds)
    {
        var reports = new List<string>();
        var generator = new ReportGenerator(connectionString);
        
        foreach (var clientId in clientIds)
        {
            reports.Add(generator.GenerateClientReport(clientId));
        }
        
        return reports;
    }
    
    private bool ValidateReport(string report)
    {
        // Валидация отчета
        return IsValidXml(report) && 
               ContainsCorrectTradingPointNames(report);
    }
    
    private bool ContainsCorrectTradingPointNames(string report)
    {
        // Проверка корректности названий ТТ в отчете
        return report.Contains("name=\"Шах\"") &&
               report.Contains("name=\"ООО Тест\"") &&
               report.Contains("name=\"ТТ с символами &amp; &lt; &gt;\"");
    }
}
```

## Тестирование производительности

### Нагрузочные тесты
```csharp
[TestClass]
public class PerformanceTests
{
    [TestMethod]
    public void GetDisplayName_PerformanceTest()
    {
        // Arrange
        var resolver = new TradingPointNameResolver(connectionString);
        var ttIds = Enumerable.Range(460000, 1000).ToArray();
        
        // Act
        var stopwatch = Stopwatch.StartNew();
        var results = resolver.GetDisplayNames(ttIds);
        stopwatch.Stop();
        
        // Assert
        Assert.IsTrue(stopwatch.ElapsedMilliseconds < 5000); // Менее 5 секунд
        Assert.AreEqual(ttIds.Length, results.Count);
    }
    
    [TestMethod]
    public void GenerateReport_PerformanceTest()
    {
        // Arrange
        var generator = new ReportGenerator(connectionString);
        var clientIds = Enumerable.Range(1, 100).ToArray();
        
        // Act
        var stopwatch = Stopwatch.StartNew();
        var reports = new List<string>();
        
        foreach (var clientId in clientIds)
        {
            reports.Add(generator.GenerateClientReport(clientId));
        }
        
        stopwatch.Stop();
        
        // Assert
        Assert.IsTrue(stopwatch.ElapsedMilliseconds < 30000); // Менее 30 секунд
        Assert.AreEqual(clientIds.Length, reports.Count);
    }
}
```

## План тестирования

### Фаза 1: Подготовка (1 день)
- [ ] Настройка тестовой среды
- [ ] Подготовка тестовых данных
- [ ] Настройка автоматизации
- [ ] Создание тестовых пользователей

### Фаза 2: Unit тестирование (1 день)
- [ ] Тестирование TradingPointNameResolver
- [ ] Тестирование ReportGenerator
- [ ] Тестирование валидации данных
- [ ] Тестирование обработки ошибок

### Фаза 3: Интеграционное тестирование (1 день)
- [ ] Тестирование полного цикла
- [ ] Тестирование с кэшированием
- [ ] Тестирование с различными типами данных
- [ ] Тестирование производительности

### Фаза 4: Регрессионное тестирование (1 день)
- [ ] Тестирование существующих отчетов
- [ ] Тестирование производительности системы
- [ ] Тестирование совместимости
- [ ] Финальная проверка

## Критерии готовности к продакшену

### Функциональные критерии
- [ ] Все тест-кейсы пройдены успешно
- [ ] ТТ с KA_NAME отображаются корректно
- [ ] ТТ без KA_NAME используют fallback логику
- [ ] Специальные символы обрабатываются правильно

### Технические критерии
- [ ] Производительность в пределах нормы
- [ ] Память используется эффективно
- [ ] Ошибок в логах нет
- [ ] Кэширование работает корректно

### Качественные критерии
- [ ] Покрытие тестами > 90%
- [ ] Время выполнения тестов < 1 часа
- [ ] Количество багов = 0
- [ ] Документация обновлена

## Отчетность

### Ежедневные отчеты
- Статус выполнения тестов
- Найденные баги
- Блокеры и риски
- План на следующий день

### Финальный отчет
- Общая статистика тестирования
- Список найденных и исправленных багов
- Рекомендации по улучшению
- Заключение о готовности к продакшену

## Контакты

### Команда тестирования
- **Руководитель тестирования**: [Имя руководителя]
- **Функциональный тестировщик**: [Имя тестировщика]
- **Автоматизатор**: [Имя автоматизатора]
- **Тестировщик производительности**: [Имя тестировщика]

### Эскалация проблем
- **Критические баги**: Немедленно
- **Блокеры**: В течение 2 часов
- **Обычные баги**: В течение 1 дня
- **Улучшения**: В течение недели

---
*Документ создан: 27.09.2025*  
*Версия: 1.0*  
*Статус: Готов к использованию*
