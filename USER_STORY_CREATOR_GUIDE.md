# Руководство по созданию User Stories из Confluence

## Обзор

Новая функция позволяет автоматически создавать User Stories в TFS на основе страниц Confluence. Система парсит статьи, извлекает User Stories и критерии приёмки, а затем создает соответствующие Work Items в TFS с необходимыми связями.

## Возможности

- ✅ **Парсинг страниц Confluence** - автоматическое извлечение User Stories
- ✅ **Предварительный просмотр** - показ того, что будет создано
- ✅ **Множественные User Stories** - поддержка US1, US2, US3 и т.д.
- ✅ **Автоматические связи** - связывание с родительским тикетом
- ✅ **Форматирование** - выделение ключевых слов жирным шрифтом
- ✅ **Логирование** - детальное отслеживание операций
- ✅ **Подтверждение пользователя** - контроль над созданием

## API Endpoints

### 1. Создание User Stories

```http
POST /api/v1/user-stories/create-from-confluence
Content-Type: application/json

{
    "confluence_url": "https://confluence.systtech.ru/pages/viewpage.action?pageId=4049385861",
    "user_confirmation": "Да"  // опционально
}
```

**Ответ при предварительном просмотре:**
```json
{
    "success": true,
    "preview": {
        "confluence_url": "https://confluence.systtech.ru/pages/viewpage.action?pageId=4049385861",
        "article_title": "229634 [TDD] [ЧВ] Оценить стоимость переименования полей в Ч-Web",
        "project": "Синергия",
        "parent_ticket": "229634",
        "user_stories_count": 2,
        "user_stories": [
            {
                "title": "US1: Переименование реквизита для Чикаго Веб",
                "description": "Я, как сотрудник ЦО, хочу переименовать реквизиты...",
                "acceptance_criteria": [
                    "Дано: Сотрудник ЦО готовит файл с кастомными переводами",
                    "Когда: Специалист ИТ-команды заполняет файлы перевода",
                    "Тогда: Система загружает файлы без ошибок"
                ],
                "us_number": "US1"
            }
        ]
    },
    "needs_confirmation": true
}
```

**Ответ после создания:**
```json
{
    "success": true,
    "created_stories": [
        {
            "id": 123456,
            "title": "US1: Переименование реквизита для Чикаго Веб",
            "us_number": "US1",
            "url": "https://tfssrv.systtech.ru/tfs/DefaultCollection/Backlog/_workitems/edit/123456"
        }
    ],
    "parent_ticket": "229634",
    "confluence_url": "https://confluence.systtech.ru/pages/viewpage.action?pageId=4049385861"
}
```

### 2. Предварительный просмотр

```http
GET /api/v1/user-stories/preview/{confluence_url}
```

### 3. Подтверждение создания

```http
POST /api/v1/user-stories/confirm-creation
?confluence_url=https://confluence.systtech.ru/pages/viewpage.action?pageId=4049385861
&user_confirmation=Да
```

### 4. Проверка состояния

```http
GET /api/v1/user-stories/health
```

## Структура создаваемых User Stories

### Поля TFS

| Поле | Значение | Описание |
|------|----------|----------|
| **System.Title** | "US1: [название]" | Заголовок с номером US |
| **System.Description** | HTML-форматированное описание | User Story с выделенными ключевыми словами |
| **Microsoft.VSTS.Common.AcceptanceCriteria** | HTML-критерии | Критерии приёмки из статьи |
| **System.State** | "New" | Начальное состояние |
| **System.AssignedTo** | Текущий пользователь | Исполнитель |
| **System.Tags** | "confluence; auto-generated; TCA" | Теги |
| **System.History** | Комментарий о создании | История с ссылкой на статью |
| **Custom.WikiLink** | URL статьи | Ссылка на исходную статью |

### Связи

- **Родитель в Backlog** → № TFS из статьи
- **Комментарий связи**: "Связан с родительским тикетом #[номер] из Confluence"

## Алгоритм работы

### 1. Парсинг Confluence
```
1.1. Извлечение pageId из URL
1.2. Запрос к Confluence API
1.3. Парсинг метаданных (Проект, № TFS)
1.4. Поиск User Stories (US1, US2, US3...)
1.5. Извлечение критериев приёмки
```

### 2. Предварительный просмотр
```
2.1. Формирование списка найденных US
2.2. Показ описаний и критериев
2.3. Отображение связей
2.4. Запрос подтверждения
```

### 3. Создание в TFS
```
3.1. Создание каждой User Story
3.2. Форматирование HTML-описаний
3.3. Создание связей с родительским тикетом
3.4. Добавление комментариев и ссылок
3.5. Логирование результатов
```

