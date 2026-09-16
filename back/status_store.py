"""
Status Store
------------
وضعیت لحظه‌ای پردازش هر session رو فقط در حافظه (نه دیتابیس) نگه می‌داره.
کاملاً جدا از back/session_store.py (که متادیتای دائمی سشن/عنوان رو روی
Postgres مدیریت می‌کنه) - این‌جا فقط وضعیت موقتِ «در حال انجام چه مرحله‌ای هستیم».

مناسب همین مقیاس (زیر ۱۰ کاربر هم‌زمان، تک‌پروسه) - بدون Redis.
"""

import threading
import time
from typing import Dict, Optional, TypedDict


class StatusEntry(TypedDict):
    step: str
    updated_at: float
    error_message: Optional[str]


_lock = threading.Lock()
_status: Dict[str, StatusEntry] = {}

# نگاشت اسم نود گراف (دقیقاً همون اسم‌هایی که تو RAGGraph._build_graph با
# workflow.add_node ثبت شدن) -> متن نمایشی فارسی.
# عمداً این‌جا نگه داشته شده تا تغییر آینده‌ی گراف مستقیم UI رو خراب نکنه.
NODE_LABELS = {
    "rewrite_query": "بازنویسی سؤال",
    "analyze_query": "تحلیل سؤال",
    "process_multi_query": "پردازش چند سؤال",
    "direct_response": "آماده‌سازی پاسخ",
    "calculator": "محاسبه",
    "calendar": "بررسی تاریخ",
    "clarify": "آماده‌سازی سؤال تکمیلی",
    "summarize": "خلاصه‌سازی",
    "compare": "مقایسه",
    "retrieve": "جستجو در اسناد",
    "generate_context": "آماده‌سازی اطلاعات مرتبط",
    "generate_answer": "تولید پاسخ",
    "response_validator": "ارزیابی پاسخ",
}

DEFAULT_LABEL = "در حال پردازش"
ERROR_STEP = "error"


def set_step(session_id: str, node_name: str) -> None:
    """با اسم یک نود گراف، وضعیت نمایشی متناظرش رو ثبت می‌کنه."""
    label = NODE_LABELS.get(node_name, DEFAULT_LABEL)
    with _lock:
        _status[session_id] = {
            "step": label,
            "updated_at": time.time(),
            "error_message": None,
        }


def set_error(session_id: str, message: str = "") -> None:
    with _lock:
        _status[session_id] = {
            "step": ERROR_STEP,
            "updated_at": time.time(),
            "error_message": message,
        }


def get_status(session_id: str) -> Optional[StatusEntry]:
    with _lock:
        entry = _status.get(session_id)
        return dict(entry) if entry else None


def clear(session_id: str) -> None:
    """بعد از پایان موفق/ناموفق پردازش صدا زده می‌شه تا حافظه رشد نکنه."""
    with _lock:
        _status.pop(session_id, None)