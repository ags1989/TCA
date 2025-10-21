# Руководство по развертыванию: Novabev. Переименование полей в Ч-Web

## Обзор развертывания

### Цель развертывания
Внедрить систему переименования полей в Чикаго Web для клиента Novabev, обеспечив возможность использования индивидуальных названий полей справочников.

### Требования к развертыванию
- **Версия системы**: Чикаго Web 3.6.208.9 или выше
- **Окружение**: Тестовое и продуктивное
- **Время развертывания**: 2-4 часа
- **Откат**: Возможен в течение 1 часа

## Предварительные требования

### 1. Системные требования
- **Node.js**: версия 16.x или выше
- **Angular**: версия 13.x или выше
- **TypeScript**: версия 4.x или выше
- **Webpack**: версия 5.x или выше

### 2. Инфраструктурные требования
- **Веб-сервер**: Nginx 1.18+ или Apache 2.4+
- **CDN**: Настроенный для статических файлов
- **Мониторинг**: Логирование и метрики
- **Резервное копирование**: Настроенное для файлов переводов

### 3. Доступы и права
- **Администратор системы**: Полные права на развертывание
- **Администратор веб-сервера**: Права на изменение конфигурации
- **Администратор CDN**: Права на загрузку файлов
- **Клиент**: Доступ к тестовому окружению для проверки

## Подготовка к развертыванию

### 1. Подготовка файлов переводов

#### Создание структуры папок
```bash
# Создание структуры для тенанта Novabev
mkdir -p assets/locale/tenants/novabev
mkdir -p assets/locale/tenants/novabev/backup
```

#### Создание файла ru-RU.json
```json
{
  "outlets": {
    "code": "Код SY",
    "name": "Наименование ТТ",
    "address": "Адрес размещения",
    "phone": "Телефон",
    "email": "Email"
  },
  "goods": {
    "name": "Название товара",
    "article": "Артикул",
    "price": "Цена продажи",
    "category": "Категория"
  },
  "counteragents": {
    "inn": "ИНН/КПП",
    "name": "Наименование организации",
    "contactPerson": "Контактное лицо",
    "phone": "Телефон"
  }
}
```

#### Создание файла en-US.json
```json
{
  "outlets": {
    "code": "Code SY",
    "name": "Outlet Name",
    "address": "Location Address",
    "phone": "Phone",
    "email": "Email"
  },
  "goods": {
    "name": "Product Name",
    "article": "Article",
    "price": "Sale Price",
    "category": "Category"
  },
  "counteragents": {
    "inn": "Tax ID",
    "name": "Organization Name",
    "contactPerson": "Contact Person",
    "phone": "Phone"
  }
}
```

### 2. Подготовка конфигурации

#### Конфигурационный файл для тенанта
```json
{
  "tenant": "novabev",
  "brand": "Novabev",
  "locale": "ru-RU",
  "fallbackLocale": "en-US",
  "cacheEnabled": true,
  "cacheTimeout": 300000,
  "debugMode": false
}
```

#### Обновление конфигурации системы
```typescript
// config/localization.config.ts
export const LOCALIZATION_CONFIG = {
  defaultLocale: 'ru-RU',
  supportedLocales: ['ru-RU', 'en-US'],
  tenantPath: 'assets/locale/tenants',
  fallbackEnabled: true,
  cacheEnabled: true,
  cacheTimeout: 300000,
  debugMode: false
};
```

### 3. Подготовка кода

#### Обновление модуля локализации
```typescript
// src/app/core/localization/localization.module.ts
import { NgModule } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { FieldLocalizationService } from './services/field-localization.service';
import { TenantResolver } from './services/tenant-resolver.service';
import { TranslationLoaderService } from './services/translation-loader.service';

@NgModule({
  imports: [HttpClientModule],
  providers: [
    FieldLocalizationService,
    TenantResolver,
    TranslationLoaderService
  ]
})
export class LocalizationModule { }
```

