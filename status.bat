@echo off
chcp 65001 >nul
echo ========================================
echo   TFS-Confluence Automation Status
echo ========================================
echo.

echo Проверка Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python найден
    python --version
) else (
    echo ✗ Python не найден
    echo   Установите Python 3.11+ с https://www.python.org/downloads/
    echo   Или через Microsoft Store
)

echo.
echo Проверка виртуального окружения...
if exist "venv\Scripts\activate.bat" (
    echo ✓ Виртуальное окружение найдено
) else (
    echo ✗ Виртуальное окружение не найдено
    echo   Запустите setup.bat для создания
)

echo.
echo Проверка конфигурации...
if exist ".env" (
    echo ✓ Файл конфигурации .env найден
) else (
    echo ✗ Файл конфигурации .env не найден
    echo   Скопируйте env.example в .env
)

echo.
echo Проверка зависимостей...
if exist "requirements.txt" (
    echo ✓ Файл зависимостей requirements.txt найден
) else (
    echo ✗ Файл зависимостей requirements.txt не найден
)

echo.
echo Проверка основного скрипта...
if exist "run.py" (
    echo ✓ Основной скрипт run.py найден
) else (
    echo ✗ Основной скрипт run.py не найден
)

echo.
echo Проверка порта 8000...
netstat -an | findstr ":8000" >nul
if %errorlevel% equ 0 (
    echo ✓ Порт 8000 занят (приложение запущено)
) else (
    echo ○ Порт 8000 свободен (приложение не запущено)
)

echo.
echo Проверка процессов Python...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table /nh 2^>nul ^| findstr "python.exe"') do (
    echo ✓ Найден процесс Python с PID: %%i
)

echo.
echo ========================================
echo   Статус проверки завершен
echo ========================================
echo.
echo Для запуска приложения используйте: start.bat
echo Для остановки приложения используйте: stop.bat
echo Для перезапуска приложения используйте: restart.bat
echo.
pause
