"""
beenavi/diary_service.py
Module quản lý Cơ sở Dữ liệu Người dùng, Nhật ký Chuyến đi,
Checklist hành trang và Lịch sử trò chuyện bằng SQLite cho FastAPI.
"""
import os
import sys
import uuid
import json
import sqlite3
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

REPO_ROOT = Path(__file__).resolve().parent
DATA_DIR = REPO_ROOT / "data"
DB_PATH = DATA_DIR / "user_diary.db"


def get_db_connection() -> sqlite3.Connection:
    """Tạo kết nối CSDL và tự động tạo bảng nếu chưa có"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_diary_database():
    """Khởi tạo toàn bộ cấu trúc bảng Người dùng, Nhật ký, Ảnh và Lịch sử Chat"""
    conn = get_db_connection()
    c = conn.cursor()

    # 1. Bảng Người dùng
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Bảng Hồ sơ sở thích cá nhân hóa
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id TEXT PRIMARY KEY,
        full_name TEXT,
        nickname TEXT,
        gender TEXT,
        location TEXT,
        travel_style TEXT DEFAULT '[]',
        default_budget_tier TEXT DEFAULT 'Tiêu chuẩn',
        frequent_companion TEXT,
        food_allergies TEXT DEFAULT '[]',
        special_requirements TEXT DEFAULT '[]',
        niche_interests TEXT DEFAULT '[]',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 3. Bảng Chuyến đi & Lịch sử sinh lộ trình
    c.execute("""
    CREATE TABLE IF NOT EXISTS trips (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        title TEXT NOT NULL,
        destination TEXT NOT NULL,
        departure_location TEXT,
        start_date TEXT,
        number_of_days INTEGER DEFAULT 3,
        budget_limit REAL DEFAULT 0.0,
        vehicle TEXT DEFAULT 'Máy bay',
        trip_type TEXT DEFAULT 'Khám phá',
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )
    """)

    # 4. Bảng Lộ trình chi tiết từng ngày
    c.execute("""
    CREATE TABLE IF NOT EXISTS itineraries (
        id TEXT PRIMARY KEY,
        trip_id TEXT UNIQUE NOT NULL,
        days_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
    )
    """)

    # 5. Bảng Ảnh kỷ niệm check-in
    c.execute("""
    CREATE TABLE IF NOT EXISTS photos (
        id TEXT PRIMARY KEY,
        trip_id TEXT NOT NULL,
        image_url TEXT NOT NULL,
        caption TEXT,
        location_tag TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
    )
    """)

    # 6. Bảng Checklist hành trang đồ dùng
    c.execute("""
    CREATE TABLE IF NOT EXISTS checklist_items (
        id TEXT PRIMARY KEY,
        trip_id TEXT NOT NULL,
        item_name TEXT NOT NULL,
        category TEXT DEFAULT 'Đồ dùng chung',
        quantity INTEGER DEFAULT 1,
        priority TEXT DEFAULT 'Bắt buộc',
        is_completed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE
    )
    """)

    # 7. Bảng Lịch sử Chat với AI Chatbot (Hỏi đáp & Ngữ cảnh)
    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# Khởi tạo ngay khi import module
init_diary_database()


# ──────────────────────────────────────────────────────────────────────────────
# PHÂN HỆ 1: QUẢN LÝ NGƯỜI DÙNG & XÁC THỰC
# ──────────────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Băm mật khẩu an toàn SHA-256 + Salt từ biến môi trường"""
    try:
        from api_server.config import AUTH_SECRET_SALT
        salt = AUTH_SECRET_SALT
    except Exception:
        salt = os.getenv("AUTH_SECRET_SALT", "beenavi_super_secret_auth_salt_prod_2026")
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


def register_user(username: str, email: str, password: str, full_name: str = "") -> dict:
    """Đăng ký tài khoản người dùng mới và tạo hồ sơ mặc định"""
    conn = get_db_connection()
    c = conn.cursor()
    user_id = str(uuid.uuid4())
    pw_hash = hash_password(password)

    try:
        c.execute(
            "INSERT INTO users (id, username, email, password_hash) VALUES (?, ?, ?, ?)",
            (user_id, username, email, pw_hash)
        )
        c.execute(
            "INSERT INTO user_profiles (user_id, full_name) VALUES (?, ?)",
            (user_id, full_name or username)
        )
        conn.commit()
        return {"id": user_id, "username": username, "email": email, "full_name": full_name or username}
    except sqlite3.IntegrityError as e:
        if "username" in str(e).lower():
            raise ValueError("Tên đăng nhập đã tồn tại")
        elif "email" in str(e).lower():
            raise ValueError("Email này đã được sử dụng")
        raise ValueError("Lỗi đăng ký tài khoản")
    finally:
        conn.close()


