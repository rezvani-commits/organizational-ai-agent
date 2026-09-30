import re
import ast
import json
import difflib
import operator
import datetime

from typing import TypedDict, List, Dict, Any, Optional

from back.intent.reference_normalizer import normalize_legal_references
from back.intent.date_reference_normalizer import normalize_dates_in_query


class QueryPart(TypedDict):
    query: str
    intent: str


_CALC_CHARS_PATTERN = re.compile(r'^[\d\s\.\+\-\*/\(\)%\^]+$')
_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("عبارت ریاضی نامعتبر است")


_FA_CHAR_MAP = str.maketrans({
    "ك": "ک", "ي": "ی", "ة": "ه", "ؤ": "و", "إ": "ا", "أ": "ا", "آ": "ا",
    "ۀ": "ه", "‌": " ", "‍": "", "ٔ": "", "ّ": "", "ْ": "", "ِ": "",
    "َ": "", "ُ": "", "ً": "", "ٍ": "", "ٌ": "",
})
_REPEATED_CHAR_PATTERN = re.compile(r'(.)\1+')
_MULTI_SPACE_PATTERN = re.compile(r'\s+')


def _normalize_fa(text: str) -> str:
    text = text.translate(_FA_CHAR_MAP)
    text = _REPEATED_CHAR_PATTERN.sub(r'\1', text)
    text = _MULTI_SPACE_PATTERN.sub(' ', text).strip().lower()
    return text


