"""
embed_and_index.py
ورودی:  ./dataNormalized/dataset_normalized.json  +  ./data/documents_registry.json
خروجی:  ./vectorStore/  (فایل‌های وکتور + متادیتا، آماده برای بارگذاری در وکتور دیتابیس)

هر چانک یکتا (بر اساس chunk_id) دقیقاً یک‌بار embed می‌شود (نوع "content").
هر Query نمونه، جدا و اضافه بر آن embed می‌شود (نوع "query_alias") و به همان chunk_id لینک می‌شود.

نکته‌ی مهم (اصلاح‌شده): متن رکوردهای "content" قبل از embed شدن با locator/sub_reference/section/
document_name غنی‌سازی می‌شود - دقیقاً هم‌راستا با enrichment سمت BM25 در HybridRetriever.
بدون این کار، وقتی کاربر می‌پرسد "ماده ۲ بند ۶ چی میگه؟"، عبارت "ماده ۲" و "بند ۶" در هیچ‌کدام
از وکتورهای content وجود نداشت (چون متن اصلی چانک هرگز شماره‌ی ماده/بند را ذکر نمی‌کند)، پس
جستجوی دنس اصولاً امکان پیدا کردن آن را نداشت - نه اینکه فقط امتیاز پایینی می‌گرفت.

رکوردهای "query_alias" enrich نمی‌شوند: این‌ها نمونه‌سوال‌های دیتاست هستند و قرار است با
سوال زنده‌ی کاربر (که هم عیناً enrich نشده) مقایسه شوند، پس باید متقارن با embed_query در
HybridRetriever بمانند.
"""
import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer

IN_FILE = os.path.join("dataNormalized", "dataset_normalized.json")
REGISTRY_FILE = os.path.join("data", "documents_registry.json")
OUT_DIR = "vectorStore"
MODEL_NAME = "intfloat/multilingual-e5-base"

# مدل‌های خانواده‌ی e5 طراحی شده‌اند که با پیشوند "query: " یا "passage: " کار کنند
# این تمایز دقیقاً با نقش content/query_alias ما هم‌خوانی دارد
PASSAGE_PREFIX = "passage: "
QUERY_PREFIX = "query: "


def load_document_names(registry_path):
    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)
    return {d["document_id"]: d.get("document_name", "بدون عنوان") for d in registry}


def build_enrichment_prefix(meta, document_name):
    """
    همان منطق enrichment سمت BM25 در HybridRetriever._enrichment، به‌علاوه‌ی sub_reference
    که آنجا هم فعلاً جا افتاده - باید در یک commit جدا آنجا هم اضافه شود تا دو مسیر هم‌راستا بمانند.
    """
    parts = [
        meta.get("locator"),
        meta.get("sub_reference"),
        meta.get("section"),
        document_name,
    ]
    return " ".join(p for p in parts if p)


def build_records(data, document_name_by_doc):
    """از روی دیتای نرمال‌شده، رکوردهای content (یکتا بر اساس chunk_id) و query_alias را می‌سازد."""
    content_records = {}   # chunk_id -> record
    query_records = []     # لیست جدا، چون چند سوال می‌توانند به یک chunk_id اشاره کنند

    for r in data:
        meta = r["metadata"]
        cid = meta["chunk_id"]
        if cid not in content_records:
            document_name = document_name_by_doc.get(meta.get("document_id"), "بدون عنوان")
            enrichment = build_enrichment_prefix(meta, document_name)
            dense_text = r["context_chunk_dense"]
            enriched_dense_text = f"{enrichment} {dense_text}".strip() if enrichment else dense_text

            content_records[cid] = {
                "id": f"{cid}__content",
                "chunk_id": cid,
                "type": "content",
                "text_for_embedding": PASSAGE_PREFIX + enriched_dense_text,
                "text_raw": r["context_chunk_raw"],
                "metadata": meta,
            }
        query_records.append({
            "id": f"{cid}__query__{r['id']}",
            "chunk_id": cid,
            "type": "query_alias",
            "text_for_embedding": QUERY_PREFIX + r["query_dense"],
            "text_raw": r["query_raw"],
            "metadata": meta,
        })

    return list(content_records.values()) + query_records


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(IN_FILE, encoding="utf-8") as f:
        data = json.load(f)

    document_name_by_doc = load_document_names(REGISTRY_FILE)

    records = build_records(data, document_name_by_doc)
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