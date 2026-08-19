"""
ai_engine/tools/base_tool.py
Định nghĩa Interface chuẩn cho mọi Tool trong hệ thống BeeNavi Orchestrator.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseTool(ABC):
    """Lớp trừu tượng cơ sở cho các công cụ của AI Orchestrator."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Hàm thực thi công cụ.
        Returns:
            Dict chứa 'success': bool, 'data': Any, 'error': Optional[str], 'summary': Optional[str]
        """
        pass
