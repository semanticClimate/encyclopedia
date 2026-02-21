# Test Encyclopedia Fixtures

This directory contains fixtures for creating test encyclopedias of various sizes.

## Fixtures

- **`small_encyclopedia.py`** - Small encyclopedia (10 entries) for fast tests
- **`medium_encyclopedia.py`** - Medium encyclopedia (60 entries) for realistic tests
- **`large_encyclopedia.py`** - Large encyclopedia (500 entries) for performance tests
- **`helpers.py`** - Helper functions for creating test entries
- **`cache.py`** - Caching utilities for test encyclopedias

## Caching

All fixtures use caching to avoid recreating encyclopedias on every test run. Cached encyclopedias are stored in the `cache/` subdirectory.

### Cache Behavior

- **Cache Key**: Generated from terms list, `add_wikipedia`, `add_images`, and `title` parameters
- **Cache Location**: `test/encyclopedia/fixtures/cache/`
- **Cache Format**: HTML files (same format as saved encyclopedias) + JSON metadata files
- **Cache Validation**: Metadata is checked to ensure cache matches parameters

### Using Cache

By default, all fixtures use caching (`use_cache=True`). To disable caching:

```python
encyclopedia = create_small_encyclopedia(use_cache=False)
```

### Cache Management

```python
from test.encyclopedia.fixtures.cache import clear_cache, get_cache_info

# Get cache information
info = get_cache_info()
print(f"Cached encyclopedias: {info['cached_count']}")
print(f"Total cache size: {info['total_size']} bytes")

# Clear all cached encyclopedias
clear_cache()
```

## Cache Directory Structure

```
fixtures/
├── cache/
│   ├── encyclopedia_<hash>.html    # Cached encyclopedia HTML files (for fast loading)
│   ├── encyclopedia_<hash>.json   # Metadata files
│   └── ...
├── small_encyclopedia.py
├── medium_encyclopedia.py
├── large_encyclopedia.py
├── helpers.py
└── cache.py

temp/test/encyclopedia/fixtures/
├── small_test_encyclopedia.html      # Human-readable copy
├── small_test_encyclopedia_metadata.json
├── medium_test_encyclopedia.html     # Human-readable copy
├── medium_test_encyclopedia_metadata.json
├── large_test_encyclopedia.html      # Human-readable copy
└── large_test_encyclopedia_metadata.json
```

### Two Storage Locations

1. **Cache Directory** (`test/encyclopedia/fixtures/cache/`):
   - Fast-loading cached files with hash-based names
   - Used by fixtures for quick loading
   - Not meant for human inspection

2. **Temp Directory** (`temp/test/encyclopedia/fixtures/`):
   - Human-readable copies with descriptive names
   - Same content as cache, but easier to find and inspect
   - Saved automatically when encyclopedias are created

## Benefits of Caching

1. **Faster Test Execution**: Avoids slow Wikipedia lookups on every test run
2. **Network Independence**: Tests can run without network access once cached
3. **Consistent Results**: Same encyclopedia data across test runs
4. **Development Speed**: Faster iteration during test development

## Cache Invalidation

Cache is automatically invalidated if:
- Parameters don't match (different terms, add_wikipedia, add_images, or title)
- Cache file is corrupted or missing
- Metadata file is corrupted or missing

To manually invalidate cache, delete files from `cache/` directory or use `clear_cache()`.
