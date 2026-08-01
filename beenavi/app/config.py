import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Nạp file .env ở thư mục gốc dự án (nếu có) trước khi đọc biến môi trường
load_dotenv(BASE_DIR / ".env")

MODEL_DIR = BASE_DIR / "models"
TEMP_DIR = BASE_DIR / "tmp"

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    str(MODEL_DIR / "Qwen3-4B-Q5_K_M.gguf")
)

# --- Speech-to-Text (Whisper) ---
# Mặc định chạy STT trên CPU để dành toàn bộ VRAM cho LLM.
# Với GPU 6GB, chỉ bật STT_DEVICE=cuda nếu bạn giảm LLM_CONTEXT
# hoặc dùng model Whisper nhỏ hơn — nếu không rất dễ tràn VRAM (OOM).
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "vi")
STT_DEVICE = os.getenv("STT_DEVICE", "cpu")

# --- LLM (Qwen3-4B qua llama-cpp-python) ---
# N_GPU_LAYERS = -1  -> offload toàn bộ layer lên GPU (khuyến nghị cho
#                       model 4B Q5_K_M, chiếm ~3.2-3.6GB VRAM, vừa với
#                       GPU 6GB kể cả khi có KV-cache của ngữ cảnh).
# Nếu gặp lỗi "out of memory" khi load model, hạ dần con số này
# (ví dụ 20, 15, 10...) qua biến môi trường N_GPU_LAYERS trong .env
# để chỉ offload một phần layer lên GPU, phần còn lại chạy trên CPU.
N_GPU_LAYERS = int(os.getenv("N_GPU_LAYERS", "-1"))

# --- Flash Attention ---
# Mặc định TẮT (False) vì GTX 1660 Ti (Turing, compute 7.5) không có Tensor Cores
# đủ để chạy Flash Attention → gây lỗi 0xC000001D (STATUS_ILLEGAL_INSTRUCTION).
# Chỉ bật (FLASH_ATTN=1 trong .env) nếu dùng GPU Ampere (RTX 30xx) trở lên.
FLASH_ATTN = os.getenv("FLASH_ATTN", "0") == "1"

LLM_CONTEXT = int(os.getenv("LLM_CONTEXT", "4096"))
# LLM_BATCH: Qwen3 có vocab 151,936 tokens → llama-cpp-python cấp phát
# n_batch × vocab × 4 bytes cho logits buffer. Với n_batch=512 → 297 MiB → OOM.
# Giảm xuống 128 → chỉ tốn ~74 MiB, tốc độ decode vẫn đủ nhanh.
LLM_BATCH = int(os.getenv("LLM_BATCH", "128"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "400"))

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

for path in [MODEL_DIR, TEMP_DIR]:
    path.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """
Bạn là trợ lý du lịch Việt Nam.

Yêu cầu:
- Trả lời bằng tiếng Việt tự nhiên, đúng chính tả.
- Hiểu đúng ngữ cảnh, ý định và sắc thái của người dùng.
- Giữ đúng số ngày, ngân sách, số người, độ tuổi,
  phương tiện và sở thích.
- Không tự bịa giá vé, giờ mở cửa, thời tiết hoặc địa chỉ.
- Nếu thiếu dữ kiện, hỏi lại ngắn gọn.
- Trả lời trực tiếp, rõ ràng, không dài dòng.
- Không hiển thị suy luận nội bộ.
"""