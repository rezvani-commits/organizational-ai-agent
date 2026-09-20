# import json
# import re
# from typing import Dict, Any, List, Optional
# from back.config import Config


# class ResponseValidator:

#     def __init__(
#         self,
#         llm,
#         faithfulness_threshold: float = None,
#         relevance_threshold: float = None,
#         completeness_threshold: float = None,
#     ):
#         self.llm = llm
#         self.faithfulness_threshold = (
#             faithfulness_threshold
#             if faithfulness_threshold is not None
#             else Config.FAITHFULNESS_THRESHOLD
#         )
#         self.relevance_threshold = (
#             relevance_threshold
#             if relevance_threshold is not None
#             else Config.RELEVANCE_THRESHOLD
#         )
#         self.completeness_threshold = (
#             completeness_threshold
#             if completeness_threshold is not None
#             else Config.COMPLETENESS_THRESHOLD
#         )
#         # برای تطبیق case-insensitive با پاسخ مدل
#         self._not_found_phrase = Config.NOT_FOUND_PHRASE.strip().lower()

#     # ---------------------------------------------------------------
#     # تشخیص پاسخ «اطلاعاتی پیدا نشد»
#     # ---------------------------------------------------------------
#     def _is_not_found_response(self, response: str) -> bool:
#         if not response:
#             return False
#         return self._not_found_phrase in response.strip().lower()

#     # ---------------------------------------------------------------
#     # Prompt سازی برای داور (Judge)
#     # ---------------------------------------------------------------
#     def _build_judge_prompt(self, question: str, context: str, response: str) -> str:
#         return f"""You are a strict and impartial evaluator (LLM-as-a-Judge) for a RAG system.

# You will be given: a user QUESTION, the retrieved CONTEXT that was available to the
# answering model, and the ANSWER that model produced. Evaluate the ANSWER on three
# criteria, each scored from 0 (worst) to 10 (best):

# 1. faithfulness: Does the answer rely ONLY on facts present in the CONTEXT, with no
#    hallucinated or fabricated information?
# 2. relevance: Does the answer directly address what the user asked in QUESTION,
#    without going off-topic or answering a different question?
# 3. completeness: Does the answer cover all the relevant information available in the
#    CONTEXT that is needed to fully answer the QUESTION (not leaving out important
#    available details)?

# QUESTION:
# {question}

# CONTEXT:
# {context}

# ANSWER:
# {response}

# Respond with STRICT JSON ONLY, no markdown fences, no extra text, in exactly this shape:
# {{
#   "faithfulness": {{"score": <0-10 integer>, "reason": "<short reason>"}},
#   "relevance": {{"score": <0-10 integer>, "reason": "<short reason>"}},
#   "completeness": {{"score": <0-10 integer>, "reason": "<short reason>"}}
# }}"""

#     # ---------------------------------------------------------------
#     # Helpers
#     # ---------------------------------------------------------------
#     def _extract_text(self, content: Any) -> str:
#         """تبدیل امن خروجی مدل (حتی اگر لیست یا آبجکت باشد) به متن رشته‌ای"""
#         if isinstance(content, str):
#             return content
#         elif isinstance(content, list):
#             parts = []
#             for item in content:
#                 if isinstance(item, dict) and "text" in item:
#                     parts.append(item["text"])
#                 elif isinstance(item, str):
#                     parts.append(item)
#                 else:
#                     parts.append(str(item))
#             return " ".join(parts)
#         return str(content)

#     def _parse_judge_json(self, text: str) -> Optional[Dict[str, Any]]:
#         """
#         خروجی داور را به JSON تبدیل می‌کند. حتی اگر مدل دور JSON را
#         با ```json ... ``` بپیچد یا متن اضافه قبل/بعدش بگذارد، تلاش
#         می‌کند اولین بلاک {...} معتبر را استخراج کند.
#         """
#         if not text:
#             return None

#         cleaned = text.strip()
#         cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", cleaned, flags=re.MULTILINE).strip()

#         try:
#             return json.loads(cleaned)
#         except json.JSONDecodeError:
#             pass

#         match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
#         if match:
#             try:
#                 return json.loads(match.group(0))
#             except json.JSONDecodeError:
#                 return None
#         return None

