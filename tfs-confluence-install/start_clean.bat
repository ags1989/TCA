@echo off
chcp 65001 >nul
echo ========================================
echo   TFS-Confluence Automation Start (Clean)
echo ========================================
echo.

echo Проверка виртуального окружения...
if not exist "venv\Scripts\activate.bat" (
    echo ОШИБКА: Виртуальное окружение не найдено
    echo Запустите setup.bat для первоначальной настройки
    pause
    exit /b 1
)

echo Активация виртуального окружения...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ОШИБКА: Не удалось активировать виртуальное окружение
    pause
    exit /b 1
)

echo Проверка конфигурации...
if not exist ".env" (
    echo ПРЕДУПРЕЖДЕНИЕ: Файл .env не найден
    echo Скопируйте env.example в .env и настройте API ключи
    echo.
)

echo Запуск приложения без reload (чистые логи)...
echo.
echo Приложение будет доступно по адресу: http://localhost:8000
echo Для остановки нажмите Ctrl+C
echo.
echo ========================================
python run_no_reload.py

echo.
echo Приложение остановлено
pause
