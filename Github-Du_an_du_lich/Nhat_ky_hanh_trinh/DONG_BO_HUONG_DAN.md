# Hướng dẫn tích hợp phân hệ Nhật ký hành trình vào Dự án tổng (Bản Tối Giản)

Tài liệu này hướng dẫn cách kết hợp các tệp mã nguồn của phân hệ **Nhật ký hành trình** vào dự án Django tổng thể của nhóm.

Phân hệ này đã được làm sạch và đóng gói thành 1 ứng dụng Django duy nhất: **`trips`**. Toàn bộ các cấu hình không thuộc phạm vi công việc của bạn (như đăng ký, đăng nhập, sinh lịch trình tự động) đã được xóa bỏ để đảm bảo tính độc lập và dễ tích hợp nhất.

---

## 1. Cơ cấu Cơ sở dữ liệu (Django ORM Models)

Mã nguồn gồm 3 models lưu trữ chính định nghĩa tại `trips/models.py`:

* **`Trip`**: Lưu thông tin cốt lõi của chuyến đi nhận từ phân hệ lập lịch của thành viên khác.
  * Các trường: `id` (UUID), `destination` (Điểm đến), `departure_location` (Điểm đi), `start_date` (Ngày bắt đầu), `number_of_days` (Số ngày), `budget_limit` (Ngân sách), `status` (Trạng thái chuyến đi).
* **`Itinerary`**: Lưu lộ trình chi tiết.
  * Trường `days` (`JSONField`) lưu cấu trúc hoạt động các ngày của chuyến đi.
* **`Photo`**: Lưu trữ các bức ảnh check-in đính kèm của chuyến đi.
  * Các trường: `image_url` (đường dẫn liên kết ảnh), `caption` (mô tả), `location_tag` (nhãn địa điểm check-in).

---

## 2. Cách tích hợp vào Dự án tổng

### Bước 1: Sao chép thư mục App
Sao chép thư mục **`trips`** vào thư mục gốc của dự án Django tổng.

### Bước 2: Đăng ký App trong cấu hình Settings
Thêm `'trips'` vào `INSTALLED_APPS` trong file `settings.py` của dự án tổng:
```python
INSTALLED_APPS = [
    # ... các app mặc định ...
    'rest_framework',
    'trips',
]
```

### Bước 3: Tạo và chạy Migrations
Chạy các lệnh để Django tự tạo cấu trúc bảng trong cơ sở dữ liệu chung:
```bash
python manage.py makemigrations trips
python manage.py migrate
```

### Bước 4: Khai báo URL Routing
Trong file `urls.py` chính của dự án tổng, include các url của phân hệ này:
```python
from django.urls import path, include

urlpatterns = [
    # ... các url cũ ...
    path('api/v1/', include('trips.urls')),
]
```

---

## 3. Danh sách các API Endpoint phục vụ kết nối
Tất cả các API đều hoạt động không yêu cầu Token xác thực (thuộc cấu hình bảo mật chung của dự án tổng):

| URL Endpoint | Phương thức | Dữ liệu đầu vào (JSON) | Chức năng (Breaktask) |
| :--- | :--- | :--- | :--- |
| `/api/v1/trips/` | `POST` | Thông tin `destination`, `start_date`, `days` (JSON timeline)... | **Lưu chuyến đi & Lưu lịch trình** |
| `/api/v1/trips/` | `GET` | Không | **Hiển thị lịch sử** (Danh sách chuyến đi kèm số lượng ảnh đã lưu) |
| `/api/v1/trips/<uuid:trip_id>/` | `GET` | Không | Lấy chi tiết lộ trình và ảnh đã gắn của chuyến đi cụ thể |
| `/api/v1/trips/<uuid:trip_id>/photos/` | `POST` | Đường dẫn `image_url`, `caption`, `location_tag` | **Lưu ảnh / Gắn ảnh vào chuyến đi** |
| `/api/v1/trips/statistics/` | `GET` | Không | **Thống kê** (Tổng chuyến đi, ảnh, địa điểm duy nhất) |

*Mọi thắc mắc về tích hợp vui lòng xem lại file test mẫu độc lập `test_journal.py` để nắm được dữ liệu đầu vào/đầu ra thực tế.*
