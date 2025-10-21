@echo off
chcp 65001 >nul
echo ========================================
echo   TFS-Confluence Automation Clean
echo ========================================
echo.

echo ВНИМАНИЕ: Этот скрипт удалит виртуальное окружение и временные файлы
echo.
set /p confirm="Вы уверены? (y/N): "
if /i not "%confirm%"=="y" (
    echo Операция отменена
    pause
    exit /b 0
)

echo.
echo Остановка приложения...
call stop.bat

echo.
echo Удаление виртуального окружения...
if exist "venv" (
    rmdir /s /q venv
    if %errorlevel% equ 0 (
        echo ✓ Виртуальное окружение удалено
    ) else (
        echo ✗ Не удалось удалить виртуальное окружение
    )
) else (
    echo ○ Виртуальное окружение не найдено
)

echo.
echo Удаление временных файлов...
if exist "__pycache__" (
    rmdir /s /q __pycache__
    echo ✓ Кэш Python удален
)

if exist "*.pyc" (
    del /q *.pyc
    echo ✓ Скомпилированные файлы Python удалены
)

if exist "logs" (
    echo Удаление логов...
    del /q logs\*.log 2>nul
    echo ✓ Логи удалены
)

echo.
echo Удаление файлов конфигурации...
if exist ".env" (
    set /p delenv="Удалить файл .env? (y/N): "
    if /i "%delenv%"=="y" (
        del .env
        echo ✓ Файл .env удален
    )
)

echo.
echo ========================================
echo   Очистка завершена
echo ========================================
echo.
echo Для повторной установки запустите: setup.bat
echo.
pause
