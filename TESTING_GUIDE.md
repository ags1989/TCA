# 🧪 Руководство по тестированию TFS-Confluence Automation

## Быстрый старт

### 1. Установка зависимостей
```bash
# Установка зависимостей для тестов
pip install -r requirements-test.txt

# Или через make
make install
```

### 2. Запуск тестов
```bash
# Все тесты
make test

# Только unit тесты
make test-unit

# Только интеграционные тесты
make test-integration

# С покрытием кода
make test-coverage
```

## 📊 Статистика тестов

- **Общее количество тестов**: 101
- **Unit тесты**: 39
- **Интеграционные тесты**: 62
- **Покрытие кода**: Настраивается через pytest-cov

## 🎯 Типы тестов

### Unit тесты (`tests/unit/`)
- **test_models.py**: 22 теста - Валидация моделей данных
- **test_services.py**: 17 тестов - Тестирование сервисов

### Интеграционные тесты (`tests/integration/`)
- **test_api_endpoints.py**: 10 тестов - API endpoints
- **test_confluence_integration.py**: 10 тестов - Confluence API
- **test_tfs_integration.py**: 15 тестов - TFS API
- **test_user_story_creation.py**: 16 тестов - Создание User Stories
- **test_system_integration.py**: 11 тестов - Комплексные тесты

## 🚀 Команды для разработки

### Основные команды
```bash
# Все тесты
make test

# Быстрые тесты (только unit)
make test-quick

# Медленные тесты (только интеграционные)
make test-slow

# Тесты с покрытием кода
make test-coverage

# Параллельный запуск
make test-parallel
```

### Специализированные команды
```bash
# Только API тесты
make test-api

# Только Confluence тесты
make test-confluence

# Только TFS тесты
make test-tfs

# Только User Story тесты
make test-user-story
```

### Отладка
```bash
# Подробный вывод
make test-debug

# Только провалившиеся тесты
make test-failed

# Наблюдение за изменениями
make test-watch
```

## 🔧 Настройка окружения

### Переменные окружения для тестов
```bash
# Confluence
export CONFLUENCE_URL="https://confluence.example.com"
export CONFLUENCE_USERNAME="test_user"
export CONFLUENCE_PASSWORD="test_password"

# TFS
export TFS_URL="https://tfssrv.systtech.ru/tfs/DefaultCollection"
export TFS_PAT="test_pat_token"
export TFS_PROJECT="Houston"
```

### Конфигурация pytest
Файл `pytest.ini` содержит:
- Пути к тестам
- Маркеры тестов
- Опции по умолчанию
- Фильтры предупреждений

## 📈 Анализ результатов

### Покрытие кода
```bash
# Запуск с покрытием
make test-coverage

# Просмотр отчета
open htmlcov/index.html
```

### Отчеты
```bash
# HTML отчет
pytest --html=reports/test_report.html --self-contained-html

# JUnit XML
pytest --junitxml=reports/junit.xml
```

## 🐛 Устранение неполадок

### Частые проблемы

1. **Ошибки импорта**
   ```bash
   # Проверка PYTHONPATH
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Ошибки асинхронности**
   ```bash
   # Убедитесь, что установлен pytest-asyncio
   pip install pytest-asyncio
   ```

3. **Ошибки зависимостей**
   ```bash
   # Переустановка зависимостей
   pip install -r requirements-test.txt --force-reinstall
   ```

### Отладка
```bash
# Запуск одного теста
pytest tests/unit/test_models.py::TestUserStoryData::test_user_story_data_valid -v

# Запуск с отладкой
pytest --pdb tests/

# Запуск с логами
pytest --log-cli-level=DEBUG tests/
```

## 🔄 Непрерывная интеграция

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
        run: make install
      - name: Run tests
        run: make ci-test
```

### Локальная CI
```bash
# Запуск как в CI
make ci-test
```

## 📚 Дополнительные ресурсы

- [Документация pytest](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Подробная документация тестов](tests/README.md)

## 🎯 Лучшие практики

1. **Запускайте тесты перед каждым коммитом**
2. **Используйте моки для внешних зависимостей**
3. **Пишите тесты для новых функций**
4. **Поддерживайте высокое покрытие кода**
5. **Используйте описательные имена тестов**

---

**Готово к тестированию! 🚀**
