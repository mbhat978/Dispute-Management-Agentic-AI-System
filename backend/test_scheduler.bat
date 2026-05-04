@echo off
echo ========================================
echo Compliance Scheduler Test Menu
echo ========================================
echo.
echo 1. Run all tasks once (Recommended)
echo 2. Run with 30-second intervals
echo 3. Show scheduler information
echo 4. Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto once
if "%choice%"=="2" goto test
if "%choice%"=="3" goto info
if "%choice%"=="4" goto end

:once
echo.
echo Running all tasks once...
call venv\Scripts\activate.bat
python test_scheduler.py --once
pause
goto end

:test
echo.
echo Starting scheduler with 30-second intervals...
echo Press Ctrl+C to stop
call venv\Scripts\activate.bat
python test_scheduler.py --test
pause
goto end

:info
echo.
call venv\Scripts\activate.bat
python test_scheduler.py --info
pause
goto end

:end

@REM Made with Bob
