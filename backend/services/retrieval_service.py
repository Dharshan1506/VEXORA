"""
retrieval_service.py
Real BM25 keyword search, dense vector cosine-similarity search,
and Reciprocal Rank Fusion (RRF) for hybrid retrieval.
Searches ONLY actual uploaded and indexed document chunks from the database.
"""

import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from rank_bm25 import BM25Okapi

from services.embedding_service import deserialize_embedding


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(va, vb) / (norm_a * norm_b))


import os
import re

RRF_K_DEFAULT = int(os.environ.get("RRF_K", "60"))
BM25_TOP_K_DEFAULT = int(os.environ.get("BM25_TOP_K", "10"))
VECTOR_TOP_K_DEFAULT = int(os.environ.get("VECTOR_TOP_K", "10"))


def load_all_chunks(conn, prefer_latest: bool = True) -> List[Dict]:
    """
    Load all indexed document chunks from the database.
    Only returns chunks whose parent document is 'indexed' AND have an embedding.
    Searches REAL uploaded documents — no hardcoded knowledge base.

    If prefer_latest is True, filters out superseded documents so the latest valid
    version is retrieved.
    """
    cursor = conn.cursor()
    where_clause = "WHERE d.status = 'indexed' AND dc.embedding IS NOT NULL AND dc.content != ''"
    if prefer_latest:
        where_clause += " AND (d.superseded_by IS NULL OR d.superseded_by = '')"

    query_sql = f"""
        SELECT
            dc.id,
            dc.id AS chunk_id,
            dc.document_id,
            dc.chunk_index,
            dc.content,
            dc.content AS chunk_text,
            dc.content_hash AS chunk_hash,
            dc.page_number,
            dc.section_name,
            dc.section_name AS section,
            dc.embedding,
            dc.ocr_used,
            dc.ocr_confidence,
            d.name AS doc_name,
            d.name AS document_name,
            d.version AS doc_version,
            d.version AS document_version,
            d.category AS doc_category,
            d.doc_type AS document_type,
            d.file_path AS source_path,
            d.upload_date AS upload_timestamp,
            d.content_hash AS doc_hash,
            d.superseded_by
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        {where_clause}
        ORDER BY dc.document_id, dc.chunk_index
    """
    cursor.execute(query_sql)
    rows = cursor.fetchall()

    # If prefer_latest was True but returned no chunks, fallback to all indexed documents
    if not rows and prefer_latest:
        cursor.execute(f"""
            SELECT
                dc.id,
                dc.id AS chunk_id,
                dc.document_id,
                dc.chunk_index,
                dc.content,
                dc.content AS chunk_text,
                dc.content_hash AS chunk_hash,
                dc.page_number,
                dc.section_name,
                dc.section_name AS section,
                dc.embedding,
                dc.ocr_used,
                dc.ocr_confidence,
                d.name AS doc_name,
                d.name AS document_name,
                d.version AS doc_version,
                d.version AS document_version,
                d.category AS doc_category,
                d.doc_type AS document_type,
                d.file_path AS source_path,
                d.upload_date AS upload_timestamp,
                d.content_hash AS doc_hash,
                d.superseded_by
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE d.status = 'indexed' AND dc.embedding IS NOT NULL AND dc.content != ''
            ORDER BY dc.document_id, dc.chunk_index
        """)
        rows = cursor.fetchall()

    chunks = []
    for row in rows:
        c = dict(row)
        if c.get("embedding"):
            c["embedding"] = deserialize_embedding(c["embedding"])
        chunks.append(c)
    return chunks


def _tokenize_text(text: str) -> List[str]:
    """Tokenize text preserving words, numbers, and percentage values."""
    return re.findall(r"\b[\w%.-]+\b", text.lower())


