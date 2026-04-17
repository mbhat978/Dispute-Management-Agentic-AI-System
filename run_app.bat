@echo off
echo ===================================
echo Multi-Agent AI System Launcher
echo ===================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ first
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js first
    pause
    exit /b 1
)

echo [1/4] Checking backend dependencies...
cd backend
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing/Updating backend dependencies...
pip install -r requirements.txt >nul 2>&1

cd ..

echo [2/4] Checking frontend dependencies...
cd frontend
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)
cd ..

echo [3/4] Starting Backend (FastAPI on port 8000)...
start "Backend" cmd /k "cd backend && venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000"

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo [4/4] Starting Frontend (Next.js on port 3000)...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================
echo System Started Successfully!
echo ===================================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C in each window to stop the servers.
echo ===================================

pause