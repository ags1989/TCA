# 🚀 Руководство по развертыванию - TFS-Confluence Automation

## 📋 Предварительные требования

### Системные требования
- **Python 3.11+** (рекомендуется Python 3.11)
- **Docker** (опционально, для контейнеризованного развертывания)
- **Git** (для управления версиями)

### Требования к API
- **TFS/Azure DevOps** Personal Access Token
- **Confluence** API Token
- **OpenAI** API Key (опционально, отключен по умолчанию)

## 🔧 Быстрая настройка (Windows)

### 🚀 **Автоматическая установка**
```bash
# 1. Первоначальная настройка
setup.bat

# 2. Настройка конфигурации
copy env.example .env
notepad .env

# 3. Запуск приложения
start.bat
```

### 🔧 **Ручная настройка**

#### 1. Первоначальная настройка
```bash
# Перейдите в каталог проекта
cd tfs-confluence-install

# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения (Windows)
venv\Scripts\activate

# Активация виртуального окружения (Linux/macOS)
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

#### 2. Настройка конфигурации
Создайте файл `.env` на основе `env.example`:

```bash
# TFS/Azure DevOps
TFS_URL=https://your-organization.visualstudio.com
TFS_PAT=your_personal_access_token
TFS_PROJECT=your-project-name
TFS_ORGANIZATION=your-organization

# Confluence
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_USER=your-email@domain.com
CONFLUENCE_TOKEN=your_api_token

# OpenAI (опционально)
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

# Приложение
DEBUG=True
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

### 3. Проверка конфигурации
```bash
# Запустите приложение
python run.py
```

### 4. Проверка работы
Откройте браузер и перейдите по адресу:
- **Основное приложение**: http://localhost:8000
- **API документация**: http://localhost:8000/docs
- **Статус системы**: http://localhost:8000/status

### 5. Управление приложением

#### Windows (bat файлы)
- **Запуск**: `start.bat`
- **Остановка**: `stop.bat`
- **Перезапуск**: `restart.bat`
- **Статус**: `status.bat`
- **Очистка**: `clean.bat`

#### Ручное управление
```bash
# Остановите приложение (Ctrl+C в терминале)

# Деактивация виртуального окружения (когда закончите работу)
deactivate
```

## 🐳 Развертывание с Docker

### 1. Создание Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создание пользователя
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Открытие порта
EXPOSE 8000

# Запуск приложения
CMD ["python", "run.py"]
```

### 2. Создание docker-compose.yml
```yaml
version: '3.8'

