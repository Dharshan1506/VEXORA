"""
llm_service.py
Calls the LLM API (supports Gemini and OpenAI-compatible endpoints).
Includes Evidence Guard to prevent hallucination on insufficient evidence.
Falls back gracefully when no API key is configured.
"""

import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Optional, Tuple

try:
    from google import genai as google_genai
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini").lower().strip()
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-2.0-flash")
OPENAI_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")

INSUFFICIENT_EVIDENCE_MSG = (
    "I couldn't find sufficient evidence in the available university documents to answer this reliably."
)

# ── Evidence Guard configuration ────────────────────────────────────────────
EVIDENCE_SCORE_THRESHOLD = float(os.environ.get("EVIDENCE_SCORE_THRESHOLD", "0.15"))
EVIDENCE_MIN_CHUNKS = int(os.environ.get("EVIDENCE_MIN_CHUNKS", "1"))


def evidence_guard(
    query: str,
    reranked_chunks: List[Dict],
    reranker_scores: Optional[List[float]] = None,
) -> Tuple[bool, str]:
    """
    Determines whether there is sufficient evidence to generate an LLM answer.
    VEXORA does NOT blindly send every question to the LLM.

    Returns:
        (sufficient: bool, reason: str)
    """
    import math

    if not reranked_chunks:
        return False, "no_chunks_retrieved"

    if len(reranked_chunks) < EVIDENCE_MIN_CHUNKS:
        return False, f"fewer_than_{EVIDENCE_MIN_CHUNKS}_chunks"

    # If reranker scores are available, check the top score against threshold
    if reranker_scores and len(reranker_scores) > 0:
        top_score = reranker_scores[0]
        # Calibrate top_score (logit) to probability [0, 1]
        if top_score < -25:
            conf = 0.0
        elif top_score > 25:
            conf = 1.0
        else:
            conf = 1.0 / (1.0 + math.exp(-top_score))

        top_chunk = reranked_chunks[0]
        bm25_score = top_chunk.get("bm25_score", 0.0) or 0.0
        vector_score = top_chunk.get("vector_score", 0.0) or 0.0

        # Reject if reranker confidence is below threshold AND neither BM25 nor Vector retriever found a strong signal
        if conf < EVIDENCE_SCORE_THRESHOLD and bm25_score < 3.5 and vector_score < 0.35:
            return (
                False,
                f"top_reranker_score_{top_score:.3f}_below_threshold_{EVIDENCE_SCORE_THRESHOLD}",
            )

    return True, "sufficient"


def _build_prompt(question: str, chunks: List[Dict]) -> str:
    evidence_parts = []
    for i, chunk in enumerate(chunks, start=1):
        doc_name = chunk.get("doc_name") or chunk.get("document_name") or "Unknown Document"
        page = chunk.get("page_number")
        section = chunk.get("section_name") or chunk.get("section") or ""
        version = chunk.get("doc_version") or chunk.get("document_version") or ""

        label = f"[Source {i}: {doc_name}"
        if version:
            label += f" ({version})"
        if page is not None:
            label += f", Page {page}"
        if section:
            label += f", Section: {section}"
        label += "]"
        evidence_parts.append(f"{label}\n{chunk['content']}")

    evidence_block = "\n\n---\n\n".join(evidence_parts)

    return f"""You are VEXORA, an evidence-grounded university knowledge assistant.

Answer only using the supplied evidence.

Do not use unsupported external knowledge.

If the evidence does not sufficiently answer the question, clearly state that sufficient evidence was not found:
"{INSUFFICIENT_EVIDENCE_MSG}"

Do not invent facts.

Do not invent dates.

Do not invent policies.

Do not invent page numbers.

Do not invent citations.

If sources disagree, explicitly identify the conflict.

Keep the answer clear and concise.

Every factual claim that depends on retrieved documents should be traceable to a source.

RETRIEVED EVIDENCE:
{evidence_block}

USER QUESTION: {question}

FINAL ANSWER:"""


def _call_openai_compatible(api_key: str, prompt: str) -> str:
    """Call an OpenAI-compatible API endpoint via standard urllib."""
    url = f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": LLM_MODEL if not LLM_MODEL.startswith("gemini") else "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))
        return res_data["choices"][0]["message"]["content"].strip()


