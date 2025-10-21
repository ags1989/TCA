# Техническое решение: Ладога. МТ. Транзитные заказы

## Архитектура решения

### Общая схема
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Мобильный     │    │   Чикаго        │    │   1С            │
│   Терминал      │    │                 │    │                 │
│                 │    │                 │    │                 │
│ - Выбор типа    │───►│ - Обработка     │───►│ - Учетная       │
│ - Префиксы      │    │ - Валидация     │    │   система       │
│ - Отгрузка      │    │ - Синхронизация │    │ - Документооборот│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Компоненты системы

#### 1. Мобильный терминал (МТ)
- **Форма заказа**: Расширенная форма с выбором типа заказа
- **Компонент выбора**: Кастомный компонент для выбора параметров
- **Валидация**: Клиентская валидация выбранных параметров
- **Синхронизация**: Передача данных в Чикаго

#### 2. Чикаго (Backend)
- **API**: Обработка запросов от МТ
- **Бизнес-логика**: Валидация и обработка транзитных заказов
- **Интеграция**: Синхронизация с 1С
- **База данных**: Хранение параметров заказов

#### 3. 1С (Учетная система)
- **Прием данных**: Обработка параметров транзитных заказов
- **Документооборот**: Создание документов с учетом префиксов
- **Отчетность**: Формирование отчетов по транзитным заказам

## Варианты реализации

### Вариант 1: Кастомный компонент ввода
**Описание**: Создание специального компонента ввода в форме реквизитов заказа

**Преимущества**:
- Интеграция в существующий интерфейс
- Единообразный пользовательский опыт
- Гибкость в настройке

**Недостатки**:
- Высокая стоимость разработки (380-500 тыс. руб.)
- Сложность реализации
- Ограничения в динамических изменениях

**Технические детали**:
```csharp
public class TransitOrderComponent : UserControl
{
    public OrderType OrderType { get; set; }
    public string Prefix { get; set; }
    public string ShippingPoint { get; set; }
    
    public void ValidateSelection()
    {
        // Валидация выбранных параметров
    }
}
```

### Вариант 2: Диалоговое окно
**Описание**: Отдельное диалоговое окно для выбора параметров транзитного заказа

**Преимущества**:
- Простота реализации
- Средняя стоимость (300-400 тыс. руб.)
- Четкое разделение логики

**Недостатки**:
- Дополнительный шаг для пользователя
- Отделение от основного процесса

**Технические детали**:
```csharp
public class TransitOrderDialog : Form
{
    public TransitOrderParameters ShowDialog()
    {
        // Отображение диалога выбора параметров
        return selectedParameters;
    }
}
```

### Вариант 3: Серийные диалоговые окна
**Описание**: Последовательные диалоги для выбора каждого параметра

**Преимущества**:
- Низкая стоимость (200-250 тыс. руб.)
- Простота реализации
- Только доработка МТ

**Недостатки**:
- Многошаговый процесс
- Потенциальная путаница для пользователя

## Выбранное решение

### Реализованный вариант
Выбран **Вариант 1** с элементами **Варианта 2**:
- Кастомный компонент в форме заказа
- Дополнительные диалоги для сложных выборов
- Интеграция с существующим интерфейсом

### Обоснование выбора
1. **Пользовательский опыт**: Интеграция в существующий интерфейс
2. **Функциональность**: Полная поддержка всех требований
3. **Гибкость**: Возможность расширения в будущем
4. **Стоимость**: Приемлемая стоимость для требуемой функциональности

## Техническая реализация

### 1. Модель данных

#### Структура транзитного заказа
```csharp
public class TransitOrder
{
    public int Id { get; set; }
    public OrderType Type { get; set; }
    public string Prefix { get; set; }
    public string ShippingPoint { get; set; }
    public DateTime ShippingDate { get; set; }
    public string Counterparty { get; set; }
    public List<OrderItem> Items { get; set; }
}

public enum OrderType
{
    Regular,        // Обычный заказ
    TransitLD,      // Транзит через розничную ЛД
    TransitMonopol  // Транзит через Монополь
}
```

