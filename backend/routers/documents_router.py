"""
routers/documents_router.py
Document upload, listing, viewing, and deletion.
Full processing pipeline on upload:
  receive → validate → save → compute hash → extract → chunk → embed → store → index
  + version detection + BM25 index awareness
"""

import os
import uuid
import json
import hashlib
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from database import get_db
from auth import get_current_user
from services.extraction_service import (
    extract_file, get_mime_type, EXTENSION_MAP, compute_file_hash
)
from services.chunking_service import chunk_pages
from services.embedding_service import embed_texts, serialize_embedding

router = APIRouter(prefix="/api/documents", tags=["documents"])

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "documents")
os.makedirs(STORAGE_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = set(EXTENSION_MAP.keys())
MAX_FILE_SIZE_MB = 50


@router.get("")
def list_documents(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    docs = [dict(r) for r in rows]
    return {"documents": docs}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("General"),
    version: str = Form("v1.0"),
    effective_date: str = Form(""),
    current_user: dict = Depends(get_current_user),
):
    # ── Step 1: Validate extension ────────────────────────────────────────────
    filename = file.filename or "upload"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{ext}'. "
                f"Supported: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    # ── Step 2: Read and validate size ───────────────────────────────────────
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Maximum: {MAX_FILE_SIZE_MB} MB.",
        )

    # ── Step 3: Compute content hash for version detection ───────────────────
    file_hash = hashlib.sha256(content).hexdigest()

    # ── Step 4: Check for duplicate (same hash, already indexed) ────────────
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name FROM documents WHERE content_hash = ? AND status = 'indexed'",
        (file_hash,),
    )
    existing = cursor.fetchone()
    if existing:
        conn.close()
        raise HTTPException(
            status_code=409,
            detail=(
                f"An identical document is already indexed: '{existing['name']}' (id={existing['id']}). "
                "Upload a different version or delete the existing one first."
            ),
        )

    # ── Step 5: Save file to disk ────────────────────────────────────────────
    doc_id = str(uuid.uuid4())
    safe_name = f"{doc_id}{ext}"
    file_path = os.path.join(STORAGE_DIR, safe_name)

    with open(file_path, "wb") as f:
        f.write(content)

    mime_type = get_mime_type(file_path)
    upload_date_str = date.today().isoformat()
    doc_type = ext.lstrip(".")

    # ── Step 6: Detect if this is a newer version of an existing document ────
    # Match by base name (without extension), case-insensitive
    base_name = os.path.splitext(filename)[0].strip().lower()
    cursor.execute(
        "SELECT id, name, version FROM documents WHERE status = 'indexed' ORDER BY created_at DESC"
    )
    all_docs = cursor.fetchall()
    superseded_doc_id = None
    for doc in all_docs:
        existing_base = os.path.splitext(doc["name"])[0].strip().lower()
        # Fuzzy match: same base name or one is contained in the other
        if base_name == existing_base or (
            len(base_name) > 5 and (base_name in existing_base or existing_base in base_name)
        ):
            superseded_doc_id = doc["id"]
            break

    # ── Step 7: Insert document record (status = 'processing') ───────────────
    cursor.execute(
        """INSERT INTO documents
           (id, name, category, version, upload_date, effective_date, status,
            file_path, file_size, mime_type, doc_type, uploaded_by, content_hash)
           VALUES (?, ?, ?, ?, ?, ?, 'processing', ?, ?, ?, ?, ?, ?)""",
        (
            doc_id,
            filename,
            category,
            version,
            upload_date_str,
            effective_date or None,
            file_path,
            len(content),
            mime_type,
            doc_type,
            current_user["user_id"],
            file_hash,
        ),
    )
    conn.commit()

    # Mark superseded document
    if superseded_doc_id:
        cursor.execute(
            "UPDATE documents SET superseded_by = ? WHERE id = ?",
            (doc_id, superseded_doc_id),
        )
        conn.commit()

    # ── Step 8: Extract text ──────────────────────────────────────────────────
    try:
        pages = extract_file(file_path)
    except Exception as e:
        cursor.execute(
            "UPDATE documents SET status = 'error' WHERE id = ?", (doc_id,)
        )
        conn.commit()
        conn.close()
        raise HTTPException(status_code=422, detail=f"Text extraction failed: {e}")

    if not pages:
        cursor.execute(
            "UPDATE documents SET status = 'error' WHERE id = ?", (doc_id,)
        )
        conn.commit()
        conn.close()
        raise HTTPException(
            status_code=422,
            detail=(
                "No text could be extracted from this file. "
                "For scanned PDFs, ensure Tesseract OCR is installed."
            ),
        )

    # Compute aggregate OCR stats
    ocr_used = any(p.get("ocr_used") for p in pages)
    ocr_confidences = [
        p.get("ocr_confidence", 1.0) for p in pages if p.get("ocr_used")
    ]
    avg_ocr_confidence = (
        sum(ocr_confidences) / len(ocr_confidences) if ocr_confidences else 1.0
    )

    # ── Step 9: Chunk the pages ───────────────────────────────────────────────
    chunks = chunk_pages(pages)
    if not chunks:
        cursor.execute(
            "UPDATE documents SET status = 'error' WHERE id = ?", (doc_id,)
        )
        conn.commit()
        conn.close()
        raise HTTPException(status_code=422, detail="Document produced no usable text chunks.")

    # ── Step 10: Generate embeddings (batch) ──────────────────────────────────
    texts = [c["content"] for c in chunks]
    try:
        embeddings = embed_texts(texts)
    except Exception as e:
        cursor.execute(
            "UPDATE documents SET status = 'error' WHERE id = ?", (doc_id,)
        )
        conn.commit()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {e}")

    # ── Step 11: Store chunks and embeddings in DB ────────────────────────────
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        chunk_id = str(uuid.uuid4())
        chunk_hash = hashlib.sha256(chunk["content"].encode()).hexdigest()
        chunk_ocr = chunk.get("ocr_used", False)
        chunk_ocr_conf = float(chunk.get("ocr_confidence", 1.0))
        cursor.execute(
            """INSERT INTO document_chunks
               (id, document_id, chunk_index, content, content_hash,
                page_number, section_name, ocr_used, ocr_confidence, embedding)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                chunk_id,
                doc_id,
                chunk["chunk_index"],
                chunk["content"],
                chunk_hash,
                chunk.get("page_number"),   # may be None for some doc types
                chunk.get("section_name", ""),
                int(chunk_ocr),
                chunk_ocr_conf,
                serialize_embedding(emb),
            ),
        )

    # ── Step 12: Mark document as indexed ─────────────────────────────────────
    cursor.execute(
        """UPDATE documents
           SET status = 'indexed', total_chunks = ?, ocr_used = ?, ocr_confidence = ?
           WHERE id = ?""",
        (len(chunks), int(ocr_used), avg_ocr_confidence, doc_id),
    )
    conn.commit()

    # ── Step 13: Record version history ───────────────────────────────────────
    version_id = str(uuid.uuid4())
    cursor.execute(
        """INSERT INTO document_versions (id, document_id, version, upload_date, content_hash)
           VALUES (?, ?, ?, ?, ?)""",
        (version_id, doc_id, version, upload_date_str, file_hash),
    )
    conn.commit()

    # ── Step 14: Conflict detection – check if numeric values conflict ────────
    if superseded_doc_id:
        _detect_and_store_conflicts(conn, cursor, superseded_doc_id, doc_id)

    # ── Return result ─────────────────────────────────────────────────────────
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    doc = dict(cursor.fetchone())
    conn.close()

    return {
        "message": "Document uploaded and indexed successfully.",
        "document": doc,
        "stats": {
            "pages_extracted": len(pages),
            "chunks_created": len(chunks),
            "ocr_used": ocr_used,
            "avg_ocr_confidence": round(avg_ocr_confidence, 3),
            "supersedes_document": superseded_doc_id,
            "content_hash": file_hash,
        },
    }


def _detect_and_store_conflicts(conn, cursor, doc_id_a: str, doc_id_b: str):
    """Check chunks of two documents for conflicting percentage values."""
    import re

    def get_chunks_text(doc_id):
        cursor.execute("SELECT content FROM document_chunks WHERE document_id = ?", (doc_id,))
        rows = cursor.fetchall()
        return " ".join(r["content"] for r in rows)

    text_a = get_chunks_text(doc_id_a)
    text_b = get_chunks_text(doc_id_b)

    nums_a = set(re.findall(r"\b(\d+(?:\.\d+)?)\s*%", text_a))
    nums_b = set(re.findall(r"\b(\d+(?:\.\d+)?)\s*%", text_b))

    # Conflict if they both have percentages but share none
    if nums_a and nums_b and not (nums_a & nums_b):
        conflict_id = str(uuid.uuid4())
        try:
            cursor.execute(
                """INSERT INTO document_conflicts
                   (id, document_id_a, document_id_b, conflict_type, description)
                   VALUES (?, ?, ?, 'percentage_mismatch', ?)""",
                (
                    conflict_id,
                    doc_id_a,
                    doc_id_b,
                    f"Older doc has {sorted(nums_a)}%, new doc has {sorted(nums_b)}%",
                ),
            )
            conn.commit()
        except Exception as e:
            print(f"[Conflict] Could not store conflict record: {e}")


@router.get("/conflicts")
def list_conflicts(current_user: dict = Depends(get_current_user)):
    """List all detected document conflicts."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT dc.*,
               da.name as doc_name_a,
               db.name as doc_name_b
        FROM document_conflicts dc
        LEFT JOIN documents da ON dc.document_id_a = da.id
        LEFT JOIN documents db ON dc.document_id_b = db.id
        ORDER BY dc.detected_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return {"conflicts": [dict(r) for r in rows]}


@router.get("/{doc_id}")
def get_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found.")

    # Also fetch version history
    cursor.execute(
        "SELECT * FROM document_versions WHERE document_id = ? ORDER BY created_at DESC",
        (doc_id,),
    )
    versions = [dict(v) for v in cursor.fetchall()]
    conn.close()

    return {"document": dict(row), "versions": versions}


@router.delete("/{doc_id}")
def delete_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT file_path FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found.")

    file_path = row["file_path"]
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

    return {"message": f"Document {doc_id} deleted successfully."}
