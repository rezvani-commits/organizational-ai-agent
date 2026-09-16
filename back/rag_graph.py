import re
import ast
import time
import uuid
import operator
import datetime
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from back.config import Config
from back.ResponseValidator import ResponseValidator
from back.rag.hybrid_retriever_langchain import HybridRetriever  # <-- retrieval هیبرید (dense + BM25)
from back.rag.answer_generator import AnswerGenerator
from back.intent.dialogue_manager import DialogueManager  # <-- تاریخچه + query rewriting
from back.intent.followup_suggester import FollowupSuggester

from typing import TypedDict, List, Dict, Any, Optional, Callable


class QueryPart(TypedDict):
    query: str  # نسخه‌ی standalone این بخش (ارجاعات مبهم resolve شده)
    intent: str  # یکی از RAGGraph.VALID_INTENTS


class RAGState(TypedDict):
    query: str  # سؤال خام همونطور که کاربر تایپ کرده
    standalone_query: str  # سؤال بعد از rewrite (اگه لازم بود)
    was_rewritten: bool
    session_id: str

    parts: List[QueryPart]  # خروجی تحلیل ترکیبی split+intent
    is_multi_query: bool
    sub_queries: List[str]  # فقط برای نمایش/لاگ - معادل متنی parts

    intent: str  # فقط برای مسیر تک‌سؤالی
    retrieved_docs: List[Dict]
    context: str
    response: str
    validation_result: Dict[str, Any]
    retry_count: int
    is_satisfied: bool
    top_k: int
    max_retries: int


# ----------------------------------------------------------------------
# ماشین‌حساب امن (بدون eval خام) - برای مسیر calculator بدون کال LLM
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


