@echo off
chcp 65001 >nul
echo ========================================
echo   TFS-Confluence Automation Setup
echo ========================================
echo.

echo [0/4] Проверка Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не найден!
    echo.
    echo Для установки Python:
    echo 1. Перейдите на https://www.python.org/downloads/
    echo 2. Скачайте Python 3.11 или новее
    echo 3. При установке ОБЯЗАТЕЛЬНО отметьте "Add Python to PATH"
    echo 4. Перезапустите этот скрипт после установки
    echo.
    echo Альтернативно, установите через Microsoft Store:
    echo - Откройте Microsoft Store
    echo - Найдите "Python 3.11" или "Python 3.12"
    echo - Нажмите "Установить"
    echo.
    pause
    exit /b 1
) else (
    echo ✓ Python найден
    python --version
)

echo.
echo [1/4] Создание виртуального окружения...
python -m venv venv
if %errorlevel% neq 0 (
    echo ОШИБКА: Не удалось создать виртуальное окружение
    echo Убедитесь, что Python установлен и доступен в PATH
    pause
    exit /b 1
)

echo [2/4] Активация виртуального окружения...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ОШИБКА: Не удалось активировать виртуальное окружение
    pause
    exit /b 1
)

echo [3/4] Обновление pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo ПРЕДУПРЕЖДЕНИЕ: Не удалось обновить pip, продолжаем...
)

echo [4/4] Установка зависимостей...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ОШИБКА: Не удалось установить зависимости
    echo Проверьте файл requirements.txt
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Установка завершена успешно!
echo ========================================
echo.
echo Следующие шаги:
echo 1. Скопируйте env.example в .env
echo 2. Отредактируйте .env с вашими API ключами
echo 3. Запустите start.bat для запуска приложения
echo.
echo Нажмите любую клавишу для выхода...
pause >nul
