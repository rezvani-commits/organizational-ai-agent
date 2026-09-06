"""
build_bm25.py
ورودی:  ./dataNormalized/dataset_normalized.json
خروجی:  ./bm25Store/bm25_index.pkl   (شیء BM25 آماده‌ی جستجو + نگاشت به chunk_id)

فقط رکوردهای "content" (چانک یکتا) ایندکس می‌شوند - سوالات نمونه اینجا لازم نیست،
چون BM25 برخلاف دنس، برای تطبیق واژگانیِ سوال با متن سند طراحی شده، نه سوال با سوال.
"""
import json
import os
import pickle
from rank_bm25 import BM25Okapi

IN_FILE = os.path.join("dataNormalized", "dataset_normalized.json")
OUT_DIR = "bm25Store"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(IN_FILE, encoding="utf-8") as f:
        data = json.load(f)

    # فقط یک نسخه از هر chunk_id یکتا (هم‌راستا با content در embed_and_index.py)
    seen = set()
    corpus_tokens = []
    chunk_ids = []
    for r in data:
        cid = r["metadata"]["chunk_id"]
        if cid in seen:
            continue
        seen.add(cid)
        tokens = r["context_chunk_keyword"].split()  # از قبل توکنایز/لماتایز شده
        corpus_tokens.append(tokens)
        chunk_ids.append(cid)

    bm25 = BM25Okapi(corpus_tokens)

    with open(os.path.join(OUT_DIR, "bm25_index.pkl"), "wb") as f:
        pickle.dump({"bm25": bm25, "chunk_ids": chunk_ids}, f)

    print(f"{len(chunk_ids)} چانک یکتا در ایندکس BM25 -> {OUT_DIR}/bm25_index.pkl")


if __name__ == "__main__":
    main()
