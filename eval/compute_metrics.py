# import argparse
# import json
# import re
# from pathlib import Path
# from collections import defaultdict
# from typing import Dict, List, Any

# EVAL_DIR = Path(__file__).parent
# RESULTS_DIR = EVAL_DIR / "results"
# REPORTS_DIR = EVAL_DIR / "reports"

# # FIX 3: به‌جای رشته‌ی هاردکد جدا (که ممکنه با Config واقعی هم‌خوان نمونه و
# # بی‌صدا خراب بشه)، مستقیم از خود Config پروژه ایمپورت می‌کنیم.
# from back.config import Config

# NOT_FOUND_PHRASE = Config.NOT_FOUND_PHRASE
# FAITHFULNESS_THRESHOLD = Config.FAITHFULNESS_THRESHOLD
# RELEVANCE_THRESHOLD = Config.RELEVANCE_THRESHOLD


# def load_results(model_name: str) -> Dict:
#     safe_name = model_name.replace("/", "_")
#     path = RESULTS_DIR / f"{safe_name}.json"
#     if not path.exists():
#         raise FileNotFoundError(f"فایل نتایج مدل {model_name} پیدا نشد: {path}")
#     with open(path, encoding="utf-8") as f:
#         return json.load(f)


# def compute_retrieval_metrics(main_results: List[Dict]) -> Dict[str, float]:
   
#     k_values = [1, 3, 5]
#     precision_at_k = {k: [] for k in k_values}
#     recall_at_k = {k: [] for k in k_values}
#     reciprocal_ranks = []

#     for r in main_results:
#         if r.get("error"):
#             continue

#         expected_chunk = r.get("expected_chunk_id")
#         if not expected_chunk:
#             continue

#         retrieved = r.get("retrieved_chunk_ids", []) or []

#         if expected_chunk in retrieved:
#             rank = retrieved.index(expected_chunk) + 1
#             reciprocal_ranks.append(1.0 / rank)
#         else:
#             reciprocal_ranks.append(0.0)

#         for k in k_values:
#             top_k = retrieved[:k]
#             relevant_in_top_k = sum(1 for c in top_k if c == expected_chunk)
#             precision_at_k[k].append(relevant_in_top_k / k if k > 0 else 0)
#             recall_at_k[k].append(relevant_in_top_k / 1.0)

#     return {
#         "MRR": sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0,
#         **{f"Precision@{k}": sum(v) / len(v) if v else 0 for k, v in precision_at_k.items()},
#         **{f"Recall@{k}": sum(v) / len(v) if v else 0 for k, v in recall_at_k.items()},
#     }


# def compute_generation_metrics(main_results: List[Dict]) -> Dict[str, float]:
    
#     faithfulness_raw_scores = []
#     relevance_raw_scores = []
#     faithfulness_pass = []
#     relevance_pass = []

#     for r in main_results:
#         if r.get("error"):
#             continue

#         validation = r.get("validation_result") or {}
#         if validation.get("is_not_found"):
#             continue  # judge اصلاً روی این رکورد اجرا نشده

#         f = validation.get("faithfulness") or {}
#         rel = validation.get("relevance") or {}
#         f_score = f.get("score")
#         r_score = rel.get("score")

#         if f_score is not None:
#             faithfulness_raw_scores.append(f_score)
#             faithfulness_pass.append(1.0 if f_score >= FAITHFULNESS_THRESHOLD else 0.0)
#         if r_score is not None:
#             relevance_raw_scores.append(r_score)
#             relevance_pass.append(1.0 if r_score >= RELEVANCE_THRESHOLD else 0.0)

#     return {
#         "Faithfulness_Mean_Score": (
#             sum(faithfulness_raw_scores) / len(faithfulness_raw_scores)
#             if faithfulness_raw_scores else 0
#         ),
#         "Faithfulness_Pass_Rate": (
#             sum(faithfulness_pass) / len(faithfulness_pass) if faithfulness_pass else 0
#         ),
#         "Answer_Relevance_Mean_Score": (
#             sum(relevance_raw_scores) / len(relevance_raw_scores)
#             if relevance_raw_scores else 0
#         ),
#         "Answer_Relevance_Pass_Rate": (
#             sum(relevance_pass) / len(relevance_pass) if relevance_pass else 0
#         ),
#     }


