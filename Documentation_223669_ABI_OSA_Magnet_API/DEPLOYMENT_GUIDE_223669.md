# Руководство по развертыванию: АБИ. Подключение к новому API OSA Магнит

## Обзор развертывания

### Цель
Обеспечить корректное развертывание интеграции с новым API OSA Магнит V2 в производственной среде.

### Компоненты для развертывания
1. **API интеграция** - подключение к новому API V2
2. **Сертификаты безопасности** - настройка аутентификации
3. **База данных** - создание новых таблиц и индексов
4. **Мобильный терминал** - обновление до версии 3.6.206.5+
5. **Функциональные флаги** - включение поддержки V2

## Предварительные требования

### Системные требования
- **.NET Framework**: 4.7.2 или выше
- **SQL Server**: 2016 или выше
- **Память**: Минимум 8 GB RAM
- **Дисковое пространство**: 20 GB свободного места
- **Сеть**: Доступ к API OSA Магнит

### Доступы и права
- **Администратор БД**: Для создания таблиц и индексов
- **Администратор серверов**: Для установки сертификатов
- **Администратор МТ**: Для обновления мобильных терминалов
- **API доступ**: Доступ к тестовому и продакшн API

### Резервное копирование
- Создать полную резервную копию БД
- Сохранить текущие конфигурации
- Создать точку восстановления системы
- Сохранить текущие сертификаты

## Этапы развертывания

### Этап 1: Подготовка сертификатов

#### 1.1 Получение сертификатов
1. Получить сертификаты от OSA Магнит
2. Проверить валидность сертификатов
3. Убедиться в корректности формата (X.509)

#### 1.2 Установка сертификатов
```bash
# Установка сертификата в хранилище Windows
certlm.msc

# Или через PowerShell
Import-Certificate -FilePath "magnet_client.p12" -CertStoreLocation "Cert:\LocalMachine\My"
```

#### 1.3 Проверка установки
```powershell
# Проверка установленных сертификатов
Get-ChildItem -Path "Cert:\LocalMachine\My" | Where-Object {$_.Subject -like "*Magnet*"}

# Проверка доступа к сертификату
$cert = Get-ChildItem -Path "Cert:\LocalMachine\My" | Where-Object {$_.Subject -like "*Magnet*"}
$cert.HasPrivateKey
```

### Этап 2: Обновление базы данных

#### 2.1 Создание новых таблиц
```sql
-- Таблица для хранения сигналов V2
CREATE TABLE osa_signals_v2 (
    id NVARCHAR(50) PRIMARY KEY,
    signal_id NVARCHAR(50) NOT NULL,
    type NVARCHAR(50),
    store_id NVARCHAR(50),
    product_code NVARCHAR(50),
    issue_type NVARCHAR(100),
    description NVARCHAR(MAX),
    priority NVARCHAR(20),
    status NVARCHAR(20) DEFAULT 'pending',
    created_at DATETIME2,
    due_date DATETIME2,
    resolved_at DATETIME2,
    merchandiser_id NVARCHAR(50),
    created_date DATETIME2 DEFAULT GETDATE(),
    updated_date DATETIME2 DEFAULT GETDATE()
);

-- Таблица для хранения обратной связи V2
CREATE TABLE osa_feedback_v2 (
    id INT IDENTITY(1,1) PRIMARY KEY,
    signal_id NVARCHAR(50) NOT NULL,
    status NVARCHAR(20),
    resolution NVARCHAR(MAX),
    photos NVARCHAR(MAX),
    completed_at DATETIME2,
    merchandiser_id NVARCHAR(50),
    created_at DATETIME2 DEFAULT GETDATE()
);

-- Таблица для кодов проблем
CREATE TABLE osa_problem_codes (
    id INT IDENTITY(1,1) PRIMARY KEY,
    code NVARCHAR(50) NOT NULL,
    description NVARCHAR(MAX),
    category NVARCHAR(50),
    is_active BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETDATE()
);
```

