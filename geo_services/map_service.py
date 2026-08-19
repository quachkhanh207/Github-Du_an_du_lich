"""
geo_services/map_service.py
Dịch vụ bản đồ: Geocoding (Nominatim/OSM) và tính khoảng cách đường bộ (OSRM).
"""
import requests


def get_location_coordinates(location_name: str) -> dict | None:
    """Lấy kinh độ, vĩ độ từ tên địa điểm nhập vào (Nominatim OpenStreetMap)."""
    url = f"https://nominatim.openstreetmap.org/search?q={location_name}&format=json&limit=1"
    headers = {"User-Agent": "BeeNavi_App/1.0"}
    try:
        response = requests.get(url, headers=headers, timeout=8).json()
        if response:
            return {
                "name": response[0]["display_name"],
                "lat":  float(response[0]["lat"]),
                "lon":  float(response[0]["lon"]),
            }
    except Exception as e:
        print(f"[Map] Lỗi gọi Map API: {e}")
    return None


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
