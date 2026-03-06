"""
Prompt builder: system + retrieved chunks (with labels) + user question.
"""

from typing import List, Dict, Any


def build_prompt(
    chunks: List[Dict[str, Any]],
    question: str,
    system_prompt: str = "",
) -> str:
    """
    Build the full prompt: system instructions, context (chunks with labels), and question.

    Args:
        chunks: List of chunk dicts (section_label, text, entry_id, term).
        question: User question.
        system_prompt: Optional system/instruction prefix.

    Returns:
        Single string with system (if any), then context block, then question.
    """
    parts = []
    if system_prompt:
        parts.append(system_prompt.strip())
        parts.append("")
    if chunks:
        parts.append("Relevant excerpts from the encyclopedia:")
        for c in chunks:
            label = c.get("section_label", "")
            term = c.get("term", "")
            text = c.get("text", "")
            if term:
                parts.append(f"[{label}] {term}: {text[:500]}")
            else:
                parts.append(f"[{label}] {text[:500]}")
        parts.append("")
    parts.append(f"Question: {question}")
    return "\n".join(parts)
