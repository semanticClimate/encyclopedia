"""
Chunker: turn sections into chunks for embedding and retrieval.

Each chunk is plain text with section_label, entry_id, term for citation.
"""

from typing import List, Dict, Any


def chunk_sections(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert sections into chunks. Currently one chunk per section; text is already plain.

    Args:
        sections: List of section dicts (section_label, text, entry_id, term).

    Returns:
        List of chunk dicts with section_label, text, entry_id, term.
        Text is plain (no HTML).
    """
    chunks = []
    for s in sections:
        text = (s.get("text") or "").strip()
        if not text:
            continue
        chunks.append({
            "section_label": s.get("section_label", ""),
            "text": text,
            "entry_id": s.get("entry_id", ""),
            "term": s.get("term", ""),
        })
    return chunks
