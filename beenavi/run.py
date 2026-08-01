import sys
from pathlib import Path
import uvicorn

# Ensure chatbot directory is in Python path
CHATBOT_DIR = Path(__file__).resolve().parent
if str(CHATBOT_DIR) not in sys.path:
    sys.path.insert(0, str(CHATBOT_DIR))

from app.config import HOST, PORT


if __name__ == "__main__":
    uvicorn.run(
        "app.server:app",
        host=HOST,
        port=PORT,
        reload=False,
        ws="auto"
    )

    # cách chạy ở mạng khác: npx localtunnel --port 8000