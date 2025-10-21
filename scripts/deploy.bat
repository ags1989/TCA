@echo off
echo ========================================
echo Deploying TFS-Confluence Automation
echo ========================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop and try again
    pause
    exit /b 1
)

echo Docker found:
docker --version

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found
    echo Please create .env file with your configuration
    pause
    exit /b 1
)

REM Build and start with Docker Compose
echo.
echo Building and starting containers...
docker-compose up --build -d

if errorlevel 1 (
    echo ERROR: Failed to start containers
    pause
    exit /b 1
)

echo.
echo ========================================
echo Deployment completed successfully!
echo ========================================
echo.
echo Application is running at:
echo - Main app: http://localhost:8000
echo - API docs: http://localhost:8000/docs
echo - Health check: http://localhost:8000/health
echo.
echo To view logs: docker-compose logs -f
echo To stop: docker-compose down
echo.
pause
