# 🐝 BeeNavi AI — Trợ Lý Du Lịch Thông Minh Toàn Diện

**BeeNavi AI** là nền tảng Trợ lý Du lịch thông minh thế hệ mới dành riêng cho du lịch Việt Nam. Hệ thống kết hợp giữa Mô hình ngôn ngữ lớn (LLM chạy Local), Trợ lý thoại 2 chiều (STT + TTS), Công cụ tìm kiếm địa điểm RAG trên 17.147 POIs, Hệ thống gợi ý hành trang thông minh (Smart Checklist) và Quản lý nhật ký hành trình cá nhân hóa.

---

## 🚀 Bản Cập Nhật Mới Nhất (Itinerary Engine v2)

Dự án vừa trải qua một đợt tái cấu trúc lớn (Major Update) để giải quyết các vấn đề về hiệu năng và độ chính xác của hệ thống sinh lịch trình:

- **Thuật toán sinh lịch trình siêu tốc (0.1s)**: Xóa bỏ hoàn toàn việc dùng LLM (thường mất 2-3 phút) để sinh lịch trình. Thay thế bằng K-Means Clustering (Phân cụm địa lý theo ngày) và Haversine Distance trực tiếp bằng Python.
- **Wizard Khởi Tạo 2 Chế Độ**:
  - **Chế độ A (Chuyến đi nhiều ngày)**: Tự động gom cụm các địa điểm theo ngày.
  - **Chế độ B (Khám phá 1 điểm)**: Quét các địa điểm tham quan/ăn uống/giải trí trong bán kính 2km từ 1 điểm neo (Anchor POI) cụ thể.
- **Nâng cấp Bộ máy Tìm kiếm (RAG Engine)**: Khắc phục triệt để lỗi "địa điểm vô danh" bằng thuật toán lọc 3 lớp: `Phrase Match -> AND Match -> OR Match` kết hợp chấm điểm `ORDER BY rank (BM25)`. Hệ thống giờ đây tìm "Lăng Bác" chuẩn xác 100%.
- **Giao diện Timeline Mới**: Timeline hiển thị màu sắc theo khung giờ (Sáng/Trưa/Tối) và tự động tính toán, gợi ý phương tiện di chuyển (Đi bộ / Gọi xe) kèm cự ly giữa các điểm đến.

---

## 🏛️ Kiến Trúc Tổng Thể

Hệ thống được thiết kế theo mô hình **FastAPI Unified Server** nguyên khối, tinh gọn, hiệu năng cao và hoạt động hoàn toàn độc lập mà không phụ thuộc vào các dịch vụ bên ngoài phức tạp:

```text
┌─────────────────────────────────────────┐
│     FRONTEND WEB UI (HTML / CSS / JS)   │
│ - Single Page Application (Leaflet Map) │
│ - Voice Call 2-way / Chat Drawer / Form │
└────────────────────┬────────────────────┘
                     │ (HTTP REST / WebSocket)
                     ▼
┌─────────────────────────────────────────┐
│        FASTAPI API GATEWAY (:8000)      │
│          (api_server/server.py)         │
└──────┬─────────────────┬──────────────┬─┘
       │                 │              │
┌──────▼──────┐   ┌──────▼──────┐   ┌───▼──────────────────┐
│   AI CORE   │   │ PLANNER &   │   │  DIARY & DB SERVICE  │
│   ENGINE    │   │ RAG ENGINE  │   │  (diary_service.py)  │
│- LLM (Qwen3)│   │- Rule Engine│   │- PostgreSQL/Supabase │
│- STT Whisper│   │- RAG (FTS)  │   │- Users, Trips, Check │
│- TTS VieNeu │   │- Weather API│   │                      │
└──────┬──────┘   └──────┬──────┘   └───┬──────────────────┘
       │                 │              │
       ▼                 ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐
│  models/     │  │ travel_      │  │ supabase_schema.sql  │
│  (*.gguf)    │  │ knowledge.db │  │ Khởi tạo CSDL Đám mây│
└──────────────┘  └──────────────┘  └──────────────────────┘
```

---

## 📂 Cấu Trúc Thư Mục Dự Án

