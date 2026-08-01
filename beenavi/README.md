# Beenavi Chatbot — Hướng dẫn cài đặt (Windows, GPU 6GB VRAM)

## 0. Cấu trúc thư mục (bắt buộc đúng như sau)

```
fulldulich/
├── run.py
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── server.py
│   ├── brain.py
│   ├── stt.py
│   └── audio.py
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
└── models/                      <- bạn tự tạo, chứa file .gguf
```

> Quan trọng: các file Python import theo dạng `from app.config import ...`,
> nên bắt buộc `config.py`, `server.py`, `brain.py`, `stt.py`, `audio.py`,
> `__init__.py` phải nằm trong thư mục con tên **`app/`**. Tương tự,
> `index.html`, `app.js`, `style.css` phải nằm trong thư mục con tên
> **`frontend/`**. Đây chính là cấu trúc của bộ file mình gửi kèm.

---

## 1. Cài công cụ nền tảng

### 1.1. Visual Studio Build Tools (bắt buộc — máy bạn chưa có)
`llama-cpp-python` không có sẵn wheel build sẵn chính thức cho Windows,
nên bắt buộc phải biên dịch từ mã nguồn trên máy bạn.

1. Tải **Visual Studio Build Tools 2022**:
   https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Khi cài, tick chọn workload **"Desktop development with C++"**.
3. Cài xong, khởi động lại máy (hoặc ít nhất mở lại terminal).

### 1.2. Kiểm tra CUDA Toolkit
Bạn đã có driver NVIDIA (`nvidia-smi` chạy được). Cần thêm **CUDA Toolkit**
(khác với driver) để có `nvcc` dùng cho biên dịch:

```powershell
nvcc --version
```

- Nếu ra version → bỏ qua bước này.
- Nếu báo lỗi "không tìm thấy lệnh" → tải CUDA Toolkit tại
  https://developer.nvidia.com/cuda-downloads (chọn bản ≤ version hiển thị
  trong góc phải `nvidia-smi`, ví dụ driver hỗ trợ CUDA 12.6 thì cài
  Toolkit 12.4 hoặc 12.6 đều được).

### 1.3. ffmpeg (bắt buộc — `app/audio.py` gọi trực tiếp lệnh `ffmpeg`)
1. Tải bản Windows tại https://www.gyan.dev/ffmpeg/builds/ (mục "release essentials")
2. Giải nén, thêm thư mục `bin` vào biến môi trường `PATH`.
3. Kiểm tra: mở terminal mới, gõ `ffmpeg -version`.

---

## 2. Tạo môi trường Python

```powershell
cd C:\Users\Tien\Desktop\fulldulich
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
```

## 3. Cài PyTorch (bản CPU — nhẹ, đủ dùng)

Whisper STT chạy trên CPU để dành toàn bộ 6GB VRAM cho LLM (xem giải thích
ở mục 5). `torch` trong dự án này chỉ dùng để kiểm tra `torch.cuda.is_available()`,
nên bản CPU là đủ và nhẹ hơn nhiều:

