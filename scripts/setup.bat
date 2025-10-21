@echo off
echo ========================================
echo TFS-Confluence Automation Setup
echo ========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Python found: 
python --version

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Copy environment file
echo.
echo Setting up environment configuration...
if not exist .env (
    if exist config.env (
        copy config.env .env
        echo Created .env file from config.env
        echo.
        echo IMPORTANT: Please edit .env file with your actual API keys and URLs
    ) else (
        echo WARNING: No config.env file found. Please create .env manually.
    )
) else (
    echo .env file already exists
)

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your API keys and URLs
echo 2. Run: python test_config.py
echo 3. Run: python run.py
echo.
pause
