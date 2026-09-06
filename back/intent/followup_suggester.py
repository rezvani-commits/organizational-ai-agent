"""
Follow-up Question Suggester
-----------------------------
مسئول تولید سؤالات تکمیلیِ پیشنهادی بعد از هر پاسخ، تا کاربر بتونه به‌راحتی
مکالمه رو ادامه بده بدون اینکه خودش سؤال بعدی رو از صفر فکر کنه.

از context بازیابی‌شده (اگه موجود باشه) استفاده می‌کنه تا پیشنهادها واقعاً
مرتبط با اطلاعاتی باشن که سیستم بهشون دسترسی داره، نه صرفاً حدس مدل.

نکته: این کلاس فعلاً به RAGGraph وصل نیست (نود جداگانه‌ای براش تعریف نشده).
اگه بخوای بعد از generate_answer_node صدا زده بشه و suggested_questions
تو خروجی run() قرار بگیره، بگو تا وصلش کنم.
"""

import json
from typing import List, Any
from langchain_groq import ChatGroq

from back.config import Config


class FollowupSuggester:
    def __init__(self, llm=None, max_suggestions: int = 3):
        """
        llm: مدلی که برای تولید پیشنهادها استفاده می‌شه. چون این کار صرفاً
             یه تولید متن کوتاه و ساده‌ست، منطقی‌ست از یه مدل سبک (مثل همون
             مدل روتر) استفاده کنی، نه مدل اصلی و گرون‌تر.
        max_suggestions: حداکثر تعداد سؤال پیشنهادی (پیش‌فرض ۳ تا)
        """
        self.llm = llm or ChatGroq(
            model=getattr(Config, "ROUTER_LLM_MODEL", Config.LLM_MODEL),
            temperature=0.3,
            api_key=Config.GROQ_API_KEY,
        )
        self.max_suggestions = max_suggestions

    def suggest(self, query: str, answer: str, context: str = "") -> List[str]:
        """
        بر اساس سؤال کاربر، پاسخ داده‌شده، و context بازیابی‌شده (اختیاری)،
        چند سؤال تکمیلی مرتبط پیشنهاد می‌ده.

        اگه به هر دلیلی (خطای API، پارس JSON و ...) شکست بخوره، لیست خالی
        برمی‌گردونه به‌جای raise کردن exception — چون این یه فیچر جانبیه
        و نباید کل پاسخ اصلی رو خراب کنه.
        """
        context_section = (
            f"\nاطلاعات مرتبطی که سیستم بهشون دسترسی داره:\n{context}\n"
            if context else ""
        )

        prompt = f"""شما در حال کمک به تولید سؤالات تکمیلی پیشنهادی برای یک دستیار پرسش‌وپاسخ اسناد حقوقی/سازمانی هستید.

با توجه به سؤال کاربر و پاسخی که دریافت کرده، {self.max_suggestions} سؤال تکمیلی کوتاه و طبیعی پیشنهاد بده که کاربر ممکنه بخواد بعداً بپرسه. این سؤالات باید:
- مستقیماً به موضوعی که الان بحث شده مرتبط باشن
- یک جنبه‌ی مرتبط، حالت خاص، یا گام منطقی بعدی رو بررسی کنن (نه صرفاً بازنویسی همون سؤال)
- به شکل چیزی باشن که خودِ کاربر تایپ می‌کنه (اول‌شخص، مثل «در مورد ... چطور؟»، «چطور می‌تونم ...»)
- با تکیه بر پایگاه دانش اسناد حقوقی/سازمانی قابل پاسخ باشن (از سؤالات نامرتبط/کلی پرهیز کن)
{context_section}
سؤال کاربر: {query}

پاسخ داده‌شده: {answer}

فقط یک آرایه‌ی JSON از رشته‌ها برگردون، بدون markdown و بدون متن اضافه. مثال:
["سؤال تکمیلی ۱؟", "سؤال تکمیلی ۲؟", "سؤال تکمیلی ۳؟"]
"""

        try:
            raw = self.llm.invoke(prompt)
            text = self._extract_text(raw.content).strip()

            # پاکسازی احتمالی از ```json ... ```
            if text.startswith("```"):
                text = text.strip("`")
                if text.lower().startswith("json"):
                    text = text[4:].strip()

            suggestions = json.loads(text)
            if not isinstance(suggestions, list):
                return []

            return [str(s).strip() for s in suggestions if str(s).strip()][: self.max_suggestions]

        except Exception as e:
            # لاگ موقت برای عیب‌یابی -- بعد از پیدا کردن علت مشکل حذفش کن
            print(f"⚠️ FollowupSuggester failed: {type(e).__name__}: {e}")
            return []

    @staticmethod
    def _extract_text(content: Any) -> str:
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