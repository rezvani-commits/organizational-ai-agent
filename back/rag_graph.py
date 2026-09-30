import time
import uuid
import json
import re
import datetime
from typing import TypedDict, List, Dict, Any, Optional, Callable
import contextvars

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from back.config import Config
from back.ResponseValidator import ResponseValidator
from back.rag.hybrid_retriever_langchain import HybridRetriever
from back.rag.answer_generator import AnswerGenerator
from back.intent.dialogue_manager import DialogueManager
from back.intent.query_analyzer import QueryAnalyzer, QueryPart

_on_step_ctx: contextvars.ContextVar = contextvars.ContextVar("on_step_ctx", default=None)


class RAGState(TypedDict):
    query: str
    standalone_query: str
    was_rewritten: bool
    session_id: str
    parts: List[QueryPart]
    is_multi_query: bool
    sub_queries: List[str]
    intent: str
    retrieved_docs: List[Dict]
    context: str
    response: str
    suggested_questions: List[str]
    validation_result: Dict[str, Any]
    retry_count: int
    is_satisfied: bool
    top_k: int
    max_retries: int
    user_access_level: Optional[int]


class RAGGraph:

    INTENT_GREETING = QueryAnalyzer.INTENT_GREETING
    INTENT_RAG = QueryAnalyzer.INTENT_RAG
    INTENT_SUMMARIZE = QueryAnalyzer.INTENT_SUMMARIZE
    INTENT_COMPARE = QueryAnalyzer.INTENT_COMPARE
    INTENT_CALENDAR = QueryAnalyzer.INTENT_CALENDAR
    INTENT_CALCULATOR = QueryAnalyzer.INTENT_CALCULATOR
    INTENT_AMBIGUOUS = QueryAnalyzer.INTENT_AMBIGUOUS
    INTENT_UNCLEAR = QueryAnalyzer.INTENT_UNCLEAR
    VALID_INTENTS = QueryAnalyzer.VALID_INTENTS

    RETRIEVAL_LOOP_INTENTS = {INTENT_RAG}

    MAX_SUB_QUESTIONS = getattr(Config, "MAX_SUB_QUESTIONS", 5)

    UNCLEAR_MESSAGE = (
        "متأسفانه پیام شما قابل درک نبود. لطفاً سؤال خود را به‌صورت واضح و کامل مطرح کنید."
    )

    

    INLINE_SUMMARY_MIN_CHARS = getattr(Config, "INLINE_SUMMARY_MIN_CHARS", 250)

    NON_SUGGESTIBLE_INTENTS = {
        INTENT_GREETING,
        INTENT_CALCULATOR,
        INTENT_CALENDAR,
        INTENT_AMBIGUOUS,
        INTENT_UNCLEAR,
    }

    _FIXED_GREETING_REPLY = (
        "با سلام. من دستیار پاسخ‌گویی به اسناد سازمانی هستم. لطفاً سؤال خود را مطرح کنید."
    )

    def __init__(self, llm=None, retriever: Optional[HybridRetriever] = None):

        self.llm = llm or ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=Config.TEMPERATURE,
            api_key=Config.main_Model_Api_key,
            base_url=Config.AVALAI_BASE_URL,
            max_tokens=Config.MAX_TOKENS,
            top_p=Config.TOP_P,
        )

        self.validator_llm = ChatOpenAI(
            model=Config.VALIDATOR_LLM_MODEL,
            temperature=0,
            api_key=Config.response_validator_api_key,
            base_url=Config.AVALAI_BASE_URL,
            max_tokens=Config.MAX_TOKENS,
        )

        self.router_llm = ChatOpenAI(
            model=Config.ROUTER_LLM_MODEL,
            temperature=Config.ROUTER_TEMPERATURE,
            api_key=Config.main_Model_Api_key,
            base_url=Config.AVALAI_BASE_URL,
            max_tokens=Config.MAX_TOKENS,
        )

        self.retriever = retriever or HybridRetriever(
            chroma_path=Config.CHROMA_PATH,
            collection_name=Config.COLLECTION_NAME,
            normalized_data_path=Config.NORMALIZED_DATA_PATH,
            registry_path=Config.REGISTRY_PATH,
            embedding_model_name=Config.EMBEDDING_MODEL,
        )

        self.dialogue_manager = DialogueManager()

        self.answer_generator = AnswerGenerator(llm=self.llm)

        self.query_analyzer = QueryAnalyzer(
            llm=self.router_llm,
            max_sub_questions=self.MAX_SUB_QUESTIONS,
        )

        self.validator = ResponseValidator(llm=self.validator_llm)

        self.graph = self._build_graph()

    def _wrap_with_status(self, node_name: str, node_fn: Callable):
        def wrapped(state):
            on_step = _on_step_ctx.get()
            if on_step:
                try:
                    on_step(node_name)
                except Exception:
                    pass
            return node_fn(state)
        return wrapped

    def _build_graph(self):
        workflow = StateGraph(RAGState)

        workflow.add_node("fast_intent_check", self._wrap_with_status("fast_intent_check", self.fast_intent_check_node))
        workflow.add_node("rewrite_query", self._wrap_with_status("rewrite_query", self.rewrite_query_node))
        workflow.add_node("analyze_query", self._wrap_with_status("analyze_query", self.analyze_query_node))
        workflow.add_node("unclear_response", self._wrap_with_status("unclear_response", self.unclear_response_node))
        workflow.add_node("process_multi_query", self._wrap_with_status("process_multi_query", self.process_multi_query_node))
        workflow.add_node("direct_response", self._wrap_with_status("direct_response", self.direct_response_node))
        workflow.add_node("calculator", self._wrap_with_status("calculator", self.calculator_node))
        workflow.add_node("calendar", self._wrap_with_status("calendar", self.calendar_node))
        workflow.add_node("clarify", self._wrap_with_status("clarify", self.clarify_node))
        workflow.add_node("summarize", self._wrap_with_status("summarize", self.summarize_node))
        workflow.add_node("compare", self._wrap_with_status("compare", self.compare_node))
        workflow.add_node("retrieve", self._wrap_with_status("retrieve", self.retrieve_node))
        workflow.add_node("generate_context", self._wrap_with_status("generate_context", self.generate_context_node))
        workflow.add_node("generate_answer", self._wrap_with_status("generate_answer", self.generate_answer_node))
        workflow.add_node("response_validator", self._wrap_with_status("response_validator", self.response_validator_node))
        workflow.add_node("no_docs_response", self._wrap_with_status("no_docs_response", self.no_docs_response_node))

        workflow.set_entry_point("fast_intent_check")

        workflow.add_conditional_edges(
            "fast_intent_check",
            self.route_after_fast_check,
            {
                "no_fast_path": "rewrite_query",
                self.INTENT_GREETING: "direct_response",
                self.INTENT_CALCULATOR: "calculator",
                self.INTENT_CALENDAR: "calendar",
            },
        )

        workflow.add_conditional_edges(
            "rewrite_query",
            self.route_after_rewrite,
            {
                "unclear": "unclear_response",
                "continue": "analyze_query",
            },
        )

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
            },
        )

        workflow.add_edge("process_multi_query", END)
        workflow.add_edge("unclear_response", END)
        workflow.add_edge("direct_response", END)
        workflow.add_edge("calculator", END)
        workflow.add_edge("calendar", END)
        workflow.add_edge("clarify", END)
        workflow.add_edge("summarize", END)
        workflow.add_edge("compare", END)

        workflow.add_conditional_edges(
            "retrieve",
            self.route_after_retrieve,
            {
                "no_docs": "no_docs_response",
                "continue": "generate_context",
            },
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
            },
        )

        return workflow.compile()

    def fast_intent_check_node(self, state: RAGState) -> Dict:
        query = state["query"]

        if self.query_analyzer.try_fast_greeting(query):
            intent = self.INTENT_GREETING
        elif self.query_analyzer.try_fast_calculator(query) is not None:
            intent = self.INTENT_CALCULATOR
        elif self.query_analyzer.try_fast_calendar(query) is not None:
            intent = self.INTENT_CALENDAR
        else:
            return {}

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

    def _is_context_usable(self, docs: Optional[List[Dict]]) -> bool:
        return bool(docs)

    def rewrite_query_node(self, state: RAGState) -> Dict:
        query = state["query"]
        history = self.dialogue_manager.get_recent_history(state["session_id"])
        history_text = self.dialogue_manager.format_history(history)

        result = self.query_analyzer.resolve_query(query, history_text)

        if result["is_unclear"]:
            return {
                "standalone_query": query,
                "was_rewritten": False,
                "intent": self.INTENT_UNCLEAR,
            }

        return {
            "standalone_query": result["standalone_query"],
            "was_rewritten": result["was_rewritten"],
        }

    def route_after_rewrite(self, state: RAGState) -> str:
        if state.get("intent") == self.INTENT_UNCLEAR:
            return "unclear"
        return "continue"

    def analyze_query_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"] or state["query"]
        return self.query_analyzer.classify_and_split(query)

    def route_after_analysis(self, state: RAGState) -> str:
        if state.get("is_multi_query"):
            return "multi"

        intent = state.get("intent", self.INTENT_RAG)
        allowed = {
            self.INTENT_GREETING, self.INTENT_CALCULATOR, self.INTENT_CALENDAR,
            self.INTENT_AMBIGUOUS, self.INTENT_SUMMARIZE, self.INTENT_COMPARE, self.INTENT_RAG,
        }
        if intent not in allowed:
            intent = self.INTENT_RAG
        return intent

    def unclear_response_node(self, state: RAGState) -> Dict:
        return {
            "response": self.UNCLEAR_MESSAGE,
            "retrieved_docs": [],
            "context": "",
            "is_satisfied": True,
            "suggested_questions": [],
        }

    def process_multi_query_node(self, state: RAGState) -> Dict:
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

        all_satisfied = all(result.get("is_satisfied", False) for result in results)

        warnings = [
            (result.get("validation_result") or {}).get("warning")
            for result in results
            if (result.get("validation_result") or {}).get("warning")
        ]
        combined_validation: Dict[str, Any] = {}
        if warnings:
            combined_validation["warning"] = " | ".join(warnings)

        combined_suggestions: List[str] = []
        for result in results:
            for q in result.get("suggested_questions", []):
                if q not in combined_suggestions:
                    combined_suggestions.append(q)
        combined_suggestions = combined_suggestions[:3]

        return {
            "response": combined_response,
            "retrieved_docs": all_docs,
            "context": "",
            "is_satisfied": all_satisfied,
            "validation_result": combined_validation,
            "suggested_questions": combined_suggestions,
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

        mini_state: Dict[str, Any] = {
            "query": sub_query,
            "standalone_query": sub_query,
            "session_id": session_id,
            "intent": intent if intent in self.VALID_INTENTS else self.INTENT_RAG,
            "retrieved_docs": [],
            "context": "",
            "response": "",
            "suggested_questions": [],
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
            self.INTENT_UNCLEAR: self.unclear_response_node,
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
                "suggested_questions": mini_state.get("suggested_questions", []),
            }

        mini_state.update(self.retrieve_node(mini_state))

        if not self._is_context_usable(mini_state.get("retrieved_docs")):
            mini_state.update({
                "response": Config.NOT_FOUND_PHRASE,
                "retrieved_docs": [],
                "context": "",
                "is_satisfied": True,
                "validation_result": {},
                "suggested_questions": [],
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
            "suggested_questions": mini_state.get("suggested_questions", []),
        }

    def direct_response_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"] or state["query"]

        if self.query_analyzer.try_fast_greeting(query):
            return {
                "response": self._FIXED_GREETING_REPLY,
                "retrieved_docs": [],
                "context": "",
                "is_satisfied": True,
                "suggested_questions": [],
            }

        prompt = f"""به پیام زیر با لحنی رسمی و مؤدبانه پاسخ کوتاه بده (مثل یک دستیار سازمانی رسمی).
از اطلاعات غیرواقعی یا اسناد داخلی استفاده نکن، فقط یک پاسخ کوتاه و رسمی بده.

پیام کاربر: "{query}"

پاسخ:
"""
        raw = self.llm.invoke(prompt)
        response_text = raw.content if hasattr(raw, "content") else str(raw)

        return {
            "response": response_text.strip(),
            "retrieved_docs": [],
            "context": "",
            "is_satisfied": True,
            "suggested_questions": [],
        }

    def calculator_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"] or state["query"]
        fast_result = self.query_analyzer.try_fast_calculator(query)

        if fast_result is not None:
            response_text = fast_result
        else:
            prompt = f"""مسئله‌ی ریاضی زیر رو حل کن.
فقط نتیجه رو با یک محاسبه‌ی خیلی کوتاه، رسمی و خوانا برگردون، بدون توضیح اضافه.

مسئله: "{query}"

پاسخ:
"""
            raw = self.llm.invoke(prompt)
            response_text = (raw.content if hasattr(raw, "content") else str(raw)).strip()

        return {
            "response": response_text,
            "retrieved_docs": [],
            "context": "",
            "is_satisfied": True,
            "suggested_questions": [],
        }

    def calendar_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"] or state["query"]
        fast_result = self.query_analyzer.try_fast_calendar(query)

        if fast_result is not None:
            response_text = fast_result
        else:
            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            prompt = f"""تاریخ امروز {today_str} است.
با توجه به این تاریخ، به سؤال زیر پاسخ کوتاه، دقیق و رسمی بده.

سؤال: "{query}"

پاسخ:
"""
            raw = self.llm.invoke(prompt)
            response_text = (raw.content if hasattr(raw, "content") else str(raw)).strip()

        return {
            "response": response_text,
            "retrieved_docs": [],
            "context": "",
            "is_satisfied": True,
            "suggested_questions": [],
        }

    def clarify_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"] or state["query"]

        prompt = f"""پیام کاربر مبهم یا ناقصه و برای پاسخ دقیق باید اطلاعات بیشتری بگیریم.

فقط یک سؤال کوتاه (حداکثر یک خط) و با لحنی رسمی و مؤدبانه بپرس تا منظور کاربر دقیق بشه.
هیچ توضیح یا پاسخ دیگه‌ای نده.

پیام کاربر: "{query}"

سؤال تکمیلی:
"""
        raw = self.llm.invoke(prompt)
        response_text = raw.content if hasattr(raw, "content") else str(raw)

        return {
            "response": response_text.strip(),
            "retrieved_docs": [],
            "context": "",
            "is_satisfied": True,
            "suggested_questions": [],
        }

    def _extract_inline_text(self, query: str) -> Optional[str]:
        cleaned = re.sub(
            r'^(لطفا\s*)?(این\s*(متن|مطلب)\s*(رو|را)?\s*)?خلاصه\s*(کن|نویسی کن|بکن)[:\s]*',
            "",
            query.strip(),
            flags=re.IGNORECASE,
        ).strip()

        if len(cleaned) >= self.INLINE_SUMMARY_MIN_CHARS:
            return cleaned
        return None

    @staticmethod
    def _parse_llm_json(text: str) -> Optional[Dict[str, Any]]:
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


    @staticmethod
    def _parse_suggestions_block(text: str) -> List[str]:
        cleaned = text.strip()
        cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", cleaned, flags=re.MULTILINE).strip()
        try:
            suggestions = json.loads(cleaned)
        except json.JSONDecodeError:
            return []
        if not isinstance(suggestions, list):
            return []
        return [str(s).strip() for s in suggestions if str(s).strip()][:3]






    def summarize_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"] or state["query"]
        top_k = state.get("top_k", Config.TOP_K)
        inline_text = self._extract_inline_text(query)

        if inline_text:
            prompt = f"""متن زیر رو با لحنی رسمی خلاصه کن.
                خلاصه باید کوتاه، دقیق و شامل نکات اصلی باشه، بدون اضافه کردن اطلاعاتی که تو متن نیست.

                متن:
                {inline_text}

                خلاصه:
                """
            raw = self.llm.invoke(prompt)
            response_text = (raw.content if hasattr(raw, "content") else str(raw)).strip()

            return {
                "response": response_text,
                "retrieved_docs": [],
                "context": "",
                "is_satisfied": True,
                "suggested_questions": [],
            }

        docs = self.retriever.retrieve(
            query=query,
            k=top_k,
            access_level=state.get("user_access_level"),
        )

        if not self._is_context_usable(docs):
            return {
                "response": Config.NOT_FOUND_PHRASE,
                "retrieved_docs": [],
                "context": "",
                "is_satisfied": True,
                "validation_result": {},
                "suggested_questions": [],
            }

        context = "\n\n---\n\n".join(
            f"[Document {i}]:\n{doc['content']}" for i, doc in enumerate(docs, 1)
        )

        prompt = f"""شما دستیار خلاصه‌سازی اسناد سازمانی هستید. لحن رسمی و مؤدبانه باشد.
                فقط بر اساس اسناد زیر خلاصه‌ای کوتاه و دقیق درباره‌ی موضوع زیر بنویس. اگر اطلاعات کافی در اسناد نبود، صراحتاً همین را در خلاصه بنویس.

                خلاصه را دقیقاً به همین شکل بنویس، بدون هیچ‌گونه escape کردن نقل‌قول یا کاراکتر خاص:

                [خلاصه‌ی کامل شما اینجا، متن خام و عادی]

                ===SUGGESTED_QUESTIONS===
                ["سؤال پیشنهادی ۱", "سؤال پیشنهادی ۲", "سؤال پیشنهادی ۳"]

                اگر خلاصه‌ی معتبری تولید کردی، حداکثر ۳ سؤال تکمیلی کوتاه بعد از خط بالا به‌صورت آرایه‌ی JSON بنویس که پاسخشان مستقیماً در همین اسناد موجود باشد؛ در غیر این صورت [] بنویس.

                موضوع: "{query}"

                اسناد:
                {context}
                """
        raw = self.llm.invoke(prompt)
        raw_text = raw.content if hasattr(raw, "content") else str(raw)
        raw_text = raw_text if isinstance(raw_text, str) else str(raw_text)

        if "===SUGGESTED_QUESTIONS===" in raw_text:
            answer_part, _, suggestions_part = raw_text.partition("===SUGGESTED_QUESTIONS===")
            response_text = answer_part.strip()
            suggestions = self._parse_suggestions_block(suggestions_part)
        else:
            response_text = raw_text.strip()
            suggestions = []

        return {
            "response": response_text,
            "retrieved_docs": docs,
            "context": context,
            "is_satisfied": True,
            "suggested_questions": suggestions,
        }

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
                "response": Config.NOT_FOUND_PHRASE,
                "retrieved_docs": [],
                "context": "",
                "is_satisfied": True,
                "validation_result": {},
                "suggested_questions": [],
            }

        context = "\n\n---\n\n".join(
            f"[Document {i}]:\n{doc['content']}" for i, doc in enumerate(docs, 1)
        )

        prompt = f"""شما دستیار مقایسه‌ی اسناد سازمانی هستید. لحن رسمی و مؤدبانه باشد.
                    با توجه به اسناد زیر، درخواست مقایسه‌ی کاربر رو نکته‌به‌نکته یا در قالب جدول کوتاه پاسخ بده تا تفاوت‌ها و شباهت‌ها واضح باشد. فقط بر اساس اطلاعات موجود در اسناد بنویس؛ اگر اطلاعات کافی نبود صراحتاً همین را بگو.

                    مقایسه را دقیقاً به همین شکل بنویس، بدون هیچ‌گونه escape کردن نقل‌قول یا کاراکتر خاص:

                    [مقایسه‌ی کامل شما اینجا، متن خام و عادی]

                    ===SUGGESTED_QUESTIONS===
                    ["سؤال پیشنهادی ۱", "سؤال پیشنهادی ۲", "سؤال پیشنهادی ۳"]

                    اگر مقایسه‌ی معتبری تولید کردی، حداکثر ۳ سؤال تکمیلی کوتاه بعد از خط بالا به‌صورت آرایه‌ی JSON بنویس که پاسخشان مستقیماً در همین اسناد موجود باشد؛ در غیر این صورت [] بنویس.

                    درخواست: "{query}"

                    اسناد:
                    {context}
                        """
        raw = self.llm.invoke(prompt)
        raw_text = raw.content if hasattr(raw, "content") else str(raw)
        raw_text = raw_text if isinstance(raw_text, str) else str(raw_text)

        if "===SUGGESTED_QUESTIONS===" in raw_text:
            answer_part, _, suggestions_part = raw_text.partition("===SUGGESTED_QUESTIONS===")
            response_text = answer_part.strip()
            suggestions = self._parse_suggestions_block(suggestions_part)
        else:
            response_text = raw_text.strip()
            suggestions = []

        return {
            "response": response_text,
            "retrieved_docs": docs,
            "context": context,
            "is_satisfied": True,
            "suggested_questions": suggestions,
        }


    def retrieve_node(self, state: RAGState) -> Dict:
        query = state["standalone_query"]
        k = state.get("top_k", Config.TOP_K)

        retrieved_docs = self.retriever.retrieve(
            query=query,
            k=k,
            access_level=state.get("user_access_level"),
        )

        return {"retrieved_docs": retrieved_docs}

    def route_after_retrieve(self, state: RAGState) -> str:
        if self._is_context_usable(state.get("retrieved_docs")):
            return "continue"
        return "no_docs"

    def no_docs_response_node(self, state: RAGState) -> Dict:
        return {
            "response": Config.NOT_FOUND_PHRASE,
            "retrieved_docs": [],
            "context": "",
            "is_satisfied": True,
            "validation_result": {},
            "suggested_questions": [],
        }

    def generate_context_node(self, state: RAGState) -> Dict:
        context_parts = [
            f"[Document {i}]:\n{doc['content']}"
            for i, doc in enumerate(state["retrieved_docs"], 1)
        ]
        return {"context": "\n\n---\n\n".join(context_parts)}

    def generate_answer_node(self, state: RAGState) -> Dict:
        result = self.answer_generator.generate(
            query=state["standalone_query"],
            context=state["context"],
            previous_feedback=state.get("validation_result"),
        )
        return {
            "response": result["answer"],
            "suggested_questions": result["suggested_questions"],
        }

    def response_validator_node(self, state: RAGState) -> Dict:
        result = self.validator.validate(
            question=state["standalone_query"],
            context=state["context"],
            response=state["response"],
            retrieved_docs=state["retrieved_docs"],
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

        will_retry = not is_satisfied and new_retry_count < max_r

        if will_retry and result.get("retry_reason") == "completeness":
            current_top_k = state.get("top_k", Config.TOP_K)
            updates["top_k"] = current_top_k + Config.TOP_K_INCREMENT

        if not is_satisfied and new_retry_count >= max_r:
            result["warning"] = (
                f"این پاسخ ممکن است کامل یا دقیق نباشد (نمره کلی: {result.get('overall_score')})."
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
            "suggested_questions": [],
            "validation_result": {},
            "retry_count": 0,
            "is_satisfied": False,
            "top_k": top_k,
            "max_retries": max_retries,
            "user_access_level": user_access_level,
        }

        final_state: Dict[str, Any] = dict(initial_state)
        node_timings: List[Dict[str, Any]] = []
        last_ts = time.time()

        token = _on_step_ctx.set(on_step)
        try:
            for step_update in self.graph.stream(initial_state, stream_mode="updates"):
                for node_name, node_output in step_update.items():
                    now_ts = time.time()
                    node_duration = now_ts - last_ts
                    last_ts = now_ts
                    node_timings.append({"node": node_name, "duration": round(node_duration, 3)})
                    print(f"⏱️  [{node_name}] took {node_duration:.3f}s")
                    if isinstance(node_output, dict):
                        final_state.update(node_output)
        finally:
            _on_step_ctx.reset(token)

        processing_time = time.time() - start_time
        print(f"⏱️  TOTAL: {processing_time:.3f}s | breakdown: {node_timings}")

        self.dialogue_manager.add_turn(session_id, "user", query)
        self.dialogue_manager.add_turn(session_id, "assistant", final_state.get("response", ""))

        attempt_count = final_state.get("retry_count", 0) + 1

        response_text = final_state["response"].strip()
        no_answer_phrases = {
            Config.NOT_FOUND_PHRASE.strip(),
        }

        suggested_questions = final_state.get("suggested_questions") or []
        if (
            final_state.get("intent") in self.NON_SUGGESTIBLE_INTENTS
            or response_text in no_answer_phrases
        ):
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
            "node_timings": node_timings,
            "session_id": session_id,
            "standalone_query": final_state["standalone_query"],
            "was_rewritten": final_state["was_rewritten"],
        }