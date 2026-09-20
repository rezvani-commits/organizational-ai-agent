
# import json
# import re
# from typing import Dict, List, Optional, Tuple

# from hazm import Lemmatizer, Normalizer, stopwords_list, word_tokenize
# from langchain_chroma import Chroma
# from langchain_community.retrievers import BM25Retriever
# from langchain_core.embeddings import Embeddings
# from sentence_transformers import SentenceTransformer


# class QueryProcessor:
#     """
#     پردازش سوال فارسی با Hazm.
#     - normalize_dense(): نرمال‌سازی سبک، برای embedding دنس (ساختار جمله دست‌نخورده می‌ماند).
#     - tokenize_keyword(): توکنایز + حذف stopword + لماتایز، برای BM25.
#     دقیقاً هم‌راستا با normalize_dataset.py که کورپوس با همان منطق آماده شده.
#     """

#     def __init__(self):
#         self.normalizer = Normalizer()
#         self.lemmatizer = Lemmatizer()
#         self.stopwords = set(stopwords_list())

#     def normalize_dense(self, text: str) -> str:
#         text = self.normalizer.normalize(text)
#         text = re.sub(r"\s+", " ", text).strip()
#         return text

#     def tokenize_keyword(self, text: str) -> List[str]:
#         text = self.normalizer.normalize(text)
#         tokens = word_tokenize(text)
#         result = []
#         for tok in tokens:
#             if tok in self.stopwords:
#                 continue
#             if re.fullmatch(r"[\W_]+", tok):
#                 continue
#             lemma = self.lemmatizer.lemmatize(tok).split("#")[0]
#             result.append(lemma)
#         return result


# class E5Embeddings(Embeddings):
#     """
#     Wrapper سازگار با اینترفیس Embeddings خودِ LangChain، برای مدل multilingual-e5-large.
#     مدل‌های خانواده‌ی e5 با پیشوند "passage: " برای متن سند و "query: " برای سوال آموزش
#     دیده‌اند - این تفکیک دقیقاً با تمایز embed_documents/embed_query در LangChain هماهنگ است.
#     """

#     def __init__(self, query_processor: QueryProcessor, model_name: str = "intfloat/multilingual-e5-base"):
#         self.query_processor = query_processor
#         self.model = SentenceTransformer(model_name)

#     def embed_documents(self, texts: List[str]) -> List[List[float]]:
#         prefixed = ["passage: " + self.query_processor.normalize_dense(t) for t in texts]
#         return self.model.encode(prefixed, normalize_embeddings=True).tolist()

#     def embed_query(self, text: str) -> List[float]:
#         prefixed = "query: " + self.query_processor.normalize_dense(text)
#         return self.model.encode([prefixed], normalize_embeddings=True)[0].tolist()


# class HybridRetriever:
#     """
#     ترکیب dense retrieval (LangChain + Chroma) با sparse retrieval (LangChain BM25Retriever) و fuse کردن نتایج.

#     نکات معماری:
#       - Chroma از طریق langchain_chroma.Chroma به همان چروماستوری که با build_chroma.py
#         ساختیم وصل می‌شود (وکتورهای موجود دوباره ساخته نمی‌شوند؛ embedding_function فقط
#         برای embed کردن سوال در لحظه‌ی جستجو استفاده می‌شود).
#       - BM25Retriever از LangChain، با preprocess_func=Hazm tokenizer خودمان ساخته می‌شود
#         تا دقیقاً هم‌راستا با bm25 قبلی (لماتایز + حذف stopword) باشد. چون این کلاس امکان
#         بارگذاری از فایل از پیش‌ساخته ندارد، هر بار از روی dataNormalized بازسازی می‌شود
#         (برای ۱۲۴ چانک این کار لحظه‌ای است، مشکلی ایجاد نمی‌کند).
#       - کلید یکتای هر نتیجه، chunk_id است (نه متن خام) - چون دو نوع رکورد در Chroma
#         داریم ("content" و "query_alias")؛ هر نتیجه‌ی دنس (چه از content چه از یک
#         query_alias مچ شود) به همان chunk_id resolve و به متن اصلی چانک نگاشت می‌شود.
#       - فیلتر access_level هم روی مسیر دنس (به‌صورت native، از طریق پارامتر filter در
#         Chroma) و هم روی مسیر اسپارس (دستی در پایتون، چون BM25Retriever فیلتر متادیتا
#         ندارد) اعمال می‌شود.
#       - وزن‌دهی دنس/BM25 پویاست: بر اساس شماره‌ی ماده/بند/تبصره یا تاریخ دقیق در سوال
#         (regex)، یا واژه‌ی کم‌تکرار/اصطلاح تخصصی (idf بالا، از خودِ vectorizer داخلی
#         BM25Retriever که یک شیء rank_bm25.BM25Okapi است).

