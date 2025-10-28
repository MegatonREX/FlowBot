@echo off
REM FlowBot GUI Launcher for Windows
REM This script launches the FlowBot GUI application

echo.
echo ========================================
echo   FlowBot - AI Workflow Assistant
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if PyQt6 is installed
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo WARNING: PyQt6 is not installed
    echo Installing required dependencies...
    echo.
    pip install -r requirements_gui.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Starting FlowBot GUI...
echo.
python gui.py

if errorlevel 1 (
    echo.
    echo ERROR: FlowBot GUI encountered an error
    pause
)
