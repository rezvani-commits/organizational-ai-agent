"""
تست مستقیم retrieval، بدون رد شدن از کل گراف (بدون LLM، بدون validator).
هدف: دیدن اینکه آیا چانک مربوط به یک سؤال خاص اصلاً retrieve می‌شه یا نه،
و fused_score‌ش چقدره نسبت به SIMILARITY_THRESHOLD.

اجرا (از ریشه‌ی پروژه):
    python debug_retrieval.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from back.config import Config
from back.rag.hybrid_retriever_langchain import HybridRetriever

QUERY = "اگه کارگر شیفت شب کار کنه، میشه بهش اضافه‌کاری هم داد؟"
ACCESS_LEVEL = 3  # همون سطحی که باهاش تست کردی
TARGET_CHUNK_ID = "CHUNK-db947f7282"  # چانکی که می‌دونیم جواب درسته

print("در حال بارگذاری retriever (ممکنه چند ثانیه طول بکشه)...")
retriever = HybridRetriever(
    chroma_path=Config.CHROMA_PATH,
    collection_name=Config.COLLECTION_NAME,
    normalized_data_path=Config.NORMALIZED_DATA_PATH,
    registry_path=Config.REGISTRY_PATH,
    embedding_model_name=Config.EMBEDDING_MODEL,
)

print(f"\nسؤال: {QUERY}")
print(f"آستانه‌ی SIMILARITY_THRESHOLD فعلی: {Config.SIMILARITY_THRESHOLD}\n")

results = retriever.retrieve(query=QUERY, k=10, access_level=ACCESS_LEVEL)

if not results:
    print("❌ هیچ نتیجه‌ای برنگشت (حتی با k=10)!")
else:
    print(f"{len(results)} نتیجه برگشت:\n")
    for i, doc in enumerate(results, 1):
        marker = " <== چانک هدف" if doc["chunk_id"] == TARGET_CHUNK_ID else ""
        above = "✅ بالای threshold" if doc["fused_score"] >= Config.SIMILARITY_THRESHOLD else "❌ زیر threshold"
        print(f"{i}. chunk_id={doc['chunk_id']}  fused_score={doc['fused_score']:.5f}  ({above}){marker}")
        print(f"   metadata.locator={doc['metadata'].get('locator')}  document_id={doc['metadata'].get('document_id')}")
        print(f"   content: {doc['content'][:100]}...")
        print()

    found = any(d["chunk_id"] == TARGET_CHUNK_ID for d in results)
    if not found:
        print(f"⚠️ چانک هدف ({TARGET_CHUNK_ID}) اصلاً تو تاپ ۱۰ نتیجه نبود!")