"""
ai_engine/intent_router.py
Module phân loại Ý định (Intent Classification) và Trích xuất Thực thể/Slots (Slot Extraction)
Tối ưu hóa siêu nhanh (< 2ms) cho Chatbot Tư vấn Du lịch BeeNavi AI.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

VIETNAM_DESTINATIONS = [
    "đà nẵng", "da nang", "hà nội", "ha noi", "hồ chí minh", "ho chi minh", "sài gòn", "saigon",
    "đà lạt", "da lat", "nha trang", "phú quốc", "phu quoc", "sa pa", "sapa", "huế", "hue",
    "hội an", "hoi an", "hạ long", "ha long", "ninh bình", "ninh binh", "vũng tàu", "vung tau",
    "quy nhơn", "quy nhon", "hải phòng", "hai phong", "cần thơ", "can tho", "hà giang", "ha giang",
    "mộc châu", "moc chau", "phú yên", "phu yen", "quảng bình", "quang binh", "buôn ma thuột",
    "phan thiết", "mũi né", "mui ne", "bảo lộc", "cao bằng", "mai châu", "côn đảo", "lý sơn",
    "ba vì", "tam đảo", "cát bà", "tam cốc", "tràng an", "bà nà", "hòn sơn", "nam du"
]

CANONICAL_DESTINATION_MAP = {
    "da nang": "Đà Nẵng", "đà nẵng": "Đà Nẵng",
    "ha noi": "Hà Nội", "hà nội": "Hà Nội",
    "ho chi minh": "Hồ Chí Minh", "hồ chí minh": "Hồ Chí Minh", "saigon": "Hồ Chí Minh", "sài gòn": "Hồ Chí Minh",
    "da lat": "Đà Lạt", "đà lạt": "Đà Lạt",
    "nha trang": "Nha Trang",
    "phu quoc": "Phú Quốc", "phú quốc": "Phú Quốc",
    "sapa": "Sa Pa", "sa pa": "Sa Pa",
    "hue": "Huế", "huế": "Huế",
    "hoi an": "Hội An", "hội an": "Hội An",
    "ha long": "Hạ Long", "hạ long": "Hạ Long",
    "ninh binh": "Ninh Bình", "ninh bình": "Ninh Bình",
    "vung tau": "Vũng Tàu", "vũng tàu": "Vũng Tàu",
    "quy nhon": "Quy Nhơn", "quy nhơn": "Quy Nhơn",
    "hai phong": "Hải Phòng", "hải phòng": "Hải Phòng",
    "can tho": "Cần Thơ", "cần thơ": "Cần Thơ",
    "ha giang": "Hà Giang", "hà giang": "Hà Giang",
    "moc chau": "Mộc Châu", "mộc châu": "Mộc Châu",
    "phu yen": "Phú Yên", "phú yên": "Phú Yên",
    "quang binh": "Quảng Bình", "quảng bình": "Quảng Bình",
    "phan thiet": "Phan Thiết", "phan thiết": "Phan Thiết",
    "mui ne": "Mũi Né", "mũi né": "Mũi Né",
    "con dao": "Côn Đảo", "côn đảo": "Côn Đảo",
    "ly son": "Lý Sơn", "lý sơn": "Lý Sơn",
    "tam dao": "Tam Đảo", "tam đảo": "Tam Đảo",
    "cat ba": "Cát Bà", "cát bà": "Cát Bà",
    "ba vi": "Ba Vì", "ba vì": "Ba Vì",
}


class IntentRouter:
    """Bộ định tuyến ý định và bóc tách slots cho Chatbot tư vấn du lịch."""

    @staticmethod
    def extract_slots(text: str) -> Dict[str, Any]:
        slots: Dict[str, Any] = {}
        lower = text.lower()

        # 1. Trích xuất Cặp Origin -> Destination (Ví dụ: Từ Hà Nội đi Ninh Bình bao xa)
        pair_match = re.search(r'(?:từ|xuất phát từ|khởi hành từ|đi từ)\s+([A-ZÀ-Ỹa-zà-ỹ\s]+?)\s+(?:đi|đến|vào|ra|sang|tới)\s+([A-ZÀ-Ỹa-zà-ỹ\s]+?)(?:\s+(?:bao xa|bao nhiêu|hết|mất|bằng|như thế nào|thế nào|\?|$))', text, re.IGNORECASE)
        if pair_match:
            orig_raw = pair_match.group(1).strip().lower()
            dest_raw = pair_match.group(2).strip().lower()

            for dest in VIETNAM_DESTINATIONS:
                if dest in orig_raw and not slots.get("origin"):
                    slots["origin"] = CANONICAL_DESTINATION_MAP.get(dest, dest.title())
                if dest in dest_raw and not slots.get("destination"):
                    slots["destination"] = CANONICAL_DESTINATION_MAP.get(dest, dest.title())

            if not slots.get("origin") and len(orig_raw) >= 2:
                slots["origin"] = orig_raw.title()
            if not slots.get("destination") and len(dest_raw) >= 2:
                slots["destination"] = dest_raw.title()

        # 1.1. Nếu chưa có Destination: Tìm theo từ điển điểm đến
        if not slots.get("destination"):
            for dest in VIETNAM_DESTINATIONS:
                pattern = r'\b' + re.escape(dest) + r'\b'
                if re.search(pattern, lower):
                    slots["destination"] = CANONICAL_DESTINATION_MAP.get(dest, dest.title())
                    break

        if not slots.get("destination"):
            loc_match = re.search(r'(?:đi|đến|ở|tại|khám phá|du lịch|thăm|tới)\s+([A-ZÀ-Ỹa-zà-ỹ\s]{2,20})(?:\s+(?:\d+|ngày|đêm|vào|cho|với|mức|giá|tiết kiệm|sang trọng|tiêu chuẩn|$))', text)
            if loc_match:
                candidate = loc_match.group(1).strip()
                cand_lower = candidate.lower()
                stop_words = [
                    "tôi", "cho tôi", "mình", "gia đình", "bạn bè", "người yêu", "chơi", 
                    "đâu", "nghỉ", "kế hoạch", "tự túc", "tiết kiệm", "sang trọng", "tiêu chuẩn",
                    "hè", "tết", "cuối tuần", "du lịch", "chuyến đi", "tour", "phượt", "nghỉ mát", "đâu đó"
                ]
                if (not any(sw == cand_lower for sw in stop_words) 
                    and not re.search(r'\d', cand_lower) 
                    and not re.search(r'\b(ngày|đêm|tuần|tháng|mức)\b', cand_lower) 
                    and len(candidate) >= 2):
                    slots["destination"] = candidate.title()

        # 1.2. Nếu chưa có Origin: Tìm từ khóa xuất phát
        if not slots.get("origin"):
            origin_match = re.search(r'(?:từ|xuất phát từ|khởi hành từ|đi từ)\s+([A-ZÀ-Ỹa-zà-ỹ\s]{2,20})(?:\s+(?:đến|đi|vào|ra|sang|tới|hết|\d+|$))', text)
            if origin_match:
                orig_cand = origin_match.group(1).strip().lower()
                for dest in VIETNAM_DESTINATIONS:
                    if dest in orig_cand:
                        slots["origin"] = CANONICAL_DESTINATION_MAP.get(dest, dest.title())
                        break
                if not slots.get("origin") and len(orig_cand) >= 2:
                    slots["origin"] = orig_cand.title()

        # 2. Trích xuất Số ngày (num_days)
        days_match = re.search(r'(\d+)\s*(?:ngày|ngay|n)\s*(?:(\d+)\s*(?:đêm|dem|d))?', lower)
        if days_match:
            try:
                days = int(days_match.group(1))
                if 1 <= days <= 30:
                    slots["num_days"] = days
                    slots["number_of_days"] = days
            except Exception:
                pass
        elif "1 tuần" in lower or "một tuần" in lower:
            slots["num_days"] = 7
        elif "cuối tuần" in lower:
            slots["num_days"] = 2

        # 3. Trích xuất Số người (num_people)
        people_match = re.search(r'(\d+)\s*(?:người|bạn|thành viên|khách)', lower)
        if people_match:
            try:
                slots["num_people"] = int(people_match.group(1))
            except Exception:
                pass

        # 4. Trích xuất Ngân sách (budget)
        if any(w in lower for w in ["tiết kiệm", "giá rẻ", "rẻ", "ít tiền", "bình dân", "budget", "sinh viên"]):
            slots["budget"] = "Tiết kiệm"
        elif any(w in lower for w in ["sang trọng", "cao cấp", "luxury", "5 sao", "resort", "xịn"]):
            slots["budget"] = "Sang trọng"
        elif any(w in lower for w in ["tiêu chuẩn", "vừa phải", "hợp lý", "tầm trung"]):
            slots["budget"] = "Tiêu chuẩn"

        # 5. Trích xuất Phương tiện (transport)
        if any(w in lower for w in ["máy bay", "flight", "vé bay"]):
            slots["transport"] = "Máy bay"
        elif any(w in lower for w in ["xe máy", "phượt xe máy", "thuê xe máy"]):
            slots["transport"] = "Xe máy"
        elif any(w in lower for w in ["ô tô", "xe hơi", "tự lái", "xe khách", "limousine"]):
            slots["transport"] = "Ô tô"
        elif any(w in lower for w in ["tàu hỏa", "tàu hoả", "xe lửa"]):
            slots["transport"] = "Tàu hỏa"

        # 6. Trích xuất Phong cách du lịch (trip_type)
        if any(w in lower for w in ["nghỉ dưỡng", "thư giãn", "relax", "chill"]):
            slots["trip_type"] = "Nghỉ dưỡng"
        elif any(w in lower for w in ["khám phá", "trải nghiệm", "phượt", "trekking", "leo núi"]):
            slots["trip_type"] = "Khám phá"
        elif any(w in lower for w in ["ẩm thực", "ăn uống", "food", "ăn sập", "quán ngon"]):
            slots["trip_type"] = "Ẩm thực"
        elif any(w in lower for w in ["chụp ảnh", "sống ảo", "check-in", "check in"]):
            slots["trip_type"] = "Sống ảo & Check-in"
        elif any(w in lower for w in ["biển", "tắm biển", "đảo", "hải sản"]):
            slots["trip_type"] = "Biển"

        # 7. Trích xuất Sở thích / Dị ứng ăn uống (dietary / preference)
        if "ăn chay" in lower:
            slots["dietary_restrictions"] = ["Ăn chay"]
        elif "dị ứng hải sản" in lower or "không ăn hải sản" in lower:
            slots["dietary_restrictions"] = ["Dị ứng hải sản"]
        elif "không ăn cay" in lower:
            slots["dietary_restrictions"] = ["Không ăn cay"]

        return slots

    @classmethod
    def classify_intent(cls, text: str, current_slots: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any], float]:
        """
        Phân loại Intent tư vấn chuyên biệt cho Chatbot và gộp Slots ngữ cảnh.
        Trả về (intent_name, extracted_slots, confidence)
        """
        lower = text.lower().strip()
        extracted_slots = cls.extract_slots(text)

        # Gộp slot từ ngữ cảnh trước đó nếu có
        merged_slots = dict(current_slots or {})
        merged_slots.update(extracted_slots)

        # 1. Intent: USER_PREFERENCE_UPDATE (Cập nhật sở thích/khẩu vị cá nhân)
        pref_keywords = ["ăn chay", "dị ứng", "sở thích", "khẩu vị", "thích đi", "không thích", "tôi thích", "gu du lịch"]
        if any(w in lower for w in pref_keywords) and not any(w in lower for w in ["quán nào", "chỗ nào", "ở đâu", "giá bao nhiêu"]):
            return "USER_PREFERENCE_UPDATE", extracted_slots, 0.95

        # 2. Intent: CHECK_WEATHER (Hỏi thời tiết)
        weather_keywords = ["thời tiết", "trời mưa", "trời nắng", "nhiệt độ", "dự báo thời tiết", "có lạnh không", "mùa này thời tiết", "có bão không", "mưa không"]
        if any(w in lower for w in weather_keywords):
            return "CHECK_WEATHER", extracted_slots, 0.95

        # 3. Intent: ASK_DISTANCE_TRANSPORT (Hỏi khoảng cách, phương tiện, cách di chuyển)
        distance_keywords = [
            "cách bao xa", "bao xa", "bao nhiêu km", "cự ly", "khoảng cách", "đi từ",
            "mất bao lâu", "đi bằng gì", "xe gì", "phương tiện di chuyển", "đường đi"
        ]
        if any(w in lower for w in distance_keywords):
            return "ASK_DISTANCE_TRANSPORT", extracted_slots, 0.95

        # 4. Intent: ASK_BUDGET_COST (Hỏi chi phí, giá vé, dự trù ngân sách, hết bao nhiêu tiền)
        budget_keywords = [
            "chi phí", "bao nhiêu tiền", "hết bao nhiêu", "ngân sách", "giá vé", "kinh phí",
            "giá phòng", "tiền ăn", "dự trù", "khoảng bao nhiêu", "chi tiêu"
        ]
        if any(w in lower for w in budget_keywords):
            return "ASK_BUDGET_COST", extracted_slots, 0.95

        # 5. Intent: ASK_CHECKLIST_PACKING (Hỏi cần mang gì, chuẩn bị đồ đạc, hành lý)
        checklist_keywords = [
            "chuẩn bị gì", "mang theo gì", "cần mang những gì", "hành lý", "đồ dùng",
            "mặc đồ gì", "trang phục", "checklist", "đem theo gì", "cần giấy tờ gì"
        ]
        if any(w in lower for w in checklist_keywords):
            return "ASK_CHECKLIST_PACKING", extracted_slots, 0.95

        # 6. Intent: EXPLORE_LOCATION (Hỏi quán ăn, chỗ chơi, danh lam, khách sạn, lộ trình kinh nghiệm du lịch)
        explore_keywords = [
            "ở đâu", "chỗ nào", "quán ăn", "quán ngon", "địa điểm", "ăn gì", "chơi gì",
            "tham quan", "bà nà", "hồ gươm", "chợ đêm", "khách sạn", "đặc sản",
            "có gì đẹp", "có gì chơi", "review", "gợi ý điểm", "khu du lịch", "check-in", "sống ảo",
            "đẹp không", "nên đi đâu", "danh lam", "bãi biển", "lộ trình", "lịch trình", "hành trình",
            "kế hoạch đi", "chuyến đi", "gợi ý lịch", "gợi ý tour"
        ]
        if any(kw in lower for kw in explore_keywords) or (extracted_slots.get("destination") and not any(kw in lower for kw in ["chào", "hi", "hello", "tạm biệt"])):
            return "EXPLORE_LOCATION", extracted_slots, 0.90

        # 7. Intent: GENERAL_TRAVEL_CHAT (Chào hỏi, hỏi đáp chung)
        return "GENERAL_TRAVEL_CHAT", extracted_slots, 0.80