class RAGGraph:
    # ------------------------------------------------------------------
    # دسته‌بندی‌های intent
    # ------------------------------------------------------------------
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

    # این‌ها تنها intent‌هایی هستن که وارد حلقه‌ی کامل retrieve/generate/validate
    # (با retry) می‌شن. بقیه برای صرفه‌جویی در توکن فقط یک پاس اجرا می‌شن.
    RETRIEVAL_LOOP_INTENTS = {INTENT_RAG}

    # حداکثر تعداد بخشی که تو یک پیام قبول می‌کنیم بشکنیم
    MAX_SUB_QUESTIONS = getattr(Config, "MAX_SUB_QUESTIONS", 5)

    # آستانه‌ی طول متن برای تشخیص «متن مستقیماً داخل پیام» در summarize
    INLINE_SUMMARY_MIN_CHARS = getattr(Config, "INLINE_SUMMARY_MIN_CHARS", 250)

    # چند تا کلمه‌ی خیلی رایج سلام/تشکر که نیازی به کال LLM برای تشخیصشون نیست
    _GREETING_EXACT = {
        "سلام", "سلاام", "درود", "صبح بخیر", "عصر بخیر", "شب بخیر",
        "خداحافظ", "بای", "فعلا", "ممنون", "مرسی", "متشکرم", "تشکر",
        "خیلی ممنون", "سپاس", "hi", "hello", "hey", "thanks", "thank you", "bye",
    }

    def __init__(self, llm=None, retriever: Optional[HybridRetriever] = None):
        """
        llm: مدل اصلی پاسخ‌دهی. اگه ندی، از Config.LLM_MODEL ساخته می‌شه.
        retriever: اگه از قبل یک HybridRetriever ساخته‌ای (مثلاً برای تست یا
                   share کردن بین چند RAGGraph)، می‌تونی بدیش تا دوباره
                   Chroma/BM25 از صفر لود نشه. اگه ندی، خودش با مسیرهای
                   Config یکی می‌سازه.
        """
        self.llm = llm or ChatGroq(
            model=Config.LLM_MODEL,
            temperature=Config.TEMPERATURE,
            api_key=Config.GROQ_API_KEY
        )

        self.retriever = retriever or HybridRetriever(
            chroma_path=Config.CHROMA_PATH,
            collection_name=Config.COLLECTION_NAME,
            normalized_data_path=Config.NORMALIZED_DATA_PATH,
            registry_path=Config.REGISTRY_PATH,
            embedding_model_name=Config.EMBEDDING_MODEL,
            fusion="rrf",
        )
        self.followup_suggester = FollowupSuggester(
            max_suggestions=3,
            llm=self.llm
        )
        self.answer_generator = AnswerGenerator(llm=self.llm)
        self.dialogue_manager = DialogueManager()

        self.graph = self._build_graph()
        self.validator = ResponseValidator(llm=self.llm)

    # ------------------------------------------------------------------
    # ساخت گراف
    # ------------------------------------------------------------------
    def _build_graph(self):
        workflow = StateGraph(RAGState)

        workflow.add_node("rewrite_query", self.rewrite_query_node)
        workflow.add_node("analyze_query", self.analyze_query_node)
        workflow.add_node("process_multi_query", self.process_multi_query_node)

        workflow.add_node("direct_response", self.direct_response_node)   # greeting
        workflow.add_node("calculator", self.calculator_node)
        workflow.add_node("calendar", self.calendar_node)
        workflow.add_node("clarify", self.clarify_node)                   # ambiguous
        workflow.add_node("summarize", self.summarize_node)
        workflow.add_node("compare", self.compare_node)

        workflow.add_node("retrieve", self.retrieve_node)
        workflow.add_node("generate_context", self.generate_context_node)
        workflow.add_node("generate_answer", self.generate_answer_node)
        workflow.add_node("response_validator", self.response_validator_node)

        workflow.set_entry_point("rewrite_query")
        workflow.add_edge("rewrite_query", "analyze_query")

        # analyze_query هم‌زمان split کردن سؤالات و تشخیص intent هر بخش رو با
        # یک کال LLM انجام می‌ده (به‌جز مواردی که با fast-path بدون LLM
        # تشخیص داده می‌شن، مثل ماشین‌حساب و تاریخ ساده).
        workflow.add_conditional_edges(
            "analyze_query",
            self.route_after_analysis,
            {
                "multi": "process_multi_query",
                self.INTENT_GREETING: "direct_response",
                self.INTENT_CALCULATOR: "calculator",
                self.INTENT_CALENDAR: "calendar",
                self.INTENT_AMBIGUOUS: "clarify",
                self.INTENT_SUMMARIZE: "summarize",
                self.INTENT_COMPARE: "compare",
                self.INTENT_RAG: "retrieve",
            }
        )

        workflow.add_edge("process_multi_query", END)

        # مسیرهای تک‌پاسی (بدون validation/retry) - برای صرفه‌جویی در توکن
        workflow.add_edge("direct_response", END)
        workflow.add_edge("calculator", END)
        workflow.add_edge("calendar", END)
        workflow.add_edge("clarify", END)
        workflow.add_edge("summarize", END)
        workflow.add_edge("compare", END)

        # مسیر کامل RAG با حلقه‌ی retry
        workflow.add_edge("retrieve", "generate_context")
        workflow.add_edge("generate_context", "generate_answer")
        workflow.add_edge("generate_answer", "response_validator")

        workflow.add_conditional_edges(
            "response_validator",
            self.should_continue,
            {
                "end": END,
                "retry_retrieve": "retrieve",
                "retry_generate": "generate_answer",
            }
        )
        return workflow.compile()

    # ------------------------------------------------------------------
    # rewrite
    # ------------------------------------------------------------------
    def rewrite_query_node(self, state: RAGState) -> Dict:
        result = self.dialogue_manager.rewrite_query(
            session_id=state["session_id"],
            query=state["query"],
        )
        return {
            "standalone_query": result["standalone_query"],
            "was_rewritten": result["was_rewritten"],
        }

    # ------------------------------------------------------------------
    # fast-path‌های بدون LLM (برای کاهش مصرف توکن)
    # ------------------------------------------------------------------
    def _try_fast_calculator(self, text: str) -> Optional[str]:
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

    def _try_fast_calendar(self, text: str) -> Optional[str]:
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

    def _try_fast_greeting(self, text: str) -> bool:
        cleaned = text.strip().strip("!.،؟?").lower()
        return cleaned in self._GREETING_EXACT

    # ------------------------------------------------------------------
    # تحلیل ترکیبی: split کردن سؤالات + تشخیص intent
    # ------------------------------------------------------------------
    def analyze_query_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"] or state["query"]

        # --- fast-path‌ها: اگه کل پیام یک عبارت خیلی ساده باشه، اصلاً کال
        #     LLM برای split/intent نمی‌زنیم (نه split لازمه نه classification) ---
        if self._try_fast_greeting(query):
            part: QueryPart = {"query": query, "intent": self.INTENT_GREETING}
            return {
                "parts": [part], "is_multi_query": False, "sub_queries": [query],
                "standalone_query": query, "intent": self.INTENT_GREETING,
            }
        calc_fast = self._try_fast_calculator(query)
        if calc_fast is not None:
            part = {"query": query, "intent": self.INTENT_CALCULATOR}
            return {
                "parts": [part], "is_multi_query": False, "sub_queries": [query],
                "standalone_query": query, "intent": self.INTENT_CALCULATOR,
            }
        cal_fast = self._try_fast_calendar(query)
        if cal_fast is not None:
            part = {"query": query, "intent": self.INTENT_CALENDAR}
            return {
                "parts": [part], "is_multi_query": False, "sub_queries": [query],
                "standalone_query": query, "intent": self.INTENT_CALENDAR,
            }

        prompt = f"""پیام کاربر رو تحلیل کن. دو کار باید انجام بدی:

۱) تشخیص بده پیام باید به چند بخش مستقل شکسته بشه یا نه:
   - اگه یک سؤال/درخواست واحده -> همون یک بخش.
   - اگه چند سؤال مستقل داره (هرکدوم بدون نیاز به جواب بقیه قابل پاسخه) ->
     به همون تعداد بخش بشکن و ضمایر مبهم رو با موضوع واقعی جایگزین کن.
   - اگه بخش‌ها زنجیره‌ای/وابسته به‌هم هستن -> نشکن، یک بخش در نظر بگیر.
     در صورت شک، نشکن.
   - حداکثر {self.MAX_SUB_QUESTIONS} بخش.

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
            return {
                "parts": [fallback_part], "is_multi_query": False,
                "sub_queries": [query], "standalone_query": query,
                "intent": self.INTENT_RAG,
            }

        parts = self._parse_analysis_output(text, fallback_query=query)
        parts = parts[: self.MAX_SUB_QUESTIONS]
        is_multi = len(parts) > 1

        updates: Dict[str, Any] = {
            "parts": parts,
            "is_multi_query": is_multi,
            "sub_queries": [p["query"] for p in parts],
        }

        if not is_multi:
            updates["standalone_query"] = parts[0]["query"]
            updates["intent"] = parts[0]["intent"]

        return updates

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

    def route_after_analysis(self, state: RAGState) -> str:
        if state.get("is_multi_query"):
            return "multi"
        intent = state.get("intent", self.INTENT_RAG)
        if intent not in self.VALID_INTENTS:
            intent = self.INTENT_RAG
        return intent

    # ------------------------------------------------------------------
    # پردازش چند سؤال (وقتی is_multi_query=True)
    # ------------------------------------------------------------------
    def process_multi_query_node(self, state: RAGState) -> Dict:
        session_id = state["session_id"]
        top_k = state.get("top_k", Config.TOP_K)
        max_retries = state.get("max_retries", Config.MAX_RETRIES)

        results = [
            self._run_single_question(
                sub_query=part["query"],
                intent=part["intent"],
                session_id=session_id,
                top_k=top_k,
                max_retries=max_retries,
            )
            for part in state["parts"]
        ]

        answer_parts = [
            f"**{i}. {r['query']}**\n{r['response']}"
            for i, r in enumerate(results, 1)
        ]
        combined_response = "\n\n".join(answer_parts)

        all_docs: List[Dict] = []
        for r in results:
            all_docs.extend(r["retrieved_docs"])

        all_satisfied = all(r["is_satisfied"] for r in results)

        warnings = [
            r["validation_result"].get("warning")
            for r in results
            if r.get("validation_result", {}).get("warning")
        ]
        combined_validation: Dict[str, Any] = {}
        if warnings:
            combined_validation["warning"] = " | ".join(warnings)

        return {
            "response": combined_response,
            "retrieved_docs": all_docs,
            "is_satisfied": all_satisfied,
            "validation_result": combined_validation,
        }

    def _run_single_question(
        self,
        sub_query: str,
        intent: str,
        session_id: str,
        top_k: int,
        max_retries: int,
    ) -> Dict[str, Any]:
        """اجرای منطق تک‌سؤالی (هر کدوم از ۷ مسیر) برای یک زیرسؤال که
        intent‌ش از قبل توسط analyze_query_node مشخص شده."""
        mini_state: Dict[str, Any] = {
            "query": sub_query,
            "standalone_query": sub_query,
            "session_id": session_id,
            "intent": intent if intent in self.VALID_INTENTS else self.INTENT_RAG,
            "retrieved_docs": [],
            "context": "",
            "response": "",
            "validation_result": {},
            "retry_count": 0,
            "is_satisfied": False,
            "top_k": top_k,
            "max_retries": max_retries,
        }

        node_by_intent = {
            self.INTENT_GREETING: self.direct_response_node,
            self.INTENT_CALCULATOR: self.calculator_node,
            self.INTENT_CALENDAR: self.calendar_node,
            self.INTENT_AMBIGUOUS: self.clarify_node,
            self.INTENT_SUMMARIZE: self.summarize_node,
            self.INTENT_COMPARE: self.compare_node,
        }

        if mini_state["intent"] in node_by_intent:
            mini_state.update(node_by_intent[mini_state["intent"]](mini_state))
            return {
                "query": sub_query,
                "response": mini_state["response"],
                "retrieved_docs": mini_state.get("retrieved_docs", []),
                "is_satisfied": True,
                "validation_result": {},
            }

        # مسیر rag - همون حلقه‌ی retry گراف اصلی رو دستی پیاده می‌کنیم
        need_retrieve = True
        while True:
            if need_retrieve:
                mini_state.update(self.retrieve_node(mini_state))
                mini_state.update(self.generate_context_node(mini_state))

            mini_state.update(self.generate_answer_node(mini_state))
            mini_state.update(self.response_validator_node(mini_state))

            decision = self.should_continue(mini_state)
            if decision == "end":
                break
            need_retrieve = decision == "retry_retrieve"

        return {
            "query": sub_query,
            "response": mini_state["response"],
            "retrieved_docs": mini_state["retrieved_docs"],
            "is_satisfied": mini_state["is_satisfied"],
            "validation_result": mini_state["validation_result"],
        }

    # ------------------------------------------------------------------
    # greeting
    # ------------------------------------------------------------------
    def direct_response_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"] or state["query"]
        prompt = f"""به پیام زیر به صورت دوستانه، کوتاه و طبیعی جواب بده