def authenticate_user(username_or_email: str, password: str) -> Optional[dict]:
    """Xác thực đăng nhập"""
    conn = get_db_connection()
    c = conn.cursor()
    pw_hash = hash_password(password)

    row = c.execute("""
        SELECT u.id, u.username, u.email, COALESCE(p.full_name, u.username) AS full_name
        FROM users u
        LEFT JOIN user_profiles p ON u.id = p.user_id
        WHERE (u.username = ? OR u.email = ?) AND u.password_hash = ?
    """, (username_or_email, username_or_email, pw_hash)).fetchone()

    conn.close()
    if row:
        return dict(row)
    return None



def get_user_profile(user_id: str) -> Optional[dict]:
    """Lấy thông tin hồ sơ và sở thích cá nhân hóa"""
    conn = get_db_connection()
    c = conn.cursor()
    row = c.execute("""
        SELECT u.id, u.username, u.email, p.full_name, p.nickname, p.gender, p.location,
               p.travel_style, p.default_budget_tier, p.frequent_companion,
               p.food_allergies, p.special_requirements, p.niche_interests
        FROM users u
        LEFT JOIN user_profiles p ON u.id = p.user_id
        WHERE u.id = ?
    """, (user_id,)).fetchone()
    conn.close()

    if not row:
        return None

    data = dict(row)
    # Parse các trường JSON
    for json_field in ["travel_style", "food_allergies", "special_requirements", "niche_interests"]:
        try:
            data[json_field] = json.loads(data.get(json_field) or "[]")
        except Exception:
            data[json_field] = []
    return data


def _ensure_json_array(val) -> str:
    if val is None:
        return "[]"
    if isinstance(val, list):
        return json.dumps(val, ensure_ascii=False)
    if isinstance(val, str):
        val_s = val.strip()
        if val_s.startswith("[") and val_s.endswith("]"):
            return val_s
        return json.dumps([val_s] if val_s else [], ensure_ascii=False)
    return "[]"


