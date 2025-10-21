@echo off
chcp 65001 >nul
echo ========================================
echo   Установка Python для TFS-Confluence
echo ========================================
echo.

echo Проверка наличия Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Python уже установлен
    python --version
    echo.
    echo Python найден! Можете запустить setup.bat
    pause
    exit /b 0
)

echo ❌ Python не найден!
echo.
echo ========================================
echo   Способы установки Python
echo ========================================
echo.

echo 1. ЧЕРЕЗ ОФИЦИАЛЬНЫЙ САЙТ (рекомендуется):
echo    https://www.python.org/downloads/
echo.
echo    Инструкция:
echo    - Скачайте Python 3.11 или новее
echo    - Запустите установщик
echo    - ОБЯЗАТЕЛЬНО отметьте "Add Python to PATH"
echo    - Нажмите "Install Now"
echo.

echo 2. ЧЕРЕЗ MICROSOFT STORE (простой способ):
echo    - Откройте Microsoft Store
echo    - Найдите "Python 3.11" или "Python 3.12"
echo    - Нажмите "Установить"
echo.

echo 3. ЧЕРЕЗ WINGET (если доступен):
echo    winget install Python.Python.3.11
echo.

echo 4. ЧЕРЕЗ CHOCOLATEY (если установлен):
echo    choco install python --version=3.11.0
echo.

echo ========================================
echo   Автоматическая установка через winget
echo ========================================
echo.

set /p auto_install="Попробовать автоматическую установку через winget? (y/N): "
if /i "%auto_install%"=="y" (
    echo.
    echo Попытка установки через winget...
    winget install Python.Python.3.11
    if %errorlevel% equ 0 (
        echo.
        echo ✓ Python установлен успешно!
        echo Перезапустите setup.bat
    ) else (
        echo.
        echo ❌ Автоматическая установка не удалась
        echo Установите Python вручную по инструкции выше
    )
) else (
    echo.
    echo Установите Python вручную по инструкции выше
    echo После установки запустите setup.bat
)

echo.
pause
