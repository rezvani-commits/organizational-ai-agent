import json
from typing import List, Any
from langchain_groq import ChatGroq

from back.config import Config


class FollowupSuggester:
    def __init__(self, llm=None, max_suggestions: int = 3):

        self.llm = llm or ChatGroq(
            model=getattr(Config, "ROUTER_LLM_MODEL", Config.LLM_MODEL),
            temperature=0.3,
            api_key=Config.main_Model_Api_key,
        )
        self.max_suggestions = max_suggestions

    def suggest(self, query: str, answer: str, context: str = "") -> List[str]:
        # اگه کانتکست خالی/فقط space باشه (سلام‌واحوال‌پرسی، سند پیدا نشد، یا عدم دسترسی)
        # اصلاً سراغ LLM نریم و سوال پیشنهادی نسازیم
        if not context or not context.strip():
            return []

        context_section = f"\nمتن اسنادی که سیستم دقیقاً بهشون دسترسی داشته (تنها منبع مجاز برای سؤالات پیشنهادی):\n{context}\n"

        prompt = f"""شما در حال کمک به تولید سؤالات تکمیلی پیشنهادی برای یک دستیار پرسش‌وپاسخ اسناد حقوقی/سازمانی هستید.

با توجه به سؤال کاربر، پاسخی که دریافت کرده، و مهم‌تر از همه متن اسناد زیر، حداکثر
{self.max_suggestions} سؤال تکمیلی کوتاه و طبیعی پیشنهاد بده که کاربر ممکنه بخواد بعداً بپرسه.

قانون قطعی و غیرقابل‌چشم‌پوشی: هر سؤالی که پیشنهاد می‌دی باید جوابش **مستقیماً و به‌طور
صریح** در همون متن اسناد زیر موجود باشه - نه در دانش عمومی حقوقی/سازمانی، نه چیزی که
"احتمالاً" هم‌جور اسناد دیگه پوشش می‌دن. اگه در مورد یه موضوع مطمئن نیستی که جوابش
دقیقاً همین‌جا هست یا نه، اون سؤال رو پیشنهاد نده.

سایر معیارها:
- مستقیماً به موضوعی که الان بحث شده مرتبط باشن
- یک جنبه‌ی دیگه از **همین متن** (نه موضوع جدید بیرون از اون) رو بررسی کنن - نه صرفاً بازنویسی همون سؤال
- به شکل چیزی باشن که خودِ کاربر تایپ می‌کنه (اول‌شخص، مثل «در مورد ... چطور؟»، «چطور می‌تونم ...»)

اگه متن اسناد زیر آنقدر محدوده که حتی یک سؤال تکمیلیِ قابل‌پاسخ ازش درنمیاد، آرایه‌ی
خالی [] برگردون. تعداد کمتر از {self.max_suggestions} (حتی صفر) همیشه به یک سؤال
حدسی/نامطمئن ترجیح داره.
{context_section}
سؤال کاربر: {query}

پاسخ داده‌شده: {answer}

فقط یک آرایه‌ی JSON از رشته‌ها برگردون، بدون markdown و بدون متن اضافه. مثال:
["سؤال تکمیلی ۱؟", "سؤال تکمیلی ۲؟"]
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