#### Префиксы заказов
```csharp
public class OrderPrefix
{
    public string Code { get; set; }
    public string Description { get; set; }
    public OrderType Type { get; set; }
    public bool IsActive { get; set; }
}

// Префиксы для Монополь
var monopolPrefixes = new List<OrderPrefix>
{
    new() { Code = "П", Description = "Оплата водителю наличными (без чека)" },
    new() { Code = "О", Description = "Оплата наличными ответственному сотруднику" },
    new() { Code = "Ч", Description = "Оплата водителю наличными + чек" },
    new() { Code = "Б", Description = "Безналичный расчет" },
    new() { Code = "Ю", Description = "QR-код по безналичному расчету" },
    new() { Code = "А", Description = "Безналичный расчет через третье лицо" },
    new() { Code = "Т", Description = "Банковский терминал" },
    new() { Code = "Д", Description = "Безналичный расчет (БАКалея)" },
    new() { Code = "Н", Description = "Безналичный расчет с НДС" }
};

// Префиксы для розничной ЛД
var ldPrefixes = new List<OrderPrefix>
{
    new() { Code = "V", Description = "Транзит через розничную продажу" },
    new() { Code = "Б", Description = "Безналичный расчет с НДС" },
    new() { Code = "О", Description = "Безналичный расчет с НДС + отсрочка" },
    new() { Code = "С", Description = "Транзит + оплата сертификатами" }
};
```

### 2. Пользовательский интерфейс

#### Компонент выбора типа заказа
```csharp
public partial class OrderTypeSelector : UserControl
{
    public event EventHandler<OrderTypeChangedEventArgs> OrderTypeChanged;
    
    private void OnOrderTypeChanged(OrderType orderType)
    {
        OrderTypeChanged?.Invoke(this, new OrderTypeChangedEventArgs(orderType));
    }
    
    private void UpdateAvailableOptions(OrderType orderType)
    {
        switch (orderType)
        {
            case OrderType.Regular:
                HideTransitOptions();
                break;
            case OrderType.TransitLD:
                ShowLDPrefixes();
                break;
            case OrderType.TransitMonopol:
                ShowMonopolOptions();
                break;
        }
    }
}
```

#### Диалог выбора параметров Монополь
```csharp
public partial class MonopolSelectionDialog : Form
{
    public MonopolSelectionResult ShowSelectionDialog()
    {
        LoadMonopolStores();
        LoadAvailablePrefixes();
        
        if (ShowDialog() == DialogResult.OK)
        {
            return new MonopolSelectionResult
            {
                Store = SelectedStore,
                Prefix = SelectedPrefix,
                IsValid = ValidateSelection()
            };
        }
        
        return null;
    }
    
    private bool ValidateSelection()
    {
        return !string.IsNullOrEmpty(SelectedStore) && 
               !string.IsNullOrEmpty(SelectedPrefix);
    }
}
```

### 3. Бизнес-логика

#### Валидация заказа
```csharp
public class OrderValidator
{
    public ValidationResult ValidateTransitOrder(TransitOrder order)
    {
        var result = new ValidationResult();
        
        if (order.Type == OrderType.TransitLD)
        {
            ValidateLDPrefix(order.Prefix, result);
        }
        else if (order.Type == OrderType.TransitMonopol)
        {
            ValidateMonopolSelection(order.ShippingPoint, order.Prefix, result);
        }
        
        ValidateShippingDate(order.ShippingDate, result);
        
        return result;
    }
    
    private void ValidateLDPrefix(string prefix, ValidationResult result)
    {
        var validPrefixes = new[] { "V", "Б", "О", "С" };
        if (!validPrefixes.Contains(prefix))
        {
            result.AddError("Недопустимый префикс для транзита через ЛД");
        }
    }
    
    private void ValidateMonopolSelection(string store, string prefix, ValidationResult result)
    {
        if (string.IsNullOrEmpty(store))
        {
            result.AddError("Не выбран магазин Монополь");
        }
        
        if (string.IsNullOrEmpty(prefix))
        {
            result.AddError("Не выбран префикс заказа");
        }
    }
}
```

#### Обработка даты отгрузки
```csharp
public class ShippingDateCalculator
{
    public DateTime CalculateShippingDate(OrderType orderType, DateTime clientShippingDate)
    {
        switch (orderType)
        {
            case OrderType.TransitLD:
            case OrderType.TransitMonopol:
                // Для транзитных заказов дата отгрузки = дата отгрузки клиента - 1 день
                return clientShippingDate.AddDays(-1);
            default:
                return clientShippingDate;
        }
    }
}
```

### 4. Интеграция с 1С

