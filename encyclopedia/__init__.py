"""
Encyclopedia package for creating structured encyclopedias from terms.

This package provides functionality to:
- Create dictionaries from terms
- Enhance with Wikipedia/Wikidata/Wiktionary
- Normalize and merge synonyms
- Generate HTML encyclopedias
"""

__version__ = "0.0.2"  # 2026-01-23

# Lazy import to avoid circular dependencies
def __getattr__(name):
    if name == "AmiEncyclopedia":
        from encyclopedia.core.encyclopedia import AmiEncyclopedia
        return AmiEncyclopedia
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ["AmiEncyclopedia"]

