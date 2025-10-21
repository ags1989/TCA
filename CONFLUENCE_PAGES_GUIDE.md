# 📄 Руководство по созданию страниц в Confluence

## 🎯 Обзор функциональности

Система поддерживает создание страниц в Confluence через API с возможностью:
- Создания обычных страниц
- Создания страниц на основе шаблонов
- Добавления меток
- Указания родительской страницы
- Поиска существующих страниц

## 🔧 Обязательные поля для создания страницы

### Минимально необходимые поля:
```json
{
  "title": "Заголовок страницы",           // ОБЯЗАТЕЛЬНО
  "content": "Содержимое страницы",        // ОБЯЗАТЕЛЬНО  
  "space_key": "DEV"                       // ОБЯЗАТЕЛЬНО
}
```

### Дополнительные поля:
```json
{
  "parent_id": "123456789",                // ID родительской страницы
  "template_id": "template-123",           // ID шаблона
  "template_data": {                       // Данные для заполнения шаблона
    "title": "Заголовок",
    "description": "Описание",
    "date": "2024-01-01",
    "user": "username"
  },
  "labels": ["tag1", "tag2"],              // Метки страницы
  "page_type": "page",                     // Тип страницы (page, blogpost)
  "representation": "storage"              // Формат содержимого
}
```

## 🌐 API Endpoints

### 1. Создание страницы (полный запрос)
```http
POST /api/v1/confluence/pages
Content-Type: application/json

{
  "title": "Документация по задаче 123456",
  "content": "<h1>Описание задачи</h1><p>Детальное описание...</p>",
  "space_key": "DEV",
  "parent_id": "123456789",
  "template_id": "template-123",
  "labels": ["documentation", "task-123456"],
  "template_data": {
    "task_id": "123456",
    "assignee": "john.doe@company.com",
    "priority": "High"
  }
}
```

### 2. Быстрое создание страницы
```http
POST /api/v1/confluence/pages/quick-create?title=Заголовок&content=Содержимое&space_key=DEV&labels=tag1,tag2
```

### 3. Поиск страниц
```http
GET /api/v1/confluence/pages?query=поисковый запрос&space_key=DEV&limit=10
```

### 4. Получение шаблонов
```http
GET /api/v1/confluence/templates?space_key=DEV
```

### 5. Получение пространств
```http
GET /api/v1/confluence/spaces
```

## 📝 Примеры использования

### Пример 1: Создание простой страницы
```python
import requests

url = "http://localhost:8001/api/v1/confluence/pages/quick-create"
params = {
    "title": "Тестовая страница",
    "content": "<h1>Заголовок</h1><p>Содержимое страницы</p>",
    "space_key": "DEV",
    "labels": "test,documentation"
}

response = requests.post(url, params=params)
print(response.json())
```

### Пример 2: Создание страницы с шаблоном
```python
import requests

url = "http://localhost:8001/api/v1/confluence/pages"
data = {
    "title": "Документация по задаче 123456",
    "content": "<p>Базовое содержимое</p>",
    "space_key": "DEV",
    "template_id": "template-123",
    "template_data": {
        "task_id": "123456",
        "assignee": "john.doe@company.com",
        "priority": "High",
        "description": "Описание задачи"
    },
    "labels": ["documentation", "task-123456"]
}

response = requests.post(url, json=data)
print(response.json())
```

### Пример 3: Поиск страниц
```python
import requests

url = "http://localhost:8001/api/v1/confluence/pages"
params = {
    "query": "документация",
    "space_key": "DEV",
    "limit": 10
}

response = requests.get(url, params=params)
print(response.json())
```

## 🎨 Работа с шаблонами

### Создание страницы на основе шаблона

1. **Получение списка шаблонов:**
```http
GET /api/v1/confluence/templates
```

2. **Создание страницы с шаблоном:**
```json
{
  "title": "Страница с шаблоном",
  "content": "<p>Базовое содержимое</p>",
  "space_key": "DEV",
  "template_id": "template-123",
  "template_data": {
    "title": "Заголовок",
    "description": "Описание",
    "date": "2024-01-01",
    "user": "username",
    "project": "ProjectName",
    "task_id": "123456"
  }
}
```

### Переменные шаблона

Система поддерживает следующие переменные:
- `{{title}}` - заголовок
- `{{description}}` - описание
- `{{date}}` - дата
- `{{time}}` - время
- `{{user}}` - пользователь
- `{{project}}` - проект
- `{{task_id}}` - ID задачи
- `{{custom_variable}}` - пользовательские переменные

