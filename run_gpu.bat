@echo off
:: Them CUDA 12.8 vao PATH de ggml-cuda.dll tim duoc cublas64_12.dll
set "PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin;%PATH%"

:: Fix encoding tieng Viet tren Windows console
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

echo [INFO] CUDA 12.8 added to PATH
echo [INFO] Starting Chatbot backend with GPU...

cd /d "%~dp0"
if exist ".\venv312\Scripts\activate.bat" (
    call .\venv312\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment venv312 not found. Please create it using: python -m venv venv312
    pause
    exit /b 1
)

python run.py