# def compute_citation_accuracy(main_results: List[Dict]) -> Dict[str, float]:

   
#     citation_pattern = re.compile(r'(ماده|بند|تبصره)\s+(\d+|[۰-۹]+)')

#     correct = 0
#     total = 0
#     skipped_no_metadata = 0

#     for r in main_results:
#         if r.get("error") or not r.get("answer"):
#             continue

#         answer = r["answer"]
#         citations_in_answer = citation_pattern.findall(answer)
#         if not citations_in_answer:
#             continue

#         chunk_meta = r.get("retrieved_chunk_metadata")
#         if not chunk_meta:
#             skipped_no_metadata += len(citations_in_answer)
#             continue

#         locator_text = " ".join(
#             f"{m.get('locator', '')} {m.get('sub_reference', '')}" for m in chunk_meta
#         )
#         locator_normalized = locator_text  # locator خودش معمولاً رقمی است (طبق registry)

#         for kind, number in citations_in_answer:
#             total += 1
#             if f"{kind} {number}" in locator_normalized or number in locator_normalized:
#                 correct += 1

#     return {
#         "Citation_Accuracy": correct / total if total else 0,
#         "Total_Citations_Checked": total,
#         "Citations_Skipped_No_Metadata": skipped_no_metadata,
#     }


# def compute_abstention_metrics(abstention_results: List[Dict]) -> Dict[str, float]:
    
#     valid = [r for r in abstention_results if not r.get("error")]
#     n = len(valid)
#     if n == 0:
#         return {"Abstention_Accuracy": 0, "False_Answer_Rate": 0, "Intent_Misroute_Rate": 0}

#     correctly_abstained_count = sum(1 for r in valid if r.get("correctly_abstained"))
#     false_answer_count = sum(1 for r in valid if not r.get("correctly_abstained"))
#     intent_misroute_count = sum(1 for r in valid if r.get("intent_misroute"))

#     return {
#         "Abstention_Accuracy": correctly_abstained_count / n,
#         "False_Answer_Rate": false_answer_count / n,  
#         "Intent_Misroute_Rate": intent_misroute_count / n,
#     }


# def compute_false_abstention_rate(main_results: List[Dict]) -> float:
#     valid = [r for r in main_results if not r.get("error")]
#     if not valid:
#         return 0

#     false_abstentions = sum(
#         1 for r in valid
#         if (r.get("answer") or "").strip() == NOT_FOUND_PHRASE.strip() and r.get("expected_chunk_id")
#     )
#     return false_abstentions / len(valid)


# def compute_latency_metrics(main_results: List[Dict], abstention_results: List[Dict]) -> Dict[str, float]:
#     all_latencies = []
#     for r in main_results + abstention_results:
#         if r.get("error"):
#             continue
#         latency = r.get("processing_time")
#         if latency:
#             all_latencies.append(latency)

#     if not all_latencies:
#         return {"Latency_Mean": 0, "Latency_p50": 0, "Latency_p95": 0}

#     all_latencies.sort()
#     n = len(all_latencies)
#     return {
#         "Latency_Mean": sum(all_latencies) / n,
#         "Latency_p50": all_latencies[n // 2],
#         "Latency_p95": all_latencies[min(int(n * 0.95), n - 1)],
#     }


# def compute_access_violation_rate(abstention_results: List[Dict]) -> float:
#     restricted = [
#         r for r in abstention_results
#         if not r.get("error") and r.get("test_access_level") is not None
#     ]
#     if not restricted:
#         return 0

#     violations = sum(1 for r in restricted if not r.get("correctly_abstained"))
#     return violations / len(restricted)


# def compute_all_metrics(model_name: str) -> Dict[str, Any]:
#     results = load_results(model_name)
#     main_results = results.get("main", [])
#     abstention_results = results.get("abstention", [])

