@echo off
:: Them CUDA 12.8 vao PATH de ggml-cuda.dll tim duoc cublas64_12.dll
set "PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin;%PATH%"

echo [INFO] CUDA 12.8 added to PATH
echo [INFO] Starting Chatbot backend with GPU...

cd /d "%~dp0"
if exist ".\venv312\Scripts\activate.bat" (
    call .\venv312\Scripts\activate.bat
) else if exist ".\venv\Scripts\activate.bat" (
    call .\venv\Scripts\activate.bat
)

python run.py
