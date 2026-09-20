import time
import uuid
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from back.config import Config
from back.ResponseValidator import ResponseValidator
from back.rag.hybrid_retriever_langchain import HybridRetriever  # <-- retrieval هیبرید (dense + BM25)
from back.rag.answer_generator import AnswerGenerator
from back.intent.dialogue_manager import DialogueManager  # <-- تاریخچه + query rewriting
from back.intent.followup_suggester import FollowupSuggester
from back.intent.query_analyzer import QueryAnalyzer, QueryPart  # <-- تشخیص intent + fast-pathها

from typing import TypedDict, List, Dict, Any, Optional, Callable


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
    user_access_level: Optional[int]


class RAGGraph:
    # ------------------------------------------------------------------
    # دسته‌بندی‌های intent - از QueryAnalyzer می‌گیریم تا هر جای دیگه‌ی
    # پروژه (مثلاً لایه‌ی API) که به RAGGraph.INTENT_* رفرنس داده، بشکنه
    # ------------------------------------------------------------------
    INTENT_GREETING = QueryAnalyzer.INTENT_GREETING
    INTENT_RAG = QueryAnalyzer.INTENT_RAG
    INTENT_SUMMARIZE = QueryAnalyzer.INTENT_SUMMARIZE
    INTENT_COMPARE = QueryAnalyzer.INTENT_COMPARE
    INTENT_CALENDAR = QueryAnalyzer.INTENT_CALENDAR
    INTENT_CALCULATOR = QueryAnalyzer.INTENT_CALCULATOR
    INTENT_AMBIGUOUS = QueryAnalyzer.INTENT_AMBIGUOUS
    VALID_INTENTS = QueryAnalyzer.VALID_INTENTS

    # این‌ها تنها intent‌هایی هستن که وارد حلقه‌ی کامل retrieve/generate/validate
    # (با retry) می‌شن. بقیه برای صرفه‌جویی در توکن فقط یک پاس اجرا می‌شن.
    RETRIEVAL_LOOP_INTENTS = {INTENT_RAG}

    # حداکثر تعداد بخشی که تو یک پیام قبول می‌کنیم بشکنیم
    MAX_SUB_QUESTIONS = getattr(Config, "MAX_SUB_QUESTIONS", 5)

    NO_ACCESSIBLE_DOCS_MESSAGE = (
        "اطلاعات کافی برای پاسخ به این سوال در اسناد قابل‌دسترسی شما یافت نشد. "
        "در صورت نیاز، درخواست ارتقای سطح دسترسی را با مدیر خود مطرح کنید."
    )

    # آستانه‌ی طول متن برای تشخیص «متن مستقیماً داخل پیام» در summarize
    INLINE_SUMMARY_MIN_CHARS = getattr(Config, "INLINE_SUMMARY_MIN_CHARS", 250)

    # آستانه‌ی fused_score (مقیاس RRF): زیر این حد یعنی سوال احتمالاً بی‌ربطه
    # یا چانک‌های برگشتی کیفیت کافی ندارن -> نمی‌ریم سراغ generate.
    # کالیبره‌شده با eval_similarity_threshold.py (بی‌ربط ~0.011-0.014 در
    # مقابل مرتبط ~0.0163)؛ عدد پیش‌فرض یکم محافظه‌کارانه انتخاب شده.
    SIMILARITY_THRESHOLD = getattr(Config, "SIMILARITY_THRESHOLD", 0.0145)

    # intent‌هایی که سوال پیشنهادی براشون بی‌معنیه (پاسخ اصلی، پاسخی مبتنی بر
    # اسناد نبوده) - برای این‌ها followup_suggester اصلاً صدا زده نمی‌شه.
    NON_SUGGESTIBLE_INTENTS = {
        QueryAnalyzer.INTENT_GREETING,
        QueryAnalyzer.INTENT_CALCULATOR,
        QueryAnalyzer.INTENT_CALENDAR,
        QueryAnalyzer.INTENT_AMBIGUOUS,
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
            api_key=Config.main_Model_Api_key
        )

        self.retriever = retriever or HybridRetriever(
            chroma_path=Config.CHROMA_PATH,
            collection_name=Config.COLLECTION_NAME,
            normalized_data_path=Config.NORMALIZED_DATA_PATH,
            registry_path=Config.REGISTRY_PATH,
            embedding_model_name=Config.EMBEDDING_MODEL,
        )
        self.followup_suggester = FollowupSuggester(
            max_suggestions=3,
            llm=self.llm
        )
        self.answer_generator = AnswerGenerator(llm=self.llm)
        self.dialogue_manager = DialogueManager()
        self.query_analyzer = QueryAnalyzer(llm=self.llm, max_sub_questions=self.MAX_SUB_QUESTIONS)

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

        workflow.add_node("fast_intent_check", self.fast_intent_check_node)
        workflow.set_entry_point("fast_intent_check")
        workflow.add_conditional_edges(
            "fast_intent_check",
            self.route_after_fast_check,
            {
                "no_fast_path": "rewrite_query",
                self.INTENT_GREETING: "direct_response",
                self.INTENT_CALCULATOR: "calculator",
                self.INTENT_CALENDAR: "calendar",
            }
        )
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
        workflow.add_node("no_docs_response", self.no_docs_response_node)
        workflow.add_conditional_edges(
            "retrieve",
            self.route_after_retrieve,
            {"no_docs": "no_docs_response", "continue": "generate_context"},
        )
        workflow.add_edge("no_docs_response", END)
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
    # fast-path سراسری: قبل از rewrite_query چک می‌شه تا برای پیام‌های
    # ساده (سلام دقیق/محاسبه‌ی خالص/الگوی رایج تاریخ)، اصلاً کال LLM
    # مربوط به query rewriting هم زده نشه - نه فقط split+intent.
    # ------------------------------------------------------------------
    def fast_intent_check_node(self, state: RAGState) -> Dict:
        query = state["query"]

        if self.query_analyzer.try_fast_greeting(query):
            intent = self.INTENT_GREETING
        elif self.query_analyzer.try_fast_calculator(query) is not None:
            intent = self.INTENT_CALCULATOR
        elif self.query_analyzer.try_fast_calendar(query) is not None:
            intent = self.INTENT_CALENDAR
        else:
            return {}  # هیچ fast-pathی match نشد -> برو سراغ rewrite_query عادی

        part: QueryPart = {"query": query, "intent": intent}
        return {
            "standalone_query": query,
            "was_rewritten": False,
            "intent": intent,
            "parts": [part],
            "is_multi_query": False,
            "sub_queries": [query],
        }

    def route_after_fast_check(self, state: RAGState) -> str:
        intent = state.get("intent")
        if intent in (self.INTENT_GREETING, self.INTENT_CALCULATOR, self.INTENT_CALENDAR):
            return intent
        return "no_fast_path"

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
    # کیفیت context (برای تصمیم رفتن سراغ generate یا نه)
    # ------------------------------------------------------------------
    def _is_context_usable(self, docs: Optional[List[Dict]]) -> bool:
        """آیا چانک‌های برگشتی برای generate کردن جواب کافی‌ان؟
        هم باید غیرخالی باشن، هم بالاترین fused_score نباید زیر threshold
        باشه - وگرنه یعنی سوال احتمالاً بی‌ربطه یا بهترین چانک پیداشده
        کیفیت کافی نداره، و بهتره یک جواب ثابت بدیم تا LLM رو مجبور به
        ساختن جواب از روی چانک‌های نامرتبط نکنیم."""
        if not docs:
            return False
        top_score = docs[0].get("fused_score", 0.0)
        return top_score >= self.SIMILARITY_THRESHOLD

    # ------------------------------------------------------------------
    # تحلیل ترکیبی: split کردن سؤالات + تشخیص intent (delegate به QueryAnalyzer)
    # ------------------------------------------------------------------
    def analyze_query_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"] or state["query"]
        return self.query_analyzer.analyze(query)

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
        """اجرای زیرسؤال‌های مستقل و ترکیب پاسخ‌ها."""

        session_id = state["session_id"]
        top_k = state.get("top_k", Config.TOP_K)
        max_retries = state.get("max_retries", Config.MAX_RETRIES)
        user_access_level = state.get("user_access_level")

        results = [
            self._run_single_question(
                sub_query=part["query"],
                intent=part["intent"],
                session_id=session_id,
                top_k=top_k,
                max_retries=max_retries,
                user_access_level=user_access_level,
            )
            for part in state["parts"]
        ]

        answer_parts = [
            f"**{i}. {result['query']}**\n{result['response']}"
            for i, result in enumerate(results, 1)
        ]

        combined_response = "\n\n".join(answer_parts)

        all_docs: List[Dict] = []
        for result in results:
            all_docs.extend(result.get("retrieved_docs", []))

        all_satisfied = all(
            result.get("is_satisfied", False)
            for result in results
        )

        warnings = [
            (result.get("validation_result") or {}).get("warning")
            for result in results
            if (result.get("validation_result") or {}).get("warning")
        ]

        combined_validation: Dict[str, Any] = {}
        if warnings:
            combined_validation["warning"] = " | ".join(warnings)

        return {
            "response": combined_response,
            "retrieved_docs": all_docs,
            "context": "",
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
        user_access_level: Optional[int] = None,
    ) -> Dict[str, Any]:
        """اجرای یک زیرسؤال در مسیر multi-query.

        مسیرهای غیر-RAG یک پاس اجرا می‌شوند.
        مسیر RAG نیز برای MVP یک پاس retrieve -> context -> answer دارد
        و وارد حلقه retry نمی‌شود؛ بنابراین هیچ while بی‌نهایتی وجود ندارد.
        """

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
            "user_access_level": user_access_level,
        }

        node_by_intent = {
            self.INTENT_GREETING: self.direct_response_node,
            self.INTENT_CALCULATOR: self.calculator_node,
            self.INTENT_CALENDAR: self.calendar_node,
            self.INTENT_AMBIGUOUS: self.clarify_node,
            self.INTENT_SUMMARIZE: self.summarize_node,
            self.INTENT_COMPARE: self.compare_node,
        }

        current_intent = mini_state["intent"]

        if current_intent in node_by_intent:
            mini_state.update(node_by_intent[current_intent](mini_state))
            return {
                "query": sub_query,
                "response": mini_state.get("response", ""),
                "retrieved_docs": mini_state.get("retrieved_docs", []),
                "is_satisfied": True,
                "validation_result": mini_state.get("validation_result", {}),
            }

        # مسیر RAG: یک پاس خطی و قطعی.
        mini_state.update(self.retrieve_node(mini_state))

        if not self._is_context_usable(mini_state.get("retrieved_docs")):
            mini_state.update({
                "response": self.NO_ACCESSIBLE_DOCS_MESSAGE,
                "retrieved_docs": [],
                "context": "",
                "is_satisfied": True,
                "validation_result": {},
            })
        else:
            mini_state.update(self.generate_context_node(mini_state))
            mini_state.update(self.generate_answer_node(mini_state))
            mini_state["is_satisfied"] = True
            mini_state["validation_result"] = {}

        return {
            "query": sub_query,
            "response": mini_state.get("response", ""),
            "retrieved_docs": mini_state.get("retrieved_docs", []),
            "is_satisfied": mini_state.get("is_satisfied", False),
            "validation_result": mini_state.get("validation_result", {}),
        }

    # ------------------------------------------------------------------
    # greeting
    # ------------------------------------------------------------------
    _FIXED_GREETING_REPLIES = [
        "سلام! چطور می‌تونم کمکتون کنم؟",
        "سلام! بفرمایید، در خدمتم.",
        "درود! چه سوالی دارید؟",
        "خواهش می‌کنم! اگه سوال دیگه‌ای بود در خدمتم.",
        "خدانگهدار! موفق باشید.",
    ]

    def direct_response_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"] or state["query"]

        # اگه دقیقاً match یکی از greeting/تشکر/خداحافظی‌های رایجه (fast-path)،
        # نیازی به LLM نیست - یه جواب ثابت کافیه.
        if self.query_analyzer.try_fast_greeting(query):
            import random
            response_text = random.choice(self._FIXED_GREETING_REPLIES)
            return {
                "response": response_text,
                "retrieved_docs": [],
                "context": "",
                "is_satisfied": True,
            }

        # غیر از اون (چیزی که LLM توی analyze_query تشخیص داده greeting-مانند
        # ولی دقیقاً match نبوده، مثلاً «سلام حالت چطوره رفیق»)، یه پاسخ
        # طبیعی‌تر با LLM می‌سازیم.
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

        fast_result = self.query_analyzer.try_fast_calculator(query)
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

        fast_result = self.query_analyzer.try_fast_calendar(query)
        if fast_result is not None:
            response_text = fast_result
        else:
            import datetime
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
        import re
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
        docs = self.retriever.retrieve(
            query=query,
            k=top_k,
            access_level=state.get("user_access_level"),
        )

        if not self._is_context_usable(docs):
            return {
                "response": self.NO_ACCESSIBLE_DOCS_MESSAGE,
                "retrieved_docs": [],
                "context": "",
                "is_satisfied": True,
                "validation_result": {},
            }

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

        docs = self.retriever.retrieve(
            query=query,
            k=top_k,
            access_level=state.get("user_access_level"),
        )

        if not self._is_context_usable(docs):
            return {
                "response": self.NO_ACCESSIBLE_DOCS_MESSAGE,
                "retrieved_docs": [],
                "context": "",
                "is_satisfied": True,
                "validation_result": {},
            }

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
        retrieved_docs = self.retriever.retrieve(
            query=query, k=k, access_level=state.get("user_access_level")
        )

        return {"retrieved_docs": retrieved_docs}

    def route_after_retrieve(self, state: RAGState) -> str:
        return "continue" if self._is_context_usable(state.get("retrieved_docs")) else "no_docs"

    def no_docs_response_node(self, state: RAGState) -> Dict:
        return {
            "response": self.NO_ACCESSIBLE_DOCS_MESSAGE,
            "retrieved_docs": [],
            "context": "",
            "is_satisfied": True,
            "validation_result": {},
        }

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

    def run(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: Optional[int] = None,
        max_retries: Optional[int] = None,
        user_access_level: Optional[int] = None,
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
            "max_retries": max_retries,
            "user_access_level": user_access_level,

        }

        # --------------------------------------------------------------
        # اجرا با .stream() به‌جای .invoke() - تنها تفاوت اینه که بعد از
        # هر نود، یک event دریافت می‌کنیم و on_step رو صدا می‌زنیم؛ منطق
        # داخل خودِ نودها دست‌نخورده می‌مونه چون فقط شکل فراخوانی گراف عوض
        # شده، نه خودِ نودها.
        # --------------------------------------------------------------
        final_state: Dict[str, Any] = dict(initial_state)

        for step_update in self.graph.stream(
            initial_state,
            stream_mode="updates",
        ):
            for node_name, node_output in step_update.items():
                if isinstance(node_output, dict):
                    final_state.update(node_output)

                if on_step:
                    try:
                        on_step(node_name)
                    except Exception:
                        # هیچ خطایی تو گزارش وضعیت نباید اجرای گراف رو متوقف کنه
                        pass

        processing_time = time.time() - start_time

        self.dialogue_manager.add_turn(session_id, "user", query)
        self.dialogue_manager.add_turn(
            session_id,
            "assistant",
            final_state.get("response", ""),
        )

        attempt_count = final_state.get("retry_count", 0) + 1

        # تولید سوالات تکمیلی پیشنهادی
        # -----------------------------------------
        # سه حالتی که سوال پیشنهادی معنی نداره و کال LLM جدا لازم نیست:
        #   ۱) intent از جنس greeting/calculator/calendar/ambiguous بوده
        #   ۲) پاسخ یکی از دو پیام «جواب نداریم» بوده (چه از generate_answer
        #      چه از مسیر no_docs/threshold - این دو پیام رشته‌ی متفاوتی دارن،
        #      برای همین هر دو رو جدا چک می‌کنیم، نه فقط یکی)
        response_text = final_state["response"].strip()
        no_answer_phrases = {
            Config.NOT_FOUND_PHRASE.strip(),
            self.NO_ACCESSIBLE_DOCS_MESSAGE.strip(),
        }
        skip_followups = (
            final_state.get("intent") in self.NON_SUGGESTIBLE_INTENTS
            or response_text in no_answer_phrases
        )

        if skip_followups:
            suggested_questions = []
        else:
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