## 🔍 Поиск и фильтрация

### Параметры поиска:
- `query` - поисковый запрос (обязательно)
- `space_key` - ключ пространства (опционально)
- `content_type` - тип контента: "page", "blogpost", "comment" (по умолчанию "page")
- `limit` - максимальное количество результатов (1-100, по умолчанию 10)
- `start` - начальная позиция для пагинации (по умолчанию 0)

### Пример поиска:
```http
GET /api/v1/confluence/pages?query=документация&space_key=DEV&content_type=page&limit=20
```

## 📊 Форматы содержимого

### 1. Storage Format (HTML) - по умолчанию
```html
<h1>Заголовок</h1>
<p>Параграф с <strong>жирным</strong> текстом</p>
<ul>
  <li>Элемент списка 1</li>
  <li>Элемент списка 2</li>
</ul>
```

### 2. Wiki Format
```wiki
h1. Заголовок
* Элемент списка 1
* Элемент списка 2
```

### 3. Atlas Document Format
```json
{
  "type": "doc",
  "content": [
    {
      "type": "heading",
      "attrs": {"level": 1},
      "content": [{"type": "text", "text": "Заголовок"}]
    }
  ]
}
```

## 🏷️ Работа с метками

### Добавление меток:
```json
{
  "title": "Страница с метками",
  "content": "<p>Содержимое</p>",
  "space_key": "DEV",
  "labels": ["documentation", "api", "test", "automation"]
}
```

### Поиск по меткам:
```http
GET /api/v1/confluence/pages?query=label:documentation
```

## 🔗 Создание иерархии страниц

### Создание дочерней страницы:
```json
{
  "title": "Дочерняя страница",
  "content": "<p>Содержимое дочерней страницы</p>",
  "space_key": "DEV",
  "parent_id": "123456789"
}
```

## ⚠️ Обработка ошибок

### Типичные ошибки:

1. **Ошибка аутентификации (401):**
```json
{
  "success": false,
  "error": "Ошибка аутентификации: Invalid credentials"
}
```

2. **Ошибка валидации (400):**
```json
{
  "success": false,
  "error": "Ошибка валидации: Title is required"
}
```

3. **Ошибка доступа (403):**
```json
{
  "success": false,
  "error": "Ошибка доступа: Insufficient permissions"
}
```

4. **Ошибка пространства (404):**
```json
{
  "success": false,
  "error": "Пространство не найдено: Space 'INVALID' does not exist"
}
```

## 🚀 Быстрый старт

### 1. Проверка подключения:
```bash
curl "http://localhost:8001/api/v1/status"
```

### 2. Получение пространств:
```bash
curl "http://localhost:8001/api/v1/confluence/spaces"
```

### 3. Создание простой страницы:
```bash
curl -X POST "http://localhost:8001/api/v1/confluence/pages/quick-create" \
  -G -d "title=Тестовая страница" \
  -d "content=<h1>Тест</h1><p>Содержимое</p>" \
  -d "space_key=DEV" \
  -d "labels=test,api"
```

### 4. Поиск страниц:
```bash
curl "http://localhost:8001/api/v1/confluence/pages?query=тест&space_key=DEV"
```

## 📋 Чек-лист для создания страницы

- [ ] Указан заголовок страницы
- [ ] Указано содержимое страницы
- [ ] Указан ключ пространства
- [ ] Проверено подключение к Confluence
- [ ] Проверены права доступа к пространству
- [ ] При необходимости указан ID родительской страницы
- [ ] При необходимости указан ID шаблона
- [ ] При необходимости указаны данные для шаблона
- [ ] При необходимости указаны метки

## 🔧 Настройка

### Переменные окружения:
```env
CONFLUENCE_URL=https://your-confluence.atlassian.net
CONFLUENCE_USER=your-email@company.com
CONFLUENCE_TOKEN=your-api-token
```

### Проверка настроек:
```python
from app.config.settings import settings
print(f"Confluence URL: {settings.CONFLUENCE_URL}")
print(f"Confluence User: {settings.CONFLUENCE_USER}")
```

## 📚 Дополнительные ресурсы

- [Confluence REST API Documentation](https://developer.atlassian.com/cloud/confluence/rest/)
- [Confluence Content Format](https://developer.atlassian.com/cloud/confluence/content-format/)
- [Confluence Templates](https://confluence.atlassian.com/doc/confluence-templates-139464.html)
