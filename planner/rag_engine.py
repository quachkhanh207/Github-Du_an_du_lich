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
        cat = (poi.get('category', '') + ' ' + (poi.get('sub_category') or '') + ' ' + (poi.get('description') or '')).lower()
        if any(kw in cat for kw in ['restaurant', 'food', 'ăn', 'quán', 'nhà hàng', 'bún', 'cơm', 'phở', 'ẩm thực', 'lẩu', 'nướng']):
            if not lunch:
                lunch.append(poi)
            else:
                evening.append(poi)
        elif any(kw in cat for kw in ['bar', 'pub', 'nightlife', 'đêm', 'chợ đêm', 'phố đi bộ']):
            evening.append(poi)
        elif any(kw in cat for kw in ['beach', 'biển', 'bãi tắm', 'đảo', 'hoàng hôn']):
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
    if poi.get("image_url") and poi["image_url"].startswith("http"):
        return poi["image_url"]

    photo_pools = {
        "coffee": [
            "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&w=600&q=80"
        ],
        "dining": [
            "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=600&q=80"
        ],
        "beach": [
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1519046904884-53103b34b206?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=600&q=80"
        ],
        "nature": [
            "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=600&q=80"
        ],
        "cultural": [
            "https://images.unsplash.com/photo-1548625361-125026723b72?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?auto=format&fit=crop&w=600&q=80"
        ],
        "nightlife": [
            "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=600&q=80"
        ]
    }
    name_desc = (poi.get("name", "") + " " + (poi.get("category") or "") + " " + (poi.get("description") or "")).lower()

    if "cafe" in name_desc or "cà phê" in name_desc or "coffee" in name_desc or "trà" in name_desc:
        pool = photo_pools["coffee"]
    elif any(k in name_desc for k in ["ăn", "quán", "nhà hàng", "bún", "phở", "cơm", "lẩu", "nướng", "hải sản", "food"]):
        pool = photo_pools["dining"]
    elif any(k in name_desc for k in ["biển", "bãi", "đảo", "vịnh", "hải đăng", "lặn"]):
        pool = photo_pools["beach"]
    elif any(k in name_desc for k in ["núi", "rừng", "thác", "săn mây", "đèo", "thung lũng", "suối", "vườn"]):
        pool = photo_pools["nature"]
    elif any(k in name_desc for k in ["chùa", "bảo tàng", "di tích", "lăng", "đền", "tháp", "phố cổ", "nhà thờ"]):
        pool = photo_pools["cultural"]
    elif any(k in name_desc for k in ["bar", "pub", "chợ đêm", "phố đi bộ", "night"]):
        pool = photo_pools["nightlife"]
    else:
        pool = photo_pools["cultural"]

    idx = abs(hash(poi.get("name", ""))) % len(pool)
    return pool[idx]

def calculate_dynamic_cost(num_days: int, budget_tier: str = "Tiêu chuẩn") -> tuple:
    """Tính toán chi phí du lịch động nhân theo số ngày, đêm và phân hạng ngân sách"""
    num_nights = max(1, num_days - 1)
    tier_lower = (budget_tier or "Tiêu chuẩn").lower()

    if "tiết kiệm" in tier_lower or "budget" in tier_lower or "re" in tier_lower:
        hotel_per_night = 350000
        food_per_day = 220000
        trans_ticket_per_day = 130000
        hotel_label = f"Homestay ({num_nights} đêm): {hotel_per_night * num_nights // 1000:,.0f}k"
        food_label = f"Ẩm thực ({num_days} ngày): {food_per_day * num_days // 1000:,.0f}k"
        trans_label = f"Vé & Di chuyển: {trans_ticket_per_day * num_days // 1000:,.0f}k"
    elif "sang" in tier_lower or "vip" in tier_lower or "luxury" in tier_lower:
        hotel_per_night = 2200000
        food_per_day = 950000
        trans_ticket_per_day = 600000
        hotel_label = f"Resort 4-5* ({num_nights} đêm): {hotel_per_night * num_nights // 1000:,.0f}k"
        food_label = f"Nhà hàng cao cấp ({num_days} ngày): {food_per_day * num_days // 1000:,.0f}k"
        trans_label = f"Tour & Xe riêng: {trans_ticket_per_day * num_days // 1000:,.0f}k"
    else: # Tiêu chuẩn
        hotel_per_night = 750000
        food_per_day = 450000
        trans_ticket_per_day = 250000
        hotel_label = f"Khách sạn 3* ({num_nights} đêm): {hotel_per_night * num_nights // 1000:,.0f}k"
        food_label = f"Ăn uống ({num_days} ngày): {food_per_day * num_days // 1000:,.0f}k"
        trans_label = f"Vé & Xe: {trans_ticket_per_day * num_days // 1000:,.0f}k"

    total = (hotel_per_night * num_nights) + ((food_per_day + trans_ticket_per_day) * num_days)
    cost_val = f"{total:,.0f} VNĐ / người".replace(",", ".")
    cost_details = f"{hotel_label} • {food_label} • {trans_label}"
    return cost_val, cost_details


