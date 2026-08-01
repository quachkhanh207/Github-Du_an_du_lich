@echo off
:: Them CUDA 12.8 vao PATH de ggml-cuda.dll tim duoc cublas64_12.dll
set "PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin;%PATH%"

echo [INFO] CUDA 12.8 added to PATH
echo [INFO] Starting Beenavi backend with GPU (venv312)...

cd /d "%~dp0beenavi"
call ..\venv312\Scripts\activate.bat
python run.py
