"""
reranker_service.py
Cross-encoder reranking of retrieved chunks.
Returns chunks AND their reranker scores for Evidence Guard.
Falls back gracefully if the model is unavailable.
"""

import os
from typing import List, Dict, Tuple, Optional

_reranker = None
_reranker_available = None   # None = not checked yet

RERANKER_MODEL = os.environ.get("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")


def _load_reranker():
    global _reranker, _reranker_available
    if _reranker_available is not None:
        return _reranker  # already determined

    try:
        from sentence_transformers import CrossEncoder
        print(f"[Reranker] Loading cross-encoder model '{RERANKER_MODEL}'...")
        _reranker = CrossEncoder(RERANKER_MODEL, max_length=512)
        _reranker_available = True
        print("[Reranker] Cross-encoder loaded.")
    except Exception as e:
        print(f"[Reranker] Not available ({e}). Using RRF order as fallback.")
        _reranker = None
        _reranker_available = False

    return _reranker


def rerank(
    query: str,
    chunks: List[Dict],
    top_k: int = 5,
) -> Tuple[List[Dict], List[float]]:
    """
    Rerank chunks by cross-encoder relevance to query.
    Uses cross-encoder if available, otherwise returns chunks in RRF order.

    Returns:
        (reranked_chunks, scores)
        where scores[i] corresponds to reranked_chunks[i]
    """
    if not chunks:
        return [], []

    reranker = _load_reranker()

    if reranker is None:
        # Fallback: return top_k in current order with placeholder scores
        result = chunks[:top_k]
        # Use normalised RRF scores as surrogate
        scores = [c.get("rrf_score", 0.5) for c in result]
        return result, scores

    pairs = [(query, c["content"]) for c in chunks]
    try:
        raw_scores = reranker.predict(pairs, show_progress_bar=False)
        scored = sorted(
            zip(raw_scores, chunks),
            key=lambda x: x[0],
            reverse=True,
        )
        top_scored = scored[:top_k]
        reranked_chunks = []
        reranker_scores = []
        for s, c in top_scored:
            c_copy = dict(c)
            c_copy["reranker_score"] = float(s)
            reranked_chunks.append(c_copy)
            reranker_scores.append(float(s))
        return reranked_chunks, reranker_scores

    except Exception as e:
        print(f"[Reranker] Predict failed: {e}. Using RRF order fallback.")
        result = chunks[:top_k]
        scores = [c.get("rrf_score", 0.5) for c in result]
        return result, scores


def is_reranker_available() -> bool:
    _load_reranker()
    return bool(_reranker_available)