class QueryAnalyzer:

    INTENT_GREETING = "greeting"
    INTENT_RAG = "rag"
    INTENT_SUMMARIZE = "summarize"
    INTENT_COMPARE = "compare"
    INTENT_CALENDAR = "calendar"
    INTENT_CALCULATOR = "calculator"
    INTENT_AMBIGUOUS = "ambiguous"
    INTENT_UNCLEAR = "unclear"

    VALID_INTENTS = {
        INTENT_GREETING, INTENT_RAG, INTENT_SUMMARIZE, INTENT_COMPARE,
        INTENT_CALENDAR, INTENT_CALCULATOR, INTENT_AMBIGUOUS, INTENT_UNCLEAR,
    }

    _GREETING_EXACT = {
        "سلام", "سلاام", "درود", "صبح بخیر", "عصر بخیر", "شب بخیر",
        "خداحافظ", "بای", "فعلا", "ممنون", "مرسی", "متشکرم", "تشکر",
        "خیلی ممنون", "سپاس", "hi", "hello", "hey", "thanks", "thank you", "bye",
    }

    _GREETING_NORMALIZED = {_normalize_fa(w) for w in _GREETING_EXACT}
    _GREETING_FUZZY_THRESHOLD = 0.78
    _GREETING_MAX_LEN = max(len(w) for w in _GREETING_NORMALIZED) + 4

    def __init__(self, llm, max_sub_questions: int = 5):
        self.llm = llm
        self.max_sub_questions = max_sub_questions


    def try_fast_calculator(self, text: str) -> Optional[str]:
        cleaned = text.strip().replace("^", "**")
        if not cleaned or not _CALC_CHARS_PATTERN.match(text.strip()):
            return None
        if not any(ch.isdigit() for ch in cleaned):
            return None
        try:
            tree = ast.parse(cleaned, mode="eval")
            result = _safe_eval(tree.body)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return f"نتیجه: {result}"
        except Exception:
            return None

    def try_fast_calendar(self, text: str) -> Optional[str]:
        q = _normalize_fa(text.strip())
        now = datetime.datetime.now()
        weekday_fa = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
        if re.search(r"امروز\s*(چند\s*شنبه|چه\s*روزی)", q):
            return f"امروز {weekday_fa[now.weekday()]} ({now.strftime('%Y-%m-%d')}) است."
        if re.search(r"(ساعت\s*(چنده|چند\s*است|الان))", q):
            return f"الان ساعت {now.strftime('%H:%M')} است."
        if re.search(r"امروز\s*چندم", q):
            return f"تاریخ امروز {now.strftime('%Y-%m-%d')} است."
        return None

    def try_fast_greeting(self, text: str) -> bool:
        cleaned = text.strip().strip("!.،؟?")
        normalized = _normalize_fa(cleaned)
        if not normalized:
            return False
        if normalized in self._GREETING_NORMALIZED:
            return True
        if len(normalized) > self._GREETING_MAX_LEN:
            return False
        best_ratio = max(
            difflib.SequenceMatcher(None, normalized, candidate).ratio()
            for candidate in self._GREETING_NORMALIZED
        )
        return best_ratio >= self._GREETING_FUZZY_THRESHOLD

    def _closest_greeting_word(self, text: str) -> Optional[str]:
        cleaned = text.strip().strip("!.،؟?")
        normalized = _normalize_fa(cleaned)
        if not normalized:
            return None
        best_word, best_ratio = None, 0.0
        for word in self._GREETING_EXACT:
            ratio = difflib.SequenceMatcher(None, normalized, _normalize_fa(word)).ratio()
            if ratio > best_ratio:
                best_word, best_ratio = word, ratio
        return best_word




    def resolve_query(self, query: str, history_text: str) -> Dict[str, Any]:
        normalized_query = normalize_dates_in_query(normalize_legal_references(query))

        prompt = f"""شما دستیار رفع‌ابهام و بازنویسی سؤال در یک سیستم پرسش‌وپاسخ اسناد سازمانی هستید. خروجی فقط یک JSON معتبر، بدون توضیح و بدون markdown.

            مراحل:
            ۱. is_unclear=true فقط زمانی که پیام کاملاً بی‌معنی و تصادفی باشد (حروف/کلمات رندوم، کیبورد قاطی‌شده، بدون هیچ معنای قابل‌فهم).
            توجه مهم: یک سؤال کوتاه، کلی یا ناقص - even اگر جزئیات کافی نداشته باشد - is_unclear نیست، چون معنا و قصد کاربر از پیام کاملاً مشخصه؛ تشخیص کامل‌بودن یا ناقص‌بودنش به مرحله‌ی بعدی تحلیل سپرده می‌شود، نه اینجا.

            مثال:
            "قوانینش چیه؟" -> is_unclear: false (سؤال واقعی و مبهمه، ولی معنا داره)
            "نمیدونم چی بپرسم" -> is_unclear: false (جمله‌ی معنادار فارسیه)
            "سلام" -> is_unclear: false
            "asdkj asdkj 123 !!! qwlekj" -> is_unclear: true (بی‌معنی محض، بدون هیچ کلمه‌ی قابل‌فهم)

            ۲. در غیر این صورت: با کمک تاریخچه، ضمایر و ارجاعات مبهم را resolve کن و غلط‌های تایپی را تصحیح کن تا یک نسخه‌ی standalone و مستقل از تاریخچه بسازی. اگر پیام از قبل standalone بود، بدون تغییر برگردان.

            مهم: اگر سؤال ذاتاً مبهم است (موضوع یا مرجع آن اصلاً مشخص نیست، نه فقط ضمیر آن)، هنگام بازنویسی این ابهام را با کلمات پرکننده‌ی بی‌معنا مثل «این موضوع»، «آن مورد»، «مسئله‌ی مذکور» پنهان نکن. ابهام واقعی باید در نسخه‌ی نهایی هم کاملاً قابل‌تشخیص بماند تا تحلیل بعدی بتواند آن را ambiguous تشخیص دهد.

            مثال:
            "قوانینش چیه؟" (بدون تاریخچه) -> استاندالون درست: "قوانین مربوط به چه موضوعی؟" (ابهام حفظ شده)
            "قوانینش چیه؟" (بدون تاریخچه) -> استاندالون غلط: "قوانین این موضوع چیست؟" (ابهام با پرکننده قایم شده - این را انجام نده)

            فرمت خروجی عادی:
            {{"is_unclear": false, "standalone_query": "<نسخه‌ی نهایی>"}}

            تاریخچه‌ی مکالمه:
            {history_text}

            پیام کاربر: "{normalized_query}"
            """

        try:
            raw = self.llm.invoke(prompt)
            text = raw.content if hasattr(raw, "content") else str(raw)
        except Exception:
            return {
                "is_unclear": False,
                "standalone_query": normalized_query,
                "was_rewritten": normalized_query.strip() != query.strip(),
            }

        parsed = self._parse_json(text if isinstance(text, str) else str(text))
        if not parsed:
            return {
                "is_unclear": False,
                "standalone_query": normalized_query,
                "was_rewritten": normalized_query.strip() != query.strip(),
            }

        if parsed.get("is_unclear"):
            return {"is_unclear": True, "standalone_query": query, "was_rewritten": False}

        standalone_query = str(parsed.get("standalone_query") or normalized_query).strip() or normalized_query
        was_rewritten = standalone_query.strip().lower() != query.strip().lower()

        return {"is_unclear": False, "standalone_query": standalone_query, "was_rewritten": was_rewritten}


    def classify_and_split(self, standalone_query: str) -> Dict[str, Any]:
        prompt = f"""شما تحلیل‌گر نوع پرسش در یک سیستم پرسش‌وپاسخ اسناد سازمانی/حقوقی هستید. خروجی فقط یک JSON معتبر، بدون توضیح و بدون markdown.

۱. اگر پیام شامل چند سؤال کاملاً مستقل است (هرکدام بدون نیاز به پاسخ بقیه قابل‌پاسخ)، به بخش‌های جدا بشکن (حداکثر {self.max_sub_questions} بخش). اگر بخش‌ها به‌هم وابسته‌اند یا شک داری، نشکن (یک بخش کافیست).

۲. برای هر بخش، دقیقاً یکی از این intentها را بده:
   - greeting: احوال‌پرسی/تشکر/گفت‌وگوی عمومی بدون نیاز به اطلاعات خاص
   - summarize: درخواست خلاصه‌سازی یک متن یا سند
   - compare: مقایسه‌ی دو یا چند چیز با هم
   - calendar: سؤال درباره‌ی تاریخ، روز هفته، یا زمان
   - calculator: یک محاسبه یا مسئله‌ی عددی
   - ambiguous: سؤال ناقص/کلی که بدون اطلاعات بیشتر قابل پاسخ دقیق نیست
   - rag: هر سؤال دیگر که برای پاسخ دقیق نیاز به جست‌وجو در اسناد داخلی دارد (پیش‌فرض)

مثال‌ها برای تشخیص درست‌تر:
"تفاوت X و Y چیست؟" -> intent: compare
"X را با Y مقایسه کن" -> intent: compare
"شباهت‌ها و تفاوت‌های X و Y رو بگو" -> intent: compare
"خلاصه‌ای از X بگو" -> intent: summarize
"X رو خلاصه کن" -> intent: summarize
"چکیده‌ی سند X چیه" -> intent: summarize

فرمت خروجی:
{{"parts": [{{"query": "<متن بخش>", "intent": "<یکی از موارد بالا>"}}]}}

پیام: "{standalone_query}"
"""

        try:
            raw = self.llm.invoke(prompt)
            text = raw.content if hasattr(raw, "content") else str(raw)
        except Exception:
            return self._fallback_single(standalone_query)

        parsed = self._parse_json(text if isinstance(text, str) else str(text))
        if not parsed:
            return self._fallback_single(standalone_query)

        parts_raw = parsed.get("parts") or []
        parts: List[QueryPart] = []
        for p in parts_raw[: self.max_sub_questions]:
            if not isinstance(p, dict):
                continue
            q_text = str(p.get("query", "")).strip()
            intent = str(p.get("intent", self.INTENT_RAG)).strip().lower()
            if intent not in self.VALID_INTENTS:
                intent = self.INTENT_RAG
            if q_text:
                parts.append({"query": q_text, "intent": intent})

        if not parts:
            parts = [{"query": standalone_query, "intent": self.INTENT_RAG}]

        is_multi = len(parts) > 1
        result: Dict[str, Any] = {
            "parts": parts,
            "is_multi_query": is_multi,
            "sub_queries": [p["query"] for p in parts],
        }
        if not is_multi:
            result["intent"] = parts[0]["intent"]
        return result

    def _fallback_single(self, query: str) -> Dict[str, Any]:
        part: QueryPart = {"query": query, "intent": self.INTENT_RAG}
        return {
            "parts": [part],
            "is_multi_query": False,
            "sub_queries": [query],
            "intent": self.INTENT_RAG,
        }

    @staticmethod
    def _parse_json(text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        cleaned = text.strip()
        cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", cleaned, flags=re.MULTILINE).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return None