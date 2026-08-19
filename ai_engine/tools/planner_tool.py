"""
ai_engine/tools/planner_tool.py
Tool sinh lịch trình du lịch cấu trúc (JSON / Ngày / Buổi / Chi phí) kết hợp Rule Engine & K-Means.
"""
import asyncio
from typing import Any, Dict, Optional
from ai_engine.tools.base_tool import BaseTool
from planner.rag_engine import RagEngine
from api_server.config import BASE_DIR


from planner.rule_engine import RuleEngineService


class PlannerTool(BaseTool):
    def __init__(self, rag_engine: Optional[RagEngine] = None):
        super().__init__(
            name="plan_itinerary",
            description="Tạo lịch trình du lịch có cấu trúc nhiều ngày, phân cụm địa điểm theo khoảng cách địa lý và quy tắc thời gian."
        )
        if rag_engine is None:
            index_path = BASE_DIR / "data" / "locations_index.json"
            self.rag_engine = RagEngine(str(index_path))
            self.rag_engine.load_index()
        else:
            self.rag_engine = rag_engine

    async def execute(
        self,
        destination: str = "Đà Nẵng",
        number_of_days: int = 3,
        budget: str = "Tiêu chuẩn",
        trip_type: str = "Khám phá",
        departure_location: str = "Hà Nội",
        weather_tag: str = "Nắng",
        temp: float = 28.0,
        user_preferences: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Thực thi tạo lịch trình, dự toán ngân sách, checklist hành trang và tọa độ bản đồ.
        """
        trip_data = {
            "destination": destination,
            "number_of_days": number_of_days,
            "num_days": number_of_days,
            "budget": budget,
            "trip_type": trip_type,
            "departure_location": departure_location
        }
        if user_preferences:
            trip_data["user_preferences"] = user_preferences

        try:
            structured = await asyncio.to_thread(self.rag_engine.get_structured_itinerary, trip_data)

            # 1. Sinh Budget Breakdown
            budget_data = RuleEngineService.calculate_budget_breakdown(
                departure=departure_location,
                destination=destination,
                num_days=number_of_days,
                budget_tier=budget,
                trip_type=trip_type
            )
            structured["budget_breakdown"] = budget_data

            # 2. Sinh Smart Checklist
            checklist_items = RuleEngineService.generate_smart_checklist(
                weather_tag=weather_tag,
                temp=temp,
                num_days=number_of_days,
                trip_type=trip_type
            )
            structured["smart_checklist"] = checklist_items

            # 3. Trích xuất Map Markers cho Live Map Sync
            days = structured.get("days", [])
            map_markers = []
            for day in days:
                d_num = day.get("dayNum", day.get("day", 1))
                for act in day.get("activities", []):
                    lat = act.get("lat", 0.0)
                    lng = act.get("lng", 0.0)
                    if lat != 0.0 and lng != 0.0:
                        map_markers.append({
                            "day": d_num,
                            "time": act.get("time", ""),
                            "title": act.get("title", ""),
                            "lat": lat,
                            "lng": lng
                        })
            structured["map_markers"] = map_markers

            # Tạo text tóm tắt lịch trình để AI đưa vào ngữ cảnh
            summary_lines = [
                f"[KẾ HOẠCH LỊCH TRÌNH ĐỀ XUẤT CHO {destination.upper()} ({number_of_days} NGÀY)]:\n",
                f"- {budget_data.get('formatted_summary', '')}\n"
            ]
            for day in days:
                day_num = day.get("day", 1)
                day_title = day.get("title", f"Ngày {day_num}")
                acts = day.get("activities", [])
                act_titles = [f"[{a.get('time', 'Sáng')}] {a.get('title', '')}" for a in acts]
                summary_lines.append(f"- Ngày {day_num} ({day_title}): " + " | ".join(act_titles))

            top_checklist = [it["item_name"] for it in checklist_items[:4]]
            summary_lines.append(f"\n- Hành trang gợi ý: {', '.join(top_checklist)}...")

            summary_text = "\n".join(summary_lines)

            return {
                "success": True,
                "data": structured,
                "summary": summary_text
            }

        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "summary": ""
            }
