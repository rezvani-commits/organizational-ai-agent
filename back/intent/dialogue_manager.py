from typing import List, Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_community.chat_message_histories import SQLChatMessageHistory
from sqlalchemy import create_engine

from back.config import Config


class DialogueManager:
    def __init__(
        self,
        llm=None,
        max_history_turns: Optional[int] = None,
        db_url: Optional[str] = None,
        table_name: Optional[str] = None,
    ):
        """
        llm: مدلی که برای rewrite کردن سؤالات تکمیلی استفاده می‌شه.
             می‌تونی همون مدل روتر (سبک) رو بدی چون این کار هم صرفاً یه
             تبدیل متن ساده‌ست، نه تولید محتوای پیچیده.
        max_history_turns: چند turn آخر مکالمه برای context در نظر گرفته بشه
                           (برای جلوگیری از رشد بی‌حد context/توکن).
        db_url: connection string استاندارد SQLAlchemy برای دیتابیس تاریخچه.
                پیش‌فرض یه فایل SQLite محلیه، ولی می‌تونی همین رو تو Config
                عوض کنی؛ مثال‌ها:
                    sqlite:///chat_history.db
                    postgresql+psycopg2://user:pass@host:5432/dbname
                    mysql+pymysql://user:pass@host:3306/dbname
        table_name: اسم جدولی که پیام‌ها توش ذخیره می‌شن (پیش‌فرض: "message_store").
        """
        self.llm = llm or ChatGroq(
            model=getattr(Config, "ROUTER_LLM_MODEL", Config.LLM_MODEL),
            temperature=0,
            api_key=Config.GROQ_API_KEY,
        )
        self.max_history_turns = max_history_turns or getattr(Config, "MAX_HISTORY_TURNS", 6)

        self.db_url = db_url or getattr(Config, "CHAT_HISTORY_DB_URL", "sqlite:///chat_history.db")
        self.table_name = table_name or getattr(Config, "CHAT_HISTORY_TABLE_NAME", "message_store")

        # یک Engine واحد با connection pool برای کل عمر DialogueManager می‌سازیم
        # (به‌جای اینکه هر بار SQLChatMessageHistory خودش یه connection جدید
        # به Postgres باز کنه). pool_pre_ping باعث می‌شه اگه connection قطع
        # شده بود (مثلاً idle timeout سمت DB)، خودکار reconnect بشه.
        self._engine = create_engine(
            self.db_url,
            pool_size=getattr(Config, "CHAT_HISTORY_POOL_SIZE", 5),
            max_overflow=getattr(Config, "CHAT_HISTORY_MAX_OVERFLOW", 10),
            pool_pre_ping=True,
        )

    # -----------------------------------------------------------------
    # ساخت آبجکت تاریخچه‌ی مخصوص یک session (روی همون engine مشترک)
    # -----------------------------------------------------------------
    def _get_history_store(self, session_id: str) -> SQLChatMessageHistory:
        # نکته: اگه نسخه‌ی langchain_community که نصبه، پارامتر
        # `connection` رو به‌جای `connection_string` بخواد، اسمش رو عوض کن؛
        # رفتار یکسانه (هر دو یک Engine/connection-string قبول می‌کنن).
        return SQLChatMessageHistory(
            session_id=session_id,
            connection=self._engine,
            table_name=self.table_name,
        )

    # -----------------------------------------------------------------
    # مدیریت تاریخچه
    # -----------------------------------------------------------------
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """کل تاریخچه‌ی ذخیره‌شده تو دیتابیس برای این session رو به فرمت
        [{"role": "user"|"assistant", "content": "..."}] برمی‌گردونه."""
        store = self._get_history_store(session_id)
        return [self._message_to_dict(m) for m in store.messages]

    def get_recent_history(self, session_id: str) -> List[Dict[str, str]]:
        """فقط N turn آخر (بر اساس max_history_turns) رو برمی‌گردونه - همینا
        برای ساخت پرامپت rewrite استفاده می‌شن تا توکن مصرفی کنترل بشه."""
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

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        if not history:
            return "(no previous conversation)"
        lines = []
        for turn in history:
            role_label = "User" if turn["role"] == "user" else "Assistant"
            lines.append(f"{role_label}: {turn['content']}")
        return "\n".join(lines)

    # -----------------------------------------------------------------
    # بازنویسی سؤال تکمیلی
    # -----------------------------------------------------------------
    def rewrite_query(self, session_id: str, query: str) -> Dict[str, Any]:
        """
        سؤال جدید کاربر رو با توجه به تاریخچه‌ی مکالمه (خونده‌شده از دیتابیس)
        بررسی می‌کنه:
        - اگه سؤال مستقل و کامل باشه، همون رو بدون تغییر برمی‌گردونه.
        - اگه سؤال تکمیلی/وابسته به context قبلی باشه (ضمیر، ارجاع، حذف بخشی از جمله)،
          یه نسخه‌ی مستقل و کامل ازش می‌سازه که بدون نیاز به تاریخچه قابل‌فهمه.

        خروجی:
            {"standalone_query": str, "was_rewritten": bool}
        """
        history = self.get_recent_history(session_id)

        # اگه اصلاً تاریخچه‌ای نیست، نیازی به rewrite نداریم
        if not history:
            return {"standalone_query": query, "was_rewritten": False}

        history_text = self._format_history(history)

        prompt = f"""You are a query rewriting assistant for a conversational RAG system.

Given the conversation history and the latest user question, decide if the latest question
depends on the previous conversation (e.g. uses pronouns like "it/that", refers back to a
previous topic, or is an incomplete follow-up).

If it depends on context: rewrite it into a fully standalone question that includes all
necessary context and can be understood without the conversation history.

If it is already a standalone, self-contained question: return it unchanged.

Respond with ONLY the final question text, nothing else — no quotes, no explanation, no markdown.

Conversation history:
{history_text}

Latest user question:
{query}

Standalone question:"""

        raw = self.llm.invoke(prompt)
        rewritten = self._extract_text(raw.content).strip().strip('"').strip()

        if not rewritten:
            # fail-safe: اگه مدل خروجی خالی داد، همون سؤال اصلی رو نگه می‌داریم
            return {"standalone_query": query, "was_rewritten": False}

        was_rewritten = rewritten.strip().lower() != query.strip().lower()
        return {"standalone_query": rewritten, "was_rewritten": was_rewritten}

    @staticmethod
    def _extract_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(item["text"])
                elif isinstance(item, str):
                    parts.append(item)
                else:
                    parts.append(str(item))
            return " ".join(parts)
        return str(content)


# ------------------------------------------------------------------------
# تست دستی اتصال به دیتابیس تاریخچه
# با این دستور از ریشه‌ی پروژه اجرا کن:
#     python -m back.intent.dialogue_manager
# ------------------------------------------------------------------------
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
        dm.clear_session(test_session)  # پاک‌سازی باقی‌مونده‌ی تست‌های قبلی
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
        dm.clear_session(test_session)  # پاک کردن رد پای تست از دیتابیس

    print("[۳/۳] همه‌چیز درسته 🎉 DialogueManager آماده‌ی استفاده است.")