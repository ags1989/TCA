# Руководство по устранению неполадок: OLAP Логирование

## Обзор

### Назначение документа
Данное руководство предназначено для быстрого диагностирования и устранения проблем с логированием запросов к OLAP системе в рамках проекта ST (Сопровождение).

### Целевая аудитория
- Инженеры поддержки BigGoodTeam
- Администраторы системы
- Специалисты по мониторингу
- Инженеры DevOps

### Связанные системы
- **OLAP система**: Аналитическая обработка данных
- **Система логирования**: Сбор и хранение логов запросов
- **Планировщик задач**: Запуск джобов проверки логирования
- **База данных**: Хранение логов и метаданных

## Диагностика проблем

### 1. Проверка статуса логирования

#### Шаг 1.1: Проверка работы джоба
```bash
# Проверка статуса джоба логирования
ps aux | grep "olap_logging_job"

# Проверка логов джоба
tail -f /var/log/olap/logging_job.log

# Проверка расписания джоба
crontab -l | grep olap
```

#### Шаг 1.2: Проверка последних записей в логе
```sql
-- Проверка последних записей в таблице логов OLAP
SELECT TOP 10 
    log_id,
    query_text,
    execution_time,
    created_date,
    status
FROM olap_query_logs 
ORDER BY created_date DESC;

-- Проверка количества записей за последние 24 часа
SELECT COUNT(*) as log_count
FROM olap_query_logs 
WHERE created_date >= DATEADD(hour, -24, GETDATE());
```

#### Шаг 1.3: Проверка доступности OLAP
```bash
# Проверка подключения к OLAP серверу
telnet olap-server.company.com 1433

# Проверка доступности через PowerShell
Test-NetConnection -ComputerName "olap-server.company.com" -Port 1433
```

### 2. Диагностика джоба логирования

#### Шаг 2.1: Проверка конфигурации джоба
```bash
# Проверка конфигурационного файла
cat /etc/olap/logging_job.conf

# Проверка переменных окружения
env | grep OLAP

# Проверка прав доступа к файлам
ls -la /var/log/olap/
```

#### Шаг 2.2: Проверка ресурсов системы
```bash
# Проверка использования CPU
top -p $(pgrep olap_logging_job)

# Проверка использования памяти
ps -o pid,ppid,cmd,%mem,%cpu -p $(pgrep olap_logging_job)

# Проверка дискового пространства
df -h /var/log/olap/
```

#### Шаг 2.3: Проверка логов системы
```bash
# Проверка системных логов
journalctl -u olap-logging-service -f

# Проверка логов планировщика
grep "olap" /var/log/cron.log

# Проверка логов базы данных
tail -f /var/log/mssql/error.log
```

### 3. Диагностика подключения к OLAP

#### Шаг 3.1: Проверка сетевого подключения
```bash
# Ping до OLAP сервера
ping olap-server.company.com

# Проверка DNS разрешения
nslookup olap-server.company.com

# Проверка портов
nmap -p 1433 olap-server.company.com
```

#### Шаг 3.2: Проверка аутентификации
```bash
# Тест подключения к базе данных
sqlcmd -S olap-server.company.com -U username -P password -Q "SELECT 1"

# Проверка строки подключения в конфигурации
grep -i "connection" /etc/olap/logging_job.conf
```

## Устранение неполадок

### Сценарий 1: Джоб не запускается

#### Симптомы
- Джоб не отображается в списке процессов
- Отсутствуют записи в логах за последние часы
- Алерты о неработающем логировании

#### Диагностика
```bash
# Проверка статуса сервиса
systemctl status olap-logging-service

# Проверка конфигурации cron
crontab -l | grep olap

# Проверка логов запуска
journalctl -u olap-logging-service --since "1 hour ago"
```

#### Решение
```bash
# Перезапуск сервиса
sudo systemctl restart olap-logging-service

# Проверка статуса после перезапуска
systemctl status olap-logging-service

# Ручной запуск джоба
sudo -u olap-user /opt/olap/scripts/logging_job.sh
```

### Сценарий 2: Джоб запускается, но не работает

#### Симптомы
- Джоб отображается в процессах
- Отсутствуют записи в таблице логов
- Ошибки в логах джоба

#### Диагностика
```bash
# Проверка логов джоба
tail -f /var/log/olap/logging_job.log

# Проверка подключения к базе данных
sqlcmd -S olap-server.company.com -U username -P password -Q "SELECT COUNT(*) FROM olap_query_logs"

# Проверка прав доступа
ls -la /var/log/olap/
```

#### Решение
```bash
# Исправление прав доступа
sudo chown -R olap-user:olap-group /var/log/olap/
sudo chmod -R 755 /var/log/olap/

# Перезапуск джоба
sudo systemctl restart olap-logging-service

# Проверка работы
tail -f /var/log/olap/logging_job.log
```

### Сценарий 3: Проблемы с подключением к OLAP

#### Симптомы
- Ошибки подключения к базе данных
- Таймауты при выполнении запросов
- Недоступность OLAP сервера

#### Диагностика
```bash
# Проверка сетевого подключения
ping olap-server.company.com

# Проверка портов
telnet olap-server.company.com 1433

# Проверка DNS
nslookup olap-server.company.com
```

#### Решение
```bash
# Перезапуск сетевых служб
sudo systemctl restart network-manager

# Проверка файрвола
sudo ufw status
sudo ufw allow 1433

# Тест подключения
sqlcmd -S olap-server.company.com -U username -P password -Q "SELECT 1"
```

