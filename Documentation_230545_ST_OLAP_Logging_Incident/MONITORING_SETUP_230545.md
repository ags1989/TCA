# Настройка мониторинга: OLAP Логирование

## Обзор

### Назначение
Данный документ описывает настройку комплексного мониторинга системы логирования OLAP запросов для предотвращения повторения инцидента 230545.

### Цели мониторинга
- **Проактивное обнаружение**: Выявление проблем до их влияния на пользователей
- **Быстрое реагирование**: Минимизация времени восстановления
- **Анализ трендов**: Понимание паттернов использования системы
- **Соответствие требованиям**: Обеспечение аудита и соответствия стандартам

## Архитектура мониторинга

### Компоненты системы мониторинга
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   OLAP System   │    │  Logging Job    │    │   Database      │
│                 │    │                 │    │                 │
│ - Query Engine  │───►│ - Log Collector │───►│ - Query Logs    │
│ - Query Cache   │    │ - Data Parser   │    │ - Metadata      │
│ - Performance   │    │ - Status Check  │    │ - Statistics    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Monitoring    │    │   Alerting      │    │   Dashboard     │
│   Agent         │    │   System        │    │   System        │
│                 │    │                 │    │                 │
│ - Metrics       │    │ - Notifications │    │ - Real-time     │
│ - Health Checks │    │ - Escalation    │    │ - Historical    │
│ - Log Analysis  │    │ - Integration   │    │ - Analytics     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Метрики и индикаторы

### 1. Метрики доступности

#### Доступность джоба логирования
```yaml
metric_name: olap_logging_job_availability
description: "Доступность джоба логирования OLAP"
measurement: "Процент времени работы джоба"
thresholds:
  warning: 95%
  critical: 90%
collection_interval: "1m"
```

#### Доступность OLAP системы
```yaml
metric_name: olap_system_availability
description: "Доступность OLAP системы"
measurement: "Процент успешных подключений"
thresholds:
  warning: 98%
  critical: 95%
collection_interval: "30s"
```

### 2. Метрики производительности

#### Время выполнения джоба
```yaml
metric_name: olap_logging_job_duration
description: "Время выполнения джоба логирования"
measurement: "Среднее время выполнения в секундах"
thresholds:
  warning: 300s
  critical: 600s
collection_interval: "5m"
```

#### Количество обработанных запросов
```yaml
metric_name: olap_queries_processed
description: "Количество обработанных запросов за период"
measurement: "Количество запросов в минуту"
thresholds:
  warning: 1000
  critical: 500
collection_interval: "1m"
```

### 3. Метрики качества данных

#### Задержка логирования
```yaml
metric_name: olap_logging_latency
description: "Задержка между запросом и записью в лог"
measurement: "Средняя задержка в секундах"
thresholds:
  warning: 60s
  critical: 300s
collection_interval: "1m"
```

#### Процент успешных записей
```yaml
metric_name: olap_logging_success_rate
description: "Процент успешно записанных логов"
measurement: "Процент успешных записей"
thresholds:
  warning: 95%
  critical: 90%
collection_interval: "5m"
```

## Настройка мониторинга

### 1. Prometheus конфигурация

#### prometheus.yml
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "olap_logging_rules.yml"

scrape_configs:
  - job_name: 'olap-logging-job'
    static_configs:
      - targets: ['olap-server:9100']
    scrape_interval: 30s
    metrics_path: /metrics

  - job_name: 'olap-database'
    static_configs:
      - targets: ['db-server:9100']
    scrape_interval: 30s

  - job_name: 'olap-system'
    static_configs:
      - targets: ['olap-server:8080']
    scrape_interval: 15s
```

#### olap_logging_rules.yml
```yaml
groups:
  - name: olap_logging
    rules:
      - alert: OLAPLoggingJobDown
        expr: up{job="olap-logging-job"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "OLAP logging job is down"
          description: "OLAP logging job has been down for more than 2 minutes"

      - alert: OLAPLoggingJobHighDuration
        expr: olap_logging_job_duration > 300
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "OLAP logging job duration is high"
          description: "OLAP logging job duration is {{ $value }}s, which is above the warning threshold"

      - alert: OLAPLoggingLowSuccessRate
        expr: olap_logging_success_rate < 95
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "OLAP logging success rate is low"
          description: "OLAP logging success rate is {{ $value }}%, which is below the warning threshold"
```

### 2. Grafana дашборд

#### Конфигурация дашборда
```json
{
  "dashboard": {
    "title": "OLAP Logging Monitoring",
    "panels": [
      {
        "title": "Job Availability",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"olap-logging-job\"}",
            "legendFormat": "Job Status"
          }
        ],
        "thresholds": [
          {
            "value": 0,
            "color": "red"
          },
          {
            "value": 1,
            "color": "green"
          }
        ]
      },
      {
        "title": "Job Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "olap_logging_job_duration",
            "legendFormat": "Duration (s)"
          }
        ],
        "yAxes": [
          {
            "label": "Duration (seconds)",
            "min": 0
          }
        ]
      },
      {
        "title": "Queries Processed",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(olap_queries_processed[5m])",
            "legendFormat": "Queries/min"
          }
        ]
      },
      {
        "title": "Success Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "olap_logging_success_rate",
            "legendFormat": "Success Rate %"
          }
        ],
        "yAxes": [
          {
            "label": "Success Rate (%)",
            "min": 0,
            "max": 100
          }
        ]
      }
    ]
  }
}
```

### 3. Настройка алертов

#### Alertmanager конфигурация
```yaml
global:
  smtp_smarthost: 'smtp.company.com:587'
  smtp_from: 'alerts@company.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://webhook.company.com/alerts'

  - name: 'critical-alerts'
    email_configs:
      - to: 'admin@company.com'
        subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/...'
        channel: '#alerts-critical'

  - name: 'warning-alerts'
    email_configs:
      - to: 'support@company.com'
        subject: 'WARNING: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}
