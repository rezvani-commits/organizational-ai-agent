import json
import re
from typing import Any, Dict, Optional

from back.config import Config

SUGGESTIONS_DELIMITER = "===SUGGESTED_QUESTIONS==="


class AnswerGenerator:

    def __init__(self, llm):
        self.llm = llm

    def _extract_text(self, content: Any) -> str:
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

    @staticmethod
    def _parse_suggestions(raw_suggestions_text: str) -> list:
        cleaned = raw_suggestions_text.strip()
        cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", cleaned, flags=re.MULTILINE).strip()
        try:
            suggestions = json.loads(cleaned)
        except json.JSONDecodeError:
            return []
        if not isinstance(suggestions, list):
            return []
        return [str(s).strip() for s in suggestions if str(s).strip()][:3]

    def generate(self, query: str, context: str, previous_feedback: Optional[dict] = None) -> Dict[str, Any]:
        feedback_note = self._build_feedback_note(previous_feedback)

        prompt = f"""شما یک دستیار پاسخ‌گویی رسمی و متخصص در اسناد حقوقی و سازمانی هستید. لحن پاسخ باید رسمی، مؤدبانه و اداری باشد.

فقط بر اساس اطلاعاتی که در «متن مرجع» زیر آمده به سؤال کاربر پاسخ بده.
اگر پاسخ در متن مرجع موجود نبود، دقیقاً همین عبارت را به‌عنوان کل پاسخ بنویس: "{Config.NOT_FOUND_PHRASE}"
{feedback_note}
پاسخ را دقیقاً به همین شکل بنویس، بدون هیچ‌گونه escape کردن نقل‌قول یا کاراکتر خاص:

[پاسخ کامل شما اینجا، متن خام و عادی، با نقل‌قول‌های داخل متن مرجع دقیقاً همان‌طور که هستند]

{SUGGESTIONS_DELIMITER}
["سؤال پیشنهادی ۱", "سؤال پیشنهادی ۲", "سؤال پیشنهادی ۳"]

اگر پاسخ معتبر تولید کردی، حداکثر ۳ سؤال تکمیلی کوتاه بعد از خط {SUGGESTIONS_DELIMITER} به‌صورت آرایه‌ی JSON بنویس که پاسخشان مستقیماً در متن مرجع موجود باشد.
اگر پاسخ NOT_FOUND بود، بعد از خط {SUGGESTIONS_DELIMITER} فقط [] بنویس.
هرگز خط {SUGGESTIONS_DELIMITER} را داخل خودِ پاسخ استفاده نکن؛ فقط یک‌بار، درست قبل از آرایه‌ی سؤالات.

متن مرجع:
{context}

سؤال کاربر:
{query}
"""

        raw_response = self.llm.invoke(prompt)
        raw_text = self._extract_text(raw_response.content)

        if SUGGESTIONS_DELIMITER in raw_text:
            answer_part, _, suggestions_part = raw_text.partition(SUGGESTIONS_DELIMITER)
            answer = answer_part.strip()
            suggestions = self._parse_suggestions(suggestions_part)
        else:
            answer = raw_text.strip()
            suggestions = []

        return {"answer": answer, "suggested_questions": suggestions}