#     metrics = {
#         "model": model_name,
#         "total_main_queries": len(main_results),
#         "total_abstention_queries": len(abstention_results),
#         "errors_count": sum(1 for r in main_results + abstention_results if r.get("error")),
#     }

#     metrics.update(compute_retrieval_metrics(main_results))
#     metrics.update(compute_generation_metrics(main_results))
#     metrics.update(compute_citation_accuracy(main_results))
#     metrics.update(compute_abstention_metrics(abstention_results))
#     metrics["False_Abstention_Rate"] = compute_false_abstention_rate(main_results)
#     metrics.update(compute_latency_metrics(main_results, abstention_results))
#     metrics["Access_Violation_Rate"] = compute_access_violation_rate(abstention_results)

#     return metrics


# def generate_comparison_report(all_metrics: List[Dict]) -> str:
#     lines = []
#     lines.append("=" * 100)
#     lines.append("گزارش مقایسه‌ای متریک‌های ارزیابی سیستم RAG")
#     lines.append("=" * 100)
#     lines.append("")

#     headers = ["متریک"] + [m["model"] for m in all_metrics]
#     lines.append(" | ".join(f"{h:<24}" for h in headers))
#     lines.append("-" * 100)

#     metric_keys = [
#         ("MRR", "MRR"),
#         ("Recall@1", "Recall@1 (Hit Rate)"),
#         ("Recall@3", "Recall@3 (Hit Rate)"),
#         ("Recall@5", "Recall@5 (Hit Rate)"),
#         ("Faithfulness_Mean_Score", "Faithfulness (میانگین 0-10)"),
#         ("Faithfulness_Pass_Rate", "Faithfulness (نرخ عبور آستانه)"),
#         ("Answer_Relevance_Mean_Score", "Relevance (میانگین 0-10)"),
#         ("Answer_Relevance_Pass_Rate", "Relevance (نرخ عبور آستانه)"),
#         ("Citation_Accuracy", "Citation Accuracy"),
#         ("Abstention_Accuracy", "Abstention Accuracy"),
#         ("False_Abstention_Rate", "False Abstention Rate"),
#         ("False_Answer_Rate", "False Answer Rate"),
#         ("Intent_Misroute_Rate", "Intent Misroute Rate"),
#         ("Access_Violation_Rate", "⚠️ Access Violation Rate"),
#         ("Latency_Mean", "Latency Mean (s)"),
#         ("Latency_p50", "Latency p50 (s)"),
#         ("Latency_p95", "Latency p95 (s)"),
#     ]

#     for key, label in metric_keys:
#         row = [f"{label:<24}"]
#         for m in all_metrics:
#             value = m.get(key, 0)
#             row.append(f"{value:<24.3f}" if isinstance(value, float) else f"{value:<24}")
#         lines.append(" | ".join(row))

#     lines.append("=" * 100)
#     lines.append("")
#     lines.append("آمار تکمیلی:")
#     for m in all_metrics:
#         lines.append(f"  {m['model']}:")
#         lines.append(f"    - تعداد کل کوئری‌ها: {m['total_main_queries'] + m['total_abstention_queries']}")
#         lines.append(f"    - تعداد خطاها: {m['errors_count']}")
#         lines.append(f"    - ارجاعات چک‌شده: {m.get('Total_Citations_Checked', 0)}")
#     lines.append("")

#     return "\n".join(lines)


# def main():
#     parser = argparse.ArgumentParser(description="محاسبه‌ی متریک‌های ارزیابی از خروجی run_eval.py")
#     parser.add_argument("--models", nargs="+", help="لیست نام مدل‌ها برای مقایسه")
#     parser.add_argument("--all", action="store_true", help="محاسبه برای همه‌ی مدل‌های موجود در results/")
#     args = parser.parse_args()

#     if args.all:
#         model_files = list(RESULTS_DIR.glob("*.json"))
#         model_names = [f.stem for f in model_files]
#     elif args.models:
#         model_names = args.models
#     else:
#         print("لطفاً یا --models یا --all را مشخص کنید.")
#         return

#     print(f"در حال محاسبه‌ی متریک‌ها برای {len(model_names)} مدل...")

