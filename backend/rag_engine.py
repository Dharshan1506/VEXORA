"""
rag_engine.py
DEPRECATED: This file previously contained a hardcoded KNOWLEDGE_BASE
(mock data). All RAG logic has been moved to:

  services/retrieval_service.py  — BM25 + vector search + RRF
  services/reranker_service.py   — cross-encoder reranking
  services/llm_service.py        — LLM generation + Evidence Guard
  services/embedding_service.py  — embedding generation
  routers/chat_router.py         — full pipeline orchestration

This file is kept as a placeholder to avoid import errors.
Do NOT add hardcoded knowledge here.
"""

# No hardcoded KNOWLEDGE_BASE.
# All retrieval operates against real uploaded documents in the database.
