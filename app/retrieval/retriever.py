import hashlib
import logging
import os
import re
from typing import Any, Dict, List, Tuple

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger("retriever")

# ----------------------------
# Configuration
# ----------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# IMPORTANT: Must match the model used to create embeddings in create_embeddings.py
DEFAULT_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "srm_knowledge_base")
DEFAULT_PERSIST_DIR = os.getenv(
    "CHROMA_PERSIST_DIR",
    os.path.join(BASE_DIR, "app", "data", "chroma_db")
)
# Also create alias path if it doesn't exist
_alt_persist_dir = os.path.join(BASE_DIR, "data", "chroma_db")
if not os.path.exists(DEFAULT_PERSIST_DIR) and os.path.exists(_alt_persist_dir):
    DEFAULT_PERSIST_DIR = _alt_persist_dir
# CRITICAL: Must match the embedding model used during ingestion (BAAI/bge-small-en-v1.5)
# Stored embeddings were generated with this model; query embeddings must use the same.
DEFAULT_EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "BAAI/bge-small-en-v1.5"
)

_collection = None
_embedding_model = None


# ----------------------------
# Embedding model loader
# ----------------------------
def _get_embedding_model():
    global _embedding_model

    if _embedding_model is not None:
        return _embedding_model

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "sentence-transformers is required. "
            "Install it with: pip install sentence-transformers"
        ) from exc

    logger.info("Loading embedding model: %s", DEFAULT_EMBEDDING_MODEL)
    _embedding_model = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)
    logger.info("Embedding model loaded.")
    return _embedding_model


# ----------------------------
# Query expansion - generate multiple query variants for better recall
# ----------------------------
def _expand_query(query: str) -> List[str]:
    """
    BGE models benefit from adding a task prefix for retrieval.
    Generate multiple query variants to improve recall.
    """
    query = query.strip()
    if not query:
        return [query]

    # BGE models perform better with the "Represent this sentence for searching: " prefix
    # Add both with and without prefix for maximal coverage
    variants = [query]

    # Add BGE-optimized retrieval query
    bgd_query = f"Represent this sentence for searching: {query}"
    variants.append(bgd_query)

    # Add keyword-focused variant if query is long enough
    words = query.split()
    if len(words) > 4:
        # Keep only meaningful keywords (length > 3)
        keywords = [w for w in words if len(w) > 3 and w.lower() not in {
            "this", "that", "with", "from", "what", "when", "where",
            "which", "there", "about", "would", "could", "should",
            "their", "them", "then", "than", "just", "also", "how",
            "tell", "give", "show", "find", "know", "very", "much",
            "many", "some", "more", "such", "only"
        }]
        if len(keywords) >= 2:
            variants.append(" ".join(keywords))

    return variants


