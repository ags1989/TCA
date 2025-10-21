#!/usr/bin/env python3
"""
Скрипт для запуска тестов
"""
import sys
import subprocess
import argparse
import os
from pathlib import Path


def run_command(command, description):
    """Запускает команду и выводит результат"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при выполнении: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Запуск тестов для TFS-Confluence Automation")
    parser.add_argument("--type", choices=["unit", "integration", "all"], default="all",
                       help="Тип тестов для запуска")
    parser.add_argument("--coverage", action="store_true",
                       help="Запуск с покрытием кода")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Подробный вывод")
    parser.add_argument("--parallel", "-n", type=int, default=1,
                       help="Количество параллельных процессов")
    parser.add_argument("--pattern", "-k", type=str,
                       help="Фильтр тестов по паттерну")
    parser.add_argument("--markers", "-m", type=str,
                       help="Фильтр тестов по маркерам")
    
    args = parser.parse_args()
    
    # Переходим в корневую директорию проекта
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🎯 TFS-Confluence Automation - Запуск тестов")
    print(f"📁 Рабочая директория: {project_root}")
    
    # Базовые опции pytest
    pytest_options = ["pytest"]
    
    if args.verbose:
        pytest_options.append("-v")
    
    if args.coverage:
        pytest_options.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])
    
    if args.parallel > 1:
        pytest_options.extend(["-n", str(args.parallel)])
    
    if args.pattern:
        pytest_options.extend(["-k", args.pattern])
    
    if args.markers:
        pytest_options.extend(["-m", args.markers])
    
    # Определяем какие тесты запускать
    if args.type == "unit":
        pytest_options.append("tests/unit/")
        test_description = "Unit тесты"
    elif args.type == "integration":
        pytest_options.append("tests/integration/")
        test_description = "Интеграционные тесты"
    else:
        pytest_options.append("tests/")
        test_description = "Все тесты"
    
    # Запускаем тесты
    command = " ".join(pytest_options)
    success = run_command(command, test_description)
    
    if success:
        print(f"\n✅ {test_description} выполнены успешно!")
        
        if args.coverage:
            print("\n📊 Отчет о покрытии кода создан в htmlcov/index.html")
    else:
        print(f"\n❌ {test_description} завершились с ошибками!")
        sys.exit(1)


if __name__ == "__main__":
    main()
