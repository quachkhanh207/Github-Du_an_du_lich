import re
import math
import random
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

def remove_accents(input_str: str) -> str:
    if not input_str:
        return ""
    s1 = u'ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾếỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ'
    s0 = u'AAAAEEEIIOOOOUUYaaaaeeeiioooouuyAaDdIiUuOoUuAaAaAaAaAaAaAaAaAaAaAaAaEeEeEeEeEeEeEeEeIiIiOoOoOoOoOoOoOoOoOoOoOoOoUuUuUuUuUuUuUuYyYyYyYy'
    s = ""
    for c in input_str:
        if c in s1:
            s += s0[s1.index(c)]
        else:
            s += c
    return s.lower()


class RuleEngineService:
    @staticmethod
    def get_estimated_cost(budget_tier: str) -> float:
        """Ước lượng chi phí cho từng mức giá địa điểm"""
        if budget_tier == "Sang trọng":
            return 800000.0
        elif budget_tier == "Tiêu chuẩn":
            return 250000.0
        else:
            return 80000.0

    @staticmethod
    def _parse_poi_data(poi: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw MD data to structured fields for Hoan's engine"""
        info = poi.get("info", "").lower()
        name_lower = poi.get("name", "").lower()
        raw_cat = poi.get("category", "")
        tags = []
        category = "Other"
        budget_tier = "Tiết kiệm"

        # Bỏ qua các địa điểm không phục vụ mục đích du lịch (cơ quan, trường học, bệnh viện, doanh nghiệp, chung cư, cửa hàng tạp hóa)
        NON_TOURIST_KEYWORDS = [
            "công ty", "cổ phần", "cpxd", "tnhh", "đối diện", "khu nội trú", 
            "trung cấp nghề", "trung cấp", "cao đẳng", "đại học", "học viện", 
            "ubnd", "công an", "trụ sở", "hội đồng", "nghĩa trang", "nội trú", "bộ tư lệnh", "đặc công", "quân đội", "chung cư", "tập thể",
            "trường thpt", "trường thcs", "trường mầm non", "tiểu học", "bệnh viện", "phòng khám", "qua 100m", "winmart", "circle k", "tạp hóa"
        ]
        if raw_cat in ["education_knowledge", "medical_emergency"] or any(kw in name_lower or kw in info for kw in NON_TOURIST_KEYWORDS):
            return {"is_invalid": True, "name": poi.get("name", ""), "tags": []}
        
        if "nhà hàng" in info or "quán ăn" in info or "đặc sản" in info or raw_cat == "dining_coffee":
            category = "Dining"
        elif "khu di tích" in info or "bảo tàng" in info or "chùa" in info or raw_cat in ["spiritual_culture", "tourism_heritage", "Khám phá"]:
            category = "Khám phá"
        elif "chợ" in info or "siêu thị" in info or raw_cat == "leisure_shopping":
            category = "Shopping"
        elif "bar" in info or "pub" in info or "chợ đêm" in info:
            category = "Nightlife"
        elif raw_cat == "lodging":
            category = "Lodging"
            
        if "view đẹp" in info or "check-in" in info or "sống ảo" in info:
            tags.append("chụp ảnh")
            tags.append("view đẹp")
            
        if "leo núi" in info or "đi bộ" in info or "vận động" in info:
            tags.append("is_strenuous")
            
        if "nhà hàng" in category and ("hải sản" in info):
            tags.append("hải sản")
            
        if "xe lăn" in info:
            tags.append("wheelchair")
            
        return {
            "name": poi.get("name", ""),
            "lat": poi.get("lat", 0.0),
            "lon": poi.get("lon", 0.0),
            "category": category,
            "tags": tags,
            "budget_tier": budget_tier,
            "raw_poi": poi
        }

    @classmethod
    def filter_candidate_pois(cls, trip_data: Dict[str, Any], raw_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        filtered: List[Dict[str, Any]] = []
        
        destination = trip_data.get("destination", "").strip()
        dest_no_accent = remove_accents(destination)
        
        # Lọc sơ bộ theo Điểm đến (Destination) nếu có
        pool = raw_candidates
        if dest_no_accent:
            dest_matches = []
            for raw_poi in raw_candidates:
                poi_text = remove_accents(raw_poi.get("raw", "") + " " + raw_poi.get("info", "") + " " + raw_poi.get("name", ""))
                if dest_no_accent in poi_text:
                    dest_matches.append(raw_poi)
            if len(dest_matches) >= 5:
                pool = dest_matches
        
        must_avoid = [remove_accents(p) for p in trip_data.get("must_avoid_places", [])]
        must_visit = [remove_accents(p) for p in trip_data.get("must_visit_places", [])]
        dining_constraints = [remove_accents(d) for d in trip_data.get("dining_constraints", [])]
        
        special_members = trip_data.get("special_members", [])
        has_strenuous_limit = any(m in ["người già", "trẻ nhỏ", "phụ nữ mang thai"] for m in special_members)
        
        for raw_poi in pool:
            poi = cls._parse_poi_data(raw_poi)
            if poi.get("is_invalid"):
                continue
            name_no_accent = remove_accents(poi.get("name", ""))
            
            # 1. Ràng buộc tránh địa điểm cụ thể
            if any(avoid in name_no_accent for avoid in must_avoid) and must_avoid:
                continue
                
            # 2. Sức khỏe
            if has_strenuous_limit and "is_strenuous" in poi["tags"]:
                if not any(mv in name_no_accent for mv in must_visit):
                    continue
                    
            # 3. Dị ứng
            is_dining_conflict = False
            for constraint in dining_constraints:
                if constraint in poi["tags"]:
                    is_dining_conflict = True
                    break
            if is_dining_conflict and not any(mv in name_no_accent for mv in must_visit):
                continue

            filtered.append(poi)
            
        return filtered

    @staticmethod
    def score_pois(trip_data: Dict[str, Any], filtered_pois: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
        scored_list: List[Tuple[Dict[str, Any], float]] = []
        
        trip_objective = trip_data.get("trip_objective", "")
        photography_pref = trip_data.get("photography_preference", "")
        shopping_interest = trip_data.get("shopping_interest", "")
        nightlife_pref = trip_data.get("nightlife_preference", "")
        must_visit = [remove_accents(p) for p in trip_data.get("must_visit_places", [])]

        for poi in filtered_pois:
            score = 100.0
            poi_tags = poi["tags"]
            poi_category = poi["category"]
            name_no_accent = remove_accents(poi["name"])
            
            if any(mv in name_no_accent for mv in must_visit) and must_visit:
                score += 500.0
            
            if trip_objective == "Nghỉ dưỡng" and poi_category == "Other":
                score += 40.0
            elif trip_objective == "Khám phá" and poi_category == "Khám phá":
                score += 40.0
            elif trip_objective == "Chụp ảnh sống ảo" and "chụp ảnh" in poi_tags:
                score += 40.0
            elif trip_objective == "Ẩm thực" and poi_category == "Dining":
                score += 40.0

            if photography_pref == "Đam mê sống ảo" and ("chụp ảnh" in poi_tags or "view đẹp" in poi_tags):
                score += 30.0

            if shopping_interest and (poi_category == "Shopping"):
                score += 30.0

            if nightlife_pref and (poi_category == "Nightlife"):
                score += 40.0

            scored_list.append((poi["raw_poi"], score))
            
        scored_list.sort(key=lambda x: x[1], reverse=True)
        return scored_list

    @staticmethod
    def k_means_clustering(pois: List[Dict[str, Any]], k: int, max_iters: int = 10) -> List[List[Dict[str, Any]]]:
        if not pois: return [[] for _ in range(k)]
        if len(pois) <= k:
            return [[p] for p in pois] + [[] for _ in range(k - len(pois))]
            
        # Init centroids randomly
        centroids = random.sample([(p["lat"], p["lon"]) for p in pois], k)
        clusters = [[] for _ in range(k)]
        
        for _ in range(max_iters):
            clusters = [[] for _ in range(k)]
            for p in pois:
                distances = [math.dist((p["lat"], p["lon"]), c) for c in centroids]
                closest_idx = distances.index(min(distances))
                clusters[closest_idx].append(p)
                
            # Update centroids
            new_centroids = []
            for cluster in clusters:
                if not cluster:
                    # random point if empty
                    new_centroids.append(random.choice([(p["lat"], p["lon"]) for p in pois]))
                else:
                    avg_lat = sum(p["lat"] for p in cluster) / len(cluster)
                    avg_lon = sum(p["lon"] for p in cluster) / len(cluster)
                    new_centroids.append((avg_lat, avg_lon))
            centroids = new_centroids
            
        return clusters

    @classmethod
    def generate_final_candidates(cls, trip_data: Dict[str, Any], raw_pois: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # 1. Hard Filter
        filtered = cls.filter_candidate_pois(trip_data, raw_pois)
        if not filtered:
            filtered = [cls._parse_poi_data(p) for p in raw_pois]
            
        # 2. Soft Scoring
        scored = cls.score_pois(trip_data, filtered)
        
        # Take top 50 (or max available)
        top_pois = [item[0] for item in scored[:50]]
        
        # 3. Geo-Clustering
        days = int(trip_data.get("number_of_days", 1))
        clusters = cls.k_means_clustering(top_pois, k=days)
        
        final_list = []
        for i, cluster in enumerate(clusters):
            # Sort cluster by score (approximated by preserving order from top_pois)
            cluster_sorted = sorted(cluster, key=lambda p: top_pois.index(p))
            # Take top 6 from this cluster for this day to prevent Context Overflow on large days
            selected_for_day = cluster_sorted[:6]
            
            # --- Greedy TSP Sort to avoid zig-zag routing ---
            if selected_for_day:
                tsp_sorted = [selected_for_day.pop(0)]
                while selected_for_day:
                    last_point = tsp_sorted[-1]
                    nearest = min(selected_for_day, key=lambda p: (p["lat"] - last_point["lat"])**2 + (p["lon"] - last_point["lon"])**2)
                    tsp_sorted.append(nearest)
                    selected_for_day.remove(nearest)
                selected_for_day = tsp_sorted
            
            # Time allocation tag for AI hint
            for idx, p in enumerate(selected_for_day):
                time_hint = "Sáng" if idx < 2 else "Chiều" if idx < 4 else "Tối"
                p["time_hint"] = time_hint
                p["day_cluster"] = i + 1
            final_list.extend(selected_for_day)
            
        return final_list

    @classmethod
    def generate_smart_checklist(
        cls,
        weather_tag: str = "Nắng",
        temp: float = 28.0,
        num_days: int = 3,
        trip_type: str = "Khám phá"
    ) -> List[Dict[str, Any]]:
        """Sinh danh sách hành trang thông minh dựa trên điều kiện thời tiết thực tế và tính chất chuyến đi."""
        checklist: List[Dict[str, Any]] = [
            {"item_name": "CCCD / Hộ chiếu bản gốc", "category": "Giấy tờ", "priority": "Bắt buộc"},
            {"item_name": "Vé máy bay / Tàu / Mã đặt phòng", "category": "Giấy tờ", "priority": "Bắt buộc"},
            {"item_name": "Sạc dự phòng & Cáp sạc đa năng", "category": "Điện tử", "priority": "Bắt buộc"},
            {"item_name": f"{num_days + 1} bộ trang phục phù hợp", "category": "Trang phục", "priority": "Bắt buộc"},
            {"item_name": "Thuốc hạ sốt, băng gạc & men tiêu hóa", "category": "Y tế", "priority": "Ưu tiên"}
        ]

        # 1. Theo thời tiết
        w_lower = weather_tag.lower()
        if "mưa" in w_lower or "ẩm" in w_lower:
            checklist.extend([
                {"item_name": "Ô dù gấp mini bỏ túi", "category": "Thời tiết", "priority": "Ưu tiên"},
                {"item_name": "Áo mưa mỏng cá nhân", "category": "Thời tiết", "priority": "Khuyên dùng"},
                {"item_name": "Túi bọc chống nước cho điện thoại", "category": "Bảo vệ", "priority": "Khuyên dùng"}
            ])
        elif "lạnh" in w_lower or temp < 20:
            checklist.extend([
                {"item_name": "Áo khoác giữ nhiệt / Áo ấm dày", "category": "Trang phục", "priority": "Bắt buộc"},
                {"item_name": "Khăn quàng cổ & Găng tay len", "category": "Trang phục", "priority": "Ưu tiên"},
                {"item_name": "Kem dưỡng ẩm & Son dưỡng môi", "category": "Cá nhân", "priority": "Khuyên dùng"}
            ])
        elif "nắng" in w_lower or temp >= 30:
            checklist.extend([
                {"item_name": "Kem chống nắng SPF 50+ & Kính mát", "category": "Chống nắng", "priority": "Bắt buộc"},
                {"item_name": "Mũ rộng vành / Nón lưỡi trai", "category": "Trang phục", "priority": "Ưu tiên"},
                {"item_name": "Bình nước cá nhân giữ lạnh", "category": "Cá nhân", "priority": "Khuyên dùng"}
            ])

        # 2. Theo phong cách chuyến đi
        t_lower = trip_type.lower()
        if "biển" in t_lower or "nghỉ dưỡng" in t_lower:
            checklist.extend([
                {"item_name": "Đồ bơi & Kính bơi", "category": "Hoạt động", "priority": "Ưu tiên"},
                {"item_name": "Dép sandal / Xỏ ngón đi biển", "category": "Trang phục", "priority": "Ưu tiên"}
            ])
        elif "khám phá" in t_lower or "trekking" in t_lower or "phượt" in t_lower:
            checklist.extend([
                {"item_name": "Giày thể thao êm chân chống trơn trượt", "category": "Trang phục", "priority": "Bắt buộc"},
                {"item_name": "Xịt chống muỗi & Côn trùng", "category": "Y tế", "priority": "Ưu tiên"}
            ])
        elif "ẩm thực" in t_lower or "food" in t_lower:
            checklist.extend([
                {"item_name": "Men vi sinh đường ruột & Trà gừng", "category": "Y tế", "priority": "Ưu tiên"},
                {"item_name": "Khăn ướt kháng khuẩn cá nhân", "category": "Cá nhân", "priority": "Khuyên dùng"}
            ])

        return checklist

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Tính khoảng cách địa lý theo đường chim bay (km) giữa 2 tọa độ GPS."""
        R = 6371.0  # Bán kính Trái Đất (km)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @classmethod
    def calculate_budget_breakdown(
        cls,
        departure: str = "Hà Nội",
        destination: str = "Đà Nẵng",
        num_days: int = 3,
        budget_tier: str = "Tiêu chuẩn",
        trip_type: str = "Khám phá"
    ) -> Dict[str, Any]:
        """Tính toán và phân bổ chi phí chi tiết theo khoảng cách địa lý và hạng mức thực tế."""
        num_nights = max(1, num_days - 1)

        # 1. Tra cứu tọa độ thực tế để tính khoảng cách
        is_local_tour = False
        if not departure or departure.lower() in ["tại chỗ", "city tour", "tại điểm đến"] or remove_accents(departure) == remove_accents(destination):
            is_local_tour = True
            distance_km = 0.0
        else:
            try:
                from geo_services.weather_service import find_destination_coordinates
                dep_coords = find_destination_coordinates(departure)
                dest_coords = find_destination_coordinates(destination)
                distance_km = cls.haversine_distance_km(
                    dep_coords["lat"], dep_coords["lon"],
                    dest_coords["lat"], dest_coords["lon"]
                )
            except Exception:
                distance_km = 0.0  # Mặc định không áp vé máy bay nếu không rõ điểm đi

        # 2. Định mức chi phí lưu trú, ăn uống, di chuyển nội thành
        if budget_tier == "Sang trọng":
            hotel_per_night = 2500000.0
            food_per_day = 1200000.0
            local_transport_day = 450000.0
            sightseeing_day = 600000.0
            base_flight_rate = 3500000.0
        elif budget_tier == "Tiết kiệm":
            hotel_per_night = 400000.0
            food_per_day = 250000.0
            local_transport_day = 120000.0
            sightseeing_day = 150000.0
            base_flight_rate = 1400000.0
        else:  # Tiêu chuẩn
            hotel_per_night = 900000.0
            food_per_day = 550000.0
            local_transport_day = 220000.0
            sightseeing_day = 350000.0
            base_flight_rate = 2200000.0

        # 3. Tính chi phí di chuyển liên tỉnh dựa theo cự ly thực tế (km)
        if is_local_tour or distance_km == 0:
            intercity_transport = 0.0
            transport_mode = "Tự túc di chuyển / Khởi hành tại chỗ"
            trans_category_name = f"Di chuyển nội thành ({destination})"
        elif distance_km < 80:
            intercity_transport = 150000.0
            transport_mode = "Xe máy / Xe bus nội tỉnh"
            trans_category_name = f"Di chuyển ({departure} ⇄ {destination})"
        elif distance_km < 350:
            intercity_transport = 450000.0 if budget_tier == "Tiết kiệm" else (700000.0 if budget_tier == "Tiêu chuẩn" else 1500000.0)
            transport_mode = "Xe Limousine / Tàu hỏa khứ hồi"
            trans_category_name = f"Di chuyển ({departure} ⇄ {destination})"
        elif distance_km < 700:
            intercity_transport = 800000.0 if budget_tier == "Tiết kiệm" else (1600000.0 if budget_tier == "Tiêu chuẩn" else 2800000.0)
            transport_mode = "Vé xe giường nằm / Tàu hỏa / Máy bay khứ hồi"
            trans_category_name = f"Di chuyển ({departure} ⇄ {destination})"
        else:
            intercity_transport = base_flight_rate
            transport_mode = "Vé máy bay khứ hồi"
            trans_category_name = f"Di chuyển ({departure} ⇄ {destination})"

        hotel_total = hotel_per_night * num_nights
        food_total = food_per_day * num_days
        local_trans_total = local_transport_day * num_days
        sightseeing_total = sightseeing_day * num_days
        contingency = (hotel_total + food_total + local_trans_total + sightseeing_total) * 0.10  # 10% dự phòng

        total_cost = intercity_transport + hotel_total + food_total + local_trans_total + sightseeing_total + contingency

        breakdown = {
            "budget_tier": budget_tier,
            "total_estimated": round(total_cost),
            "currency": "VNĐ",
            "categories": [
                {
                    "name": trans_category_name,
                    "amount": round(intercity_transport),
                    "desc": f"{transport_mode} (Khoảng cách ~{round(distance_km)}km)"
                },
                {
                    "name": f"Lưu trú khách sạn ({num_nights} đêm)",
                    "amount": round(hotel_total),
                    "desc": f"{round(hotel_per_night):,}đ/đêm"
                },
                {
                    "name": f"Ăn uống & Đặc sản ({num_days} ngày)",
                    "amount": round(food_total),
                    "desc": f"{round(food_per_day):,}đ/ngày (3 bữa + ăn vặt)"
                },
                {
                    "name": f"Di chuyển nội thành ({num_days} ngày)",
                    "amount": round(local_trans_total),
                    "desc": "Thuê xe máy / Taxi / Grab di chuyển giữa các điểm"
                },
                {
                    "name": f"Vé tham quan & Trải nghiệm",
                    "amount": round(sightseeing_total),
                    "desc": "Vé vào cổng danh lam thắng cảnh, cáp treo, giải trí"
                },
                {
                    "name": "Quỹ dự phòng & Phát sinh (10%)",
                    "amount": round(contingency),
                    "desc": "Chi tiêu phát sinh, mua quà lưu niệm"
                }
            ],
            "formatted_summary": f"Tổng dự toán: ~{round(total_cost):,} VNĐ/người (Mức {budget_tier})"
        }
        return breakdown


# Alias backward-compatible với các module cũ dùng tên BeeNaviRuleEngine
BeeNaviRuleEngine = RuleEngineService
