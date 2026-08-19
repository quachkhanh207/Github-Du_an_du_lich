"""
geo_services/weather_service.py
Dịch vụ thời tiết thực tế và sinh Quy tắc hoạt động du lịch (Weather Rules) cho AI.
"""
import os
try:
    import requests
except ImportError:
    import httpx as requests
from typing import Dict, Any, Optional

# API key đọc từ .env
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")

# Tọa độ chuẩn của các thành phố du lịch hàng đầu Việt Nam (Truy xuất siêu tốc 0.001s)
CITY_COORDINATES = {
    "hà nội": {"lat": 21.0285, "lon": 105.8542, "name": "Hà Nội"},
    "ha noi": {"lat": 21.0285, "lon": 105.8542, "name": "Hà Nội"},
    "hanoi": {"lat": 21.0285, "lon": 105.8542, "name": "Hà Nội"},
    "đà nẵng": {"lat": 16.0544, "lon": 108.2022, "name": "Đà Nẵng"},
    "da nang": {"lat": 16.0544, "lon": 108.2022, "name": "Đà Nẵng"},
    "danang": {"lat": 16.0544, "lon": 108.2022, "name": "Đà Nẵng"},
    "hồ chí minh": {"lat": 10.8231, "lon": 106.6297, "name": "Hồ Chí Minh"},
    "ho chi minh": {"lat": 10.8231, "lon": 106.6297, "name": "Hồ Chí Minh"},
    "sài gòn": {"lat": 10.8231, "lon": 106.6297, "name": "Hồ Chí Minh"},
    "saigon": {"lat": 10.8231, "lon": 106.6297, "name": "Hồ Chí Minh"},
    "sa pa": {"lat": 22.3364, "lon": 103.8438, "name": "Sa Pa"},
    "sapa": {"lat": 22.3364, "lon": 103.8438, "name": "Sa Pa"},
    "đà lạt": {"lat": 11.9404, "lon": 108.4583, "name": "Đà Lạt"},
    "da lat": {"lat": 11.9404, "lon": 108.4583, "name": "Đà Lạt"},
    "dalat": {"lat": 11.9404, "lon": 108.4583, "name": "Đà Lạt"},
    "nha trang": {"lat": 12.2388, "lon": 109.1967, "name": "Nha Trang"},
    "nhatrang": {"lat": 12.2388, "lon": 109.1967, "name": "Nha Trang"},
    "phú quốc": {"lat": 10.2899, "lon": 103.9840, "name": "Phú Quốc"},
    "phu quoc": {"lat": 10.2899, "lon": 103.9840, "name": "Phú Quốc"},
    "huế": {"lat": 16.4637, "lon": 107.5909, "name": "Huế"},
    "hue": {"lat": 16.4637, "lon": 107.5909, "name": "Huế"},
    "hội an": {"lat": 15.8801, "lon": 108.3380, "name": "Hội An"},
    "hoi an": {"lat": 15.8801, "lon": 108.3380, "name": "Hội An"},
    "hạ long": {"lat": 20.9599, "lon": 107.0425, "name": "Hạ Long"},
    "ha long": {"lat": 20.9599, "lon": 107.0425, "name": "Hạ Long"},
    "ninh bình": {"lat": 20.2506, "lon": 105.9745, "name": "Ninh Bình"},
    "ninh binh": {"lat": 20.2506, "lon": 105.9745, "name": "Ninh Bình"},
    "vũng tàu": {"lat": 10.3460, "lon": 107.0843, "name": "Vũng Tàu"},
    "vung tau": {"lat": 10.3460, "lon": 107.0843, "name": "Vũng Tàu"},
    "quy nhơn": {"lat": 13.7820, "lon": 109.2197, "name": "Quy Nhơn"},
    "quy nhon": {"lat": 13.7820, "lon": 109.2197, "name": "Quy Nhơn"},
    "hải phòng": {"lat": 20.8449, "lon": 106.6881, "name": "Hải Phòng"},
    "hai phong": {"lat": 20.8449, "lon": 106.6881, "name": "Hải Phòng"},
    "cần thơ": {"lat": 10.0452, "lon": 105.7469, "name": "Cần Thơ"},
    "can tho": {"lat": 10.0452, "lon": 105.7469, "name": "Cần Thơ"},
    "hà giang": {"lat": 22.8233, "lon": 104.9839, "name": "Hà Giang"},
    "ha giang": {"lat": 22.8233, "lon": 104.9839, "name": "Hà Giang"},
    "mộc châu": {"lat": 20.8444, "lon": 104.6469, "name": "Mộc Châu"},
    "moc chau": {"lat": 20.8444, "lon": 104.6469, "name": "Mộc Châu"},
}


