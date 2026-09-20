from back.rag.hybrid_retriever_langchain import HybridRetriever


retriever = HybridRetriever(
    chroma_path="chromaStore",
    collection_name="legal_docs",
    normalized_data_path="dataNormalized/dataset_normalized.json",
    registry_path="data/documents_registry.json",
    embedding_model_name="intfloat/multilingual-e5-base",
)
results = retriever.retrieve("تعریف قانونی مأموریت یک دستگاه دولتی چیه؟", k=10, access_level=3)
for r in results:
    print(r['chunk_id'], r['metadata'].get('locator'), r['fused_score'])

TOP_K = 3  # همان مقدار فعلی production - عمداً همین را تست می‌کنیم، نه عدد دیگر


def print_results(title, results):
    print(f"\n{'=' * 70}")
    print(title)
    print("=" * 70)
    for i, r in enumerate(results, 1):
        print(
            f"{i}. {r['chunk_id']} | score={r.get('fused_score'):.5f} | "
            f"locator={r['metadata'].get('locator')} | doc={r['metadata'].get('document_id')}"
        )
        print(f"   {r['content'][:180]}")


# هر مورد: (کوئری، توضیح این‌که چه چیزی را تست می‌کند، chunk_id درستی که انتظار داریم دیده شود یا None)
test_cases = [
    (
        "اگه بیمارستان دولتی طرف قرارداد بیمه نباشه چیکار باید کرد؟",
        "پارافریز کامل (کلمات کلیدی متفاوت از سؤال اصلی دیتاست) - تست واقعی توانایی Dense",
        "CHUNK-8c64be92ed",
    ),
    (
        "تعریف قانونی مأموریت یک دستگاه دولتی چیه؟",
        "پارافریز سؤال مفهومی درباره‌ی تعریف - کلمات کلیدی 'مأموریت'، 'دستگاه' مشترک ولی ساختار جمله فرق دارد",
        "CHUNK-4d2b7c5dca",
    ),
    (
        "آیا میشه به مدیرعامل بیشتر از سقف تعیین‌شده حقوق داد؟",
        "پارافریز با نفی/سؤال بله-خیر به‌جای بیان مستقیم؛ تست اینکه آیا مدل معنای 'ممنوعیت' را می‌فهمد",
        "CHUNK-55f8fb657b",
    ),
    (
        "برای عینک زدن بیمه چقدر پول میده؟",
        "کلمات محاوره‌ای و غیررسمی (نه زبان حقوقی دیتاست) - تست فاصله‌ی سبک نوشتاری",
        "CHUNK-fb97f7db91",
    ),
    (
        "شرایط استفاده از بیمه تکمیلی برای پیمانکارهای غیرمستقیم چیه؟",
        "اصطلاح تخصصی نادر ('پیمانکار غیرمستقیم' نزدیک به 'نیروهای غیرمستقیم') - تست تأثیر _has_rare_term",
        "CHUNK-be25094f70",
    ),
    (
        "آیا کارخانه‌های خصوصی هم مشمول این بخشنامه‌ها هستند؟",
        "کاملاً خارج از دامنه‌ی دیتاست (این اسناد مخصوص دستگاه دولتی/شرکت‌های وابسته‌اند، نه کارخانه‌ی خصوصی معمولی) - "
        "تست رفتار وقتی جواب واقعی وجود ندارد",
        None,
    ),
    (
        "توی این بخشنامه‌ها اصلا حرفی از هوش مصنوعی زده شده؟",
        "کاملاً بی‌ربط به کل کورپوس - تست اینکه امتیازها همه پایین و نزدیک به هم می‌مانند (نه یک false positive مطمئن)",
        None,
    ),
]

for q, why, expected in test_cases:
    print(f"\nQUERY: {q}")
    print(f"هدف تست: {why}")
    if expected:
        print(f"chunk مورد انتظار: {expected}")

    tokens = retriever.query_processor.tokenize_keyword(q)
    alpha = retriever.estimate_alpha(q, tokens)
    print("has_structural_reference:", retriever._has_structural_reference(q))
    print("alpha:", alpha)

    results = retriever.retrieve(q, k=TOP_K, access_level=3)
    print_results("RESULTS", results)

    if expected:
        found = any(r["chunk_id"] == expected for r in results)
        print(f"\n>>> نتیجه: {'✅ پیدا شد' if found else '❌ پیدا نشد'}")



        