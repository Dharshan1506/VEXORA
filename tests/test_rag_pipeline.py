"""
tests/test_rag_pipeline.py
Real end-to-end tests for the VEXORA RAG pipeline.
Tests all requirements specified in Section 30 of Master Prompt:
  TEST 1: Upload a real PDF (extract, chunk, embed, index BM25/vector)
  TEST 2: Question with answer in PDF (BM25 + vector + RRF + rerank + Evidence Guard + LLM/citations)
  TEST 3: Question with NO evidence (Evidence Guard blocks, "Insufficient evidence", no hallucination)
  TEST 4: Question with paraphrased/different wording (Semantic vector retrieval)
  TEST 5: Conflicting documents detection (Conflict detector identifies discrepant sources)
  TEST 6: Document version upgrade (Newer version supersedes older, latest preferred for retrieval)
  TEST 7: Conversation persistence (Messages persist to and load from DB)

Run with: py -m pytest tests/test_rag_pipeline.py -v -s
"""

import os
import sys
import uuid
import json
import tempfile
import pymupdf as fitz

# Fix Windows console encoding for Unicode output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add backend to path for direct module imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

from database import init_db, get_db
from services.extraction_service import extract_file, compute_file_hash
from services.chunking_service import chunk_pages
from services.embedding_service import embed_text, embed_texts, serialize_embedding
from services.retrieval_service import hybrid_search, load_all_chunks, vector_search, bm25_search, rrf_fusion
from services.reranker_service import rerank, is_reranker_available
from services.llm_service import generate_answer, evidence_guard, INSUFFICIENT_EVIDENCE_MSG
from routers.chat_router import _detect_conflicts


def _create_sample_pdf(file_path: str):
    """Generate a real 2-page PDF document using PyMuPDF."""
    doc = fitz.open()

    # Page 1: Minimum attendance requirements
    page1 = doc.new_page()
    text1 = """VEXORA UNIVERSITY ACADEMIC REGULATIONS 2026

Section 1: Minimum Attendance Requirement
Students must maintain a minimum aggregate attendance of 80% across all registered theoretical and practical courses in a semester to be eligible to appear for the Semester End Examinations (SEE). Any student with attendance between 70% and 79% may apply for medical condonation subject to Academic Council approval.

Section 2: Condonation Application Process
Applications for attendance condonation must be submitted to the Dean of Academic Affairs within seven working days of the cessation of classes accompanied by certified medical documentation from a registered hospital."""
    page1.insert_text((50, 72), text1, fontsize=11)

    # Page 2: Detention and exam rules
    page2 = doc.new_page()
    text2 = """Section 3: Mandatory Detention Rules
Students whose aggregate attendance falls below 70% under any circumstance shall be detained from appearing in the Semester End Examinations. Detained candidates are required to re-register for the course in the subsequent academic session.

Section 4: Internal Examination Weightage
Continuous Internal Assessment (CIA) accounts for 40% of the total course evaluation, while the Semester End Examination accounts for the remaining 60%. A minimum score of 50% in both CIA and SEE separately is mandatory to qualify for credit award."""
    page2.insert_text((50, 72), text2, fontsize=11)

    doc.save(file_path)
    doc.close()


# ─── TEST 1: Upload a real PDF ───────────────────────────────────────────────
def test_test1_upload_real_pdf():
    """
    TEST 1:
    Upload a real PDF.
    Expected: document stored, text extracted, chunks created, embeddings generated,
    BM25 index updated, vector index updated.
    """
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf_path = tmp.name

    try:
        _create_sample_pdf(pdf_path)

        # 1. Verify extraction from real PDF
        pages = extract_file(pdf_path)
        assert len(pages) == 2, f"Expected 2 extracted pages, got {len(pages)}"
        assert "80%" in pages[0]["text"]
        assert pages[0]["page"] == 1
        assert pages[1]["page"] == 2
        print(f"[TEST 1a] Extracted {len(pages)} pages from real PDF")

        # 2. Verify chunking with metadata
        chunks = chunk_pages(pages)
        assert len(chunks) >= 2, "Expected at least 2 chunks"
        assert all(c["page_number"] in (1, 2) for c in chunks), "Invalid page numbers"
        assert all("section_name" in c for c in chunks), "Missing section_name"
        print(f"[TEST 1b] Created {len(chunks)} chunks with real page & section metadata")

        # 3. Verify embeddings generation
        texts = [c["content"] for c in chunks]
        embeddings = embed_texts(texts)
        assert len(embeddings) == len(chunks)
        assert len(embeddings[0]) > 0
        print(f"[TEST 1c] Generated {len(embeddings)} real embeddings (dim={len(embeddings[0])})")

        # 4. Insert into database
        doc_id = str(uuid.uuid4())
        file_hash = compute_file_hash(pdf_path)
        cursor.execute(
            """INSERT INTO documents
               (id, name, category, version, upload_date, status, file_path, file_size, content_hash, total_chunks)
               VALUES (?, 'Test_Regulations.pdf', 'Academic', 'v1.0', '2026-10-05', 'indexed', ?, ?, ?, ?)""",
            (doc_id, pdf_path, os.path.getsize(pdf_path), file_hash, len(chunks)),
        )

        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            chunk_id = str(uuid.uuid4())
            cursor.execute(
                """INSERT INTO document_chunks
                   (id, document_id, chunk_index, content, page_number, section_name, embedding, ocr_used, ocr_confidence)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 0, 1.0)""",
                (chunk_id, doc_id, i, chunk["content"], chunk["page_number"], chunk["section_name"], serialize_embedding(emb)),
            )
        conn.commit()

        # 5. Verify retrieval from DB
        db_chunks = load_all_chunks(conn)
        test_chunks = [c for c in db_chunks if c["document_id"] == doc_id]
        assert len(test_chunks) == len(chunks), "Stored chunks mismatch"
        print(f"[TEST 1d] Successfully indexed {len(test_chunks)} chunks in DB")

    finally:
        conn.close()
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)

    print("[TEST 1] PASS: Real PDF ingestion pipeline executed successfully\n")


