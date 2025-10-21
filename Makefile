# Makefile для TFS-Confluence Automation

.PHONY: help install test test-unit test-integration test-coverage test-watch clean lint format

# Цвета для вывода
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

help: ## Показать справку
	@echo "$(GREEN)TFS-Confluence Automation - Доступные команды:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Установить зависимости
	@echo "$(GREEN)📦 Установка зависимостей...$(NC)"
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov pytest-xdist pytest-html

test: ## Запустить все тесты
	@echo "$(GREEN)🧪 Запуск всех тестов...$(NC)"
	python tests/run_tests.py --type all

test-unit: ## Запустить unit тесты
	@echo "$(GREEN)🧪 Запуск unit тестов...$(NC)"
	python tests/run_tests.py --type unit

test-integration: ## Запустить интеграционные тесты
	@echo "$(GREEN)🧪 Запуск интеграционных тестов...$(NC)"
	python tests/run_tests.py --type integration

test-coverage: ## Запустить тесты с покрытием кода
	@echo "$(GREEN)🧪 Запуск тестов с покрытием кода...$(NC)"
	python tests/run_tests.py --type all --coverage

test-watch: ## Запустить тесты в режиме наблюдения
	@echo "$(GREEN)🧪 Запуск тестов в режиме наблюдения...$(NC)"
	pytest-watch tests/ --runner "python tests/run_tests.py --type all"

test-parallel: ## Запустить тесты параллельно
	@echo "$(GREEN)🧪 Запуск тестов параллельно...$(NC)"
	python tests/run_tests.py --type all --parallel 4

test-api: ## Запустить только API тесты
	@echo "$(GREEN)🧪 Запуск API тестов...$(NC)"
	python tests/run_tests.py --type integration --markers "api"

test-confluence: ## Запустить только тесты Confluence
	@echo "$(GREEN)🧪 Запуск тестов Confluence...$(NC)"
	python tests/run_tests.py --type integration --markers "confluence"

test-tfs: ## Запустить только тесты TFS
	@echo "$(GREEN)🧪 Запуск тестов TFS...$(NC)"
	python tests/run_tests.py --type integration --markers "tfs"

test-user-story: ## Запустить только тесты User Story
	@echo "$(GREEN)🧪 Запуск тестов User Story...$(NC)"
	python tests/run_tests.py --type integration --markers "user_story"

lint: ## Проверить код линтерами
	@echo "$(GREEN)🔍 Проверка кода линтерами...$(NC)"
	flake8 app/ tests/ --max-line-length=120 --ignore=E203,W503
	pylint app/ --disable=C0114,C0116

format: ## Форматировать код
	@echo "$(GREEN)🎨 Форматирование кода...$(NC)"
	black app/ tests/ --line-length=120
	isort app/ tests/ --profile black

clean: ## Очистить временные файлы
	@echo "$(GREEN)🧹 Очистка временных файлов...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

dev-setup: install ## Настройка окружения для разработки
	@echo "$(GREEN)🛠️ Настройка окружения для разработки...$(NC)"
	pip install pre-commit
	pre-commit install

ci-test: ## Запуск тестов для CI/CD
	@echo "$(GREEN)🤖 Запуск тестов для CI/CD...$(NC)"
	python tests/run_tests.py --type all --coverage --parallel 2

# Команды для разработки
run-dev: ## Запустить приложение в режиме разработки
	@echo "$(GREEN)🚀 Запуск приложения в режиме разработки...$(NC)"
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Запустить приложение в продакшене
	@echo "$(GREEN)🚀 Запуск приложения в продакшене...$(NC)"
	uvicorn app.main:app --host 0.0.0.0 --port 8000

# Команды для тестирования
test-quick: ## Быстрые тесты (только unit)
	@echo "$(GREEN)⚡ Быстрые тесты...$(NC)"
	python tests/run_tests.py --type unit

test-slow: ## Медленные тесты (только интеграционные)
	@echo "$(GREEN)🐌 Медленные тесты...$(NC)"
	python tests/run_tests.py --type integration --markers "slow"

# Команды для отладки
test-debug: ## Запустить тесты в режиме отладки
	@echo "$(GREEN)🐛 Запуск тестов в режиме отладки...$(NC)"
	python tests/run_tests.py --type all --verbose

test-failed: ## Запустить только провалившиеся тесты
	@echo "$(GREEN)🔄 Запуск провалившихся тестов...$(NC)"
	pytest --lf -v

# Команды для документации
docs: ## Сгенерировать документацию
	@echo "$(GREEN)📚 Генерация документации...$(NC)"
	pdoc --html app --output-dir docs

# Команды для безопасности
security: ## Проверить безопасность
	@echo "$(GREEN)🔒 Проверка безопасности...$(NC)"
	safety check
	bandit -r app/

# Команды для мониторинга
monitor: ## Мониторинг тестов
	@echo "$(GREEN)📊 Мониторинг тестов...$(NC)"
	pytest --html=reports/test_report.html --self-contained-html

# Команды для профилирования
profile: ## Профилирование тестов
	@echo "$(GREEN)📈 Профилирование тестов...$(NC)"
	python -m cProfile -o profile.stats tests/run_tests.py --type all
