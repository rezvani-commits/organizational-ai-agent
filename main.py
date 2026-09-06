import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from back.config import Config
from back.rag_graph import RAGGraph


def main():
    Config.validate()

    print("🚀 در حال راه‌اندازی RAGGraph (retrieval هیبرید از chromaStore)...")
    # نکته: دیگه نیازی به VectorStoreManager/data_loader یا ایندکس‌سازی دستی
    # نیست - HybridRetriever خودش مستقیماً از chromaStore + dataNormalized +
    # documents_registry.json تغذیه می‌شه (باید از قبل با اسکریپت ایندکس‌سازی ساخته شده باشن).
    rag = RAGGraph()

    # TODO: این سؤال‌ها نمونه‌ان - با یک سؤال واقعی از دیتاست اسناد حقوقی/سازمانی خودتون جایگزین کنید
    test_query = "چه شرایطی برای فسخ قرارداد پیش‌بینی شده است؟"
    print(f"\n❓ Query: {test_query}")

    result = rag.run(test_query, session_id="test_session")
    print("\n📝 Result:")
    print(result["answer"])
    print(f"\n⏱️ Time: {result['processing_time']:.2f}s")

    # تست follow-up question برای بررسی dialogue manager
    followup_query = "و در مورد فسخ یک‌طرفه چطور؟"
    print(f"\n❓ Follow-up Query: {followup_query}")

    result2 = rag.run(followup_query, session_id="test_session")
    print(f"🔄 Rewritten to: {result2['standalone_query']}  (was_rewritten={result2['was_rewritten']})")
    print("\n📝 Result:")
    print(result2["answer"])
    print(f"\n⏱️ Time: {result2['processing_time']:.2f}s")


if __name__ == "__main__":
    main()