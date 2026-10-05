"""
embedding_service.py
Generates dense vector embeddings.
Supports multiple providers via environment configuration:
- sentence-transformers (default local CPU/GPU, fast, no external API key needed)
- gemini (Google GenAI text-embedding-004)
- openai (OpenAI-compatible embeddings)
Model is loaded lazily and cached in memory.
"""

import os
import json
from typing import List

EMBEDDING_PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "sentence-transformers").lower().strip()
MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

_model = None


def _get_model():
    global _model
    if _model is None:
        if EMBEDDING_PROVIDER == "sentence-transformers":
            from sentence_transformers import SentenceTransformer
            print(f"[Embedding] Loading model '{MODEL_NAME}' (provider: {EMBEDDING_PROVIDER})...")
            _model = SentenceTransformer(MODEL_NAME)
            dim_fn = getattr(_model, "get_embedding_dimension", getattr(_model, "get_sentence_embedding_dimension", None))
            dim = dim_fn() if dim_fn else 384
            print(f"[Embedding] Model loaded — dim={dim}")
        elif EMBEDDING_PROVIDER == "gemini":
            from google import genai
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY")
            _model = genai.Client(api_key=api_key)
            print(f"[Embedding] Gemini embedding client configured (model: {MODEL_NAME})")
        else:
            # Fallback to sentence-transformers
            from sentence_transformers import SentenceTransformer
            print(f"[Embedding] Unknown provider '{EMBEDDING_PROVIDER}', falling back to sentence-transformers with '{MODEL_NAME}'")
            _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_text(text: str) -> List[float]:
    """Embed a single string. Returns a list of floats."""
    if EMBEDDING_PROVIDER == "gemini":
        client = _get_model()
        model_name = MODEL_NAME if "embedding" in MODEL_NAME else "text-embedding-004"
        response = client.models.embed_content(
            model=model_name,
            contents=text,
        )
        return response.embeddings[0].values

    # Default: sentence-transformers
    model = _get_model()
    vec = model.encode(text, convert_to_tensor=False, normalize_embeddings=True)
    return vec.tolist()


def embed_texts(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """Embed a batch of strings. Returns a list-of-lists of floats."""
    if not texts:
        return []

    if EMBEDDING_PROVIDER == "gemini":
        return [embed_text(t) for t in texts]

    # Default: sentence-transformers
    model = _get_model()
    vecs = model.encode(
        texts,
        batch_size=batch_size,
        convert_to_tensor=False,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 50,
    )
    return [v.tolist() for v in vecs]


def serialize_embedding(vec: List[float]) -> str:
    """Convert float list to JSON string for SQLite storage."""
    return json.dumps(vec)


def deserialize_embedding(json_str: str) -> List[float]:
    """Deserialize embedding from JSON string."""
    return json.loads(json_str)
