"""
routers/documents_router.py
Document upload, listing, filtering, viewing, deletion, and real Policy Compare.
Full processing pipeline on upload:
  receive → validate → save → compute hash → extract → chunk → embed → store → index
  + version detection + category classification + conflict detection
"""

import os
import re
import uuid
import json
import hashlib
from datetime import date
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse

from database import get_db
from auth import get_current_user
from services.extraction_service import (
    extract_file, get_mime_type, EXTENSION_MAP, compute_file_hash
)
from services.chunking_service import chunk_pages
from services.embedding_service import embed_texts, serialize_embedding
from services.policy_compare_service import compare_policies

router = APIRouter(prefix="/api/documents", tags=["documents"])

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "documents")
os.makedirs(STORAGE_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = set(EXTENSION_MAP.keys())
MAX_FILE_SIZE_MB = 50

VALID_CATEGORIES = ["Academic", "Examination", "Hostel", "Placement", "Rules", "General"]


def _classify_category(filename: str, text_sample: str, user_cat: str = "") -> str:
    """
    Determine category in preferred order:
      1. User-selected category (if valid and not 'General')
      2. Content / filename heuristic classification
      3. User selection ('General')
      4. Fallback: 'General'
    """
    if user_cat and user_cat in VALID_CATEGORIES and user_cat != "General":
        return user_cat

    combined = f"{filename} {text_sample}".lower()

    if any(k in combined for k in ["examination", "exam schedule", "hall ticket", "revaluation", "grade card", "evaluation scheme", "arrear"]):
        return "Examination"
    if any(k in combined for k in ["hostel", "mess", "warden", "room allotment", "inmates"]):
        return "Hostel"
    if any(k in combined for k in ["placement", "campus recruitment", "internship", "package", "recruiter", "cgpa cutoff", "training & placement", "job offer"]):
        return "Placement"
    if any(k in combined for k in ["disciplinary", "ragging", "code of conduct", "penalty", "detention rules", "university rules"]):
        return "Rules"
    if any(k in combined for k in ["curriculum", "syllabus", "academic regulations", "credit system", "semester", "undergraduate", "postgraduate", "attendance", "b.e", "b.tech"]):
        return "Academic"

    if user_cat in VALID_CATEGORIES:
        return user_cat
    return "General"


class CompareRequest(BaseModel):
    source_document_id: str
    target_document_id: str


# ── 1. List Documents with real Category filtering ───────────────────────────
@router.get("")
def list_documents(
    category: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    conn = get_db()
    cursor = conn.cursor()

    if category and category.strip() and category.strip().lower() != "all":
        cursor.execute(
            """SELECT id, name, category, version, upload_date, effective_date, status,
                      file_size, mime_type, doc_type, total_chunks, uploaded_by,
                      content_hash, ocr_used, ocr_confidence, superseded_by, created_at
               FROM documents
               WHERE LOWER(category) = LOWER(?)
               ORDER BY created_at DESC""",
            (category.strip(),),
        )
    else:
        cursor.execute(
            """SELECT id, name, category, version, upload_date, effective_date, status,
                      file_size, mime_type, doc_type, total_chunks, uploaded_by,
                      content_hash, ocr_used, ocr_confidence, superseded_by, created_at
               FROM documents
               ORDER BY created_at DESC"""
        )

    rows = cursor.fetchall()
    conn.close()

    docs = []
    for r in rows:
        d = dict(r)
        d["indexed"] = (d.get("status") == "indexed")
        d["chunk_count"] = d.get("total_chunks", 0)
        d["uploaded_at"] = d.get("upload_date") or (d.get("created_at") or "")[:10]
        docs.append(d)

    return {"documents": docs}


# ── 2. List Versions for Compare Dropdowns ───────────────────────────────────
@router.get("/versions")
def list_document_versions(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, name, version, category, upload_date, total_chunks, status, content_hash
           FROM documents
           WHERE status = 'indexed'
           ORDER BY name ASC, version DESC"""
    )
    rows = cursor.fetchall()
    conn.close()
    return {"versions": [dict(r) for r in rows]}


# ── 3. Real Policy Compare API ───────────────────────────────────────────────
@router.post("/compare")
def compare_policies_endpoint(
    req: CompareRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Compare two real documents from the database.
    Extracts clauses, numerical shifts, additions and deletions with exact page citations.
    """
    if not req.source_document_id or not req.target_document_id:
        raise HTTPException(status_code=400, detail="Both source_document_id and target_document_id are required.")

    conn = get_db()
    try:
        result = compare_policies(req.source_document_id, req.target_document_id, conn)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy comparison failed: {e}")
    finally:
        conn.close()


# ── 4. Suggested Queries (Evidence-Aware) ────────────────────────────────────
@router.get("/suggested-queries")
def get_suggested_queries(current_user: dict = Depends(get_current_user)):
    """
    Dynamically generates discover queries based on REAL indexed documents.
    Cards indicate whether real grounding evidence exists in the vault.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, category, status FROM documents WHERE status = 'indexed'")
    docs = [dict(r) for r in cursor.fetchall()]

    # Check which topics have real evidence in document chunks
    cursor.execute("""
        SELECT DISTINCT dc.document_id, d.name, d.category,
               LOWER(dc.content) as content
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE d.status = 'indexed'
    """)
    chunk_samples = cursor.fetchall()
    conn.close()

    has_attendance = False
    attendance_doc = None
    has_exam = False
    exam_doc = None
    has_placement = False
    placement_doc = None
    has_regulations = False
    regulations_doc = None
    has_hostel = False
    hostel_doc = None

    for r in chunk_samples:
        content = r["content"]
        dname = r["name"]
        if not has_attendance and ("attendance" in content or "condonation" in content):
            has_attendance = True
            attendance_doc = dname
        if not has_exam and ("internal assessment" in content or "cia" in content or "examination" in content or "evaluation" in content):
            has_exam = True
            exam_doc = dname
        if not has_placement and ("placement" in content or "recruitment" in content or "cgpa" in content):
            has_placement = True
            placement_doc = dname
        if not has_regulations and ("academic regulations" in content or "credit system" in content or "curriculum" in content):
            has_regulations = True
            regulations_doc = dname
        if not has_hostel and ("hostel" in content or "mess" in content or "warden" in content):
            has_hostel = True
            hostel_doc = dname

    suggestions = [
        {
            "id": "attendance",
            "title": "Attendance Policy",
            "text": "What is the minimum attendance requirement for semester exams?",
            "has_evidence": has_attendance,
            "badge": "Verified Evidence" if has_attendance else "Suggested Query",
            "source_doc": attendance_doc,
            "category": "Academic",
        },
        {
            "id": "exam",
            "title": "Internal Exams & Evaluation",
            "text": "What is the weightage of Continuous Internal Assessment and end semester exams?",
            "has_evidence": has_exam,
            "badge": "Verified Evidence" if has_exam else "Suggested Query",
            "source_doc": exam_doc,
            "category": "Examination" if has_exam else "Academic",
        },
        {
            "id": "regulations",
            "title": "Academic Regulations",
            "text": "What are the key policy requirements in the uploaded academic regulations?",
            "has_evidence": has_regulations or bool(docs),
            "badge": "Verified Evidence" if (has_regulations or docs) else "Suggested Query",
            "source_doc": regulations_doc or (docs[0]["name"] if docs else None),
            "category": "Academic",
        },
        {
            "id": "placement",
            "title": "Placement Rules",
            "text": "What CGPA and documents are required for campus placement eligibility?",
            "has_evidence": has_placement,
            "badge": "Verified Evidence" if has_placement else "Suggested Query (No Vault Doc)",
            "source_doc": placement_doc,
            "category": "Placement",
        },
    ]

    if has_hostel:
        suggestions.append({
            "id": "hostel",
            "title": "Hostel Guidelines",
            "text": "What are the hostel allotment guidelines and mess regulations?",
            "has_evidence": True,
            "badge": "Verified Evidence",
            "source_doc": hostel_doc,
            "category": "Hostel",
        })

    return {"suggestions": suggestions}


# ── 5. Document Upload Pipeline ──────────────────────────────────────────────
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("General"),
    version: str = Form("v1.0"),
    effective_date: str = Form(""),
    current_user: dict = Depends(get_current_user),
):
    filename = file.filename or "upload"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Maximum: {MAX_FILE_SIZE_MB} MB.",
        )

    # SHA-256 Content Hash for duplicate detection
    file_hash = hashlib.sha256(content).hexdigest()

    conn = get_db()
    cursor = conn.cursor()

    # Exact duplicate check
    cursor.execute(
        "SELECT id, name FROM documents WHERE content_hash = ? AND status = 'indexed'",
        (file_hash,),
    )
    existing_duplicate = cursor.fetchone()
    if existing_duplicate:
        conn.close()
        raise HTTPException(
            status_code=409,
            detail=(
                f"Duplicate document detected: '{existing_duplicate['name']}' with identical content is already indexed in the Knowledge Vault. "
                "Upload an updated version or delete the existing document first."
            ),
        )

    # Save to disk
    doc_id = str(uuid.uuid4())
    safe_name = f"{doc_id}{ext}"
    file_path = os.path.join(STORAGE_DIR, safe_name)

    with open(file_path, "wb") as f:
        f.write(content)

    mime_type = get_mime_type(file_path)
    upload_date_str = date.today().isoformat()
    doc_type = ext.lstrip(".")

    # Version upgrade detection (same base name)
    base_name = os.path.splitext(filename)[0].strip().lower()
    cursor.execute(
        "SELECT id, name, version FROM documents WHERE status = 'indexed' ORDER BY created_at DESC"
    )
    all_indexed = cursor.fetchall()
    superseded_doc_id = None
    assigned_version = version

    for d in all_indexed:
        existing_base = os.path.splitext(d["name"])[0].strip().lower()
        if base_name == existing_base or (
            len(base_name) > 5 and (base_name in existing_base or existing_base in base_name)
        ):
            superseded_doc_id = d["id"]
            # Auto-upgrade version tag if user left default v1.0
            if version == "v1.0":
                old_ver = d["version"]
                match = re.search(r"v?(\d+)(?:\.(\d+))?", old_ver)
                if match:
                    major = int(match.group(1)) + 1
                    assigned_version = f"v{major}.0"
                else:
                    assigned_version = "v2.0"
            break

    # Extract text from file
    try:
        pages = extract_file(file_path)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        conn.close()
        raise HTTPException(status_code=422, detail=f"Text extraction failed: {e}")

    if not pages:
        if os.path.exists(file_path):
            os.remove(file_path)
        conn.close()
        raise HTTPException(
            status_code=422,
            detail="No readable text could be extracted from this document. If scanned, ensure OCR is configured.",
        )

    # Reliable Category Determination
    sample_text = " ".join(p.get("text", "")[:300] for p in pages[:3])
    final_category = _classify_category(filename, sample_text, category)

    # Aggregate OCR stats
    ocr_used = any(p.get("ocr_used") for p in pages)
    ocr_confidences = [p.get("ocr_confidence", 1.0) for p in pages if p.get("ocr_used")]
    avg_ocr_confidence = (
        sum(ocr_confidences) / len(ocr_confidences) if ocr_confidences else 1.0
    )

    # Chunking
    chunks = chunk_pages(pages)
    if not chunks:
        if os.path.exists(file_path):
            os.remove(file_path)
        conn.close()
        raise HTTPException(status_code=422, detail="Document produced no usable text chunks.")

    # Embeddings
    texts = [c["content"] for c in chunks]
    try:
        embeddings = embed_texts(texts)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        conn.close()
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {e}")

    # Insert document record
    cursor.execute(
        """INSERT INTO documents
           (id, name, category, version, upload_date, effective_date, status,
            file_path, file_size, mime_type, doc_type, uploaded_by, content_hash,
            total_chunks, ocr_used, ocr_confidence)
           VALUES (?, ?, ?, ?, ?, ?, 'indexed', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            doc_id,
            filename,
            final_category,
            assigned_version,
            upload_date_str,
            effective_date or None,
            file_path,
            len(content),
            mime_type,
            doc_type,
            current_user["user_id"],
            file_hash,
            len(chunks),
            int(ocr_used),
            avg_ocr_confidence,
        ),
    )

    # Mark superseded document
    if superseded_doc_id:
        cursor.execute(
            "UPDATE documents SET superseded_by = ? WHERE id = ?",
            (doc_id, superseded_doc_id),
        )

    # Insert chunks with embeddings
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
                chunk.get("page_number"),
                chunk.get("section_name", "") or "",
                int(chunk_ocr),
                chunk_ocr_conf,
                serialize_embedding(emb),
            ),
        )

    # Record version entry
    version_id = str(uuid.uuid4())
    cursor.execute(
        """INSERT INTO document_versions (id, document_id, version, upload_date, content_hash)
           VALUES (?, ?, ?, ?, ?)""",
        (version_id, doc_id, assigned_version, upload_date_str, file_hash),
    )
    conn.commit()

    # Detect conflicts across existing indexed documents
    _detect_and_store_conflicts_for_doc(conn, cursor, doc_id)

    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    doc_record = dict(cursor.fetchone())
    doc_record["indexed"] = True
    doc_record["chunk_count"] = len(chunks)
    doc_record["uploaded_at"] = upload_date_str
    conn.close()

    return {
        "message": "Document uploaded, chunked, embedded, and indexed successfully.",
        "document": doc_record,
        "stats": {
            "pages_extracted": len(pages),
            "chunks_created": len(chunks),
            "category": final_category,
            "version": assigned_version,
            "ocr_used": ocr_used,
            "avg_ocr_confidence": round(avg_ocr_confidence, 3),
            "supersedes_document": superseded_doc_id,
            "content_hash": file_hash,
        },
    }


