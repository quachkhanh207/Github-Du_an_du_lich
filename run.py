import sys
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