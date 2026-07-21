import numpy as np
from typing import Dict, List, Tuple

from app.utils.logger import get_logger

logger = get_logger("reranker")

_reranker = None


def _get_reranker():
    global _reranker
    if _reranker is not None:
        logger.debug("Reranker already loaded, using cached instance")
        return _reranker
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as exc:
        logger.error("Failed to import CrossEncoder: %s", exc)
        raise RuntimeError(
            "Failed to import CrossEncoder for reranking. "
            "Install sentence-transformers and try again."
        ) from exc
    try:
        logger.info("Loading reranker model: cross-encoder/ms-marco-MiniLM-L-12-v2")
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-12-v2")
        logger.info("Reranker model loaded successfully")
        return _reranker
    except Exception as exc:
        logger.error("Failed to load reranker model: %s", exc, exc_info=True)
        raise RuntimeError(f"Failed to load reranker: {str(exc)}") from exc


def rerank_documents(
    query: str,
    documents: List[str],
    metadatas: List[Dict] = None,
    top_k: int = 10,
) -> Tuple[List[str], List[Dict]]:
    try:
        if not documents:
            logger.warning("No documents provided for reranking")
            return [], [] if metadatas else []
        query_clean = query.strip() if isinstance(query, str) else str(query).strip()
        if not query_clean:
            logger.error("Invalid query")
            return [], [] if metadatas else []
        indexed_docs: List[Tuple[int, str]] = []
        for idx, doc in enumerate(documents):
            cleaned = doc.strip() if isinstance(doc, str) else str(doc).strip()
            if cleaned:
                indexed_docs.append((idx, cleaned))
        if not indexed_docs:
            logger.error("No valid documents after sanitization")
            return [], [] if metadatas else []
        docs_clean = [d for _, d in indexed_docs]
        original_idx_map = [i for i, _ in indexed_docs]
        logger.info("Reranking %d documents for query: %s...", len(docs_clean), query_clean[:50])
        pairs = [(query_clean, doc) for doc in docs_clean]
        reranker_model = _get_reranker()
        try:
            scores = reranker_model.predict(pairs)
            logger.info("Reranker produced %d scores (type: %s)", len(scores), type(scores).__name__)
        except Exception as score_exc:
            logger.error("Reranking prediction failed: %s", score_exc, exc_info=True)
            raise RuntimeError(f"Reranking failed: {str(score_exc)}") from score_exc
        if isinstance(scores, np.ndarray):
            scores = scores.tolist()
        if not isinstance(scores, (list, tuple)) or len(scores) == 0:
            logger.error("Invalid scores: expected non-empty list, got %s", type(scores).__name__)
            raise ValueError("Reranker returned invalid scores")
        if len(scores) != len(docs_clean):
            logger.error("Score count mismatch: expected %d, got %d", len(docs_clean), len(scores))
            raise ValueError(f"Score count mismatch: {len(scores)} vs {len(docs_clean)}")
        ranked: List[Tuple[int, str, float]] = list(zip(original_idx_map, docs_clean, scores))
        ranked.sort(key=lambda x: float(x[2]), reverse=True)
        top_scores = ranked[:min(5, len(ranked))]
        logger.info("Top reranking scores: %s", [round(float(s), 4) for _, _, s in top_scores])
        top_k = min(top_k, len(ranked))
        result = ranked[:top_k]
        reranked_docs = [doc for _, doc, _ in result]
        reranked_metas: List[Dict] = []
        if metadatas:
            for orig_idx, _, _ in result:
                if orig_idx < len(metadatas):
                    reranked_metas.append(metadatas[orig_idx])
                else:
                    reranked_metas.append({"source": "unknown", "chunk_id": "unknown", "distance": 0})
        else:
            reranked_metas = []
        logger.info("Returning %d reranked documents", len(reranked_docs))
        return reranked_docs, reranked_metas
    except Exception as exc:
        logger.error("Reranking pipeline failed: %s", exc, exc_info=True)
        raise RuntimeError(f"Document reranking failed: {str(exc)}") from exc