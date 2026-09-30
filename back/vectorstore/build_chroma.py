
import json
import numpy as np
import chromadb

VECTOR_DIR = "vectorStore"
CHROMA_DIR = "chromaStore"
COLLECTION_NAME = "legal_docs"
REGISTRY_FILE = "data/documents_registry.json" 


def none_to_str(v):
    return v if v is not None else ""


def main():
    embeddings = np.load(f"{VECTOR_DIR}/embeddings.npy")
    with open(f"{VECTOR_DIR}/vectors_metadata.json", encoding="utf-8") as f:
        records = json.load(f)

    with open(REGISTRY_FILE, encoding="utf-8") as f:
        registry = json.load(f)
    access_level_by_doc = {d["document_id"]: d["access_level"] for d in registry}
    document_name_by_doc = {d["document_id"]: d.get("document_name", "بدون عنوان") for d in registry}

    assert len(embeddings) == len(records), "تعداد وکتورها و متادیتا برابر نیست!"

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [r["id"] for r in records]
    documents = [r["text_raw"] for r in records] 
    metadatas = []
    for r in records:
        m = r["metadata"]
        doc_id = m.get("document_id")
        metadatas.append({
            "chunk_id": r["chunk_id"],
            "type": r["type"],
            "document_id": none_to_str(doc_id),
            "document_name": document_name_by_doc.get(doc_id, "بدون عنوان"),
            "access_level": access_level_by_doc.get(doc_id, 1),
            "section": none_to_str(m.get("section")),
            "locator": none_to_str(m.get("locator")),
            "sub_reference": none_to_str(m.get("sub_reference")),
        })

    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=documents,
        metadatas=metadatas,
    )

    print(f"{collection.count()} وکتور در Chroma بارگذاری شد -> {CHROMA_DIR}/")


if __name__ == "__main__":
    main()
