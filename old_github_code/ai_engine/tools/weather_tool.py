"""
ai_engine/tools/weather_tool.py
Tool tra cứu Thời tiết thực tế và Weather Rules từ OpenWeatherMap.
"""
import asyncio
from typing import Any, Dict, Optional
from ai_engine.tools.base_tool import BaseTool
from geo_services.weather_service import get_weather_by_destination, get_realtime_weather


class WeatherTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="get_weather",
            description="Lấy thông tin thời tiết thực tế (nhiệt độ, mưa, nắng, độ ẩm) và Quy tắc hoạt động du lịch phù hợp theo thời tiết."
        )

    async def execute(
        self,
        destination: str = "Đà Nẵng",
        lat: float = 0.0,
        lon: float = 0.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Thực thi tra cứu thời tiết.
        """
        try:
            if lat != 0.0 and lon != 0.0:
                weather_info = await asyncio.to_thread(get_realtime_weather, lat, lon)
                weather_info["destination"] = destination
            else:
                weather_info = await asyncio.to_thread(get_weather_by_destination, destination)

            city = weather_info.get("city", destination)
            temp = weather_info.get("temp", 28)
            desc = weather_info.get("description", "Thời tiết mát mẻ")
            weather_rule = weather_info.get("weather_rule", "Ưu tiên các hoạt động ngoài trời")
            weather_tag = weather_info.get("weather_tag", "Nắng")

            summary_text = (
                f"[DỮ LIỆU THỜI TIẾT THỰC TẾ TẠI {city.upper()}]:\n"
                f"- Nhiệt độ: {temp}°C | Trạng thái: {desc} ({weather_tag})\n"
                f"- QUY TẮC ĐỀ XUẤT THEO THỜI TIẾT: {weather_rule}"
            )

            return {
                "success": True,
                "data": weather_info,
                "summary": summary_text
            }

        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "summary": ""
            }
