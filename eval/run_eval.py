import argparse
import json
import time
import uuid
from pathlib import Path

from back.config import Config
from back.rag_graph import RAGGraph

EVAL_DIR = Path(__file__).parent
MAIN_DATASET_PATH = EVAL_DIR / "gold_dataset_main_reduced.json"
ABSTENTION_DATASET_PATH = EVAL_DIR / "gold_dataset_abstention.json"
RESULTS_DIR = EVAL_DIR / "results"

FULL_ACCESS_LEVEL = 3

MAX_CONSECUTIVE_QUOTA_ERRORS = 3

QUOTA_ERROR_KEYWORDS = [
    "rate limit", "ratelimit", "429", "quota", "insufficient_quota",
    "too many requests", "resource_exhausted", "exceeded",
]


def looks_like_quota_error(error_message: str) -> bool:
    if not error_message:
        return False
    lowered = error_message.lower()
    return any(kw in lowered for kw in QUOTA_ERROR_KEYWORDS)


def load_datasets(limit: int = None):
    with open(MAIN_DATASET_PATH, encoding="utf-8") as f:
        main_data = json.load(f)
    with open(ABSTENTION_DATASET_PATH, encoding="utf-8") as f:
        abstention_data = json.load(f)
    if limit:
        main_data = main_data[:limit]
        abstention_data = abstention_data[:limit]
    return main_data, abstention_data


def load_existing_results(out_path: Path):
    if not out_path.exists():
        return None
    with open(out_path, encoding="utf-8") as f:
        return json.load(f)


