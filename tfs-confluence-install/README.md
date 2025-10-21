# 🤖 TFS-Confluence Automation

Комплексная система автоматизации для интеграции TFS/Azure DevOps, Confluence и AI для автоматического создания и управления рабочими элементами.

## 🚀 Быстрый старт

### 🚀 **Автоматическая установка (Windows)**

#### Требования
- **Python 3.11+** (обязательно!)
- Windows 10/11
- Интернет-соединение

#### Если Python не установлен:
```bash
# Запустите установщик Python
install_python.bat
```

#### Установка приложения:
```bash
# 1. Первоначальная настройка
setup.bat

# 2. Настройка конфигурации
copy env.example .env
# Отредактируйте .env файл любым текстовым редактором
# (Блокнот, Notepad++, VS Code и т.д.)

# 3. Запуск приложения
start.bat              # Продакшен режим (рекомендуется)
start_dev.bat          # Режим разработки (с reload)
start_clean.bat        # Чистые логи (без reload)
```

## 🐍 Установка Python (если не установлен)

### Способ 1: Официальный сайт (рекомендуется)
1. Перейдите на https://www.python.org/downloads/
2. Скачайте **Python 3.11** или новее
3. Запустите установщик
4. **ВАЖНО**: Отметьте галочку "Add Python to PATH"
5. Нажмите "Install Now"
6. Дождитесь завершения установки

### Способ 2: Microsoft Store (простой)
1. Откройте Microsoft Store
2. Найдите "Python 3.11" или "Python 3.12"
3. Нажмите "Установить"
4. Дождитесь завершения установки

### Способ 3: Через winget (если доступен)
```bash
winget install Python.Python.3.11
```

### Способ 4: Через Chocolatey (если установлен)
```bash
choco install python --version=3.11.0
```

### Проверка установки
```bash
python --version
```
Должно показать версию Python 3.11 или новее.

## ⚙️ Настройка конфигурации

### 1. Создание файла .env
```bash
# Скопируйте шаблон конфигурации
copy env.example .env
```

### 2. Настройка API ключей
Откройте файл `.env` любым текстовым редактором и заполните:

```env
# TFS/Azure DevOps настройки
TFS_URL=https://dev.azure.com/yourorganization
TFS_PAT=your_personal_access_token
TFS_PROJECT=your_project_name

# Confluence настройки
CONFLUENCE_URL=https://yourcompany.atlassian.net/wiki
CONFLUENCE_TOKEN=your_confluence_token
CONFLUENCE_USER=your_email@company.com

# OpenAI настройки (опционально)
OPENAI_API_KEY=your_openai_api_key
```

### 3. Получение API ключей

#### TFS Personal Access Token (PAT):
1. Перейдите в Azure DevOps → User Settings → Personal Access Tokens
2. Создайте новый токен с правами: Work Items (Read & Write), Code (Read)
3. Скопируйте токен в `TFS_PAT`

#### Confluence API Token:
1. Перейдите в Atlassian Account Settings → Security → API tokens
2. Создайте новый токен
3. Скопируйте токен в `CONFLUENCE_TOKEN`

### 4. Проверка настроек
```bash
# Запустите проверку статуса
status.bat
```

### 🔧 **Ручная установка**

#### 1. Установка
```bash
# Клонируйте репозиторий или скачайте архив
cd tfs-confluence-install

# Установите зависимости
pip install -r requirements.txt
```

#### 2. Настройка окружения
```bash
# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения (Windows)
venv\Scripts\activate

# Активация виртуального окружения (Linux/macOS)
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

#### 3. Настройка конфигурации
```bash
# Скопируйте шаблон конфигурации
copy env.example .env