#     all_metrics = []
#     for model_name in model_names:
#         try:
#             print(f"  پردازش {model_name}...")
#             metrics = compute_all_metrics(model_name)
#             all_metrics.append(metrics)
#         except Exception as e:
#             print(f"  ❌ خطا در پردازش {model_name}: {e}")

#     REPORTS_DIR.mkdir(exist_ok=True)
#     report_json_path = REPORTS_DIR / "metrics_comparison.json"
#     with open(report_json_path, "w", encoding="utf-8") as f:
#         json.dump(all_metrics, f, ensure_ascii=False, indent=2)
#     print(f"\n✅ گزارش JSON ذخیره شد -> {report_json_path}")

#     report_text = generate_comparison_report(all_metrics)
#     report_txt_path = REPORTS_DIR / "metrics_comparison.txt"
#     with open(report_txt_path, "w", encoding="utf-8") as f:
#         f.write(report_text)
#     print(f"✅ گزارش متنی ذخیره شد -> {report_txt_path}")

#     print("\n" + report_text)


# if __name__ == "__main__":
#     main()







import argparse
import json
import re
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from back.config import Config


# ============================================================
# Paths
# ============================================================

EVAL_DIR = Path(__file__).parent
RESULTS_DIR = EVAL_DIR / "results"
REPORTS_DIR = EVAL_DIR / "reports"

DEFAULT_MODEL = "gpt-4.1-mini"
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-base"


# ============================================================
# Helpers
# ============================================================

def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_id(value):
    if value is None:
        return None
    return str(value).strip()


def get_result_file(model_name):
    return RESULTS_DIR / f"{model_name}.json"


def normalize_persian_digits(text):
    if text is None:
        return ""

    table = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹",
        "0123456789",
    )

    return str(text).translate(table)


# ============================================================
# Retrieval Metrics
# ============================================================

def compute_retrieval_metrics(main_results):
    reciprocal_ranks = []

    precision_at_1 = []
    precision_at_3 = []
    precision_at_5 = []

    recall_at_1 = []
    recall_at_3 = []
    recall_at_5 = []

    for result in main_results:
        expected_chunk_id = result.get(
            "expected_chunk_id"
        )

        retrieved_chunk_ids = result.get(
            "retrieved_chunk_ids",
            [],
        )

        if not expected_chunk_id:
            continue

        expected_chunk_id = str(
            expected_chunk_id
        )

        retrieved_chunk_ids = [
            str(x)
            for x in retrieved_chunk_ids
        ]

        # ----------------------------
        # MRR
        # ----------------------------

        rank = None

        for i, chunk_id in enumerate(
            retrieved_chunk_ids,
            start=1,
        ):
            if chunk_id == expected_chunk_id:
                rank = i
                break

        reciprocal_ranks.append(
            1 / rank if rank else 0.0
        )

        # ----------------------------
        # Precision / Recall
        # ----------------------------

        for k, target in [
            (1, precision_at_1),
            (3, precision_at_3),
            (5, precision_at_5),
        ]:
            top_k = retrieved_chunk_ids[:k]

            relevant = (
                1
                if expected_chunk_id in top_k
                else 0
            )

            target.append(
                relevant / k
            )

        for k, target in [
            (1, recall_at_1),
            (3, recall_at_3),
            (5, recall_at_5),
        ]:
            top_k = retrieved_chunk_ids[:k]

            relevant = (
                1
                if expected_chunk_id in top_k
                else 0
            )

            target.append(relevant)

    return {
        "MRR": (
            float(np.mean(reciprocal_ranks))
            if reciprocal_ranks
            else 0.0
        ),
        "Precision@1": (
            float(np.mean(precision_at_1))
            if precision_at_1
            else 0.0
        ),
        "Precision@3": (
            float(np.mean(precision_at_3))
            if precision_at_3
            else 0.0
        ),
        "Precision@5": (
            float(np.mean(precision_at_5))
            if precision_at_5
            else 0.0
        ),
        "Recall@1": (
            float(np.mean(recall_at_1))
            if recall_at_1
            else 0.0
        ),
        "Recall@3": (
            float(np.mean(recall_at_3))
            if recall_at_3
            else 0.0
        ),
        "Recall@5": (
            float(np.mean(recall_at_5))
            if recall_at_5
            else 0.0
        ),
    }


