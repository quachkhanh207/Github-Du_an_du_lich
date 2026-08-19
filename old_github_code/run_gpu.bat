@echo off
title BeeNavi AI - GPU Launcher
cd /d "%~dp0"

echo ======================================================
echo           BeeNavi AI - GPU Launcher (CUDA)
echo ======================================================
echo.

REM Cau hinh PATH CUDA neu co
if exist "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin" (
    set "PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin;%PATH%"
) else if exist "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin" (
    set "PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin;%PATH%"
) else if exist "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\bin" (
    set "PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\bin;%PATH%"
)

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
echo [1/1] Khoi dong BeeNavi Unified Server (FastAPI :8000 + GPU)...
"%PYTHON_EXE%" run.py

