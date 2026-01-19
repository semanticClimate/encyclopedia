# Tests for Batch-Size, Missing Descriptions, and Missing Images

## Overview

This test suite (`test_batch_size_and_features.py`) contains comprehensive tests for three critical features:

1. **Batch-Size Functionality** - Verifies that batch processing respects the `batch_size` parameter
2. **Missing Descriptions** - Ensures entries with Wikipedia URLs but no descriptions are properly fetched
3. **Missing Images** - Ensures entries without images get images added when requested

## Test Structure

### TestBatchSize
Tests that verify batch-size is respected when processing entries:

- `test_batch_size_respected_for_wikipedia_descriptions()` - Verifies batch processing for Wikipedia descriptions
- `test_batch_size_respected_for_images()` - Verifies batch processing for images

**Key Assertions:**
- Batch size parameter controls how many entries are processed at once
- Delays are added between batches (not within batches)
- All entries are processed regardless of batch size

### TestMissingDescriptions
Tests that verify missing descriptions are properly handled:

- `test_entry_with_url_but_no_description_gets_fetched()` - Entry with URL but no description gets fetched
- `test_entry_with_empty_description_gets_fetched()` - Entry with empty description gets re-fetched
- `test_has_non_empty_description_check()` - Helper function correctly identifies empty descriptions
- `test_add_wikipedia_descriptions_handles_missing_descriptions()` - Batch processing handles missing descriptions

**Key Assertions:**
- Entries with Wikipedia URLs but no descriptions are re-fetched
- Empty descriptions are treated as missing
- The `_has_non_empty_description()` helper correctly identifies empty descriptions

### TestMissingImages
Tests that verify missing images are properly handled:

- `test_entry_without_images_gets_image_added()` - Entry without images gets image added
- `test_entry_with_existing_images_skipped()` - Entries with existing images are skipped
- `test_add_image_links_handles_missing_images()` - Batch processing handles missing images
- `test_image_extraction_handles_missing_wikipedia_page()` - Gracefully handles missing Wikipedia pages
- `test_image_extraction_handles_no_images_found()` - Gracefully handles cases where no images are found

**Key Assertions:**
- Entries without images get images added
- Entries with existing images are skipped (not re-processed)
- Missing Wikipedia pages are handled gracefully
- Cases where no images are found are handled gracefully

### TestIntegration
Integration tests that combine multiple features:

- `test_full_workflow_with_batch_size()` - Full workflow with batch-size for both descriptions and images

**Key Assertions:**
- Batch processing works correctly for both descriptions and images
- All entries get descriptions and images added
- Batch delays are properly applied

## Running the Tests

### Basic Usage
```bash
cd /Users/pm286/workspace/encyclopedia
python -m pytest test/encyclopedia/test_batch_size_and_features.py -v
```

### Run Specific Test Class
```bash
python -m pytest test/encyclopedia/test_batch_size_and_features.py::TestBatchSize -v
python -m pytest test/encyclopedia/test_batch_size_and_features.py::TestMissingDescriptions -v
python -m pytest test/encyclopedia/test_batch_size_and_features.py::TestMissingImages -v
```

### Run Specific Test
```bash
python -m pytest test/encyclopedia/test_batch_size_and_features.py::TestBatchSize::test_batch_size_respected_for_wikipedia_descriptions -v
```

### Run with Coverage
```bash
python -m pytest test/encyclopedia/test_batch_size_and_features.py --cov=encyclopedia.utils.encyclopedia_builder --cov=encyclopedia.cli.versioned_editor -v
```

## Test Dependencies

The tests use `unittest.mock` to mock Wikipedia API calls, so they don't require actual network access. This makes them:
- Fast (no network delays)
- Reliable (no dependency on Wikipedia availability)
- Deterministic (consistent results)

## Key Mocking Strategy

1. **Wikipedia Page Lookups**: Mocked using `patch('encyclopedia.cli.versioned_editor._get_wikipedia_page_for_entry')`
2. **Image Extraction**: Mocked using `patch('encyclopedia.cli.versioned_editor._extract_images_from_wikipedia_page')`
3. **Time Delays**: Mocked using `patch('time.sleep')` to verify delays are added without actually waiting
4. **Entry Processing**: Mocked using `patch('encyclopedia.utils.encyclopedia_builder.add_wikipedia_description_to_entry')` and `add_image_link_to_entry`

## Expected Test Results

All tests should pass when:
- The batch-size functionality correctly processes entries in batches
- Missing descriptions are properly fetched
- Missing images are properly added
- Batch delays are properly applied

## Troubleshooting

### Permission Errors
If you see `PermissionError` related to SSL/requests, this is likely due to sandbox restrictions. The tests should run fine in a normal environment.

### Import Errors
Make sure you're running from the project root directory:
```bash
cd /Users/pm286/workspace/encyclopedia
python -m pytest test/encyclopedia/test_batch_size_and_features.py -v
```

### Mock Errors
If mocks aren't working correctly, verify that the patch paths match the actual import paths in the code.

## Related Files

- `encyclopedia/utils/encyclopedia_builder.py` - Contains `add_wikipedia_descriptions_to_encyclopedia()` and `add_image_links_to_encyclopedia()`
- `encyclopedia/cli/versioned_editor.py` - Contains `add_wikipedia_feature()` and `add_images_feature()`
- `Examples/create_encyclopedia_from_wordlist.py` - Uses these functions in the main script