#     توجه: langchain-community (که BM25Retriever از آن می‌آید) توسط خودِ LangChain
#     در حال کنار گذاشته شدن اعلام شده؛ برای این پروژه مشکلی ایجاد نمی‌کند، ولی اگر بعداً
#     هشدار deprecation آزاردهنده شد، جایگزین مستقیم "langchain-classic" یا نوشتن دستی
#     (نسخه‌ی قبلی بدون LangChain که قبلاً نوشتیم) در دسترس است.
#     """

#     _ARTICLE_PATTERN = re.compile(r"(ماده|بند|تبصره|بخش|فصل)\s*[۰-۹0-9]+")
#     _DATE_PATTERN = re.compile(r"[۰-۹0-9]{4}[/\-][۰-۹0-9]{1,2}[/\-][۰-۹0-9]{1,2}")

#     def __init__(
#         self,
#         chroma_path: str = "chromaStore",
#         collection_name: str = "legal_docs",
#         normalized_data_path: str = "dataNormalized/dataset_normalized.json",
#         registry_path: str = "data/documents_registry.json",
#         embedding_model_name: str = "intfloat/multilingual-e5-base",
#         fusion: str = "rrf",  # "rrf" یا "weighted"
#         alpha: float = 0.7,  # وزن پیش‌فرض دنس؛ فقط وقتی dynamic_alpha=False استفاده می‌شود
#         dynamic_alpha: bool = True,
#         rrf_k: int = 60,
#         rare_term_percentile: float = 0.85,
#     ):
#         self.query_processor = QueryProcessor()
#         self.fusion = fusion
#         self.alpha = alpha
#         self.dynamic_alpha = dynamic_alpha
#         self.rrf_k = rrf_k

#         # ---------- مسیر دنس: Chroma از طریق LangChain، روی وکتور دیتابیس موجود ----------
#         self.embeddings = E5Embeddings(self.query_processor, embedding_model_name)
#         self._vector_store = Chroma(
#             collection_name=collection_name,
#             persist_directory=chroma_path,
#             embedding_function=self.embeddings,
#         )

#         # ---------- رجیستری سند + لوکاپ نهایی chunk_id -> متن خام/متادیتا/access_level ----------
#         with open(registry_path, encoding="utf-8") as f:
#             registry = json.load(f)
#         access_level_by_doc = {d["document_id"]: d["access_level"] for d in registry}
#         document_name_by_doc = {d["document_id"]: d.get("document_name", "بدون عنوان") for d in registry}

#         with open(normalized_data_path, encoding="utf-8") as f:
#             normalized_data = json.load(f)

#         self._chunk_lookup: Dict[str, Dict] = {}
#         bm25_texts: List[str] = []
#         bm25_metadatas: List[Dict] = []
#         for r in normalized_data:
#             meta = r["metadata"]
#             cid = meta["chunk_id"]
#             if cid in self._chunk_lookup:
#                 continue
#             access_level = access_level_by_doc.get(meta.get("document_id"), 1)
#             meta["document_name"] = document_name_by_doc.get(meta.get("document_id"), "بدون عنوان")
#             self._chunk_lookup[cid] = {
#                 "content": r["context_chunk_raw"],
#                 "metadata": meta,
#                 "access_level": access_level,
#             }

