# Руководство по развертыванию: ATYASHEVO Сервис УКБ. Инд. критерий для исключения повторного распознавания адреса

## Обзор развертывания

### Цель развертывания
Развернуть функциональность классификатора "Отправлять на распознавание" в продуктивном окружении, обеспечив стабильную работу управления отправкой торговых точек на распознавание адресов.

### Компоненты для развертывания
- **База данных**: Обновления схемы с таблицами классификаторов
- **Чикаго**: Обновленная версия с поддержкой классификатора
- **Сервис РиГ**: Настроенная логика обработки классификатора
- **API**: Обновленные эндпоинты для управления классификаторами

### Требования к развертыванию
- **Время простоя**: Минимальное (не более 1 часа)
- **Откат**: Возможность быстрого отката к предыдущей версии
- **Мониторинг**: Отслеживание работы новой функциональности
- **Обучение**: Подготовка пользователей

## Подготовка к развертыванию

### 1. Проверка готовности

#### Проверка кода
- [ ] Все тесты пройдены успешно
- [ ] Код проверен на соответствие стандартам
- [ ] Документация обновлена
- [ ] Версия помечена для релиза

#### Проверка окружения
- [ ] Тестовое окружение работает корректно
- [ ] База данных готова к обновлению
- [ ] Сервис РиГ готов к интеграции
- [ ] Резервные копии созданы

#### Проверка зависимостей
- [ ] Сервис РиГ готов к приему обновлений
- [ ] Сетевые подключения стабильны
- [ ] Ресурсы серверов достаточны
- [ ] Мониторинг настроен

### 2. Создание резервных копий

#### Резервная копия базы данных
```sql
-- Создание полной резервной копии
BACKUP DATABASE [Chicago] 
TO DISK = 'C:\Backups\Chicago_Before_Classifier.bak'
WITH FORMAT, INIT, COMPRESSION;

-- Проверка целостности
RESTORE VERIFYONLY 
FROM DISK = 'C:\Backups\Chicago_Before_Classifier.bak';
```

#### Резервная копия конфигурации
```powershell
# Копирование конфигурационных файлов
Copy-Item "C:\Chicago\Config\*" "C:\Backups\Config_Backup\" -Recurse

# Копирование файлов приложения
Copy-Item "C:\Chicago\App\*" "C:\Backups\App_Backup\" -Recurse
```

#### Резервная копия сервиса РиГ
- Экспорт конфигурации сервиса РиГ
- Создание резервной копии базы данных сервиса
- Сохранение настроек интеграции

### 3. Подготовка скриптов развертывания

