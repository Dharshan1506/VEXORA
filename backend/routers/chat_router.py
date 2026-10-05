"""
routers/chat_router.py
Full RAG pipeline:
  authenticate → save user msg → embed query
  → BM25 + vector search → RRF → rerank → Evidence Guard
  → LLM (if sufficient) → citations → conflict detection
  → save assistant msg + retrieval log → respond

Debug mode: set DEBUG_RETRIEVAL=true in backend/.env to log full pipeline details.
"""

import os
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import get_db
from auth import get_current_user
from services.embedding_service import embed_text
from services.retrieval_service import hybrid_search
from services.reranker_service import rerank
from services.llm_service import generate_answer, INSUFFICIENT_EVIDENCE_MSG

router = APIRouter(prefix="/api/chat", tags=["chat"])

DEBUG_RETRIEVAL = os.environ.get("DEBUG_RETRIEVAL", "false").lower() == "true"


class ChatRequest(BaseModel):
    query: Optional[str] = None
    message: Optional[str] = None
    conversation_id: Optional[str] = None
    debug: bool = False   # client can request debug info per-query


def _detect_conflicts(reranked_chunks):
    """
    Detect if two chunks from different documents have contradictory numerical
    values for the same key terms (e.g. attendance 75% vs 80%).
    Returns a list of conflict descriptions.
    """
    conflicts = []
    import re

    # Extract (doc_id, doc_name, number) triples for percent values
    doc_numbers = {}  # doc_id → set of percentages mentioned
    for chunk in reranked_chunks:
        doc_id = chunk.get("document_id", "")
        doc_name = chunk.get("doc_name", "") or chunk.get("document_name", "")
        numbers = set(re.findall(r"\b(\d+(?:\.\d+)?)\s*%", chunk["content"]))
        if numbers:
            if doc_id not in doc_numbers:
                doc_numbers[doc_id] = {"doc_name": doc_name, "values": set()}
            doc_numbers[doc_id]["values"].update(numbers)

    doc_ids = list(doc_numbers.keys())
    for i in range(len(doc_ids)):
        for j in range(i + 1, len(doc_ids)):
            id_a, id_b = doc_ids[i], doc_ids[j]
            values_a = doc_numbers[id_a]["values"]
            values_b = doc_numbers[id_b]["values"]
            differing = values_a.symmetric_difference(values_b)
            if differing and values_a & values_b == set():
                # No shared values but both have percentages — potential conflict
                conflicts.append({
                    "doc_a": doc_numbers[id_a]["doc_name"],
                    "doc_id_a": id_a,
                    "values_a": list(values_a),
                    "doc_b": doc_numbers[id_b]["doc_name"],
                    "doc_id_b": id_b,
                    "values_b": list(values_b),
                    "note": "Documents cite different percentage values — verify which is current.",
                })

    return conflicts


