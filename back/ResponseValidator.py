import json
import re
from typing import Dict, Any, List, Optional
from back.config import Config


class ResponseValidator:

    def __init__(
        self,
        llm,
        faithfulness_threshold: float = None,
        relevance_threshold: float = None,
        completeness_threshold: float = None,
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

        # ۲. صدا زدن داور
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
            "faithfulness": faithfulness,
            "relevance": relevance,
            "completeness": completeness,
            "retry_reason": retry_reason,
            # این فیلد فقط زمانی پر می‌شود که RAGGraph تصمیم بگیرد دیگر retry نکند
            "warning": None,
            "raw_judge_response": raw_text,
        }