#### 2.2 Создание индексов
```sql
-- Индексы для таблицы сигналов
CREATE INDEX IX_osa_signals_v2_signal_id ON osa_signals_v2(signal_id);
CREATE INDEX IX_osa_signals_v2_store_id ON osa_signals_v2(store_id);
CREATE INDEX IX_osa_signals_v2_status ON osa_signals_v2(status);
CREATE INDEX IX_osa_signals_v2_created_at ON osa_signals_v2(created_at);

-- Индексы для таблицы обратной связи
CREATE INDEX IX_osa_feedback_v2_signal_id ON osa_feedback_v2(signal_id);
CREATE INDEX IX_osa_feedback_v2_merchandiser_id ON osa_feedback_v2(merchandiser_id);

-- Индексы для таблицы кодов проблем
CREATE INDEX IX_osa_problem_codes_code ON osa_problem_codes(code);
CREATE INDEX IX_osa_problem_codes_category ON osa_problem_codes(category);
```

#### 2.3 Создание хранимых процедур
```sql
-- Процедура для получения сигналов
CREATE PROCEDURE sp_GetOsaSignalsV2
    @StoreId NVARCHAR(50) = NULL,
    @Status NVARCHAR(20) = NULL,
    @Priority NVARCHAR(20) = NULL
AS
BEGIN
    SELECT * FROM osa_signals_v2
    WHERE (@StoreId IS NULL OR store_id = @StoreId)
      AND (@Status IS NULL OR status = @Status)
      AND (@Priority IS NULL OR priority = @Priority)
    ORDER BY created_at DESC;
END;

-- Процедура для сохранения обратной связи
CREATE PROCEDURE sp_SaveOsaFeedbackV2
    @SignalId NVARCHAR(50),
    @Status NVARCHAR(20),
    @Resolution NVARCHAR(MAX),
    @Photos NVARCHAR(MAX),
    @MerchandiserId NVARCHAR(50)
AS
BEGIN
    INSERT INTO osa_feedback_v2 (signal_id, status, resolution, photos, merchandiser_id, completed_at)
    VALUES (@SignalId, @Status, @Resolution, @Photos, @MerchandiserId, GETDATE());
    
    UPDATE osa_signals_v2 
    SET status = @Status, resolved_at = GETDATE()
    WHERE signal_id = @SignalId;
END;
```

### Этап 3: Обновление системы

#### 3.1 Обновление до версии 3.6.206.5+
1. **Подготовка**:
   - Создать резервную копию текущей версии
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

#### 3.2 Проверка обновления
```sql
-- Проверка версии системы в БД
SELECT TOP 1 Version FROM SystemInfo 
ORDER BY LastUpdateDate DESC;

-- Ожидаемый результат: 3.6.206.5 или выше
```

### Этап 4: Настройка API интеграции

#### 4.1 Конфигурация подключения
```json
{
  "osa_api": {
    "base_url": "https://api.magnet.ru/osa/v2/",
    "timeout": 30000,
    "retry_attempts": 3,
    "certificate_path": "C:\\Certificates\\magnet_client.p12",
    "certificate_password": "encrypted_password",
    "client_id": "abi_client_id",
    "client_secret": "encrypted_client_secret"
  }
}
```

#### 4.2 Настройка синхронизации
```json
{
  "sync_settings": {
    "signals_interval": 900000,
    "feedback_interval": 300000,
    "max_retries": 5,
    "batch_size": 100,
    "enable_auto_sync": true
  }
}
```

#### 4.3 Настройка уведомлений
```json
{
  "notifications": {
    "email_enabled": true,
    "smtp_server": "smtp.company.com",
    "smtp_port": 587,
    "smtp_username": "noreply@company.com",
    "smtp_password": "encrypted_password",
    "recipients": ["admin@company.com", "support@company.com"],
    "templates": {
      "success": "templates/success.html",
      "error": "templates/error.html",
      "feedback": "templates/feedback.html"
    }
  }
}
```

### Этап 5: Включение функциональных флагов

#### 5.1 Настройка в системе
1. Войти в систему управления функциональными флагами
2. Найти флаг "OSA API V2 Support"
3. Установить значение "Включен"
4. Сохранить изменения

#### 5.2 Проверка активации
```sql
-- Проверка статуса функционального флага
SELECT * FROM FeatureFlags 
WHERE FlagName = 'OSA API V2 Support';

-- Ожидаемый результат: IsEnabled = 1
```

### Этап 6: Тестирование интеграции

#### 6.1 Проверка подключения к API
```bash
# Тест подключения к API
curl -X GET "https://api.magnet.ru/osa/v2/health" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json"

# Ожидаемый ответ
{
  "status": "ok",
  "version": "2.0",
  "timestamp": "2025-09-25T10:00:00Z"
}
```

