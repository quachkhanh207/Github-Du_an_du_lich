import os
import re
import json
import sqlite3
import math
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

from planner.region_service import detect_data_tier, TIER_FULL, TIER_GENERAL

# Thư mục gốc
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DB_PATH = DATA_DIR / "travel_knowledge.db"

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))
    except:
        return 0.0

def kmeans_cluster(pois, k, max_iter=15):
    valid = [p for p in pois if p.get('lat') and p.get('lon')]
    if not valid:
        return {}
    if k <= 1 or len(valid) <= k:
        return {i+1: valid[i::k] for i in range(k)}
    
    centers = random.sample(valid, k)
    clusters = {i: [] for i in range(k)}
    
    for _ in range(max_iter):
        clusters = {i: [] for i in range(k)}
        for poi in valid:
            dists = [haversine_km(poi['lat'], poi['lon'], c['lat'], c['lon']) for c in centers]
            clusters[dists.index(min(dists))].append(poi)
        
        new_centers = []
        for i in range(k):
            if clusters[i]:
                avg_lat = sum(float(p['lat']) for p in clusters[i]) / len(clusters[i])
                avg_lon = sum(float(p['lon']) for p in clusters[i]) / len(clusters[i])
                new_centers.append({'lat': avg_lat, 'lon': avg_lon})
            else:
                new_centers.append(centers[i])
        centers = new_centers
    
    return {i+1: clusters[i] for i in range(k)}

def time_route_day(pois_for_day, start_time="08:00"):
    morning, lunch, afternoon, evening = [], [], [], []
    for poi in pois_for_day:
        cat = (poi.get('category', '') + ' ' + poi.get('sub_category', '')).lower()
        if any(kw in cat for kw in ['restaurant', 'food', 'ăn', 'quán', 'nhà hàng', 'bún', 'cơm', 'phở', 'ẩm thực']):
            if not lunch:
                lunch.append(poi)
            else:
                evening.append(poi)
        elif any(kw in cat for kw in ['bar', 'pub', 'nightlife', 'đêm']):
            evening.append(poi)
        elif any(kw in cat for kw in ['beach', 'biển', 'bãi tắm', 'đảo']):
            afternoon.append(poi)
        else:
            if len(morning) < 2:
                morning.append(poi)
            elif len(afternoon) < 2:
                afternoon.append(poi)
            else:
                evening.append(poi)
                
    schedule = []
    if morning:
        schedule.append({**morning[0], 'time': '08:00'})
    if len(morning) > 1:
        schedule.append({**morning[1], 'time': '10:00'})
    if lunch:
        schedule.append({**lunch[0], 'time': '12:00'})
    if afternoon:
        schedule.append({**afternoon[0], 'time': '14:30'})
    if len(afternoon) > 1:
        schedule.append({**afternoon[1], 'time': '16:00'})
    if evening:
        schedule.append({**evening[0], 'time': '19:00'})
        
    schedule.sort(key=lambda x: x['time'])
    
    for i in range(len(schedule)):
        if i == 0:
            schedule[i]['distance_from_prev'] = 0.0
        else:
            prev = schedule[i-1]
            curr = schedule[i]
            if prev.get('lat') and prev.get('lon') and curr.get('lat') and curr.get('lon'):
                dist = haversine_km(prev['lat'], prev['lon'], curr['lat'], curr['lon'])
                schedule[i]['distance_from_prev'] = round(dist, 1)
            else:
                schedule[i]['distance_from_prev'] = 0.0
                
    return schedule

def get_theme_img(poi):
    theme_images = {
        "dining": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80",
        "beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80",
        "sightseeing": "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=600&q=80",
        "nature": "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=600&q=80",
        "nightlife": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80",
        "cultural": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=600&q=80"
    }
    cat_lower = (poi.get("category", "") + " " + (poi.get("description") or "")).lower()
    if "ăn" in cat_lower or "nhà hàng" in cat_lower or "quán" in cat_lower or "bún" in cat_lower:
        return theme_images["dining"]
    elif "biển" in cat_lower or "bãi" in cat_lower or "đảo" in cat_lower:
        return theme_images["beach"]
    elif "bar" in cat_lower or "pub" in cat_lower or "chợ đêm" in cat_lower:
        return theme_images["nightlife"]
    elif "núi" in cat_lower or "rừng" in cat_lower or "thác" in cat_lower:
        return theme_images["nature"]
    elif "chùa" in cat_lower or "bảo tàng" in cat_lower or "di tích" in cat_lower:
        return theme_images["cultural"]
    else:
        return theme_images["sightseeing"]

