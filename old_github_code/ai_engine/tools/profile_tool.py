"""
ai_engine/tools/profile_tool.py
Tool truy xuất và cập nhật Hồ sơ cá nhân hóa (sở thích, dị ứng, phong cách, ngân sách).
"""
import asyncio
from typing import Any, Dict, Optional
import diary_service
from ai_engine.tools.base_tool import BaseTool


class ProfileTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="user_profile",
            description="Đọc và cập nhật hồ sơ sở thích cá nhân, phong cách du lịch, chế độ ăn uống và ngân sách của người dùng."
        )

    async def execute(
        self,
        action: str = "get",
        user_id: Optional[str] = None,
        profile_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Thực thi Tool Hồ sơ người dùng.
        action: 'get' | 'update'
        """
        if not user_id:
            # Fallback nếu chưa login hoặc chạy chế độ khách
            return {
                "success": True,
                "data": None,
                "summary": "Người dùng chưa đăng nhập hoặc đang dùng tài khoản khách."
            }

        try:
            if action == "get":
                profile = await asyncio.to_thread(diary_service.get_user_profile, user_id)
                if not profile:
                    return {
                        "success": True,
                        "data": None,
                        "summary": "Chưa có hồ sơ sở thích cá nhân cụ thể."
                    }

                summary_parts = []
                if profile.get("full_name"):
                    summary_parts.append(f"Họ tên: {profile['full_name']}")
                if profile.get("travel_style"):
                    summary_parts.append(f"Phong cách du lịch: {', '.join(profile['travel_style'])}")
                if profile.get("default_budget_tier"):
                    summary_parts.append(f"Ngân sách ưu tiên: {profile['default_budget_tier']}")
                if profile.get("food_allergies"):
                    summary_parts.append(f"Dị ứng / Kiêng cữ thực phẩm: {', '.join(profile['food_allergies'])}")
                if profile.get("special_requirements"):
                    summary_parts.append(f"Yêu cầu đặc biệt: {', '.join(profile['special_requirements'])}")
                if profile.get("frequent_companion"):
                    summary_parts.append(f"Đối tượng đi cùng thường xuyên: {profile['frequent_companion']}")

                summary_str = "; ".join(summary_parts) if summary_parts else "Hồ sơ mặc định."
                return {
                    "success": True,
                    "data": profile,
                    "summary": summary_str
                }

            elif action == "update" and profile_data:
                updated = await asyncio.to_thread(diary_service.update_user_profile, user_id, profile_data)
                return {
                    "success": True,
                    "data": updated,
                    "summary": "Đã cập nhật hồ sơ sở thích thành công."
                }

            return {
                "success": False,
                "data": None,
                "error": f"Hành động '{action}' không hợp lệ hoặc thiếu dữ liệu."
            }

        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "summary": "Không thể truy vấn hồ sơ người dùng."
            }