```text
beenavi/
├── 🖥️ api_server/          # Cổng Gateway Web & API Backend (FastAPI)
│   ├── config.py           # Cấu hình VRAM, LLM_BATCH, token limits, system prompt
│   └── server.py           # REST endpoints, WebSocket Voice Chat, Auth & Static
├── 🧠 ai_engine/           # Phân hệ Trí tuệ Nhân tạo & Xử lý Giọng nói
│   ├── brain.py            # Trình điều khiển LLM (Qwen3-4B local qua llama-cpp-python)
│   ├── speech_to_text.py   # Nhận diện giọng nói (Faster-Whisper)
│   ├── text_to_speech.py   # Tổng hợp giọng nói tự nhiên (VieNeu-TTS)
│   ├── audio_processor.py  # Xử lý âm thanh (chuyển đổi định dạng, khử im lặng VAD)
│   ├── intent_router.py    # Phân loại ý định người dùng (Hỏi đáp, Lên lịch)
│   ├── orchestrator.py     # Điều phối luồng xử lý Context + Tool Calling + LLM
│   └── context_merger.py   # Ghép nối dữ liệu RAG và lịch sử hội thoại vào Prompt
├── 🗺️ planner/             # Phân hệ Thiết kế Lộ trình Du lịch
│   ├── rag_engine.py       # Tìm kiếm địa điểm ngữ nghĩa & không gian (FTS5)
│   └── rule_engine.py      # Thuật toán phân bổ ngày, buổi, thời gian & ngân sách
├── 🌐 geo_services/        # Phân hệ Dữ liệu Địa lý & Khí hậu
│   └── weather_service.py  # Lấy thời tiết thực tế (Open-Meteo API / OpenWeatherMap)
├── 💾 diary_service.py     # Quản lý Data Access Layer tương tác với Supabase DB
├── 💻 frontend/            # Giao diện người dùng Web SPA
│   ├── index.html          # Trang chủ tích hợp AI Floating Widget
│   ├── admin_dashboard.html# Giao diện Xương sống - Quản lý lộ trình
│   └── backbone_app.js     # Logic điều khiển giao diện (Timeline, Leaflet Map)
├── 📊 data/                # Cơ sở dữ liệu của hệ thống
│   └── supabase_schema.sql # Cấu trúc CSDL chuẩn của dự án để nạp lên Supabase
├── 🤖 models/              # Nơi chứa các Mô hình AI Offline
│   └── Qwen3-4B-Q5_K_M.gguf# LLM Chính được load qua llama-cpp
├── 🛠️ scripts/             # Bộ công cụ hỗ trợ & Quản trị dữ liệu
├── .env.example            # File mẫu cấu hình biến môi trường
├── requirements.txt        # Danh sách thư viện Python cần thiết (cơ bản)
├── requirements_ai.txt     # Danh sách thư viện AI (torch, llama-cpp-python, whisper)
├── run_all.bat             # File Batch khởi chạy nhanh trên Windows
└── run_gpu.bat             # File Batch khởi chạy tối ưu với GPU NVIDIA CUDA
```

---

## ✨ Các Tính Năng Cốt Lõi

### 1. 🤖 Lập Lịch Trình Thông Minh (AI Travel Planner)
- Khởi tạo lịch trình chi tiết từ 1 đến 14 ngày theo điểm xuất phát, điểm đến, ngân sách, phương tiện và phong cách du lịch.
- Tự động trừ chi phí di chuyển chính (vé máy bay, xe khách) để phân bổ hợp lý vào tiền phòng và ăn uống.
- Tự động chia slot hoạt động theo từng buổi (Sáng, Trưa, Chiều, Tối) và ước tính chi phí cho từng điểm dừng chân.

### 2. 🎙️ Trợ Lý Thoại 2 Chiều (Real-time Voice AI)
- Giao tiếp thoại trực tiếp hai chiều **không độ trễ** qua WebSocket (`/ws`).
- Nhận diện giọng nói tiếng Việt chuẩn xác bằng mô hình `Faster-Whisper` kết hợp VAD (Voice Activity Detection).
- Phản hồi bằng giọng đọc tiếng Việt truyền cảm bằng mô hình `VieNeu-TTS`, stream audio trực tiếp về Frontend.

### 3. 🔍 RAG Engine Địa Điểm Thực Tế (17.147 POIs)
- CSDL địa phương hóa lưu trữ 17.147 danh lam thắng cảnh, khách sạn, nhà hàng, quán cà phê và điểm check-in khắp 63 tỉnh thành Việt Nam.
- Tìm kiếm toàn văn (FTS5) siêu tốc với thời gian phản hồi < 0.01s.

### 4. 🌤️ Dự Báo Thời Tiết Điểm Đến (Live Weather)
- Lấy dữ liệu nhiệt độ, độ ẩm và trạng thái thời tiết thời gian thực thông qua API Open-Meteo.
- Đưa cảnh báo thời tiết vào prompt hệ thống để AI sinh câu trả lời tinh tế hơn.

### 5. 🎒 Checklist Hành Trang Thông Minh (Smart Checklist)
- Tự động sinh danh sách đồ dùng theo điều kiện thời tiết (Nắng, Lạnh, Mưa) và phương tiện di chuyển.
- Theo dõi tiến độ % chuẩn bị và lưu trữ trên Cloud qua Supabase.

### 6. 🗺️ Bản Đồ Lộ Trình Tương Tác (Interactive Map)
- Tích hợp bản đồ vệ tinh / đường phố Leaflet trực quan.
- Tự động định vị các điểm đến trong ngày, vẽ đường nối lộ trình di chuyển.

### 7. 📖 Nhật Ký Chuyến Đi & Tài Khoản
- Lưu lại toàn bộ lịch sử các tour đã tạo vào CSDL Cloud, cho phép chia sẻ hoặc sao chép (clone) dễ dàng.

---

## 💻 Yêu Cầu Hệ Thống & Phần Cứng

