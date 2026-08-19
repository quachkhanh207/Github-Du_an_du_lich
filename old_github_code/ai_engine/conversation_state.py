"""
ai_engine/conversation_state.py
Module quản lý Trạng thái Hội thoại (Conversation State), Session Slots và Bộ nhớ ngắn hạn/dài hạn cho BeeNavi AI.
Lưu trữ trên SQLite đảm bảo bền vững và phục hồi ngữ cảnh sau mỗi lượt trò chuyện.
"""
import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from api_server.config import BASE_DIR

DB_PATH = BASE_DIR / "data" / "user_diary.db"


class ConversationStateManager:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Khởi tạo bảng theo dõi session state và slot filling nếu chưa có."""
        conn = self._get_connection()
        c = conn.cursor()

        # 1. Bảng Chat Sessions lưu trữ slots hiện tại (destination, days, budget,...)
        c.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT,
            current_intent TEXT,
            slots_json TEXT DEFAULT '{}',
            pending_action TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # 2. Cập nhật bảng chat_messages để có thêm metadata intent & tools_called nếu chưa có
        c.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            intent TEXT,
            tools_called_json TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Migration an toàn nếu bảng chat_messages đã tồn tại từ trước nhưng thiếu cột
        existing_cols = [r["name"] for r in c.execute("PRAGMA table_info(chat_messages)").fetchall()]
        if "intent" not in existing_cols:
            c.execute("ALTER TABLE chat_messages ADD COLUMN intent TEXT")
        if "tools_called_json" not in existing_cols:
            c.execute("ALTER TABLE chat_messages ADD COLUMN tools_called_json TEXT DEFAULT '[]'")

        conn.commit()
        conn.close()

    def get_or_create_session(self, session_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Lấy session hiện tại hoặc tạo mới nếu chưa tồn tại."""
        conn = self._get_connection()
        c = conn.cursor()

        row = c.execute("SELECT * FROM chat_sessions WHERE session_id = ?", (session_id,)).fetchone()
        if not row:
            now_str = time.strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""
                INSERT INTO chat_sessions (session_id, user_id, current_intent, slots_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, user_id, "GENERAL_CHAT", "{}", now_str))
            conn.commit()
            conn.close()
            return {
                "session_id": session_id,
                "user_id": user_id,
                "current_intent": "GENERAL_CHAT",
                "slots": {},
                "pending_action": None
            }

        session_data = dict(row)
        conn.close()

        try:
            session_data["slots"] = json.loads(session_data.get("slots_json") or "{}")
        except Exception:
            session_data["slots"] = {}

        return session_data

    def update_session_slots(
        self,
        session_id: str,
        new_slots: Dict[str, Any],
        intent: Optional[str] = None,
        pending_action: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cập nhật các slot tích lũy trong phiên hội thoại."""
        current = self.get_or_create_session(session_id, user_id)
        merged_slots = current.get("slots", {})
        
        # Chỉ ghi đè slot nếu có giá trị mới hợp lệ
        for k, v in new_slots.items():
            if v is not None and v != "":
                merged_slots[k] = v

        current_intent = intent or current.get("current_intent", "GENERAL_CHAT")
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        conn = self._get_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE chat_sessions
            SET current_intent = ?, slots_json = ?, pending_action = ?, updated_at = ?
            WHERE session_id = ?
        """, (current_intent, json.dumps(merged_slots, ensure_ascii=False), pending_action, now_str, session_id))
        conn.commit()
        conn.close()

        merged_slots_copy = dict(merged_slots)
        return {
            "session_id": session_id,
            "user_id": user_id or current.get("user_id"),
            "current_intent": current_intent,
            "slots": merged_slots_copy,
            "pending_action": pending_action
        }

    def clear_session_slots(self, session_id: str):
        """Xóa trắng các slots khi người dùng bắt đầu một yêu cầu hoàn toàn mới."""
        conn = self._get_connection()
        c = conn.cursor()
        c.execute("UPDATE chat_sessions SET slots_json = '{}', pending_action = NULL WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: Optional[str] = None,
        tools_called: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ):
        """Lưu tin nhắn vào lịch sử hội thoại."""
        msg_id = str(uuid.uuid4())
        tools_json = json.dumps(tools_called or [], ensure_ascii=False)

        conn = self._get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO chat_messages (id, user_id, session_id, role, content, intent, tools_called_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (msg_id, user_id, session_id, role, content, intent, tools_json))
        conn.commit()
        conn.close()

    def get_recent_history(self, session_id: str, limit: int = 6) -> List[Dict[str, str]]:
        """Lấy danh sách tin nhắn gần nhất để đưa vào ngữ cảnh LLM."""
        conn = self._get_connection()
        c = conn.cursor()
        rows = c.execute("""
            SELECT role, content
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (session_id, limit)).fetchall()
        conn.close()

        history = [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
        return history
