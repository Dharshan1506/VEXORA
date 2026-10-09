"""
main.py — VEXORA FastAPI Application
Uses modern lifespan context manager (no deprecated @on_event).
"""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env before anything else
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers.auth_router import router as auth_router
from routers.documents_router import router as documents_router
from routers.conversations_router import router as conversations_router
from routers.chat_router import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialise database and seed default users."""
    print("[VEXORA] Initialising database...")
    init_db()
    print("[VEXORA] Database ready.")
    print("[VEXORA] Default accounts (change passwords in production):")
    print("         admin@vexora.edu   / Admin@2026")
    print("         student@vexora.edu / Student@2026")
    print("         scholar@university.edu / Scholar@2026")
    yield
    # Shutdown: nothing to clean up


app = FastAPI(
    title="VEXORA Knowledge Intelligence API",
    description="Multimodal RAG platform for university knowledge management.",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(conversations_router)
app.include_router(chat_router)


# ── Health check (public) ─────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    gemini_configured = bool(
        os.environ.get("GEMINI_API_KEY")
        and os.environ.get("GEMINI_API_KEY") != "your-gemini-api-key-here"
    )
    db_ok = False
    doc_count = 0
    chunk_count = 0
    try:
        from database import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM documents WHERE status = 'indexed'")
        doc_count = cursor.fetchone()["cnt"]
        cursor.execute("SELECT COUNT(*) as cnt FROM document_chunks")
        chunk_count = cursor.fetchone()["cnt"]
        conn.close()
        db_ok = True
    except Exception as e:
        print(f"[Health] DB check failed: {e}")

    return {
        "status": "ok" if db_ok else "degraded",
        "service": "VEXORA RAG Engine",
        "version": "2.1.0",
        "database_connected": db_ok,
        "indexed_documents": doc_count,
        "indexed_chunks": chunk_count,
        "gemini_configured": gemini_configured,
        "debug_retrieval": os.environ.get("DEBUG_RETRIEVAL", "false"),
    }


# ── Analytics (public, aggregated only) ──────────────────────────────────────
@app.get("/api/analytics")
def analytics():
    from database import get_db
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM documents WHERE status = 'indexed'")
    total_docs = cursor.fetchone()["cnt"]
    cursor.execute("SELECT COUNT(*) as cnt FROM document_chunks")
    total_chunks = cursor.fetchone()["cnt"]
    cursor.execute("SELECT COUNT(*) as cnt FROM messages WHERE role = 'user'")
    total_queries = cursor.fetchone()["cnt"]
    cursor.execute("SELECT COUNT(*) as cnt FROM document_conflicts")
    total_conflicts = cursor.fetchone()["cnt"]
    conn.close()
    return {
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "total_queries": total_queries,
        "total_conflicts": total_conflicts,
    }


# ── Debug: full pipeline trace (authenticated) ────────────────────────────────
@app.post("/api/debug/retrieval")
def debug_retrieval_pipeline(body: dict):
    """
    Run BM25 + vector + RRF + reranker for a query and return full pipeline
    details WITHOUT saving to DB and WITHOUT calling LLM.
    Body: {"query": "..."}
    """
    query = (body or {}).get("query", "").strip()
    if not query:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="query is required")

    from database import get_db
    from services.embedding_service import embed_text
    from services.retrieval_service import hybrid_search
    from services.reranker_service import rerank, is_reranker_available

    conn = get_db()
    query_embedding = embed_text(query)
    retrieved, debug_info = hybrid_search(query, query_embedding, conn, top_k=8)
    reranked, reranker_scores = rerank(query, retrieved, top_k=5)
    conn.close()

    return {
        "query": query,
        "pipeline": {
            "total_chunks_in_db": debug_info["total_chunks_in_db"],
            "bm25_top5": debug_info["bm25_results"][:5],
            "vector_top5": debug_info["vector_results"][:5],
            "rrf_top5": debug_info["rrf_results"][:5],
            "reranker_available": is_reranker_available(),
            "reranked": [
                {
                    "chunk_id": c["id"],
                    "doc_name": c.get("doc_name"),
                    "page": c.get("page_number"),
                    "section": c.get("section_name"),
                    "reranker_score": round(reranker_scores[i], 4) if i < len(reranker_scores) else None,
                    "rrf_score": c.get("rrf_score"),
                    "snippet": c["content"][:300],
                }
                for i, c in enumerate(reranked)
            ],
            "evidence_threshold": float(os.environ.get("EVIDENCE_SCORE_THRESHOLD", "0.15")),
        },
    }


# ── Debug: system status ──────────────────────────────────────────────────────
@app.get("/api/debug/system")
def debug_system_status():
    from services.embedding_service import _get_model
    from services.reranker_service import is_reranker_available
    from services.extraction_service import is_ocr_available
    try:
        model = _get_model()
        embedding_ok = True
        embedding_dim = model.get_sentence_embedding_dimension()
    except Exception as e:
        embedding_ok = False
        embedding_dim = None

    return {
        "embedding_model": os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        "embedding_loaded": embedding_ok,
        "embedding_dim": embedding_dim,
        "reranker_available": is_reranker_available(),
        "ocr_available": is_ocr_available(),
        "gemini_configured": bool(
            os.environ.get("GEMINI_API_KEY")
            and os.environ.get("GEMINI_API_KEY") != "your-gemini-api-key-here"
        ),
        "llm_model": os.environ.get("LLM_MODEL", "gemini-2.0-flash"),
        "evidence_threshold": float(os.environ.get("EVIDENCE_SCORE_THRESHOLD", "0.15")),
        "debug_retrieval": os.environ.get("DEBUG_RETRIEVAL", "false") == "true",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
