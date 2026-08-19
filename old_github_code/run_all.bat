@echo off
title BeeNavi AI - Unified Server Launcher
cd /d "%~dp0"

echo ======================================================
echo           BeeNavi AI - Unified Server Launcher
echo    AI RAG + Chatbot + User Diary + Itinerary Planner
echo ======================================================
echo.

REM Tim Python trong venv312 hoac he thong
set PYTHON_EXE=python
if exist "..\venv312\Scripts\python.exe" (
    set "PYTHON_EXE=..\venv312\Scripts\python.exe"
) else if exist "venv312\Scripts\python.exe" (
    set "PYTHON_EXE=venv312\Scripts\python.exe"
)

echo Dang su dung Python: %PYTHON_EXE%

REM Kiem tra file .env
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Tao file .env tu .env.example...
        copy .env.example .env >nul
    )
)

echo.
echo [1/1] Khoi dong BeeNavi Unified Server (FastAPI :8000)...
start "BeeNavi AI Server" cmd /k "cd /d "%~dp0" && "%PYTHON_EXE%" run.py"

echo.
echo ======================================================
echo  He thong da duoc khoi dong thanh cong!
echo    - BeeNavi Web UI  : http://localhost:8000
echo    - API Docs        : http://localhost:8000/docs
echo ======================================================
echo.
pause