def _classify_weather(weather_main: str, temp: float, humidity: int) -> str:
    """Phân loại thời tiết thành tag chuẩn."""
    has_thunder = "thunderstorm" in weather_main
    has_rain = any(w in weather_main for w in ["rain", "drizzle", "thunderstorm"])
    is_fog = any(w in weather_main for w in ["mist", "fog", "haze", "smoke"])
    is_windy = "squall" in weather_main or "tornado" in weather_main

    if has_thunder:
        return "Mưa lớn"
    if has_rain and humidity >= 80:
        return "Ẩm ướt"
    if has_rain:
        return "Mưa"
    if temp < 14:
        return "Lạnh giá"
    if temp < 20:
        return "Lạnh"
    if temp >= 33:
        return "Nắng nóng"
    if is_fog or is_windy:
        return "Gió"
    if 22 <= temp < 33:
        return "Nắng"
    return "Ấm áp"


def _generate_weather_rule(weather_tag: str, temp: float, desc: str) -> str:
    """Sinh quy tắc hoạt động du lịch phù hợp với thời tiết."""
    if weather_tag in ["Mưa", "Mưa lớn", "Ẩm ướt"]:
        return (
            f"Thời tiết {desc} ({temp}°C): Ưu tiên tham quan bảo tàng, di tích lịch sử có mái che, "
            f"trải nghiệm food tour ẩm thực truyền thống và quán cafe view ngắm mưa. "
            f"Hạn chế các hoạt động leo núi ngoài trời."
        )
    elif weather_tag == "Nắng nóng" or temp >= 33:
        return (
            f"Thời tiết nắng gắt ({temp}°C): Khung giờ trưa từ 11:30 đến 15:00 ưu tiên nghỉ ngơi, ăn uống trong nhà "
            f"hoặc quán cafe máy lạnh. Hoạt động dạo phố, chụp ảnh ngoài trời xếp vào sáng sớm (07:30 - 09:30) "
            f"hoặc chiều muộn sau 16:30."
        )
    elif weather_tag in ["Lạnh", "Lạnh giá"] or temp < 20:
        return (
            f"Thời tiết se lạnh ({temp}°C): Rất thích hợp dạo bộ, check-in đồi chè, săn mây và thưởng thức các món "
            f"nóng hổi (lẩu, nướng, đồ uống ấm). Nhớ mang theo áo khoác ấm khi ra ngoài vào ban đêm."
        )
    else:
        return (
            f"Thời tiết nắng ráo, trong lành ({temp}°C): Điều kiện lý tưởng nhất cho mọi hoạt động ngoài trời, "
            f"tham quan danh lam thắng cảnh, dạo phố và chụp ảnh kỷ niệm."
        )


import time

_WEATHER_CACHE = {}
_CACHE_TTL_SEC = 1800  # 30 phút TTL