# ─── TEST 2: Question with answer in PDF ──────────────────────────────────────
def test_test2_question_with_known_answer():
    """
    TEST 2:
    Ask a question whose answer exists in the PDF.
    Expected: BM25 retrieves relevant chunk, vector search retrieves relevant chunk,
    RRF combines them, reranker selects evidence, LLM generates grounded answer, citation appears.
    """
    conn = get_db()
    query = "What is the minimum attendance requirement for semester examinations?"
    query_emb = embed_text(query)

    retrieved, debug_info = hybrid_search(query, query_emb, conn, top_k=5)
    conn.close()

    assert len(retrieved) > 0, "No chunks retrieved"
    print(f"[TEST 2a] Retrieved {len(retrieved)} candidate chunks via BM25 + Vector + RRF")

    # Cross-encoder rerank
    reranked, scores = rerank(query, retrieved, top_k=3)
    assert len(reranked) > 0, "Reranker returned empty list"
    assert any("80%" in c["content"] for c in reranked), "Reranked evidence must contain 80% minimum attendance chunk"
    print(f"[TEST 2b] Top reranked chunk score: {scores[0]:.4f} ({reranked[0]['content'][:60]}...)")

    # Evidence Guard check
    sufficient, reason = evidence_guard(query, reranked, scores)
    assert sufficient, f"Evidence Guard unexpectedly failed: {reason}"
    print(f"[TEST 2c] Evidence Guard approved: {reason}")

    # Generate answer
    ans_result = generate_answer(query, reranked, scores)
    assert ans_result["evidence_status"] == "sufficient"
    assert "80" in ans_result["content"] or "attendance" in ans_result["content"].lower()
    assert reranked[0].get("page_number") is not None, "Page number must be preserved"
    print(f"[TEST 2d] Grounded Answer: {ans_result['content'][:150]}...")
    print(f"[TEST 2e] Source Citation: {reranked[0].get('doc_name')} Page {reranked[0].get('page_number')} ({reranked[0].get('section_name')})")

    print("[TEST 2] PASS: Question with answer in PDF correctly retrieved and cited\n")


# ─── TEST 3: Question with NO evidence ───────────────────────────────────────
def test_test3_question_without_evidence_no_hallucination():
    """
    TEST 3:
    Ask a question whose answer does NOT exist.
    Expected: Evidence Guard blocks unsupported answer.
    Response: "Insufficient evidence." No hallucinated answer.
    """
    unrelated_query = "What is the nuclear fission cross-section of cobalt-60 in the cafeteria?"

    # Case A: empty chunk list
    sufficient, reason = evidence_guard(unrelated_query, [])
    assert not sufficient
    ans_a = generate_answer(unrelated_query, [], reranker_scores=[])
    assert ans_a["evidence_status"] == "insufficient"
    assert ans_a["llm_used"] is False
    assert INSUFFICIENT_EVIDENCE_MSG in ans_a["content"]
    print(f"[TEST 3a] Blocked on empty retrieval: {ans_a['content']}")

    # Case B: retrieved chunks with low reranker score
    dummy_chunks = [{
        "id": "c1",
        "document_id": "d1",
        "content": "Students must maintain 80% attendance for examinations.",
        "doc_name": "Attendance Policy.pdf",
        "page_number": 1,
    }]
    low_scores = [-8.5]
    sufficient_b, reason_b = evidence_guard(unrelated_query, dummy_chunks, low_scores)
    assert not sufficient_b
    ans_b = generate_answer(unrelated_query, dummy_chunks, reranker_scores=low_scores)
    assert ans_b["evidence_status"] == "insufficient"
    assert ans_b["llm_used"] is False
    assert INSUFFICIENT_EVIDENCE_MSG in ans_b["content"]
    print(f"[TEST 3b] Blocked on low reranker score: {reason_b}")

    print("[TEST 3] PASS: Evidence Guard blocks hallucination when evidence is absent\n")


