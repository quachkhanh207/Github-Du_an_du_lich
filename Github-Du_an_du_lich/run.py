import sys
import os

# Fix encoding tren Windows console (tranh loi 'charmap' khi print tieng Viet)
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from pathlib import Path
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from chatbot.config import HOST, PORT


if __name__ == "__main__":
    uvicorn.run(
        "chatbot.server:app",
        host=HOST,
        port=PORT,
        reload=False,
        ws="auto"
    )