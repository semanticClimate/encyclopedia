# Diagnostic Tests for Missing Descriptions and Images

**Date:** Tuesday, January 20, 2026, 10:17:59 GMT (system date)

## Purpose

These tests are designed to diagnose two specific issues:
1. **Climate (Q7937) entry doesn't have a description** despite having a Wikipedia URL
2. **No entries have images** despite using `--add-images` flag

## Test File

`test_missing_descriptions_and_images_diagnostic.py`

## Running the Tests

### Run All Diagnostic Tests
```bash
cd /Users/pm286/workspace/encyclopedia
python -m pytest test/encyclopedia/test_missing_descriptions_and_images_diagnostic.py -v -s
```

The `-s` flag shows print statements (diagnostic output).

### Run Specific Test Class
```bash
# Test missing descriptions
python -m pytest test/encyclopedia/test_missing_descriptions_and_images_diagnostic.py::TestMissingDescriptionsDiagnostic -v -s

# Test missing images
python -m pytest test/encyclopedia/test_missing_descriptions_and_images_diagnostic.py::TestMissingImagesDiagnostic -v -s

# Test real-world scenario
python -m pytest test/encyclopedia/test_missing_descriptions_and_images_diagnostic.py::TestRealWorldScenarioDiagnostic -v -s
```

### Run Specific Test
```bash
# Test Climate entry specifically
python -m pytest test/encyclopedia/test_missing_descriptions_and_images_diagnostic.py::TestMissingDescriptionsDiagnostic::test_climate_entry_should_have_description -v -s

# Test full pipeline for descriptions
python -m pytest test/encyclopedia/test_missing_descriptions_and_images_diagnostic.py::TestMissingDescriptionsDiagnostic::test_full_pipeline_missing_descriptions -v -s

# Test full pipeline for images
python -m pytest test/encyclopedia/test_missing_descriptions_and_images_diagnostic.py::TestMissingImagesDiagnostic::test_full_pipeline_missing_images -v -s
```

## Test Structure

### TestMissingDescriptionsDiagnostic

1. **`test_climate_entry_should_have_description`**
   - Tests that Climate entry gets a description when `add_wikipedia_feature()` is called
   - **Diagnostic assertions:**
     - Checks if Wikipedia page lookup is called
     - Checks if paragraph extraction is called
     - Checks if description HTML is added
     - Prints diagnostic output showing what happened

2. **`test_entry_with_url_but_no_description_gets_fetched`**
   - Tests that entries with Wikipedia URL but no description are processed
   - **Diagnostic assertions:**
     - Tracks calls to `add_wikipedia_description_to_entry`
     - Checks if description was actually added
     - Prints initial and final state

3. **`test_add_wikipedia_feature_skips_entry_with_description`**
   - Tests that entries with descriptions are correctly identified and skipped
   - **Diagnostic assertions:**
     - Verifies the skip logic works correctly

4. **`test_full_pipeline_missing_descriptions`**
   - Tests the full pipeline from `create_encyclopedia_from_wordlist()`
   - **Diagnostic assertions:**
     - Tracks all Wikipedia feature calls
     - Tracks all description add calls
     - Shows final state of all entries
     - Identifies which entries are missing descriptions

### TestMissingImagesDiagnostic

1. **`test_entry_should_get_image_added`**
   - Tests that entries get images added when `add_images_feature()` is called
   - **Diagnostic assertions:**
     - Checks if Wikipedia page lookup is called
     - Checks if image extraction is called
     - Checks if images are found
     - Checks if `figure_html` is added

2. **`test_add_image_links_processes_all_entries`**
   - Tests that `add_image_links_to_encyclopedia()` processes all entries
   - **Diagnostic assertions:**
     - Tracks calls to `add_image_link_to_entry`
     - Verifies all entries are processed
     - Checks results dictionary

3. **`test_full_pipeline_missing_images`**
   - Tests the full pipeline with `--add-images` flag
   - **Diagnostic assertions:**
     - Tracks all image feature calls
     - Tracks all image add calls
     - Shows final state of all entries
     - Identifies which entries are missing images

