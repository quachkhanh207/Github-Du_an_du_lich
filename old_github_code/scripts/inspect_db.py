"""
scripts/inspect_db.py
Xem chi tiết cấu trúc, số lượng bản ghi và mẫu dữ liệu của 2 Hệ CSDL trong dự án BeeNavi.
"""
import sqlite3
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_KNOWLEDGE = REPO_ROOT / "data" / "travel_knowledge.db"
DB_DIARY = REPO_ROOT / "data" / "user_diary.db"

print("=========================================================================")
print("🏛️  HỆ THỐNG CƠ SỞ DỮ LIỆU DỰ ÁN BEENAVI")
print("=========================================================================\n")

# 1. CSDL Tri thức du lịch (RAG Knowledge)
print("1️⃣  CSDL TRI THỨC & RAG (Địa điểm du lịch thực tế):")
print(f"   📁 Đường dẫn: {DB_KNOWLEDGE}")
if DB_KNOWLEDGE.exists():
    conn = sqlite3.connect(str(DB_KNOWLEDGE))
    c = conn.cursor()
    tables = [t[0] for t in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    count = c.execute("SELECT count(*) FROM pois").fetchone()[0]
    size_mb = DB_KNOWLEDGE.stat().st_size / (1024 * 1024)
    print(f"   📊 Dung lượng: {size_mb:.2f} MB | Tổng địa điểm: {count:,} POIs")
    print(f"   📑 Danh sách bảng: {', '.join(tables)}")
    print("   📋 Cấu trúc bảng `pois`:")
    for col in c.execute("PRAGMA table_info(pois)").fetchall():
        print(f"      • {col[1]:<15} : Kiểu dữ liệu {col[2]}")
    
    print("\n   🔍 Mẫu 3 địa điểm trong CSDL:")
    for r in c.execute("SELECT name, category, lat, lon, address FROM pois LIMIT 3").fetchall():
        print(f"      📍 {r[0]} ({r[1]}) - Tọa độ: [{r[2]}, {r[3]}] - Địa chỉ: {r[4] or 'Đang cập nhật'}")
    conn.close()
else:
    print("   ❌ Chưa tìm thấy file CSDL.")

print("\n" + "-" * 73 + "\n")

# 2. CSDL Nhật ký & Người dùng (SQLite)
print("2️⃣  CSDL NHẬT KÝ HÀNH TRÌNH & NGƯỜI DÙNG (SQLite):")
print(f"   📁 Đường dẫn: {DB_DIARY}")
if DB_DIARY.exists():
    conn2 = sqlite3.connect(str(DB_DIARY))
    c2 = conn2.cursor()
    tables2 = [t[0] for t in c2.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
    size_mb2 = DB_DIARY.stat().st_size / (1024 * 1024)
    print(f"   📊 Dung lượng: {size_mb2:.2f} MB")
    print("   📑 Danh sách bảng quản lý:")
    for t in tables2:
        try:
            cnt = c2.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
            print(f"      • {t:<28} : {cnt} bản ghi")
        except Exception:
            pass
    conn2.close()
else:
    print("   ❌ Chưa tìm thấy file CSDL.")

print("\n=========================================================================")