services:
  tfs-confluence-automation:
    build: .
    ports:
      - "8000:8000"
    environment:
      - TFS_URL=${TFS_URL}
      - TFS_PAT=${TFS_PAT}
      - TFS_PROJECT=${TFS_PROJECT}
      - CONFLUENCE_URL=${CONFLUENCE_URL}
      - CONFLUENCE_USER=${CONFLUENCE_USER}
      - CONFLUENCE_TOKEN=${CONFLUENCE_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEBUG=${DEBUG:-False}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 3. Запуск с Docker Compose
```bash
# Сборка и запуск
docker-compose up --build -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

## 🌐 Продакшн развертывание

### 1. Настройка окружения
```bash
# Переменные окружения для продакшна
export DEBUG=False
export LOG_LEVEL=WARNING
export HOST=0.0.0.0
export PORT=8000
```

### 2. Обратный прокси (Nginx)
Создайте `nginx.conf`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Таймауты
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Статические файлы
    location /static/ {
        alias /app/frontend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 3. SSL сертификат (Let's Encrypt)
```bash
# Установка certbot
sudo apt install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com
```

### 4. Systemd сервис
Создайте `/etc/systemd/system/tfs-confluence-automation.service`:
```ini
[Unit]
Description=TFS-Confluence Automation
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/tfs-confluence-automation
Environment=PATH=/opt/tfs-confluence-automation/venv/bin
ExecStart=/opt/tfs-confluence-automation/venv/bin/python run.py
Restart=always
RestartSec=10

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=tfs-confluence-automation

[Install]
WantedBy=multi-user.target
```

Включите и запустите сервис:
```bash
sudo systemctl enable tfs-confluence-automation
sudo systemctl start tfs-confluence-automation
```

## 🔐 Конфигурация безопасности

### 1. Безопасность переменных окружения
- Никогда не коммитьте `.env` файлы в систему контроля версий
- Используйте файлы конфигурации для разных окружений
- Регулярно ротируйте API ключи
- Используйте токены с минимальными правами доступа

### 2. Сетевая безопасность
```bash
# Правила файрвола (UFW)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 3. Безопасность приложения
- Включите HTTPS в продакшне
- Используйте сильную аутентификацию для админских endpoints
- Реализуйте ограничение скорости запросов
- Регулярно обновляйте зависимости

## 📊 Мониторинг и логирование

### 1. Проверки здоровья
```bash
# Здоровье приложения
curl http://localhost:8000/health

# Статус системы
curl http://localhost:8000/status

# Docker здоровье
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### 2. Управление логами
```bash
# Просмотр логов приложения
docker-compose logs -f tfs-confluence-automation

# Системные логи
sudo journalctl -u tfs-confluence-automation -f

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 3. Настройка мониторинга
- **Prometheus** для сбора метрик
- **Grafana** для визуализации
- **ELK Stack** для анализа логов
- **Uptime monitoring** для проверки доступности

## 🔄 CI/CD Pipeline

### 1. GitHub Actions
Проект включает полный CI/CD pipeline:
- **Тестирование**: Автоматические тесты на каждом PR
- **Безопасность**: Сканирование уязвимостей
- **Сборка**: Создание Docker образов
- **Развертывание**: Автоматическое развертывание в продакшн

### 2. Ручное развертывание
```bash
# Получение последних изменений
git pull origin main

# Обновление зависимостей
pip install -r requirements.txt

# Перезапуск сервиса
sudo systemctl restart tfs-confluence-automation
```

## 🛠️ Устранение неполадок

### Частые проблемы

#### 1. Ошибки подключения к API
```bash
# Тест подключения к TFS
python -c "from app.services.tfs_service import TFSService; import asyncio; asyncio.run(TFSService().test_connection())"

# Тест подключения к Confluence
python -c "from app.services.confluence_service import ConfluenceService; import asyncio; asyncio.run(ConfluenceService().test_connection())"
```

#### 2. Проблемы с правами доступа
```bash
# Исправление прав на файлы
sudo chown -R appuser:appuser /opt/tfs-confluence-automation
sudo chmod -R 755 /opt/tfs-confluence-automation
```

#### 3. Конфликты портов
```bash
# Проверка использования порта
sudo netstat -tlnp | grep :8000

# Завершение процесса, использующего порт
sudo kill -9 $(sudo lsof -t -i:8000)
```

### Анализ логов
```bash
# Ошибки приложения
grep "ERROR" logs/app.log

# Проблемы производительности
grep "slow" logs/app.log

# Сбои API
grep "RequestException" logs/app.log
```

## 📈 Оптимизация производительности

### 1. Настройка приложения
```python
# В run.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # Количество воркеров
        log_level="info"
    )
```

### 2. Оптимизация базы данных
- Используйте пул соединений
- Реализуйте кэширование
- Оптимизируйте запросы

### 3. Ограничения ресурсов
```yaml
# docker-compose.yml
services:
  tfs-confluence-automation:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

## 🔄 Резервное копирование и восстановление

### 1. Резервное копирование конфигурации
```bash
# Резервное копирование конфигурации
tar -czf config-backup-$(date +%Y%m%d).tar.gz .env docker-compose.yml

# Резервное копирование логов
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```

### 2. Резервное копирование приложения
```bash
# Полное резервное копирование приложения
tar -czf app-backup-$(date +%Y%m%d).tar.gz \
  --exclude=venv \
  --exclude=__pycache__ \
  --exclude=.git \
  .
```

### 3. Процедура восстановления
```bash
# Восстановление из резервной копии
tar -xzf app-backup-YYYYMMDD.tar.gz
pip install -r requirements.txt
python run.py
```

## 📞 Поддержка

### Получение помощи
1. **Проверьте логи** на наличие сообщений об ошибках
2. **Запустите диагностику**: `curl http://localhost:8000/status`
3. **Изучите документацию**: FEATURES.md
4. **Проверьте GitHub issues** на наличие известных проблем
5. **Bat файлы**: BAT_FILES.md (Windows)
6. **Краткое описание bat файлов**: README_BAT.md

### Контактная информация
- **Технические проблемы**: Создайте GitHub issue
- **Помощь с конфигурацией**: Проверьте API документацию
- **Проблемы безопасности**: Обратитесь к системному администратору

---

## 🎯 Краткая справка

| Задача | Команда |
|--------|---------|
| **Автоматическая установка** | `setup.bat` |
| **Запуск приложения** | `start.bat` |
| **Остановка приложения** | `stop.bat` |
| **Перезапуск приложения** | `restart.bat` |
| **Проверка статуса** | `status.bat` |
| **Очистка системы** | `clean.bat` |
| Создание venv | `python -m venv venv` |
| Активация venv (Windows) | `venv\Scripts\activate` |
| Активация venv (Linux/macOS) | `source venv/bin/activate` |
| Установка | `pip install -r requirements.txt` |
| Запуск | `python run.py` |
| Остановка | `Ctrl+C` |
| Деактивация venv | `deactivate` |
| Docker | `docker-compose up -d` |
| Статус | `curl http://localhost:8000/status` |
| Логи | `docker-compose logs -f` |

**URL приложения:**
- Основное приложение: http://localhost:8000
- API документация: http://localhost:8000/docs
- Проверка здоровья: http://localhost:8000/health
- Статус системы: http://localhost:8000/status
