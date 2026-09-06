"""
embed_and_index.py
ورودی:  ./dataNormalized/dataset_normalized.json
خروجی:  ./vectorStore/  (فایل‌های وکتور + متادیتا، آماده برای بارگذاری در وکتور دیتابیس)

هر چانک یکتا (بر اساس chunk_id) دقیقاً یک‌بار embed می‌شود (نوع "content").
هر Query نمونه، جدا و اضافه بر آن embed می‌شود (نوع "query_alias") و به همان chunk_id لینک می‌شود.
"""
import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer

IN_FILE = os.path.join("dataNormalized", "dataset_normalized.json")
OUT_DIR = "vectorStore"
MODEL_NAME = "intfloat/multilingual-e5-base"

# مدل‌های خانواده‌ی e5 طراحی شده‌اند که با پیشوند "query: " یا "passage: " کار کنند
# این تمایز دقیقاً با نقش content/query_alias ما هم‌خوانی دارد
PASSAGE_PREFIX = "passage: "
QUERY_PREFIX = "query: "


def build_records(data):
    """از روی دیتای نرمال‌شده، رکوردهای content (یکتا بر اساس chunk_id) و query_alias را می‌سازد."""
    content_records = {}   # chunk_id -> record
    query_records = []     # لیست جدا، چون چند سوال می‌توانند به یک chunk_id اشاره کنند

    for r in data:
        cid = r["metadata"]["chunk_id"]
        if cid not in content_records:
            content_records[cid] = {
                "id": f"{cid}__content",
                "chunk_id": cid,
                "type": "content",
                "text_for_embedding": PASSAGE_PREFIX + r["context_chunk_dense"],
                "text_raw": r["context_chunk_raw"],
                "metadata": r["metadata"],
            }
        query_records.append({
            "id": f"{cid}__query__{r['id']}",
            "chunk_id": cid,
            "type": "query_alias",
            "text_for_embedding": QUERY_PREFIX + r["query_dense"],
            "text_raw": r["query_raw"],
            "metadata": r["metadata"],
        })

    return list(content_records.values()) + query_records


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(IN_FILE, encoding="utf-8") as f:
        data = json.load(f)

    records = build_records(data)
    print(f"{len(records)} رکورد آماده‌ی embedding "
          f"({sum(1 for r in records if r['type']=='content')} content + "
          f"{sum(1 for r in records if r['type']=='query_alias')} query_alias)")

    model = SentenceTransformer(MODEL_NAME)
    texts = [r["text_for_embedding"] for r in records]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

    # ذخیره‌ی وکتورها و متادیتا جدا از هم (فرمت رایج برای اکثر وکتور دیتابیس‌ها)
    np.save(os.path.join(OUT_DIR, "embeddings.npy"), embeddings)

    meta_out = [
        {
            "id": r["id"],
            "chunk_id": r["chunk_id"],
            "type": r["type"],
            "text_raw": r["text_raw"],
            "metadata": r["metadata"],
        }
        for r in records
    ]
    with open(os.path.join(OUT_DIR, "vectors_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta_out, f, ensure_ascii=False, indent=2)

    print(f"ذخیره شد -> {OUT_DIR}/embeddings.npy  (shape: {embeddings.shape})")
    print(f"ذخیره شد -> {OUT_DIR}/vectors_metadata.json")


if __name__ == "__main__":
    main()
