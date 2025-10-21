# Тесты для TFS-Confluence Automation

Этот каталог содержит все тесты для приложения TFS-Confluence Automation.

## Структура тестов

```
tests/
├── __init__.py                 # Инициализация пакета тестов
├── conftest.py                 # Конфигурация pytest и фикстуры
├── run_tests.py                # Скрипт для запуска тестов
├── README.md                   # Документация по тестам
├── unit/                       # Unit тесты
│   ├── test_models.py          # Тесты моделей данных
│   └── test_services.py        # Тесты сервисов
├── integration/                # Интеграционные тесты
│   ├── test_api_endpoints.py   # Тесты API endpoints
│   ├── test_confluence_integration.py  # Тесты Confluence API
│   ├── test_tfs_integration.py # Тесты TFS API
│   └── test_user_story_creation.py     # Тесты создания User Stories
└── fixtures/                   # Тестовые данные
    └── sample_data.py          # Образцы данных для тестов
```

## Типы тестов

### Unit тесты (`tests/unit/`)
- **test_models.py**: Тестирование моделей данных (Pydantic)
- **test_services.py**: Тестирование отдельных методов сервисов

### Интеграционные тесты (`tests/integration/`)
- **test_api_endpoints.py**: Тестирование API endpoints
- **test_confluence_integration.py**: Тестирование интеграции с Confluence
- **test_tfs_integration.py**: Тестирование интеграции с TFS
- **test_user_story_creation.py**: Тестирование создания User Stories

## Запуск тестов

### Быстрый запуск
```bash
# Все тесты
make test

# Только unit тесты
make test-unit

# Только интеграционные тесты
make test-integration

# Тесты с покрытием кода
make test-coverage
```

### Детальный запуск
```bash
# Запуск через pytest
pytest tests/

# Запуск с подробным выводом
pytest -v tests/

# Запуск с покрытием кода
pytest --cov=app tests/

# Запуск параллельно
pytest -n 4 tests/

# Запуск только определенных тестов
pytest -k "test_user_story" tests/
pytest -m "api" tests/
```

### Запуск через скрипт
```bash
# Все тесты
python tests/run_tests.py

# Unit тесты
python tests/run_tests.py --type unit

# Интеграционные тесты
python tests/run_tests.py --type integration

# С покрытием кода
python tests/run_tests.py --coverage

# Параллельно
python tests/run_tests.py --parallel 4

# Фильтр по паттерну
python tests/run_tests.py --pattern "test_user_story"

# Фильтр по маркерам
python tests/run_tests.py --markers "api"
```

## Маркеры тестов

- `unit`: Unit тесты
- `integration`: Интеграционные тесты
- `slow`: Медленные тесты
- `api`: API тесты
- `confluence`: Тесты Confluence
- `tfs`: Тесты TFS
- `user_story`: Тесты User Story

## Фикстуры

### Основные фикстуры (conftest.py)
- `test_app`: Тестовое приложение FastAPI
- `mock_confluence_service`: Мок Confluence сервиса
- `mock_tfs_service`: Мок TFS сервиса
- `mock_user_story_creator_service`: Мок User Story Creator сервиса
- `sample_confluence_article`: Образец статьи Confluence
- `sample_user_story_data`: Образец данных User Story
- `sample_tfs_response`: Образец ответа TFS
- `test_settings`: Настройки для тестов

### Образцы данных (fixtures/sample_data.py)
- `get_sample_confluence_article()`: Статья Confluence
- `get_sample_user_story_data()`: Данные User Story
- `get_sample_work_item_info()`: Work Item Info
- `get_sample_project_info()`: Project Info
- `get_sample_tfs_response()`: Ответ TFS API
- `get_sample_confluence_response()`: Ответ Confluence API

## Конфигурация

### pytest.ini
Основная конфигурация pytest с настройками:
- Пути к тестам
- Маркеры
- Опции по умолчанию
- Фильтры предупреждений

### Makefile
Удобные команды для разработки:
- `make test`: Запуск всех тестов
- `make test-unit`: Unit тесты
- `make test-integration`: Интеграционные тесты
- `make test-coverage`: С покрытием кода
- `make lint`: Проверка кода
- `make format`: Форматирование кода

## Покрытие кода

Для анализа покрытия кода:
```bash
# Запуск с покрытием
make test-coverage

# Просмотр отчета
open htmlcov/index.html
```

## Отладка тестов

### Запуск в режиме отладки
```bash
# Подробный вывод
pytest -v -s tests/

# Остановка на первой ошибке
pytest -x tests/

# Запуск только провалившихся тестов
pytest --lf tests/

# Запуск в режиме отладки
python -m pdb -m pytest tests/
```

### Логирование
```bash
# Включение логов
pytest --log-cli-level=DEBUG tests/

# Сохранение логов в файл
pytest --log-file=test.log tests/
```

## Непрерывная интеграция

### GitHub Actions
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: make ci-test
```

## Лучшие практики

1. **Именование тестов**: `test_<function_name>_<scenario>`
2. **Один тест - одна проверка**: Каждый тест проверяет одну функциональность
3. **Использование фикстур**: Переиспользование тестовых данных
4. **Мокирование внешних зависимостей**: Не зависим от внешних сервисов
5. **Чистые тесты**: Каждый тест независим от других
6. **Описательные сообщения**: Понятные assert сообщения

## Устранение неполадок

### Частые проблемы

1. **Ошибки импорта**: Убедитесь, что PYTHONPATH настроен правильно
2. **Ошибки асинхронности**: Используйте `pytest-asyncio`
3. **Ошибки моков**: Проверьте правильность настройки моков
4. **Ошибки зависимостей**: Установите все зависимости из `requirements-test.txt`

### Отладка

```bash
# Проверка установки pytest
pytest --version

# Проверка доступности модулей
python -c "import app; print('OK')"

# Запуск одного теста
pytest tests/unit/test_models.py::TestUserStoryData::test_user_story_data_valid -v
```

## Дополнительные ресурсы

- [Документация pytest](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
