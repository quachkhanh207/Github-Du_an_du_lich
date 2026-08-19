# 🐝 BeeNavi AI — Trợ Lý Du Lịch Thông Minh Toàn Diện

> **BeeNavi AI** là nền tảng Trợ lý Du lịch thông minh thế hệ mới dành riêng cho du lịch Việt Nam. Hệ thống kết hợp giữa **Mô hình ngôn ngữ lớn (LLM chạy Local)**, **Trợ lý thoại 2 chiều (STT + TTS)**, **Công cụ tìm kiếm địa điểm RAG trên 17.147 POIs**, **Hệ thống gợi ý hành trang thông minh (Smart Checklist)** và **Quản lý nhật ký hành trình cá nhân hóa**.

---

## 📑 Mục Lục
1. [Kiến Trúc Tổng Thể](#-kiến-trúc-tổng-thể)
2. [Cấu Trúc Thư Mục Dự Án](#-cấu-trúc-thư-mục-dự-án)
3. [Các Tính Năng Cốt Lõi](#-các-tính-năng-cốt-lõi)
4. [Yêu Cầu Hệ Thống & Phần Cứng](#-yêu-cầu-hệ-thống--phần-cứng)
5. [Hướng Dẫn Cài Đặt Từng Bước](#-hướng-dẫn-cài-đặt-từng-bước)
6. [Hướng Dẫn Khởi Chạy](#-hướng-dẫn-khởi-chạy)
7. [Tài Liệu API Endpoints](#-tài-liệu-api-endpoints)
8. [Bộ Công Cụ Phát Triển & Quản Trị (Scripts)](#-bộ-công-cụ-phát-triển--quản-trị-scripts)

---

## 🏛️ Kiến Trúc Tổng Thể

Hệ thống được thiết kế theo mô hình **FastAPI Unified Server** nguyên khối, tinh gọn, hiệu năng cao và hoạt động hoàn toàn độc lập mà không phụ thuộc vào các dịch vụ bên ngoài phức tạp:

```
                  ┌─────────────────────────────────────────┐
                  │    FRONTEND WEB UI (HTML / CSS / JS)     │
                  │  - Single Page Application (Leaflet Map)│
                  │  - Voice Call 2-way / Chat Drawer / Form│
                  └────────────────────┬────────────────────┘
                                       │ (HTTP REST / WebSocket)
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │      FASTAPI API GATEWAY (:8000)        │
                  │       (api_server/server.py)            │
                  └──────┬─────────────────┬──────────────┬─┘
                         │                 │              │
        ┌────────────────▼───┐  ┌──────────▼────────┐  ┌──▼───────────────────┐
        │   AI CORE ENGINE   │  │  PLANNER & RAG    │  │  DIARY & DB SERVICE  │
        │ - LLM (Qwen3-4B)   │  │ - Rule Engine     │  │ (diary_service.py)   │
        │ - STT (Whisper)    │  │ - RAG Engine (FTS)│  │                      │
        │ - TTS (VieNeu-TTS) │  │ - Weather Service │  │                      │
        └─────────┬──────────┘  └──────────┬────────┘  └──┬───────────────────┘
                  │                        │              │
                  ▼                        ▼              ▼
        ┌───────────────────┐    ┌──────────────────┐  ┌──────────────────────┐
        │   models/ (*.gguf)│    │ travel_knowledge │  │    user_diary.db     │
        │   VieNeu / Whisper│    │     .db (POIs)   │  │ (Users, Trips, Chk)  │
        └───────────────────┘    └──────────────────┘  └──────────────────────┘
```

---

## 📂 Cấu Trúc Thư Mục Dự Án

```
beenavi/
├── 🖥️ api_server/                   # Cổng Gateway Web & API Backend (FastAPI)
│   ├── config.py                   # Cấu hình VRAM, số layer GPU, token limits, system prompt
│   └── server.py                   # REST endpoints, WebSocket Voice Chat, Auth & Static files
│
├── 🧠 ai_engine/                    # Phân hệ Trí tuệ Nhân tạo & Xử lý Giọng nói
│   ├── brain.py                    # Trình điều khiển LLM (Qwen3-4B local qua llama-cpp-python)
│   ├── speech_to_text.py           # Nhận diện giọng nói tiếng Việt (Faster-Whisper)
│   ├── text_to_speech.py           # Tổng hợp giọng nói tự nhiên tiếng Việt (VieNeu-TTS)
│   ├── audio_processor.py          # Xử lý âm thanh (chuyển đổi định dạng, khử im lặng)
│   ├── intent_router.py            # Phân loại ý định người dùng (Hỏi đáp, Tạo tour, Điều chỉnh)
│   ├── orchestrator.py             # Điều phối luồng xử lý Context + Tool Calling + LLM
│   ├── conversation_state.py       # Quản lý trạng thái hội thoại và ngữ cảnh đa lượt
│   ├── context_merger.py           # Ghép nối dữ liệu RAG và lịch sử hội thoại vào Prompt
│   └── tools/                      # Hệ thống công cụ AI Tool Calling
│       ├── base_tool.py            # Base class định nghĩa Tool
│       ├── rag_tool.py             # Tool tìm kiếm POIs thực tế
│       ├── weather_tool.py         # Tool dự báo thời tiết
│       ├── map_tool.py             # Tool định vị & đo khoảng cách
│       ├── budget_tool.py          # Tool tính toán ngân sách chi tiết
│       └── checklist_tool.py       # Tool gợi ý danh sách chuẩn bị
│
├── 🗺️ planner/                      # Phân hệ Thiết kế Lộ trình Du lịch
│   ├── rag_engine.py               # Tìm kiếm địa điểm ngữ nghĩa & không gian (SQLite FTS5)
│   ├── rule_engine.py              # Thuật toán phân bổ ngày, buổi, thời gian & ngân sách
│   └── dataset_checklist.txt       # Bộ quy tắc chuẩn bị đồ theo hình thức chuyến đi
│
├── 🌐 geo_services/                 # Phân hệ Dữ liệu Địa lý & Khí hậu
│   ├── weather_service.py          # Lấy thời tiết thực tế (Open-Meteo API / OpenWeatherMap)
│   └── map_service.py              # Geocoding địa danh & khoảng cách qua OpenStreetMap
│
├── 💾 diary_service.py              # Quản lý CSDL Người dùng, Chuyến đi, Checklist (SQLite thuần)
│
├── 💻 frontend/                     # Giao diện người dùng Web SPA
│   ├── index.html                  # Giao diện chính (Home, Khám phá, Tạo lộ trình, Nhật ký)
│   └── app.js                      # Logic JavaScript (Bản đồ Leaflet, Gọi thoại, Render lộ trình)
│
├── 📊 data/                         # Cơ sở dữ liệu của hệ thống
│   ├── travel_knowledge.db         # CSDL SQLite FTS5 chứa 17.147 POIs toàn quốc
│   ├── locations_index.json        # Chỉ mục tra cứu nhanh địa điểm
│   └── user_diary.db               # CSDL tài khoản, lộ trình cá nhân & checklist chuyến đi
│
├── 🤖 models/                       # Thư mục lưu trữ Model AI Offline (git-ignored)
│   ├── Qwen3-4B-Q5_K_M.gguf        # Mô hình LLM chính
│   └── hub/                        # Cache mô hình VieNeu-TTS và Whisper
│
├── 🛠️ scripts/                      # Bộ công cụ hỗ trợ & Quản trị dữ liệu
│   ├── build_travel_db.py          # Xây dựng travel_knowledge.db từ dữ liệu thô
│   ├── inspect_db.py               # Kiểm tra nhanh cấu trúc & số lượng bản ghi CSDL
│   ├── test_unified_system.py      # Kiểm thử toàn diện hệ sinh thái Backend
│   └── ingest_dataset.py           # Tiền xử lý dữ liệu OpenStreetMap
│
├── .env.example                    # File mẫu cấu hình biến môi trường
├── .gitignore                      # Cấu hình loại trừ file nhị phân & dữ liệu lớn
├── requirements.txt                # Danh sách thư viện Python cần thiết
├── run.py                          # Script Python khởi chạy FastAPI Server
├── run_all.bat                     # File Batch khởi chạy nhanh trên Windows
└── run_gpu.bat                     # File Batch khởi chạy tối ưu với GPU NVIDIA CUDA
```

---

## ✨ Các Tính Năng Cốt Lõi

### 1. 🤖 Lập Lịch Trình Thông Minh (AI Travel Planner)
- Khởi tạo lịch trình chi tiết từ 1 đến 14 ngày theo điểm xuất phát, điểm đến, ngân sách, phương tiện và phong cách du lịch.
- Tự động trừ chi phí di chuyển chính (vé máy bay, xe khách) để phân bổ hợp lý vào tiền phòng và ăn uống.
- Tự động chia slot hoạt động theo từng buổi (Sáng, Trưa, Chiều, Tối) và ước tính chi phí cho từng điểm dừng chân.

### 2. 🎙️ Trợ Lý Thoại 2 Chiều (Real-time Voice AI)
- Giao tiếp thoại trực tiếp hai chiều không cần gõ phím.
- Nhận diện giọng nói tiếng Việt chuẩn xác bằng mô hình **Faster-Whisper**.
- Phản hồi bằng giọng đọc tiếng Việt truyền cảm, tự nhiên bằng mô hình **VieNeu-TTS**.

### 3. 🔍 RAG Engine Địa Điểm Thực Tế (17.147 POIs)
- CSDL địa phương hóa lưu trữ 17.147 danh lam thắng cảnh, khách sạn, nhà hàng, quán cà phê và điểm check-in khắp 63 tỉnh thành Việt Nam.
- Tìm kiếm toàn văn (FTS5) siêu tốc với thời gian phản hồi < 0.01s.

### 4. 🌤️ Dự Báo Thời Tiết Điểm Đến Thực Tế (Live Weather)
- Tự động lấy dữ liệu nhiệt độ, độ ẩm và trạng thái thời tiết thời gian thực theo điểm đến thông qua **Open-Meteo** (không cần API key) và **OpenWeatherMap**.
- Phân tích điều kiện thời tiết để đưa ra cảnh báo và tinh chỉnh hành trang phù hợp (tránh mưa, chuẩn bị đồ ấm khi lên vùng cao).

### 5. 🎒 Checklist Hành Trang Thông Minh (Smart Checklist)
- Tự động sinh danh sách đồ dùng theo điều kiện thời tiết (Nắng, Lạnh, Mưa) và phương tiện di chuyển (Máy bay, Xe máy phượt, Ô tô).
- Hỗ trợ thêm món đồ tùy chỉnh, đánh dấu hoàn thành, tính thanh tiến độ `% đã chuẩn bị` và lưu trữ trực tiếp vào CSDL của chuyến đi.

### 6. 🗺️ Bản Đồ Lộ Trình Tương Tác (Interactive Map)
- Tích hợp bản đồ vệ tinh / đường phố **Leaflet** trực quan.
- Tự động định vị các điểm đến trong ngày, vẽ đường nối lộ trình di chuyển và tính khoảng cách giữa các trạm.

### 7. 📖 Nhật Ký Chuyến Đi & Tài Khoản (User Travel Journal)
- Đăng ký / Đăng nhập tài khoản, lưu trữ hồ sơ sở thích cá nhân.
- Lưu lại toàn bộ lịch sử các tour đã tạo hoặc clone từ cộng đồng vào CSDL SQLite.

---

## 💻 Yêu Cầu Hệ Thống & Phần Cứng

| Thành phần | Khuyến nghị GPU (Tối ưu) | Chế độ CPU Only (Tối thiểu) |
|---|---|---|
| **Hệ điều hành** | Windows 10/11 64-bit hoặc Linux | Windows 10/11 64-bit hoặc Linux |
| **Python** | Python 3.10 – 3.12 (Khuyên dùng **3.12**) | Python 3.10 – 3.12 |
| **CPU** | Intel Core i5 / AMD Ryzen 5 trở lên | Intel Core i5 / AMD Ryzen 5 (4 cores+) |
| **RAM** | 16 GB RAM | 8 GB – 16 GB RAM |
| **GPU** | NVIDIA GTX 1660 Ti / RTX 3060 trở lên (6GB+ VRAM) | Không bắt buộc |
| **CUDA** | CUDA 12.1 – 12.8 | Không cần |
| **Phần mềm phụ** | FFmpeg (xử lý audio) | FFmpeg |

---

## 🛠️ Hướng Dẫn Cài Đặt Từng Bước

### Bước 1: Clone Repository
```powershell
git clone <URL_REPO_CUA_BAN>
cd beenavi
```

### Bước 2: Tạo Môi Trường Ảo Python
```powershell
python -m venv venv312
.\venv312\Scripts\activate
```

### Bước 3: Cài Đặt PyTorch & Llama-cpp (Hỗ trợ GPU CUDA)
- **Nếu dùng GPU NVIDIA (CUDA 12.x):**
```powershell
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/wheels/cxx11/cu122
```
- **Nếu chỉ dùng CPU:**
```powershell
pip install torch
pip install llama-cpp-python
```

### Bước 4: Cài Đặt Toàn Bộ Thư Viện Cần Thiết
```powershell
pip install -r requirements.txt
```

### Bước 5: Cấu Hình File Môi Trường
Sao chép file `.env.example` thành `.env`:
```powershell
copy .env.example .env
```
*(File `.env` mặc định đã được cấu hình sẵn các giá trị tối ưu).*

### Bước 6: Tải Mô Hình AI vào Thư Mục `models/`
1. Tải mô hình **`Qwen3-4B-Q5_K_M.gguf`** (khoảng ~2.88 GB).
2. Đặt file vào đường dẫn: `beenavi/models/Qwen3-4B-Q5_K_M.gguf`.

---

## 🚀 Hướng Dẫn Khởi Chạy

### Cách 1: Khởi Chạy Tự Động 1-Click (Windows)
Double-click vào file:
```
run_all.bat
```

### Cách 2: Khởi Chạy Tối Ưu GPU CUDA (Windows)
Double-click vào file:
```
run_gpu.bat
```

### Cách 3: Khởi Chạy Bằng Command Line
```powershell
python run.py
```

Sau khi khởi chạy thành công:
- **Giao diện Web Ứng Dụng:** [http://localhost:8000](http://localhost:8000)
- **Tài liệu API Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📡 Tài Liệu API Endpoints

### 1. Trợ Lý AI & Hội Thoại
- `POST /chat`: Gửi tin nhắn văn bản, sinh lịch trình hoặc giải đáp thắc mắc.
- `POST /voice-chat`: Tải file ghi âm `.webm/.wav`, thực hiện STT → LLM → TTS trả lời kèm file âm thanh.
- `WS /ws/voice-chat`: Kênh WebSocket giao tiếp thời gian thực cho cuộc gọi thoại.

### 2. Dịch Vụ Địa Lý & Khí Hậu
- `GET /api/weather?city={cityName}`: Lấy nhiệt độ, độ ẩm và mô tả thời tiết trực tiếp của điểm đến.
- `GET /api/geocode?q={locationName}`: Tra cứu tọa độ vĩ độ/kinh độ của địa danh.

### 3. Người Dùng & Xác Thực
- `POST /api/users/register`: Đăng ký tài khoản mới.
- `POST /api/users/login`: Đăng nhập hệ thống và nhận Bearer Token.
- `GET /api/users/profile`: Lấy thông tin hồ sơ và sở thích cá nhân.
- `PUT /api/users/profile`: Cập nhật sở thích, ngân sách, phong cách du lịch.

### 4. Quản Lý Chuyến Đi & Checklist
- `GET /api/trips`: Danh sách toàn bộ các chuyến đi đã lưu trong nhật ký.
- `POST /api/trips`: Lưu chuyến đi mới kèm toàn bộ lịch trình chi tiết.
- `GET /api/trips/{trip_id}/checklist`: Lấy danh sách checklist đồ dùng của chuyến đi.
- `POST /api/trips/{trip_id}/checklist`: Thêm món đồ mới vào checklist chuyến đi.
- `POST /api/trips/{trip_id}/checklist/bulk`: Khởi tạo / lưu danh sách checklist hàng loạt.
- `PUT /api/checklist/{item_id}`: Cập nhật trạng thái đã chuẩn bị (`is_completed`).
- `DELETE /api/checklist/{item_id}`: Xóa món đồ khỏi checklist.
- `GET /api/trips/statistics`: Thống kê tổng quan (số chuyến đi, số địa danh đã khám phá).

---

## 🛠️ Bộ Công Cụ Phát Triển & Quản Trị (Scripts)

Các công cụ quản trị dữ liệu được đặt trong thư mục `scripts/`:

```powershell
# 1. Kiểm tra sức khỏe toàn bộ hệ sinh thái CSDL & Backend
python scripts/test_unified_system.py

# 2. Xem chi tiết cấu trúc, dung lượng và số lượng bản ghi của các CSDL
python scripts/inspect_db.py

# 3. Biên dịch và lập chỉ mục CSDL tri thức du lịch 17.147 POIs
python scripts/build_travel_db.py
```

---

## 📄 Bản Quyền & Giấy Phép

Dự án được xây dựng và phát triển phục vụ mục đích học tập, nghiên cứu và ứng dụng công nghệ AI vào du lịch Việt Nam.