#### 6.2 Тест получения сигналов
```bash
# Тест получения сигналов
curl -X GET "https://api.magnet.ru/osa/v2/signals" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json"
```

#### 6.3 Тест отправки обратной связи
```bash
# Тест отправки обратной связи
curl -X POST "https://api.magnet.ru/osa/v2/feedback" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "signal_id": "test_signal_001",
    "status": "completed",
    "resolution": "Проблема устранена"
  }'
```

## Мониторинг развертывания

### Логи для отслеживания
1. **Логи API**: `logs/api.log`
2. **Логи системы**: `logs/system.log`
3. **Логи БД**: `logs/database.log`
4. **Логи МТ**: `logs/mobile.log`

### Ключевые метрики
- **Время отклика API**: < 5 секунд
- **Успешность запросов**: > 99%
- **Количество ошибок**: < 1% от общего числа запросов
- **Использование ресурсов**: CPU < 80%, Memory < 8GB

### Команды для проверки
```sql
-- Проверка подключения к БД
SELECT @@VERSION;

-- Проверка созданных таблиц
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME LIKE 'osa_%';

-- Проверка последних сигналов
SELECT TOP 10 * FROM osa_signals_v2 
ORDER BY created_at DESC;
```

## Откат изменений

### Процедура отката
1. **Отключение функциональных флагов**:
   - Установить значение "Отключен"
   - Перезапустить систему

2. **Откат БД**:
   - Восстановить из резервной копии
   - Проверить целостность данных

3. **Откат системы**:
   - Установить предыдущую версию
   - Восстановить настройки

4. **Откат сертификатов**:
   - Восстановить старые сертификаты
   - Перезапустить службы

### Критерии для отката
- Критические ошибки в работе API
- Потеря данных
- Неприемлемая производительность
- Проблемы с безопасностью

## План развертывания

### Подготовительный этап (1 день)
- [ ] Создание резервных копий
- [ ] Подготовка сертификатов
- [ ] Тестирование на тестовом окружении
- [ ] Уведомление пользователей

### Основной этап (4 часа)
- [ ] Установка сертификатов (30 мин)
- [ ] Обновление БД (1 час)
- [ ] Обновление системы (1 час)
- [ ] Настройка API (1 час)
- [ ] Включение флагов (30 мин)

### Контрольный этап (2 часа)
- [ ] Проверка работы всех компонентов
- [ ] Мониторинг логов
- [ ] Тестирование ключевых сценариев
- [ ] Документирование результатов

## Контакты и поддержка

### Команда развертывания
- **Руководитель**: Оздоган Татьяна
- **Разработчик**: Ярочкин Артем
- **Администратор БД**: [Имя администратора БД]
- **Администратор серверов**: [Имя администратора серверов]

### Экстренные контакты
- **Техническая поддержка**: +7-XXX-XXX-XXXX
- **Горячая линия**: support@company.com
- **Чат поддержки**: [Ссылка на чат]

### Документация для справки
- [Техническое решение](TECHNICAL_SOLUTION_223669.md)
- [Руководство по тестированию](TESTING_GUIDE_223669.md)
- [Пользовательская документация](USER_GUIDE_223669.md)

## Чек-лист развертывания

### Предварительные проверки
- [ ] Резервные копии созданы
- [ ] Тестовое окружение проверено
- [ ] Сертификаты получены и проверены
- [ ] Пользователи уведомлены
- [ ] План отката подготовлен

### Развертывание
- [ ] Сертификаты установлены
- [ ] Таблицы БД созданы
- [ ] Индексы созданы
- [ ] Хранимые процедуры созданы
- [ ] Система обновлена
- [ ] API настроен
- [ ] Функциональные флаги включены

### Проверки после развертывания
- [ ] Логи не содержат критических ошибок
- [ ] API подключение работает
- [ ] Получение сигналов функционирует
- [ ] Отправка обратной связи работает
- [ ] МТ синхронизируется корректно
- [ ] Производительность в пределах нормы

### Завершение
- [ ] Документация обновлена
- [ ] Пользователи обучены
- [ ] Мониторинг настроен
- [ ] План поддержки активирован

---
*Документ создан: 27.09.2025*  
*Версия: 1.0*  
*Статус: Готов к использованию*