#### Обновление компонентов
```typescript
// src/app/shared/components/grid/grid.component.ts
import { Component, Input } from '@angular/core';
import { FieldLocalizationService } from '../../services/field-localization.service';

@Component({
  selector: 'app-grid',
  template: `
    <table>
      <thead>
        <tr>
          <th *ngFor="let column of columns">
            {{ getLocalizedHeader(column) }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr *ngFor="let row of data">
          <td *ngFor="let column of columns">
            {{ row[column.field] }}
          </td>
        </tr>
      </tbody>
    </table>
  `
})
export class GridComponent {
  @Input() columns: GridColumn[] = [];
  @Input() data: any[] = [];

  constructor(
    private fieldLocalization: FieldLocalizationService
  ) {}

  getLocalizedHeader(column: GridColumn): string {
    return this.fieldLocalization.getFieldName(
      column.entityName, 
      column.fieldName
    );
  }
}
```

## Процесс развертывания

### Этап 1: Подготовка окружения

#### 1.1 Создание резервной копии
```bash
# Создание резервной копии текущей версии
cp -r /var/www/chicago-web /var/www/chicago-web-backup-$(date +%Y%m%d-%H%M%S)

# Создание резервной копии конфигурации
cp -r /etc/nginx/sites-available/chicago-web /etc/nginx/sites-available/chicago-web-backup-$(date +%Y%m%d-%H%M%S)
```

#### 1.2 Проверка системы
```bash
# Проверка доступности сервисов
systemctl status nginx
systemctl status chicago-web

# Проверка места на диске
df -h

# Проверка логов
tail -f /var/log/nginx/error.log
tail -f /var/log/chicago-web/app.log
```

### Этап 2: Развертывание кода

#### 2.1 Остановка сервисов
```bash
# Остановка приложения
systemctl stop chicago-web

# Перезагрузка Nginx (если необходимо)
systemctl reload nginx
```

#### 2.2 Развертывание нового кода
```bash
# Переход в директорию приложения
cd /var/www/chicago-web

# Получение последней версии
git pull origin main

# Установка зависимостей
npm install

# Сборка приложения
npm run build:production
```

#### 2.3 Копирование файлов переводов
```bash
# Создание директории для файлов переводов
mkdir -p dist/assets/locale/tenants/novabev

# Копирование файлов переводов
cp assets/locale/tenants/novabev/ru-RU.json dist/assets/locale/tenants/novabev/
cp assets/locale/tenants/novabev/en-US.json dist/assets/locale/tenants/novabev/
cp assets/locale/tenants/novabev/tenant-config.json dist/assets/locale/tenants/novabev/

# Установка прав доступа
chmod 644 dist/assets/locale/tenants/novabev/*.json
chown www-data:www-data dist/assets/locale/tenants/novabev/*.json
```

### Этап 3: Обновление конфигурации

#### 3.1 Обновление конфигурации Nginx
```nginx
# /etc/nginx/sites-available/chicago-web
server {
    listen 80;
    server_name chicago-web.example.com;
    root /var/www/chicago-web/dist;
    index index.html;

    # Кэширование статических файлов
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Обработка файлов переводов
    location /assets/locale/tenants/ {
        expires 1h;
        add_header Cache-Control "public";
        add_header Access-Control-Allow-Origin "*";
    }

    # Основное приложение
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Логирование
    access_log /var/log/nginx/chicago-web-access.log;
    error_log /var/log/nginx/chicago-web-error.log;
}
```

#### 3.2 Обновление конфигурации приложения
```typescript
// src/environments/environment.prod.ts
export const environment = {
  production: true,
  apiUrl: 'https://api.chicago-web.example.com',
  localization: {
    defaultLocale: 'ru-RU',
    supportedLocales: ['ru-RU', 'en-US'],
    tenantPath: 'assets/locale/tenants',
    fallbackEnabled: true,
    cacheEnabled: true,
    cacheTimeout: 300000
  }
};
```

### Этап 4: Запуск и проверка

#### 4.1 Запуск сервисов
```bash
# Запуск приложения
systemctl start chicago-web

# Проверка статуса
systemctl status chicago-web

# Перезагрузка Nginx
systemctl reload nginx
```

#### 4.2 Проверка развертывания
```bash
# Проверка доступности приложения
curl -I http://chicago-web.example.com

# Проверка файлов переводов
curl -I http://chicago-web.example.com/assets/locale/tenants/novabev/ru-RU.json

# Проверка логов
tail -f /var/log/chicago-web/app.log
```

## Тестирование развертывания

### 1. Автоматизированные проверки

#### Скрипт проверки развертывания
```bash
#!/bin/bash
# check-deployment.sh

echo "Проверка развертывания системы переименования полей..."

# Проверка доступности приложения
if curl -s -o /dev/null -w "%{http_code}" http://chicago-web.example.com | grep -q "200"; then
    echo "✅ Приложение доступно"
else
    echo "❌ Приложение недоступно"
    exit 1
fi

# Проверка файлов переводов
if curl -s -o /dev/null -w "%{http_code}" http://chicago-web.example.com/assets/locale/tenants/novabev/ru-RU.json | grep -q "200"; then
    echo "✅ Файл ru-RU.json доступен"
else
    echo "❌ Файл ru-RU.json недоступен"
    exit 1
fi

# Проверка JSON валидности
if curl -s http://chicago-web.example.com/assets/locale/tenants/novabev/ru-RU.json | jq . > /dev/null 2>&1; then
    echo "✅ JSON файл валиден"
else
    echo "❌ JSON файл невалиден"
    exit 1
fi

echo "✅ Все проверки пройдены успешно"
```

#### Запуск проверок
```bash
chmod +x check-deployment.sh
./check-deployment.sh
```

### 2. Ручное тестирование

#### Проверка переименования полей
1. **Открыть приложение**: http://chicago-web.example.com
2. **Авторизоваться**: Под тенантом Novabev
3. **Открыть справочник ТТ**: Проверить заголовок "Код SY"
4. **Открыть карточку ТТ**: Проверить метку поля "Код SY"
5. **Проверить другие справочники**: Товары, Контрагенты

#### Проверка мультитенантности
1. **Переключиться на Default**: Проверить стандартные названия
2. **Вернуться на Novabev**: Проверить переименованные поля
3. **Проверить изоляцию**: Настройки не должны влиять друг на друга

### 3. Нагрузочное тестирование

#### Скрипт нагрузочного тестирования
```bash
#!/bin/bash
# load-test.sh

echo "Нагрузочное тестирование..."

# Тестирование загрузки переводов
for i in {1..100}; do
    curl -s http://chicago-web.example.com/assets/locale/tenants/novabev/ru-RU.json > /dev/null
    if [ $((i % 10)) -eq 0 ]; then
        echo "Выполнено $i запросов"
    fi
done

echo "Нагрузочное тестирование завершено"
```

## Мониторинг после развертывания

### 1. Настройка мониторинга

#### Конфигурация Prometheus
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'chicago-web'
    static_configs:
      - targets: ['chicago-web.example.com:80']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

#### Конфигурация Grafana
```json
{
  "dashboard": {
    "title": "Chicago Web - Field Localization",
    "panels": [
      {
        "title": "Translation Load Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, translation_load_duration_seconds)"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(translation_cache_hits_total) / rate(translation_cache_requests_total)"
          }
        ]
      }
    ]
  }
}
```

### 2. Алерты

#### Конфигурация алертов
```yaml
# alerts.yml
groups:
  - name: chicago-web-localization
    rules:
      - alert: TranslationLoadError
        expr: rate(translation_load_errors_total[5m]) > 0.1
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "High translation load error rate"
          description: "Translation load error rate is {{ $value }} errors per second"

      - alert: TranslationCacheMiss
        expr: rate(translation_cache_misses_total[5m]) > 0.5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High translation cache miss rate"
          description: "Translation cache miss rate is {{ $value }} misses per second"
```

### 3. Логирование

#### Конфигурация логов
```typescript
// src/app/core/logging/logger.config.ts
export const LOGGER_CONFIG = {
  level: 'info',
  format: 'json',
  transports: [
    {
      type: 'file',
      filename: '/var/log/chicago-web/app.log',
      maxsize: 10485760, // 10MB
      maxFiles: 5
    },
    {
      type: 'console'
    }
  ]
};
```

## Откат развертывания

### 1. Процедура отката

#### Автоматический откат
```bash
#!/bin/bash
# rollback.sh

echo "Выполнение отката развертывания..."

# Остановка приложения
systemctl stop chicago-web

# Восстановление из резервной копии
cp -r /var/www/chicago-web-backup-* /var/www/chicago-web

# Восстановление конфигурации Nginx
cp /etc/nginx/sites-available/chicago-web-backup-* /etc/nginx/sites-available/chicago-web

# Перезагрузка Nginx
systemctl reload nginx

# Запуск приложения
systemctl start chicago-web

echo "Откат завершен"
```

#### Ручной откат
1. **Остановить приложение**: `systemctl stop chicago-web`
2. **Восстановить код**: Из резервной копии
3. **Восстановить конфигурацию**: Nginx и приложения
4. **Запустить сервисы**: `systemctl start chicago-web`
5. **Проверить работу**: Тестирование основных функций

### 2. Проверка отката

#### Скрипт проверки отката
```bash
#!/bin/bash
# check-rollback.sh

echo "Проверка отката..."

# Проверка доступности приложения
if curl -s -o /dev/null -w "%{http_code}" http://chicago-web.example.com | grep -q "200"; then
    echo "✅ Приложение доступно после отката"
else
    echo "❌ Приложение недоступно после отката"
    exit 1
fi

# Проверка отсутствия файлов переводов
if curl -s -o /dev/null -w "%{http_code}" http://chicago-web.example.com/assets/locale/tenants/novabev/ru-RU.json | grep -q "404"; then
    echo "✅ Файлы переводов удалены"
else
    echo "❌ Файлы переводов все еще доступны"
    exit 1
fi

echo "✅ Откат выполнен успешно"
```

## Поддержка после развертывания

### 1. Документация для поддержки

#### Руководство по устранению неполадок
```markdown
# Устранение неполадок системы переименования полей

## Проблема: Поля не переименовываются
**Причина**: Файлы переводов не загружены
**Решение**: 
1. Проверить доступность файлов переводов
2. Проверить права доступа к файлам
3. Перезагрузить приложение

## Проблема: Ошибка загрузки переводов
**Причина**: Невалидный JSON файл
**Решение**:
1. Проверить синтаксис JSON файла
2. Восстановить из резервной копии
3. Проверить кодировку файла

## Проблема: Медленная загрузка страниц
**Причина**: Проблемы с кэшированием
**Решение**:
1. Очистить кэш браузера
2. Проверить настройки кэширования Nginx
3. Перезагрузить приложение
```

### 2. Контакты поддержки

#### Эскалация проблем
- **Уровень 1**: Техническая поддержка (8:00-18:00)
- **Уровень 2**: Разработчики (24/7)
- **Уровень 3**: Архитектор системы (критические проблемы)

#### Каналы связи
- **Email**: support@chicago-web.example.com
- **Телефон**: +7 (XXX) XXX-XX-XX
- **Slack**: #chicago-web-support
- **Jira**: Проект CHICAGO-WEB

## Заключение

### Ключевые моменты развертывания
1. **Подготовка**: Тщательная подготовка файлов и конфигурации
2. **Тестирование**: Обязательное тестирование на всех этапах
3. **Мониторинг**: Непрерывный мониторинг после развертывания
4. **Поддержка**: Готовность к быстрому реагированию на проблемы

### Рекомендации
- **Резервное копирование**: Обязательно перед каждым развертыванием
- **Поэтапное развертывание**: Сначала тестовое, затем продуктивное
- **Документирование**: Ведение логов всех изменений
- **Обучение**: Подготовка команды поддержки

---
*Документ создан: 27.09.2025*  
*Версия: 1.0*  
*Статус: Готов к использованию*
