@echo off
chcp 65001 >nul
echo ========================================
echo   TFS-Confluence Automation Restart
echo ========================================
echo.

echo Остановка приложения...
call stop.bat

echo.
echo Ожидание 3 секунды...
timeout /t 3 /nobreak >nul

echo Запуск приложения...
call start.bat
