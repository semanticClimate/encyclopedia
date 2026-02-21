"""
Caching utilities for test encyclopedia fixtures.

Caches created encyclopedias to disk to avoid recreating them on every test run.
Also saves readable copies to temp directory for human inspection.
"""

import hashlib
import json
from pathlib import Path
from typing import List, Optional

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources


# Cache directory for test fixtures (for fast loading)
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Temp directory for human-readable copies
TEMP_FIXTURES_DIR = Resources.get_temp_dir("test", "encyclopedia", "fixtures")
TEMP_FIXTURES_DIR.mkdir(parents=True, exist_ok=True)


def _generate_cache_key(
    terms: List[str],
    add_wikipedia: bool,
    add_images: bool,
    title: str
) -> str:
    """
    Generate a cache key from encyclopedia parameters.
    
    Args:
        terms: List of terms
        add_wikipedia: Whether Wikipedia descriptions were added
        add_images: Whether images were added
        title: Encyclopedia title
        
    Returns:
        Cache key (hash string)
    """
    # Create a unique identifier from parameters
    cache_data = {
        'terms': sorted(terms),  # Sort for consistency
        'add_wikipedia': add_wikipedia,
        'add_images': add_images,
        'title': title
    }
    cache_string = json.dumps(cache_data, sort_keys=True)
    cache_hash = hashlib.sha256(cache_string.encode('utf-8')).hexdigest()
    return cache_hash[:16]  # Use first 16 chars for shorter filenames


def _get_cache_file_path(cache_key: str) -> Path:
    """
    Get the cache file path for a given cache key.
    
    Args:
        cache_key: Cache key
        
    Returns:
        Path to cached HTML file
    """
    return CACHE_DIR / f"encyclopedia_{cache_key}.html"


def _get_cache_metadata_path(cache_key: str) -> Path:
    """
    Get the metadata file path for a given cache key.
    
    Args:
        cache_key: Cache key
        
    Returns:
        Path to metadata JSON file
    """
    return CACHE_DIR / f"encyclopedia_{cache_key}.json"


def load_cached_encyclopedia(
    terms: List[str],
    add_wikipedia: bool,
    add_images: bool,
    title: str
) -> Optional[AmiEncyclopedia]:
    """
    Load encyclopedia from cache if it exists.
    
    Args:
        terms: List of terms
        add_wikipedia: Whether Wikipedia descriptions were added
        add_images: Whether images were added
        title: Encyclopedia title
        
    Returns:
        AmiEncyclopedia instance if cache exists, None otherwise
    """
    cache_key = _generate_cache_key(terms, add_wikipedia, add_images, title)
    cache_file = _get_cache_file_path(cache_key)
    metadata_file = _get_cache_metadata_path(cache_key)
    
    # Check if cache exists
    if not cache_file.exists():
        return None
    
    # Verify metadata matches
    if metadata_file.exists():
        try:
            metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
            expected_key = _generate_cache_key(
                metadata['terms'],
                metadata['add_wikipedia'],
                metadata['add_images'],
                metadata['title']
            )
            if expected_key != cache_key:
                # Cache mismatch - invalidate
                cache_file.unlink(missing_ok=True)
                metadata_file.unlink(missing_ok=True)
                return None
        except Exception:
            # If metadata is corrupted, invalidate cache
            cache_file.unlink(missing_ok=True)
            metadata_file.unlink(missing_ok=True)
            return None
    
    # Load from cache
    try:
        encyclopedia = AmiEncyclopedia(title=title)
        encyclopedia.create_from_html_file(cache_file)
        return encyclopedia
    except Exception as e:
        # If loading fails, invalidate cache
        print(f"Warning: Failed to load cached encyclopedia: {e}")
        cache_file.unlink(missing_ok=True)
        metadata_file.unlink(missing_ok=True)
        return None


def save_encyclopedia_to_cache(
    encyclopedia: AmiEncyclopedia,
    terms: List[str],
    add_wikipedia: bool,
    add_images: bool,
    title: str,
    save_to_temp: bool = True
) -> Path:
    """
    Save encyclopedia to cache and optionally to temp directory.
    
    Args:
        encyclopedia: AmiEncyclopedia instance to cache
        terms: List of terms used to create it
        add_wikipedia: Whether Wikipedia descriptions were added
        add_images: Whether images were added
        title: Encyclopedia title
        save_to_temp: If True, also save readable copy to temp directory (default: True)
        
    Returns:
        Path to cached file
    """
    cache_key = _generate_cache_key(terms, add_wikipedia, add_images, title)
    cache_file = _get_cache_file_path(cache_key)
    metadata_file = _get_cache_metadata_path(cache_key)
    
    # Save encyclopedia HTML to cache
    encyclopedia.save_wiki_normalized_html(cache_file)
    
    # Save metadata
    metadata = {
        'terms': terms,
        'add_wikipedia': add_wikipedia,
        'add_images': add_images,
        'title': title,
        'cache_key': cache_key,
        'entry_count': len(encyclopedia.entries)
    }
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    
    # Also save readable copy to temp directory for human inspection
    if save_to_temp:
        # Create readable filename from title
        safe_title = title.lower().replace(' ', '_').replace('/', '_')
        temp_filename = f"{safe_title}.html"
        temp_file = TEMP_FIXTURES_DIR / temp_filename
        encyclopedia.save_wiki_normalized_html(temp_file)
        
        # Save metadata to temp as well
        temp_metadata_file = TEMP_FIXTURES_DIR / f"{safe_title}_metadata.json"
        temp_metadata_file.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    
    return cache_file


def clear_cache():
    """Clear all cached encyclopedias."""
    if CACHE_DIR.exists():
        for cache_file in CACHE_DIR.glob("encyclopedia_*.html"):
            cache_file.unlink(missing_ok=True)
        for metadata_file in CACHE_DIR.glob("encyclopedia_*.json"):
            metadata_file.unlink(missing_ok=True)


def get_cache_info() -> dict:
    """
    Get information about cached encyclopedias.
    
    Returns:
        Dictionary with cache statistics
    """
    cache_count = 0
    cache_size = 0
    temp_count = 0
    temp_size = 0
    temp_files_list = []
    
    if CACHE_DIR.exists():
        cache_files = list(CACHE_DIR.glob("encyclopedia_*.html"))
        cache_count = len(cache_files)
        cache_size = sum(f.stat().st_size for f in cache_files if f.exists())
    
    if TEMP_FIXTURES_DIR.exists():
        temp_files = list(TEMP_FIXTURES_DIR.glob("*.html"))
        temp_count = len(temp_files)
        temp_size = sum(f.stat().st_size for f in temp_files if f.exists())
        temp_files_list = [f.name for f in temp_files]
    
    return {
        'cached_count': cache_count,
        'total_size': cache_size,
        'cache_dir': str(CACHE_DIR),
        'temp_count': temp_count,
        'temp_size': temp_size,
        'temp_dir': str(TEMP_FIXTURES_DIR),
        'temp_files': temp_files_list
    }


def list_saved_encyclopedias() -> List[Path]:
    """
    List all saved encyclopedia files in temp directory.
    
    Returns:
        List of Path objects to saved encyclopedia HTML files
    """
    if not TEMP_FIXTURES_DIR.exists():
        return []
    
    return sorted(TEMP_FIXTURES_DIR.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
