@echo off
echo ========================================
echo Starting TFS-Confluence Automation
echo ========================================

REM Check if virtual environment exists
if not exist venv (
    echo ERROR: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found
    echo Please create .env file with your configuration
    pause
    exit /b 1
)

REM Start the application
echo.
echo Starting TFS-Confluence Automation server...
echo Server will be available at: http://localhost:8000
echo API documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python run.py
