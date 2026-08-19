"""
ai_engine/tools/budget_tool.py
Công cụ ước tính chi phí tham khảo và tư vấn ngân sách cho chuyến du lịch.
"""
from typing import Any, Dict, Optional
from ai_engine.tools.base_tool import BaseTool


class BudgetTool(BaseTool):
    """Tool tư vấn dự trù kinh phí, chi tiêu du lịch theo từng phân khúc."""

    # Bảng định mức chi phí trung bình 1 người / 1 ngày theo phân khúc (VND)
    COST_BENCHMARKS = {
        "Tiết kiệm": {
            "lodging_per_night": 200000,    # Homestay / Dorm / Nhà nghỉ
            "food_per_day": 150000,          # Ăn uống bình dân, đặc sản đường phố
            "transport_per_day": 80000,      # Thuê xe máy + xăng
            "activities_per_day": 100000,    # Vé tham quan di tích / điểm miễn phí
            "desc": "Tối ưu chi phí, ở homestay/dorm, ăn quán bình dân, đi xe máy"
        },
        "Tiêu chuẩn": {
            "lodging_per_night": 550000,    # Khách sạn 3 sao
            "food_per_day": 350000,          # Nhà hàng đặc sản, quán cafe đẹp
            "transport_per_day": 180000,     # Taxi / Grab / Thuê xe máy thoải mái
            "activities_per_day": 250000,    # Vé khu du lịch, vé cáp treo, trải nghiệm
            "desc": "Cân bằng tiện nghi & trải nghiệm, khách sạn 3 sao, ẩm thực đặc sản đa dạng"
        },
        "Sang trọng": {
            "lodging_per_night": 1800000,   # Khách sạn 4-5 sao / Resort
            "food_per_day": 900000,          # Nhà hàng cao cấp, hải sản tươi sống, fine dining
            "transport_per_day": 500000,     # Thuê xe ô tô riêng / Grab car thoải mái
            "activities_per_day": 600000,    # Tour riêng, dịch vụ VIP, thể thao biển
            "desc": "Trải nghiệm cao cấp, nghỉ dưỡng resort/5 sao, dịch vụ tiện nghi tối đa"
        }
    }

    def __init__(self):
        super().__init__(
            name="budget_tool",
            description="Tư vấn và ước tính chi phí dự trù cho chuyến du lịch theo phân khúc và số ngày."
        )

    async def execute(
        self,
        budget_tier: str = "Tiêu chuẩn",
        num_days: int = 1,
        num_people: int = 1,
        destination: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Ước tính chi phí chuyến đi:
        - budget_tier: 'Tiết kiệm', 'Tiêu chuẩn', hoặc 'Sang trọng'
        - num_days: Số ngày (mặc định 1)
        - num_people: Số người (mặc định 1)
        - destination: Điểm đến (nếu có để điều chỉnh hệ số vùng)
        """
        # Chuẩn hóa tier
        tier = "Tiêu chuẩn"
        tier_lower = budget_tier.lower()
        if any(w in tier_lower for w in ["tiết kiệm", "rẻ", "bình dân", "budget", "sinh viên"]):
            tier = "Tiết kiệm"
        elif any(w in tier_lower for w in ["sang trọng", "cao cấp", "luxury", "5 sao", "resort"]):
            tier = "Sang trọng"

        days = max(1, min(int(num_days), 30))
        people = max(1, int(num_people))
        nights = max(1, days - 1) if days > 1 else 1

        benchmark = self.COST_BENCHMARKS.get(tier, self.COST_BENCHMARKS["Tiêu chuẩn"])

        # Hệ số điều chỉnh theo địa phương (ví dụ Phú Quốc/Hạ Long cao hơn chút, vùng cao rẻ hơn)
        location_multiplier = 1.0
        if destination:
            dest_lower = destination.lower()
            if any(k in dest_lower for k in ["phú quốc", "nha trang", "hạ long", "côn đảo"]):
                location_multiplier = 1.15
            elif any(k in dest_lower for k in ["hà giang", "mộc châu", "cao bằng", "ninh bình"]):
                location_multiplier = 0.9

        lodging_cost = int(benchmark["lodging_per_night"] * nights * location_multiplier)
        food_cost = int(benchmark["food_per_day"] * days * people * location_multiplier)
        transport_cost = int(benchmark["transport_per_day"] * days * location_multiplier)
        activities_cost = int(benchmark["activities_per_day"] * days * people * location_multiplier)

        total_per_person = int((lodging_cost / people) + (food_cost / people) + (transport_cost / people) + (activities_cost / people))
        total_trip_cost = total_per_person * people

        data = {
            "budget_tier": tier,
            "days": days,
            "nights": nights,
            "people": people,
            "destination": destination or "Chung",
            "breakdown": {
                "lodging": f"{lodging_cost:,.0f} VND ({nights} đêm)",
                "food": f"{food_cost:,.0f} VND ({days} ngày)",
                "local_transport": f"{transport_cost:,.0f} VND",
                "activities_tickets": f"{activities_cost:,.0f} VND",
            },
            "estimated_total_per_person": f"{total_per_person:,.0f} VND",
            "estimated_total_trip": f"{total_trip_cost:,.0f} VND",
            "note": "(Ước tính chi phí tại điểm đến, chưa bao gồm vé máy bay/tàu xe liên tỉnh)."
        }

        dest_text = f" tại {destination}" if destination else ""
        summary = (
            f"[DỰ TOÁN NGÂN SÁCH THAM KHẢO{dest_text.upper()} ({tier.upper()} - {days} ngày {nights} đêm)]:\n"
            f"- Tổng chi phí ước tính: ~{total_per_person:,.0f} VND / người ({benchmark['desc']})\n"
            f"- Chi tiết định mức:\n"
            f"  + Chỗ ở ({nights} đêm): ~{lodging_cost:,.0f} VND\n"
            f"  + Ăn uống ({days} ngày): ~{food_cost:,.0f} VND\n"
            f"  + Đi lại nội địa ({days} ngày): ~{transport_cost:,.0f} VND\n"
            f"  + Vé tham quan & vui chơi: ~{activities_cost:,.0f} VND\n"
            f"- Lưu ý: Chưa bao gồm vé máy bay/xe khách liên tỉnh."
        )

        return {
            "success": True,
            "data": data,
            "error": None,
            "summary": summary
        }
