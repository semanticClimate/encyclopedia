# Saved Encyclopedia Files

All test encyclopedias are automatically saved to disk in two locations:

## 1. Cache Directory (Fast Loading)

**Location:** `test/encyclopedia/fixtures/cache/`

- Hash-based filenames for fast lookup
- Used by fixtures for quick loading
- Format: `encyclopedia_<hash>.html` + `encyclopedia_<hash>.json`

## 2. Temp Directory (Human Readable)

**Location:** `temp/test/encyclopedia/fixtures/`

- Descriptive filenames for easy identification
- Same content as cache, but easier to find and inspect
- Automatically created when encyclopedias are generated

### Saved Files

When fixtures create encyclopedias, the following files are saved:

- `small_test_encyclopedia.html` - Small encyclopedia (10 entries)
- `small_test_encyclopedia_metadata.json` - Metadata for small encyclopedia
- `medium_test_encyclopedia.html` - Medium encyclopedia (60 entries)
- `medium_test_encyclopedia_metadata.json` - Metadata for medium encyclopedia
- `large_test_encyclopedia.html` - Large encyclopedia (500 entries)
- `large_test_encyclopedia_metadata.json` - Metadata for large encyclopedia

## Viewing Saved Files

All HTML files can be opened in a web browser for inspection. Metadata JSON files contain:
- Terms used to create the encyclopedia
- Parameters (add_wikipedia, add_images)
- Entry count
- Cache key

## Listing Saved Files

```python
from test.encyclopedia.fixtures.cache import list_saved_encyclopedias, get_cache_info

# List all saved encyclopedia files
saved_files = list_saved_encyclopedias()
for file in saved_files:
    print(f"  {file.name} ({file.stat().st_size} bytes)")

# Get cache statistics
info = get_cache_info()
print(f"Cached: {info['cached_count']} files")
print(f"Temp: {info['temp_count']} files")
print(f"Temp directory: {info['temp_dir']}")
```

## Benefits

1. **Human Inspection**: All encyclopedias saved with readable names in temp directory
2. **Fast Loading**: Cache directory provides quick access for tests
3. **Persistence**: Files persist across test runs
4. **Debugging**: Easy to inspect encyclopedia content during test development
