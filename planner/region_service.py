"""
planner/region_service.py
Xác định vùng dữ liệu hỗ trợ (data tier) cho từng điểm đến.
BeeNavi hiện chỉ có dữ liệu POI thực tế tại Hà Nội; các tỉnh khác dùng kiến thức chung của LLM.
"""

# Vùng dữ liệu POI thực tế (lat/lon box). Chỉ Hà Nội hiện có dữ liệu đầy đủ.
# Mở rộng: thêm box cho tỉnh mới khi có dataset.
SUPPORTED_REGIONS = [
    {
        "name": "Hà Nội",
        "tier": "full_data",
        "lat_min": 20.85,
        "lat_max": 21.25,
        "lon_min": 105.6,
        "lon_max": 106.1,
        "aliases": ["hà nội", "ha noi", "hanoi", "thủ đô"],
    }
]

# Điểm đến đã biết nhưng chưa có dữ liệu thực tế -> tier 2 (kiến thức chung)
KNOWN_DESTINATIONS = [
    "đà nẵng", "da nang", "hồ chí minh", "ho chi minh", "sài gòn", "saigon",
    "đà lạt", "da lat", "nha trang", "phú quốc", "phu quoc", "sa pa", "sapa",
    "huế", "hue", "hội an", "hoi an", "hạ long", "ha long", "ninh bình",
    "ninh binh", "vũng tàu", "vung tau", "quy nhơn", "quy nhon", "hải phòng",
    "hai phong", "cần thơ", "can tho", "hà giang", "ha giang", "mộc châu",
    "moc chau", "phú yên", "phu yen", "quảng bình", "quang binh",
    "buôn ma thuột", "phan thiết", "mũi né", "mui ne", "bảo lộc", "cao bằng",
    "mai châu", "côn đảo", "lý sơn",
]

TIER_FULL = "full_data"           # Có POI thực tế -> RAG + Rule đầy đủ
TIER_GENERAL = "general_knowledge"  # Không có POI -> LLM dùng kiến thức chung, có disclaimer
TIER_UNKNOWN = "unknown"          # Không nhận diện được điểm đến


def remove_accents(s: str) -> str:
    if not s:
        return ""
    s1 = u'ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾếỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ'
    s0 = u'AAAAEEEIIOOOOUUYaaaaeeeiioooouuyAaDdIiUuOoUuAaAaAaAaAaAaAaAaAaAaAaAaEeEeEeEeEeEeEeEeIiIiOoOoOoOoOoOoOoOoOoOoOoOoUuUuUuUuUuUuUuYyYyYyYy'
    out = []
    for c in s:
        out.append(s0[s1.index(c)] if c in s1 else c)
    return "".join(out).lower()


def detect_data_tier(destination: str) -> dict:
    """
    Trả về dict: {"tier": ..., "region": str|None, "note": str}
    - full_data: có POI thực tế (hiện chỉ Hà Nội)
    - general_knowledge: điểm đến đã biết nhưng chưa có dữ liệu
    - unknown: không xác định được
    """
    if not destination:
        return {"tier": TIER_UNKNOWN, "region": None, "note": ""}

    dest_na = remove_accents(destination)

    for region in SUPPORTED_REGIONS:
        for alias in region["aliases"]:
            if alias in dest_na:
                return {
                    "tier": TIER_FULL,
                    "region": region["name"],
                    "note": f"BeeNavi có dữ liệu địa điểm thực tế đầy đủ tại {region['name']}.",
                }

    if any(k in dest_na for k in KNOWN_DESTINATIONS):
        return {
            "tier": TIER_GENERAL,
            "region": None,
            "note": "Điểm đến này chưa có dữ liệu địa điểm thực tế trong CSDL. BeeNavi sẽ gợi ý dựa trên kiến thức chung; thông tin có thể không đầy đủ và cần kiểm chứng thêm.",
        }

    return {"tier": TIER_UNKNOWN, "region": None, "note": ""}


def get_supported_regions_summary() -> str:
    """Câu thông báo phạm vi hỗ trợ cho UI/chat."""
    names = [r["name"] for r in SUPPORTED_REGIONS]
    if len(names) == 1:
        return f"BeeNavi hiện có dữ liệu địa điểm thực tế tại {names[0]}. Các điểm đến khác sẽ được gợi ý dựa trên kiến thức chung."
    return f"BeeNavi hiện có dữ liệu địa điểm thực tế tại: {', '.join(names)}. Các điểm đến khác sẽ được gợi ý dựa trên kiến thức chung."
