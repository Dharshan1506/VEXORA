"""
chunking_service.py
Splits extracted page text into overlapping chunks,
preserving page number, chunk index, and OCR metadata.
"""

import os
import re
from typing import List, Dict

CHUNK_SIZE_WORDS = int(os.environ.get("CHUNK_SIZE", "500"))   # target words per chunk
OVERLAP_WORDS = int(os.environ.get("CHUNK_OVERLAP", "100"))      # overlap between consecutive chunks
MIN_CHUNK_WORDS = int(os.environ.get("MIN_CHUNK_WORDS", "30"))   # discard chunks smaller than this


def chunk_pages(
    pages: List[Dict],
    chunk_size: int = None,
    overlap: int = None,
) -> List[Dict]:
    """
    Splits a list of {page, text, ocr_used, ocr_confidence} dicts into
    overlapping word-window chunks. Preserves all metadata per chunk.
    Returns a list of chunk dicts ready for embedding + DB insertion.
    """
    c_size = chunk_size or CHUNK_SIZE_WORDS
    ovlp = overlap or OVERLAP_WORDS

    chunks = []
    chunk_index = 0

    for page_info in pages:
        page_num = page_info["page"]
        text = page_info["text"].strip()
        ocr_used = page_info.get("ocr_used", False)
        ocr_confidence = page_info.get("ocr_confidence", 1.0)

        if not text:
            continue

        words = text.split()
        step = max(1, c_size - ovlp)

        # If the page is short enough to be one chunk
        if len(words) <= c_size:
            if len(words) >= MIN_CHUNK_WORDS:
                chunks.append({
                    "chunk_index": chunk_index,
                    "content": text,
                    "page_number": page_num,
                    "section_name": _infer_section(text),
                    "ocr_used": ocr_used,
                    "ocr_confidence": ocr_confidence,
                })
                chunk_index += 1
            continue

        # Sliding window
        for i in range(0, len(words), step):
            window = words[i: i + c_size]
            if len(window) < MIN_CHUNK_WORDS:
                continue
            chunk_text = " ".join(window)
            chunks.append({
                "chunk_index": chunk_index,
                "content": chunk_text,
                "page_number": page_num,
                "section_name": _infer_section(chunk_text),
                "ocr_used": ocr_used,
                "ocr_confidence": ocr_confidence,
            })
            chunk_index += 1

    return chunks


def _infer_section(text: str) -> str:
    """
    Heuristic: detect headings at start of text.
    Handles markdown (# Title), Section/Article labels, numbered items (1.1 Title),
    ALL CAPS headings, or short Title-Case lines.
    """
    first_line = text.split("\n")[0].strip()
    # Strip markdown header hashes
    cleaned_line = re.sub(r"^#{1,6}\s*", "", first_line).strip()
    words_in_line = cleaned_line.split()

    if 1 <= len(words_in_line) <= 14:
        lower = cleaned_line.lower()
        if (
            cleaned_line.istitle()
            or cleaned_line.isupper()
            or any(lower.startswith(prefix) for prefix in (
                "section", "article", "chapter", "rule", "policy", "clause", "part", "appendix"
            ))
            or re.match(r"^\d+(\.\d+)*\s+[A-Za-z]", cleaned_line)
        ):
            return cleaned_line[:120]
    return ""