def _detect_and_store_conflicts_for_doc(conn, cursor, new_doc_id: str):
    """Scan other indexed documents for percentage parameter conflicts with new_doc_id."""
    cursor.execute("SELECT id, name FROM documents WHERE id != ? AND status = 'indexed'", (new_doc_id,))
    other_docs = cursor.fetchall()
    if not other_docs:
        return

    def get_doc_percentages(doc_id):
        cursor.execute("SELECT content FROM document_chunks WHERE document_id = ?", (doc_id,))
        rows = cursor.fetchall()
        text = " ".join(r["content"] for r in rows)
        return set(re.findall(r"\b(\d+(?:\.\d+)?)\s*%", text))

    nums_new = get_doc_percentages(new_doc_id)
    if not nums_new:
        return

    for other in other_docs:
        nums_other = get_doc_percentages(other["id"])
        # If both mention percentages on relevant policies but share none
        if nums_other and not (nums_new & nums_other):
            conflict_id = str(uuid.uuid4())
            try:
                cursor.execute(
                    """INSERT INTO document_conflicts
                       (id, document_id_a, document_id_b, conflict_type, description)
                       VALUES (?, ?, ?, 'percentage_mismatch', ?)""",
                    (
                        conflict_id,
                        other["id"],
                        new_doc_id,
                        f"'{other['name']}' cites {sorted(nums_other)}% vs '{new_doc_id}' cites {sorted(nums_new)}%",
                    ),
                )
                conn.commit()
            except Exception as e:
                print(f"[Conflict] Error storing conflict: {e}")