#             enrichment_parts = [p for p in (meta.get("locator"), meta.get("section"), meta.get("document_name")) if p]        
#             enriched_text = " ".join(enrichment_parts + [r["context_chunk_raw"]])
#             bm25_texts.append(enriched_text)
#             bm25_metadatas.append({"chunk_id": cid})

#         # ---------- مسیر اسپارس: BM25Retriever از LangChain، با توکنایزر Hazm خودمان ----------
#         self._bm25_retriever = BM25Retriever.from_texts(
#             texts=bm25_texts,
#             metadatas=bm25_metadatas,
#             preprocess_func=self.query_processor.tokenize_keyword,
#         )
#         self._bm25_retriever.k = len(bm25_texts)  # امتیاز همه را می‌خواهیم، نه فقط ۴ تای پیش‌فرض

#         self._idf_threshold = self._compute_idf_threshold(rare_term_percentile)

#     # ---------- تشخیص نوع سوال برای وزن‌دهی پویا ----------

#     def _compute_idf_threshold(self, percentile: float) -> float:
#         idf = self._bm25_retriever.vectorizer.idf  # شیء rank_bm25.BM25Okapi زیرِ BM25Retriever
#         values = sorted(idf.values())
#         if not values:
#             return float("inf")
#         idx = min(int(len(values) * percentile), len(values) - 1)
#         return values[idx]

#     def _has_structural_reference(self, text: str) -> bool:
#         """آیا سوال به شماره‌ی ماده/بند/تبصره یا تاریخ دقیق اشاره دارد؟"""
#         return bool(self._ARTICLE_PATTERN.search(text) or self._DATE_PATTERN.search(text))
#     #واقا یوز لس بدرد نخور
#     def _has_rare_term(self, tokens: List[str]) -> bool:
#         """آیا سوال شامل واژه‌ی کم‌تکرار (idf بالا، یعنی اصطلاح تخصصی) است؟"""
#         idf = self._bm25_retriever.vectorizer.idf
#         return any(idf.get(t, 0) >= self._idf_threshold for t in tokens)

#     def estimate_alpha(self, query: str, query_tokens: List[str]) -> float:
#         """
#         وزن دنس (alpha) را برمی‌گرداند؛ وزن BM25 = 1 - alpha.
#         پیش‌فرض دنس غالب است (سوالات معمولاً محاوره‌ای‌اند)، ولی با وجود شماره‌ی
#         ماده/بند/تاریخ یا اصطلاح نادر، وزن BM25 به‌طور محسوس بالا می‌رود.
#         """
#         alpha = 0.7
#         if self._has_structural_reference(query):
#             alpha -= 0.35
#         if self._has_rare_term(query_tokens):
#             alpha -= 0.15
#         return max(0.15, min(0.9, alpha))

#     # ---------- مسیر دنس ----------

#     def _dense_search(self, query: str, k: int, access_level: Optional[int]) -> List[Tuple[str, float]]:
#         filter_ = {"access_level": {"$lte": access_level}} if access_level is not None else None
#         # similarity_search_with_score خودش embed_query را روی embeddings ما صدا می‌زند
#         results = self._vector_store.similarity_search_with_score(query, k=k, filter=filter_)

#         best_per_chunk: Dict[str, float] = {}
#         for doc, distance in results:
#             chunk_id = doc.metadata["chunk_id"]
#             score = 1.0 - distance  # کالکشن با cosine ساخته شده؛ وکتورها هم normalize شده‌اند
#             if chunk_id not in best_per_chunk or score > best_per_chunk[chunk_id]:
#                 best_per_chunk[chunk_id] = score