#### Скрипт обновления базы данных
```sql
-- Создание таблицы классификаторов
CREATE TABLE [dbo].[refOutletClassifiers] (
    [Id] INT IDENTITY(1,1) PRIMARY KEY,
    [OutletId] INT NOT NULL,
    [ClassifierCode] NVARCHAR(50) NOT NULL,
    [ClassifierValue] NVARCHAR(10) NULL,
    [CreatedDate] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [ModifiedDate] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [CreatedBy] NVARCHAR(100) NULL,
    [ModifiedBy] NVARCHAR(100) NULL,
    
    CONSTRAINT [FK_refOutletClassifiers_Outlets] 
        FOREIGN KEY ([OutletId]) REFERENCES [dbo].[refOutlets]([Id]),
    CONSTRAINT [FK_refOutletClassifiers_Classifiers] 
        FOREIGN KEY ([ClassifierCode]) REFERENCES [dbo].[refClassifiers]([Code])
);

-- Создание таблицы справочника классификаторов
CREATE TABLE [dbo].[refClassifiers] (
    [Id] INT IDENTITY(1,1) PRIMARY KEY,
    [Code] NVARCHAR(50) NOT NULL UNIQUE,
    [Name] NVARCHAR(255) NOT NULL,
    [Description] NVARCHAR(500) NULL,
    [IsActive] BIT NOT NULL DEFAULT 1,
    [CreatedDate] DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);

-- Вставка классификатора "Отправлять на распознавание"
INSERT INTO [dbo].[refClassifiers] ([Code], [Name], [Description])
VALUES ('SEND_FOR_RECOGNITION', 'Отправлять на распознавание', 
        'Классификатор для управления отправкой торговых точек на распознавание адресов');

-- Добавление поля для быстрого доступа к классификатору
ALTER TABLE [dbo].[refOutlets] 
ADD [SendForRecognition] NVARCHAR(10) NULL;

-- Создание индексов для производительности
CREATE INDEX IX_refOutletClassifiers_OutletId ON [dbo].[refOutletClassifiers] ([OutletId]);
CREATE INDEX IX_refOutletClassifiers_ClassifierCode ON [dbo].[refOutletClassifiers] ([ClassifierCode]);
CREATE INDEX IX_refOutletClassifiers_Value ON [dbo].[refOutletClassifiers] ([ClassifierValue]);
CREATE INDEX IX_refOutlets_SendForRecognition ON [dbo].[refOutlets] ([SendForRecognition]);

-- Создание таблицы аудита классификаторов
CREATE TABLE [dbo].[ClassifierAuditLog] (
    [Id] INT IDENTITY(1,1) PRIMARY KEY,
    [OutletId] INT NOT NULL,
    [ClassifierCode] NVARCHAR(50) NOT NULL,
    [OldValue] NVARCHAR(10) NULL,
    [NewValue] NVARCHAR(10) NULL,
    [UserId] NVARCHAR(100) NULL,
    [Timestamp] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [Action] NVARCHAR(50) NOT NULL
);

CREATE INDEX IX_ClassifierAuditLog_OutletId ON [dbo].[ClassifierAuditLog] ([OutletId]);
CREATE INDEX IX_ClassifierAuditLog_Timestamp ON [dbo].[ClassifierAuditLog] ([Timestamp]);
```

#### Скрипт обновления конфигурации
```xml
<!-- Обновление конфигурации Чикаго -->
<configuration>
  <appSettings>
    <!-- Существующие настройки -->
    <add key="Database.ConnectionString" value="..." />
    
    <!-- Новые настройки для классификаторов -->
    <add key="Classifiers.Enabled" value="true" />
    <add key="Classifiers.SendForRecognition.Code" value="SEND_FOR_RECOGNITION" />
    <add key="Classifiers.SendForRecognition.DefaultValue" value="0" />
    <add key="Classifiers.SendForRecognition.AllowedValues" value="0,1,2" />
    <add key="Classifiers.AutoStatusChange" value="true" />
    <add key="Classifiers.AuditEnabled" value="true" />
  </appSettings>
  
  <system.web>
    <!-- Настройки для обработки классификаторов -->
    <httpRuntime maxRequestLength="10240" executionTimeout="300" />
  </system.web>
</configuration>
```

#### Скрипт обновления сервиса РиГ
```powershell
# Скрипт обновления сервиса РиГ
param(
    [string]$ServicePath = "C:\RecognitionService",
    [string]$BackupPath = "C:\Backups\RecognitionService_Backup"
)

# Создание резервной копии
Write-Host "Создание резервной копии сервиса РиГ..."
Copy-Item $ServicePath $BackupPath -Recurse -Force

# Остановка службы
Write-Host "Остановка службы РиГ..."
Stop-Service -Name "RecognitionService" -Force

# Копирование новых файлов
Write-Host "Копирование новых файлов..."
Copy-Item ".\NewFiles\*" $ServicePath -Recurse -Force

# Обновление конфигурации
Write-Host "Обновление конфигурации..."
Copy-Item ".\Config\RecognitionService.config" "$ServicePath\config\"

# Запуск службы
Write-Host "Запуск службы РиГ..."
Start-Service -Name "RecognitionService"

# Проверка статуса
Write-Host "Проверка статуса службы..."
Get-Service -Name "RecognitionService"
```

## Процесс развертывания

### Этап 1: Подготовка (15 минут)