#     def _not_found_result(self) -> Dict[str, Any]:
#         """پاسخ صادقانه‌ی 'پیدا نشد' -> معتبر و نهایی، بدون نیاز به judge."""
#         return {
#             "is_valid": True,
#             "is_not_found": True,
#             "overall_score": None,
#             "faithfulness": {"score": None, "reason": "پاسخ 'پیدا نشد' بود؛ ارزیابی نشد"},
#             "relevance": {"score": None, "reason": "پاسخ 'پیدا نشد' بود؛ ارزیابی نشد"},
#             "completeness": {"score": None, "reason": "پاسخ 'پیدا نشد' بود؛ ارزیابی نشد"},
#             "retry_reason": None,
#             "warning": None,
#             "raw_judge_response": None,
#         }

#     def _fallback_result(self, raw_text: Optional[str] = None) -> Dict[str, Any]:
#         """در صورت شکست پارس JSON یا خطای LLM، یک نتیجه‌ی نامعتبر و امن
#         برمی‌گرداند تا گراف بتواند retry کند به‌جای کرش کردن."""
#         reason = "خروجی داور قابل تبدیل به JSON نبود یا خطا رخ داد"
#         return {
#             "is_valid": False,
#             "is_not_found": False,
#             "overall_score": 0.0,
#             "faithfulness": {"score": 0, "reason": reason},
#             "relevance": {"score": 0, "reason": reason},
#             "completeness": {"score": 0, "reason": reason},
#             "retry_reason": "faithfulness_relevance",
#             "warning": "خطای فنی در فرآیند ارزیابی رخ داد",
#             "raw_judge_response": raw_text,
#         }

#     def _decide_retry_reason(
#         self, f_score: float, r_score: float, c_score: float
#     ) -> Optional[str]:
#         """
#         اولویت با completeness است (چون تنها معیاریست که با retrieve مجدد
#         قابل حل است). faithfulness/relevance پایین یعنی مشکل از تولید پاسخ
#         است، نه بازیابی.
#         """
#         if c_score < self.completeness_threshold:
#             return "completeness"
#         if f_score < self.faithfulness_threshold or r_score < self.relevance_threshold:
#             return "faithfulness_relevance"
#         return None

#     # ---------------------------------------------------------------
#     # متد اصلی
#     # ---------------------------------------------------------------
#     def validate(
#         self,
#         question: str,
#         context: str,
#         response: str,
#         retrieved_docs: Optional[List[Dict]] = None,
#     ) -> Dict[str, Any]:

#         # ۱. اگر پاسخ صادقانه «پیدا نشد» بود، اصلاً نیازی به judge نیست
#         if self._is_not_found_response(response):
#             return self._not_found_result()

#         # ۲. صدا زدن داور
#         prompt = self._build_judge_prompt(question, context, response)
#         try:
#             raw = self.llm.invoke(prompt)
#             raw_text = self._extract_text(raw.content)
#         except Exception as e:
#             return self._fallback_result(raw_text=f"LLM invoke error: {e}")

#         parsed = self._parse_judge_json(raw_text)
#         if parsed is None:
#             return self._fallback_result(raw_text=raw_text)

#         try:
#             faithfulness = parsed.get("faithfulness", {}) or {}
#             relevance = parsed.get("relevance", {}) or {}
#             completeness = parsed.get("completeness", {}) or {}

#             f_score = float(faithfulness.get("score", 0))
#             r_score = float(relevance.get("score", 0))
#             c_score = float(completeness.get("score", 0))
#         except (TypeError, ValueError):
#             return self._fallback_result(raw_text=raw_text)

#         is_valid = (
#             f_score >= self.faithfulness_threshold
#             and r_score >= self.relevance_threshold
#             and c_score >= self.completeness_threshold
#         )

#         retry_reason = None if is_valid else self._decide_retry_reason(f_score, r_score, c_score)
#         overall_score = round((f_score + r_score + c_score) / 3, 2)

#         return {
#             "is_valid": is_valid,
#             "is_not_found": False,
#             "overall_score": overall_score,
#             "faithfulness": faithfulness,
#             "relevance": relevance,
#             "completeness": completeness,
#             "retry_reason": retry_reason,
#             # این فیلد فقط زمانی پر می‌شود که RAGGraph تصمیم بگیرد دیگر retry نکند
#             "warning": None,
#             "raw_judge_response": raw_text,
#         }

















import json
import re
import asyncio
from typing import Dict, Any, List, Optional
from back.config import Config