# Отредактируйте .env с вашими API ключами
notepad .env
```

#### 4. Запуск
```bash
# Запустите приложение
python run.py
```

### 🌐 **Использование**
Откройте браузер и перейдите по адресу: http://localhost:8000

### 🛑 **Управление приложением**

#### Windows (bat файлы)
- **Установка Python**: `install_python.bat` - если Python не установлен
- **Первоначальная настройка**: `setup.bat` - создание окружения и установка зависимостей
- **Запуск (продакшен)**: `start.bat` - стабильный режим без reload
- **Запуск (разработка)**: `start_dev.bat` - с автоматической перезагрузкой
- **Запуск (чистые логи)**: `start_clean.bat` - без reload, чистые логи
- **Остановка**: `stop.bat`
- **Перезапуск**: `restart.bat`
- **Статус**: `status.bat` - проверка всех компонентов
- **Очистка**: `clean.bat` - удаление виртуального окружения

#### Режимы запуска
- **start.bat** - Продакшен режим (рекомендуется для использования)
- **start_dev.bat** - Режим разработки с автоматической перезагрузкой при изменении файлов
- **start_clean.bat** - Режим без reload для максимально чистых логов

#### 📋 Подробное описание BAT файлов
См. [README_BAT.md](README_BAT.md) для детального описания всех bat файлов и их функций.

#### Ручное управление
```bash
# Остановите приложение (Ctrl+C в терминале)

# Деактивация виртуального окружения (когда закончите работу)
deactivate
```

## ✨ Основные возможности

### 🤖 Создание User Stories из Confluence
- Автоматическое создание User Stories в TFS на основе статей Confluence
- Извлечение критериев приемки из таблиц Given/When/Then
- Связывание с родительскими Work Items
- Предварительный просмотр перед созданием

### 🔗 Создание цепочек изменений
- Создание связанных Epic → Feature → Backlog Item
- Анализ естественного языка для извлечения параметров
- Автоматическое определение проекта из родительского элемента

### 📋 Генерация чек-листов БДК ЗЗЛ
- Автоматическая генерация чек-листов для проверки готовности к внедрению
- Поиск связанных тест-планов, интеграционных тестов и багов
- Оптимизированная производительность с кэшированием


## 🎨 Пользовательский интерфейс

### Чат-интерфейс
- Интерактивный чат для обработки запросов
- Отображение результатов в реальном времени
- Подтверждение действий пользователем

### Быстрые действия
- **Создать цепочку тикетов**: Быстрый доступ к созданию цепочек изменений
- **Чек-лист БД**: Генерация чек-листов БДК ЗЗЛ
- **Создай UserStory в TFS по статье TDD**: Создание User Stories из Confluence

### Мониторинг
- Статус подключения к TFS/Azure DevOps
- Статус подключения к Confluence
- Статус AI-сервиса (опционально)

## 🔧 API Endpoints

### Основные
- `POST /process-request` - Обработка пользовательских запросов
- `GET /status` - Статус системы
- `GET /health` - Проверка здоровья приложения


### Advanced
- `POST /api/v1/change-chain-chat` - Создание цепочек изменений
- `POST /api/v1/checklist-chat` - Генерация чек-листов

## 📋 Требования

### Системные
- Python 3.11+
- 2GB RAM (минимум)
- 1GB свободного места на диске
- Виртуальное окружение (рекомендуется)

### API ключи
- **TFS/Azure DevOps**: Personal Access Token
- **Confluence**: API Token
- **OpenAI**: API Key (опционально)

## 🛠️ Установка и настройка

### 1. Создание виртуального окружения
```bash
# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения (Windows)
venv\Scripts\activate

# Активация виртуального окружения (Linux/macOS)
source venv/bin/activate
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка конфигурации
Создайте файл `.env` на основе `env.example`:

```bash
# TFS/Azure DevOps
TFS_URL=https://your-organization.visualstudio.com
TFS_PAT=your_personal_access_token
TFS_PROJECT=your-project-name

# Confluence
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_USER=your-email@domain.com
CONFLUENCE_TOKEN=your_api_token

# OpenAI (опционально)
OPENAI_API_KEY=your_openai_api_key
```

### 4. Запуск приложения
```bash
python run.py
```

### 5. Проверка работы
- Откройте http://localhost:8000
- Проверьте статус сервисов
- Попробуйте создать User Story из Confluence

### 6. Остановка приложения
```bash
# Остановите приложение (Ctrl+C в терминале)

# Деактивация виртуального окружения (когда закончите работу)
deactivate
```

## 🐳 Docker развертывание

### 1. Создание образа
```bash
docker build -t tfs-confluence-automation .
```

### 2. Запуск контейнера
```bash
docker run -d \
  --name tfs-confluence-automation \
  -p 8000:8000 \
  --env-file .env \
  tfs-confluence-automation
```

