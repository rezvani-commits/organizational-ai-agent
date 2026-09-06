# """
# test_retriever.py
# یه تست دستی سریع - چند تا سوال واقعی از Golden QA رو می‌گیره، جواب می‌بینه چه چانکی برگردونده،
# و مقایسه می‌کنه با locator/document_id واقعی که باید بود.
# """
# from back.hybrid_retriever_langchain import HybridRetriever
# import json

# # چند نمونه سوال واقعی از dataset_clean.json (خودت جایگزین کن با سوالات خودت)
# TEST_QUERIES = [
#     "مدت اعتبار شناسنامه خدمات چقدره؟",
#     "ماده ۲ بند ۵ چی میگه؟",
#     "شرایط افزایش حقوق و مزایای کارکنان چیست؟",
# ]

# hr = HybridRetriever(dynamic_alpha=True)

# for q in TEST_QUERIES:
#     print("="*60)
#     print("سوال:", q)
#     results = hr.retrieve(q, k=3, access_level=3)  # سطح ۳ یعنی همه‌چی قابل دیدنه، برای تست
#     for i, r in enumerate(results, 1):
#         print(f"  [{i}] score={r['fused_score']:.4f} | alpha={r['dense_weight_used']} | "
#               f"doc={r['metadata']['document_id']} | locator={r['metadata']['locator']}")
#         print(f"      متن: {r['content'][:100]}...")
#     print()