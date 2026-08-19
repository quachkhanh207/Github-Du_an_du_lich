"""
ai_engine/orchestrator.py
Bộ điều phối trung tâm (AI Orchestrator) cho hệ thống BeeNavi.
Phân tích Ý định -> Thực thi Tool song song -> Ghép ngữ cảnh -> Gọi LLM Qwen3-4B Streaming -> Lưu trữ State.
"""
import asyncio
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from ai_engine.brain import Brain
from ai_engine.context_merger import ContextMerger
from ai_engine.conversation_state import ConversationStateManager
from ai_engine.intent_router import IntentRouter
from ai_engine.tools.diary_tool import DiaryTool
from ai_engine.tools.planner_tool import PlannerTool
from ai_engine.tools.profile_tool import ProfileTool
from ai_engine.tools.rag_tool import RagTool
from ai_engine.tools.weather_tool import WeatherTool
from planner.rag_engine import RagEngine


class AIOrchestrator:
    """Lớp điều phối trung tâm cho toàn bộ luồng AI và Tools của BeeNavi."""

    def __init__(
        self,
        brain: Optional[Brain] = None,
        rag_engine: Optional[RagEngine] = None,
        state_manager: Optional[ConversationStateManager] = None
    ):
        self.brain = brain
        self.rag_engine = rag_engine
        self.state_manager = state_manager or ConversationStateManager()

        # Khởi tạo các Tool
        self.profile_tool = ProfileTool()
        self.rag_tool = RagTool(rag_engine=self.rag_engine)
        self.weather_tool = WeatherTool()
        self.planner_tool = PlannerTool(rag_engine=self.rag_engine)
        self.diary_tool = DiaryTool()

    async def _dispatch_tools(
        self,
        intent: str,
        user_text: str,
        slots: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
        """
        Thực thi các tool song song bất đồng bộ tùy theo Intent và Slots.
        """
        tasks = {}
        tool_names = []

        # 1. Luôn truy xuất hồ sơ cá nhân hóa (nếu có user_id)
        if user_id:
            tasks["user_profile"] = self.profile_tool.execute(action="get", user_id=user_id)
            tool_names.append("user_profile")

        destination = slots.get("destination")
        num_days = slots.get("num_days", 3)
        budget = slots.get("budget", "Tiêu chuẩn")
        trip_type = slots.get("trip_type", "Khám phá")

        # 2. Xử lý theo từng Intent
        if intent == "PLAN_ITINERARY":
            if destination:
                tasks["get_weather"] = self.weather_tool.execute(destination=destination)
                tool_names.append("get_weather")

                # Lấy trước weather nếu cần hoặc chạy cùng lúc
                trip_payload = {
                    "destination": destination,
                    "number_of_days": num_days,
                    "num_days": num_days,
                    "budget": budget,
                    "trip_type": trip_type
                }
                tasks["query_rag"] = self.rag_tool.execute(trip_data=trip_payload)
                tasks["plan_itinerary"] = self.planner_tool.execute(
                    destination=destination,
                    number_of_days=num_days,
                    budget=budget,
                    trip_type=trip_type
                )
                tool_names.extend(["query_rag", "plan_itinerary"])

        elif intent == "EXPLORE_LOCATION":
            if destination:
                tasks["get_weather"] = self.weather_tool.execute(destination=destination)
                tool_names.append("get_weather")
            tasks["query_rag"] = self.rag_tool.execute(query=user_text, limit=6)
            tool_names.append("query_rag")

        elif intent == "CHECK_WEATHER":
            dest_for_weather = destination or "Hà Nội"
            tasks["get_weather"] = self.weather_tool.execute(destination=dest_for_weather)
            tool_names.append("get_weather")

        elif intent == "MANAGE_DIARY":
            tasks["diary_service"] = self.diary_tool.execute(action="get_trips", user_id=user_id)
            tool_names.append("diary_service")

        elif intent == "USER_PREFERENCE_UPDATE":
            # Cập nhật trực tiếp sở thích nếu có
            if user_id and slots.get("dietary_restrictions"):
                tasks["user_profile_update"] = self.profile_tool.execute(
                    action="update",
                    user_id=user_id,
                    profile_data={"food_allergies": slots.get("dietary_restrictions")}
                )
                tool_names.append("user_profile_update")

        elif intent == "GENERAL_CHAT":
            # Tự động kích hoạt RAG Agent nếu người dùng hỏi về điểm đến, ẩm thực, vui chơi
            if destination or any(kw in user_text.lower() for kw in ["ở đâu", "quán", "chơi", "ăn", "đi đâu", "đẹp", "du lịch", "khách sạn", "địa điểm", "chùa", "bãi", "biển"]):
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
        explicit_trip_data: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Xử lý toàn bộ chu trình hội thoại và sinh token streaming kèm Live Map Sync, Checklist và Budget Breakdown.
        Yields:
            Dict chứa: {"type": "token"|"clarification"|"final", "text": str, ...}
        """
        session_id = session_id or str(uuid.uuid4())
        session = self.state_manager.get_or_create_session(session_id, user_id)
        current_slots = session.get("slots", {})

        # Nếu có dữ liệu trip_data tường minh từ form client truyền vào
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

        # 2. Xử lý Slot Clarification (Hỏi lại nếu thiếu thông tin bắt buộc)
        if intent == "PLAN_ITINERARY" and not active_slots.get("destination"):
            clarification_msg = "Bạn muốn lên lịch trình khám phá tỉnh thành hoặc địa điểm nào tại Việt Nam? (Ví dụ: Đà Nẵng, Sa Pa, Đà Lạt, Phú Quốc...)"
            self.state_manager.save_message(
                session_id=session_id,
                role="user",
                content=user_text,
                intent=intent,
                user_id=user_id
            )
            self.state_manager.save_message(
                session_id=session_id,
                role="assistant",
                content=clarification_msg,
                intent=intent,
                user_id=user_id
            )
            self.state_manager.update_session_slots(session_id, {}, pending_action="AWAITING_DESTINATION")
            yield {
                "type": "answer",
                "text": clarification_msg,
                "intent": intent,
                "slots": active_slots,
                "session_id": session_id
            }
            return

        # 3. Kích hoạt Tool Dispatcher song song
        tool_results, tool_names = await self._dispatch_tools(
            intent=intent,
            user_text=user_text,
            slots=active_slots,
            user_id=user_id
        )

        # 4. Gộp ngữ cảnh vào Dynamic System Prompt
        dynamic_prompt = ContextMerger.build_dynamic_prompt(
            user_message=user_text,
            tool_results=tool_results,
            slots=active_slots,
            intent=intent
        )

        # Lấy lịch sử hội thoại gần nhất
        history = self.state_manager.get_recent_history(session_id=session_id, limit=6)

        # Lưu tin nhắn người dùng vào CSDL
        self.state_manager.save_message(
            session_id=session_id,
            role="user",
            content=user_text,
            intent=intent,
            tools_called=tool_names,
            user_id=user_id
        )

        # 5. Trích xuất Metadata Tối Ưu Hóa (Live Map, Budget, Checklist)
        weather_data = tool_results.get("get_weather", {}).get("data")
        structured_itinerary = tool_results.get("plan_itinerary", {}).get("data")

        map_markers = []
        budget_breakdown = None
        smart_checklist = None
        data_tier = None
        coverage_note = None

        if structured_itinerary:
            map_markers = structured_itinerary.get("map_markers", [])
            budget_breakdown = structured_itinerary.get("budget_breakdown")
            smart_checklist = structured_itinerary.get("smart_checklist")
            data_tier = structured_itinerary.get("data_tier")
            coverage_note = structured_itinerary.get("coverage_note")

        if not self.brain:
            fallback_ans = f"Xin chào! Tôi đã nhận thông tin về {active_slots.get('destination', 'chuyến đi của bạn')}. Hệ thống đã điều phối các công cụ thành công!"
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
                "weather": weather_data,
                "structured_itinerary": structured_itinerary,
                "map_markers": map_markers,
                "budget_breakdown": budget_breakdown,
                "smart_checklist": smart_checklist,
                "data_tier": data_tier,
                "coverage_note": coverage_note,
                "session_id": session_id,
                "tools_called": tool_names
            }
            return

        full_answer = ""
        loop = asyncio.get_event_loop()

        def run_sync_stream():
            return list(self.brain.stream(
                user_text=user_text,
                history=history,
                custom_system_prompt=dynamic_prompt
            ))

        stream_chunks = await loop.run_in_executor(None, run_sync_stream)

        for chunk in stream_chunks:
            if chunk and chunk.strip():
                full_answer = chunk.strip()
                yield {
                    "type": "partial_answer",
                    "text": full_answer,
                    "intent": intent,
                    "session_id": session_id
                }

        if not full_answer:
            full_answer = f"Chào bạn! Tôi là BeeNavi AI. Tôi có thể hỗ trợ bạn tìm kiếm địa điểm, lên lịch trình và kiểm tra thời tiết tại {active_slots.get('destination', 'Việt Nam')}."

        # Lưu câu trả lời của AI vào CSDL
        self.state_manager.save_message(
            session_id=session_id,
            role="assistant",
            content=full_answer,
            intent=intent,
            tools_called=tool_names,
            user_id=user_id
        )

        # Trả về kết quả hoàn chỉnh cuối cùng
        yield {
            "type": "answer",
            "text": full_answer,
            "intent": intent,
            "slots": active_slots,
            "weather": weather_data,
            "structured_itinerary": structured_itinerary,
            "map_markers": map_markers,
            "budget_breakdown": budget_breakdown,
            "smart_checklist": smart_checklist,
            "data_tier": data_tier,
            "coverage_note": coverage_note,
            "session_id": session_id,
            "tools_called": tool_names
        }
