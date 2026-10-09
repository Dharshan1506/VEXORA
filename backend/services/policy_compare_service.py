"""
services/policy_compare_service.py
Real Policy & Version Comparison Engine.
Extracts clauses and policy parameters from actual document chunks stored in the database.
Compares actual document content to detect:
  - numerical value shifts (percentages, marks, days, CGPA)
  - added clauses
  - removed clauses
  - modified regulations
Returns structured comparison results with real page and section citations.
NO hardcoded / fabricated demo values.
"""

import re
import difflib
from typing import Dict, List, Any, Optional


# Regex patterns for policy parameter extraction
PERCENT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*%")
DAYS_PATTERN = re.compile(r"\b(\d+)\s*(?:working\s+days|calendar\s+days|days|weeks|months)\b", re.IGNORECASE)
MARKS_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?)\s*(?:marks|points|credits)\b", re.IGNORECASE)
CGPA_PATTERN = re.compile(r"\b(?:cgpa|gpa)\s*(?:of|>=|above|minimum)?\s*(\d+(?:\.\d+)?)\b", re.IGNORECASE)

# Keywords to identify parameter topics
TOPIC_KEYWORDS = {
    "Minimum Attendance Requirement": ["attendance", "minimum attendance", "overall attendance", "aggregate attendance"],
    "Medical Condonation Limit": ["medical condonation", "condonation", "medical reasons", "hospitalization"],
    "Sports Condonation Policy": ["sports condonation", "sports", "symposium", "on-duty"],
    "Detention Penalty Threshold": ["detention", "detained", "prevented from", "shortage of attendance"],
    "Continuous Assessment Weightage": ["continuous internal assessment", "cia", "internal assessment", "internal examination", "cia weightage"],
    "Semester End Examination Weightage": ["semester end examination", "see", "end semester", "university examination weightage"],
    "Re-examination Window": ["re-examination", "revaluation", "supplementary", "attempt window"],
    "Passing Criteria": ["minimum marks", "qualify", "passing minimum", "passing criteria"],
    "Credit Requirements": ["credits", "minimum credits", "degree requirement"],
}


def _clean_snippet(text: str, max_len: int = 250) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) > max_len:
        return cleaned[:max_len] + "..."
    return cleaned


def _find_topic(sentence: str) -> Optional[str]:
    lower = sentence.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return topic
    return None


def _extract_parameters_from_chunks(chunks: List[Dict]) -> Dict[str, Dict[str, Any]]:
    """
    Extract structured parameters with real source locations from document chunks.
    Returns a dict mapping topic -> parameter data.
    """
    extracted = {}

    for chunk in chunks:
        content = chunk.get("content", "")
        page = chunk.get("page_number")
        section = chunk.get("section_name", "") or "General"
        doc_name = chunk.get("doc_name") or chunk.get("document_name") or "Document"

        # Split into sentences for fine-grained extraction
        sentences = re.split(r"(?<=[.!?])\s+", content)
        for sent in sentences:
            sent_clean = sent.strip()
            if not sent_clean or len(sent_clean) < 15:
                continue

            topic = _find_topic(sent_clean)
            if not topic:
                continue

            # Look for values in this sentence
            val = None
            pct_matches = PERCENT_PATTERN.findall(sent_clean)
            days_matches = DAYS_PATTERN.findall(sent_clean)
            marks_matches = MARKS_PATTERN.findall(sent_clean)
            cgpa_matches = CGPA_PATTERN.findall(sent_clean)

            if pct_matches:
                # Prefer first percentage found
                val = f"{pct_matches[0]}%"
            elif days_matches:
                val = f"{days_matches[0]} Days"
            elif marks_matches:
                val = f"{marks_matches[0]} Marks"
            elif cgpa_matches:
                val = f"{cgpa_matches[0]} CGPA"
            else:
                # Textual policy statement
                val = "Included"

            if topic not in extracted or extracted[topic]["value"] == "Included" and val != "Included":
                extracted[topic] = {
                    "topic": topic,
                    "value": val,
                    "page": page,
                    "section": section,
                    "snippet": _clean_snippet(sent_clean),
                    "doc_name": doc_name,
                }

    return extracted


