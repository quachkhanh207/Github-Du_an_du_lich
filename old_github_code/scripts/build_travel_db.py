"""
beenavi/scripts/build_travel_db.py
Xây dựng cơ sở dữ liệu tìm kiếm du lịch (SQLite FTS5 + locations_index.json)
từ tập dữ liệu markdown trong beenavi/data/md_dataset.
"""
import os
import sys
import re
import json
import sqlite3
import time
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
MD_DATASET_DIR = DATA_DIR / "md_dataset"
DB_PATH = DATA_DIR / "travel_knowledge.db"
JSON_PATH = DATA_DIR / "locations_index.json"


def parse_markdown_file(file_path: Path) -> dict | None:
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    name_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else file_path.stem

    def get_field(field_name: str) -> str:
        m = re.search(rf"-\s+\*\*{field_name}:\*\*\s*(.+)$", content, re.MULTILINE | re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            return "" if val.lower() in ["none", "null", ""] else val
        return ""

    category = get_field("Danh mục") or "Khám phá"
    sub_category = get_field("Danh mục con") or ""
    lat_str = get_field("Latitude")
    lon_str = get_field("Longitude")
    address = get_field("Địa chỉ") or ""
    cuisine = get_field("Ẩm thực") or ""
    description = get_field("Mô tả") or ""
    open_hours = get_field("Giờ mở cửa") or ""
    wheelchair = get_field("Hỗ trợ xe lăn") or ""

    try:
        lat = float(lat_str) if lat_str else 0.0
        lon = float(lon_str) if lon_str else 0.0
    except ValueError:
        lat, lon = 0.0, 0.0

    return {
        "id": file_path.stem,
        "name": name,
        "category": category,
        "sub_category": sub_category,
        "lat": lat,
        "lon": lon,
        "address": address,
        "cuisine": cuisine,
        "description": description,
        "open_hours": open_hours,
        "wheelchair": wheelchair,
    }


def build_database():
    print("======================================================")
    print("  BeeNavi Knowledge Database Builder (Safe & Fast)    ")
    print("======================================================")

    if not MD_DATASET_DIR.exists():
        print(f"[Lỗi] Không tìm thấy thư mục: {MD_DATASET_DIR}")
        return

    md_files = sorted(list(MD_DATASET_DIR.glob("*.md")))
    total_files = len(md_files)
    print(f"[1/3] Đang đọc {total_files} file địa điểm markdown...")
    start_time = time.time()

    records = []
    json_records = []

    for f in md_files:
        poi = parse_markdown_file(f)
        if not poi or not poi["name"]:
            continue
        records.append((
            poi["id"],
            poi["name"],
            poi["category"],
            poi["sub_category"],
            poi["lat"],
            poi["lon"],
            poi["address"],
            poi["cuisine"],
            poi["description"],
            poi["open_hours"],
            poi["wheelchair"]
        ))
        json_records.append({
            "name": poi["name"],
            "lat": poi["lat"],
            "lon": poi["lon"],
            "category": poi["category"],
            "info": f"{poi['name']}; {poi['category']}; {poi['address'] or poi['description']}"
        })

    print(f"[2/3] Đang tạo CSDL SQLite FTS5 (Full-Text Search) tại {DB_PATH}...")
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except Exception:
            pass

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Tạo bảng chính
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pois (
        id TEXT PRIMARY KEY,
        name TEXT,
        category TEXT,
        sub_category TEXT,
        lat REAL,
        lon REAL,
        address TEXT,
        cuisine TEXT,
        description TEXT,
        open_hours TEXT,
        wheelchair TEXT
    )
    """)

    # Tạo bảng Full Text Search FTS5
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS pois_fts USING fts5(
        id UNINDEXED,
        name,
        category,
        sub_category,
        address,
        cuisine,
        description,
        content='pois',
        content_rowid='rowid'
    )
    """)

    cursor.executemany("""
    INSERT INTO pois (id, name, category, sub_category, lat, lon, address, cuisine, description, open_hours, wheelchair)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)

    cursor.execute("""
    INSERT INTO pois_fts(rowid, id, name, category, sub_category, address, cuisine, description)
    SELECT rowid, id, name, category, sub_category, address, cuisine, description FROM pois
    """)

    # Tạo index cho lat, lon, category
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pois_lat_lon ON pois(lat, lon)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pois_category ON pois(category)")

    conn.commit()
    conn.close()

    print(f"[3/3] Đang xuất file cache JSON: {JSON_PATH}...")
    with open(JSON_PATH, "w", encoding="utf-8") as jf:
        json.dump(json_records, jf, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    print("======================================================")
    print(f"✅ Hoàn tất xây dựng CSDL cho {len(records)} địa điểm!")
    print(f"   ⏱️  Thời gian: {elapsed:.2f} giây (Siêu nhanh & An toàn 100%)")
    print(f"   📁 SQLite DB : {DB_PATH} ({DB_PATH.stat().st_size / (1024*1024):.2f} MB)")
    print(f"   📁 JSON Cache: {JSON_PATH} ({JSON_PATH.stat().st_size / (1024*1024):.2f} MB)")
    print("======================================================")


if __name__ == "__main__":
    build_database()
