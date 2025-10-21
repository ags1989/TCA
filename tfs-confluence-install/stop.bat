@echo off
chcp 65001 >nul
echo ========================================
echo   TFS-Confluence Automation Stop
echo ========================================
echo.

echo Поиск процессов Python...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table /nh 2^>nul ^| findstr "python.exe"') do (
    echo Найден процесс Python с PID: %%i
    echo Завершение процесса...
    taskkill /pid %%i /f >nul 2>&1
    if %errorlevel% equ 0 (
        echo Процесс успешно завершен
    ) else (
        echo Не удалось завершить процесс (возможно, нет прав)
    )
)

echo.
echo Проверка порта 8000...
netstat -an | findstr ":8000" >nul
if %errorlevel% equ 0 (
    echo ПРЕДУПРЕЖДЕНИЕ: Порт 8000 все еще занят
    echo Возможно, приложение не остановилось полностью
) else (
    echo Порт 8000 свободен
)

echo.
echo ========================================
echo   Остановка завершена
echo ========================================
echo.
echo Для полной очистки также выполните:
echo - Деактивация виртуального окружения: deactivate
echo - Удаление виртуального окружения: rmdir /s /q venv
echo.
pause