@router.post("")
def chat(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    user_query = (req.message or req.query or "").strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query/message cannot be empty.")

    emit_debug = DEBUG_RETRIEVAL or req.debug
    conn = get_db()
    cursor = conn.cursor()

    # ─── 1. Get or create conversation ─────────────────────────────────────────
    conv_id = req.conversation_id
    if not conv_id:
        conv_id = str(uuid.uuid4())
        title = user_query[:80]
        cursor.execute(
            "INSERT INTO conversations (id, user_id, title) VALUES (?, ?, ?)",
            (conv_id, current_user["user_id"], title),
        )
        conn.commit()
    else:
        cursor.execute(
            "SELECT id FROM conversations WHERE id = ? AND user_id = ?",
            (conv_id, current_user["user_id"]),
        )
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Conversation not found.")

    # ─── 2. Save user message ───────────────────────────────────────────────────
    user_msg_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO messages (id, conversation_id, role, content) VALUES (?, ?, 'user', ?)",
        (user_msg_id, conv_id, user_query),
    )
    conn.commit()

    # ─── 3. Generate query embedding ────────────────────────────────────────────
    try:
        query_embedding = embed_text(user_query)
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}")

    # ─── 4. Hybrid retrieval: BM25 + vector + RRF ───────────────────────────────
    retrieved, retrieval_debug = hybrid_search(
        user_query, query_embedding, conn, top_k=8, bm25_top_k=10, vector_top_k=10
    )

    if emit_debug:
        print("\n" + "=" * 60)
        print(f"[DEBUG] QUERY: {user_query}")
        print(f"[DEBUG] Total chunks in DB: {retrieval_debug['total_chunks_in_db']}")
        print(f"[DEBUG] BM25 top results: {json.dumps(retrieval_debug['bm25_results'][:3], indent=2)}")
        print(f"[DEBUG] Vector top results: {json.dumps(retrieval_debug['vector_results'][:3], indent=2)}")
        print(f"[DEBUG] RRF results: {json.dumps(retrieval_debug['rrf_results'][:5], indent=2)}")

    # ─── 5. Cross-encoder rerank ────────────────────────────────────────────────
    reranked, reranker_scores = rerank(user_query, retrieved, top_k=5)

    reranker_debug = [
        {
            "chunk_id": c["id"],
            "doc_name": c.get("doc_name"),
            "page": c.get("page_number"),
            "reranker_score": round(reranker_scores[i], 4) if i < len(reranker_scores) else None,
            "snippet": c["content"][:120],
        }
        for i, c in enumerate(reranked)
    ]

    if emit_debug:
        print(f"[DEBUG] Reranker results: {json.dumps(reranker_debug, indent=2)}")

    # ─── 6. LLM generation (Evidence Guard inside) ──────────────────────────────
    llm_result = generate_answer(user_query, reranked, reranker_scores)
    answer_content = llm_result["content"]
    evidence_status = llm_result["evidence_status"]

    if emit_debug:
        print(f"[DEBUG] Evidence Guard: {evidence_status} / reason: {llm_result.get('evidence_guard_reason')}")
        print(f"[DEBUG] LLM used: {llm_result['llm_used']}")
        print(f"[DEBUG] Answer (first 200 chars): {answer_content[:200]}")
        print("=" * 60 + "\n")

    # ─── 7. Build citations & sources ────────────────────────────────────────────
    citations = []
    sources = []

    # Only build citations if evidence was sufficient
    if evidence_status == "sufficient" and reranked:
        for i, chunk in enumerate(reranked, start=1):
            score_val = reranker_scores[i - 1] if i - 1 < len(reranker_scores) else 0.0
            # Sigmoid-normalise reranker score to [0,1] for display
            import math
            normalised_score = round(1.0 / (1.0 + math.exp(-score_val)), 3)
            doc_name = chunk.get("doc_name") or chunk.get("document_name") or "Unknown"

            citations.append({
                "id": i,
                "document_id": chunk.get("document_id"),
                "document_name": doc_name,
                "docName": doc_name,
                "page": chunk.get("page_number"),
                "section": chunk.get("section_name", "") or chunk.get("section", "") or "General",
                "version": chunk.get("doc_version", "") or chunk.get("document_version", ""),
            })
            sources.append({
                "citationId": i,
                "document_id": chunk.get("document_id"),
                "document_name": doc_name,
                "docName": doc_name,
                "page": chunk.get("page_number"),
                "section": chunk.get("section_name", "") or chunk.get("section", "") or "General",
                "version": chunk.get("doc_version", "") or chunk.get("document_version", ""),
                "snippet": chunk["content"][:500],
                "score": normalised_score,
                "rerankerScore": round(score_val, 4),
                "chunkId": chunk["id"],
                "documentId": chunk["document_id"],
                "rrf_score": chunk.get("rrf_score"),
                "bm25_rank": chunk.get("bm25_rank"),
                "vector_rank": chunk.get("vector_rank"),
            })

    # ─── 8. Conflict detection ────────────────────────────────────────────────
    conflicts = _detect_conflicts(reranked) if reranked else []
    if conflicts and evidence_status == "sufficient":
        conflict_note = "\n\n⚠️ **Conflicting Information Detected:**\n"
        for conflict in conflicts:
            conflict_note += (
                f"- **{conflict['doc_a']}** cites {conflict['values_a']}%"
                f" vs **{conflict['doc_b']}** cites {conflict['values_b']}%. "
                f"{conflict['note']}\n"
            )
        answer_content += conflict_note

    # ─── 9. Build response metadata ──────────────────────────────────────────────
    if evidence_status == "sufficient" and reranked:
        top = reranked[0]
        page_str = f" p. {top.get('page_number')}" if top.get("page_number") is not None else ""
        key_info = (
            f"Source Verified: {top.get('doc_name')}{page_str}"
            f"{' (' + top.get('doc_version') + ')' if top.get('doc_version') else ''}"
        )
        evidence_strength = (
            "Strong Evidence (Verified)"
            if llm_result["llm_used"]
            else "Evidence Retrieved (LLM not configured)"
        )
    else:
        key_info = "Insufficient evidence in uploaded documents."
        evidence_strength = "Insufficient Evidence"

    # ─── 10. Build debug_info for storage ────────────────────────────────────────
    debug_info_payload = None
    if emit_debug:
        debug_info_payload = json.dumps({
            "retrieval": retrieval_debug,
            "reranker": reranker_debug,
            "evidence_status": evidence_status,
            "evidence_guard_reason": llm_result.get("evidence_guard_reason"),
            "llm_used": llm_result["llm_used"],
            "conflicts": conflicts,
        })

    # ─── 11. Save assistant message ───────────────────────────────────────────────
    asst_msg_id = str(uuid.uuid4())
    cursor.execute(
        """INSERT INTO messages
           (id, conversation_id, role, content, key_information, evidence_strength,
            evidence_status, citations, sources, debug_info)
           VALUES (?, ?, 'assistant', ?, ?, ?, ?, ?, ?, ?)""",
        (
            asst_msg_id,
            conv_id,
            answer_content,
            key_info,
            evidence_strength,
            evidence_status,
            json.dumps(citations),
            json.dumps(sources),
            debug_info_payload,
        ),
    )
    conn.commit()

    # ─── 12. Save retrieval log ───────────────────────────────────────────────────
    log_id = str(uuid.uuid4())
    cursor.execute(
        """INSERT INTO retrieval_logs
           (id, message_id, query, bm25_results, vector_results, rrf_results,
            reranker_results, evidence_status, evidence_threshold, top_scores, llm_used)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            log_id,
            asst_msg_id,
            user_query,
            json.dumps(retrieval_debug.get("bm25_results", [])),
            json.dumps(retrieval_debug.get("vector_results", [])),
            json.dumps(retrieval_debug.get("rrf_results", [])),
            json.dumps(reranker_debug),
            evidence_status,
            float(os.environ.get("EVIDENCE_SCORE_THRESHOLD", "0.15")),
            json.dumps(reranker_scores[:5] if reranker_scores else []),
            int(llm_result["llm_used"]),
        ),
    )
    conn.commit()
    conn.close()

    # ─── 13. Return response ──────────────────────────────────────────────────────
    response = {
        "conversation_id": conv_id,
        "query": user_query,
        "message": user_query,
        "evidence_status": evidence_status,
        "evidenceStatus": evidence_status,
        "sources": sources,
        "citations": citations,
        "answer_text": answer_content,
        "answer": {
            "role": "assistant",
            "content": answer_content,
            "keyInformation": key_info,
            "evidenceStrength": evidence_strength,
            "evidenceStatus": evidence_status,
            "citations": citations,
            "sources": sources,
            "llm_used": llm_result["llm_used"],
            "conflicts": conflicts,
        },
    }

    if emit_debug:
        response["debug"] = {
            "total_chunks_in_db": retrieval_debug["total_chunks_in_db"],
            "bm25_top": retrieval_debug["bm25_results"][:5],
            "vector_top": retrieval_debug["vector_results"][:5],
            "rrf_top": retrieval_debug["rrf_results"][:5],
            "reranker": reranker_debug,
            "evidence_guard_reason": llm_result.get("evidence_guard_reason"),
            "fallback_reason": llm_result.get("fallback_reason"),
        }

    return response
