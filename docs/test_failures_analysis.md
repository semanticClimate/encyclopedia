# Test Failures Analysis - January 21, 2026

## Overview

There are **5 failing tests** in `test/encyclopedia/test_missing_descriptions_and_images_diagnostic.py`. All failures are related to missing descriptions and images in encyclopedia entries.

## Failing Tests Summary

1. ✅ **`test_climate_entry_should_have_description`** - FAILING
2. ✅ **`test_entry_with_url_but_no_description_gets_fetched`** - FAILING  
3. ✅ **`test_full_pipeline_missing_descriptions`** - FAILING
4. ✅ **`test_climate_entry_from_real_file`** - FAILING
5. ✅ **`test_all_entries_have_images_from_real_file`** - FAILING

## Root Cause Analysis

### Issue 1: Wikipedia Content Extraction Failing (Tests 1-4)

**Problem:** The `_get_first_paragraph_html_from_wikipedia_page()` function is returning `(None, None)` for the "Climate" entry, causing the message:

```
⚠ No valid content found for 'climate' (may be redirect/disambiguation)
```

**Location:** `encyclopedia/cli/versioned_editor.py`, lines 229-303

**Why It Fails:**

1. **`create_first_wikipedia_para()` returns None or invalid content**
   - The function calls `wikipedia_page.create_first_wikipedia_para()` (line 244)
   - This method may return `None` or a `WikipediaPara` object with no valid content
   - The code checks for `para_obj.para_element` but it may be `None` or empty

2. **Fallback extraction also fails**
   - If `create_first_wikipedia_para()` fails, it falls back to direct HTML extraction (lines 280-298)
   - Looks for `div[@id='mw-content-text']//p[1]` but may not find valid content
   - The `_filter_wikipedia_messages()` function may be filtering out valid content

3. **Content filtering too aggressive**
   - `_filter_wikipedia_messages()` (lines 149-175) filters out text containing patterns like:
     - "other reasons this message may be displayed"
     - "this is an accepted version of this page"
     - "this page was last edited"
     - "you may be looking for"
     - "redirected from"
     - "this article is about"
   - **Problem:** The pattern "this article is about" may be filtering out legitimate first paragraphs that start with "This article is about..."

**Code Flow:**

```python
def add_wikipedia_feature(entry_dict: Dict, encyclopedia: AmiEncyclopedia):
    # ...
    wikipedia_page = _get_wikipedia_page_for_entry(entry_dict)  # ✅ Gets page successfully
    definition_html, description_html = _get_first_paragraph_html_from_wikipedia_page(wikipedia_page)  # ❌ Returns (None, None)
    
    if description_html or definition_html:
        # ✅ Would update entry
    else:
        # ❌ Prints "No valid content found" and exits without adding description
        print(f"  ⚠ No valid content found for '{term}' (may be redirect/disambiguation)")
```

**Specific Failure Points:**

1. **Line 244:** `wikipedia_page.create_first_wikipedia_para()` may return `None`
2. **Line 247:** `para_obj.para_element` may be `None` even if `para_obj` exists
3. **Line 200:** `_filter_wikipedia_messages()` may incorrectly filter valid content
4. **Line 282:** XPath `".//div[@id='mw-content-text']//p[1]"` may not find content
5. **Line 291:** Even if paragraph found, filtering may remove it

### Issue 2: Images Not Being Added (Test 5)

**Problem:** Images are not being extracted from Wikipedia pages or not being saved to entries.

**Location:** `encyclopedia/cli/versioned_editor.py`, lines 380-500+ (image extraction)

**Why It Fails:**

1. **Image extraction methods failing**
   - `extract_a_elem_with_image_from_infobox()` may return `None`
   - `get_infobox()` may return `None` or empty infobox
   - Direct HTML extraction may not find images

2. **Image links not being saved**
   - Even if images are extracted, they may not be properly saved to `entry_dict['figure_html']` or `entry_dict['image_link']`
   - The `add_images_feature()` function may not be updating entries correctly

3. **Full pipeline issue**
   - The `create_encyclopedia_from_wordlist()` function may not be calling `add_images_feature()` correctly
   - Or images may be extracted but lost during HTML generation/saving

## Detailed Test Failure Explanations

### Test 1: `test_climate_entry_should_have_description`

**What it tests:** Climate entry (Q7937) should get a description when `add_wikipedia_feature()` is called.

**Why it fails:**
- Entry has `wikipedia_url: "https://en.wikipedia.org/wiki/Climate"` but no `description_html`
- `add_wikipedia_feature()` is called
- `_get_wikipedia_page_for_entry()` successfully gets the Wikipedia page
- `_get_first_paragraph_html_from_wikipedia_page()` returns `(None, None)`
- Function prints "⚠ No valid content found" and exits without adding description
- Test assertion fails: `assert has_description_after` → `False`

**Root cause:** `_get_first_paragraph_html_from_wikipedia_page()` cannot extract valid content from the Climate Wikipedia page.

### Test 2: `test_entry_with_url_but_no_description_gets_fetched`

**What it tests:** Entries with Wikipedia URLs but no descriptions should be processed by `add_wikipedia_descriptions_to_encyclopedia()`.

**Why it fails:**
- Calls `add_wikipedia_descriptions_to_encyclopedia()` which internally calls `add_wikipedia_feature()`
- Same issue as Test 1: content extraction fails
- Entry still has no description after processing
- Test assertion fails: `assert _has_non_empty_description(entry)` → `False`

**Root cause:** Same as Test 1 - content extraction failing.

### Test 3: `test_full_pipeline_missing_descriptions`

**What it tests:** Full pipeline (`create_encyclopedia_from_wordlist()`) should add descriptions to all entries.

**Why it fails:**
- Creates encyclopedia from wordlist `["climate", "greenhouse gas"]`
- Pipeline calls `add_wikipedia_descriptions_to_encyclopedia()` internally
- Same content extraction issue occurs
- Entries end up without descriptions
- Test assertion fails: `assert has_desc` for each entry → `False`

**Root cause:** Same content extraction issue propagated through full pipeline.

### Test 4: `test_climate_entry_from_real_file`

**What it tests:** Climate entry from actual generated HTML file should have a description.

**Why it fails:**
- Loads `temp/climate_encyclopedia.html` file
- Finds Climate entry in loaded encyclopedia
- Entry has `wikipedia_url` but no `description_html`
- This confirms the real-world issue: descriptions are missing from generated files
- Test assertion fails: `assert has_desc` → `False`

**Root cause:** The encyclopedia file was generated with the same bug - descriptions weren't added during creation.

### Test 5: `test_all_entries_have_images_from_real_file`

**What it tests:** All entries in actual generated HTML file should have images.

**Why it fails:**
- Loads `temp/climate_encyclopedia.html` file
- Checks all entries for `figure_html` or `images` fields
- No entries have images
- Test assertion fails: `assert entries_with_images == len(encyclopedia.entries)` → `False`

**Root cause:** Images are not being extracted or saved during encyclopedia creation.

## Code Issues Identified

### Issue A: Content Filtering Too Aggressive

**File:** `encyclopedia/cli/versioned_editor.py`, lines 149-175

**Problem:** `_filter_wikipedia_messages()` filters out text containing "this article is about", which may be filtering legitimate first paragraphs.

**Example:** A Wikipedia article might start with:
> "This article is about the long-term average of weather patterns..."

This would be incorrectly filtered out.

**Fix needed:** Make filtering more specific or check if the pattern appears at the start of the paragraph (not just anywhere).

### Issue B: No Fallback for Failed Extraction

**File:** `encyclopedia/cli/versioned_editor.py`, lines 229-303

**Problem:** If `create_first_wikipedia_para()` fails and fallback extraction also fails, the function returns `(None, None)` without trying alternative methods.

**Fix needed:** Add more robust fallback methods or better error handling.

### Issue C: Image Extraction Not Robust

**File:** `encyclopedia/cli/versioned_editor.py`, lines 380-500+

**Problem:** Multiple image extraction methods may all fail, and there's no clear error reporting.

**Fix needed:** Improve error handling and add more fallback methods for image extraction.

### Issue D: No Validation of Extracted Content

**Problem:** Even if content is extracted, there's no validation that it's actually useful (non-empty, contains real text, etc.).

**Fix needed:** Add validation checks before returning extracted content.

## Recommendations

### Immediate Fixes

1. **Fix content filtering**
   - Make `_filter_wikipedia_messages()` more specific
   - Only filter if patterns appear at the start of text (not anywhere)
   - Add logging to see what's being filtered

2. **Improve content extraction**
   - Add more fallback methods
   - Try multiple XPath patterns
   - Validate extracted content before returning

3. **Fix image extraction**
   - Add better error handling
   - Try more extraction methods
   - Validate images before saving

4. **Add diagnostic logging**
   - Log what content is found
   - Log what's being filtered
   - Log why extraction fails

### Long-term Improvements

1. **Better error handling**
   - Don't silently fail - report why extraction failed
   - Provide actionable error messages

2. **Content validation**
   - Validate extracted content is useful
   - Check for minimum length, text content, etc.

3. **Retry logic**
   - Retry failed extractions with different methods
   - Handle transient Wikipedia API issues

4. **Test improvements**
   - Add tests for edge cases (redirects, disambiguation pages)
   - Test with various Wikipedia page types

## Style Guide Compliance

All tests follow the style guide:
- ✅ No mocks (use real implementations)
- ✅ Output to `temp/` directory
- ✅ Use `Resources.TEMP_DIR`
- ✅ Real API calls to Wikipedia

The failures are **not** due to style guide violations - they reveal actual bugs in the content extraction logic.

## Next Steps

1. **Investigate Wikipedia page structure**
   - Check what the Climate Wikipedia page actually contains
   - Verify XPath patterns match actual HTML structure

2. **Debug content extraction**
   - Add detailed logging to `_get_first_paragraph_html_from_wikipedia_page()`
   - See exactly what's being extracted and why it's failing

3. **Fix filtering logic**
   - Make `_filter_wikipedia_messages()` more specific
   - Test with actual Wikipedia content

4. **Fix image extraction**
   - Debug why images aren't being found
   - Verify image extraction methods work correctly

5. **Re-run tests**
   - After fixes, re-run all 5 failing tests
   - Verify they pass with real Wikipedia content

---

**Date:** January 21, 2026  
**Branch:** pmr202601  
**Status:** 5 tests failing - root causes identified