4. **`test_image_extraction_returns_empty_list`**
   - Tests behavior when no images are found
   - **Diagnostic assertions:**
     - Verifies graceful handling of empty image list

### TestRealWorldScenarioDiagnostic

1. **`test_climate_entry_from_real_file`**
   - Tests the actual Climate entry from `temp/climate_encyclopedia.html`
   - **Diagnostic assertions:**
     - Loads the actual generated file
     - Finds Climate entry (Q7937)
     - Shows all its properties
     - Identifies what's missing

2. **`test_all_entries_have_images_from_real_file`**
   - Tests all entries from the actual generated file
   - **Diagnostic assertions:**
     - Loads the actual generated file
     - Checks each entry for images
     - Lists entries without images
     - Shows which entries have Wikipedia URLs but no images

## Understanding Diagnostic Output

The tests print diagnostic information using `print()` statements. Look for:

### For Descriptions:
```
=== DIAGNOSTIC OUTPUT ===
Entry term: climate
Wikipedia URL: https://en.wikipedia.org/wiki/Climate
Has description after: False
Description HTML length: 0
Description HTML content: None
========================
```

This shows:
- Whether the entry has a Wikipedia URL
- Whether description was added
- What the description HTML contains

### For Images:
```
=== IMAGE PROCESSING DIAGNOSTICS ===
Total calls: 2
Expected calls: 2
  - {'term': 'climate change', 'has_url': True, 'has_image_before': False}
  - {'term': 'greenhouse gas', 'has_url': True, 'has_image_before': False}
Results: {'total': 2, 'successful': 2, 'with_images': 2, ...}
Entries with images after: 2
====================================
```

This shows:
- How many entries were processed
- Whether images were added
- What the results dictionary contains

## What to Look For

### When Tests Fail

1. **If `test_climate_entry_should_have_description` fails:**
   - Check if `add_wikipedia_feature()` is being called
   - Check if Wikipedia page lookup succeeds
   - Check if paragraph extraction succeeds
   - Check if description HTML is actually added to the entry

2. **If `test_full_pipeline_missing_descriptions` fails:**
   - Check if `add_wikipedia_descriptions_to_encyclopedia()` is called
   - Check if entries with URLs but no descriptions are included
   - Check if descriptions are added during processing
   - Check if descriptions are preserved after processing

3. **If `test_entry_should_get_image_added` fails:**
   - Check if `add_images_feature()` is being called
   - Check if Wikipedia page lookup succeeds
   - Check if image extraction succeeds
   - Check if `figure_html` is added to the entry

4. **If `test_full_pipeline_missing_images` fails:**
   - Check if `add_image_links_to_encyclopedia()` is called
   - Check if entries are processed
   - Check if images are added during processing
   - Check if images are preserved after processing

### Diagnostic Assertions

Each test includes assertions that will help identify where the problem occurs:

- **Initial state checks**: Verify entry state before processing
- **Function call checks**: Verify functions are called
- **Intermediate state checks**: Verify state during processing
- **Final state checks**: Verify final state after processing
- **Print statements**: Show diagnostic information

## Expected Behavior

### For Descriptions:
- Entries with Wikipedia URLs but no descriptions should get descriptions added
- `add_wikipedia_feature()` should be called for entries needing descriptions
- `add_wikipedia_descriptions_to_encyclopedia()` should process all entries
- Descriptions should be preserved in the final encyclopedia

### For Images:
- Entries should get images added when `--add-images` is used
- `add_images_feature()` should be called for entries needing images
- `add_image_links_to_encyclopedia()` should process all entries
- Images should be preserved in the final encyclopedia

## Next Steps

After running these tests:

1. **Review the diagnostic output** to see where the process fails
2. **Check the assertions** to see which checks fail
3. **Identify the root cause** based on the diagnostic information
4. **Fix the code** based on the diagnostic findings
5. **Re-run the tests** to verify the fix

## Notes

- These tests use mocking to avoid actual Wikipedia API calls
- The real-world scenario tests require the actual generated file
- Diagnostic output is printed even when tests pass (use `-s` flag)
- Tests are designed to fail with helpful error messages showing what's wrong