# ============================================================
# Generation Metrics
# ============================================================

def compute_generation_metrics(main_results):
    faithfulness_scores = []
    relevance_scores = []

    for result in main_results:
        validation = (
            result.get("validation_result")
            or {}
        )

        faithfulness = (
            validation.get("faithfulness")
            or {}
        )

        relevance = (
            validation.get("relevance")
            or {}
        )

        if faithfulness.get("score") is not None:
            faithfulness_scores.append(
                float(
                    faithfulness["score"]
                )
            )

        if relevance.get("score") is not None:
            relevance_scores.append(
                float(
                    relevance["score"]
                )
            )

    return {
        "Faithfulness_Mean_Score": (
            float(np.mean(faithfulness_scores))
            if faithfulness_scores
            else 0.0
        ),
        "Faithfulness_Pass_Rate": (
            float(
                np.mean(
                    [
                        score >= 7
                        for score in faithfulness_scores
                    ]
                )
            )
            if faithfulness_scores
            else 0.0
        ),
        "Answer_Relevance_Mean_Score": (
            float(np.mean(relevance_scores))
            if relevance_scores
            else 0.0
        ),
        "Answer_Relevance_Pass_Rate": (
            float(
                np.mean(
                    [
                        score >= 7
                        for score in relevance_scores
                    ]
                )
            )
            if relevance_scores
            else 0.0
        ),
    }


# ============================================================
# Ideal Answer Similarity
# ============================================================

def compute_ideal_answer_similarity(main_results):
    """
    Compare generated answer with ideal_answer.

    The ideal_answer is already stored inside each
    result record by run_eval.py, so no additional
    Gold Dataset lookup is necessary.
    """

    print(
        "\nLoading embedding model for "
        "Ideal Answer evaluation..."
    )

    embedding_model = SentenceTransformer(
        EMBEDDING_MODEL_NAME
    )

    similarities = []

    checked = 0
    skipped = 0

    skipped_records = []

    for result in main_results:

        record_id = result.get("record_id")

        ideal_answer = result.get(
            "ideal_answer"
        )

        generated_answer = result.get(
            "answer"
        )

        # ----------------------------------------------------
        # Missing ideal answer
        # ----------------------------------------------------

        if not ideal_answer:
            skipped += 1

            skipped_records.append(
                {
                    "record_id": record_id,
                    "reason": "missing_ideal_answer",
                }
            )

            continue

        # ----------------------------------------------------
        # Missing generated answer
        # ----------------------------------------------------

        if not generated_answer:
            skipped += 1

            skipped_records.append(
                {
                    "record_id": record_id,
                    "reason": "missing_generated_answer",
                }
            )

            continue

        ideal_answer = str(
            ideal_answer
        ).strip()

        generated_answer = str(
            generated_answer
        ).strip()

        if not ideal_answer or not generated_answer:
            skipped += 1

            skipped_records.append(
                {
                    "record_id": record_id,
                    "reason": "empty_answer",
                }
            )

            continue

        # ----------------------------------------------------
        # E5 embeddings
        # ----------------------------------------------------

        texts = [
            f"query: {ideal_answer}",
            f"passage: {generated_answer}",
        ]

        embeddings = embedding_model.encode(
            texts,
            normalize_embeddings=True,
        )

        ideal_embedding = embeddings[0]
        generated_embedding = embeddings[1]

        similarity = float(
            np.dot(
                ideal_embedding,
                generated_embedding,
            )
        )

        # Numerical safety
        similarity = max(
            -1.0,
            min(1.0, similarity),
        )

        similarities.append(similarity)
        checked += 1

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    if similarities:
        mean_similarity = float(
            np.mean(similarities)
        )

        min_similarity = float(
            np.min(similarities)
        )

        max_similarity = float(
            np.max(similarities)
        )
    else:
        mean_similarity = 0.0
        min_similarity = 0.0
        max_similarity = 0.0

    print(
        f"Ideal Answer checked: {checked}"
    )

    print(
        f"Ideal Answer skipped: {skipped}"
    )

    return {
        "Ideal_Answer_Similarity_Mean":
            mean_similarity,

        "Ideal_Answer_Similarity_Min":
            min_similarity,

        "Ideal_Answer_Similarity_Max":
            max_similarity,

        "Ideal_Answer_Queries_Checked":
            checked,

        "Ideal_Answer_Queries_Skipped":
            skipped,
    }


