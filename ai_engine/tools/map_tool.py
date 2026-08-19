"""
ai_engine/tools/map_tool.py
Công cụ tra cứu tọa độ địa lý, định vị và tính toán khoảng cách/cự ly di chuyển giữa các địa điểm.
"""
from typing import Any, Dict, Optional
from ai_engine.tools.base_tool import BaseTool
from geo_services.map_service import get_location_coordinates, calculate_distance


class MapTool(BaseTool):
    """Tool tra cứu bản đồ, tọa độ và tính khoảng cách di chuyển."""

    def __init__(self):
        super().__init__(
            name="map_service",
            description="Tra cứu tọa độ địa danh, tính cự ly khoảng cách và gợi ý phương tiện di chuyển."
        )

    async def execute(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
        location: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Thực thi tra cứu bản đồ:
        - Nếu có origin và destination: Tính khoảng cách giữa 2 điểm.
        - Nếu chỉ có location: Tra cứu tọa độ và địa chỉ chi tiết.
        """
        try:
            # 1. Trường hợp tính khoảng cách giữa 2 địa danh
            if origin and destination:
                orig_coords = get_location_coordinates(origin)
                dest_coords = get_location_coordinates(destination)

                if not orig_coords or not dest_coords:
                    return {
                        "success": False,
                        "data": None,
                        "error": f"Không thể định vị tọa độ của '{origin}' hoặc '{destination}'.",
                        "summary": f"[BẢN ĐỒ]: Không tìm thấy tọa độ chính xác cho tuyến {origin} - {destination}."
                    }

                dist_km = calculate_distance(orig_coords, dest_coords)
                
                # Đề xuất phương tiện dựa trên cự ly
                suggested_transport = "Xe máy hoặc Ô tô / Taxi"
                est_time = "15-30 phút"
                if dist_km:
                    if dist_km <= 1.5:
                        suggested_transport = "Đi bộ (thích hợp dạo phố, ngắm cảnh)"
                        est_time = f"{int(dist_km * 15)} phút đi bộ"
                    elif dist_km <= 10:
                        suggested_transport = "Xe máy / Taxi / Grab"
                        est_time = f"{int(dist_km * 2.5)} - {int(dist_km * 3.5)} phút"
                    elif dist_km <= 100:
                        suggested_transport = "Ô tô / Xe buýt / Thuê xe riêng"
                        est_time = f"{round(dist_km / 40, 1)} giờ"
                    else:
                        suggested_transport = "Máy bay / Xe khách đường dài / Tàu hỏa"
                        est_time = f"{round(dist_km / 60, 1)} - {round(dist_km / 50, 1)} giờ"

                data = {
                    "origin": orig_coords,
                    "destination": dest_coords,
                    "distance_km": dist_km,
                    "suggested_transport": suggested_transport,
                    "estimated_time": est_time
                }

                summary = (
                    f"[THÔNG TIN DI CHUYỂN & CỰ LY]:\n"
                    f"- Tuyến: {origin} ➔ {destination}\n"
                    f"- Khoảng cách đường bộ: ~{dist_km} km\n"
                    f"- Gợi ý phương tiện: {suggested_transport} (Thời gian ước tính: ~{est_time})"
                )

                return {
                    "success": True,
                    "data": data,
                    "error": None,
                    "summary": summary
                }

            # 2. Trường hợp tra cứu tọa độ 1 địa điểm
            target_loc = location or destination or origin
            if target_loc:
                coords = get_location_coordinates(target_loc)
                if coords:
                    return {
                        "success": True,
                        "data": coords,
                        "error": None,
                        "summary": f"[ĐỊA ĐIỂM / TỌA ĐỘ]: '{target_loc}' ({coords.get('name')}) - Tọa độ: [{coords.get('lat')}, {coords.get('lon')}]."
                    }

            return {
                "success": False,
                "data": None,
                "error": "Vui lòng cung cấp ít nhất một địa điểm cần tra cứu.",
                "summary": None
            }

        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "summary": f"[BẢN ĐỒ]: Lỗi khi tra cứu địa lý: {e}"
            }
