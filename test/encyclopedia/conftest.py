"""
Pytest configuration for encyclopedia tests.
Path setup is handled by pytest.ini pythonpath setting.
"""

import pytest
from pathlib import Path

from encyclopedia.core.encyclopedia import AmiEncyclopedia

# Import fixtures using relative imports from the fixtures directory
# Since pytest.ini sets pythonpath to ".", we can import from test.encyclopedia.fixtures
from test.encyclopedia.fixtures.small_encyclopedia import (
    create_small_encyclopedia,
    SMALL_ENCYCLOPEDIA_TERMS
)
from test.encyclopedia.fixtures.medium_encyclopedia import (
    create_medium_encyclopedia,
    MEDIUM_ENCYCLOPEDIA_TERMS
)
from test.encyclopedia.fixtures.large_encyclopedia import (
    create_large_encyclopedia,
    LARGE_ENCYCLOPEDIA_TERMS
)
from test.encyclopedia.fixtures.cache import (
    load_cached_encyclopedia
)


# Session-scoped fixtures for ensuring cached encyclopedias exist (expensive operation)
@pytest.fixture(scope="session", autouse=True)
def _ensure_cached_encyclopedias():
    """Ensure cached encyclopedias exist (runs once per session)."""
    # Create and cache small encyclopedia if not already cached
    create_small_encyclopedia(add_wikipedia=True, add_images=True, validate=False, verbose=False, use_cache=True)
    
    # Create and cache medium encyclopedia if not already cached
    create_medium_encyclopedia(add_wikipedia=True, add_images=True, validate=False, verbose=False, use_cache=True)
    
    # Create and cache large encyclopedia if not already cached
    create_large_encyclopedia(add_wikipedia=True, add_images=False, validate=False, verbose=False, use_cache=True)


# Function-scoped fixtures that load fresh copies from cache for each test (immutable inputs)
@pytest.fixture(scope="function")
def small_encyclopedia():
    """Return a fresh copy of small encyclopedia loaded from cache for each test (function-scoped, immutable)."""
    # Load from cache (ensures fresh, immutable copy for each test)
    cached = load_cached_encyclopedia(
        terms=SMALL_ENCYCLOPEDIA_TERMS,
        add_wikipedia=True,
        add_images=True,
        title="Small Test Encyclopedia"
    )
    
    if cached is None:
        # If cache doesn't exist, create it (shouldn't happen due to autouse fixture)
        cached = create_small_encyclopedia(add_wikipedia=True, add_images=True, validate=False, verbose=False, use_cache=True)
    
    return cached


@pytest.fixture(scope="function")
def medium_encyclopedia():
    """Return a fresh copy of medium encyclopedia loaded from cache for each test (function-scoped, immutable)."""
    # Load from cache (ensures fresh, immutable copy for each test)
    cached = load_cached_encyclopedia(
        terms=MEDIUM_ENCYCLOPEDIA_TERMS,
        add_wikipedia=True,
        add_images=True,
        title="Medium Test Encyclopedia"
    )
    
    if cached is None:
        # If cache doesn't exist, create it (shouldn't happen due to autouse fixture)
        cached = create_medium_encyclopedia(add_wikipedia=True, add_images=True, validate=False, verbose=False, use_cache=True)
    
    return cached


@pytest.fixture(scope="function")
def large_encyclopedia():
    """Return a fresh copy of large encyclopedia loaded from cache for each test (function-scoped, immutable)."""
    # Load from cache (ensures fresh, immutable copy for each test)
    cached = load_cached_encyclopedia(
        terms=LARGE_ENCYCLOPEDIA_TERMS,
        add_wikipedia=True,
        add_images=False,
        title="Large Test Encyclopedia"
    )
    
    if cached is None:
        # If cache doesn't exist, create it (shouldn't happen due to autouse fixture)
        cached = create_large_encyclopedia(add_wikipedia=True, add_images=False, validate=False, verbose=False, use_cache=True)
    
    return cached