(مثل یک دستیار مفید که در حال گفت‌وگوی معمولی با کاربره).
از اطلاعات غیرواقعی یا اسناد داخلی استفاده نکن، فقط یک پاسخ محاوره‌ای بده.

پیام کاربر: "{query}"

پاسخ:"""
        raw = self.llm.invoke(prompt)
        response_text = raw.content if hasattr(raw, "content") else str(raw)
        return {
            "response": response_text.strip(),
            "retrieved_docs": [],
            "context": "",
            "is_satisfied": True,
        }

    # ------------------------------------------------------------------
    # calculator
    # ------------------------------------------------------------------
    def calculator_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"] or state["query"]

        fast_result = self._try_fast_calculator(query)
        if fast_result is not None:
            response_text = fast_result
        else:
            # مسئله‌ی عددیِ بیان‌شده با کلمات (نه یک عبارت خالص) - نیاز به یک
            # کال کوتاه LLM داره
            prompt = f"""مسئله‌ی ریاضی زیر رو حل کن. فقط نتیجه رو با یک محاسبه‌ی
خیلی کوتاه و خوانا برگردون، بدون توضیح اضافه.

مسئله: "{query}"

پاسخ:"""
            raw = self.llm.invoke(prompt)
            response_text = (raw.content if hasattr(raw, "content") else str(raw)).strip()

        return {
            "response": response_text,
            "retrieved_docs": [],
            "context": "",
            "is_satisfied": True,
        }

    # ------------------------------------------------------------------
    # calendar
    # ------------------------------------------------------------------
    def calendar_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"] or state["query"]

        fast_result = self._try_fast_calendar(query)
        if fast_result is not None:
            response_text = fast_result
        else:
            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            prompt = f"""تاریخ امروز {today_str} است. با توجه به این تاریخ،