### Сценарий 4: Недостаток ресурсов

#### Симптомы
- Медленная работа джоба
- Ошибки нехватки памяти
- Высокая нагрузка на CPU

#### Диагностика
```bash
# Проверка использования ресурсов
top -p $(pgrep olap_logging_job)

# Проверка дискового пространства
df -h /var/log/olap/

# Проверка памяти
free -h
```

#### Решение
```bash
# Очистка старых логов
find /var/log/olap/ -name "*.log" -mtime +30 -delete

# Увеличение лимитов памяти
echo "olap-user soft memlock unlimited" >> /etc/security/limits.conf
echo "olap-user hard memlock unlimited" >> /etc/security/limits.conf

# Перезапуск джоба
sudo systemctl restart olap-logging-service
```

## Профилактические меры

### 1. Мониторинг

#### Настройка алертов
```bash
# Скрипт проверки статуса джоба
#!/bin/bash
if ! pgrep -f "olap_logging_job" > /dev/null; then
    echo "ALERT: OLAP logging job is not running" | mail -s "OLAP Alert" admin@company.com
fi
```

#### Дашборд мониторинга
```sql
-- Запрос для дашборда
SELECT 
    DATE(created_date) as log_date,
    COUNT(*) as query_count,
    AVG(execution_time) as avg_execution_time
FROM olap_query_logs 
WHERE created_date >= DATEADD(day, -7, GETDATE())
GROUP BY DATE(created_date)
ORDER BY log_date DESC;
```

### 2. Автоматизация

#### Скрипт автоматического восстановления
```bash
#!/bin/bash
# Автоматическое восстановление джоба логирования

LOG_FILE="/var/log/olap/auto_recovery.log"
JOB_NAME="olap_logging_job"

check_job_status() {
    if ! pgrep -f "$JOB_NAME" > /dev/null; then
        echo "$(date): Job $JOB_NAME is not running" >> $LOG_FILE
        return 1
    fi
    return 0
}

restart_job() {
    echo "$(date): Restarting $JOB_NAME" >> $LOG_FILE
    sudo systemctl restart olap-logging-service
    sleep 10
    
    if check_job_status; then
        echo "$(date): Job $JOB_NAME restarted successfully" >> $LOG_FILE
        return 0
    else
        echo "$(date): Failed to restart $JOB_NAME" >> $LOG_FILE
        return 1
    fi
}

# Основная логика
if ! check_job_status; then
    restart_job
fi
```

#### Настройка cron для автоматической проверки
```bash
# Добавление в crontab
# Проверка каждые 5 минут
*/5 * * * * /opt/olap/scripts/check_logging_job.sh
```

### 3. Резервное копирование

#### Скрипт резервного копирования логов
```bash
#!/bin/bash
# Резервное копирование логов OLAP

BACKUP_DIR="/backup/olap_logs"
LOG_DIR="/var/log/olap"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание директории для бэкапа
mkdir -p "$BACKUP_DIR/$DATE"

# Копирование логов
cp -r "$LOG_DIR"/* "$BACKUP_DIR/$DATE/"

# Сжатие архива
tar -czf "$BACKUP_DIR/olap_logs_$DATE.tar.gz" -C "$BACKUP_DIR" "$DATE"

# Удаление временной директории
rm -rf "$BACKUP_DIR/$DATE"

# Удаление старых бэкапов (старше 30 дней)
find "$BACKUP_DIR" -name "olap_logs_*.tar.gz" -mtime +30 -delete
```

## Эскалация и контакты

### Уровни эскалации

#### Уровень 1: Инженер поддержки
- **Время реакции**: 15 минут
- **Действия**: Базовая диагностика и решение
- **Контакты**: support@company.com

#### Уровень 2: Старший инженер
- **Время реакции**: 30 минут
- **Действия**: Углубленная диагностика
- **Контакты**: senior-support@company.com

#### Уровень 3: Архитектор системы
- **Время реакции**: 1 час
- **Действия**: Архитектурные изменения
- **Контакты**: architect@company.com

### Контакты команды
- **BigGoodTeam Lead**: lead@company.com
- **DevOps Team**: devops@company.com
- **Database Team**: dba@company.com
- **Emergency Hotline**: +7 (XXX) XXX-XX-XX

## Документация и ресурсы

### Внутренние ресурсы
- **Confluence**: https://confluence.company.com/olap
- **Wiki**: https://wiki.company.com/troubleshooting
- **Runbooks**: https://runbooks.company.com/olap

### Внешние ресурсы
- **Microsoft SQL Server Documentation**: https://docs.microsoft.com/sql
- **OLAP Best Practices**: https://docs.microsoft.com/analysis-services
- **Monitoring Tools**: https://docs.microsoft.com/azure/monitoring

## Заключение

### Ключевые принципы
1. **Быстрая диагностика**: Использование систематического подхода
2. **Документирование**: Запись всех действий и результатов
3. **Коммуникация**: Информирование заинтересованных сторон
4. **Обучение**: Постоянное улучшение процедур

### Следующие шаги
1. **Регулярное тестирование**: Проверка процедур восстановления
2. **Обновление документации**: Актуализация руководства
3. **Обучение команды**: Повышение квалификации
4. **Автоматизация**: Внедрение дополнительных автоматических решений

---
*Документ создан: 27.09.2025*  
*Версия: 1.0*  
*Статус: Активно используется*
