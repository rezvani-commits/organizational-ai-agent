import json
import re
from typing import Dict, List, Optional, Tuple

from hazm import Lemmatizer, Normalizer, stopwords_list, word_tokenize
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


class QueryProcessor:

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

    _ARTICLE_PATTERN = re.compile(r"(ماده|بند|تبصره|بخش|فصل)\s*[۰-۹0-9]+")
    _DATE_PATTERN = re.compile(r"[۰-۹0-9]{4}[/\-][۰-۹0-9]{1,2}[/\-][۰-۹0-9]{1,2}")

    def __init__(
        self,
        chroma_path: str = "chromaStore",
        collection_name: str = "legal_docs",
        normalized_data_path: str = "dataNormalized/dataset_normalized.json",
        registry_path: str = "data/documents_registry.json",
        embedding_model_name: str = "intfloat/multilingual-e5-base",
        alpha: float = 0.7,
        dynamic_alpha: bool = True,
        rrf_k: int = 60,
    ):
        self.query_processor = QueryProcessor()
        self.alpha = alpha
        self.dynamic_alpha = dynamic_alpha
        self.rrf_k = rrf_k

        self.embeddings = E5Embeddings(self.query_processor, embedding_model_name)
        self._vector_store = Chroma(
            collection_name=collection_name,
            persist_directory=chroma_path,
            embedding_function=self.embeddings,
        )

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

        self._bm25_retriever = BM25Retriever.from_texts(
            texts=bm25_texts,
            metadatas=bm25_metadatas,
            preprocess_func=self.query_processor.tokenize_keyword,
        )
        self._bm25_retriever.k = len(bm25_texts)


    def _has_structural_reference(self, text: str) -> bool:
        return bool(self._ARTICLE_PATTERN.search(text) or self._DATE_PATTERN.search(text))

    def estimate_alpha(self, query: str, query_tokens: List[str]) -> float:
        alpha = 0.7
        if self._has_structural_reference(query):
            alpha -= 0.35
        return max(0.15, min(0.9, alpha))


    def _dense_search(self, query: str, k: int, access_level: Optional[int]) -> List[Tuple[str, float]]:
        filter_ = {"access_level": {"$lte": access_level}} if access_level is not None else None
        results = self._vector_store.similarity_search_with_score(query, k=k, filter=filter_)

        best_per_chunk: Dict[str, float] = {}
        for doc, distance in results:
            chunk_id = doc.metadata["chunk_id"]
            score = 1.0 - distance 
            if chunk_id not in best_per_chunk or score > best_per_chunk[chunk_id]:
                best_per_chunk[chunk_id] = score

        return sorted(best_per_chunk.items(), key=lambda x: -x[1])


    def _sparse_search(self, query: str, k: int, access_level: Optional[int]) -> List[Tuple[str, float]]:
        docs = self._bm25_retriever.invoke(query)

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