def bm25_search(
    query: str,
    chunks: List[Dict],
    top_k: int = 10,
) -> List[Tuple[float, Dict]]:
    """
    Real BM25 search over actual uploaded document chunks.
    Returns (score, chunk) tuples sorted by BM25 score descending.
    """
    if not chunks:
        return []

    # Tokenize corpus
    tokenized_corpus = [_tokenize_text(c["content"]) for c in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    query_tokens = _tokenize_text(query)
    if not query_tokens:
        query_tokens = query.lower().split()
    scores = bm25.get_scores(query_tokens)

    scored = sorted(
        zip(scores, chunks),
        key=lambda x: x[0],
        reverse=True,
    )
    return [(float(s), c) for s, c in scored[:top_k]]


def vector_search(
    query_embedding: List[float],
    chunks: List[Dict],
    top_k: int = 10,
) -> List[Tuple[float, Dict]]:
    """
    Real cosine-similarity vector search against actual uploaded chunk embeddings.
    Returns (cosine_similarity, chunk) tuples sorted descending.
    """
    if not chunks:
        return []

    scored = [
        (_cosine_similarity(query_embedding, c["embedding"]), c)
        for c in chunks
        if c.get("embedding")
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]


def rrf_fusion(
    bm25_results: List[Tuple[float, Dict]],
    vector_results: List[Tuple[float, Dict]],
    k: int = None,
) -> List[Dict]:
    """
    Reciprocal Rank Fusion of BM25 and vector-search ranked lists.
    Formula: RRF(d) = Σ 1/(k + rank(d))
    Returns merged, deduplicated list sorted by RRF score descending.
    Each chunk carries rrf_score, bm25_rank, vector_rank, bm25_score, vector_score,
    and metadata.
    """
    k_val = k if k is not None else RRF_K_DEFAULT
    rrf_scores: Dict[str, float] = {}
    bm25_ranks: Dict[str, int] = {}
    vector_ranks: Dict[str, int] = {}
    bm25_score_map: Dict[str, float] = {}
    vector_score_map: Dict[str, float] = {}
    chunk_map: Dict[str, Dict] = {}

    for rank, (score, chunk) in enumerate(bm25_results):
        cid = chunk["id"]
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (k_val + rank + 1)
        bm25_ranks[cid] = rank + 1
        bm25_score_map[cid] = score
        chunk_map[cid] = chunk

    for rank, (score, chunk) in enumerate(vector_results):
        cid = chunk["id"]
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (k_val + rank + 1)
        vector_ranks[cid] = rank + 1
        vector_score_map[cid] = score
        chunk_map[cid] = chunk

    sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)

    result = []
    for cid in sorted_ids:
        chunk = dict(chunk_map[cid])  # copy to avoid mutating cache
        chunk["chunk_id"] = cid
        chunk["rrf_score"] = round(rrf_scores[cid], 6)
        chunk["bm25_rank"] = bm25_ranks.get(cid)
        chunk["vector_rank"] = vector_ranks.get(cid)
        chunk["bm25_score"] = round(bm25_score_map.get(cid, 0.0), 4)
        chunk["vector_score"] = round(vector_score_map.get(cid, 0.0), 4)
        chunk["metadata"] = {
            "document_id": chunk.get("document_id"),
            "document_name": chunk.get("doc_name"),
            "document_type": chunk.get("document_type"),
            "page_number": chunk.get("page_number"),
            "section": chunk.get("section_name"),
            "source_path": chunk.get("source_path"),
            "upload_timestamp": chunk.get("upload_timestamp"),
            "document_version": chunk.get("doc_version"),
            "content_hash": chunk.get("doc_hash"),
            "ocr_used": chunk.get("ocr_used"),
            "ocr_confidence": chunk.get("ocr_confidence"),
        }
        result.append(chunk)

    return result


def hybrid_search(
    query: str,
    query_embedding: List[float],
    conn,
    top_k: int = 8,
    bm25_top_k: int = 10,
    vector_top_k: int = 10,
) -> Tuple[List[Dict], Dict]:
    """
    Full hybrid retrieval pipeline:
      1. Load all indexed chunks from DB (real uploaded documents only)
      2. BM25 search
      3. Dense vector search
      4. RRF fusion
      5. Return top_k candidates

    Returns:
        (fused_chunks, debug_info)
    """
    chunks = load_all_chunks(conn)

    debug_info = {
        "total_chunks_in_db": len(chunks),
        "bm25_results": [],
        "vector_results": [],
        "rrf_results": [],
    }

    if not chunks:
        return [], debug_info

    bm25_results = bm25_search(query, chunks, top_k=bm25_top_k)
    vector_results = vector_search(query_embedding, chunks, top_k=vector_top_k)

    # Populate debug info
    debug_info["bm25_results"] = [
        {
            "chunk_id": c["id"],
            "doc_name": c.get("doc_name"),
            "page": c.get("page_number"),
            "score": round(s, 4),
            "snippet": c["content"][:120],
        }
        for s, c in bm25_results
    ]
    debug_info["vector_results"] = [
        {
            "chunk_id": c["id"],
            "doc_name": c.get("doc_name"),
            "page": c.get("page_number"),
            "score": round(s, 4),
            "snippet": c["content"][:120],
        }
        for s, c in vector_results
    ]

    fused = rrf_fusion(bm25_results, vector_results)

    debug_info["rrf_results"] = [
        {
            "chunk_id": c["id"],
            "doc_name": c.get("doc_name"),
            "page": c.get("page_number"),
            "rrf_score": c.get("rrf_score"),
            "bm25_rank": c.get("bm25_rank"),
            "vector_rank": c.get("vector_rank"),
        }
        for c in fused[:top_k]
    ]

    return fused[:top_k], debug_info