def generate_answer(
    question: str,
    chunks: List[Dict],
    reranker_scores: Optional[List[float]] = None,
) -> Dict:
    """
    Generate an LLM answer from question + retrieved chunks.
    Evidence Guard is checked BEFORE calling LLM.

    Returns a dict with:
        content               - the answer text
        llm_used              - bool, whether LLM was called
        evidence_status       - 'sufficient' | 'insufficient'
        fallback_reason       - reason if LLM was not used
        evidence_guard_reason - why evidence guard fired (if applicable)
    """
    # ── 1. Evidence Guard Check ───────────────────────────────────────────────
    sufficient, guard_reason = evidence_guard(question, chunks, reranker_scores)

    if not sufficient:
        return {
            "content": INSUFFICIENT_EVIDENCE_MSG,
            "llm_used": False,
            "evidence_status": "insufficient",
            "fallback_reason": "evidence_guard",
            "evidence_guard_reason": guard_reason,
        }

    # ── 2. API Key Check ──────────────────────────────────────────────────────
    api_key = (
        os.environ.get("LLM_API_KEY", "")
        or os.environ.get("GEMINI_API_KEY", "")
    ).strip()

    if not api_key or api_key.startswith("your-gemini") or api_key.startswith("your-llm"):
        # No configured API key — return raw grounded evidence directly without fabrication
        content = "**Retrieved Evidence** *(Configure GEMINI_API_KEY or LLM_API_KEY in backend/.env for AI synthesis)*\n\n"
        for i, chunk in enumerate(chunks, start=1):
            doc_name = chunk.get("doc_name") or chunk.get("document_name") or "Unknown"
            page = chunk.get("page_number")
            section = chunk.get("section_name") or chunk.get("section") or ""
            header = f"**[{i}] {doc_name}"
            if page is not None:
                header += f" — Page {page}"
            if section:
                header += f", {section}"
            header += "**"
            content += f"{header}\n{chunk['content']}\n\n"
        return {
            "content": content.strip(),
            "llm_used": False,
            "evidence_status": "sufficient",
            "fallback_reason": "no_api_key",
            "evidence_guard_reason": None,
        }

    # ── 3. Call LLM Provider ──────────────────────────────────────────────────
    prompt = _build_prompt(question, chunks)

    # Provider: OpenAI-compatible
    if LLM_PROVIDER == "openai":
        try:
            answer_text = _call_openai_compatible(api_key, prompt)
            final_status = (
                "insufficient"
                if INSUFFICIENT_EVIDENCE_MSG[:40].lower() in answer_text.lower()
                else "sufficient"
            )
            return {
                "content": answer_text,
                "llm_used": True,
                "evidence_status": final_status,
                "fallback_reason": None,
                "evidence_guard_reason": None,
            }
        except Exception as e:
            print(f"[LLM] OpenAI API error: {e}")
            return _format_grounded_fallback(chunks, f"OpenAI API error: {e}")

    # Provider: Gemini (default)
    if not _GENAI_AVAILABLE:
        return {
            "content": "google-genai package is not installed. Run: py -m pip install google-genai",
            "llm_used": False,
            "evidence_status": "sufficient",
            "fallback_reason": "package_missing",
            "evidence_guard_reason": None,
        }

    try:
        client = google_genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt,
        )
        answer_text = response.text.strip()

        # If LLM itself reports insufficient evidence
        final_status = (
            "insufficient"
            if INSUFFICIENT_EVIDENCE_MSG[:40].lower() in answer_text.lower()
            else "sufficient"
        )

        return {
            "content": answer_text,
            "llm_used": True,
            "evidence_status": final_status,
            "fallback_reason": None,
            "evidence_guard_reason": None,
        }
    except Exception as e:
        print(f"[LLM] Gemini API error: {e}")
        return _format_grounded_fallback(chunks, f"Gemini API error: {e}")


def _format_grounded_fallback(chunks: List[Dict], error_msg: str) -> Dict:
    content = f"**Note: LLM unavailable ({error_msg}). Showing retrieved evidence directly:**\n\n"
    for i, chunk in enumerate(chunks, start=1):
        page = chunk.get("page_number")
        page_str = f" — Page {page}" if page is not None else ""
        content += f"**[{i}] {chunk.get('doc_name')}{page_str}**\n{chunk['content']}\n\n"
    return {
        "content": content.strip(),
        "llm_used": False,
        "evidence_status": "sufficient",
        "fallback_reason": error_msg,
        "evidence_guard_reason": None,
    }