```

## Скрипты мониторинга

### 1. Скрипт проверки статуса джоба

#### check_logging_job.sh
```bash
#!/bin/bash
# Скрипт проверки статуса джоба логирования OLAP

JOB_NAME="olap_logging_job"
LOG_FILE="/var/log/olap/health_check.log"
ALERT_EMAIL="admin@company.com"

# Функция логирования
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# Проверка статуса джоба
check_job_status() {
    if pgrep -f "$JOB_NAME" > /dev/null; then
        log_message "INFO: Job $JOB_NAME is running"
        return 0
    else
        log_message "ERROR: Job $JOB_NAME is not running"
        return 1
    fi
}

# Проверка последних записей в логе
check_recent_logs() {
    local log_count=$(sqlcmd -S olap-server.company.com -U username -P password -Q "SELECT COUNT(*) FROM olap_query_logs WHERE created_date >= DATEADD(minute, -10, GETDATE())" -h -1)
    
    if [ "$log_count" -gt 0 ]; then
        log_message "INFO: Recent logs found: $log_count records"
        return 0
    else
        log_message "WARNING: No recent logs found in the last 10 minutes"
        return 1
    fi
}

# Отправка алерта
send_alert() {
    local message="$1"
    echo "$message" | mail -s "OLAP Logging Alert" $ALERT_EMAIL
    log_message "ALERT: $message"
}

# Основная логика
main() {
    log_message "Starting health check for $JOB_NAME"
    
    if ! check_job_status; then
        send_alert "OLAP logging job is not running"
        exit 1
    fi
    
    if ! check_recent_logs; then
        send_alert "No recent logs found in OLAP system"
        exit 1
    fi
    
    log_message "Health check completed successfully"
    exit 0
}

# Запуск скрипта
main "$@"
```

### 2. Скрипт сбора метрик

#### collect_metrics.sh
```bash
#!/bin/bash
# Скрипт сбора метрик для мониторинга OLAP

METRICS_FILE="/var/log/olap/metrics.prom"
TEMP_FILE="/tmp/olap_metrics.tmp"

# Функция записи метрики
write_metric() {
    local name="$1"
    local value="$2"
    local labels="$3"
    echo "$name{$labels} $value" >> $TEMP_FILE
}

# Сбор метрик джоба
collect_job_metrics() {
    local job_pid=$(pgrep -f "olap_logging_job")
    
    if [ -n "$job_pid" ]; then
        write_metric "olap_logging_job_up" "1" ""
        
        # Время работы джоба
        local uptime=$(ps -o etime= -p $job_pid | tr -d ' ')
        write_metric "olap_logging_job_uptime_seconds" "$(date -d "$uptime" +%s 2>/dev/null || echo 0)" ""
        
        # Использование памяти
        local memory=$(ps -o rss= -p $job_pid | tr -d ' ')
        write_metric "olap_logging_job_memory_bytes" "$((memory * 1024))" ""
        
        # Использование CPU
        local cpu=$(ps -o %cpu= -p $job_pid | tr -d ' ')
        write_metric "olap_logging_job_cpu_percent" "$cpu" ""
    else
        write_metric "olap_logging_job_up" "0" ""
    fi
}

# Сбор метрик базы данных
collect_database_metrics() {
    local query="
    SELECT 
        COUNT(*) as total_logs,
        COUNT(CASE WHEN created_date >= DATEADD(minute, -5, GETDATE()) THEN 1 END) as recent_logs,
        AVG(execution_time) as avg_execution_time
    FROM olap_query_logs
    WHERE created_date >= DATEADD(hour, -1, GETDATE())
    "
    
    local result=$(sqlcmd -S olap-server.company.com -U username -P password -Q "$query" -h -1)
    local total_logs=$(echo "$result" | cut -d' ' -f1)
    local recent_logs=$(echo "$result" | cut -d' ' -f2)
    local avg_execution_time=$(echo "$result" | cut -d' ' -f3)
    
    write_metric "olap_query_logs_total" "$total_logs" ""
    write_metric "olap_query_logs_recent" "$recent_logs" ""
    write_metric "olap_query_avg_execution_time_seconds" "$avg_execution_time" ""
}

