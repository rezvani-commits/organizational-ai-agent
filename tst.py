from back.config import Config
from back.rag.hybrid_retriever_langchain import HybridRetriever

r = HybridRetriever(
    chroma_path=Config.CHROMA_PATH,
    collection_name=Config.COLLECTION_NAME,
    normalized_data_path=Config.NORMALIZED_DATA_PATH,
    registry_path=Config.REGISTRY_PATH,
    embedding_model_name=Config.EMBEDDING_MODEL,
)

query = "تفاوت خدمت و وظیفه در دستگاه‌های اجرایی چیه؟"
docs = r.retrieve(query, k=5, access_level=3)

print("=" * 60)
print(f"query: {query}")
print(f"found: {len(docs)}")
print("=" * 60)

for d in docs:
    print("-" * 40)
    print(f"chunk_id: {d['chunk_id']}")
    print(f"score:    {d.get('fused_score')}")
    print(f"access:   {d['metadata'].get('access_level')}")
    print(f"doc_id:   {d['metadata'].get('document_id')}")
    print(f"content:  {d['content'][:120]}")