#### API для передачи данных
```csharp
public class OrderIntegrationService
{
    public async Task<bool> SendOrderTo1C(TransitOrder order)
    {
        var orderData = new
        {
            OrderId = order.Id,
            Type = order.Type.ToString(),
            Prefix = order.Prefix,
            ShippingPoint = order.ShippingPoint,
            ShippingDate = order.ShippingDate,
            Counterparty = order.Counterparty,
            Items = order.Items.Select(i => new
            {
                ProductId = i.ProductId,
                Quantity = i.Quantity,
                Price = i.Price
            })
        };
        
        var response = await _httpClient.PostAsJsonAsync("/api/orders", orderData);
        return response.IsSuccessStatusCode;
    }
}
```

#### Конфигурация интеграции
```xml
<configuration>
  <appSettings>
    <add key="1C.Integration.Enabled" value="true" />
    <add key="1C.Integration.BaseUrl" value="http://1c-server/api" />
    <add key="1C.Integration.Timeout" value="30000" />
    <add key="1C.Integration.RetryCount" value="3" />
  </appSettings>
</configuration>
```

## Конфигурация системы

### Настройки префиксов
```json
{
  "orderPrefixes": {
    "monopol": [
      {
        "code": "П",
        "description": "Оплата водителю наличными (без чека)",
        "isActive": true
      },
      {
        "code": "О", 
        "description": "Оплата наличными ответственному сотруднику",
        "isActive": true
      }
    ],
    "ld": [
      {
        "code": "V",
        "description": "Транзит через розничную продажу",
        "isActive": true
      },
      {
        "code": "Б",
        "description": "Безналичный расчет с НДС",
        "isActive": true
      }
    ]
  }
}
```

### Настройки магазинов Монополь
```json
{
  "monopolStores": [
    {
      "id": "monopol-001",
      "name": "Монополь",
      "isActive": true
    },
    {
      "id": "monopol-m-001", 
      "name": "Монополь-М",
      "isActive": true
    },
    {
      "id": "monopol-br-001",
      "name": "Монополь-БР", 
      "isActive": true
    },
    {
      "id": "monopol-market-001",
      "name": "Монополь-Маркет",
      "isActive": true
    },
    {
      "id": "ran-trade-001",
      "name": "Ран-Трейд",
      "isActive": true
    }
  ]
}
```

## Производительность и масштабируемость

### Оптимизации
1. **Кэширование**: Кэширование списков префиксов и магазинов
2. **Асинхронность**: Асинхронная передача данных в 1С
3. **Валидация**: Клиентская валидация для снижения нагрузки на сервер
4. **Пакетная обработка**: Группировка запросов к 1С

### Мониторинг
```csharp
public class TransitOrderMetrics
{
    public int TotalTransitOrders { get; set; }
    public int SuccessfulIntegrations { get; set; }
    public int FailedIntegrations { get; set; }
    public TimeSpan AverageProcessingTime { get; set; }
    
    public void RecordOrder(TransitOrder order, bool success, TimeSpan processingTime)
    {
        TotalTransitOrders++;
        if (success)
            SuccessfulIntegrations++;
        else
            FailedIntegrations++;
        
        AverageProcessingTime = CalculateAverage(processingTime);
    }
}
```

## Безопасность

### Валидация данных
- Проверка корректности выбранных параметров
- Валидация дат отгрузки
- Проверка прав доступа к функциям

### Аудит
```csharp
public class TransitOrderAudit
{
    public void LogOrderCreation(TransitOrder order, string userId)
    {
        var auditEntry = new
        {
            Timestamp = DateTime.UtcNow,
            UserId = userId,
            OrderId = order.Id,
            OrderType = order.Type.ToString(),
            Prefix = order.Prefix,
            ShippingPoint = order.ShippingPoint,
            Action = "OrderCreated"
        };
        
        _auditService.Log(auditEntry);
    }
}
```

## Заключение

### Реализованные возможности
- ✅ Выбор типа заказа (обычный/транзитный)
- ✅ Выбор префиксов для Монополь и ЛД
- ✅ Выбор магазинов Монополь
- ✅ Валидация параметров
- ✅ Интеграция с 1С
- ✅ Расчет даты отгрузки

### Технические преимущества
- **Модульность**: Четкое разделение компонентов
- **Расширяемость**: Легкое добавление новых префиксов
- **Производительность**: Оптимизированная обработка
- **Надежность**: Валидация и обработка ошибок

### Следующие шаги
1. **Пилотное тестирование**: Запуск на ограниченной группе пользователей
2. **Мониторинг**: Отслеживание производительности и ошибок
3. **Оптимизация**: Улучшение на основе обратной связи
4. **Расширение**: Добавление новых функций при необходимости

---
*Документ создан: 27.09.2025*  
*Версия: 1.0*  
*Статус: Реализовано*
