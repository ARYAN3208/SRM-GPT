import logging
import numpy as np
from typing import List, Tuple, Union

logger = logging.getLogger("reranker")

_reranker = None

def _get_reranker():
    """Load and cache CrossEncoder reranker model."""
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
    top_k: int = 10,
    return_scores: bool = False
) -> Union[List[str], List[Tuple[str, float]]]:
    """
    Rerank documents using CrossEncoder based on query relevance.
    
    Args:
        query: The search query
        documents: List of documents to rerank
        top_k: Number of top documents to return
        return_scores: If True, return (document, score) tuples
    
    Returns:
        List of top-k reranked documents (with or without scores)
    """
    try:
        # Validate inputs
        if not documents:
            logger.warning("No documents provided for reranking")
            return [] if not return_scores else []

        # Sanitize query
        query_clean = query.strip() if isinstance(query, str) else str(query).strip()
        if not query_clean:
            logger.error("Invalid query")
            return [] if not return_scores else []

        # Sanitize documents
        docs_clean = []
        for doc in documents:
            if isinstance(doc, str):
                docs_clean.append(doc.strip())
            else:
                docs_clean.append(str(doc).strip())
        
        # Filter empty documents
        docs_clean = [d for d in docs_clean if d]

        if not docs_clean:
            logger.error("No valid documents after sanitization")
            return [] if not return_scores else []

        logger.info(f"Reranking {len(docs_clean)} documents for query: {query_clean[:50]}...")

        # Create query-document pairs
        pairs = [(query_clean, doc) for doc in docs_clean]

        # Get reranker
        reranker = _get_reranker()

        # Predict scores
        try:
            scores = reranker.predict(pairs)
            logger.info(f"Reranker produced {len(scores)} scores (type: {type(scores).__name__})")
        except Exception as score_exc:
            logger.error(f"Reranking prediction failed: {score_exc}", exc_info=True)
            raise RuntimeError(f"Reranking failed: {str(score_exc)}") from score_exc

        # Convert numpy array to list if needed
        if isinstance(scores, np.ndarray):
            scores = scores.tolist()
            logger.debug("Converted numpy array scores to list")

        # Validate scores length (more lenient check)
        if not isinstance(scores, (list, tuple)) or len(scores) == 0:
            logger.error(f"Invalid scores: expected non-empty list, got {type(scores).__name__}")
            raise ValueError("Reranker returned invalid scores")

        if len(scores) != len(docs_clean):
            logger.error(f"Score count mismatch: expected {len(docs_clean)}, got {len(scores)}")
            raise ValueError(f"Score count mismatch: {len(scores)} vs {len(docs_clean)}")

        # Rank documents by score
        ranked = list(zip(docs_clean, scores))
        ranked.sort(key=lambda x: float(x[1]), reverse=True)

        # Log top scores
        top_scores = ranked[:min(5, len(ranked))]
        logger.info(f"Top reranking scores: {[round(float(score), 4) for doc, score in top_scores]}")

        # Enforce top_k limit
        top_k = min(top_k, len(ranked))
        result = ranked[:top_k]

        if return_scores:
            logger.info(f"Returning {len(result)} documents with scores")
            return [(doc, float(score)) for doc, score in result]

        # Extract documents only
        docs_only = [doc for doc, score in result]
        logger.info(f"Returning {len(docs_only)} reranked documents")

        return docs_only

    except Exception as exc:
        logger.error(f"Reranking pipeline failed: {exc}", exc_info=True)
        raise RuntimeError(f"Document reranking failed: {str(exc)}") from exc