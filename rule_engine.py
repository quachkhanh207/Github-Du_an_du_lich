import csv
import math
from collections import defaultdict


class BeeNaviRuleEngine:
    """Rule Engine 3-lớp cho hệ thống BeeNavi Checklist."""

    # Ánh xạ weather tag người dùng → các từ khóa con trong dataset
    WEATHER_ALIASES: dict[str, list[str]] = {
        "Mưa lớn":  ["Mưa lớn", "Mưa", "Ẩm ướt"],
        "Ẩm ướt":   ["Ẩm ướt", "Mưa", "Mưa ẩm"],
        "Mưa":      ["Mưa", "Mưa ẩm", "Mưa nhẹ"],
        "Lạnh giá": ["Lạnh giá", "Lạnh", "Tuyết"],
        "Lạnh":     ["Lạnh", "Lạnh nhẹ"],
        "Nắng nóng":["Nắng nóng", "Nắng", "Ấm áp", "Hanh khô"],
        "Nắng":     ["Nắng", "Ấm áp", "Nắng nóng", "Hanh khô"],
        "Ấm áp":    ["Ấm áp", "Nắng"],
        "Gió":      ["Gió", "Bụi", "Gió / Bụi"],
    }

    def __init__(self, dataset_path: str = "dataset_checklist.txt"):
        self.dataset_path = dataset_path
        self.items = self._load_dataset()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_dataset(self) -> list[dict]:
        """Đọc và parse file dataset_checklist.txt (CSV)."""
        items = []
        try:
            with open(self.dataset_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    items.append(row)
        except Exception as e:
            print(f"[X] Không thể đọc file dataset: {e}")
        return items

    def _tag_match(self, cell_value: str, accepted_tags: list[str]) -> bool:
        """
        Kiểm tra xem cell_value (có thể chứa nhiều tag phân cách bởi '/')
        có chứa bất kỳ tag nào trong accepted_tags không.

        VD: cell="Nắng nóng / Ấm áp", tags=["Nắng nóng"] → True
        """
        if cell_value.strip() == "Tất cả":
            return True
        for tag in accepted_tags:
            if tag.lower() in cell_value.lower():
                return True
        return False

    def _expand_weather_tags(self, weather_tag: str) -> list[str]:
        """Trả về danh sách tag con để match dataset."""
        return self.WEATHER_ALIASES.get(weather_tag, [weather_tag])

    def _calculate_quantity(self, item_name: str, days: int) -> int:
        """Tính số lượng đồ dùng dựa trên số ngày."""
        name = item_name.lower()
        # Quần áo thay thường xuyên
        if any(k in name for k in ["áo thun", "đồ lót", "tất", "vớ", "áo phông"]):
            return days + 1  # Dự phòng thêm 1
        # Quần mặc 2 ngày/cái
        if "quần" in name and "quần áo" not in name:
            return max(1, math.ceil(days / 2))
        # Bộ ngủ, bộ tắm mang 1
        if any(k in name for k in ["quần áo ngủ", "đồ ngủ"]):
            return 1
        # Thuốc mang theo theo số ngày
        if "thuốc" in name and "đặc trị" not in name:
            return 1
        return 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def filter_checklist(
        self,
        weather_tag: str,
        vehicle: str,
        trip_type: str,
        days: int,
    ) -> list[dict]:
        """
        Thuật toán lọc đồ dùng 3 lớp của BeeNavi.

        Lớp 1 – Bắt buộc toàn cầu: item bắt buộc áp dụng cho mọi chuyến.
        Lớp 2 – Khớp theo bối cảnh: thời tiết AND phương tiện AND loại hình.
        Lớp 3 – Loại trùng: không thêm item đã có trong kết quả.
        """
        seen_ids: set[str] = set()
        output: list[dict] = []
        weather_tags = self._expand_weather_tags(weather_tag)

        for item in self.items:
            item_id = item["ID"]
            if item_id in seen_ids:
                continue

            match_weather = self._tag_match(item["Thoi_Tiet"], weather_tags)
            match_vehicle = self._tag_match(item["Phuong_Tien"], [vehicle])
            match_trip    = self._tag_match(item["Loai_Chuyen_Di"], [trip_type])

            if match_weather and match_vehicle and match_trip:
                qty = self._calculate_quantity(item["Ten_Do_Dung"], days)
                output.append({
                    "id":       item_id,
                    "name":     item["Ten_Do_Dung"],
                    "category": item["Danh_Muc"],
                    "quantity": qty,
                    "priority": item["Muc_Do_Thiet_Yeu"],
                })
                seen_ids.add(item_id)

        # Sắp xếp: Bắt buộc trước, rồi Khuyến khích, rồi Không bắt buộc
        priority_order = {"Bắt buộc": 0, "Khuyến khích": 1, "Không bắt buộc": 2}
        output.sort(key=lambda x: priority_order.get(x["priority"], 3))
        return output

    def group_by_category(self, items: list[dict]) -> dict[str, list[dict]]:
        """Nhóm danh sách item theo Danh_Muc."""
        groups: dict[str, list[dict]] = defaultdict(list)
        for item in items:
            groups[item["category"]].append(item)
        return dict(groups)