def save_results(results: dict, out_path: Path):
    RESULTS_DIR.mkdir(exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def run_main_item(rag: RAGGraph, item: dict) -> dict:
    session_id = f"eval-{uuid.uuid4()}"
    start = time.time()
    error = None
    try:
        result = rag.run(
            query=item["query"],
            session_id=session_id,
            user_access_level=FULL_ACCESS_LEVEL,
        )
    except Exception as e:
        result = {}
        error = f"{type(e).__name__}: {e}"
    elapsed = time.time() - start

    retrieved_chunk_ids = [
        doc.get("chunk_id") for doc in result.get("retrieved_docs", []) or []
    ]

    retrieved_chunk_metadata = [
        {
            "chunk_id": doc.get("chunk_id"),
            "locator": (doc.get("metadata") or {}).get("locator"),
            "sub_reference": (doc.get("metadata") or {}).get("sub_reference"),
            "document_id": (doc.get("metadata") or {}).get("document_id"),
        }
        for doc in result.get("retrieved_docs", []) or []
    ]

    return {
        "record_id": item["id"],
        "dataset": "main",
        "query": item["query"],
        "expected_chunk_id": item.get("metadata", {}).get("chunk_id"),
        "document_id": item.get("metadata", {}).get("document_id"),
        "ideal_answer": item.get("ideal_answer"),
        "retrieved_chunk_ids": retrieved_chunk_ids,
        "retrieved_chunk_metadata": retrieved_chunk_metadata,
        "answer": result.get("answer"),
        "intent": result.get("intent"),
        "validation_result": result.get("validation_result"),
        "is_satisfied": result.get("is_satisfied"),
        "retry_count": result.get("retry_count"),
        "processing_time": result.get("processing_time", round(elapsed, 3)),
        "node_timings": result.get("node_timings"),
        "error": error,
    }


def run_abstention_item(rag: RAGGraph, item: dict) -> dict:
    session_id = f"eval-{uuid.uuid4()}"
    access_level = item.get("test_access_level")
    start = time.time()
    error = None
    try:
        result = rag.run(
            query=item["query"],
            session_id=session_id,
            user_access_level=access_level,
        )
    except Exception as e:
        result = {}
        error = f"{type(e).__name__}: {e}"
    elapsed = time.time() - start

    answer = (result.get("answer") or "").strip()
    check_mode = item.get("check_mode", "exact")
    if check_mode == "contains":
        
        correctly_abstained = Config.NOT_FOUND_PHRASE.strip() in answer
    else:
        correctly_abstained = answer == Config.NOT_FOUND_PHRASE.strip()

    intent = result.get("intent")
    fast_path_intents = {"greeting", "calendar", "calculator"}
    intent_misroute = (not correctly_abstained) and (intent in fast_path_intents)

    return {
        "record_id": item["id"],
        "dataset": "abstention",
        "abstention_type": item["abstention_type"],
        "query": item["query"],
        "test_access_level": access_level,
        "answer": result.get("answer"),
        "intent": intent,
        "check_mode": check_mode,
        "correctly_abstained": correctly_abstained,
        "intent_misroute": intent_misroute,
        "processing_time": result.get("processing_time", round(elapsed, 3)),
        "error": error,
    }


def run_all(model_name: str, router_model_name: str = None, limit: int = None, resume: bool = False):
    router_model_name = router_model_name or model_name

    Config.LLM_MODEL = model_name
    Config.ROUTER_LLM_MODEL = router_model_name

    safe_name = model_name.replace("/", "_")
    out_path = RESULTS_DIR / f"{safe_name}.json"

    main_data, abstention_data = load_datasets(limit=limit)

    done_main_ids = set()
    done_abstention_ids = set()
    results = {
        "model": model_name,
        "router_model": router_model_name,
        "judge_model": Config.VALIDATOR_LLM_MODEL,
        "main": [],
        "abstention": [],
    }

    if resume:
        existing = load_existing_results(out_path)
        if existing:
            for r in existing.get("main", []):
                if not r.get("error"):
                    done_main_ids.add(r["record_id"])
                    results["main"].append(r)
            for r in existing.get("abstention", []):
                if not r.get("error"):
                    done_abstention_ids.add(r["record_id"])
                    results["abstention"].append(r)
            print(f"[resume] {len(done_main_ids)} سؤال اصلی و {len(done_abstention_ids)} سؤال abstention قبلاً موفق بودن؛ رد می‌شن.\n")

    print(f"در حال ساخت RAGGraph با مدل پاسخ‌دهی={model_name} | روتینگ={router_model_name}")
    print(f"مدل Judge ثابت: {Config.VALIDATOR_LLM_MODEL}\n")

    rag = RAGGraph()

    consecutive_quota_errors = 0
    stopped_early = False

    print(f"[۱/۲] اجرای دیتاست اصلی ({len(main_data)} سؤال، {len(done_main_ids)} تا از قبل انجام‌شده) ...")
    for i, item in enumerate(main_data, 1):
        if item["id"] in done_main_ids:
            continue

        r = run_main_item(rag, item)
        results["main"].append(r)
        save_results(results, out_path)  

        if r.get("error") and looks_like_quota_error(r["error"]):
            consecutive_quota_errors += 1
            print(f"    ⚠️  خطای شبیه quota/rate-limit ({consecutive_quota_errors}/{MAX_CONSECUTIVE_QUOTA_ERRORS}): {r['error'][:150]}")
            if consecutive_quota_errors >= MAX_CONSECUTIVE_QUOTA_ERRORS:
                print("\n🛑 به نظر می‌رسه سقف استفاده تموم شده. اجرا متوقف شد تا quota هدر نره.")
                print(f"   نتایج تا همین‌جا ذخیره شدن -> {out_path}")
                print(f"   بعداً با همین دستور + --resume ادامه بده.")
                stopped_early = True
                break
        else:
            consecutive_quota_errors = 0  

        if i % 10 == 0 or i == len(main_data):
            print(f"    {i}/{len(main_data)}")

    if not stopped_early:
        print(f"\n[۲/۲] اجرای دیتاست abstention ({len(abstention_data)} سؤال، {len(done_abstention_ids)} تا از قبل انجام‌شده) ...")
        for i, item in enumerate(abstention_data, 1):
            if item["id"] in done_abstention_ids:
                continue

            r = run_abstention_item(rag, item)
            results["abstention"].append(r)
            save_results(results, out_path)

            if r.get("error") and looks_like_quota_error(r["error"]):
                consecutive_quota_errors += 1
                print(f"    ⚠️  خطای شبیه quota/rate-limit ({consecutive_quota_errors}/{MAX_CONSECUTIVE_QUOTA_ERRORS}): {r['error'][:150]}")
                if consecutive_quota_errors >= MAX_CONSECUTIVE_QUOTA_ERRORS:
                    print("\n🛑 به نظر می‌رسه سقف استفاده تموم شده. اجرا متوقف شد.")
                    print(f"   نتایج تا همین‌جا ذخیره شدن -> {out_path}")
                    print(f"   بعداً با همین دستور + --resume ادامه بده.")
                    stopped_early = True
                    break
            else:
                consecutive_quota_errors = 0

            if i % 5 == 0 or i == len(abstention_data):
                print(f"    {i}/{len(abstention_data)}")

    save_results(results, out_path)

    if stopped_early:
        print(f"\n⏸️  اجرا نصفه‌کاره متوقف شد. پیشرفت: {len(results['main'])}/{len(main_data)} اصلی، {len(results['abstention'])}/{len(abstention_data)} abstention.")
    else:
        print(f"\n✅ اجرا کامل شد و ذخیره شد -> {out_path}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="اسم دقیق مدل (پاسخ‌دهی)")
    parser.add_argument("--router-model", default=None, help="اگه جدا از --model باشه؛ پیش‌فرض همون model")
    parser.add_argument("--limit", type=int, default=None, help="فقط N رکورد اول هر دیتاست (برای تست سریع)")
    parser.add_argument("--resume", action="store_true", help="ادامه از نتایج قبلی همین مدل، بدون تکرار سؤالات موفق")
    args = parser.parse_args()

    run_all(args.model, args.router_model, args.limit, args.resume)