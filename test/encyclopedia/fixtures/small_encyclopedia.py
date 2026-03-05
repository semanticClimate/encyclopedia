"""
Small encyclopedia fixture generator (10-20 entries).

Creates a small encyclopedia for fast tests and basic functionality verification.
Uses caching to avoid recreating encyclopedias on every test run.
"""

from pathlib import Path

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from Examples.create_encyclopedia_from_wordlist import create_encyclopedia_from_wordlist
from test.encyclopedia.fixtures.cache import (
    load_cached_encyclopedia,
    save_encyclopedia_to_cache
)


# Climate-related terms that should have images on Wikipedia
SMALL_ENCYCLOPEDIA_TERMS = [
    "atom",           # Has image, description, Wikidata
    "climate",        # Has description, Wikidata, synonyms
    "DNA",            # Has image, description, Wikidata
    "ecosystem",      # Has description, Wikidata
    "greenhouse gas", # Has image, description, Wikidata, synonyms
    "methane",        # Has image, description, Wikidata
    "ocean",          # Has description, Wikidata
    "photosynthesis", # Has description, Wikidata
    "protein",        # Has image, description, Wikidata
    "telescope"       # Has image, description, Wikidata
]


def create_small_encyclopedia(
    add_wikipedia: bool = True,
    add_images: bool = True,
    validate: bool = False,
    verbose: bool = False,
    use_cache: bool = True
) -> AmiEncyclopedia:
    """
    Create small encyclopedia for fast tests.
    
    Uses caching to avoid recreating encyclopedias on every test run.
    Cache is based on terms, add_wikipedia, add_images, and title parameters.
    
    Args:
        add_wikipedia: If True, add Wikipedia descriptions (default: True)
        add_images: If True, add images from Wikipedia (default: True)
        validate: If True, validate results (default: False for speed)
        verbose: If True, show detailed progress (default: False)
        use_cache: If True, use cached version if available (default: True)
        
    Returns:
        AmiEncyclopedia instance with 10-20 entries
    """
    title = "Small Test Encyclopedia"
    
    # Try to load from cache
    if use_cache:
        cached = load_cached_encyclopedia(
            terms=SMALL_ENCYCLOPEDIA_TERMS,
            add_wikipedia=add_wikipedia,
            add_images=add_images,
            title=title
        )
        if cached is not None:
            if verbose:
                print(f"Loaded small encyclopedia from cache ({len(cached.entries)} entries)")
            return cached
    
    # Create new encyclopedia
    if verbose:
        print("Creating new small encyclopedia (this may take a while)...")
    
    encyclopedia = create_encyclopedia_from_wordlist(
        terms=SMALL_ENCYCLOPEDIA_TERMS,
        title=title,
        add_wikipedia=add_wikipedia,
        add_images=add_images,
        batch_size=10,
        validate=validate,
        verbose=verbose
    )
    
    # Save to cache and temp directory
    if use_cache:
        cache_file = save_encyclopedia_to_cache(
            encyclopedia=encyclopedia,
            terms=SMALL_ENCYCLOPEDIA_TERMS,
            add_wikipedia=add_wikipedia,
            add_images=add_images,
            title=title,
            save_to_temp=True
        )
        if verbose:
            print(f"Saved small encyclopedia to cache: {cache_file}")
            from test.encyclopedia.fixtures.cache import TEMP_FIXTURES_DIR
            temp_file = Path(TEMP_FIXTURES_DIR, "small_test_encyclopedia.html")
            print(f"Saved readable copy to temp: {temp_file}")
    
    return encyclopedia