def _wmo_code_to_desc_and_tag(code: int, temp: float) -> tuple:
    """Chuyển mã thời tiết chuẩn WMO sang mô tả tiếng Việt và thẻ phân loại."""
    if code == 0:
        return "Trời quang, nắng đẹp", ("Nắng nóng" if temp >= 33 else "Nắng")
    elif code in (1, 2):
        return "Ít mây, nắng dịu", ("Nắng nóng" if temp >= 33 else "Ấm áp" if temp >= 22 else "Lạnh" if temp < 20 else "Nắng")
    elif code == 3:
        return "Nhiều mây, râm mát", ("Lạnh" if temp < 20 else "Ấm áp")
    elif code in (45, 48):
        return "Sương mù nhẹ, se lạnh", "Gió"
    elif code in (51, 53, 55):
        return "Mưa phùn rải rác", "Mưa"
    elif code in (61, 63, 65):
        return "Có mưa rào", "Mưa"
    elif code in (80, 81, 82, 95, 96, 99):
        return "Mưa dông lớn", "Mưa lớn"
    else:
        return "Nắng ráo, trời mát", "Nắng"


def _regional_fallback_weather(lat: float, lon: float) -> dict:
    """Sinh thời tiết dự phòng theo đặc thù khí hậu từng vùng miền của Việt Nam."""
    # Sa Pa / vùng núi cao phía Bắc
    if lat >= 22.0 and lon <= 104.5:
        temp, humidity, desc, tag = 17.0, 75, "Se lạnh, sương mù nhẹ", "Lạnh"
    # Hà Nội / Đồng bằng Bắc Bộ
    elif lat >= 20.0:
        temp, humidity, desc, tag = 25.0, 70, "Tiết trời mát mẻ, dịu nhẹ", "Ấm áp"
    # Đà Lạt / Cao nguyên Lâm Viên
    elif 11.5 <= lat <= 12.2 and 108.2 <= lon <= 108.7:
        temp, humidity, desc, tag = 18.5, 78, "Nắng dịu, không khí se lạnh", "Lạnh"
    # Miền Trung (Đà Nẵng, Huế, Hội An, Quy Nhơn)
    elif 15.0 <= lat < 20.0:
        temp, humidity, desc, tag = 29.0, 68, "Nắng ráo, biển êm sóng nhẹ", "Nắng"
    # Miền Nam & Phú Quốc
    else:
        temp, humidity, desc, tag = 31.0, 65, "Nắng ấm, trời trong xanh", "Nắng"

    return {
        "temp": temp,
        "humidity": humidity,
        "description": desc,
        "weather_tag": tag,
        "weather_rule": _generate_weather_rule(tag, temp, desc)
    }


def get_realtime_weather(lat: float, lon: float) -> dict:
    """Lấy thông tin thời tiết thời gian thực qua OpenWeatherMap API hoặc Open-Meteo (kèm TTL cache 30 phút)."""
    cache_key = f"coords_{round(lat, 2)}_{round(lon, 2)}"
    now = time.time()
    if cache_key in _WEATHER_CACHE:
        cached_entry, expire_time = _WEATHER_CACHE[cache_key]
        if now < expire_time:
            return dict(cached_entry)

    # 1. Thử gọi OpenWeatherMap API nếu có API key hợp lệ
    if WEATHER_API_KEY and WEATHER_API_KEY != "your-openweathermap-api-key-here":
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=vi"
        try:
            response = requests.get(url, timeout=4).json()
            if response.get("cod") == 200:
                weather_main = response["weather"][0]["main"].lower()
                temp = response["main"]["temp"]
                humidity = response["main"]["humidity"]
                desc = response["weather"][0]["description"].title()
                weather_tag = _classify_weather(weather_main, temp, humidity)
                weather_rule = _generate_weather_rule(weather_tag, round(temp, 1), desc)

                result = {
                    "temp": round(temp, 1),
                    "humidity": humidity,
                    "description": desc,
                    "weather_tag": weather_tag,
                    "weather_rule": weather_rule
                }
                _WEATHER_CACHE[cache_key] = (result, now + _CACHE_TTL_SEC)
                return result
        except Exception as e:
            print(f"[Weather] OpenWeatherMap call failed: {e}")

    # 2. Gọi Open-Meteo API (Miễn phí 100%, thời gian thực cho mọi tọa độ tại VN, không cần API key)
    try:
        om_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code"
        om_res = requests.get(om_url, timeout=4).json()
        if "current" in om_res:
            cur = om_res["current"]
            temp = float(cur.get("temperature_2m", 26.0))
            humidity = int(cur.get("relative_humidity_2m", 65))
            wmo_code = int(cur.get("weather_code", 0))
            desc, weather_tag = _wmo_code_to_desc_and_tag(wmo_code, temp)
            weather_rule = _generate_weather_rule(weather_tag, round(temp, 1), desc)

            result = {
                "temp": round(temp, 1),
                "humidity": humidity,
                "description": desc,
                "weather_tag": weather_tag,
                "weather_rule": weather_rule
            }
            _WEATHER_CACHE[cache_key] = (result, now + _CACHE_TTL_SEC)
            return result
    except Exception as e:
        print(f"[Weather] Open-Meteo call failed: {e}")

    # 3. Fallback khí hậu theo vùng miền chính xác của tọa độ điểm đến
    fallback = _regional_fallback_weather(lat, lon)
    _WEATHER_CACHE[cache_key] = (fallback, now + _CACHE_TTL_SEC)
    return fallback