به سؤال زیر پاسخ کوتاه و دقیق بده.

سؤال: "{query}"

پاسخ:"""
            raw = self.llm.invoke(prompt)
            response_text = (raw.content if hasattr(raw, "content") else str(raw)).strip()

        return {
            "response": response_text,
            "retrieved_docs": [],
            "context": "",
            "is_satisfied": True,
        }

    # ------------------------------------------------------------------
    # ambiguous -> سؤال تکمیلی
    # ------------------------------------------------------------------
    def clarify_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"] or state["query"]
        prompt = f"""پیام کاربر مبهم یا ناقصه و برای پاسخ دقیق باید اطلاعات
بیشتری بگیریم. فقط یک سؤال کوتاه (حداکثر یک خط) بپرس تا منظور کاربر
دقیق بشه. هیچ توضیح یا پاسخ دیگه‌ای نده.

پیام کاربر: "{query}"

سؤال تکمیلی:"""
        raw = self.llm.invoke(prompt)
        response_text = raw.content if hasattr(raw, "content") else str(raw)
        return {
            "response": response_text.strip(),
            "retrieved_docs": [],
            "context": "",
            "is_satisfied": True,
        }

    # ------------------------------------------------------------------
    # summarize
    # ------------------------------------------------------------------
    def _extract_inline_text(self, query: str) -> Optional[str]:
        """اگه خودِ متن قابل‌خلاصه‌سازی داخل پیام باشه (نه فقط اسم یه موضوع)،
        اون رو برمی‌گردونه؛ در غیر این‌صورت None (یعنی باید بریم سراغ retrieval)."""
        cleaned = re.sub(
            r'^(لطفا\s*)?(این\s*(متن|مطلب)\s*(رو|را)?\s*)?خلاصه\s*(کن|نویسی کن|بکن)[:\s]*',
            "", query.strip(), flags=re.IGNORECASE,
        ).strip()
        if len(cleaned) >= self.INLINE_SUMMARY_MIN_CHARS:
            return cleaned
        return None

    def summarize_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"] or state["query"]
        top_k = state.get("top_k", Config.TOP_K)

        inline_text = self._extract_inline_text(query)

        if inline_text:
            prompt = f"""متن زیر رو خلاصه کن. خلاصه باید کوتاه، دقیق و شامل
