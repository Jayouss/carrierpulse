@echo off
setlocal enabledelayedexpansion
title CarrierPulse - Automated Installer

echo ================================================================
echo               CARRIER PULSE - INSTALLATION
echo       Commercial Telecom Discovery & Line Verification
echo ================================================================
echo.

:: 1. Check Python installation
echo [1/4] Checking Python availability...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not found in system PATH.
    echo Please install Python 3.11 or newer from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%a in ('python --version 2^>^&1') do set PY_VER=%%a
echo [OK] Detected Python %PY_VER%
echo.

:: 2. Create virtual environment
echo [2/4] Setting up Python virtual environment (.venv)...
if not exist ".venv" (
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created successfully.
) else (
    echo [OK] Existing virtual environment found.
)
echo.

:: 3. Upgrade pip and install dependencies
echo [3/4] Installing required packages...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Package installation failed. Please check your internet connection.
    pause
    exit /b 1
)
echo [OK] Dependencies installed successfully.
echo.

:: 4. Verify installation
echo [4/4] Verifying setup...
python -c "import fastapi, uvicorn, httpx, phonenumbers, keyring; print('[OK] All core libraries loaded successfully.')"
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Verification warning. Some modules may require manual check.
)

echo.
echo ================================================================
echo               INSTALLATION COMPLETE!
echo ================================================================
echo You can now launch the application anytime by double-clicking:
echo                    "Start App.bat"
echo ================================================================
echo.
pause