### 3. Docker Compose
```bash
docker-compose up -d
```

## 📊 Мониторинг

### Статус системы
```bash
curl http://localhost:8000/status
```

### Проверка здоровья
```bash
curl http://localhost:8000/health
```

### Логи
```bash
# Docker
docker logs tfs-confluence-automation

# Локально (с активированным виртуальным окружением)
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS
tail -f logs/app.log
deactivate
```

## 🆘 Устранение неполадок

### Частые проблемы

#### 1. Ошибки подключения
- Проверьте API ключи в `.env`
- Убедитесь, что URL сервисов корректны
- Проверьте права доступа токенов

#### 2. Ошибки создания User Stories
- Проверьте доступность статьи Confluence
- Убедитесь, что в статье есть таблицы с критериями приемки
- Проверьте права на создание Work Items в TFS

#### 3. Ошибки создания цепочек изменений
- Убедитесь, что родительский Work Item существует
- Проверьте права на создание Epic, Feature, Backlog Item
- Проверьте корректность названия запроса

### Получение помощи
- 📖 **Документация**: QUICK_START.md, DEPLOYMENT.md, FEATURES.md
- 🧪 **Тестирование**: `venv\Scripts\activate && python -m pytest tests/ && deactivate`
- 📊 **Мониторинг**: http://localhost:8000/status
- 🐛 **Логи**: Проверьте файлы в папке `logs/`

## 🔧 Разработка

### Структура проекта
```
tfs-confluence-install/
├── app/                    # Основной код приложения
│   ├── api/               # API endpoints
│   ├── services/          # Бизнес-логика
│   ├── models/            # Модели данных
│   └── config/            # Конфигурация
├── frontend/              # Веб-интерфейс
│   └── static/            # Статические файлы
├── tests/                 # Тесты
├── logs/                  # Логи
├── requirements.txt       # Зависимости
├── run.py                 # Точка входа
└── README.md              # Документация
```

### Запуск тестов
```bash
# Активация виртуального окружения
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# Все тесты
python -m pytest tests/

# Только unit тесты
python -m pytest tests/unit/

# Только integration тесты
python -m pytest tests/integration/

# Деактивация виртуального окружения
deactivate
```

### Разработка
```bash
# Активация виртуального окружения
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# Установка в режиме разработки
pip install -e .

# Запуск с отладкой
DEBUG=True python run.py

# Деактивация виртуального окружения
deactivate
```

## 📈 Производительность

### Рекомендации
- Используйте SSD для логов
- Настройте кэширование для часто используемых данных
- Мониторьте использование памяти
- Регулярно очищайте старые логи

### Оптимизация
- Асинхронная обработка запросов
- Кэширование результатов API
- Пакетные операции для TFS
- Оптимизированные запросы к Confluence

## 🔐 Безопасность

### Рекомендации
- Никогда не коммитьте `.env` файлы
- Используйте токены с минимальными правами
- Регулярно ротируйте API ключи
- Включите HTTPS в продакшне
- Мониторьте логи на подозрительную активность

## 📞 Поддержка

### Документация
- **QUICK_START.md**: Быстрый старт (включая виртуальное окружение)
- **DEPLOYMENT.md**: Развертывание (включая виртуальное окружение)
- **FEATURES.md**: Детальное описание возможностей
- **BAT_FILES.md**: Управление через bat файлы (Windows)
- **README_BAT.md**: Краткое описание bat файлов

### Контакты
- **Технические проблемы**: Создайте GitHub issue
- **Помощь с конфигурацией**: Проверьте API документацию
- **Проблемы безопасности**: Обратитесь к системному администратору

---

## 🎉 Готово к использованию!

Ваша система TFS-Confluence Automation готова к:
- 📝 **Созданию User Stories** в TFS из статей Confluence
- 🔗 **Созданию цепочек изменений** (Epic → Feature → Backlog Item)
- 📋 **Генерации чек-листов БДК ЗЗЛ** для проверки готовности
- 📊 **Мониторингу статуса** всех подключенных сервисов

**Важно**: Не забудьте активировать виртуальное окружение перед запуском:
```bash
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS
```

**Удачной автоматизации!** 🚀
