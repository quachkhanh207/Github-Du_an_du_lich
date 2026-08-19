"""
ai_engine/tools/checklist_tool.py
Công cụ gợi ý danh mục chuẩn bị hành lý, đồ dùng thiết yếu và thông minh cho chuyến du lịch.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from ai_engine.tools.base_tool import BaseTool
from api_server.config import BASE_DIR

CHECKLIST_DATA_PATH = BASE_DIR / "planner" / "dataset_checklist.txt"


class ChecklistTool(BaseTool):
    """Tool gợi ý danh sách chuẩn bị đồ dùng du lịch thông minh."""

    def __init__(self, dataset_path: Optional[Path] = None):
        super().__init__(
            name="checklist_tool",
            description="Gợi ý danh sách đồ dùng, trang phục và giấy tờ cần chuẩn bị cho chuyến đi."
        )
        self.dataset_path = dataset_path or CHECKLIST_DATA_PATH
        self._items_cache: List[Dict[str, str]] = []
        self._load_dataset()

    def _load_dataset(self):
        """Tải dữ liệu từ dataset_checklist.txt"""
        if not self.dataset_path.exists():
            return

        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if not lines:
                return

            header = [h.strip() for h in lines[0].strip().split(",")]
            # Format: ID,Ten_Do_Dung,Danh_Muc,Loai_Chuyen_Di,Thoi_Tiet,Phuong_Tien,Muc_Do_Thiet_Yeu
            for line in lines[1:]:
                parts = [p.strip() for p in line.strip().split(",")]
                if len(parts) >= 7:
                    self._items_cache.append({
                        "id": parts[0],
                        "name": parts[1],
                        "category": parts[2],
                        "trip_type": parts[3],
                        "weather": parts[4],
                        "transport": parts[5],
                        "urgency": parts[6]
                    })
        except Exception as e:
            print(f"[ChecklistTool] Lỗi đọc dataset checklist: {e}")

    async def execute(
        self,
        weather_tag: Optional[str] = None,
        trip_type: Optional[str] = None,
        transport: Optional[str] = None,
        destination: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Lọc danh sách đồ dùng phù hợp:
        - weather_tag: 'Nắng nóng', 'Mưa', 'Lạnh', 'Mát mẻ'...
        - trip_type: 'Biển', 'Trekking', 'Khám phá', 'Nghỉ dưỡng', 'Phượt'...
        - transport: 'Máy bay', 'Xe máy', 'Ô tô'...
        """
        # Nếu chưa load được từ file thì dùng danh mục cơ bản
        if not self._items_cache:
            self._load_dataset()

        selected_items = []
        weather_kw = (weather_tag or "").lower()
        trip_kw = (trip_type or "").lower()
        trans_kw = (transport or "").lower()

        # Suy luận thêm từ destination
        if destination:
            dest_lower = destination.lower()
            if any(k in dest_lower for k in ["sapa", "hà giang", "mộc châu", "đà lạt"]) and not weather_kw:
                weather_kw = "lạnh"
            elif any(k in dest_lower for k in ["phú quốc", "nha trang", "đà nẵng", "vũng tàu", "mũi né"]):
                trip_kw = trip_kw or "biển"

        for item in self._items_cache:
            item_cat = item["category"]
            item_trip = item["trip_type"].lower()
            item_w = item["weather"].lower()
            item_t = item["transport"].lower()
            urgency = item["urgency"]

            # Luôn giữ đồ bắt buộc chung
            if item_trip == "tất cả" and item_w == "tất cả" and item_t == "tất cả" and urgency == "Bắt buộc":
                selected_items.append(item)
                continue

            # Lọc theo điều kiện
            match_trip = (item_trip == "tất cả") or any(k in item_trip for k in trip_kw.split()) if trip_kw else (item_trip == "tất cả")
            match_weather = (item_w == "tất cả") or any(k in item_w for k in weather_kw.split()) if weather_kw else (item_w == "tất cả")
            match_trans = (item_t == "tất cả") or any(k in item_t for k in trans_kw.split()) if trans_kw else (item_t == "tất cả")

            if match_trip and match_weather and match_trans:
                selected_items.append(item)

        # Gom nhóm theo danh mục
        categorized: Dict[str, List[str]] = {}
        for it in selected_items[:25]:  # Giới hạn số lượng tiêu biểu
            cat = it["category"]
            if cat not in categorized:
                categorized[cat] = []
            tag = " [Bắt buộc]" if it["urgency"] == "Bắt buộc" else ""
            categorized[cat].append(f"{it['name']}{tag}")

        # Tạo summary đẹp cho Prompt
        summary_lines = ["[GỢI Ý DANH SÁCH HÀNH LÝ & ĐỒ DÙNG CẦN CHUẨN BỊ]:"]
        for cat, items in categorized.items():
            summary_lines.append(f"- **{cat}**: {', '.join(items)}")

        summary = "\n".join(summary_lines)

        return {
            "success": True,
            "data": {
                "destination": destination,
                "weather_condition": weather_tag,
                "trip_type": trip_type,
                "categories": categorized,
                "total_items": len(selected_items)
            },
            "error": None,
            "summary": summary
        }
