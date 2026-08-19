"""
ai_engine/tools/rag_tool.py
Tool truy vấn dữ liệu từ 17.147 POIs (CSDL SQLite FTS5) cho AI Orchestrator.
"""
import asyncio
from typing import Any, Dict, Optional, List
from ai_engine.tools.base_tool import BaseTool
from planner.rag_engine import RagEngine
from api_server.config import BASE_DIR


class RagTool(BaseTool):
    def __init__(self, rag_engine: Optional[RagEngine] = None):
        super().__init__(
            name="query_rag",
            description="Truy vấn địa điểm thực tế, danh lam thắng cảnh, quán ăn, khách sạn từ CSDL 17.147 POIs."
        )
        if rag_engine is None:
            index_path = BASE_DIR / "data" / "locations_index.json"
            self.rag_engine = RagEngine(str(index_path))
            self.rag_engine.load_index()
        else:
            self.rag_engine = rag_engine

    async def execute(
        self,
        query: str = "",
        trip_data: Optional[Dict[str, Any]] = None,
        limit: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Thực thi tra cứu RAG Engine.
        - Nếu có trip_data (destination, days,...): Lọc địa điểm theo phân cụm & ngày.
        - Nếu có query text: Tìm kiếm ngữ nghĩa / FTS5 POIs.
        """
        try:
            if trip_data and (trip_data.get("destination") or trip_data.get("number_of_days") or trip_data.get("num_days")):
                # Tìm kiếm địa điểm cho lịch trình
                raw_text = await asyncio.to_thread(self.rag_engine.search_locations, trip_data)
                return {
                    "success": True,
                    "data": {"structured_search": True, "text": raw_text},
                    "summary": raw_text
                }
            elif query:
                # Tra cứu thông tin điểm đến / quán ăn theo câu hỏi
                knowledge_text = await asyncio.to_thread(self.rag_engine.query_knowledge, query, limit=limit)
                return {
                    "success": True,
                    "data": {"query": query, "text": knowledge_text},
                    "summary": knowledge_text
                }

            return {
                "success": True,
                "data": None,
                "summary": ""
            }

        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "summary": ""
            }