## Примеры использования

### Python (requests)

```python
import requests

# 1. Получение предварительного просмотра
response = requests.post(
    "http://127.0.0.1:8000/api/v1/user-stories/create-from-confluence",
    json={"confluence_url": "https://confluence.systtech.ru/pages/viewpage.action?pageId=4049385861"}
)

preview = response.json()
print(f"Найдено User Stories: {preview['preview']['user_stories_count']}")

# 2. Подтверждение создания
if input("Создать? (Да/Нет): ") == "Да":
    confirm_response = requests.post(
        "http://127.0.0.1:8000/api/v1/user-stories/confirm-creation",
        params={
            "confluence_url": "https://confluence.systtech.ru/pages/viewpage.action?pageId=4049385861",
            "user_confirmation": "Да"
        }
    )
    
    result = confirm_response.json()
    for story in result["created_stories"]:
        print(f"Создана: {story['title']} (ID: {story['id']})")
```

### cURL

```bash
# Предварительный просмотр
curl -X POST "http://127.0.0.1:8000/api/v1/user-stories/create-from-confluence" \
  -H "Content-Type: application/json" \
  -d '{"confluence_url": "https://confluence.systtech.ru/pages/viewpage.action?pageId=4049385861"}'

# Подтверждение создания
curl -X POST "http://127.0.0.1:8000/api/v1/user-stories/confirm-creation" \
  -d "confluence_url=https://confluence.systtech.ru/pages/viewpage.action?pageId=4049385861" \
  -d "user_confirmation=Да"
```

## Обработка ошибок

### Типичные ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| "Не удалось извлечь pageId" | Некорректный URL | Проверить формат URL Confluence |
| "В статье не найдены User Stories" | Отсутствуют US в статье | Проверить структуру статьи |
| "Родительский тикет не найден" | № TFS не существует | Проверить номер тикета |
| "Ошибка при создании User Story" | Проблемы с TFS API | Проверить права доступа |

### Логирование

Все операции логируются с детальной информацией:

```
2024-12-23 15:30:15 | INFO | User Story Creator | create_user_stories:123 | 
✅ User Stories созданы успешно:
   📄 Статья: https://confluence.systtech.ru/pages/viewpage.action?pageId=4049385861
   🔗 Родительский тикет: #229634
   📊 Создано User Stories: 2
   
   📋 US1: Переименование реквизита для Чикаго Веб
      🆔 ID: 123456
      🔗 Связан с: #229634 (Родитель в Backlog)
      🔗 URL: https://tfssrv.systtech.ru/tfs/DefaultCollection/Backlog/_workitems/edit/123456
```

## Требования к статьям Confluence

### Обязательные элементы

1. **Таблица метаданных** с полями:
   - Проект
   - № TFS

2. **Секция User Stories** с:
   - US1, US2, US3 и т.д.
   - Текст в формате "Я, как... хочу... чтобы..."
   - Критерии приёмки в таблице "Дано/Когда/Тогда"

### Пример структуры статьи

```markdown
| Проект | Синергия |
| № TFS | 229634 |
| ... | ... |

## User Stories и критерии приёмки

| Название US | User Story | Дано | Когда | Тогда |
|-------------|------------|------|-------|-------|
| US1Переименование реквизита | Я, как сотрудник ЦО, хочу переименовать реквизиты... | Сотрудник ЦО готовит файл... | Специалист ИТ-команды заполняет... | Система загружает файлы... |
```

## Настройка

### Переменные окружения

```env
# Confluence
CONFLUENCE_URL=https://confluence.systtech.ru
CONFLUENCE_USER=your-email@company.com
CONFLUENCE_TOKEN=your_token

# TFS
TFS_URL=https://tfssrv.systtech.ru/tfs/DefaultCollection
TFS_PAT_TOKEN=your_pat_token
TFS_PROJECT=Backlog
```

### Кастомные поля

При необходимости можно добавить дополнительные поля в создаваемые User Stories, изменив метод `_create_single_user_story` в `UserStoryCreatorService`.

## Мониторинг и отладка

### Проверка состояния

```bash
curl http://127.0.0.1:8000/api/v1/user-stories/health
```

### Логи

Логи сохраняются в файл `logs/app.log` с детальной информацией о каждой операции.

### Отладка парсинга

Для отладки парсинга Confluence можно использовать метод `_parse_confluence_page` напрямую:

```python
from app.services.user_story_creator_service import user_story_creator_service

page_data = await user_story_creator_service._parse_confluence_page(confluence_url)
print(f"Найдено User Stories: {len(page_data.user_stories)}")
```
