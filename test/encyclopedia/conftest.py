"""
Pytest configuration for encyclopedia tests.
Path setup is handled by pytest.ini pythonpath setting.
"""

import pytest
from pathlib import Path

from encyclopedia.core.encyclopedia import AmiEncyclopedia

# Import fixtures using relative imports from the fixtures directory
# Since pytest.ini sets pythonpath to ".", we can import from test.encyclopedia.fixtures
from test.encyclopedia.fixtures.small_encyclopedia import create_small_encyclopedia
from test.encyclopedia.fixtures.medium_encyclopedia import create_medium_encyclopedia
from test.encyclopedia.fixtures.large_encyclopedia import create_large_encyclopedia


@pytest.fixture(scope="session")
def small_encyclopedia():
    """Create small encyclopedia for fast tests."""
    return create_small_encyclopedia(add_wikipedia=True, add_images=True, validate=False, verbose=False)


@pytest.fixture(scope="session")
def medium_encyclopedia():
    """Create medium encyclopedia for realistic tests."""
    return create_medium_encyclopedia(add_wikipedia=True, add_images=True, validate=False, verbose=False)


@pytest.fixture(scope="session")
def large_encyclopedia():
    """Create large encyclopedia for performance tests."""
    return create_large_encyclopedia(add_wikipedia=True, add_images=False, validate=False, verbose=False)

