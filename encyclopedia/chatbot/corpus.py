"""
Corpus loading and section extraction for chatbot.

Turns encyclopedia entries into labelled sections (term, description, definition, etc.)
for indexing and retrieval.
"""

from pathlib import Path
from typing import List, Dict, Any
import re

from encyclopedia.core.encyclopedia import AmiEncyclopedia


def load_entries_from_encyclopedia(source) -> List[Dict[str, Any]]:
    """
    Load entries from an encyclopedia (file path or AmiEncyclopedia instance).

    Args:
        source: Path to HTML file, path to JSON file (aggregated export from
            count_climate_encyclopedia_entries.py --export), or AmiEncyclopedia
            instance with .entries.

    Returns:
        List of entry dicts, each with at least term and optional
        description_html, definition_html, wikipedia_url, wikidata_id.
    """
    if isinstance(source, Path):
        source = str(source)
    if isinstance(source, str):
        path = Path(source)
        if path.suffix.lower() == ".json" and path.exists():
            return load_entries_from_json(path)
        enc = AmiEncyclopedia()
        enc.create_from_html_file(path)
        return list(enc.entries) if enc.entries else []
    if hasattr(source, "entries"):
        return list(source.entries) if source.entries else []
    return []


def load_entries_from_json(json_path: Path) -> List[Dict[str, Any]]:
    """
    Load entries from the aggregated JSON export (e.g. temp/chatbot/climate_encyclopedia_entries.json).

    Expects JSON with top-level key "entries" containing a list of entry dicts.

    Args:
        json_path: Path to the JSON file.

    Returns:
        List of entry dicts.
    """
    import json as json_module
    text = json_path.read_text(encoding="utf-8")
    data = json_module.loads(text)
    entries = data.get("entries", data) if isinstance(data, dict) else data
    if not isinstance(entries, list):
        return []
    return entries


def _strip_html(html: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def entries_to_sections(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert entries to a flat list of sections with labels for retrieval.

    Each section dict has: section_label, text, entry_id, term.
    entry_id is derived from term (e.g. normalized) or index if missing.

    Args:
        entries: List of entry dicts from load_entries_from_encyclopedia.

    Returns:
        List of section dicts with section_label, text, entry_id, term.
    """
    sections = []
    for idx, entry in enumerate(entries):
        term = entry.get("term") or entry.get("search_term") or ""
        entry_id = entry.get("wikidata_id") or entry.get("wikipedia_url") or f"entry_{idx}"
        if isinstance(entry_id, str) and len(entry_id) > 80:
            entry_id = f"entry_{idx}"

        if term:
            label_term = "term"
            sections.append({
                "section_label": label_term,
                "text": term,
                "entry_id": str(entry_id),
                "term": term,
            })

        desc = entry.get("description_html")
        if desc:
            text = _strip_html(desc)
            if text:
                sections.append({
                    "section_label": "description",
                    "text": text,
                    "entry_id": str(entry_id),
                    "term": term,
                })

        defin = entry.get("definition_html")
        if defin:
            text = _strip_html(defin)
            if text:
                sections.append({
                    "section_label": "definition",
                    "text": text,
                    "entry_id": str(entry_id),
                    "term": term,
                })

    return sections