```powershell
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

## 4. Cài các thư viện còn lại

```powershell
pip install -r requirements.txt
```

## 5. Cài `llama-cpp-python` với tăng tốc CUDA (bước quan trọng nhất)

```powershell
$env:CMAKE_ARGS="-DGGML_CUDA=on"
pip install llama-cpp-python --no-cache-dir
```

Quá trình build mất khoảng 5-15 phút (biên dịch mã nguồn CUDA). Nếu thấy
log có dòng `-- Found CUDAToolkit` là đang build đúng hướng GPU.

Nếu lệnh báo lỗi không tìm thấy `cl.exe`/`cmake` → mở terminal
**"x64 Native Tools Command Prompt for VS 2022"** (cài kèm Build Tools ở
bước 1.1) rồi kích hoạt lại venv và chạy lại lệnh trên trong terminal đó.

---

## 6. Tải model Qwen3-4B (GGUF)

Model mặc định dự án dùng là `Qwen3-4B-Q5_K_M.gguf` (~2.9GB), rất vừa với
GPU 6GB VRAM. Tạo thư mục `models/` rồi tải bằng `huggingface-hub` (đã có
sẵn trong requirements.txt):

```powershell
mkdir models
huggingface-cli download unsloth/Qwen3-4B-GGUF Qwen3-4B-Q5_K_M.gguf --local-dir models
```

Sau khi tải xong, file phải nằm đúng tại `models/Qwen3-4B-Q5_K_M.gguf`.

---

## 7. Cấu hình cho GPU 6GB VRAM

Copy `.env.example` thành `.env` (không bắt buộc, giá trị mặc định trong
`app/config.py` đã hợp lý cho 6GB VRAM):

```powershell
copy .env.example .env
```

Giải thích các thông số quan trọng:
- `N_GPU_LAYERS=-1` → offload toàn bộ layer model lên GPU. Với Qwen3-4B
  Q5_K_M (~2.9GB) + KV-cache ngữ cảnh 4096 token, tổng dùng khoảng
  3.2-3.8GB VRAM — vừa với 6GB, còn dư khoảng 2GB.
- `STT_DEVICE=cpu` → Whisper chạy CPU, không tranh VRAM với LLM. Đây là
  lựa chọn AN TOÀN nhất cho GPU 6GB.
- Nếu khi chạy `python run.py` bạn thấy lỗi **CUDA out of memory**:
  giảm dần `N_GPU_LAYERS` trong `.env` (ví dụ `28`, rồi `20`, `15`...
  model Qwen3-4B có khoảng 36 layer) để chỉ offload một phần lên GPU,
  hoặc giảm `LLM_CONTEXT` xuống `2048`.

---

## 8. Chạy server

```powershell
python run.py
```

Lần đầu chạy, model load mất khoảng 15-40 giây (tuỳ ổ đĩa). Terminal sẽ
in ra dòng `Loading Qwen model: ...` và `n_gpu_layers=-1, n_ctx=4096`.
Mở trình duyệt tại: **http://localhost:8000**

Bạn sẽ thấy nút chat tròn (logo Beenavi) ở góc phải dưới màn hình — đó là
chatbot đã được nối vào backend thật (WebSocket `/ws`), gõ tin nhắn hoặc
bấm micro để test giọng nói tiếng Việt.

---

## 9. Những gì mình đã sửa/nối trong đợt này

1. **`requirements.txt`**: bỏ `llama-cpp-python` ra khỏi file (phải cài
   riêng theo bước 5 để có CUDA), thêm ghi chú rõ ràng.
2. **`app/config.py`**: nạp file `.env` bằng `python-dotenv` (trước đây
   có khai báo trong requirements nhưng chưa từng được dùng), thêm biến
   `N_GPU_LAYERS` để bạn tinh chỉnh VRAM.
3. **`app/brain.py`**: dùng `N_GPU_LAYERS` từ config thay vì cố định `-1`.
4. **`frontend/index.html`**: sửa đường dẫn `style.css` và `app.js` từ
   tương đối (`"style.css"`) sang `"/static/style.css"` — trước đó bị
   lỗi 404 vì server chỉ mount static tại `/static`.
5. **`frontend/app.js`**: đây là phần việc chính — khung chat nổi
   (`#cbPanel`, nút `cbSendText`, `cbToggleMic`, `cbToggleVoiceCall`...)
   đã có sẵn trong HTML kèm ghi chú "Backend: FastAPI /chat, /ws,
   /transcribe" nhưng **các hàm JS này chưa từng được viết** — nút bấm
   không hoạt động. Mình đã viết đầy đủ, kết nối WebSocket `/ws` thật:
   - Gõ tin nhắn → gửi qua WS, nhận câu trả lời AI stream theo thời gian thực.
   - Bấm Micro → ghi âm thật qua `MediaRecorder`, gửi audio streaming lên
     server, hiển thị transcript và câu trả lời.
   - Đàm thoại trực tiếp → ghi âm theo lượt, phát câu trả lời bằng
     `speechSynthesis` (đọc to), tự động lặp lại lượt nói tiếp theo.
   - Thanh tìm kiếm AI ở đầu trang và nút "Nhân bản lịch trình cộng đồng"
     trước đó gọi vào code chat cũ (khung `chatDrawer`) không tồn tại
     trong HTML → mình đã trỏ lại đúng về khung chat thật.

## 10. Giới hạn còn tồn tại (chưa làm trong đợt này)

- **Chụp ảnh / AI Vision**: nút chụp ảnh, đăng ảnh trong khung chat đã
  hoạt động (hiển thị ảnh), nhưng backend **chưa có endpoint phân tích
  ảnh** — AI sẽ chỉ báo là chưa hỗ trợ, không tự bịa kết quả phân tích.
  Muốn có tính năng này cần thêm model Vision + endpoint riêng.
- **Lịch trình AI hiển thị trực quan** (bản đồ, các thẻ ngày 1/ngày 2...)
  vẫn đang là dữ liệu mẫu tĩnh (`DESTINATIONS_DB`), chưa được sinh ra từ
  câu trả lời thực tế của AI — AI hiện chỉ trả lời bằng văn bản trong
  khung chat.
- **Lịch sử hội thoại** chỉ lưu trong RAM theo từng kết nối WebSocket,
  mất khi tắt tab hoặc restart server (chưa có database).
- Nút `📸 Đăng ảnh` trên hero section (đầu trang, ngoài khung chat) vẫn
  là code cũ (`triggerChatVisionUpload`), chưa nối — nếu cần dùng, báo
  mình làm tiếp.