نکات اصلی باشه، بدون اضافه کردن اطلاعاتی که تو متن نیست.

متن:
{inline_text}

خلاصه:"""
            raw = self.llm.invoke(prompt)
            response_text = (raw.content if hasattr(raw, "content") else str(raw)).strip()
            return {
                "response": response_text,
                "retrieved_docs": [],
                "context": "",
                "is_satisfied": True,
            }

        # متن مستقیم تو پیام نبود -> از اسناد داخلی درباره‌ی موضوع خلاصه بساز
        docs = self.retriever.retrieve(query=query, k=top_k)
        context = "\n\n---\n\n".join(
            f"[Document {i}]:\n{doc['content']}" for i, doc in enumerate(docs, 1)
        )
        prompt = f"""با توجه به اسناد زیر، یک خلاصه‌ی کوتاه و دقیق درباره‌ی
موضوع زیر بنویس. فقط بر اساس اطلاعات موجود تو اسناد بنویس؛ اگه اطلاعات
کافی نبود صراحتاً بگو.

موضوع: "{query}"

اسناد:
{context}

خلاصه:"""
        raw = self.llm.invoke(prompt)
        response_text = (raw.content if hasattr(raw, "content") else str(raw)).strip()

        return {
            "response": response_text,
            "retrieved_docs": docs,
            "context": context,
            "is_satisfied": True,
        }

    # ------------------------------------------------------------------
    # compare
    # ------------------------------------------------------------------
    def compare_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"] or state["query"]
        top_k = state.get("top_k", Config.TOP_K)

        docs = self.retriever.retrieve(query=query, k=top_k)
        context = "\n\n---\n\n".join(
            f"[Document {i}]:\n{doc['content']}" for i, doc in enumerate(docs, 1)
        )
        prompt = f"""با توجه به اسناد زیر، درخواست مقایسه‌ی کاربر رو پاسخ بده.
پاسخ رو به‌صورت نکته‌به‌نکته یا جدول کوتاه بنویس تا تفاوت‌ها و شباهت‌ها
واضح باشه. فقط بر اساس اطلاعات موجود تو اسناد بنویس؛ اگه اطلاعات کافی
نبود صراحتاً بگو.

درخواست: "{query}"

اسناد:
{context}