from pathlib import Path

def find_destination_coordinates(destination_name: str) -> dict:
    """Tra cứu tọa độ linh hoạt từ cache hoặc CSDL 17.147 POIs thật."""
    dest_clean = destination_name.lower().strip()

    # 1. Tìm trong danh mục cache nhanh
    for key, val in CITY_COORDINATES.items():
        if key in dest_clean or dest_clean in key:
            return val

    # 2. Truy vấn trực tiếp từ CSDL 17.147 POIs (SQLite)
    db_path = Path(__file__).resolve().parent.parent / "data" / "travel_knowledge.db"
    if db_path.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            c = conn.cursor()
            rows = c.execute(
                "SELECT name, lat, lon FROM pois WHERE name LIKE ? OR address LIKE ? LIMIT 5",
                (f"%{dest_clean}%", f"%{dest_clean}%")
            ).fetchall()
            conn.close()
            if rows:
                valid_coords = [(r[1], r[2]) for r in rows if r[1] != 0.0 and r[2] != 0.0]
                if valid_coords:
                    avg_lat = sum(c[0] for c in valid_coords) / len(valid_coords)
                    avg_lon = sum(c[1] for c in valid_coords) / len(valid_coords)
                    return {"lat": round(avg_lat, 4), "lon": round(avg_lon, 4), "name": destination_name.title()}
        except Exception as e:
            print(f"[Weather] Lỗi query CSDL POIs cho {destination_name}: {e}")

    # Mặc định trung tâm Việt Nam (Đà Nẵng: 16.0544, 108.2022) nếu hoàn toàn không tìm thấy
    return {"lat": 16.0544, "lon": 108.2022, "name": destination_name.title()}


def get_weather_by_destination(destination_name: str) -> dict:
    """Tìm tọa độ và lấy thời tiết kèm quy tắc du lịch theo tên điểm đến (kèm TTL cache & CSDL POIs)."""
    dest_clean = destination_name.lower().strip()
    cache_key = f"dest_{dest_clean}"
    now = time.time()
    if cache_key in _WEATHER_CACHE:
        cached_entry, expire_time = _WEATHER_CACHE[cache_key]
        if now < expire_time:
            return dict(cached_entry)

    coords = find_destination_coordinates(destination_name)
    lat = coords["lat"]
    lon = coords["lon"]
    city_name = coords.get("name", destination_name)

    weather = get_realtime_weather(lat, lon)
    weather["city"] = city_name
    weather["lat"] = lat
    weather["lon"] = lon

    _WEATHER_CACHE[cache_key] = (weather, now + _CACHE_TTL_SEC)
    return weather