#### 1.1 Уведомление пользователей
- Отправка уведомления о плановом обслуживании
- Информирование о времени простоя
- Подготовка инструкций для пользователей

#### 1.2 Финальная проверка
- Проверка готовности всех компонентов
- Проверка резервных копий
- Проверка скриптов развертывания

### Этап 2: Развертывание базы данных (20 минут)

#### 2.1 Остановка приложений
```powershell
# Остановка служб
Stop-Service -Name "Chicago" -Force
Stop-Service -Name "RecognitionService" -Force
Stop-Service -Name "IntegrationService" -Force
```

#### 2.2 Обновление базы данных
```sql
-- Выполнение скриптов обновления
-- Проверка целостности данных
-- Создание индексов
-- Обновление статистики
```

#### 2.3 Проверка обновления
```sql
-- Проверка создания таблиц
SELECT COUNT(*) FROM [dbo].[refOutletClassifiers];
SELECT COUNT(*) FROM [dbo].[refClassifiers];

-- Проверка данных
SELECT * FROM [dbo].[refClassifiers] WHERE [Code] = 'SEND_FOR_RECOGNITION';
```

### Этап 3: Развертывание приложений (15 минут)

#### 3.1 Обновление Чикаго
```powershell
# Копирование новых файлов
Copy-Item ".\Chicago\*" "C:\Chicago\" -Recurse -Force

# Обновление конфигурации
Copy-Item ".\Config\Chicago.config" "C:\Chicago\config\"

# Запуск службы
Start-Service -Name "Chicago"
```

#### 3.2 Обновление сервиса РиГ
```powershell
# Выполнение скрипта обновления сервиса РиГ
.\Update-RecognitionService.ps1 -ServicePath "C:\RecognitionService"
```

#### 3.3 Обновление службы интеграции
```powershell
# Обновление службы интеграции
Copy-Item ".\IntegrationService\*" "C:\IntegrationService\" -Recurse -Force
Start-Service -Name "IntegrationService"
```

### Этап 4: Настройка классификатора (10 минут)

#### 4.1 Инициализация классификатора
```sql
-- Проверка создания классификатора
SELECT * FROM [dbo].[refClassifiers] WHERE [Code] = 'SEND_FOR_RECOGNITION';

-- Установка значений по умолчанию для существующих ТТ
UPDATE [dbo].[refOutlets] 
SET [SendForRecognition] = '0' 
WHERE [SendForRecognition] IS NULL;
```

#### 4.2 Настройка мониторинга
```powershell
# Настройка мониторинга классификаторов
Set-EventLog -LogName "Application" -Source "ClassifierService" -Enabled $true
```

### Этап 5: Тестирование (15 минут)

#### 5.1 Базовое тестирование
- Проверка запуска всех служб
- Проверка подключения к базе данных
- Проверка работы API классификаторов

#### 5.2 Функциональное тестирование
- Создание тестовой ТТ с классификатором
- Проверка отправки на распознавание
- Проверка автоматической смены статусов

### Этап 6: Запуск в продуктив (5 минут)

#### 6.1 Постепенный запуск
- Включение функциональности для тестовых пользователей
- Мониторинг работы системы
- Постепенное расширение на всех пользователей

#### 6.2 Финальная проверка
- Проверка всех компонентов
- Мониторинг производительности
- Проверка логов на ошибки

## Проверка развертывания

### 1. Проверка компонентов

#### Проверка служб
```powershell
# Проверка статуса всех служб
Get-Service -Name "Chicago", "RecognitionService", "IntegrationService"

# Проверка логов
Get-EventLog -LogName "Application" -Source "Chicago" -Newest 10
Get-EventLog -LogName "Application" -Source "ClassifierService" -Newest 10
```

#### Проверка базы данных
```sql
-- Проверка целостности
DBCC CHECKDB('Chicago');

-- Проверка новых таблиц
SELECT COUNT(*) FROM [dbo].[refOutletClassifiers];
SELECT COUNT(*) FROM [dbo].[refClassifiers];

-- Проверка производительности
SELECT * FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'DETAILED');
```

