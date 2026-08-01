# 🤖 Voice & Text Travel Chatbot (Backend & Frontend)

Hệ thống Chatbot Trợ lý Du lịch thông minh tích hợp nhận dạng giọng nói (Speech-to-Text) và Mô hình ngôn ngữ lớn (LLM Qwen3) chạy Local tối ưu hóa cho GPU/CPU.

---

## 📂 Cấu trúc thư mục dự án

```text
├── chatbot/                # 🧠 BACKEND CHATBOT (Python / FastAPI / LLM / STT)
│   ├── __init__.py
│   ├── audio.py            # Xử lý & chuyển đổi file âm thanh (FFmpeg)
│   ├── brain.py            # Khởi tạo & truy vấn mô hình LLM (Qwen3 qua llama-cpp-python)
│   ├── config.py           # Cấu hình tham số mô hình, VRAM, GPU & hệ thống
│   ├── server.py           # REST API & WebSocket Server (FastAPI)
│   └── stt.py              # Nhận dạng giọng nói tiếng Việt (Faster-Whisper)
│
├── frontend/               # 💻 FRONTEND WEB UI (Giao diện người dùng)
│   ├── app.js              # Xử lý WebSocket, ghi âm micro & hiệu ứng giao diện
│   ├── index.html          # Trang web chính Chatbot du lịch
│   ├── sam_son_hero.png    # Hình ảnh banner giao diện
│   └── style.css           # Cấu hình giao diện CSS
│
├── models/                 # 📦 Thư mục chứa trọng số mô hình AI (GGUF Model)
│   └── .gitkeep
│
├── .env.example            # File mẫu cấu hình biến môi trường
├── .gitignore              # Cấu hình loại bỏ file lớn, venvs & secrets khỏi Git
├── requirements.txt        # Danh sách các thư viện Python cần thiết
├── run.py                  # Script Python khởi chạy ứng dụng
└── run_gpu.bat             # Batch script khởi chạy dự án với GPU (NVIDIA CUDA)
```

---

## ⚠️ Lưu ý về các file không đẩy lên GitHub

Các thư mục và file sau đây **không được đẩy lên GitHub** do giới hạn dung lượng của GitHub (tối đa 100MB/file) hoặc do là file môi trường cục bộ:

1. **Trọng số mô hình LLM (`models/Qwen3-4B-Q5_K_M.gguf`)**: Dung lượng ~2.88 GB.
2. **Môi trường ảo Python (`venv/`, `venv312/`)**.
3. **File cấu hình bảo mật cục bộ (`.env`)**.
4. **Các file log & âm thanh tạm (`build_log.txt`, `tmp/`)**.

---

## 🛠️ Hướng dẫn Cài đặt & Khởi chạy Chi tiết

### 1. Yêu cầu hệ thống
- **Hệ điều hành**: Windows 10/11 (khuyên dùng) hoặc Linux / macOS.
- **Python**: Phiên bản 3.12 trở lên.
- **Phần cứng**:
  - **GPU (Khuyên dùng)**: NVIDIA GPU VRAM 6GB+ (ví dụ GTX 1660 Ti, RTX 3060, v.v.) + CUDA Toolkit (v11.x hoặc v12.x).
  - **CPU**: RAM 8GB+ (nếu không dùng GPU).
- **FFmpeg**: Cần thiết để xử lý âm thanh ghi âm từ micro.

---

### 2. Cài đặt Môi trường Python

1. **Mở Terminal/PowerShell tại thư mục gốc dự án** và tạo môi trường ảo Python:
   ```bash
   python -m venv venv312
   ```

2. **Kích hoạt môi trường ảo**:
   - Trên Windows (PowerShell):
     ```powershell
     .\venv312\Scripts\activate
     ```
   - Trên Linux / macOS:
     ```bash
     source venv312/bin/activate
     ```

3. **Cài đặt các thư viện cần thiết**:
   ```bash
   pip install -r requirements.txt
   ```

---

### 3. Tải & Đặt File Model AI (LLM Qwen3)

1. **Tải File Model GGUF**:
   - Tải mô hình `Qwen3-4B-Q5_K_M.gguf` (dung lượng ~2.88GB) từ HuggingFace hoặc kho lưu trữ của nhóm.
2. **Đặt file Model vào thư mục `models/`**:
   - Đường dẫn chính xác sau khi tải:
     ```text
     models/Qwen3-4B-Q5_K_M.gguf
     ```

*Lưu ý: Bạn cũng có thể dùng mô hình GGUF khác và đổi tên đường dẫn trong file `.env` qua biến `MODEL_PATH`.*

---

### 4. Cài đặt FFmpeg (Dành cho xử lý Giọng nói Voice STT)

- Tải **FFmpeg** từ trang chủ: [ffmpeg.org](https://ffmpeg.org/download.html)
- Giải nén và thêm thư mục `bin` của FFmpeg vào **System PATH** của Windows để lệnh `ffmpeg` có thể gọi được từ dòng lệnh.

---

### 5. Cấu hình Biến môi trường (`.env`)

1. Tạo file `.env` từ file mẫu `.env.example`:
   ```bash
   cp .env.example .env
   ```
2. Chỉnh sửa các tham số trong file `.env` (nếu cần):
   - `N_GPU_LAYERS=-1`: Offload toàn bộ các tầng LLM lên GPU (đặt `0` nếu chỉ chạy CPU).
   - `STT_DEVICE=cpu`: Chạy mô hình Whisper STT trên CPU (hoặc `cuda` nếu dư VRAM).
   - `HOST=0.0.0.0` & `PORT=8000`.

---

### 6. Khởi chạy Ứng dụng

#### Cách 1: Chạy bằng GPU (NVIDIA CUDA) - Khuyên dùng
Double click vào file `run_gpu.bat` hoặc chạy lệnh trong Terminal:
```powershell
.\run_gpu.bat
```

#### Cách 2: Chạy trực tiếp qua Python
```bash
python run.py
```

---

### 🌐 Truy cập Giao diện Web (Frontend)

Sau khi server khởi chạy thành công, mở trình duyệt web và truy cập địa chỉ:
👉 **[http://localhost:8000](http://localhost:8000)** (hoặc **[http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)**)

Tại đây bạn có thể chat qua văn bản hoặc bấm nút Micro để trò chuyện trực tiếp bằng giọng nói với Chatbot Du lịch!