class RagEngine:
    def __init__(self, index_path=None):
        self.db_path = DB_PATH
        self.loaded = True
        self.locations = []

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
                    SELECT p.id, p.name, p.category, p.sub_category, p.address, p.lat, p.lon, p.description, p.image_url
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
                            
                # 3. Nếu vẫn quá ít kết quả, thử OR
                if len(rows) < 5:
                    or_q = " OR ".join([f'"{w}"' for w in words[:6]])
                    or_rows = c.execute(query_sql, (or_q, limit)).fetchall()
                    existing_ids = {r['id'] for r in rows}
                    for r in or_rows:
                        if r['id'] not in existing_ids:
                            rows.append(r)
                            existing_ids.add(r['id'])
                            
                rows = rows[:limit]
            else:
                rows = c.execute("SELECT id, name, category, sub_category, address, lat, lon, description, image_url FROM pois LIMIT ?", (limit,)).fetchall()
                
            pois = [dict(r) for r in rows]
            conn.close()
        except Exception as e:
            print(f"[RAG] DB Query error: {e}")
        return pois

    def get_structured_itinerary(self, trip_data: dict) -> dict:
        mode = trip_data.get("mode", "A")
        dest = trip_data.get("destination", "Đà Nẵng")
        budget = trip_data.get("budget", "Tiêu chuẩn")
        
        # CHẾ ĐỘ B: KHÁM PHÁ ĐỊA ĐIỂM CỤ THỂ (Bán kính 2km)
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
                
            cost_val, cost_desc = calculate_dynamic_cost(1, budget)

            return {
                "destination": dest,
                "title": f"Khám phá {dest}",
                "subtitle": f"Bán kính 2km quanh {anchor['name']}",
                "cost": "Tùy chi tiêu (Ước tính ~250.000 VNĐ)",
                "costDetails": "Khoảng cách gần, đi bộ hoặc gọi xe công nghệ",
                "center": [anchor["lat"], anchor["lon"]],
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
        all_lats, all_lngs = [], []

        for d in range(1, num_days + 1):
            pois_for_day = clusters.get(d, [])
            if not pois_for_day:
                continue
                
            # 3. Xếp giờ
            schedule = time_route_day(pois_for_day)
            
            activities = []
            for act in schedule:
                if act.get("lat") and act.get("lon"):
                    all_lats.append(float(act["lat"]))
                    all_lngs.append(float(act["lon"]))

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
            
        # 4. Tính toán chi phí động theo số ngày & phân hạng ngân sách
        cost_val, cost_desc = calculate_dynamic_cost(num_days, budget)

        # 5. Tính toán Centroid trung tâm bản đồ chính xác
        center_coords = [sum(all_lats)/len(all_lats), sum(all_lngs)/len(all_lngs)] if all_lats else [16.068, 108.230]

        return {
            "destination": dest,
            "title": f"Lịch Trình Chi Tiết • {dest} ({num_days}N{max(1, num_days-1)}Đ)",
            "subtitle": f"RAG Engine đã tự động phân cụm địa lý {len(raw_pois)} địa điểm thực tế.",
            "cost": cost_val,
            "costDetails": cost_desc,
            "center": center_coords,
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
