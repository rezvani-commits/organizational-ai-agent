"""
نرمال‌سازی دیتاست برای دو مسیر ایندکس: دنس (embedding) و کیورد (BM25)
ورودی:  ./data/dataset_clean.json
خروجی:  ./dataNormalized/dataset_normalized.json
"""
import json
import os
import re
from hazm import Normalizer, word_tokenize, Lemmatizer, stopwords_list

IN_DIR = "data"
OUT_DIR = "dataNormalized"
IN_FILE = os.path.join(IN_DIR, "dataset_clean.json")
OUT_FILE = os.path.join(OUT_DIR, "dataset_normalized.json")

hazm_normalizer = Normalizer()
lemmatizer = Lemmatizer()
STOPWORDS = set(stopwords_list())


def normalize_light(text: str) -> str:
    """نرمال‌سازی سبک - برای embedding دنس. فقط یکسان‌سازی نویسه‌ها، بدون تغییر معنایی."""
    if not text:
        return text
    text = hazm_normalizer.normalize(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_keyword(text: str) -> str:
    """نرمال‌سازی سنگین - برای BM25. توکنایز + حذف stopword + لماتایز."""
    if not text:
        return text
    text = hazm_normalizer.normalize(text)
    tokens = word_tokenize(text)
    result = []
    for tok in tokens:
        if tok in STOPWORDS:
            continue
        if re.fullmatch(r"[\W_]+", tok):  # فقط علائم نگارشی
            continue
        lemma = lemmatizer.lemmatize(tok)
        lemma = lemma.split("#")[0]  # حالت فعل: "رفت#رو" -> "رفت"
        result.append(lemma)
    return " ".join(result)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(IN_FILE, encoding="utf-8") as f:
        data = json.load(f)

    out_records = []
    for r in data:
        chunk_raw = r["context_chunk"]
        query_raw = r["query"]

        out_records.append({
            "id": r["id"],
            "metadata": r["metadata"],  # دست‌نخورده - نیاز به نرمال‌سازی نداره
            "context_chunk_raw": chunk_raw,
            "context_chunk_dense": normalize_light(chunk_raw),
            "context_chunk_keyword": normalize_keyword(chunk_raw),
            "query_raw": query_raw,
            "query_dense": normalize_light(query_raw),
            "query_keyword": normalize_keyword(query_raw),
        })

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out_records, f, ensure_ascii=False, indent=2)

    print(f"{len(out_records)} رکورد نرمال‌سازی شد -> {OUT_FILE}")


if __name__ == "__main__":
    main()