# ---------------------------------------------------------------
# RAGAS (اختیاری) - اگر نصب نباشد یا خطا بدهد، سیستم فقط با
# LLM-as-Judge کار می‌کند و کرش نمی‌کند.
# ---------------------------------------------------------------
try:
    from ragas import SingleTurnSample
    from ragas.metrics import Faithfulness, ResponseRelevancy, LLMContextPrecisionWithoutReference
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper

    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False


class ResponseValidator:

    def __init__(
        self,
        llm,
        faithfulness_threshold: float = None,
        relevance_threshold: float = None,
        completeness_threshold: float = None,
        use_ragas: bool = None,
        embeddings=None,
        ragas_weight: float = 0.4,
    ):
        self.llm = llm
        self.faithfulness_threshold = (
            faithfulness_threshold
            if faithfulness_threshold is not None
            else Config.FAITHFULNESS_THRESHOLD
        )
        self.relevance_threshold = (
            relevance_threshold
            if relevance_threshold is not None
            else Config.RELEVANCE_THRESHOLD
        )
        self.completeness_threshold = (
            completeness_threshold
            if completeness_threshold is not None
            else Config.COMPLETENESS_THRESHOLD
        )
        # برای تطبیق case-insensitive با پاسخ مدل
        self._not_found_phrase = Config.NOT_FOUND_PHRASE.strip().lower()

        # ---- تنظیمات RAGAS ----
        # use_ragas اگر صراحتاً پاس نشود، از Config خوانده می‌شود (در صورت وجود)
        # و اگر آنجا هم نبود، فقط زمانی فعال می‌شود که کتابخانه نصب باشد.
        if use_ragas is None:
            use_ragas = getattr(Config, "USE_RAGAS", True)
        self.use_ragas = bool(use_ragas) and RAGAS_AVAILABLE

        # وزن نمرات RAGAS در ترکیب نهایی با LLM-judge (۰ تا ۱).
        # مثلاً 0.4 یعنی ۴۰٪ RAGAS + ۶۰٪ LLM-judge.
        self.ragas_weight = ragas_weight

        self._ragas_llm_wrapper = None
        self._ragas_embeddings_wrapper = None
        self._faithfulness_metric = None
        self._answer_relevancy_metric = None
        self._context_precision_metric = None

        if self.use_ragas:
            try:
                self._ragas_llm_wrapper = LangchainLLMWrapper(self.llm)
                self._faithfulness_metric = Faithfulness(llm=self._ragas_llm_wrapper)
                self._context_precision_metric = LLMContextPrecisionWithoutReference(
                    llm=self._ragas_llm_wrapper
                )
                # answer_relevancy به embeddings نیاز دارد؛ اگر پاس نشده باشد
                # این متریک غیرفعال می‌شود ولی faithfulness/context_precision فعال می‌مانند.
                if embeddings is not None:
                    self._ragas_embeddings_wrapper = LangchainEmbeddingsWrapper(embeddings)
                    self._answer_relevancy_metric = ResponseRelevancy(
                        llm=self._ragas_llm_wrapper,
                        embeddings=self._ragas_embeddings_wrapper,
                    )
            except Exception:
                # اگر ساخت متریک‌ها با خطا مواجه شد، RAGAS را کامل غیرفعال کن
                # تا validate() هیچ‌وقت به خاطر این بخش کرش نکند.
                self.use_ragas = False

    # ---------------------------------------------------------------
    # تشخیص پاسخ «اطلاعاتی پیدا نشد»
    # ---------------------------------------------------------------
    def _is_not_found_response(self, response: str) -> bool:
        if not response:
            return False
        return self._not_found_phrase in response.strip().lower()

    # ---------------------------------------------------------------
    # Prompt سازی برای داور (Judge)
    # ---------------------------------------------------------------
    def _build_judge_prompt(self, question: str, context: str, response: str) -> str:
        return f"""You are a strict and impartial evaluator (LLM-as-a-Judge) for a RAG system.

You will be given: a user QUESTION, the retrieved CONTEXT that was available to the
answering model, and the ANSWER that model produced. Evaluate the ANSWER on three
criteria, each scored from 0 (worst) to 10 (best):

1. faithfulness: Does the answer rely ONLY on facts present in the CONTEXT, with no
   hallucinated or fabricated information?
2. relevance: Does the answer directly address what the user asked in QUESTION,
   without going off-topic or answering a different question?
3. completeness: Does the answer cover all the relevant information available in the
   CONTEXT that is needed to fully answer the QUESTION (not leaving out important
   available details)?

QUESTION:
{question}

CONTEXT:
{context}

ANSWER:
{response}

Respond with STRICT JSON ONLY, no markdown fences, no extra text, in exactly this shape:
{{
  "faithfulness": {{"score": <0-10 integer>, "reason": "<short reason>"}},
  "relevance": {{"score": <0-10 integer>, "reason": "<short reason>"}},
  "completeness": {{"score": <0-10 integer>, "reason": "<short reason>"}}
}}"""

    # ---------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------
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

    def _parse_judge_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        خروجی داور را به JSON تبدیل می‌کند. حتی اگر مدل دور JSON را
        با ```json ... ``` بپیچد یا متن اضافه قبل/بعدش بگذارد، تلاش
        می‌کند اولین بلاک {...} معتبر را استخراج کند.
        """
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

    def _not_found_result(self) -> Dict[str, Any]:
        """پاسخ صادقانه‌ی 'پیدا نشد' -> معتبر و نهایی، بدون نیاز به judge."""
        return {
            "is_valid": True,
            "is_not_found": True,
            "overall_score": None,
            "faithfulness": {"score": None, "reason": "پاسخ 'پیدا نشد' بود؛ ارزیابی نشد"},
            "relevance": {"score": None, "reason": "پاسخ 'پیدا نشد' بود؛ ارزیابی نشد"},
            "completeness": {"score": None, "reason": "پاسخ 'پیدا نشد' بود؛ ارزیابی نشد"},
            "retry_reason": None,
            "warning": None,
            "raw_judge_response": None,
            "ragas": None,
        }

    def _fallback_result(self, raw_text: Optional[str] = None) -> Dict[str, Any]:
        """در صورت شکست پارس JSON یا خطای LLM، یک نتیجه‌ی نامعتبر و امن
        برمی‌گرداند تا گراف بتواند retry کند به‌جای کرش کردن."""
        reason = "خروجی داور قابل تبدیل به JSON نبود یا خطا رخ داد"
        return {
            "is_valid": False,
            "is_not_found": False,
            "overall_score": 0.0,
            "faithfulness": {"score": 0, "reason": reason},
            "relevance": {"score": 0, "reason": reason},
            "completeness": {"score": 0, "reason": reason},
            "retry_reason": "faithfulness_relevance",
            "warning": "خطای فنی در فرآیند ارزیابی رخ داد",
            "raw_judge_response": raw_text,
            "ragas": None,
        }

    def _decide_retry_reason(
        self, f_score: float, r_score: float, c_score: float
    ) -> Optional[str]:
        """
        اولویت با completeness است (چون تنها معیاریست که با retrieve مجدد
        قابل حل است). faithfulness/relevance پایین یعنی مشکل از تولید پاسخ
        است، نه بازیابی.
        """
        if c_score < self.completeness_threshold:
            return "completeness"
        if f_score < self.faithfulness_threshold or r_score < self.relevance_threshold:
            return "faithfulness_relevance"
        return None

    # ---------------------------------------------------------------
    # ارزیابی با RAGAS
    # ---------------------------------------------------------------
    def _evaluate_with_ragas(
        self, question: str, context: str, response: str
    ) -> Optional[Dict[str, Any]]:
        """
        اجرای متریک‌های RAGAS روی همان یک نمونه (single-turn).
        خروجی نمرات را روی مقیاس ۰-۱۰ (هماهنگ با LLM-judge) برمی‌گرداند.
        اگر RAGAS غیرفعال باشد یا خطا بدهد، None برمی‌گرداند تا validate()
        بدون آن ادامه دهد (fail-open روی LLM-judge).
        """
        if not self.use_ragas:
            return None

        try:
            sample = SingleTurnSample(
                user_input=question,
                response=response,
                retrieved_contexts=[context] if isinstance(context, str) else list(context),
            )

            async def _score_all():
                results = {}
                results["faithfulness"] = await self._faithfulness_metric.single_turn_ascore(sample)
                results["context_precision"] = await self._context_precision_metric.single_turn_ascore(
                    sample
                )
                if self._answer_relevancy_metric is not None:
                    results["answer_relevancy"] = await self._answer_relevancy_metric.single_turn_ascore(
                        sample
                    )
                return results

            raw_scores = asyncio.run(_score_all())

            # تبدیل مقیاس ۰-۱ به ۰-۱۰ برای هماهنگی با LLM-judge
            return {
                "faithfulness": round(raw_scores["faithfulness"] * 10, 2),
                # answer_relevancy معادل نزدیک‌ترین متریک RAGAS به relevance ماست
                "relevance": (
                    round(raw_scores["answer_relevancy"] * 10, 2)
                    if "answer_relevancy" in raw_scores
                    else None
                ),
                # context_precision معادل نزدیک‌ترین متریک RAGAS به completeness ماست
                "completeness": round(raw_scores["context_precision"] * 10, 2),
            }
        except Exception as e:
            # هر خطایی (مشکل شبکه، ناسازگاری نسخه، ...) نباید کل validate را بترکاند
            return {"error": str(e)}

    def _combine_scores(
        self, llm_score: float, ragas_score: Optional[float]
    ) -> float:
        """ترکیب وزنی نمره LLM-judge و RAGAS برای یک معیار مشخص.
        اگر نمره RAGAS برای آن معیار موجود نباشد (مثلاً answer_relevancy
        بدون embeddings)، فقط از نمره LLM-judge استفاده می‌شود."""
        if ragas_score is None:
            return llm_score
        return round((1 - self.ragas_weight) * llm_score + self.ragas_weight * ragas_score, 2)

    # ---------------------------------------------------------------
    # متد اصلی
    # ---------------------------------------------------------------
    def validate(
        self,
        question: str,
        context: str,
        response: str,
        retrieved_docs: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:

        # ۱. اگر پاسخ صادقانه «پیدا نشد» بود، اصلاً نیازی به judge نیست
        if self._is_not_found_response(response):
            return self._not_found_result()

        # ۲. صدا زدن داور (LLM-as-Judge)
        prompt = self._build_judge_prompt(question, context, response)
        try:
            raw = self.llm.invoke(prompt)
            raw_text = self._extract_text(raw.content)
        except Exception as e:
            return self._fallback_result(raw_text=f"LLM invoke error: {e}")

        parsed = self._parse_judge_json(raw_text)
        if parsed is None:
            return self._fallback_result(raw_text=raw_text)

        try:
            faithfulness = parsed.get("faithfulness", {}) or {}
            relevance = parsed.get("relevance", {}) or {}
            completeness = parsed.get("completeness", {}) or {}

            f_score = float(faithfulness.get("score", 0))
            r_score = float(relevance.get("score", 0))
            c_score = float(completeness.get("score", 0))
        except (TypeError, ValueError):
            return self._fallback_result(raw_text=raw_text)

        # ۳. صدا زدن RAGAS (اختیاری) و ترکیب نمرات
        ragas_result = self._evaluate_with_ragas(question, context, response)
        ragas_error = None
        if ragas_result and "error" in ragas_result:
            ragas_error = ragas_result["error"]
            ragas_result = None

        if ragas_result:
            f_score = self._combine_scores(f_score, ragas_result.get("faithfulness"))
            r_score = self._combine_scores(r_score, ragas_result.get("relevance"))
            c_score = self._combine_scores(c_score, ragas_result.get("completeness"))

        is_valid = (
            f_score >= self.faithfulness_threshold
            and r_score >= self.relevance_threshold
            and c_score >= self.completeness_threshold
        )

        retry_reason = None if is_valid else self._decide_retry_reason(f_score, r_score, c_score)
        overall_score = round((f_score + r_score + c_score) / 3, 2)

        return {
            "is_valid": is_valid,
            "is_not_found": False,
            "overall_score": overall_score,
            # نمره نهایی (ترکیب‌شده) در score قرار می‌گیرد ولی reason همان توضیح LLM-judge می‌ماند
            "faithfulness": {"score": f_score, "reason": faithfulness.get("reason")},
            "relevance": {"score": r_score, "reason": relevance.get("reason")},
            "completeness": {"score": c_score, "reason": completeness.get("reason")},
            "retry_reason": retry_reason,
            # این فیلد فقط زمانی پر می‌شود که RAGGraph تصمیم بگیرد دیگر retry نکند
            "warning": ragas_error,
            "raw_judge_response": raw_text,
            "ragas": ragas_result,
        }