class RagEngine:
    def __init__(self, index_path=None):
        self.db_path = DB_PATH
        self.loaded = True
        self.locations = [] # Giữ lại property này cho các chỗ gọi cũ nếu có

    def load_index(self):
        pass

    def _query_sqlite(self, query_text: str, limit: int = 50):
        if not self.db_path.exists():
            return []
        
        clean_q = re.sub(r"[^\w\s\u00C0-\u1EF9]", " ", query_text)
        words = [w.strip() for w in clean_q.split() if len(w.strip()) > 1]
        
        pois = []
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            if words:
                query_sql = """
                    SELECT p.id, p.name, p.category, p.sub_category, p.address, p.lat, p.lon, p.description
                    FROM pois_fts f
                    JOIN pois p ON f.id = p.id
                    WHERE pois_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """
                # 1. Thử Phrase Match trước (Đúng cụm từ)
                phrase_q = f'"{clean_q.strip()}"'
                rows = c.execute(query_sql, (phrase_q, limit)).fetchall()
                
                # 2. Nếu ít hoặc không có, thử AND match (Phải có đủ các chữ)
                if len(rows) < limit:
                    and_q = " AND ".join([f'"{w}"' for w in words[:6]])
                    and_rows = c.execute(query_sql, (and_q, limit)).fetchall()
                    existing_ids = {r['id'] for r in rows}
                    for r in and_rows:
                        if r['id'] not in existing_ids:
                            rows.append(r)
                            existing_ids.add(r['id'])
                            
                # 3. Nếu vẫn quá ít kết quả (ví dụ truy vấn mở), thử OR
                if len(rows) < 5:
                    or_q = " OR ".join([f'"{w}"' for w in words[:6]])
                    or_rows = c.execute(query_sql, (or_q, limit)).fetchall()
                    existing_ids = {r['id'] for r in rows}
                    for r in or_rows:
                        if r['id'] not in existing_ids:
                            rows.append(r)
                            existing_ids.add(r['id'])
                            
                # Cắt đúng limit
                rows = rows[:limit]
            else:
                rows = c.execute("SELECT id, name, category, sub_category, address, lat, lon, description FROM pois LIMIT ?", (limit,)).fetchall()
                
            pois = [dict(r) for r in rows]
            conn.close()
        except Exception as e:
            print(f"[RAG] DB Query error: {e}")
        return pois

    def get_structured_itinerary(self, trip_data: dict) -> dict:
        mode = trip_data.get("mode", "A")
        dest = trip_data.get("destination", "Đà Nẵng")
        
        # CHẾ ĐỘ B: KHÁM PHÁ ĐỊA ĐIỂM CỤ THỂ
        if mode == "B":
            session_val = trip_data.get("session", "Sáng")
            anchor_pois = self._query_sqlite(dest, limit=1)
            
            if not anchor_pois:
                return {
                    "destination": dest,
                    "title": f"Không tìm thấy {dest}",
                    "subtitle": "Vui lòng thử tên địa điểm khác.",
                    "cost": "N/A", "costDetails": "", "days": []
                }
                
            anchor = anchor_pois[0]
            # Lấy POI xung quanh < 2.0km
            all_pois = self._query_sqlite(dest.split()[0] if len(dest.split()) > 0 else "Hà", limit=200) 
            nearby = []
            for p in all_pois:
                if p['id'] != anchor['id'] and haversine_km(anchor['lat'], anchor['lon'], p['lat'], p['lon']) < 2.0:
                    nearby.append(p)
                    
            selected_pois = [anchor] + nearby[:4]
            schedule = time_route_day(selected_pois, start_time="08:00" if session_val=="Sáng" else "14:00")
            
            activities = []
            for act in schedule:
                activities.append({
                    "time": act["time"],
                    "title": act["name"],
                    "desc": act.get("description") or f"Khám phá {act['name']}",
                    "lat": act["lat"],
                    "lng": act["lon"],
                    "category": act.get("category", "Tham quan"),
                    "img": get_theme_img(act),
                    "distance_from_prev": act.get("distance_from_prev", 0)
                })
                
            return {
                "destination": dest,
                "title": f"Khám phá {dest}",
                "subtitle": f"Bán kính 2km quanh {anchor['name']}",
                "cost": "Tùy chi tiêu",
                "costDetails": "Khoảng cách gần, đi bộ hoặc gọi xe công nghệ",
                "days": [{
                    "dayNum": 1,
                    "title": f"Buổi {session_val} tại {dest}",
                    "activities": activities
                }]
            }

        # CHẾ ĐỘ A: CHUYẾN ĐI NHIỀU NGÀY
        try:
            num_days = int(trip_data.get("num_days", 3))
        except:
            num_days = 3
            
        budget = trip_data.get("budget", "Tiêu chuẩn")
        
        # 1. Truy vấn POIs
        raw_pois = self._query_sqlite(dest, limit=60)
        if not raw_pois:
            return {
                "destination": dest,
                "title": f"Không tìm thấy dữ liệu cho {dest}",
                "subtitle": "Vui lòng nhập tên thành phố phổ biến.", 
                "cost": "", "costDetails": "", "days": []
            }
            
        # 2. Phân cụm K-Means
        clusters = kmeans_cluster(raw_pois, k=num_days)
        
        days_list = []
        for d in range(1, num_days + 1):
            pois_for_day = clusters.get(d, [])
            if not pois_for_day:
                continue
                
            # 3. Xếp giờ
            schedule = time_route_day(pois_for_day)
            
            activities = []
            for act in schedule:
                activities.append({
                    "time": act["time"],
                    "title": act["name"],
                    "desc": act.get("description") or f"Khám phá {act['name']}",
                    "lat": act["lat"],
                    "lng": act["lon"],
                    "category": act.get("category", "Tham quan"),
                    "img": get_theme_img(act),
                    "distance_from_prev": act.get("distance_from_prev", 0)
                })
                
            days_list.append({
                "dayNum": d,
                "title": f"Ngày {d}: Khám phá cụm địa điểm",
                "activities": activities
            })
            
        # Chi phí
        cost_map = {
            "Tiết kiệm": ("1.500.000 VNĐ / người", "Homestay: 600k • Ẩm thực: 500k • Vé & xe: 400k"),
            "Tiêu chuẩn": ("2.850.000 VNĐ / người", "Khách sạn 3*: 1.200k • Ăn uống: 950k • Vé & xe: 700k"),
            "Sang trọng": ("5.200.000 VNĐ / người", "Resort 4-5*: 2.800k • Nhà hàng cao cấp: 1.500k • Tour VIP: 900k"),
        }
        cost_val, cost_desc = cost_map.get(budget, cost_map["Tiêu chuẩn"])

        return {
            "destination": dest,
            "title": f"Lịch Trình Chi Tiết • {dest} ({num_days}N{max(1, num_days-1)}Đ)",
            "subtitle": f"RAG Engine đã tự động phân cụm địa lý {len(raw_pois)} địa điểm",
            "cost": cost_val,
            "costDetails": cost_desc,
            "days": days_list
        }
        
    def query_knowledge(self, query_text: str, limit: int = 6) -> str:
        pois = self._query_sqlite(query_text, limit=limit)
        if not pois: return ""
        context = "\n\n[DỮ LIỆU ĐỊA ĐIỂM DU LỊCH THỰC TẾ TRA CỨU TỪ CSDL]:\n"
        for p in pois:
            context += f"- **{p['name']}** ({p['category']}) | Mô tả: {p['description']}\n"
        return context

    def search_locations(self, trip_data: dict) -> str:
        return ""
    
    def find_exact_location(self, name: str):
        pois = self._query_sqlite(name, limit=1)
        if pois:
            return {"lat": pois[0]["lat"], "lon": pois[0]["lon"], "name": pois[0]["name"]}
        return None
