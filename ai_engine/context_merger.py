"""
ai_engine/context_merger.py
Bộ gộp ngữ cảnh thông minh và tạo Prompt động cho Chatbot Tư vấn Du lịch BeeNavi AI.
"""
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
        intent: str = "GENERAL_TRAVEL_CHAT",
        is_voice_mode: bool = False
    ) -> str:
        """
        Ghép dữ liệu từ các Tool chuyên biệt vào System Prompt kèm thời gian thực tế.
        """
        now = datetime.datetime.now()
        days_vn = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
        day_str = days_vn[now.weekday()]
        current_time_str = f"{day_str}, ngày {now.day:02d} tháng {now.month:02d} năm {now.year} (Giờ Việt Nam: {now.strftime('%H:%M')})"

        sections: List[str] = [
            SYSTEM_PROMPT.strip(),
            f"[THỜI GIAN THỰC TẾ]: Hôm nay là {current_time_str}."
        ]

        # Chế độ Cuộc gọi Thoại & Chat Đa phương thức -> Tối ưu súc tích, phản xạ cực nhanh
        if is_voice_mode:
            sections.append(
                "[CHẾ ĐỘ TRÒ CHUYỆN ĐA PHƯƠNG THỨC (VOICE & TEXT CHAT)]:\n"
                "- Bạn đang trò chuyện tư vấn trực tiếp với khách hàng (hệ thống vừa hiển thị văn bản vừa phát âm thanh đọc câu trả lời).\n"
                "- Trả lời súc tích, tự nhiên, thân thiện, mạch lạc và giàu thông tin hữu ích.\n"
                "- QUY TẮC DẤU CÂU & NGỮ ĐIỆU CHO GIỌNG ĐỌC AI:\n"
                "  + Luôn sử dụng đầy đủ dấu chấm (.), dấu phẩy (,), dấu hỏi (?) và LUÔN CÁCH KHOẢNG TRẮNG sau mỗi dấu câu (Ví dụ: 'kế hoạch chi tiết nhé. Bạn muốn...' thay vì 'nhé.Bạn').\n"
                "  + TUYỆT ĐỐI KHÔNG dùng dấu gạch chéo (/) trong câu (Ví dụ: không viết 'ngày/đêm', 'xe/tàu', '1/2' mà hãy viết rõ 'ngày và đêm', 'xe hoặc tàu', '1 đến 2').\n"
                "- Trình bày đẹp mắt với các gạch đầu dòng ngắn gọn hoặc bôi đậm tên địa điểm/món ăn để người dùng dễ đọc.\n"
                "- TUYỆT ĐỐI KHÔNG bắt đầu bằng 'Chào bạn', 'Chào bạn!', 'Xin chào'. Hãy đi thẳng ngay vào câu trả lời, hoặc dùng các từ đệm tự nhiên như 'Được thôi,', 'Tuyệt vời,', 'Mình hiểu rồi,', 'Ok,'."
            )

        # 1. Ngữ cảnh Hồ sơ & Sở thích người dùng (Cá nhân hóa)
        profile_summary = tool_results.get("user_profile", {}).get("summary")
        if profile_summary and "chưa đăng nhập" not in profile_summary.lower():
            sections.append(
                f"\n[HỒ SƠ & SỞ THÍCH CỦA NGƯỜI DÙNG]:\n"
                f"- {profile_summary}\n"
                f"- LƯU Ý: Ưu tiên gợi ý phù hợp với sở thích, kiêng cữ và khẩu vị này của người dùng!"
            )

        # 2. Ngữ cảnh Thời tiết thực tế
        weather_summary = tool_results.get("get_weather", {}).get("summary")
        if weather_summary:
            sections.append(f"\n{weather_summary}")

        # 3. Ngữ cảnh Tri thức Địa điểm RAG (17.147 POIs)
        rag_summary = tool_results.get("query_rag", {}).get("summary")
        if rag_summary and rag_summary.strip():
            sections.append(f"\n{rag_summary}")

        # 4. Ngữ cảnh Bản đồ, Khoảng cách & Tuyến đường
        map_summary = tool_results.get("map_service", {}).get("summary")
        if map_summary and map_summary.strip():
            sections.append(f"\n{map_summary}")

        # 5. Ngữ cảnh Dự toán Ngân sách & Chi phí
        budget_summary = tool_results.get("budget_tool", {}).get("summary")
        if budget_summary and budget_summary.strip():
            sections.append(f"\n{budget_summary}")

        # 6. Ngữ cảnh Danh sách Hành lý & Đồ dùng cần chuẩn bị
        checklist_summary = tool_results.get("checklist_tool", {}).get("summary")
        if checklist_summary and checklist_summary.strip():
            sections.append(f"\n{checklist_summary}")

        # 7. Chỉ dẫn trọng tâm theo từng Intent
        if intent == "CHECK_WEATHER":
            sections.append(
                "\n[HƯỚNG DẪN TRẢ LỜI]: Tóm tắt ngắn gọn tình hình thời tiết, nhiệt độ hiện tại và đưa ra lời khuyên thiết thực (ví dụ: mang áo ấm, mang ô/dù, trang phục phù hợp)."
            )
        elif intent == "ASK_DISTANCE_TRANSPORT":
            sections.append(
                "\n[HƯỚNG DẪN TRẢ LỜI]: Nêu rõ cự ly (km), thời gian di chuyển ước tính và gợi ý phương tiện thuận tiện nhất (xe máy, taxi, đi bộ hoặc thuê xe)."
            )
        elif intent == "ASK_BUDGET_COST":
            sections.append(
                "\n[HƯỚNG DẪN TRẢ LỜI]: Tư vấn rõ ràng các khoản chi phí dự kiến (chỗ ở, ăn uống, đi lại, vé tham quan). Trình bày mạch lạc, dễ hiểu kèm mẹo tiết kiệm chi phí nếu có."
            )
        elif intent == "ASK_CHECKLIST_PACKING":
            sections.append(
                "\n[HƯỚNG DẪN TRẢ LỜI]: Liệt kê các vật dụng cần thiết theo danh mục (Giấy tờ, Thiết bị, Trang phục, Y tế cá nhân) phù hợp với thời tiết và đặc thù điểm đến."
            )
        elif intent == "EXPLORE_LOCATION":
            sections.append(
                "\n[HƯỚNG DẪN TRẢ LỜI]: Giới thiệu địa điểm hấp dẫn, điểm đặc sắc, món ăn ngon/đặc sản nên thử dựa trên dữ liệu thực tế đã tra cứu. Trả lời truyền cảm, hữu ích và chân thực."
            )
        else:
            sections.append(
                "\n[HƯỚNG DẪN TRẢ LỜI]: Đóng vai trò là một Chuyên gia Trợ lý Du lịch Việt Nam nhiệt tình, am hiểu văn hóa và địa phương. Giải đáp súc tích, thân thiện và chính xác."
            )

        return "\n\n".join(sections)
