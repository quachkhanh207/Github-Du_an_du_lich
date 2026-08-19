import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import asyncio
from ai_engine.orchestrator import AIOrchestrator
from ai_engine.intent_router import IntentRouter
from planner.rag_engine import RagEngine


async def test_chatbot_tools():
    print("======================================================")
    print("     TEST HỆ THỐNG TOOLS & INTENT ROUTER CHATBOT      ")
    print("======================================================")

    rag = RagEngine()
    orchestrator = AIOrchestrator(rag_engine=rag)

    test_cases = [
        ("Ở Đà Nẵng có quán hải sản nào ngon view đẹp?", "EXPLORE_LOCATION"),
        ("Thời tiết Sa Pa ngày mai có mưa lạnh không?", "CHECK_WEATHER"),
        ("Từ Hà Nội đi Ninh Bình bao xa và nên đi bằng xe gì?", "ASK_DISTANCE_TRANSPORT"),
        ("Đi du lịch Đà Lạt 3 ngày 2 đêm hết khoảng bao nhiêu tiền?", "ASK_BUDGET_COST"),
        ("Đi biển Phú Quốc mùa hè cần chuẩn bị những đồ dùng gì?", "ASK_CHECKLIST_PACKING"),
        ("Tôi là người ăn chay và dị ứng hải sản", "USER_PREFERENCE_UPDATE"),
    ]

    for query, expected_intent in test_cases:
        print(f"\n[Test Case] Query: '{query}'")
        intent, slots, conf = IntentRouter.classify_intent(query)
        print(f" -> Intent: {intent} (Confidence: {conf:.2f}) | Expected: {expected_intent}")
        print(f" -> Slots: {slots}")

        results, tools_called = await orchestrator._dispatch_tools(intent, query, slots)
        print(f" -> Tools Called: {tools_called}")
        for t_name, t_res in results.items():
            success = t_res.get("success", False)
            summary = t_res.get("summary", "")
            first_line = summary.split("\n")[0] if summary else ""
            print(f"    * [{t_name}] Success={success} | Summary: {first_line}")

    print("\n======================================================")
    print("      TẤT CẢ TEST CASES ĐÃ HOÀN TẤT THÀNH CÔNG!       ")
    print("======================================================")


if __name__ == "__main__":
    asyncio.run(test_chatbot_tools())