مقایسه:"""
        raw = self.llm.invoke(prompt)
        response_text = (raw.content if hasattr(raw, "content") else str(raw)).strip()

        return {
            "response": response_text,
            "retrieved_docs": docs,
            "context": context,
            "is_satisfied": True,
        }

    # ------------------------------------------------------------------
    # مسیر کامل rag (retrieve -> generate -> validate با retry)
    # ------------------------------------------------------------------
    def retrieve_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"]
        k = state.get("top_k", Config.TOP_K)
        retrieved_docs = self.retriever.retrieve(query=query, k=k)
        return {"retrieved_docs": retrieved_docs}

    def generate_context_node(self, state: RAGState) -> Dict:
        context_parts = [
            f"[Document {i}]:\n{doc['content']}"
            for i, doc in enumerate(state["retrieved_docs"], 1)
        ]
        return {"context": "\n\n---\n\n".join(context_parts)}

    def generate_answer_node(self, state: RAGState) -> Dict:
        response = self.answer_generator.generate(
            query=state["standalone_query"],
            context=state["context"],
            previous_feedback=state.get("validation_result"),
        )
        return {"response": response}

    def response_validator_node(self, state: RAGState) -> Dict:
        result = self.validator.validate(
            question=state["standalone_query"],
            context=state["context"],
            response=state["response"],
            retrieved_docs=state["retrieved_docs"]
        )

        is_satisfied = result["is_valid"]
        retries = state.get("retry_count", 0)
        max_r = state.get("max_retries", Config.MAX_RETRIES)
        new_retry_count = retries if is_satisfied else retries + 1

        updates: Dict[str, Any] = {
            "validation_result": result,
            "is_satisfied": is_satisfied,
            "retry_count": new_retry_count,
        }

        will_retry = (not is_satisfied) and (new_retry_count < max_r)
        if will_retry and result.get("retry_reason") == "completeness":
            current_top_k = state.get("top_k", Config.TOP_K)
            updates["top_k"] = current_top_k + Config.TOP_K_INCREMENT

        if (not is_satisfied) and (new_retry_count >= max_r):
            result["warning"] = (
                f"این پاسخ ممکن است کامل یا دقیق نباشد "
                f"(نمره کلی: {result.get('overall_score')})."
            )

        return updates

    def should_continue(self, state: RAGState) -> str:
        max_r = state.get("max_retries", Config.MAX_RETRIES)
        is_satisfied = state.get("is_satisfied", False)
        retry_count = state.get("retry_count", 0)

        if is_satisfied or retry_count >= max_r:
            return "end"

        retry_reason = (state.get("validation_result") or {}).get("retry_reason")
        if retry_reason == "completeness":
            return "retry_retrieve"
        return "retry_generate"

    # ------------------------------------------------------------------
    # ورودی اصلی
    # ------------------------------------------------------------------
#     def run(
#         self,
#         query: str,
#         session_id: Optional[str] = None,
#         top_k: Optional[int] = None,
#         max_retries: Optional[int] = None,
#     ) -> Dict[str, Any]:
#         session_id = session_id or str(uuid.uuid4())
#         top_k = top_k if top_k is not None else Config.TOP_K
#         max_retries = max_retries if max_retries is not None else Config.MAX_RETRIES

#         start_time = time.time()

#         initial_state: RAGState = {
#             "query": query,
#             "standalone_query": "",
#             "was_rewritten": False,
#             "session_id": session_id,
#             "parts": [],
#             "is_multi_query": False,
#             "sub_queries": [],
#             "intent": "",
#             "retrieved_docs": [],
#             "context": "",
#             "response": "",
#             "validation_result": {},
#             "retry_count": 0,
#             "is_satisfied": False,
#             "top_k": top_k,
#             "max_retries": max_retries
#         }

#         final_state = self.graph.invoke(initial_state)
#         processing_time = time.time() - start_time

#         self.dialogue_manager.add_turn(session_id, "user", query)
#         self.dialogue_manager.add_turn(session_id, "assistant", final_state["response"])

#         attempt_count = final_state["retry_count"] + 1

#         # تولید سوالات تکمیلی پیشنهادی
# # -----------------------------------------

#         try:
#             suggested_questions = self.followup_suggester.suggest(
#                 query=final_state.get("standalone_query", query),
#                 answer=final_state["response"],
#                 context=final_state.get("context", "")
#             )
#         except Exception as e:
#             print(f"⚠️ خطا در تولید سوالات پیشنهادی: {e}")
#             suggested_questions = []

#         return {
#             "answer": final_state["response"],
#             "intent": final_state.get("intent"),
#             "suggested_questions": suggested_questions,
#             "is_multi_query": final_state.get("is_multi_query", False),
#             "sub_queries": final_state.get("sub_queries", []),
#             "retrieved_docs": final_state["retrieved_docs"],
#             "retry_count": final_state["retry_count"],
#             "attempt_count": attempt_count,
#             "is_satisfied": final_state["is_satisfied"],
#             "validation_result": final_state["validation_result"],
#             "warning": (final_state.get("validation_result") or {}).get("warning"),
#             "processing_time": processing_time,
#             "session_id": session_id,
#             "standalone_query": final_state["standalone_query"],
#             "was_rewritten": final_state["was_rewritten"],
#         }





    def run(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: Optional[int] = None,
        max_retries: Optional[int] = None,
        on_step: Optional[Callable[[str], None]] = None,
        # ^ هوک اختیاری: بعد از اجرای هر نود گراف صدا زده می‌شه (اسم نود بهش پاس
        #   داده می‌شه). کاملاً اختیاریه و پیش‌فرضش None - یعنی اگه کسی دیگه
        #   (مثلاً تست یا اسکریپت دیگه‌ای) rag.run() رو بدون این آرگومان صدا بزنه،
        #   دقیقاً مثل قبل کار می‌کنه و هیچ رفتاری تغییر نمی‌کنه.
    ) -> Dict[str, Any]:
        session_id = session_id or str(uuid.uuid4())
        top_k = top_k if top_k is not None else Config.TOP_K
        max_retries = max_retries if max_retries is not None else Config.MAX_RETRIES

        start_time = time.time()

        initial_state: RAGState = {
            "query": query,
            "standalone_query": "",
            "was_rewritten": False,
            "session_id": session_id,
            "parts": [],
            "is_multi_query": False,
            "sub_queries": [],
            "intent": "",
            "retrieved_docs": [],
            "context": "",
            "response": "",
            "validation_result": {},
            "retry_count": 0,
            "is_satisfied": False,
            "top_k": top_k,
            "max_retries": max_retries
        }

        # --------------------------------------------------------------
        # اجرا با .stream() به‌جای .invoke() - تنها تفاوت اینه که بعد از
        # هر نود، یک event دریافت می‌کنیم و on_step رو صدا می‌زنیم؛ منطق
        # داخل خودِ نودها دست‌نخورده می‌مونه چون فقط شکل فراخوانی گراف عوض
        # شده، نه خودِ نودها.
        # --------------------------------------------------------------
        final_state: Dict[str, Any] = dict(initial_state)
        for step_update in self.graph.stream(initial_state, stream_mode="updates"):
            for node_name, node_output in step_update.items():
                if node_output:
                    final_state.update(node_output)
                if on_step:
                    try:
                        on_step(node_name)
                    except Exception:
                        # هیچ خطایی تو گزارش وضعیت نباید اجرای گراف رو متوقف کنه
                        pass

        processing_time = time.time() - start_time

        self.dialogue_manager.add_turn(session_id, "user", query)
        self.dialogue_manager.add_turn(session_id, "assistant", final_state["response"])

        attempt_count = final_state["retry_count"] + 1

        # تولید سوالات تکمیلی پیشنهادی
        # -----------------------------------------

        try:
            suggested_questions = self.followup_suggester.suggest(
                query=final_state.get("standalone_query", query),
                answer=final_state["response"],
                context=final_state.get("context", "")
            )
        except Exception as e:
            print(f"⚠️ خطا در تولید سوالات پیشنهادی: {e}")
            suggested_questions = []

        return {
            "answer": final_state["response"],
            "intent": final_state.get("intent"),
            "suggested_questions": suggested_questions,
            "is_multi_query": final_state.get("is_multi_query", False),
            "sub_queries": final_state.get("sub_queries", []),
            "retrieved_docs": final_state["retrieved_docs"],
            "retry_count": final_state["retry_count"],
            "attempt_count": attempt_count,
            "is_satisfied": final_state["is_satisfied"],
            "validation_result": final_state["validation_result"],
            "warning": (final_state.get("validation_result") or {}).get("warning"),
            "processing_time": processing_time,
            "session_id": session_id,
            "standalone_query": final_state["standalone_query"],
            "was_rewritten": final_state["was_rewritten"],
        }