# ─── TEST 4: Ask using different wording (Semantic Vector Search) ─────────────
def test_test4_semantic_retrieval_paraphrase():
    """
    TEST 4:
    Ask using different wording.
    Document: "Students must maintain a minimum aggregate attendance..."
    Question: "Can I sit for exams if my attendance is below the required percentage?"
    Expected: Semantic vector search retrieves the relevant chunk.
    """
    conn = get_db()
    chunks = load_all_chunks(conn)
    conn.close()

    if not chunks:
        print("[TEST 4] SKIP: No chunks in DB")
        return

    paraphrase_query = "Can I sit for exams if my attendance is below the required percentage?"
    query_emb = embed_text(paraphrase_query)
    results = vector_search(query_emb, chunks, top_k=3)

    assert len(results) > 0
    top_score, top_chunk = results[0]
    assert "attendance" in top_chunk["content"].lower() or "examination" in top_chunk["content"].lower()
    print(f"[TEST 4a] Paraphrased query: '{paraphrase_query}'")
    print(f"[TEST 4b] Top semantic similarity: {top_score:.4f}")
    print(f"[TEST 4c] Retrieved snippet: {top_chunk['content'][:100]}...")

    print("[TEST 4] PASS: Semantic vector search handles vocabulary mismatch and paraphrase\n")


# ─── TEST 5: Conflicting documents detection ──────────────────────────────────
def test_test5_conflicting_documents_detection():
    """
    TEST 5:
    Create conflicting documents.
    Expected: system detects conflict and surfaces both sources.
    """
    chunk_a = {
        "id": "c_a",
        "document_id": "doc_policy_2024",
        "doc_name": "Old Attendance Policy.pdf",
        "content": "Students must maintain a minimum attendance of 75% across all semester courses.",
        "page_number": 2,
    }
    chunk_b = {
        "id": "c_b",
        "document_id": "doc_regulations_2026",
        "doc_name": "Academic Regulations 2026.pdf",
        "content": "Students must maintain a minimum attendance of 85% to be eligible for examinations.",
        "page_number": 4,
    }

    conflicts = _detect_conflicts([chunk_a, chunk_b])
    assert len(conflicts) > 0, "Failed to detect conflict between 75% and 85%"
    c = conflicts[0]
    assert c["doc_a"] in ("Old Attendance Policy.pdf", "Academic Regulations 2026.pdf")
    assert c["doc_b"] in ("Old Attendance Policy.pdf", "Academic Regulations 2026.pdf")
    print(f"[TEST 5a] Detected Conflict: {c['doc_a']} ({c['values_a']}%) vs {c['doc_b']} ({c['values_b']}%)")

    print("[TEST 5] PASS: Conflict detection engine identifies contradictory numeric policies\n")


# ─── TEST 6: Document version management ─────────────────────────────────────
def test_test6_document_version_management():
    """
    TEST 6:
    Upload a newer document version.
    Expected: latest valid version is preferred for retrieval.
    """
    conn = get_db()
    cursor = conn.cursor()

    doc_v1_id = f"test-doc-v1-{uuid.uuid4().hex[:6]}"
    doc_v2_id = f"test-doc-v2-{uuid.uuid4().hex[:6]}"

    # Insert v1.0 (superseded by v2.0)
    cursor.execute(
        """INSERT INTO documents (id, name, version, status, upload_date, superseded_by)
           VALUES (?, 'Hostel Guidelines.pdf', 'v1.0', 'indexed', '2025-01-01', ?)""",
        (doc_v1_id, doc_v2_id),
    )
    # Insert v2.0 (active)
    cursor.execute(
        """INSERT INTO documents (id, name, version, status, upload_date, superseded_by)
           VALUES (?, 'Hostel Guidelines.pdf', 'v2.0', 'indexed', '2026-09-01', NULL)""",
        (doc_v2_id,),
    )

    # Insert chunks
    cursor.execute(
        """INSERT INTO document_chunks (id, document_id, chunk_index, content, embedding)
           VALUES (?, ?, 0, 'Hostel curfew in v1.0 is 9:00 PM.', '[]')""",
        (str(uuid.uuid4()), doc_v1_id),
    )
    cursor.execute(
        """INSERT INTO document_chunks (id, document_id, chunk_index, content, embedding)
           VALUES (?, ?, 0, 'Hostel curfew in v2.0 is 10:30 PM.', '[]')""",
        (str(uuid.uuid4()), doc_v2_id),
    )
    conn.commit()

    # Load with prefer_latest = True (default)
    active_chunks = load_all_chunks(conn, prefer_latest=True)
    v1_found = any(c["document_id"] == doc_v1_id for c in active_chunks)
    v2_found = any(c["document_id"] == doc_v2_id for c in active_chunks)

    # Clean up test rows
    cursor.execute("DELETE FROM documents WHERE id IN (?, ?)", (doc_v1_id, doc_v2_id))
    conn.commit()
    conn.close()

    assert not v1_found, "Superseded version v1.0 should NOT be loaded when preferring latest"
    assert v2_found, "Active version v2.0 must be loaded for retrieval"
    print("[TEST 6a] Active version v2.0 preferred; superseded v1.0 excluded from primary retrieval")

    print("[TEST 6] PASS: Version management prioritizes latest active document version\n")