### 2. Функциональная проверка

#### Создание тестовой ТТ
1. Открыть Чикаго
2. Создать тестовую ТТ
3. Установить классификатор "1"
4. Проверить отправку на распознавание

#### Проверка API
- Проверка эндпоинтов управления классификаторами
- Проверка валидации данных
- Проверка аудита операций

### 3. Мониторинг

#### Ключевые метрики
- **Производительность**: Время отклика системы
- **Ошибки**: Количество ошибок в логах
- **Классификаторы**: Использование разных значений
- **Распознавание**: Успешность отправки на распознавание

#### Настройка алертов
```powershell
# Настройка алертов для критических ошибок
$Alert = @{
    Name = "ClassifierError"
    Query = "EventLog[Application] | where Source == 'ClassifierService' and Level == 'Error'"
    Threshold = 5
    Action = "Send-Email -To 'admin@company.com' -Subject 'Classifier Service Error'"
}
```

## План отката

### Условия для отката
- Критические ошибки в работе системы
- Проблемы с производительностью
- Невозможность создания/редактирования ТТ
- Проблемы с распознаванием адресов

### Процедура отката

#### 1. Немедленный откат (10 минут)
```powershell
# Остановка всех служб
Stop-Service -Name "Chicago", "RecognitionService", "IntegrationService" -Force

# Восстановление из резервной копии
Restore-Database -Database "Chicago" -BackupFile "C:\Backups\Chicago_Before_Classifier.bak"

# Восстановление приложений
Copy-Item "C:\Backups\App_Backup\*" "C:\Chicago\" -Recurse -Force
Copy-Item "C:\Backups\RecognitionService_Backup\*" "C:\RecognitionService\" -Recurse -Force

# Запуск служб
Start-Service -Name "Chicago", "RecognitionService", "IntegrationService"
```

#### 2. Проверка отката
- Проверка работы всех служб
- Проверка базы данных
- Тестирование основной функциональности
- Уведомление пользователей

### Восстановление после отката
1. Анализ причин проблем
2. Исправление найденных ошибок
3. Повторное тестирование
4. Планирование повторного развертывания

## Обучение пользователей

### 1. Подготовка материалов
- Инструкции по использованию классификатора
- Видео-уроки
- FAQ по часто задаваемым вопросам
- Контакты для поддержки

### 2. Проведение обучения
- Групповые сессии для администраторов
- Индивидуальные консультации
- Демонстрация функциональности
- Практические упражнения

### 3. Поддержка после развертывания
- Горячая линия поддержки
- Онлайн-чат с поддержкой
- База знаний
- Регулярные обновления

## Мониторинг и поддержка

### 1. Ежедневный мониторинг
- Проверка логов на ошибки
- Мониторинг производительности
- Проверка работы классификаторов
- Анализ использования функциональности

### 2. Еженедельный анализ
- Статистика использования классификаторов
- Анализ производительности
- Обратная связь от пользователей
- Планирование улучшений

### 3. Ежемесячный отчет
- Общая статистика работы
- Найденные проблемы и их решения
- Рекомендации по улучшению
- Планы на следующий месяц

## Заключение

### Критерии успешного развертывания
- ✅ Все службы работают стабильно
- ✅ Классификатор функционирует корректно
- ✅ Пользователи могут управлять классификаторами
- ✅ Производительность не снизилась
- ✅ Нет критических ошибок

### Следующие шаги
1. **Мониторинг**: Отслеживание работы системы
2. **Поддержка**: Помощь пользователям
3. **Оптимизация**: Улучшение на основе обратной связи
4. **Развитие**: Добавление новых функций

### Контакты для поддержки
- **Техническая поддержка**: support@company.com
- **Горячая линия**: +7 (XXX) XXX-XX-XX
- **Документация**: https://docs.company.com/classifiers

---
*Документ создан: 27.09.2025*  
*Версия: 1.0*  
*Статус: Готово к развертыванию*
