"""
Encyclopedia package for creating structured encyclopedias from terms.

This package provides functionality to:
- Create dictionaries from terms
- Enhance with Wikipedia/Wikidata/Wiktionary
- Normalize and merge synonyms
- Generate HTML encyclopedias

Non-empty by agreement: __version__ and lazy AmiEncyclopedia import (avoids circular deps).
"""

__version__ = "0.0.7"  # 2026-02-09

# Lazy import to avoid circular dependencies
def __getattr__(name):
    if name == "AmiEncyclopedia":
        from encyclopedia.core.encyclopedia import AmiEncyclopedia
        return AmiEncyclopedia
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ["AmiEncyclopedia"]