# ============================================================
# Citation Accuracy
# ============================================================

def extract_citations(text):
    """
    Extract explicit Persian citations such as:

        ماده ۲
        بند ۶
        تبصره ۳
    """

    if not text:
        return []

    pattern = (
        r"(?:ماده|بند|تبصره)"
        r"\s+"
        r"(\d+|[۰-۹]+)"
    )

    return re.findall(
        pattern,
        text,
    )


def compute_citation_accuracy(main_results):
    total_checked = 0
    correct = 0
    skipped_no_metadata = 0

    for result in main_results:

        answer = result.get(
            "answer",
            "",
        )

        citations = extract_citations(
            answer
        )

        if not citations:
            continue

        metadata = result.get(
            "retrieved_chunk_metadata",
            [],
        )

        if not metadata:
            skipped_no_metadata += len(
                citations
            )
            continue

        metadata_text = " ".join(
            str(item)
            for item in metadata
        )

        metadata_text = (
            normalize_persian_digits(
                metadata_text
            )
        )

        for citation in citations:

            total_checked += 1

            citation = (
                normalize_persian_digits(
                    citation
                )
            )

            if citation in metadata_text:
                correct += 1

    return {
        "Citation_Accuracy": (
            correct / total_checked
            if total_checked
            else 0.0
        ),
        "Total_Citations_Checked":
            total_checked,
        "Citations_Skipped_No_Metadata":
            skipped_no_metadata,
    }


# ============================================================
# Abstention Metrics
# ============================================================

def compute_abstention_metrics(
    abstention_results
):
    total = len(abstention_results)

    correctly_abstained = sum(
        1
        for result in abstention_results
        if result.get("correctly_abstained")
    )

    intent_misroutes = sum(
        1
        for result in abstention_results
        if result.get("intent_misroute")
    )

    return {
        "Abstention_Accuracy": (
            correctly_abstained / total
            if total
            else 0.0
        ),
        "False_Answer_Rate": (
            (total - correctly_abstained)
            / total
            if total
            else 0.0
        ),
        "Intent_Misroute_Rate": (
            intent_misroutes / total
            if total
            else 0.0
        ),
    }


# ============================================================
# False Abstention Rate
# ============================================================

def compute_false_abstention_rate(
    main_results
):
    total = 0
    false_abstentions = 0

    not_found_phrase = (
        Config.NOT_FOUND_PHRASE
    )

    for result in main_results:

        if not result.get(
            "expected_chunk_id"
        ):
            continue

        total += 1

        answer = str(
            result.get("answer", "")
        ).strip()

        if not_found_phrase in answer:
            false_abstentions += 1

    return (
        false_abstentions / total
        if total
        else 0.0
    )


# ============================================================
# Latency
# ============================================================