# ----------------------------
# Chroma collection loader
# ----------------------------
def _get_collection():
    global _collection

    if _collection is not None:
        return _collection

    try:
        import chromadb
    except ImportError as exc:
        raise RuntimeError(
            "chromadb is required. Install it with: pip install chromadb"
        ) from exc

    os.makedirs(DEFAULT_PERSIST_DIR, exist_ok=True)

    class SentenceTransformerEmbeddingFunction:
        def __init__(self, model_name: str):
            self.model_name = model_name
            self.model = _get_embedding_model()

        def name(self):
            return self.model_name

        def __call__(self, input):
            if not input:
                return []

            embeddings = self.model.encode(
                list(input),
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            if hasattr(embeddings, "tolist"):
                return embeddings.tolist()
            return list(embeddings)

        def embed_query(self, input):
            return self.__call__(input)

        def embed_document(self, input):
            return self.__call__(input)

    client = chromadb.PersistentClient(path=DEFAULT_PERSIST_DIR)

    embedding_function = SentenceTransformerEmbeddingFunction(DEFAULT_EMBEDDING_MODEL)

    # Use get_collection since the collection already exists with pre-computed embeddings
    # Do NOT pass embedding_function - it conflicts with the persisted default config
    _collection = client.get_collection(
        name=DEFAULT_COLLECTION_NAME
    )

    logger.info(
        "Connected to Chroma collection '%s' at %s",
        DEFAULT_COLLECTION_NAME,
        DEFAULT_PERSIST_DIR
    )
    return _collection


# ----------------------------
# Utility helpers
# ----------------------------
def _normalize_text(text: Any) -> str:
    if not isinstance(text, str):
        text = str(text or "")
    return re.sub(r"\s+", " ", text).strip()


def _is_boilerplate(text: str) -> bool:
    text = _normalize_text(text).lower()
    if not text:
        return True

    if len(text) < 80:
        return True

    boilerplate_patterns = [
        "skip to main content",
        "privacy policy",
        "terms and conditions",
        "all rights reserved",
        "copyright 20",
    ]

    if any(pattern in text for pattern in boilerplate_patterns):
        return True

    words = re.findall(r"\b\w+\b", text)
    if len(words) < 12:
        return True

    return False


def _sanitize_metadata(meta: Any) -> Dict[str, Any]:
    if not isinstance(meta, dict):
        meta = {}

    source = meta.get("source") or meta.get("source_name") or "unknown"
    chunk_id = meta.get("chunk_id") or meta.get("id") or "unknown"

    return {
        "source": str(source)[:80],
        "chunk_id": str(chunk_id)[:60],
        "page": str(meta.get("page", ""))[:20],
    }


def _deduplicate_rows(rows: List[Tuple[float, str, Dict[str, Any]]]) -> List[Tuple[float, str, Dict[str, Any]]]:
    seen = set()
    deduped = []

    for distance, doc, meta in rows:
        doc_text = _normalize_text(doc)
        if not doc_text:
            continue

        key = hashlib.md5(doc_text.lower().encode("utf-8")).hexdigest()

        if key in seen:
            continue

        seen.add(key)
        deduped.append((distance, doc_text, meta))

    return deduped


# ----------------------------
# Main retrieval function
# ----------------------------
def retrieve_documents(
    query: str,
    top_k: int = 50
) -> Dict[str, List[List[Any]]]:
    """
    Retrieve relevant documents from Chroma.

    Returns:
        {
            "documents": [[...]],
            "metadatas": [[...]],
            "distances": [[...]]
        }
    """
    if not isinstance(query, str) or not query.strip():
        logger.warning("Empty query provided to retrieve_documents")
        return {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

    query = query.strip()

    try:
        collection = _get_collection()
    except Exception as exc:
        logger.error("Failed to initialize Chroma collection: %s", exc, exc_info=True)
        return {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

    logger.info("Retrieval Started: %s", query)

    try:
        # Generate query variants for better recall
        query_variants = _expand_query(query)

        # Use a much larger top_k to ensure we get enough candidates after filtering
        n_results = max(top_k * 3, 60)

        all_docs = []
        all_metas = []
        all_dists = []

        # Embed the query ourselves using the same model that generated the stored embeddings
        model = _get_embedding_model()

        # Try primary query first (without BGE prefix for better general matching)
        query_embedding = model.encode([query_variants[0]], normalize_embeddings=True)[0].tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        all_docs.extend(docs)
        all_metas.extend(metas)
        all_dists.extend(dists)

        # If few results, fall back to BGE-optimized query and keyword variants
        if len(docs) < 20 and len(query_variants) > 1:
            for variant in query_variants[1:]:
                var_embedding = model.encode([variant], normalize_embeddings=True)[0].tolist()
                variant_results = collection.query(
                    query_embeddings=[var_embedding],
                    n_results=n_results,
                    include=["documents", "metadatas", "distances"]
                )
                v_docs = variant_results.get("documents", [[]])[0]
                v_metas = variant_results.get("metadatas", [[]])[0]
                v_dists = variant_results.get("distances", [[]])[0]
                all_docs.extend(v_docs)
                all_metas.extend(v_metas)
                all_dists.extend(v_dists)

        logger.info("Chroma Returned (primary+variants): %s candidate docs", len(all_docs))

        rows: List[Tuple[float, str, Dict[str, Any]]] = []

        for doc, meta, dist in zip(all_docs, all_metas, all_dists):
            if not isinstance(doc, str):
                doc = str(doc or "")

            doc_text = _normalize_text(doc)
            if not doc_text:
                continue

            if _is_boilerplate(doc_text):
                continue

            try:
                distance = float(dist)
            except (TypeError, ValueError):
                continue

            safe_meta = _sanitize_metadata(meta)
            rows.append((distance, doc_text, safe_meta))

        # Deduplicate by content hash
        rows = _deduplicate_rows(rows)

        # Sort by distance (smaller is better)
        rows.sort(key=lambda item: item[0])

        # Keep enough results - the reranker will filter relevance better
        final_rows = rows[:max(top_k, 10)]

        final_docs = [doc for _, doc, _ in final_rows]
        final_metas = [meta for _, _, meta in final_rows]
        final_dists = [dist for dist, _, _ in final_rows]

        logger.info(
            "Filter stats: kept=%s total_candidates=%s",
            len(final_rows), len(all_docs)
        )

        logger.info("Candidates After Filtering: %s", len(final_rows))

        if final_rows:
            for idx, (dist, doc, meta) in enumerate(final_rows[:10], start=1):
                logger.info(
                    "Rank=%s | Score=%s | Distance=%.4f | Source=%s | Chunk=%s",
                    idx,
                    round((1 - dist) * 100, 2),
                    dist,
                    meta.get("source", "unknown"),
                    meta.get("chunk_id", "unknown"),
                )

        logger.info("Final Documents Returned: %s", len(final_rows))

        return {
            "documents": [final_docs],
            "metadatas": [final_metas],
            "distances": [final_dists],
        }

    except Exception as exc:
        logger.error("Retrieval failed: %s", exc, exc_info=True)
        return {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }