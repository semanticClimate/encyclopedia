# Test Failures Summary - January 21, 2026

## Overview

6 tests are currently failing. These need to be fixed when resuming work.

## Failing Tests

### 1. HTML File Structure Issues (3 tests)

**Error:** `ValueError: HTML dictionary needs html/body/div[@role='ami_dictionary']`

**Affected Tests:**
- `test/encyclopedia/test_html_description_and_image_validation.py::TestComprehensiveValidation::test_validation_from_real_file`
- `test/encyclopedia/test_missing_descriptions_and_images_diagnostic.py::TestRealWorldScenarioDiagnostic::test_climate_entry_from_real_file`
- `test/encyclopedia/test_missing_descriptions_and_images_diagnostic.py::TestRealWorldScenarioDiagnostic::test_all_entries_have_images_from_real_file`

**Root Cause:**
- Tests are trying to load HTML files using `encyclopedia.create_from_html_file()`
- The HTML files don't have the required structure: `html/body/div[@role='ami_dictionary']`
- Files like `temp/climate_encyclopedia.html` are encyclopedia files, not dictionary files

**Fix Needed:**
- Use `encyclopedia.create_from_html_file()` only for dictionary HTML files
- For encyclopedia HTML files, use a different loading method
- Or update the HTML files to have the correct structure
- Or skip these tests if the files don't exist or have wrong format

### 2. WikipediaPage.url Attribute Error (3 tests)

**Error:** `AttributeError: 'WikipediaPage' object has no attribute 'url'`

**Affected Tests:**
- `test/encyclopedia/test_missing_descriptions_and_images_diagnostic.py::TestMissingDescriptionsDiagnostic::test_climate_entry_should_have_description`
- `test/encyclopedia/test_missing_descriptions_and_images_diagnostic.py::TestMissingDescriptionsDiagnostic::test_entry_with_url_but_no_description_gets_fetched`
- `test/encyclopedia/test_missing_descriptions_and_images_diagnostic.py::TestMissingDescriptionsDiagnostic::test_full_pipeline_missing_descriptions`

**Root Cause:**
- Code in `encyclopedia/cli/versioned_editor.py` tries to access `wikipedia_page.url`
- The `WikipediaPage` object from `amilib` doesn't have a `url` attribute
- Need to use the correct method to get the URL from WikipediaPage

**Location:**
- `encyclopedia/cli/versioned_editor.py` - `add_wikipedia_feature()` function
- Line ~349: `entry_dict['wikipedia_url'] = wikipedia_page.url`

**Fix Needed:**
- Check what attributes/methods WikipediaPage actually has
- Use correct method to get URL (e.g., `wikipedia_page.get_url()` or `wikipedia_page.wikipedia_url`)
- Update all places where `wikipedia_page.url` is accessed

## Detailed Error Messages

### Error 1: HTML Dictionary Structure
```
ValueError: HTML dictionary needs html/body/div[@role='ami_dictionary']
```

**Stack Trace Location:**
- `encyclopedia/core/encyclopedia.py:153` in `create_from_html_content()`
- Calls `AmiDictionary.create_from_html_file()` which expects dictionary structure

**Files Affected:**
- `temp/climate_encyclopedia.html` - This is an encyclopedia file, not a dictionary file

### Error 2: WikipediaPage.url Attribute
```
AttributeError: 'WikipediaPage' object has no attribute 'url'
```

**Stack Trace Location:**
- `encyclopedia/cli/versioned_editor.py` - `add_wikipedia_feature()` function
- Line ~349: `entry_dict['wikipedia_url'] = wikipedia_page.url`
- Also line ~367: `print(f"    URL: {wikipedia_page.url}")`

**Investigation Needed:**
- Check `amilib.wikimedia.WikipediaPage` class to see what methods/attributes it has
- Common possibilities:
  - `wikipedia_page.get_url()`
  - `wikipedia_page.wikipedia_url`
  - `wikipedia_page.page_url`
  - `wikipedia_page.url` (if it exists but needs to be accessed differently)

## Files to Fix

1. **`encyclopedia/cli/versioned_editor.py`**
   - Fix `wikipedia_page.url` access
   - Find correct method to get URL from WikipediaPage

2. **`test/encyclopedia/test_html_description_and_image_validation.py`**
   - Fix `test_validation_from_real_file` to handle encyclopedia HTML files correctly

3. **`test/encyclopedia/test_missing_descriptions_and_images_diagnostic.py`**
   - Fix `test_climate_entry_from_real_file` to handle encyclopedia HTML files correctly
   - Fix `test_all_entries_have_images_from_real_file` to handle encyclopedia HTML files correctly

## Investigation Steps

1. **Check WikipediaPage API:**
   ```python
   from amilib.wikimedia import WikipediaPage
   # Check what attributes/methods WikipediaPage has
   print(dir(WikipediaPage))
   # Or check documentation
   ```

2. **Check HTML File Structure:**
   ```python
   from pathlib import Path
   from lxml.html import fromstring
   
   html_file = Path("temp/climate_encyclopedia.html")
   content = html_file.read_text()
   root = fromstring(content)
   
   # Check structure
   print(root.xpath("//div[@role='ami_dictionary']"))
   print(root.xpath("//div[@role='ami_entry']"))
   ```

3. **Find Correct Loading Method:**
   - Check if `AmiEncyclopedia` has a method to load from encyclopedia HTML files
   - Or create a method to convert encyclopedia HTML to dictionary format

## Next Steps

1. Investigate `WikipediaPage` API to find correct URL access method
2. Fix `add_wikipedia_feature()` to use correct URL access
3. Fix HTML file loading tests to use correct method for encyclopedia files
4. Re-run all 6 failing tests
5. Verify all tests pass

---

**Date:** January 21, 2026  
**Status:** 6 tests failing - needs investigation and fixes  
**Priority:** High - blocks validation and diagnostic tests
