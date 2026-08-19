"""
run.py — Khởi động BeeNavi AI Server (FastAPI, cổng 8000)
"""
import os
import sys
from pathlib import Path

# Fix Windows console UTF-8 encoding
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Đảm bảo thư mục gốc beenavi/ nằm trong sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn
from api_server.config import HOST, PORT

if __name__ == "__main__":
    print(f"[BeeNavi AI] Khởi động server tại http://{HOST}:{PORT}")
    uvicorn.run(
        "api_server.server:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info"
    )
