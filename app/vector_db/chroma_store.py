import chromadb
import hashlib
from typing import Any, Dict, List

CHROMA_PATH = "app/data/chroma_db"
COLLECTION_NAME = "srm_knowledge_base"

client = chromadb.PersistentClient(path=CHROMA_PATH)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)

def _make_id(source: str, chunk_id: Any, text: str) -> str:
    base = f"{source}|{chunk_id}|{text}"
    return hashlib.sha1(base.encode("utf-8", errors="ignore")).hexdigest()

def add_documents(data: List[Dict[str, Any]], batch_size: int = 256) -> None:
    ids, documents, embeddings, metadatas = [], [], [], []
    seen_ids = set()

    for item in data:
        text = (item.get("text") or "").strip()
        emb = item.get("embedding")
        if not text or emb is None:
            continue

        source = item.get("source", "unknown")
        chunk_id = item.get("chunk_id", "")

        doc_id = _make_id(source, chunk_id, text)

        if doc_id in seen_ids:
            continue
        seen_ids.add(doc_id)

        metadata = item.get("metadata") or {}
        metadata.setdefault("source", source)
        metadata.setdefault("chunk_id", chunk_id)

        ids.append(doc_id)
        documents.append(text)
        embeddings.append(emb)
        metadatas.append(metadata)

        if len(ids) >= batch_size:
            collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
            ids, documents, embeddings, metadatas = [], [], [], []

    if ids:
        collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

def get_collection_count() -> int:
    return collection.count()