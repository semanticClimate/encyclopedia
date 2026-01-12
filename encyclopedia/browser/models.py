"""
Data models for encyclopedia browser.

Defines data structures for entries and search results.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class EncyclopediaEntry:
    """Represents a single encyclopedia entry."""
    entry_id: str
    term: str
    canonical_term: str
    search_terms: List[str]
    wikidata_id: str
    wikipedia_url: str
    description_html: str
    description_text: str  # Plain text version for search
    synonyms: List[str]
    category: Optional[str] = None
    entry_index: int = 0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SearchResult:
    """Represents a search result."""
    entry: EncyclopediaEntry
    score: float  # Relevance score (0-100)
    match_type: str  # "exact", "stemmed", "fuzzy"
    matched_fields: List[str]  # Which fields matched
    highlights: Optional[Dict[str, List[str]]] = None  # Highlighted snippets