def compute_latency_metrics(
    main_results
):
    latencies = []

    for result in main_results:

        value = result.get(
            "processing_time"
        )

        if value is None:
            continue

        try:
            latencies.append(
                float(value)
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

    if not latencies:
        return {
            "Latency_Mean": 0.0,
            "Latency_p50": 0.0,
            "Latency_p95": 0.0,
        }

    return {
        "Latency_Mean":
            float(np.mean(latencies)),

        "Latency_p50":
            float(np.percentile(
                latencies,
                50,
            )),

        "Latency_p95":
            float(np.percentile(
                latencies,
                95,
            )),
    }


# ============================================================
# Access Violation
# ============================================================

def compute_access_violation_rate(
    abstention_results
):
    values = [
        result.get("access_violation")
        for result in abstention_results
        if "access_violation" in result
    ]

    if not values:
        return 0.0

    return float(
        np.mean(
            [
                bool(value)
                for value in values
            ]
        )
    )


# ============================================================
# Main
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Result model name.",
    )

    args = parser.parse_args()

    model_name = args.model

    result_path = get_result_file(
        model_name
    )

    if not result_path.exists():
        raise FileNotFoundError(
            f"Result file not found:\n"
            f"{result_path}"
        )

    gold_path = (
        EVAL_DIR
        / "gold_dataset_main_reduced.json"
    )

    abstention_path = (
        EVAL_DIR
        / "gold_dataset_abstention.json"
    )

    if not gold_path.exists():
        raise FileNotFoundError(
            f"Gold dataset not found:\n"
            f"{gold_path}"
        )

    if not abstention_path.exists():
        raise FileNotFoundError(
            f"Abstention dataset not found:\n"
            f"{abstention_path}"
        )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    result_data = load_json(
        result_path
    )

    gold_data = load_json(
        gold_path
    )

    abstention_data = load_json(
        abstention_path
    )

    main_results = result_data.get(
        "main",
        [],
    )

    abstention_results = result_data.get(
        "abstention",
        [],
    )

    # --------------------------------------------------------
    # Basic information
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("RAG EVALUATION")
    print("=" * 60)

    print(
        f"Model: {model_name}"
    )

    print(
        f"Main results: {len(main_results)}"
    )

    print(
        f"Gold main records: {len(gold_data)}"
    )

    print(
        f"Abstention results: "
        f"{len(abstention_results)}"
    )

    print(
        f"Gold abstention records: "
        f"{len(abstention_data)}"
    )

    # --------------------------------------------------------
    # Verify result structure
    # --------------------------------------------------------

    if main_results:

        first = main_results[0]

        print("\nFirst result record:")
        print(
            f"  record_id: "
            f"{first.get('record_id')}"
        )

        print(
            f"  has ideal_answer: "
            f"{bool(first.get('ideal_answer'))}"
        )

        print(
            f"  has generated answer: "
            f"{bool(first.get('answer'))}"
        )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    metrics = {
        "model": model_name,

        "total_main_queries":
            len(main_results),

        "total_abstention_queries":
            len(abstention_results),

        "errors_count":
            sum(
                1
                for result in main_results
                if result.get("error")
            ),
    }

    # Retrieval
    metrics.update(
        compute_retrieval_metrics(
            main_results
        )
    )

    # Generation
    metrics.update(
        compute_generation_metrics(
            main_results
        )
    )

    # Ideal Answer
    metrics.update(
        compute_ideal_answer_similarity(
            main_results
        )
    )

    # Citation
    metrics.update(
        compute_citation_accuracy(
            main_results
        )
    )

    # Abstention
    metrics.update(
        compute_abstention_metrics(
            abstention_results
        )
    )

    # False abstention
    metrics[
        "False_Abstention_Rate"
    ] = compute_false_abstention_rate(
        main_results
    )

    # Latency
    metrics.update(
        compute_latency_metrics(
            main_results
        )
    )

    # Access
    metrics[
        "Access_Violation_Rate"
    ] = compute_access_violation_rate(
        abstention_results
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        REPORTS_DIR
        / "metrics_comparison.json"
    )

    txt_path = (
        REPORTS_DIR
        / "metrics_comparison.txt"
    )

    with open(
        json_path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            [metrics],
            f,
            ensure_ascii=False,
            indent=2,
        )

    with open(
        txt_path,
        "w",
        encoding="utf-8",
    ) as f:
        for key, value in metrics.items():
            f.write(
                f"{key}: {value}\n"
            )

    # --------------------------------------------------------
    # Print
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("FINAL METRICS")
    print("=" * 60)

    for key, value in metrics.items():
        print(
            f"{key}: {value}"
        )

    print("=" * 60)

    print(
        f"\nJSON saved to:\n{json_path}"
    )

    print(
        f"TXT saved to:\n{txt_path}"
    )


if __name__ == "__main__":
    main()