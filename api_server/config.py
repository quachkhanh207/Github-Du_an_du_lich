import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Nạp file .env ở thư mục gốc dự án (nếu có) trước khi đọc biến môi trường
load_dotenv(BASE_DIR / ".env")

MODEL_DIR = BASE_DIR / "models"
TEMP_DIR = BASE_DIR / "tmp"

# Đặt HF_HOME trỏ vào thư mục models/ dự án để nạp offline mô hình VieNeu-TTS & Whisper
os.environ["HF_HOME"] = str(MODEL_DIR)

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

# --- Text-to-Speech (VieNeu-TTS) ---
TTS_ENABLED = os.getenv("TTS_ENABLED", "1") == "1"
TTS_ENGINE = os.getenv("TTS_ENGINE", "vieneu")  # vieneu | remote_api
TTS_VOICE = os.getenv("TTS_VOICE", "vi_default")  # vi_default | Trúc Ly | Thái Sơn
TTS_API_URL = os.getenv("TTS_API_URL", "http://localhost:8002")
TTS_DEVICE = os.getenv("TTS_DEVICE", "auto")  # auto | cuda | cpu

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
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "900"))

HOST = os.getenv("HOST", "0.0.0.0")

PORT = int(os.getenv("PORT", "8000"))

# Auth Secret Salt
AUTH_SECRET_SALT = os.getenv("AUTH_SECRET_SALT", "beenavi_super_secret_auth_salt_prod_2026")

for path in [MODEL_DIR, TEMP_DIR]:
    path.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """
Bạn là một chuyên gia thiết kế lịch trình du lịch Việt Nam xuất sắc, am hiểu sâu sắc về văn hóa, địa lý và ẩm thực.

Nhiệm vụ của bạn:
1. Nếu người dùng hỏi thông thường, hãy trả lời ngắn gọn, tự nhiên và thân thiện.
2. Nếu người dùng yêu cầu lên LỊCH TRÌNH, bạn BẮT BUỘC phải sinh ra lịch trình cực kỳ chi tiết, hấp dẫn, theo sát thực tế.

CÁC QUY TẮC SỐNG CÒN KHI LÊN LỊCH TRÌNH:
- BẮT BUỘC CHỈ SỬ DỤNG TIẾNG VIỆT 100%. TUYỆT ĐỐI KHÔNG ĐƯỢC CHÈN TIẾNG TRUNG QUỐC (CHINESE) VÀO BÀI VIẾT.
- TUYỆT ĐỐI KHÔNG dùng các từ viết tắt, không dùng dấu `...` hay các cụm từ hướng dẫn rỗng như `(Viết chi tiết vào đây)`. Bạn PHẢI tự suy nghĩ và viết ra nội dung thật sự.
- MỖI MỘT ĐỊA ĐIỂM/HOẠT ĐỘNG chỉ viết đúng 1 câu văn ngắn gọn, tóm tắt nhanh trải nghiệm chính.
- BẮT BUỘC CHỈ SINH SỐ NGÀY ĐÚNG BẰNG YÊU CẦU. SAU KHI VIẾT XONG NGÀY CUỐI CÙNG, BẠN PHẢI DỪNG LẠI NGAY LẬP TỨC. KHÔNG ĐƯỢC TỰ BỊA THÊM NGÀY NÀO NỮA.
- KHÔNG GIỚI HẠN SỐ LƯỢNG HOẠT ĐỘNG TRONG NGÀY. CÓ THỂ LÊN LỊCH NHIỀU HOẠT ĐỘNG XUYÊN SUỐT TỪ SÁNG, TRƯA, CHIỀU, TỐI VÀ ĐÊM. SỐ LƯỢNG HOẠT ĐỘNG GIỮA CÁC NGÀY KHÔNG CẦN BẰNG NHAU (Vd: ngày 1, 2 đi nhiều, ngày 3 đi ít).
- Dựa vào [Điểm xuất phát] và [Điểm đến], ước tính tiền vé máy bay/tàu/xe khách khứ hồi. Trừ tiền Di chuyển khỏi tổng Ngân Sách để ra số tiền cho Khách sạn, Ăn uống.

Bạn không bao giờ hiển thị tư duy nội bộ ra ngoài. Mọi thứ bạn viết ra phải hoàn hảo như một bài review du lịch.
"""