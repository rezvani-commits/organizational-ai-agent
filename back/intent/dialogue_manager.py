from typing import List, Dict, Any, Optional

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_community.chat_message_histories import SQLChatMessageHistory
from sqlalchemy import create_engine

from back.config import Config


class DialogueManager:
    """
    فقط مسئول ذخیره/بازیابی تاریخچه‌ی مکالمه است.
    بازنویسی سؤال دیگر اینجا انجام نمی‌شود؛ این کار حالا داخل
    QueryAnalyzer.analyze_with_context انجام می‌شود (ادغام با تحلیل intent
    برای کم‌کردن یک کال LLM جدا).
    """

    def __init__(
        self,
        max_history_turns: Optional[int] = None,
        db_url: Optional[str] = None,
        table_name: Optional[str] = None,
    ):
        self.max_history_turns = max_history_turns or getattr(Config, "MAX_HISTORY_TURNS", 6)

        self.db_url = db_url or getattr(Config, "CHAT_HISTORY_DB_URL", "sqlite:///chat_history.db")
        self.table_name = table_name or getattr(Config, "CHAT_HISTORY_TABLE_NAME", "message_store")

        self._engine = create_engine(
            self.db_url,
            pool_size=getattr(Config, "CHAT_HISTORY_POOL_SIZE", 5),
            max_overflow=getattr(Config, "CHAT_HISTORY_MAX_OVERFLOW", 10),
            pool_pre_ping=True,
        )

    def _get_history_store(self, session_id: str) -> SQLChatMessageHistory:
        return SQLChatMessageHistory(
            session_id=session_id,
            connection=self._engine,
            table_name=self.table_name,
        )

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        store = self._get_history_store(session_id)
        return [self._message_to_dict(m) for m in store.messages]

    def get_recent_history(self, session_id: str) -> List[Dict[str, str]]:
        history = self.get_history(session_id)
        max_messages = self.max_history_turns * 2
        return history[-max_messages:] if len(history) > max_messages else history

    def add_turn(self, session_id: str, role: str, content: str) -> None:
        """role: 'user' یا 'assistant'"""
        store = self._get_history_store(session_id)
        if role == "user":
            store.add_user_message(content)
        else:
            store.add_ai_message(content)

    def clear_session(self, session_id: str) -> None:
        store = self._get_history_store(session_id)
        store.clear()

    @staticmethod
    def _message_to_dict(message: BaseMessage) -> Dict[str, str]:
        role = "user" if isinstance(message, HumanMessage) else "assistant"
        return {"role": role, "content": message.content}

    def format_history(self, history: List[Dict[str, str]]) -> str:
        if not history:
            return "(no previous conversation)"
        lines = []
        for turn in history:
            role_label = "User" if turn["role"] == "user" else "Assistant"
            lines.append(f"{role_label}: {turn['content']}")
        return "\n".join(lines)


if __name__ == "__main__":
    import sys
    from sqlalchemy import text

    print("[۱/۳] در حال تست اتصال خام به دیتابیس...")
    try:
        dm = DialogueManager()
        with dm._engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("      ✅ اتصال خام به دیتابیس با موفقیت برقرار شد.")
    except Exception as exc:
        print(f"      ❌ اتصال به دیتابیس شکست خورد: {exc}")
        print("      -> connection string، یوزر/پسورد، و باز بودن پورت رو چک کن.")
        sys.exit(1)

    print("[۲/۳] در حال نوشتن و خواندن یک پیام تستی (بدون نیاز به LLM)...")
    try:
        test_session = "connection-test-session"
        dm.clear_session(test_session)
        dm.add_turn(test_session, "user", "سلام، این یک پیام تستیه")
        dm.add_turn(test_session, "assistant", "سلام! پیام تستی با موفقیت ذخیره شد.")

        history = dm.get_history(test_session)
        assert len(history) == 2, f"انتظار ۲ پیام بود، ولی {len(history)} تا برگشت"
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

        print("      ✅ نوشتن و خواندن از جدول message_store با موفقیت انجام شد.")
        print(f"      تاریخچه‌ی ذخیره‌شده: {history}")
    except Exception as exc:
        print(f"      ❌ خواندن/نوشتن پیام شکست خورد: {exc}")
        sys.exit(1)
    finally:
        dm.clear_session(test_session)

    print("[۳/۳] همه‌چیز درسته 🎉 DialogueManager آماده‌ی استفاده است.")