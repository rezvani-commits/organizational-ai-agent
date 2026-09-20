from typing import Any, Optional

from back.config import Config


class AnswerGenerator:

    def __init__(self, llm):
        self.llm = llm

    def _extract_text(self, content: Any) -> str:
        """تبدیل امن خروجی مدل (حتی اگر لیست یا آبجکت باشد) به متن رشته‌ای"""
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

    def _build_feedback_note(self, previous_feedback: Optional[dict]) -> str:
        """
        اگه تلاش قبلی به خاطر faithfulness/relevance رد شده بود، دلیلش رو
        به شکل یک یادداشت برای مدل آماده می‌کنه تا توی تلاش بعدی اصلاح کنه.
        previous_feedback همون validation_result تلاش قبلیه (یا None/خالی).
        """
        if not previous_feedback:
            return ""

        if previous_feedback.get("retry_reason") != "faithfulness_relevance":
            return ""

        f_reason = previous_feedback.get("faithfulness", {}).get("reason", "")
        r_reason = previous_feedback.get("relevance", {}).get("reason", "")

        return f"""

توجه: پاسخ قبلی شما به این دلایل رد شد:
- مشکل در صحت/وفاداری به منبع: {f_reason}
- مشکل در ارتباط با سؤال: {r_reason}
مطمئن شو پاسخ جدید فقط بر اساس «متن مرجع» زیر باشه و مستقیماً به سؤال کاربر پاسخ بده."""

    def generate(self, query: str, context: str, previous_feedback: Optional[dict] = None) -> str:
        feedback_note = self._build_feedback_note(previous_feedback)

        prompt = f"""شما یک دستیار پاسخ‌گویی متخصص در اسناد حقوقی و سازمانی هستید.

فقط بر اساس اطلاعاتی که در «متن مرجع» زیر آمده به سؤال کاربر پاسخ بده.
اگر پاسخ در متن مرجع موجود نبود، دقیقاً همین عبارت را برگردان: "{Config.NOT_FOUND_PHRASE}"
{feedback_note}

متن مرجع:
{context}

سؤال کاربر:
{query}

پاسخ (دقیق و مختصر):"""

        raw_response = self.llm.invoke(prompt)
        return self._extract_text(raw_response.content)