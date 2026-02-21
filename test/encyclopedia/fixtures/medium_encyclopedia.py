"""
Medium encyclopedia fixture generator (50-100 entries).

Creates a medium encyclopedia for realistic testing and performance checks.
Uses caching to avoid recreating encyclopedias on every test run.
"""

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from Examples.create_encyclopedia_from_wordlist import create_encyclopedia_from_wordlist
from test.encyclopedia.fixtures.cache import (
    load_cached_encyclopedia,
    save_encyclopedia_to_cache
)


# Diverse terms across multiple categories
MEDIUM_ENCYCLOPEDIA_TERMS = [
    # Climate-related (10 entries)
    "climate change",
    "global warming",
    "greenhouse gas",
    "carbon dioxide",
    "methane",
    "ice sheet",
    "sea level rise",
    "ocean acidification",
    "atmosphere",
    "precipitation",
    
    # Science-related (15 entries)
    "atom",
    "molecule",
    "DNA",
    "protein",
    "cell",
    "evolution",
    "photosynthesis",
    "ecosystem",
    "biodiversity",
    "genetics",
    "microscope",
    "telescope",
    "laboratory",
    "experiment",
    "hypothesis",
    
    # Technology-related (10 entries)
    "computer",
    "algorithm",
    "software",
    "hardware",
    "network",
    "internet",
    "database",
    "programming",
    "artificial intelligence",
    "machine learning",
    
    # Geography-related (10 entries)
    "continent",
    "ocean",
    "mountain",
    "river",
    "desert",
    "forest",
    "island",
    "volcano",
    "glacier",
    "plateau",
    
    # Additional diverse terms (15 entries)
    "energy",
    "solar power",
    "wind energy",
    "renewable energy",
    "fossil fuel",
    "pollution",
    "conservation",
    "sustainability",
    "biodiversity",
    "climate adaptation",
    "weather",
    "meteorology",
    "geology",
    "chemistry",
    "physics"
]


def create_medium_encyclopedia(
    add_wikipedia: bool = True,
    add_images: bool = True,
    validate: bool = False,
    verbose: bool = False,
    use_cache: bool = True
) -> AmiEncyclopedia:
    """
    Create medium encyclopedia for realistic tests.
    
    Uses caching to avoid recreating encyclopedias on every test run.
    
    Args:
        add_wikipedia: If True, add Wikipedia descriptions (default: True)
        add_images: If True, add images from Wikipedia (default: True)
        validate: If True, validate results (default: False for speed)
        verbose: If True, show detailed progress (default: False)
        use_cache: If True, use cached version if available (default: True)
        
    Returns:
        AmiEncyclopedia instance with 50-100 entries
    """
    title = "Medium Test Encyclopedia"
    
    # Try to load from cache
    if use_cache:
        cached = load_cached_encyclopedia(
            terms=MEDIUM_ENCYCLOPEDIA_TERMS,
            add_wikipedia=add_wikipedia,
            add_images=add_images,
            title=title
        )
        if cached is not None:
            if verbose:
                print(f"Loaded medium encyclopedia from cache ({len(cached.entries)} entries)")
            return cached
    
    # Create new encyclopedia
    if verbose:
        print("Creating new medium encyclopedia (this may take a while)...")
    
    encyclopedia = create_encyclopedia_from_wordlist(
        terms=MEDIUM_ENCYCLOPEDIA_TERMS,
        title=title,
        add_wikipedia=add_wikipedia,
        add_images=add_images,
        batch_size=20,
        validate=validate,
        verbose=verbose
    )
    
    # Save to cache and temp directory
    if use_cache:
        cache_file = save_encyclopedia_to_cache(
            encyclopedia=encyclopedia,
            terms=MEDIUM_ENCYCLOPEDIA_TERMS,
            add_wikipedia=add_wikipedia,
            add_images=add_images,
            title=title,
            save_to_temp=True
        )
        if verbose:
            print(f"Saved medium encyclopedia to cache: {cache_file}")
            from test.encyclopedia.fixtures.cache import TEMP_FIXTURES_DIR
            temp_file = TEMP_FIXTURES_DIR / "medium_test_encyclopedia.html"
            print(f"Saved readable copy to temp: {temp_file}")
    
    return encyclopedia
