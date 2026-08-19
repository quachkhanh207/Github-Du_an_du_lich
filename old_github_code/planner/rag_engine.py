"""
planner/rag_engine.py
RAG Engine (Retrieval-Augmented Generation) cho BeeNavi.
Sử dụng CSDL SQLite FTS5 kết hợp Cache Index để truy vấn kiến thức du lịch
từ 17.147 địa điểm thực tế trên toàn Việt Nam.
"""
import os
import re
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DB_PATH = DATA_DIR / "travel_knowledge.db"
JSON_INDEX_PATH = DATA_DIR / "locations_index.json"


class RagEngine:
    def __init__(self, index_path: Optional[str] = None):
        self.db_path = DB_PATH
        self.index_path = Path(index_path) if index_path else JSON_INDEX_PATH
        self.locations: List[Dict[str, Any]] = []
        self.loaded = False

    def load_index(self):
        """Nạp index từ JSON cache hoặc SQLite DB"""
        if self.index_path.exists():
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    self.locations = json.load(f)
                self.loaded = True
                print(f"[RAG] Đã nạp thành công {len(self.locations)} địa điểm từ cache.", flush=True)
                return
            except Exception as e:
                print(f"[RAG] Lỗi khi đọc cache JSON: {e}", flush=True)

        # Fallback từ SQLite DB nếu file JSON chưa có
        if self.db_path.exists():
            try:
                conn = sqlite3.connect(str(self.db_path))
                c = conn.cursor()
                rows = c.execute("SELECT name, lat, lon, category, address, description FROM pois").fetchall()
                self.locations = [
                    {
                        "name": r[0],
                        "lat": r[1],
                        "lon": r[2],
                        "category": r[3],
                        "info": f"{r[0]}; {r[3]}; {r[4] or r[5]}"
                    }
                    for r in rows
                ]
                conn.close()
                self.loaded = True
                print(f"[RAG] Đã nạp thành công {len(self.locations)} địa điểm từ SQLite DB.", flush=True)
            except Exception as e:
                print(f"[RAG] Lỗi khi nạp từ SQLite DB: {e}", flush=True)

    def query_knowledge(self, query_text: str, limit: int = 6) -> str:
        """
        Tìm kiếm ngữ nghĩa/từ khóa cho câu hỏi Chat thông thường.
        Trả về đoạn Context tóm tắt các địa điểm thật để chèn vào LLM Prompt.
        """
        if not self.db_path.exists():
            return ""

        # Làm sạch câu truy vấn để tìm FTS5
        clean_q = re.sub(r"[^\w\s\u00C0-\u1EF9]", " ", query_text)
        words = [w.strip() for w in clean_q.split() if len(w.strip()) > 1]
        if not words:
            return ""

        # Tạo MATCH query: tìm kiếm theo cụm hoặc các từ chính
        fts_query = " OR ".join([f'"{w}"' for w in words[:6]])

        try:
            conn = sqlite3.connect(str(self.db_path))
            c = conn.cursor()
            query_sql = """
                SELECT p.name, p.category, p.sub_category, p.address, p.cuisine, p.description, p.open_hours
                FROM pois_fts f
                JOIN pois p ON f.id = p.id
                WHERE pois_fts MATCH ?
                LIMIT ?
            """
            rows = c.execute(query_sql, (fts_query, limit)).fetchall()
            conn.close()

            BLACKLIST_POIS = [
                "qua 100m", "công an", "ubnd", "hội đồng", "nhà nghỉ", "nghĩa trang", 
                "bệnh viện", "trung cấp nghề", "chính trị", "nội trú", "thpt", "thcs", "tiểu học"
            ]

            if not rows:
                return ""

            context = "\n\n[DỮ LIỆU ĐỊA ĐIỂM DU LỊCH THỰC TẾ TRA CỨU TỪ CSDL]:\n"
            valid_count = 0
            for r in rows:
                name, cat, subcat, addr, cuisine, desc, hours = r
                full_txt = f"{name} {addr or ''} {desc or ''}".lower()
                if any(bad in full_txt for bad in BLACKLIST_POIS):
                    continue

                item_desc = f"- **{name}** ({cat}" + (f" - {subcat}" if subcat else "") + ")"
                if addr:
                    item_desc += f" | Địa chỉ: {addr}"
                if cuisine:
                    item_desc += f" | Ẩm thực: {cuisine}"
                if hours:
                    item_desc += f" | Giờ mở cửa: {hours}"
                if desc:
                    item_desc += f" | Mô tả: {desc}"
                context += item_desc + "\n"
                valid_count += 1
                if valid_count >= limit:
                    break

            if valid_count == 0:
                return ""

            context += "(Hãy ưu tiên sử dụng các thông tin địa điểm có thật ở trên để tư vấn cho người dùng một cách chính xác nhất).\n"
            return context

        except Exception as e:
            print(f"[RAG] Lỗi query_knowledge: {e}")
            return ""

    def search_locations(self, trip_data: dict) -> str:
        """
        Tìm kiếm các POIs và phân cụm theo ngày cho chức năng LẬP LỊCH TRÌNH.
        """
        if not self.loaded:
            self.load_index()

        if not self.locations:
            return ""

        from planner.rule_engine import RuleEngineService

        # Lọc danh sách candidates theo điểm đến nếu có
        dest = trip_data.get("destination", "").lower().strip()
        filtered_candidates = []

        BLACKLIST_POIS = [
            "qua 100m", "công an", "ubnd", "hội đồng", "nhà nghỉ", "nghĩa trang", 
            "bệnh viện", "trung cấp nghề", "chính trị", "nội trú", "thpt", "thcs", "tiểu học"
        ]

        if dest:
            for loc in self.locations:
                loc_info = (loc.get("name", "") + " " + loc.get("info", "")).lower()
                if any(bad in loc_info for bad in BLACKLIST_POIS):
                    continue
                if dest in loc_info:
                    filtered_candidates.append(loc)

        if not filtered_candidates:
            filtered_candidates = [
                loc for loc in self.locations 
                if not any(bad in (loc.get("name", "") + " " + loc.get("info", "")).lower() for bad in BLACKLIST_POIS)
            ]

        # Sử dụng RuleEngine để phân cụm theo ngày và buổi
        try:
            final_pois = RuleEngineService.generate_final_candidates(trip_data, filtered_candidates)
        except Exception as e:
            print(f"[RAG] Rule Engine error: {e}")
            final_pois = []

        if not final_pois:
            import random
            fallback = list(filtered_candidates)
            random.shuffle(fallback)
            final_pois = fallback[:10]

        result = "\n\n[DỮ LIỆU ĐỊA ĐIỂM GỢI Ý TỪ CSDL]:\n"

        days_dict = {}
        for poi in final_pois:
            d = poi.get("day_cluster", 1)
            if d not in days_dict:
                days_dict[d] = []
            if len(days_dict[d]) < 3:  # Tối đa 3 điểm nổi bật mỗi ngày
                days_dict[d].append(poi)

        for d in sorted(days_dict.keys()):
            result += f"* Ngày {d}: "
            items_str = []
            for poi in days_dict[d]:
                name = poi.get("name", "")
                time_hint = poi.get("time_hint", "Sáng")
                if not name and poi.get("info"):
                    name = poi.get("info").split(";")[0]
                items_str.append(f"[{time_hint}] {name}")
            result += " | ".join(items_str) + "\n"

        result += "(Hãy dùng các địa điểm gợi ý này để xếp vào Ngày 1, Ngày 2... Mỗi hoạt động viết 1 câu súc tích).\n"
        return result


    def get_structured_itinerary(self, trip_data: dict) -> dict:
        """Sinh cấu trúc lịch trình chi tiết (JSON) gồm các Ngày, Buổi, Tọa độ phục vụ Bản đồ và UI."""
        if not self.loaded:
            self.load_index()

        dest = trip_data.get("destination", "Đà Nẵng")
        try:
            num_days = int(trip_data.get("num_days", 3))
        except (ValueError, TypeError):
            num_days = 3

        budget = trip_data.get("budget", "Tiêu chuẩn")
        dest_lower = dest.lower().strip()

        # Lọc candidates theo điểm đến
        filtered_candidates = []
        for loc in self.locations:
            loc_info = (loc.get("name", "") + " " + loc.get("info", "")).lower()
            if dest_lower in loc_info:
                filtered_candidates.append(loc)

        if not filtered_candidates:
            filtered_candidates = self.locations

        from planner.rule_engine import RuleEngineService
        try:
            final_pois = RuleEngineService.generate_final_candidates(trip_data, filtered_candidates)
        except Exception:
            final_pois = []

        if not final_pois:
            import random
            fallback = list(filtered_candidates)
            random.shuffle(fallback)
            final_pois = fallback[:num_days * 4]

        # Phân nhóm theo ngày
        days_dict = {}
        for poi in final_pois:
            d = poi.get("day_cluster", 1)
            if d > num_days:
                d = ((d - 1) % num_days) + 1
            if d not in days_dict:
                days_dict[d] = []
            days_dict[d].append(poi)

        days_list = []
        time_slots = ["08:00", "11:30", "15:30", "19:00"]
        # Bộ ảnh chủ đề chất lượng cao theo đúng thể loại địa điểm (Ẩm thực, Biển, Danh lam, Thiên nhiên, Văn hóa)
        theme_images = {
            "dining": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80",
            "beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80",
            "sightseeing": "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=600&q=80",
            "nature": "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=600&q=80",
            "nightlife": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80",
            "cultural": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=600&q=80"
        }

        for d in range(1, num_days + 1):
            pois_for_day = days_dict.get(d, [])
            activities = []
            for idx, p in enumerate(pois_for_day[:4]):
                time_val = time_slots[idx] if idx < len(time_slots) else "09:00"
                name_val = p.get("name", f"Điểm tham quan {idx+1}")
                info_val = p.get("info", "")
                parts = info_val.split(";")
                desc_val = parts[2] if len(parts) > 2 else (p.get("description") or f"Khám phá nét đẹp đặc sắc tại {name_val}")
                
                # Gán ảnh động theo thể loại
                cat_lower = (p.get("category", "") + " " + info_val).lower()
                if "ăn" in cat_lower or "nhà hàng" in cat_lower or "quán" in cat_lower or "bún" in cat_lower:
                    img_url = theme_images["dining"]
                elif "biển" in cat_lower or "bãi" in cat_lower or "đảo" in cat_lower:
                    img_url = theme_images["beach"]
                elif "bar" in cat_lower or "pub" in cat_lower or "chợ đêm" in cat_lower:
                    img_url = theme_images["nightlife"]
                elif "núi" in cat_lower or "rừng" in cat_lower or "thác" in cat_lower:
                    img_url = theme_images["nature"]
                elif "chùa" in cat_lower or "bảo tàng" in cat_lower or "di tích" in cat_lower:
                    img_url = theme_images["cultural"]
                else:
                    img_url = theme_images["sightseeing"]

                activities.append({
                    "time": time_val,
                    "title": name_val,
                    "desc": desc_val.strip(),
                    "lat": p.get("lat", 0.0),
                    "lng": p.get("lon", 0.0),
                    "category": p.get("category", "Khám phá"),
                    "img": p.get("image_url") or img_url
                })

            days_list.append({
                "dayNum": d,
                "title": f"Ngày {d}: Khám phá điểm đến & ẩm thực {dest}",
                "subtitle": f"{len(activities)} địa điểm gợi ý theo RAG Engine",
                "activities": activities
            })

        # Chi phí ước tính
        cost_map = {
            "Tiết kiệm": ("1.500.000 VNĐ / người", "Homestay: 600k • Ẩm thực: 500k • Vé & xe: 400k"),
            "Tiêu chuẩn": ("2.850.000 VNĐ / người", "Khách sạn 3*: 1.200k • Ăn uống: 950k • Vé & xe: 700k"),
            "Sang trọng": ("5.200.000 VNĐ / người", "Resort 4-5*: 2.800k • Nhà hàng cao cấp: 1.500k • Tour VIP: 900k"),
        }
        cost_val, cost_desc = cost_map.get(budget, cost_map["Tiêu chuẩn"])

        return {
            "destination": dest,
            "title": f"Lịch Trình Chi Tiết • {dest} ({num_days}N{max(1, num_days-1)}Đ)",
            "subtitle": f"AI & RAG Engine đã tối ưu hóa {len(final_pois)} địa điểm thực tế và cung đường di chuyển.",
            "cost": cost_val,
            "costDetails": cost_desc,
            "days": days_list
        }

    def find_exact_location(self, name: str) -> Optional[Dict[str, Any]]:
        """Tìm tọa độ chính xác của địa điểm theo tên"""
        if not self.loaded:
            self.load_index()

        if not name or not self.locations:
            return None

        clean_name = name.lower().strip()
        for loc in self.locations:
            loc_name = loc.get("name", "").lower()
            if clean_name in loc_name or loc_name in clean_name:
                if "lat" in loc and loc["lat"] != 0.0:
                    return {"lat": loc["lat"], "lon": loc["lon"], "name": loc["name"]}

        return None