# Сбор метрик системы
collect_system_metrics() {
    # Использование диска
    local disk_usage=$(df /var/log/olap | tail -1 | awk '{print $5}' | sed 's/%//')
    write_metric "olap_logging_disk_usage_percent" "$disk_usage" ""
    
    # Размер логов
    local log_size=$(du -s /var/log/olap | cut -f1)
    write_metric "olap_logging_directory_size_bytes" "$((log_size * 1024))" ""
}

# Основная функция
main() {
    # Очистка временного файла
    > $TEMP_FILE
    
    # Сбор всех метрик
    collect_job_metrics
    collect_database_metrics
    collect_system_metrics
    
    # Перемещение в финальный файл
    mv $TEMP_FILE $METRICS_FILE
    
    echo "Metrics collected at $(date)"
}

# Запуск
main "$@"
```

### 3. Настройка cron для автоматического мониторинга

#### crontab
```bash
# Проверка статуса каждые 2 минуты
*/2 * * * * /opt/olap/scripts/check_logging_job.sh

# Сбор метрик каждые 30 секунд
* * * * * /opt/olap/scripts/collect_metrics.sh
* * * * * sleep 30; /opt/olap/scripts/collect_metrics.sh

# Очистка старых логов каждый день в 2:00
0 2 * * * /opt/olap/scripts/cleanup_logs.sh

# Еженедельный отчет каждый понедельник в 9:00
0 9 * * 1 /opt/olap/scripts/weekly_report.sh
```

## Интеграция с системами уведомлений

### 1. Slack интеграция

#### slack_notifier.py
```python
#!/usr/bin/env python3
import requests
import json
import sys

def send_slack_alert(message, severity="warning"):
    webhook_url = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    
    color = "good" if severity == "info" else "warning" if severity == "warning" else "danger"
    
    payload = {
        "attachments": [
            {
                "color": color,
                "title": "OLAP Logging Alert",
                "text": message,
                "fields": [
                    {
                        "title": "Severity",
                        "value": severity.upper(),
                        "short": True
                    },
                    {
                        "title": "System",
                        "value": "OLAP Logging",
                        "short": True
                    }
                ],
                "footer": "OLAP Monitoring System",
                "ts": int(time.time())
            }
        ]
    }
    
    response = requests.post(webhook_url, json=payload)
    return response.status_code == 200

if __name__ == "__main__":
    message = sys.argv[1] if len(sys.argv) > 1 else "Test alert"
    severity = sys.argv[2] if len(sys.argv) > 2 else "warning"
    send_slack_alert(message, severity)
```

### 2. Email уведомления

#### email_notifier.sh
```bash
#!/bin/bash
# Скрипт отправки email уведомлений

ALERT_EMAIL="admin@company.com"
SMTP_SERVER="smtp.company.com"
SMTP_PORT="587"
SMTP_USER="alerts@company.com"
SMTP_PASS="password"

send_email() {
    local subject="$1"
    local body="$2"
    local recipient="$3"
    
    (
        echo "To: $recipient"
        echo "From: $SMTP_USER"
        echo "Subject: $subject"
        echo "Content-Type: text/html"
        echo ""
        echo "$body"
    ) | sendmail -S "$SMTP_SERVER:$SMTP_PORT" -au"$SMTP_USER" -ap"$SMTP_PASS" "$recipient"
}

# Использование
# send_email "OLAP Alert" "Job is down" "admin@company.com"
```

## Дашборды и отчеты

### 1. Основной дашборд

#### Компоненты дашборда
- **Статус системы**: Общее состояние всех компонентов
- **Метрики производительности**: Графики времени выполнения и пропускной способности
- **Качество данных**: Процент успешных записей и задержки
- **Использование ресурсов**: CPU, память, диск
- **Исторические данные**: Тренды за последние 24 часа, 7 дней, 30 дней

### 2. Алертный дашборд

#### Компоненты алертного дашборда
- **Активные алерты**: Текущие проблемы и их статус
- **История алертов**: Лог всех сработавших алертов
- **Время восстановления**: MTTR для различных типов проблем
- **Эскалация**: Статус эскалации критических проблем

### 3. Еженедельные отчеты

#### Содержание отчета
- **Общая статистика**: Количество запросов, время работы, доступность
- **Производительность**: Средние и пиковые значения метрик
- **Проблемы**: Список инцидентов и их решения
- **Рекомендации**: Предложения по улучшению системы

## Заключение

### Ключевые преимущества
- **Проактивность**: Обнаружение проблем до их влияния на пользователей
- **Автоматизация**: Минимизация ручного вмешательства
- **Видимость**: Полная картина состояния системы
- **Аналитика**: Данные для принятия решений

### Следующие шаги
1. **Внедрение**: Поэтапное развертывание мониторинга
2. **Тестирование**: Проверка всех компонентов
3. **Обучение**: Подготовка команды
4. **Оптимизация**: Постоянное улучшение на основе данных

---
*Документ создан: 27.09.2025*  
*Версия: 1.0*  
*Статус: Готово к внедрению*
