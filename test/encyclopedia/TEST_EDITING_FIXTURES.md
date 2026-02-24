# Editing Tests Fixtures Documentation

**Date:** February 21, 2026 (system date)  
**Status:** Test Fixtures Documentation

## Overview

This document describes the fixtures used for editing tests and whether new fixtures are needed.

## Existing Fixtures Used

### ✅ `small_encyclopedia` (from `conftest.py`)

**Source:** `test/encyclopedia/fixtures/small_encyclopedia.py`

**Description:** Small encyclopedia with 10 entries (atom, climate, DNA, ecosystem, greenhouse gas, methane, ocean, photosynthesis, protein, telescope)

**Used in:**
- `test_editing_delete.py` - All delete tests
- `test_editing_hide.py` - All hide/show tests
- `test_editing_mark_needs_editing.py` - All mark needs editing tests
- `test_editing_add_from_wikipedia.py` - All add from Wikipedia tests
- `test_editing_merge.py` - Some merge tests

**Why suitable:**
- Fast to load (cached)
- Has entries with Wikipedia content
- Has entries with Wikidata IDs
- Good for basic functionality tests

### ✅ `medium_encyclopedia` (from `conftest.py`)

**Source:** `test/encyclopedia/fixtures/medium_encyclopedia.py`

**Description:** Medium encyclopedia with 60 entries across multiple categories

**Used in:**
- `test_editing_merge.py` - Some merge tests (if needed)

**Why suitable:**
- More realistic size for merge tests
- Diverse entries
- Good for performance tests

## New Fixtures Needed

### ⚠️ None Required (Using Existing Fixtures)

All editing tests can use existing fixtures (`small_encyclopedia` and `medium_encyclopedia`). The tests create additional test data inline where needed (e.g., creating source encyclopedias for merge tests).

## Test Output Locations

All test outputs are saved to `temp/test/encyclopedia/` for human inspection:

### Delete Tests
- `temp/test/encyclopedia/TestDeleteEntry/`
  - `soft_delete_test.html`
  - `hard_delete_test.html`
  - `restore_deleted_test.html`
  - `deleted_entries.json`
  - `version_bump_metadata.json`

### Hide Tests
- `temp/test/encyclopedia/TestHideEntry/`
  - `hide_entry_test.html`
  - `show_entry_test.html`
  - `hidden_entries.json`
  - `version_bump_hide_metadata.json`

### Mark Needs Editing Tests
- `temp/test/encyclopedia/TestMarkNeedsEditing/`
  - `mark_needs_editing_test.html`
  - `entries_needing_editing.json`
  - `version_bump_mark_metadata.json`

### Add From Wikipedia Tests
- `temp/test/encyclopedia/TestAddEntryFromWikipedia/`
  - `add_new_term_test.html`
  - `duplicate_by_wikidata_id.json`
  - `duplicate_by_term.json`
  - `version_bump_add_metadata.json`

### Merge Tests
- `temp/test/encyclopedia/TestMergeEncyclopedia/`
  - `merge_no_overlap_test.html`
  - `merge_with_duplicates_result.json`
  - `merge_metadata.json`
  - `merge_conflict_resolution.json`
  - `version_bump_merge_metadata.json`

## Fixture Creation Strategy

### Inline Test Data

For tests that need specific scenarios (e.g., merge tests), test data is created inline:

```python
# Create source encyclopedia inline
source_encyclopedia = AmiEncyclopedia(title="Source Encyclopedia")
source_entry = {
    'term': 'test_term',
    # ... entry data
}
source_encyclopedia.entries.append(source_entry)
```

**Benefits:**
- No need for additional fixtures
- Tests are self-contained
- Easy to understand test scenarios
- Flexible for different test cases

### Using Existing Fixtures

For general functionality tests, use existing fixtures:

```python
def test_delete_entry(self, small_encyclopedia):
    # Use small_encyclopedia fixture
    entry = small_encyclopedia.entries[0]
    # ... test code
```

**Benefits:**
- Fast (cached fixtures)
- Consistent test data
- Real-world scenarios

## Output Files for Human Inspection

All tests save outputs to `temp/test/encyclopedia/` with descriptive filenames:

1. **HTML Files**: Full encyclopedia HTML after operations
2. **JSON Files**: Metadata, results, and intermediate data
3. **Metadata Files**: Version info, operation results

**Purpose:**
- Verify operations worked correctly
- Inspect HTML structure
- Check metadata persistence
- Debug test failures

## Notes

- All fixtures use caching (via `test/encyclopedia/fixtures/cache.py`)
- Fixtures are session-scoped (created once per test session)
- Test outputs are saved to temp directory (not committed to git)
- All outputs use Path constructor (no string concatenation)
- All dates use system date (via `datetime.now(timezone.utc)`)