def update_user_profile(user_id: str, profile_data: dict) -> dict:
    """Cập nhật hồ sơ và sở thích cá nhân hóa"""
    conn = get_db_connection()
    c = conn.cursor()

    food_field = profile_data.get("food_allergies") or profile_data.get("dietary_restrictions")
    style_field = profile_data.get("travel_style")
    budget_field = profile_data.get("default_budget_tier") or profile_data.get("budget_preference", "Tiêu chuẩn")

    c.execute("""
        UPDATE user_profiles
        SET full_name = COALESCE(?, full_name), 
            nickname = COALESCE(?, nickname), 
            gender = COALESCE(?, gender), 
            location = COALESCE(?, location),
            travel_style = ?, 
            default_budget_tier = ?, 
            frequent_companion = COALESCE(?, frequent_companion),
            food_allergies = ?, 
            special_requirements = ?, 
            niche_interests = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (
        profile_data.get("full_name"),
        profile_data.get("nickname"),
        profile_data.get("gender"),
        profile_data.get("location"),
        _ensure_json_array(style_field),
        budget_field,
        profile_data.get("frequent_companion"),
        _ensure_json_array(food_field),
        _ensure_json_array(profile_data.get("special_requirements")),
        _ensure_json_array(profile_data.get("niche_interests")),
        user_id
    ))
    conn.commit()
    conn.close()
    return get_user_profile(user_id)


# ──────────────────────────────────────────────────────────────────────────────
# PHÂN HỆ 2: QUẢN LÝ CHUYẾN ĐI, LỊCH TRÌNH & THỐNG KÊ
# ──────────────────────────────────────────────────────────────────────────────

def create_trip(trip_data: dict, user_id: Optional[str] = None) -> dict:
    """Tạo chuyến đi và lưu lịch trình chi tiết vào CSDL"""
    conn = get_db_connection()
    c = conn.cursor()
    trip_id = str(uuid.uuid4())
    itinerary_id = str(uuid.uuid4())

    title = trip_data.get("title") or f"Chuyến đi {trip_data.get('destination', 'Việt Nam')}"
    destination = trip_data.get("destination", "Đà Nẵng")
    departure_location = trip_data.get("departure_location", "Hà Nội")
    start_date = trip_data.get("start_date") or time.strftime("%Y-%m-%d")
    number_of_days = int(trip_data.get("number_of_days") or trip_data.get("num_days") or 3)
    budget_limit = float(trip_data.get("budget_limit") or 0.0)
    vehicle = trip_data.get("vehicle", "Máy bay")
    trip_type = trip_data.get("trip_type", "Khám phá")
    days = trip_data.get("days", [])

    c.execute("""
        INSERT INTO trips (id, user_id, title, destination, departure_location, start_date, number_of_days, budget_limit, vehicle, trip_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (trip_id, user_id, title, destination, departure_location, start_date, number_of_days, budget_limit, vehicle, trip_type))

    c.execute("""
        INSERT INTO itineraries (id, trip_id, days_json)
        VALUES (?, ?, ?)
    """, (itinerary_id, trip_id, json.dumps(days, ensure_ascii=False)))

    # Tạo sẵn các đồ dùng mặc định vào checklist
    default_items = [
        ("CCCD / Hộ chiếu bản gốc", "Giấy tờ", "Bắt buộc"),
        ("Vé máy bay / Đặt phòng khách sạn", "Giấy tờ", "Bắt buộc"),
        ("Kem chống nắng & Kính mát", "Cá nhân", "Ưu tiên"),
        ("Sạc dự phòng & Tai nghe", "Điện tử", "Bắt buộc"),
        ("Thuốc hạ sốt & Băng gạc y tế", "Y tế", "Khuyên dùng"),
    ]
    for item_name, cat, prio in default_items:
        c.execute("""
            INSERT INTO checklist_items (id, trip_id, item_name, category, priority)
            VALUES (?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), trip_id, item_name, cat, prio))

    conn.commit()
    conn.close()

    return get_trip_detail(trip_id)


def save_or_update_trip(trip_data: dict, user_id: Optional[str] = None) -> dict:
    """Lưu hoặc cập nhật lộ trình chuyến đi vào CSDL SQLite cho User"""
    conn = get_db_connection()
    c = conn.cursor()

    trip_id = trip_data.get("id") or trip_data.get("trip_id")
    title = trip_data.get("title") or f"Chuyến đi {trip_data.get('destination', 'Việt Nam')}"
    destination = trip_data.get("destination", "Việt Nam")
    departure_location = trip_data.get("departure_location", "Hà Nội")
    start_date = trip_data.get("start_date") or time.strftime("%Y-%m-%d")
    number_of_days = int(trip_data.get("number_of_days") or trip_data.get("num_days") or len(trip_data.get("days", [])) or 3)
    budget_limit = float(trip_data.get("budget_limit") or trip_data.get("total_budget") or 0.0)
    vehicle = trip_data.get("vehicle", "Máy bay")
    trip_type = trip_data.get("trip_type", "Khám phá")
    days = trip_data.get("days", [])

    existing = None
    if trip_id:
        existing = c.execute("SELECT id FROM trips WHERE id = ?", (trip_id,)).fetchone()
    elif user_id and destination:
        existing = c.execute("SELECT id FROM trips WHERE user_id = ? AND destination = ? ORDER BY created_at DESC LIMIT 1", (user_id, destination)).fetchone()

    if existing:
        target_id = existing[0]
        c.execute("""
            UPDATE trips 
            SET title = ?, destination = ?, number_of_days = ?, budget_limit = ?
            WHERE id = ?
        """, (title, destination, number_of_days, budget_limit, target_id))

        it_exists = c.execute("SELECT id FROM itineraries WHERE trip_id = ?", (target_id,)).fetchone()
        if it_exists:
            c.execute("UPDATE itineraries SET days_json = ? WHERE trip_id = ?", (json.dumps(days, ensure_ascii=False), target_id))
        else:
            c.execute("INSERT INTO itineraries (id, trip_id, days_json) VALUES (?, ?, ?)", (str(uuid.uuid4()), target_id, json.dumps(days, ensure_ascii=False)))
        conn.commit()
        conn.close()
        return get_trip_detail(target_id)
    else:
        conn.close()
        return create_trip(trip_data, user_id)


def get_user_trips(user_id: Optional[str] = None) -> List[dict]:
    """Lấy danh sách tất cả chuyến đi"""
    conn = get_db_connection()
    c = conn.cursor()

    if user_id:
        rows = c.execute("""
            SELECT t.*, 
                   (SELECT COUNT(*) FROM photos WHERE trip_id = t.id) as photo_count,
                   (SELECT COUNT(*) FROM checklist_items WHERE trip_id = t.id) as checklist_count
            FROM trips t
            WHERE t.user_id = ?
            ORDER BY t.created_at DESC
        """, (user_id,)).fetchall()
    else:
        rows = c.execute("""
            SELECT t.*, 
                   (SELECT COUNT(*) FROM photos WHERE trip_id = t.id) as photo_count,
                   (SELECT COUNT(*) FROM checklist_items WHERE trip_id = t.id) as checklist_count
            FROM trips t
            ORDER BY t.created_at DESC
        """).fetchall()

    trips = [dict(r) for r in rows]
    conn.close()
    return trips


def get_trip_detail(trip_id: str) -> Optional[dict]:
    """Lấy thông tin chi tiết một chuyến đi (kèm Lộ trình, Ảnh, Checklist)"""
    conn = get_db_connection()
    c = conn.cursor()

    trip_row = c.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if not trip_row:
        conn.close()
        return None

    trip = dict(trip_row)

    # Lấy Itinerary
    it_row = c.execute("SELECT days_json FROM itineraries WHERE trip_id = ?", (trip_id,)).fetchone()
    if it_row:
        try:
            trip["days"] = json.loads(it_row["days_json"])
        except Exception:
            trip["days"] = []
    else:
        trip["days"] = []

    # Lấy Photos
    photo_rows = c.execute("SELECT * FROM photos WHERE trip_id = ? ORDER BY created_at DESC", (trip_id,)).fetchall()
    trip["photos"] = [dict(p) for p in photo_rows]

    # Lấy Checklist
    chk_rows = c.execute("SELECT * FROM checklist_items WHERE trip_id = ? ORDER BY created_at ASC", (trip_id,)).fetchall()
    trip["checklist"] = [dict(k) for k in chk_rows]

    conn.close()
    return trip


def delete_trip(trip_id: str) -> bool:
    """Xóa chuyến đi"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    conn.commit()
    conn.close()
    return True


# ──────────────────────────────────────────────────────────────────────────────
# PHÂN HỆ 3: QUẢN LÝ ẢNH & CHECKLIST
# ──────────────────────────────────────────────────────────────────────────────

def add_photo_to_trip(trip_id: str, image_url: str, caption: str = "", location_tag: str = "") -> dict:
    """Thêm ảnh check-in vào chuyến đi"""
    conn = get_db_connection()
    c = conn.cursor()
    photo_id = str(uuid.uuid4())

    c.execute("""
        INSERT INTO photos (id, trip_id, image_url, caption, location_tag)
        VALUES (?, ?, ?, ?, ?)
    """, (photo_id, trip_id, image_url, caption, location_tag))
    conn.commit()
    conn.close()

    return {"id": photo_id, "trip_id": trip_id, "image_url": image_url, "caption": caption, "location_tag": location_tag}


def get_trip_checklist(trip_id: str) -> List[dict]:
    """Lấy danh sách tất cả đồ dùng checklist của chuyến đi"""
    conn = get_db_connection()
    c = conn.cursor()
    rows = c.execute("SELECT * FROM checklist_items WHERE trip_id = ? ORDER BY created_at ASC", (trip_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_checklist_item(trip_id: str, item_name: str, category: str = "Đồ dùng chung", quantity: int = 1, priority: str = "Bắt buộc", is_completed: int = 0) -> dict:
    """Thêm một mục đồ dùng mới vào checklist của chuyến đi"""
    conn = get_db_connection()
    c = conn.cursor()
    item_id = str(uuid.uuid4())
    c.execute("""
        INSERT INTO checklist_items (id, trip_id, item_name, category, quantity, priority, is_completed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (item_id, trip_id, item_name, category, quantity, priority, 1 if is_completed else 0))
    conn.commit()
    conn.close()
    return {
        "id": item_id,
        "trip_id": trip_id,
        "item_name": item_name,
        "category": category,
        "quantity": quantity,
        "priority": priority,
        "is_completed": 1 if is_completed else 0
    }


def update_checklist_item(item_id: str, is_completed: bool) -> bool:
    """Cập nhật trạng thái đồ dùng đã chuẩn bị"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE checklist_items SET is_completed = ? WHERE id = ?", (1 if is_completed else 0, item_id))
    conn.commit()
    conn.close()
    return True


def delete_checklist_item(item_id: str) -> bool:
    """Xóa một đồ dùng khỏi checklist"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM checklist_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return True


def save_trip_checklist_bulk(trip_id: str, items: List[dict]) -> List[dict]:
    """Lưu danh sách nhiều đồ dùng cùng lúc cho chuyến đi"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM checklist_items WHERE trip_id = ?", (trip_id,))
    res = []
    for it in items:
        item_id = it.get("id") or str(uuid.uuid4())
        item_name = it.get("item_name") or it.get("text") or "Đồ dùng"
        category = it.get("category", "Đồ dùng chung")
        quantity = int(it.get("quantity", 1))
        priority = it.get("priority", "Bắt buộc")
        is_completed = 1 if (it.get("is_completed") or it.get("checked")) else 0
        c.execute("""
            INSERT INTO checklist_items (id, trip_id, item_name, category, quantity, priority, is_completed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (item_id, trip_id, item_name, category, quantity, priority, is_completed))
        res.append({
            "id": item_id,
            "trip_id": trip_id,
            "item_name": item_name,
            "category": category,
            "quantity": quantity,
            "priority": priority,
            "is_completed": is_completed
        })
    conn.commit()
    conn.close()
    return res


def get_user_statistics(user_id: Optional[str] = None) -> dict:
    """Thống kê tổng quan: Tổng chuyến đi, tổng ảnh, tổng địa điểm"""
    conn = get_db_connection()
    c = conn.cursor()

    if user_id:
        total_trips = c.execute("SELECT COUNT(*) FROM trips WHERE user_id = ?", (user_id,)).fetchone()[0]
        total_photos = c.execute("""
            SELECT COUNT(*) FROM photos p
            JOIN trips t ON p.trip_id = t.id
            WHERE t.user_id = ?
        """, (user_id,)).fetchone()[0]
        unique_dest = c.execute("SELECT COUNT(DISTINCT destination) FROM trips WHERE user_id = ?", (user_id,)).fetchone()[0]
    else:
        total_trips = c.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
        total_photos = c.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
        unique_dest = c.execute("SELECT COUNT(DISTINCT destination) FROM trips").fetchone()[0]

    conn.close()
    return {
        "total_trips": total_trips,
        "total_photos": total_photos,
        "unique_destinations": unique_dest,
    }


# ──────────────────────────────────────────────────────────────────────────────
# PHÂN HỆ 4: LỊCH SỬ HỘI THOẠI CHATBOT (SESSION & MESSAGES)
# ──────────────────────────────────────────────────────────────────────────────

def save_chat_message(role: str, content: str, session_id: str = "default", user_id: Optional[str] = None) -> dict:
    """Lưu tin nhắn của User hoặc AI vào CSDL"""
    conn = get_db_connection()
    c = conn.cursor()
    msg_id = str(uuid.uuid4())

    c.execute("""
        INSERT INTO chat_messages (id, user_id, session_id, role, content)
        VALUES (?, ?, ?, ?, ?)
    """, (msg_id, user_id, session_id, role, content))
    conn.commit()
    conn.close()

    return {"id": msg_id, "session_id": session_id, "role": role, "content": content}


def get_chat_history(session_id: str = "default", limit: int = 50) -> List[dict]:
    """Lấy danh sách tin nhắn cũ trong phiên chat"""
    conn = get_db_connection()
    c = conn.cursor()

    rows = c.execute("""
        SELECT id, role, content, created_at
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY created_at ASC
        LIMIT ?
    """, (session_id, limit)).fetchall()

    conn.close()
    return [dict(r) for r in rows]