def compare_policies(doc_id_a: str, doc_id_b: str, conn) -> Dict[str, Any]:
    """
    Compare two real documents from the database.
    Loads actual chunks, extracts clauses and parameters, and computes differences.
    """
    cursor = conn.cursor()

    # Load document metadata
    cursor.execute("SELECT id, name, version, upload_date, category, content_hash FROM documents WHERE id = ?", (doc_id_a,))
    doc_a_row = cursor.fetchone()
    cursor.execute("SELECT id, name, version, upload_date, category, content_hash FROM documents WHERE id = ?", (doc_id_b,))
    doc_b_row = cursor.fetchone()

    if not doc_a_row:
        raise ValueError(f"Source document ID '{doc_id_a}' not found.")
    if not doc_b_row:
        raise ValueError(f"Target document ID '{doc_id_b}' not found.")

    doc_a = dict(doc_a_row)
    doc_b = dict(doc_b_row)

    # Identical document check
    if doc_id_a == doc_id_b or (doc_a.get("content_hash") and doc_a["content_hash"] == doc_b.get("content_hash")):
        return {
            "source_document": doc_a,
            "target_document": doc_b,
            "summary": {
                "total_changes": 0,
                "changed": 0,
                "added": 0,
                "removed": 0,
                "is_identical": True,
            },
            "changes": [],
            "message": f"Both selections reference identical document content ('{doc_a['name']}'). No policy shifts found.",
        }

    # Load chunks for both documents
    cursor.execute(
        """SELECT id, chunk_index, page_number, section_name, content
           FROM document_chunks
           WHERE document_id = ?
           ORDER BY chunk_index ASC""",
        (doc_id_a,),
    )
    chunks_a = [dict(r) for r in cursor.fetchall()]

    cursor.execute(
        """SELECT id, chunk_index, page_number, section_name, content
           FROM document_chunks
           WHERE document_id = ?
           ORDER BY chunk_index ASC""",
        (doc_id_b,),
    )
    chunks_b = [dict(r) for r in cursor.fetchall()]

    # Attach document names to chunks
    for c in chunks_a:
        c["doc_name"] = doc_a["name"]
    for c in chunks_b:
        c["doc_name"] = doc_b["name"]

    # Extract structured parameters from both documents
    params_a = _extract_parameters_from_chunks(chunks_a)
    params_b = _extract_parameters_from_chunks(chunks_b)

    changes = []
    all_topics = list(dict.fromkeys(list(params_a.keys()) + list(params_b.keys())))

    for topic in all_topics:
        in_a = topic in params_a
        in_b = topic in params_b

        if in_a and in_b:
            item_a = params_a[topic]
            item_b = params_b[topic]

            if item_a["value"] != item_b["value"]:
                # Changed parameter value
                changes.append({
                    "parameter": topic,
                    "old_value": item_a["value"],
                    "new_value": item_b["value"],
                    "type": "changed",
                    "source_a": {
                        "doc_name": doc_a["name"],
                        "page": item_a["page"],
                        "section": item_a["section"],
                        "snippet": item_a["snippet"],
                    },
                    "source_b": {
                        "doc_name": doc_b["name"],
                        "page": item_b["page"],
                        "section": item_b["section"],
                        "snippet": item_b["snippet"],
                    },
                })
            else:
                # Same value - check if snippets or clauses differ significantly
                sim = difflib.SequenceMatcher(None, item_a["snippet"], item_b["snippet"]).ratio()
                if sim < 0.85:
                    changes.append({
                        "parameter": f"{topic} (Wording Revision)",
                        "old_value": item_a["snippet"][:40] + "...",
                        "new_value": item_b["snippet"][:40] + "...",
                        "type": "changed",
                        "source_a": {
                            "doc_name": doc_a["name"],
                            "page": item_a["page"],
                            "section": item_a["section"],
                            "snippet": item_a["snippet"],
                        },
                        "source_b": {
                            "doc_name": doc_b["name"],
                            "page": item_b["page"],
                            "section": item_b["section"],
                            "snippet": item_b["snippet"],
                        },
                    })
        elif in_b and not in_a:
            # Added clause in new document
            item_b = params_b[topic]
            changes.append({
                "parameter": topic,
                "old_value": "Not Included",
                "new_value": item_b["value"],
                "type": "added",
                "source_a": {
                    "doc_name": doc_a["name"],
                    "page": None,
                    "section": "N/A",
                    "snippet": f"Clause absent in {doc_a['name']}.",
                },
                "source_b": {
                    "doc_name": doc_b["name"],
                    "page": item_b["page"],
                    "section": item_b["section"],
                    "snippet": item_b["snippet"],
                },
            })
        elif in_a and not in_b:
            # Removed clause in new document
            item_a = params_a[topic]
            changes.append({
                "parameter": topic,
                "old_value": item_a["value"],
                "new_value": "Removed / Not Specified",
                "type": "removed",
                "source_a": {
                    "doc_name": doc_a["name"],
                    "page": item_a["page"],
                    "section": item_a["section"],
                    "snippet": item_a["snippet"],
                },
                "source_b": {
                    "doc_name": doc_b["name"],
                    "page": None,
                    "section": "N/A",
                    "snippet": f"Clause removed or omitted in {doc_b['name']}.",
                },
            })

    # If no topic-level differences were found, do a section-level diff
    if not changes and chunks_a and chunks_b:
        # Check overall section headings
        sec_a = {c.get("section_name", ""): c for c in chunks_a if c.get("section_name")}
        sec_b = {c.get("section_name", ""): c for c in chunks_b if c.get("section_name")}

        added_sections = set(sec_b.keys()) - set(sec_a.keys())
        removed_sections = set(sec_a.keys()) - set(sec_b.keys())

        for sec in list(added_sections)[:3]:
            c = sec_b[sec]
            changes.append({
                "parameter": f"Section: {sec}",
                "old_value": "Absent",
                "new_value": "Added Clause",
                "type": "added",
                "source_a": {
                    "doc_name": doc_a["name"],
                    "page": None,
                    "section": "N/A",
                    "snippet": "Section not found in previous version.",
                },
                "source_b": {
                    "doc_name": doc_b["name"],
                    "page": c.get("page_number"),
                    "section": sec,
                    "snippet": _clean_snippet(c.get("content", "")),
                },
            })

        for sec in list(removed_sections)[:3]:
            c = sec_a[sec]
            changes.append({
                "parameter": f"Section: {sec}",
                "old_value": "Present",
                "new_value": "Removed Clause",
                "type": "removed",
                "source_a": {
                    "doc_name": doc_a["name"],
                    "page": c.get("page_number"),
                    "section": sec,
                    "snippet": _clean_snippet(c.get("content", "")),
                },
                "source_b": {
                    "doc_name": doc_b["name"],
                    "page": None,
                    "section": "N/A",
                    "snippet": "Section omitted in revised version.",
                },
            })

    changed_count = sum(1 for c in changes if c["type"] == "changed")
    added_count = sum(1 for c in changes if c["type"] == "added")
    removed_count = sum(1 for c in changes if c["type"] == "removed")

    return {
        "source_document": doc_a,
        "target_document": doc_b,
        "summary": {
            "total_changes": len(changes),
            "changed": changed_count,
            "added": added_count,
            "removed": removed_count,
            "is_identical": len(changes) == 0,
        },
        "changes": changes,
        "message": (
            f"Detected {len(changes)} policy shifts across {doc_a['name']} and {doc_b['name']}."
            if changes
            else "No substantive policy parameter differences detected between these two documents."
        ),
    }