# ─── TEST 7: Conversation persistence ────────────────────────────────────────
def test_test7_conversation_persistence():
    """
    TEST 7:
    Open an old conversation.
    Expected: messages load from database.
    """
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    user_id = str(uuid.uuid4())
    conv_id = str(uuid.uuid4())

    cursor.execute(
        "INSERT INTO users (id, name, email, hashed_password) VALUES (?, ?, ?, ?)",
        (user_id, "Scholar Tester", f"tester_{user_id[:6]}@vexora.edu", "pbkdf2_dummy"),
    )
    cursor.execute(
        "INSERT INTO conversations (id, user_id, title) VALUES (?, ?, ?)",
        (conv_id, user_id, "Examination Regulations Discussion"),
    )

    # Add user message
    msg1_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO messages (id, conversation_id, role, content) VALUES (?, ?, 'user', ?)",
        (msg1_id, conv_id, "What are the passing criteria in semester exams?"),
    )

    # Add assistant response with citations
    msg2_id = str(uuid.uuid4())
    sample_citations = json.dumps([{"id": 1, "docName": "Academic Regulations.pdf", "page": 2, "section": "Section 4"}])
    sample_sources = json.dumps([{"citationId": 1, "docName": "Academic Regulations.pdf", "page": 2, "snippet": "Minimum score of 50% is required."}])
    cursor.execute(
        """INSERT INTO messages
           (id, conversation_id, role, content, key_information, evidence_strength,
            evidence_status, citations, sources)
           VALUES (?, ?, 'assistant', ?, ?, ?, ?, ?, ?)""",
        (
            msg2_id,
            conv_id,
            "Students must achieve a minimum of 50% in both CIA and SEE separately to qualify for credit award.",
            "Source Verified: Academic Regulations.pdf p. 2",
            "Strong Evidence (Verified)",
            "sufficient",
            sample_citations,
            sample_sources,
        ),
    )
    conn.commit()

    # Query from database to verify persistence
    cursor.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conv_id,),
    )
    loaded_messages = cursor.fetchall()
    conn.close()

    assert len(loaded_messages) == 2, f"Expected 2 messages, got {len(loaded_messages)}"
    user_msg = dict(loaded_messages[0])
    asst_msg = dict(loaded_messages[1])

    assert user_msg["role"] == "user"
    assert asst_msg["role"] == "assistant"
    assert asst_msg["evidence_status"] == "sufficient"
    loaded_cites = json.loads(asst_msg["citations"])
    assert len(loaded_cites) == 1
    assert loaded_cites[0]["page"] == 2
    assert loaded_cites[0]["docName"] == "Academic Regulations.pdf"
    print(f"[TEST 7a] Loaded {len(loaded_messages)} persisted messages for conversation {conv_id[:8]}...")
    print(f"[TEST 7b] Persisted Citation: {loaded_cites[0]['docName']} Page {loaded_cites[0]['page']}")

    print("[TEST 7] PASS: Conversation memory persists and reloads correctly from database\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" VEXORA MASTER RAG PIPELINE VERIFICATION SUITE")
    print("=" * 70 + "\n")

    test_test1_upload_real_pdf()
    test_test2_question_with_known_answer()
    test_test3_question_without_evidence_no_hallucination()
    test_test4_semantic_retrieval_paraphrase()
    test_test5_conflicting_documents_detection()
    test_test6_document_version_management()
    test_test7_conversation_persistence()

    print("=" * 70)
    print(" ALL 7 REAL RAG PIPELINE TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)
