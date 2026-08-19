import time
import datetime
from typing import Any, Dict, List, Optional
from api_server.config import SYSTEM_PROMPT


class ContextMerger:
    """Bộ gộp ngữ cảnh thông minh cho AI Orchestrator."""

    @staticmethod
    def build_dynamic_prompt(
        user_message: str,
        tool_results: Dict[str, Dict[str, Any]],
        user_profile: Optional[Dict[str, Any]] = None,
        slots: Optional[Dict[str, Any]] = None,
        intent: str = "GENERAL_CHAT"
    ) -> str:
        """
        Ghép dữ liệu các Tool vào System Prompt kèm thời gian thực tế.
        """
        now = datetime.datetime.now()
        days_vn = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
        day_str = days_vn[now.weekday()]
        current_time_str = f"{day_str}, ngày {now.day:02d} tháng {now.month:02d} năm {now.year} (Giờ Việt Nam: {now.strftime('%H:%M')})"

        sections: List[str] = [
            SYSTEM_PROMPT.strip(),
            f"[THỜI GIAN THỰC TẾ]: Hôm nay là {current_time_str}. Khi người dùng hỏi về ngày/giờ, hãy trả lời chính xác theo mốc thời gian thực này."
        ]

        # 1. Ngữ cảnh Hồ sơ & Sở thích người dùng (Cá nhân hóa)
        profile_summary = tool_results.get("user_profile", {}).get("summary")
        if profile_summary and "chưa đăng nhập" not in profile_summary.lower():
            sections.append(
                f"\n[HỒ SƠ & SỞ THÍCH CÁ NHÂN HÓA CỦA NGƯỜI DÙNG]:\n"
                f"- {profile_summary}\n"
                f"- LƯU Ý: Hãy cá nhân hóa câu trả lời dựa trên sở thích, kiêng cữ và ngân sách này của người dùng!"
            )

        # 2. Ngữ cảnh Thời tiết thực tế & Quy tắc gợi ý
        weather_summary = tool_results.get("get_weather", {}).get("summary")
        if weather_summary:
            sections.append(f"\n{weather_summary}")

        # 3. Ngữ cảnh Tri thức Địa điểm RAG (17.147 POIs)
        rag_summary = tool_results.get("query_rag", {}).get("summary")
        if rag_summary and rag_summary.strip():
            sections.append(f"\n{rag_summary}")

        # 4. Ngữ cảnh Lịch trình mẫu từ Planner Engine (Rule + K-Means)
        planner_summary = tool_results.get("plan_itinerary", {}).get("summary")
        if planner_summary and planner_summary.strip():
            sections.append(f"\n{planner_summary}")

        # 5. Ngữ cảnh Nhật ký & Lịch sử chuyến đi
        diary_summary = tool_results.get("diary_service", {}).get("summary")
        if diary_summary and diary_summary.strip():
            sections.append(f"\n{diary_summary}")

        # 6. Chỉ dẫn cụ thể theo từng Intent
        if intent == "PLAN_ITINERARY":
            sections.append(
                "\n[HƯỚNG DẪN ĐẶC BIỆT KHI VIẾT LỊCH TRÌNH]:\n"
                "1. ĐIỂM XUẤT PHÁT: Nếu người dùng KHÔNG chỉ định rõ nơi xuất phát (ví dụ chỉ nói 'Hà Nội' hoặc 'Đà Nẵng'), TUYỆT ĐỐI KHÔNG tự ý giả định người dùng ở TP.HCM! Hãy tính toán theo tour tại chỗ hoặc ghi chú rõ: '(Dự toán di chuyển nội thành / chưa bao gồm vé liên tỉnh tùy nơi xuất phát của bạn)'.\n"
                "2. ĐỊA GIỚI HÀNH CHÍNH: CHỈ gợi ý các địa điểm thuộc đúng tỉnh thành điểm đến (Ví dụ: Hà Nội chỉ gợi ý Hồ Gươm, Phố Cổ, Văn Miếu, Hồ Tây, Lăng Bác, Bát Tràng... KHÔNG đưa Đền Hùng Phú Thọ hay Hòa Bình vào lịch trình Hà Nội).\n"
                "3. CHẤT LƯỢNG ĐỊA ĐIỂM: Chỉ giới thiệu danh lam thắng cảnh, di tích lịch sử nổi tiếng, quán ăn ngon, cafe view đẹp. KHÔNG đưa cơ quan công quyền, đồn công an hay trường học vào lịch trình du lịch.\n"
                "4. Trình bày lịch trình rõ ràng theo từng Ngày (Ngày 1, Ngày 2...).\n"
                "5. Mỗi hoạt động viết đúng 1 câu ngắn gọn, súc tích, hấp dẫn.\n"
                "6. KẾT THÚC: Hãy hỏi khách hàng có muốn điều chỉnh thêm gì không (đổi ngày, ngân sách, hoạt động) hay muốn chốt phương án này để lưu vào Balo hành trang."
            )
        elif intent == "CHECK_WEATHER":
            sections.append(
                "\n[HƯỚNG DẪN]: Tóm tắt nhanh thời tiết hiện tại và gợi ý hoạt động phù hợp (trong nhà/ngoài trời, mang ô/áo ấm) dựa trên quy tắc thời tiết trên."
            )
        elif intent == "EXPLORE_LOCATION":
            sections.append(
                "\n[HƯỚNG DẪN]: Cung cấp thông tin địa điểm chi tiết, giờ mở cửa, địa chỉ và món ăn đặc sắc dựa vào dữ liệu thực tế tra cứu được. Chỉ gợi ý các điểm đến thuộc đúng địa phương được hỏi."
            )

        return "\n\n".join(sections)