#         return sorted(best_per_chunk.items(), key=lambda x: -x[1])

#     # ---------- مسیر اسپارس ----------

#     def _sparse_search(self, query: str, k: int, access_level: Optional[int]) -> List[Tuple[str, float]]:
#         docs = self._bm25_retriever.invoke(query)  # preprocess_func خودمان داخلش صدا زده می‌شود

#         # BM25Retriever فقط داکیومنت‌ها را می‌دهد، نه امتیاز خام؛ امتیاز را مستقیم از خودِ vectorizer می‌گیریم
#         query_tokens = self.query_processor.tokenize_keyword(query)
#         if not query_tokens:
#             return []
#         scores = self._bm25_retriever.vectorizer.get_scores(query_tokens)
#         score_by_chunk = {
#             self._bm25_retriever.docs[i].metadata["chunk_id"]: float(scores[i])
#             for i in range(len(scores))
#         }

#         results = []
#         for doc in docs:
#             chunk_id = doc.metadata["chunk_id"]
#             score = score_by_chunk.get(chunk_id, 0.0)
#             if score <= 0:
#                 continue
#             if access_level is not None and self._chunk_lookup[chunk_id]["access_level"] > access_level:
#                 continue
#             results.append((chunk_id, score))
#             if len(results) >= k:
#                 break

#         results.sort(key=lambda x: -x[1])
#         return results

#     # ---------- fusion ----------

#     def _fuse_rrf(
#         self,
#         dense_results: List[Tuple[str, float]],
#         sparse_results: List[Tuple[str, float]],
#         k: int,
#         dense_weight: float,
#         sparse_weight: float,
#     ) -> List[Tuple[str, float]]:
#         scores: Dict[str, float] = {}
#         for rank, (chunk_id, _) in enumerate(dense_results):
#             scores[chunk_id] = scores.get(chunk_id, 0.0) + dense_weight / (self.rrf_k + rank + 1)
#         for rank, (chunk_id, _) in enumerate(sparse_results):
#             scores[chunk_id] = scores.get(chunk_id, 0.0) + sparse_weight / (self.rrf_k + rank + 1)
#         return sorted(scores.items(), key=lambda x: -x[1])[:k]

#     def _fuse_weighted(
#         self,
#         dense_results: List[Tuple[str, float]],
#         sparse_results: List[Tuple[str, float]],
#         k: int,
#         dense_weight: float,
#         sparse_weight: float,
#     ) -> List[Tuple[str, float]]:
#         def minmax(items: List[Tuple[str, float]]) -> Dict[str, float]:
#             if not items:
#                 return {}
#             values = [v for _, v in items]
#             lo, hi = min(values), max(values)
#             span = (hi - lo) or 1e-9
#             return {cid: (v - lo) / span for cid, v in items}

#         dense_norm = minmax(dense_results)
#         sparse_norm = minmax(sparse_results)
#         all_ids = set(dense_norm) | set(sparse_norm)

#         fused = {
#             cid: dense_weight * dense_norm.get(cid, 0.0) + sparse_weight * sparse_norm.get(cid, 0.0)
#             for cid in all_ids
#         }
#         return sorted(fused.items(), key=lambda x: -x[1])[:k]

#     # ---------- API اصلی ----------

#     def retrieve(
#         self,
#         query: str,
#         k: int = 5,
#         dense_k: Optional[int] = None,
#         sparse_k: Optional[int] = None,
#         access_level: Optional[int] = None,
#     ) -> List[Dict]:
#         """
#         access_level: سطح دسترسی کاربر (۱ تا ۳). اگر None باشد، هیچ فیلتری اعمال نمی‌شود
#         (فقط برای دیباگ/تست مناسب است - در مسیر واقعی همیشه باید پاس داده شود).
#         """
#         dense_k = dense_k or max(k * 3, k)
#         sparse_k = sparse_k or max(k * 3, k)

