"""
ai_engine/tools/diary_tool.py
Tool đọc lịch sử chuyến đi và lưu chuyến đi/nhật ký vào CSDL SQLite cho AI Orchestrator.
"""
import asyncio
from typing import Any, Dict, Optional, List
from ai_engine.tools.base_tool import BaseTool
import diary_service


class DiaryTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="diary_service",
            description="Đọc lịch sử các chuyến đi đã tạo, lấy chi tiết chuyến đi hoặc lưu chuyến đi mới vào nhật ký cá nhân."
        )

    async def execute(
        self,
        action: str = "get_trips",
        user_id: Optional[str] = None,
        trip_id: Optional[str] = None,
        trip_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        action: 'get_trips' | 'get_trip_detail' | 'save_trip'
        """
        try:
            if action == "get_trips":
                trips = await asyncio.to_thread(diary_service.get_user_trips, user_id)
                if not trips:
                    return {
                        "success": True,
                        "data": [],
                        "summary": "Người dùng chưa có chuyến đi nào trong lịch sử nhật ký."
                    }

                recent_trips = trips[:3]
                trip_names = [f"'{t.get('title')}' ({t.get('destination')}, {t.get('number_of_days')} ngày)" for t in recent_trips]
                summary = f"[LỊCH SỬ CHUYẾN ĐI ĐÃ LƯU]: Người dùng đã từng tạo {len(trips)} chuyến đi, gần nhất là: " + ", ".join(trip_names)
                return {
                    "success": True,
                    "data": trips,
                    "summary": summary
                }

            elif action == "get_trip_detail" and trip_id:
                detail = await asyncio.to_thread(diary_service.get_trip_detail, trip_id)
                return {
                    "success": True if detail else False,
                    "data": detail,
                    "summary": f"Chi tiết chuyến đi {detail.get('title') if detail else 'Không tìm thấy'}"
                }

            elif action == "save_trip" and trip_data:
                saved = await asyncio.to_thread(diary_service.save_or_update_trip, trip_data, user_id)
                return {
                    "success": True,
                    "data": saved,
                    "summary": f"Đã lưu thành công chuyến đi '{saved.get('title')}' vào nhật ký."
                }

            return {
                "success": False,
                "data": None,
                "error": f"Hành động '{action}' không hợp lệ hoặc thiếu dữ liệu.",
                "summary": ""
            }

        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "summary": ""
            }
