@echo off
setlocal enabledelayedexpansion
title CarrierPulse - Telecom Discovery Platform

echo ================================================================
echo                       CARRIER PULSE
echo       Commercial Telecom Discovery & Line Verification
echo ================================================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo [NOTICE] Virtual environment not found. Checking system Python...
    python -c "import fastapi, uvicorn, phonenumbers" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Dependencies are not installed.
        echo Please run "Install.bat" first to set up the environment.
        echo.
        pause
        exit /b 1
    )
) else (
    call .venv\Scripts\activate.bat
)

echo Starting CarrierPulse server...
echo URL: http://127.0.0.1:8765
echo.
echo Opening your web browser...

:: Open default browser after a 2-second delay in background
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8765"

:: Start Uvicorn server on localhost
python -m uvicorn app.main:app --host 127.0.0.1 --port 8765

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] The server stopped unexpectedly.
    pause
)
