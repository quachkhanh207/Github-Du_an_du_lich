"""
ai_engine/orchestrator.py
Bộ điều phối trung tâm (AI Orchestrator) cho Chatbot Tư vấn Du lịch BeeNavi.
Phân tích Ý định -> Thực thi Tool chuyên biệt song song -> Ghép ngữ cảnh -> Gọi LLM Qwen3-4B Streaming -> Lưu trữ State độc lập.
"""
import asyncio
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from ai_engine.brain import Brain
from ai_engine.context_merger import ContextMerger
from ai_engine.conversation_state import ConversationStateManager
from ai_engine.intent_router import IntentRouter
from ai_engine.tools.budget_tool import BudgetTool
from ai_engine.tools.checklist_tool import ChecklistTool
from ai_engine.tools.map_tool import MapTool
from ai_engine.tools.profile_tool import ProfileTool
from ai_engine.tools.rag_tool import RagTool
from ai_engine.tools.weather_tool import WeatherTool
from planner.rag_engine import RagEngine
from api_server.config import LLM_MAX_TOKENS_VOICE


class AIOrchestrator:
    """Lớp điều phối trung tâm cho Chatbot Tư vấn Du lịch BeeNavi AI."""

    def __init__(
        self,
        brain: Optional[Brain] = None,
        rag_engine: Optional[RagEngine] = None,
        state_manager: Optional[ConversationStateManager] = None
    ):
        self.brain = brain
        self.rag_engine = rag_engine
        self.state_manager = state_manager or ConversationStateManager()

        # Khởi tạo bộ 6 Tool chuyên biệt cho Chatbot tư vấn
        self.profile_tool = ProfileTool()
        self.rag_tool = RagTool(rag_engine=self.rag_engine)
        self.weather_tool = WeatherTool()
        self.map_tool = MapTool()
        self.budget_tool = BudgetTool()
        self.checklist_tool = ChecklistTool()

    async def _dispatch_tools(
        self,
        intent: str,
        user_text: str,
        slots: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
        """
        Thực thi các tool song song bất đồng bộ tùy theo Intent và Slots tư vấn.
        """
        tasks = {}
        tool_names = []

        # 1. Luôn truy xuất hồ sơ cá nhân hóa (nếu user đã đăng nhập)
        if user_id:
            tasks["user_profile"] = self.profile_tool.execute(action="get", user_id=user_id)
            tool_names.append("user_profile")

        destination = slots.get("destination")
        origin = slots.get("origin")
        num_days = slots.get("num_days", 1)
        budget = slots.get("budget", "Tiêu chuẩn")
        trip_type = slots.get("trip_type", "Khám phá")
        transport = slots.get("transport", "Xe máy")

        # 2. Phân phối Tool theo từng Intent tư vấn
        if intent == "CHECK_WEATHER":
            dest_for_weather = destination or "Hà Nội"
            tasks["get_weather"] = self.weather_tool.execute(destination=dest_for_weather)
            tool_names.append("get_weather")

        elif intent == "ASK_DISTANCE_TRANSPORT":
            if origin and destination:
                tasks["map_service"] = self.map_tool.execute(origin=origin, destination=destination)
                tool_names.append("map_service")
            elif destination:
                tasks["map_service"] = self.map_tool.execute(destination=destination)
                tasks["query_rag"] = self.rag_tool.execute(query=user_text, limit=4)
                tool_names.extend(["map_service", "query_rag"])

        elif intent == "ASK_BUDGET_COST":
            tasks["budget_tool"] = self.budget_tool.execute(
                budget_tier=budget,
                num_days=num_days,
                destination=destination,
                num_people=slots.get("num_people", 1)
            )
            tasks["query_rag"] = self.rag_tool.execute(query=user_text, limit=4)
            tool_names.extend(["budget_tool", "query_rag"])

        elif intent == "ASK_CHECKLIST_PACKING":
            if destination:
                tasks["get_weather"] = self.weather_tool.execute(destination=destination)
                tool_names.append("get_weather")
            tasks["checklist_tool"] = self.checklist_tool.execute(
                weather_tag=slots.get("weather_tag"),
                trip_type=trip_type,
                transport=transport,
                destination=destination
            )
            tool_names.append("checklist_tool")

        elif intent == "EXPLORE_LOCATION":
            if destination:
                tasks["get_weather"] = self.weather_tool.execute(destination=destination)
                tool_names.append("get_weather")
            tasks["query_rag"] = self.rag_tool.execute(query=user_text, limit=6)
            tool_names.append("query_rag")

        elif intent == "USER_PREFERENCE_UPDATE":
            if user_id and slots.get("dietary_restrictions"):
                tasks["user_profile_update"] = self.profile_tool.execute(
                    action="update",
                    user_id=user_id,
                    profile_data={"food_allergies": slots.get("dietary_restrictions")}
                )
                tool_names.append("user_profile_update")

        elif intent == "GENERAL_TRAVEL_CHAT":
            # Tự động kích hoạt RAG nếu người dùng hỏi về điểm đến, ẩm thực, vui chơi, khách sạn
            if destination or any(kw in user_text.lower() for kw in [
                "ở đâu", "quán", "chơi", "ăn", "đi đâu", "đẹp", "du lịch", "khách sạn",
                "địa điểm", "chùa", "bãi", "biển", "vé", "đặc sản", "kinh nghiệm", "review"
            ]):
                tasks["query_rag"] = self.rag_tool.execute(query=user_text, limit=4)
                tool_names.append("query_rag")

        if not tasks:
            return {}, []

        # Chạy đồng thời tất cả các tasks cần thiết
        keys = list(tasks.keys())
        results_list = await asyncio.gather(*[tasks[k] for k in keys], return_exceptions=True)

        tool_results = {}
        for k, res in zip(keys, results_list):
            if isinstance(res, Exception):
                tool_results[k] = {"success": False, "error": str(res), "summary": ""}
            else:
                tool_results[k] = res

        return tool_results, tool_names

    async def stream_chat(
        self,
        user_text: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        explicit_trip_data: Optional[Dict[str, Any]] = None,
        is_voice_mode: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Xử lý chu trình trò chuyện tư vấn và sinh token streaming.
        Yields:
            Dict chứa: {"type": "token"|"metadata"|"answer", "text": str, ...}
        """
        session_id = session_id or str(uuid.uuid4())
        session = self.state_manager.get_or_create_session(session_id, user_id)
        current_slots = session.get("slots", {})

        if explicit_trip_data:
            current_slots.update(explicit_trip_data)

        # 1. Phân loại Intent & Bóc tách Slots
        intent, extracted_slots, confidence = IntentRouter.classify_intent(user_text, current_slots)
        updated_session = self.state_manager.update_session_slots(
            session_id=session_id,
            new_slots=extracted_slots,
            intent=intent,
            user_id=user_id
        )
        active_slots = updated_session.get("slots", {})

        # 2. Kích hoạt Tool Dispatcher song song
        tool_results, tool_names = await self._dispatch_tools(
            intent=intent,
            user_text=user_text,
            slots=active_slots,
            user_id=user_id
        )

        # 3. Gộp ngữ cảnh vào Dynamic System Prompt
        dynamic_prompt = ContextMerger.build_dynamic_prompt(
            user_message=user_text,
            tool_results=tool_results,
            slots=active_slots,
            intent=intent,
            is_voice_mode=is_voice_mode
        )

        # Lấy lịch sử hội thoại gần nhất để duy trì mạch nói chuyện
        history = self.state_manager.get_recent_history(session_id=session_id, limit=6)

        # Lưu tin nhắn người dùng vào CSDL hội thoại
        self.state_manager.save_message(
            session_id=session_id,
            role="user",
            content=user_text,
            intent=intent,
            tools_called=tool_names,
            user_id=user_id
        )

        # 4. Trích xuất Metadata trả kèm cho Client (Weather, Map, Budget, Checklist)
        weather_data = tool_results.get("get_weather", {}).get("data")
        map_data = tool_results.get("map_service", {}).get("data")
        budget_data = tool_results.get("budget_tool", {}).get("data")
        checklist_data = tool_results.get("checklist_tool", {}).get("data")
        rag_data = tool_results.get("query_rag", {}).get("data")

        # Gửi sự kiện mở đầu kèm metadata nếu có
        yield {
            "type": "start",
            "intent": intent,
            "session_id": session_id,
            "tools_called": tool_names,
            "metadata": {
                "weather": weather_data,
                "map": map_data,
                "budget": budget_data,
                "checklist": checklist_data,
                "rag_pois": rag_data if isinstance(rag_data, list) else None
            }
        }

        # 5. Sinh phản hồi qua LLM Brain (Streaming)
        if not self.brain:
            fallback_ans = (
                f"Tôi đã ghi nhận câu hỏi của bạn về "
                f"'{active_slots.get('destination', user_text)}' và sẵn sàng giải đáp thêm các thông tin về địa điểm, ăn uống, thời tiết, chi phí và đồ đạc cần mang theo!"
            )
            self.state_manager.save_message(
                session_id=session_id,
                role="assistant",
                content=fallback_ans,
                intent=intent,
                user_id=user_id
            )
            yield {
                "type": "answer",
                "text": fallback_ans,
                "intent": intent,
                "slots": active_slots,
                "session_id": session_id
            }
            return

        full_response_text = []
        try:
            max_toks = LLM_MAX_TOKENS_VOICE if is_voice_mode else None
            async for token in self.brain.generate_stream(
                prompt=user_text,
                system_prompt=dynamic_prompt,
                history=history,
                max_tokens=max_toks
            ):
                full_response_text.append(token)
                yield {
                    "type": "token",
                    "text": token,
                    "intent": intent,
                    "session_id": session_id
                }

            complete_text = "".join(full_response_text).strip()

            # Lưu câu trả lời của AI vào CSDL
            self.state_manager.save_message(
                session_id=session_id,
                role="assistant",
                content=complete_text,
                intent=intent,
                tools_called=tool_names,
                user_id=user_id
            )

            # Gửi gói kết thúc
            yield {
                "type": "final",
                "text": complete_text,
                "intent": intent,
                "slots": active_slots,
                "session_id": session_id
            }

        except Exception as e:
            err_msg = f"Đã xảy ra lỗi khi tạo phản hồi tư vấn: {e}"
            yield {
                "type": "error",
                "text": err_msg,
                "session_id": session_id
            }
