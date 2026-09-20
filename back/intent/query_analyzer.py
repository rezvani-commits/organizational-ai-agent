import re
import ast
import operator
import datetime

from typing import TypedDict, List, Dict, Any, Optional


class QueryPart(TypedDict):
    query: str  # نسخه‌ی standalone این بخش (ارجاعات مبهم resolve شده)
    intent: str  # یکی از QueryAnalyzer.VALID_INTENTS


# ----------------------------------------------------------------------
# ماشین‌حساب امن (بدون eval خام) - برای fast-path بدون کال LLM
# ----------------------------------------------------------------------
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


class QueryAnalyzer:
    """
    تشخیص intent (+ split کردن سؤالات ترکیبی) برای پیام کاربر.

    اول چند fast-path ارزون (بدون LLM) رو امتحان می‌کنه: greeting دقیق،
    عبارت ریاضی خالص، الگوهای رایج تاریخ/ساعت. فقط اگه هیچ‌کدوم match
    نکرد، یک کال LLM برای split+intent می‌زنه.

    این fast-path ها (try_fast_calculator/try_fast_calendar) از بیرون
    (مثلاً calculator_node/calendar_node توی rag_graph.py) هم صدا زده
    می‌شن تا خودِ جواب رو (نه فقط تشخیص intent) بدون LLM بسازن.
    """

    INTENT_GREETING = "greeting"      # احوال‌پرسی/تشکر/گفت‌وگوی عمومی
    INTENT_RAG = "rag"                # نیاز به جست‌وجو در اسناد داخلی
    INTENT_SUMMARIZE = "summarize"    # خلاصه‌سازی متن/سند
    INTENT_COMPARE = "compare"        # مقایسه‌ی دو یا چند چیز
    INTENT_CALENDAR = "calendar"      # سؤال درباره‌ی تاریخ/روز/زمان
    INTENT_CALCULATOR = "calculator"  # محاسبه‌ی عددی
    INTENT_AMBIGUOUS = "ambiguous"    # سؤال ناقص -> باید سؤال تکمیلی پرسید

    VALID_INTENTS = {
        INTENT_GREETING, INTENT_RAG, INTENT_SUMMARIZE, INTENT_COMPARE,
        INTENT_CALENDAR, INTENT_CALCULATOR, INTENT_AMBIGUOUS,
    }

    # چند تا کلمه‌ی خیلی رایج سلام/تشکر که نیازی به کال LLM برای تشخیصشون نیست
    _GREETING_EXACT = {
        "سلام", "سلاام", "درود", "صبح بخیر", "عصر بخیر", "شب بخیر",
        "خداحافظ", "بای", "فعلا", "ممنون", "مرسی", "متشکرم", "تشکر",
        "خیلی ممنون", "سپاس", "hi", "hello", "hey", "thanks", "thank you", "bye",
    }

    def __init__(self, llm, max_sub_questions: int = 5):
        self.llm = llm
        self.max_sub_questions = max_sub_questions

    # ------------------------------------------------------------------
    # fast-path‌های بدون LLM
    # ------------------------------------------------------------------
    def try_fast_calculator(self, text: str) -> Optional[str]:
        """اگه پیام فقط یک عبارت ریاضی خالص باشه (بدون هیچ کلمه‌ای)،
        بدون هیچ کال LLM محاسبه و برگردونده می‌شه."""
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
        """الگوهای خیلی رایج تاریخ/ساعت رو بدون LLM جواب می‌ده."""
        q = text.strip()
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
        cleaned = text.strip().strip("!.،؟?").lower()
        return cleaned in self._GREETING_EXACT

    # ------------------------------------------------------------------
    # تحلیل ترکیبی: split کردن سؤالات + تشخیص intent
    # ------------------------------------------------------------------
    def analyze(self, query: str) -> Dict[str, Any]:
        """
        خروجی: dict با کلیدهای parts / is_multi_query / sub_queries، و اگه
        تک‌بخشی بود، standalone_query / intent هم داره (برای سازگاری مستقیم
        با ساختار RAGState).
        """
        if self.try_fast_greeting(query):
            part: QueryPart = {"query": query, "intent": self.INTENT_GREETING}
            return self._single_part_result(query, part)

        if self.try_fast_calculator(query) is not None:
            part = {"query": query, "intent": self.INTENT_CALCULATOR}
            return self._single_part_result(query, part)

        if self.try_fast_calendar(query) is not None:
            part = {"query": query, "intent": self.INTENT_CALENDAR}
            return self._single_part_result(query, part)

        prompt = f"""پیام کاربر رو تحلیل کن. دو کار باید انجام بدی:

۱) تشخیص بده پیام باید به چند بخش مستقل شکسته بشه یا نه:
   - اگه یک سؤال/درخواست واحده -> همون یک بخش.
   - اگه چند سؤال مستقل داره (هرکدوم بدون نیاز به جواب بقیه قابل پاسخه) ->
     به همون تعداد بخش بشکن و ضمایر مبهم رو با موضوع واقعی جایگزین کن.
   - اگه بخش‌ها زنجیره‌ای/وابسته به‌هم هستن -> نشکن، یک بخش در نظر بگیر.
     در صورت شک، نشکن.
   - حداکثر {self.max_sub_questions} بخش.

۲) برای هر بخش، intent‌ش رو مشخص کن - دقیقاً یکی از این‌ها:
   - greeting: سلام/خداحافظی/تشکر/گفت‌وگوی عمومی بدون نیاز به اطلاعات خاص.
   - summarize: درخواست خلاصه کردن یک متن یا سند.
   - compare: مقایسه‌ی دو یا چند چیز با هم.
   - calendar: سؤال درباره‌ی تاریخ، روز هفته، یا زمان.
   - calculator: یک محاسبه یا مسئله‌ی عددی.
   - ambiguous: سؤال ناقص/کلی‌ای که بدون اطلاعات بیشتر از کاربر نمی‌شه
     دقیق جوابش داد (باید سؤال تکمیلی پرسیده بشه).
   - rag: هر سؤال دیگه‌ای که برای جواب دقیق نیاز به جست‌وجو در اسناد/
     دانش‌نامه‌ی داخلی داره (پیش‌فرض وقتی هیچ‌کدوم از موارد بالا صدق نمی‌کنه).

خروجی رو دقیقاً به این فرم بده (بدون توضیح اضافه)، برای هر بخش یک بلاک،
با یک خط خالی بین بلاک‌ها:

INTENT: <greeting|summarize|compare|calendar|calculator|ambiguous|rag>
QUERY: <متن standalone این بخش>

پیام کاربر: "{query}"

خروجی:"""

        try:
            raw = self.llm.invoke(prompt)
            text = raw.content if hasattr(raw, "content") else str(raw)
        except Exception:
            # امن‌ترین fallback: تک‌بخشی و rag
            fallback_part: QueryPart = {"query": query, "intent": self.INTENT_RAG}
            return self._single_part_result(query, fallback_part)

        parts = self._parse_analysis_output(text, fallback_query=query)
        parts = parts[: self.max_sub_questions]
        is_multi = len(parts) > 1

        result: Dict[str, Any] = {
            "parts": parts,
            "is_multi_query": is_multi,
            "sub_queries": [p["query"] for p in parts],
        }

        if not is_multi:
            result["standalone_query"] = parts[0]["query"]
            result["intent"] = parts[0]["intent"]

        return result

    @staticmethod
    def _single_part_result(query: str, part: QueryPart) -> Dict[str, Any]:
        return {
            "parts": [part],
            "is_multi_query": False,
            "sub_queries": [query],
            "standalone_query": query,
            "intent": part["intent"],
        }

    def _parse_analysis_output(self, text: str, fallback_query: str) -> List[QueryPart]:
        parts: List[QueryPart] = []
        current_intent: Optional[str] = None

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            match_intent = re.match(r"(?i)^intent\s*:\s*(.+)$", line)
            if match_intent:
                current_intent = match_intent.group(1).strip().lower()
                continue

            match_query = re.match(r"(?i)^query\s*:\s*(.+)$", line)
            if match_query:
                query_text = match_query.group(1).strip()
                intent = self.INTENT_RAG
                if current_intent:
                    for candidate in self.VALID_INTENTS:
                        if candidate in current_intent:
                            intent = candidate
                            break
                if query_text:
                    parts.append({"query": query_text, "intent": intent})
                current_intent = None

        if not parts:
            parts = [{"query": fallback_query, "intent": self.INTENT_RAG}]

        return parts
