import threading
import time
from typing import Dict, Optional, TypedDict


class StatusEntry(TypedDict):
    step: str
    updated_at: float
    error_message: Optional[str]


_lock = threading.Lock()
_status: Dict[str, StatusEntry] = {}
NODE_LABELS = {
"fast_intent_check": "در حال تشخیص نوع درخواست...",
  "rewrite_query": "در حال پردازش سؤال...",
  "analyze_query": "در حال تحلیل سؤال...",
  "retrieve": "در حال جستجو در اسناد...",
  "generate_context": "در حال آماده‌سازی اطلاعات مرتبط...",
  "generate_answer": "در حال تولید پاسخ...",
  "response_validator": "در حال ارزیابی پاسخ...",
  "calculator": "در حال محاسبه...",
  "calendar": "در حال بررسی تاریخ...",
  "summarize": "در حال خلاصه‌سازی...",
  "compare": "در حال مقایسه...",
  "clarify": "در حال آماده‌سازی سؤال تکمیلی...",
  "direct_response": "در حال پاسخ‌گویی...",
  "no_docs_response": "در حال بررسی سطح دسترسی...",
  "process_multi_query": "در حال پردازش چند سؤال...",
}

DEFAULT_LABEL = "در حال پردازش"
ERROR_STEP = "error"


def set_step(session_id: str, node_name: str) -> None:
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
    with _lock:
        _status.pop(session_id, None)