# ── 6. Conflict List & Trigger Scan ──────────────────────────────────────────
@router.get("/conflicts")
def list_conflicts(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT dc.*,
               da.name as doc_name_a,
               db.name as doc_name_b,
               da.version as doc_version_a,
               db.version as doc_version_b,
               da.upload_date as upload_date_a,
               db.upload_date as upload_date_b
        FROM document_conflicts dc
        LEFT JOIN documents da ON dc.document_id_a = da.id
        LEFT JOIN documents db ON dc.document_id_b = db.id
        ORDER BY dc.detected_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return {"conflicts": [dict(r) for r in rows]}


@router.post("/conflicts/scan")
def trigger_conflict_scan(current_user: dict = Depends(get_current_user)):
    """Run full pairwise conflict scan across all indexed documents."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM documents WHERE status = 'indexed'")
    docs = [dict(r) for r in cursor.fetchall()]

    detected = 0
    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            doc_a, doc_b = docs[i], docs[j]
            # Check if conflict already logged
            cursor.execute(
                """SELECT id FROM document_conflicts
                   WHERE (document_id_a = ? AND document_id_b = ?)
                      OR (document_id_a = ? AND document_id_b = ?)""",
                (doc_a["id"], doc_b["id"], doc_b["id"], doc_a["id"]),
            )
            if cursor.fetchone():
                continue

            # Check percentage diff
            cursor.execute("SELECT content FROM document_chunks WHERE document_id = ?", (doc_a["id"],))
            text_a = " ".join(r["content"] for r in cursor.fetchall())
            cursor.execute("SELECT content FROM document_chunks WHERE document_id = ?", (doc_b["id"],))
            text_b = " ".join(r["content"] for r in cursor.fetchall())

            nums_a = set(re.findall(r"\b(\d+(?:\.\d+)?)\s*%", text_a))
            nums_b = set(re.findall(r"\b(\d+(?:\.\d+)?)\s*%", text_b))

            if nums_a and nums_b and not (nums_a & nums_b):
                conflict_id = str(uuid.uuid4())
                cursor.execute(
                    """INSERT INTO document_conflicts
                       (id, document_id_a, document_id_b, conflict_type, description)
                       VALUES (?, ?, ?, 'percentage_mismatch', ?)""",
                    (
                        conflict_id,
                        doc_a["id"],
                        doc_b["id"],
                        f"'{doc_a['name']}' cites {sorted(nums_a)}% vs '{doc_b['name']}' cites {sorted(nums_b)}%",
                    ),
                )
                detected += 1

    conn.commit()
    conn.close()
    return {"message": f"Conflict scan complete. {detected} new conflicts detected."}


# ── 7. Document Content Viewer API (Real chunks & sections) ──────────────────
@router.get("/{doc_id}/content")
def get_document_content(
    doc_id: str,
    current_user: dict = Depends(get_current_user),
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    doc_row = cursor.fetchone()
    if not doc_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found.")

    doc = dict(doc_row)

    cursor.execute(
        """SELECT id, chunk_index, page_number, section_name, content
           FROM document_chunks
           WHERE document_id = ?
           ORDER BY chunk_index ASC""",
        (doc_id,),
    )
    chunks = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Build unique section structure
    seen_sections = set()
    sections = []
    for c in chunks:
        sec_name = (c.get("section_name") or "").strip()
        page = c.get("page_number")
        if sec_name and sec_name not in seen_sections:
            seen_sections.add(sec_name)
            sections.append({
                "id": f"sec_{len(sections) + 1}",
                "title": sec_name,
                "page": page or 1,
            })

    if not sections and chunks:
        # Generate default page-based outline
        pages_seen = set()
        for c in chunks:
            p = c.get("page_number") or 1
            if p not in pages_seen:
                pages_seen.add(p)
                sections.append({
                    "id": f"page_{p}",
                    "title": f"Page {p} Overview",
                    "page": p,
                })

    full_text = "\n\n".join(c["content"] for c in chunks)

    # Extract detected policy entities from text
    pct_matches = list(dict.fromkeys(re.findall(r"\b\d+(?:\.\d+)?\s*%", full_text)))[:4]
    days_matches = list(dict.fromkeys(re.findall(r"\b\d+\s*(?:working\s+days|days|weeks)\b", full_text, re.I)))[:2]
    marks_matches = list(dict.fromkeys(re.findall(r"\b\d+\s*marks\b", full_text, re.I)))[:2]

    detected_entities = [f"{p} Requirement" for p in pct_matches]
    detected_entities.extend(days_matches)
    detected_entities.extend(marks_matches)

    return {
        "id": doc["id"],
        "name": doc["name"],
        "category": doc["category"],
        "version": doc["version"],
        "upload_date": doc["upload_date"],
        "effective_date": doc.get("effective_date"),
        "total_chunks": doc.get("total_chunks", len(chunks)),
        "file_size": doc.get("file_size", 0),
        "status": doc.get("status"),
        "has_pdf_file": bool(doc.get("file_path") and os.path.exists(doc["file_path"])),
        "sections": sections,
        "chunks": chunks,
        "full_text": full_text,
        "detected_entities": detected_entities,
    }


# ── 8. Document Binary File Stream (for PDF Viewer) ──────────────────────────
@router.get("/{doc_id}/file")
def get_document_file(
    doc_id: str,
    token: Optional[str] = Query(None),
):
    """Serve the actual uploaded document binary (PDF/DOCX/etc.) for rendering."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, mime_type, name FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row["file_path"] or not os.path.exists(row["file_path"]):
        raise HTTPException(status_code=404, detail="Original document file not found on server.")

    media_type = row["mime_type"] or "application/pdf"
    return FileResponse(
        path=row["file_path"],
        media_type=media_type,
        filename=row["name"],
        content_disposition_type="inline",
    )


# ── 9. Get Single Document Metadata ──────────────────────────────────────────
@router.get("/{doc_id}")
def get_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found.")

    cursor.execute(
        "SELECT * FROM document_versions WHERE document_id = ? ORDER BY created_at DESC",
        (doc_id,),
    )
    versions = [dict(v) for v in cursor.fetchall()]
    conn.close()

    doc = dict(row)
    doc["indexed"] = (doc.get("status") == "indexed")
    doc["chunk_count"] = doc.get("total_chunks", 0)
    return {"document": doc, "versions": versions}


# ── 10. Delete Document (clean DB & disk) ────────────────────────────────────
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
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"[Delete] Warning: Could not remove file {file_path}: {e}")

    # Remove all related records from DB
    cursor.execute("DELETE FROM document_chunks WHERE document_id = ?", (doc_id,))
    cursor.execute("DELETE FROM document_versions WHERE document_id = ?", (doc_id,))
    cursor.execute("DELETE FROM document_conflicts WHERE document_id_a = ? OR document_id_b = ?", (doc_id, doc_id))
    cursor.execute("UPDATE documents SET superseded_by = NULL WHERE superseded_by = ?", (doc_id,))
    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

    conn.commit()
    conn.close()

    return {"message": f"Document {doc_id} and all related chunks and conflicts deleted successfully."}
