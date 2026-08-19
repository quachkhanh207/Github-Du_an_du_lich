import sqlite3
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

conn = sqlite3.connect("data/travel_knowledge.db")
c = conn.cursor()

total = c.execute("SELECT count(*) FROM pois").fetchone()[0]

fields = ["name", "category", "sub_category", "address", "cuisine", "description", "open_hours", "wheelchair"]
print(f"TỔNG SỐ ĐỊA ĐIỂM TRONG DATASET: {total:,} bản ghi\n")
print(f"{'Tên trường (Field)':<20} | {'Số lượng có dữ liệu':<20} | {'Tỷ lệ':<10}")
print("-" * 58)
for f in fields:
    cnt = c.execute(f"SELECT count(*) FROM pois WHERE {f} IS NOT NULL AND trim({f}) != '' AND {f} != 'None'").fetchone()[0]
    pct = (cnt / total) * 100
    print(f"{f:<20} | {cnt:>10,} / {total:,} bản ghi | {pct:>6.1f} %")

coords_cnt = c.execute("SELECT count(*) FROM pois WHERE lat != 0.0 AND lon != 0.0").fetchone()[0]
print(f"{'lat, lon (Tọa độ)':<20} | {coords_cnt:>10,} / {total:,} bản ghi | {(coords_cnt/total)*100:>6.1f} %")
conn.close()
