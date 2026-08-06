import requests

WEATHER_API_KEY = "77e52defbc5a07e5931feda1df0497ee"


def get_location_coordinates(location_name: str) -> dict | None:
    """Lấy kinh độ, vĩ độ từ tên địa điểm nhập vào (Nominatim OpenStreetMap)."""
    url = f"https://nominatim.openstreetmap.org/search?q={location_name}&format=json&limit=1"
    headers = {"User-Agent": "BeeNavi_App/1.0"}
    try:
        response = requests.get(url, headers=headers, timeout=8).json()
        if response:
            return {
                "name": response[0]["display_name"],
                "lat": float(response[0]["lat"]),
                "lon": float(response[0]["lon"]),
            }
    except Exception as e:
        print(f"[X] Lỗi gọi Map API: {e}")
    return None


def _classify_weather(weather_main: str, temp: float, humidity: int) -> str:
    """
    Phân loại thời tiết thành tag khớp với dataset_checklist.txt.

    Thứ tự ưu tiên: Mưa lớn > Mưa > Ẩm ướt > Lạnh giá > Lạnh > Nắng nóng > Ấm áp > Nắng
    """
    has_thunder = "thunderstorm" in weather_main
    has_rain    = any(w in weather_main for w in ["rain", "drizzle", "thunderstorm"])
    is_fog      = any(w in weather_main for w in ["mist", "fog", "haze", "smoke"])
    is_windy    = "squall" in weather_main or "tornado" in weather_main

    if has_thunder:
        return "Mưa lớn"
    if has_rain and humidity >= 80:
        return "Ẩm ướt"
    if has_rain:
        return "Mưa"
    if temp < 10:
        return "Lạnh giá"
    if temp < 18:
        return "Lạnh"
    if temp >= 33:
        return "Nắng nóng"
    if is_fog or is_windy:
        return "Gió"
    if 22 <= temp < 33:
        return "Nắng"
    return "Ấm áp"


def get_realtime_weather(lat: float, lon: float) -> dict:
    """Lấy thông tin thời tiết thời gian thực (OpenWeatherMap) và phân loại Tag."""
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=vi"
    )
    try:
        response = requests.get(url, timeout=8).json()
        if response.get("cod") == 200:
            weather_main = response["weather"][0]["main"].lower()
            temp         = response["main"]["temp"]
            humidity     = response["main"]["humidity"]
            desc         = response["weather"][0]["description"]
            weather_tag  = _classify_weather(weather_main, temp, humidity)

            return {
                "temp":        round(temp, 1),
                "humidity":    humidity,
                "description": desc.title(),
                "weather_tag": weather_tag,
            }
    except Exception as e:
        print(f"[X] Lỗi gọi Weather API: {e}")

    return {"temp": 25, "humidity": 60, "description": "Không rõ", "weather_tag": "Nắng"}


def calculate_distance(start_coords: dict, dest_coords: dict) -> float | None:
    """Tính quãng đường di chuyển giữa 2 điểm bằng OSRM (đường bộ, km)."""
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{start_coords['lon']},{start_coords['lat']};"
        f"{dest_coords['lon']},{dest_coords['lat']}?overview=false"
    )
    try:
        response = requests.get(url, timeout=8).json()
        if response.get("code") == "Ok":
            return round(response["routes"][0]["distance"] / 1000, 1)
    except Exception:
        pass
    return None