#         query_tokens = self.query_processor.tokenize_keyword(query)
#         alpha = self.estimate_alpha(query, query_tokens) if self.dynamic_alpha else self.alpha

#         dense_results = self._dense_search(query, dense_k, access_level)
#         sparse_results = self._sparse_search(query, sparse_k, access_level)

#         if self.fusion == "rrf":
#             fused = self._fuse_rrf(dense_results, sparse_results, k, alpha, 1 - alpha)
#         elif self.fusion == "weighted":
#             fused = self._fuse_weighted(dense_results, sparse_results, k, alpha, 1 - alpha)
#         else:
#             raise ValueError(f"روش fusion ناشناخته: {self.fusion}")

#         output = []
#         for chunk_id, fused_score in fused:
#             entry = self._chunk_lookup[chunk_id]
#             output.append({
#                 "chunk_id": chunk_id,
#                 "content": entry["content"],
#                 "metadata": entry["metadata"],
#                 "fused_score": fused_score,
#                 "dense_weight_used": round(alpha, 2),
#             })
#         return output





import json
import re
from typing import Dict, List, Optional, Tuple

from hazm import Lemmatizer, Normalizer, stopwords_list, word_tokenize
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


class QueryProcessor:
    """
    پردازش سوال فارسی با Hazm.
    - normalize_dense(): نرمال‌سازی سبک، برای embedding دنس (ساختار جمله دست‌نخورده می‌ماند).
    - tokenize_keyword(): توکنایز + حذف stopword + لماتایز، برای BM25.
    دقیقاً هم‌راستا با normalize_dataset.py که کورپوس با همان منطق آماده شده.
    """

    def __init__(self):
        self.normalizer = Normalizer()
        self.lemmatizer = Lemmatizer()
        self.stopwords = set(stopwords_list())

    def normalize_dense(self, text: str) -> str:
        text = self.normalizer.normalize(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def tokenize_keyword(self, text: str) -> List[str]:
        text = self.normalizer.normalize(text)
        tokens = word_tokenize(text)
        result = []
        for tok in tokens:
            if tok in self.stopwords:
                continue
            if re.fullmatch(r"[\W_]+", tok):
                continue
            lemma = self.lemmatizer.lemmatize(tok).split("#")[0]
            result.append(lemma)
        return result


class E5Embeddings(Embeddings):
    """
    Wrapper سازگار با اینترفیس Embeddings خودِ LangChain، برای مدل multilingual-e5-large.
    مدل‌های خانواده‌ی e5 با پیشوند "passage: " برای متن سند و "query: " برای سوال آموزش
    دیده‌اند - این تفکیک دقیقاً با تمایز embed_documents/embed_query در LangChain هماهنگ است.
    """

    def __init__(self, query_processor: QueryProcessor, model_name: str = "intfloat/multilingual-e5-base"):
        self.query_processor = query_processor
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        prefixed = ["passage: " + self.query_processor.normalize_dense(t) for t in texts]
        return self.model.encode(prefixed, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> List[float]:
        prefixed = "query: " + self.query_processor.normalize_dense(text)
        return self.model.encode([prefixed], normalize_embeddings=True)[0].tolist()


class HybridRetriever:
    """
    ترکیب dense retrieval (LangChain + Chroma) با sparse retrieval (LangChain BM25Retriever) و fuse کردن نتایج با RRF.

    نکات معماری:
      - Chroma از طریق langchain_chroma.Chroma به همان چروماستوری که با build_chroma.py
        ساختیم وصل می‌شود (وکتورهای موجود دوباره ساخته نمی‌شوند؛ embedding_function فقط
        برای embed کردن سوال در لحظه‌ی جستجو استفاده می‌شود).
      - BM25Retriever از LangChain، با preprocess_func=Hazm tokenizer خودمان ساخته می‌شود
        تا دقیقاً هم‌راستا با bm25 قبلی (لماتایز + حذف stopword) باشد. چون این کلاس امکان
        بارگذاری از فایل از پیش‌ساخته ندارد، هر بار از روی dataNormalized بازسازی می‌شود
        (برای ۱۲۴ چانک این کار لحظه‌ای است، مشکلی ایجاد نمی‌کند).
      - کلید یکتای هر نتیجه، chunk_id است (نه متن خام) - چون دو نوع رکورد در Chroma
        داریم ("content" و "query_alias")؛ هر نتیجه‌ی دنس (چه از content چه از یک
        query_alias مچ شود) به همان chunk_id resolve و به متن اصلی چانک نگاشت می‌شود.
      - فیلتر access_level هم روی مسیر دنس (به‌صورت native، از طریق پارامتر filter در
        Chroma) و هم روی مسیر اسپارس (دستی در پایتون، چون BM25Retriever فیلتر متادیتا
        ندارد) اعمال می‌شود.
      - وزن‌دهی دنس/BM25 پویاست: فقط بر اساس وجود شماره‌ی ماده/بند/تبصره/بخش/فصل در سوال
        (regex) وزن BM25 بالا می‌رود. (توضیح تصمیم زیر را ببینید.)

    تصمیم‌های گرفته‌شده بعد از تست A/B مستقل روی لایه‌ی ریتریو (بدون LLM، روی ۳۰ سوال
    واقعی/نیمه‌واقعی از دو batch جدا):
      - وزن‌دهی بر اساس اشاره‌ی ساختاری (ماده/بند/تبصره/بخش/فصل + عدد) نگه داشته شد:
        در تست مستقیم، خاموش کردنش رتبه‌ی چانک درست را برای سوالات ساختاری صریح
        (مثل «طبق ماده ۲ بند ۵...») از ۱ به ۳ می‌انداخت.
      - وزن‌دهی بر اساس واژه‌ی نادر/idf بالا (rare-term) که قبلاً وجود داشت، حذف شد:
        روی هر دو batch تست (۱۳ و ۱۷ سوال) هیچ تفاوتی در رتبه‌بندی ایجاد نمی‌کرد، و از نظر
        آماری هم روی کورپوس کوچک ۱۲۴ چانکی سیگنال قابل‌اعتمادی نبود (احتمال بالای
        false-trigger صرفاً به خاطر کوچک بودن کورپوس).
      - fusion وزن‌دهی‌شده‌ی min-max (جایگزین RRF) هم حذف شد چون در عمل هرگز استفاده
        نمی‌شد (fusion همیشه "rrf" بود).
      - محدودیت شناخته‌شده: حداقل یک مورد (چانک ماده ۶) در تست حتی با وزن ساختاری هم
        رتبه‌ی ۲ گرفت نه ۱ - چون top_k >= 2 است همچنان به LLM می‌رسد، برای MVP پذیرفته شد
        (ریشه‌یابی دقیق‌ترش به بعد موکول شد).

    توجه: langchain-community (که BM25Retriever از آن می‌آید) توسط خودِ LangChain
    در حال کنار گذاشته شدن اعلام شده؛ برای این پروژه مشکلی ایجاد نمی‌کند، ولی اگر بعداً
    هشدار deprecation آزاردهنده شد، جایگزین مستقیم "langchain-classic" یا نوشتن دستی
    (نسخه‌ی قبلی بدون LangChain که قبلاً نوشتیم) در دسترس است.
    """

    _ARTICLE_PATTERN = re.compile(r"(ماده|بند|تبصره|بخش|فصل)\s*[۰-۹0-9]+")
    _DATE_PATTERN = re.compile(r"[۰-۹0-9]{4}[/\-][۰-۹0-9]{1,2}[/\-][۰-۹0-9]{1,2}")

    def __init__(
        self,
        chroma_path: str = "chromaStore",
        collection_name: str = "legal_docs",
        normalized_data_path: str = "dataNormalized/dataset_normalized.json",
        registry_path: str = "data/documents_registry.json",
        embedding_model_name: str = "intfloat/multilingual-e5-base",
        alpha: float = 0.7,  # وزن پیش‌فرض دنس؛ فقط وقتی dynamic_alpha=False استفاده می‌شود
        dynamic_alpha: bool = True,
        rrf_k: int = 60,
    ):
        self.query_processor = QueryProcessor()
        self.alpha = alpha
        self.dynamic_alpha = dynamic_alpha
        self.rrf_k = rrf_k

        # ---------- مسیر دنس: Chroma از طریق LangChain، روی وکتور دیتابیس موجود ----------
        self.embeddings = E5Embeddings(self.query_processor, embedding_model_name)
        self._vector_store = Chroma(
            collection_name=collection_name,
            persist_directory=chroma_path,
            embedding_function=self.embeddings,
        )

        # ---------- رجیستری سند + لوکاپ نهایی chunk_id -> متن خام/متادیتا/access_level ----------
        with open(registry_path, encoding="utf-8") as f:
            registry = json.load(f)
        access_level_by_doc = {d["document_id"]: d["access_level"] for d in registry}
        document_name_by_doc = {d["document_id"]: d.get("document_name", "بدون عنوان") for d in registry}

        with open(normalized_data_path, encoding="utf-8") as f:
            normalized_data = json.load(f)

        self._chunk_lookup: Dict[str, Dict] = {}
        bm25_texts: List[str] = []
        bm25_metadatas: List[Dict] = []
        for r in normalized_data:
            meta = r["metadata"]
            cid = meta["chunk_id"]
            if cid in self._chunk_lookup:
                continue
            access_level = access_level_by_doc.get(meta.get("document_id"), 1)
            meta["document_name"] = document_name_by_doc.get(meta.get("document_id"), "بدون عنوان")
            self._chunk_lookup[cid] = {
                "content": r["context_chunk_raw"],
                "metadata": meta,
                "access_level": access_level,
            }

            enrichment_parts = [p for p in (meta.get("locator"), meta.get("section"), meta.get("document_name")) if p]        
            enriched_text = " ".join(enrichment_parts + [r["context_chunk_raw"]])
            bm25_texts.append(enriched_text)
            bm25_metadatas.append({"chunk_id": cid})

        # ---------- مسیر اسپارس: BM25Retriever از LangChain، با توکنایزر Hazm خودمان ----------
        self._bm25_retriever = BM25Retriever.from_texts(
            texts=bm25_texts,
            metadatas=bm25_metadatas,
            preprocess_func=self.query_processor.tokenize_keyword,
        )
        self._bm25_retriever.k = len(bm25_texts)  # امتیاز همه را می‌خواهیم، نه فقط ۴ تای پیش‌فرض

    # ---------- تشخیص نوع سوال برای وزن‌دهی پویا ----------

    def _has_structural_reference(self, text: str) -> bool:
        """آیا سوال به شماره‌ی ماده/بند/تبصره یا تاریخ دقیق اشاره دارد؟"""
        return bool(self._ARTICLE_PATTERN.search(text) or self._DATE_PATTERN.search(text))

    def estimate_alpha(self, query: str, query_tokens: List[str]) -> float:
        """
        وزن دنس (alpha) را برمی‌گرداند؛ وزن BM25 = 1 - alpha.
        پیش‌فرض دنس غالب است (سوالات معمولاً محاوره‌ای‌اند)، ولی با وجود شماره‌ی
        ماده/بند/تاریخ، وزن BM25 به‌طور محسوس بالا می‌رود.
        """
        alpha = 0.7
        if self._has_structural_reference(query):
            alpha -= 0.35
        return max(0.15, min(0.9, alpha))

    # ---------- مسیر دنس ----------

    def _dense_search(self, query: str, k: int, access_level: Optional[int]) -> List[Tuple[str, float]]:
        filter_ = {"access_level": {"$lte": access_level}} if access_level is not None else None
        # similarity_search_with_score خودش embed_query را روی embeddings ما صدا می‌زند
        results = self._vector_store.similarity_search_with_score(query, k=k, filter=filter_)

        best_per_chunk: Dict[str, float] = {}
        for doc, distance in results:
            chunk_id = doc.metadata["chunk_id"]
            score = 1.0 - distance  # کالکشن با cosine ساخته شده؛ وکتورها هم normalize شده‌اند
            if chunk_id not in best_per_chunk or score > best_per_chunk[chunk_id]:
                best_per_chunk[chunk_id] = score

        return sorted(best_per_chunk.items(), key=lambda x: -x[1])

    # ---------- مسیر اسپارس ----------

    def _sparse_search(self, query: str, k: int, access_level: Optional[int]) -> List[Tuple[str, float]]:
        docs = self._bm25_retriever.invoke(query)  # preprocess_func خودمان داخلش صدا زده می‌شود

        # BM25Retriever فقط داکیومنت‌ها را می‌دهد، نه امتیاز خام؛ امتیاز را مستقیم از خودِ vectorizer می‌گیریم
        query_tokens = self.query_processor.tokenize_keyword(query)
        if not query_tokens:
            return []
        scores = self._bm25_retriever.vectorizer.get_scores(query_tokens)
        score_by_chunk = {
            self._bm25_retriever.docs[i].metadata["chunk_id"]: float(scores[i])
            for i in range(len(scores))
        }

        results = []
        for doc in docs:
            chunk_id = doc.metadata["chunk_id"]
            score = score_by_chunk.get(chunk_id, 0.0)
            if score <= 0:
                continue
            if access_level is not None and self._chunk_lookup[chunk_id]["access_level"] > access_level:
                continue
            results.append((chunk_id, score))
            if len(results) >= k:
                break

        results.sort(key=lambda x: -x[1])
        return results

    # ---------- fusion (RRF) ----------

    def _fuse_rrf(
        self,
        dense_results: List[Tuple[str, float]],
        sparse_results: List[Tuple[str, float]],
        k: int,
        dense_weight: float,
        sparse_weight: float,
    ) -> List[Tuple[str, float]]:
        scores: Dict[str, float] = {}
        for rank, (chunk_id, _) in enumerate(dense_results):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + dense_weight / (self.rrf_k + rank + 1)
        for rank, (chunk_id, _) in enumerate(sparse_results):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + sparse_weight / (self.rrf_k + rank + 1)
        return sorted(scores.items(), key=lambda x: -x[1])[:k]

    # ---------- API اصلی ----------

    def retrieve(
        self,
        query: str,
        k: int = 5,
        dense_k: Optional[int] = None,
        sparse_k: Optional[int] = None,
        access_level: Optional[int] = None,
    ) -> List[Dict]:
        """
        access_level: سطح دسترسی کاربر (۱ تا ۳). اگر None باشد، هیچ فیلتری اعمال نمی‌شود
        (فقط برای دیباگ/تست مناسب است - در مسیر واقعی همیشه باید پاس داده شود).
        """
        dense_k = dense_k or max(k * 3, k)
        sparse_k = sparse_k or max(k * 3, k)

        query_tokens = self.query_processor.tokenize_keyword(query)
        alpha = self.estimate_alpha(query, query_tokens) if self.dynamic_alpha else self.alpha

        dense_results = self._dense_search(query, dense_k, access_level)
        sparse_results = self._sparse_search(query, sparse_k, access_level)

        fused = self._fuse_rrf(dense_results, sparse_results, k, alpha, 1 - alpha)

        output = []
        for chunk_id, fused_score in fused:
            entry = self._chunk_lookup[chunk_id]
            output.append({
                "chunk_id": chunk_id,
                "content": entry["content"],
                "metadata": entry["metadata"],
                "fused_score": fused_score,
                "dense_weight_used": round(alpha, 2),
            })
        return output