| Thành phần | Khuyến nghị GPU (Tối ưu nhất) | Chế độ CPU Only (Tối thiểu) |
| :--- | :--- | :--- |
| **Hệ điều hành** | Windows 10/11 64-bit hoặc Linux | Windows 10/11 64-bit hoặc Linux |
| **Python** | Python 3.10 – 3.12 (Khuyên dùng 3.12) | Python 3.10 – 3.12 |
| **CPU** | Intel Core i5 / AMD Ryzen 5 trở lên | Intel Core i5 / AMD Ryzen 5 (4 cores+) |
| **RAM** | 16 GB RAM | 8 GB – 16 GB RAM |
| **GPU** | NVIDIA GTX 1660 Ti / RTX 3060 trở lên (6GB+ VRAM) | Không bắt buộc |
| **CUDA** | CUDA 12.1 – 12.8 | Không cần |
| **Phần mềm phụ**| FFmpeg (xử lý audio format) | FFmpeg |

---

## 🛠️ Hướng Dẫn Cài Đặt Từng Bước

### Bước 1: Clone Repository
```bash
git clone <URL_REPO_CUA_BAN>
cd beenavi
```

### Bước 2: Tạo Môi Trường Ảo Python
```bash
python -m venv venv312
.\venv312\Scripts\activate  # Lệnh kích hoạt trên Windows
```

### Bước 3: Cài Đặt PyTorch & Llama-cpp (Hỗ trợ GPU CUDA)
**Nếu dùng GPU NVIDIA (CUDA 12.x):**
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
set CMAKE_ARGS="-DGGML_CUDA=on"
set FORCE_CMAKE=1
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/wheels/cxx11/cu122 --force-reinstall --no-cache-dir
```
**Nếu chỉ dùng CPU:**
```bash
pip install torch
pip install llama-cpp-python
```

### Bước 4: Cài Đặt Toàn Bộ Thư Viện Cần Thiết
```bash
pip install -r requirements.txt
pip install -r requirements_ai.txt
```

### Bước 5: Cấu Hình File Môi Trường
Sao chép file `.env.example` thành `.env`:
```bash
copy .env.example .env
```
Mở `.env` và thiết lập (Đặc biệt lưu ý `SUPABASE_URL` và `SUPABASE_KEY`):
```ini
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="eyJhbG..."
N_GPU_LAYERS=-1       # Tùy chỉnh VRAM offload
LLM_BATCH=128         # Tối ưu RAM cho Qwen3 Vocab
STT_DEVICE=cuda       # Đổi thành cpu nếu VRAM quá hẻo
FLASH_ATTN=0          # Bật thành 1 nếu dùng Card RTX 30 Series trở lên
```

### Bước 6: Khởi Tạo Cơ Sở Dữ Liệu
Vào trang quản trị [Supabase](https://supabase.com/), tạo project mới, mở SQL Editor và chạy nội dung file `data/supabase_schema.sql`.

### Bước 7: Tải Mô Hình AI vào Thư Mục `models/`
- Tải mô hình `Qwen3-4B-Q5_K_M.gguf` (khoảng ~2.88 GB).
- Đặt file vào đường dẫn: `beenavi/models/Qwen3-4B-Q5_K_M.gguf`.

---

## 🚀 Hướng Dẫn Khởi Chạy

**Cách 1: Khởi Chạy Tự Động 1-Click (Windows)**
Double-click vào file `run_all.bat`.

**Cách 2: Khởi Chạy Tối Ưu GPU CUDA (Windows)**
Double-click vào file `run_gpu.bat`.

**Cách 3: Khởi Chạy Bằng Command Line**
```bash
python -m api_server.server
```

Sau khi khởi chạy thành công, truy cập:
- Giao diện Web Trang Chủ & Chatbot: [http://localhost:8000](http://localhost:8000)
- Quản trị Lịch trình: [http://localhost:8000/login.html](http://localhost:8000/login.html)

---

## 📡 Tài Liệu API Endpoints Nổi Bật

### 1. Trợ Lý AI & Hội Thoại
- `WS /ws`: Kênh WebSocket giao tiếp thời gian thực cho cuộc gọi thoại đa phương thức.
- `POST /chat`: Gửi tin nhắn văn bản, sinh lịch trình hoặc giải đáp thắc mắc.

### 2. Dịch Vụ Địa Lý & Khí Hậu
- `GET /api/weather?destination={cityName}`: Lấy nhiệt độ, độ ẩm và mô tả thời tiết trực tiếp của điểm đến.

### 3. Người Dùng & Xác Thực
- `POST /api/users/register`: Đăng ký tài khoản mới.
- `POST /api/users/login`: Đăng nhập hệ thống và nhận Bearer Token.

### 4. Quản Lý Chuyến Đi & Checklist
- `GET /api/trips`: Danh sách toàn bộ các chuyến đi đã lưu trong nhật ký.
- `POST /api/trips`: Lưu chuyến đi mới kèm toàn bộ lịch trình chi tiết.
- `GET /api/trips/statistics`: Thống kê tổng quan.

---

## 📄 Bản Quyền & Giấy Phép
Dự án được xây dựng và phát triển phục vụ mục đích học tập, nghiên cứu và ứng dụng công nghệ AI vào hệ sinh thái du lịch Việt Nam.
