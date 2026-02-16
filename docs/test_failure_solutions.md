# Solutions for Test Failures

**Date:** February 16, 2026  
**Status:** Proposed Solutions

## Summary

4 test failures in 2 categories:
1. **Missing `figure_html`** (1 test): `test_entry_without_images_gets_image_added`
2. **HTML dictionary structure error** (3 tests): Tests loading encyclopedia HTML files

---

## Issue 1: Missing `figure_html` in Test

### Problem
- Test mocks `_extract_images_from_wikipedia_page()` but `add_images_feature()` doesn't use it
- `add_images_feature()` calls `AmiEntry.add_figures_to_entry()` directly
- Mock isn't called, so `figure_html` isn't set

### Root Cause
The test mocks the wrong function. `add_images_feature()` uses:
```python
ami_entry.add_figures_to_entry(wikipedia_page)
```
But the test mocks:
```python
_extract_images_from_wikipedia_page()  # Not used by add_images_feature()
```

### Solution Options

#### Option A: Fix the Test (Recommended)
Mock `AmiEntry.add_figures_to_entry()` and set up the expected element structure:

```python
def test_entry_without_images_gets_image_added(self):
    """Test that entries without images get images added"""
    encyclopedia = AmiEncyclopedia(title="Test")
    entry = {
        "term": "climate change",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Climate_change",
        "description_html": "<p>Description</p>",
    }
    encyclopedia.entries = [entry]
    
    # Mock Wikipedia page
    mock_wikipedia_page = Mock()
    mock_wikipedia_page.url = "https://en.wikipedia.org/wiki/Climate_change"
    
    # Create mock figure element structure that amilib expects
    from lxml.etree import Element
    mock_figure_elem = Element('a')
    mock_figure_elem.set('href', 'https://en.wikipedia.org/wiki/File:Climate_change_image.jpg')
    mock_figure_elem.set('class', 'wikipedia-image-link')
    
    # Create mock AmiEntry with figure div structure
    mock_ami_entry = Mock()
    mock_figure_div = Element('div')
    mock_figure_div.set('title', 'figure')
    mock_figure_div.append(mock_figure_elem)
    mock_ami_entry.element = Element('div')
    mock_ami_entry.element.append(mock_figure_div)
    
    with patch('encyclopedia.cli.versioned_editor._get_wikipedia_page_for_entry',
               return_value=mock_wikipedia_page):
        with patch('amilib.ami_dict.AmiEntry.create_lxml_entry_from_term',
                   return_value=Element('div')):
            with patch('amilib.ami_dict.AmiEntry.create_from_element',
                       return_value=mock_ami_entry):
                add_images_feature(entry, encyclopedia, verbose=False)
    
    # Verify image was added
    assert 'figure_html' in entry
    assert entry['figure_html'] is not None
    assert 'image_link' in entry
    assert entry['image_link'] is not None
```

**Pros:**
- Tests actual code path
- Verifies `add_images_feature()` works correctly
- No code changes needed

**Cons:**
- More complex mock setup

#### Option B: Refactor `add_images_feature()` to Use `_extract_images_from_wikipedia_page()`
Make `add_images_feature()` use the existing helper function:

```python
def add_images_feature(entry_dict: Dict, encyclopedia: AmiEncyclopedia, verbose: bool = False):
    # ... existing code ...
    
    # Extract images using helper function
    image_elements = _extract_images_from_wikipedia_page(wikipedia_page, verbose=verbose)
    
    if image_elements:
        # Process first image element
        figure_elem = image_elements[0]
        _fix_image_urls(figure_elem)
        entry_dict['figure_html'] = copy.deepcopy(figure_elem)
        # ... extract image_link ...
```

**Pros:**
- Uses existing helper function
- Test mock would work

**Cons:**
- Changes working code
- May break existing functionality
- `_extract_images_from_wikipedia_page()` only finds infobox images, while `add_figures_to_entry()` may find more

**Recommendation:** Option A (fix the test)

---

## Issue 2: HTML Dictionary Structure Error

### Problem
- Tests call `encyclopedia.create_from_html_file()` which always expects dictionary format
- Files are encyclopedia format (`div[@role='ami_encyclopedia']`)
- `AmiDictionary.create_from_html_file()` raises: `ValueError: HTML dictionary needs html/body/div[@role='ami_dictionary']`

### Root Cause
`AmiEncyclopedia.create_from_html_file()` always calls `AmiDictionary.create_from_html_file()` which expects dictionary format. But `_load_encyclopedia_from_html_file()` already handles both formats correctly.

### Solution Options

#### Option A: Update `create_from_html_file()` to Handle Both Formats (Recommended)
Make `AmiEncyclopedia.create_from_html_file()` detect format and handle both:

```python
def create_from_html_file(self, html_file: Path) -> 'AmiEncyclopedia':
    """Create encyclopedia from HTML file, handling both dictionary and encyclopedia formats"""
    if not html_file.exists():
        raise FileNotFoundError(f"HTML file not found: {html_file}")
    
    html_content = html_file.read_text(encoding='utf-8')
    
    # Parse HTML to detect format
    from lxml.html import fromstring
    html_root = fromstring(html_content.encode('utf-8'))
    encyclopedia_div = html_root.xpath(".//div[@role='ami_encyclopedia']")
    dictionary_div = html_root.xpath(".//div[@role='ami_dictionary']")
    
    if encyclopedia_div:
        # Encyclopedia format - extract entries directly
        from encyclopedia.cli.versioned_editor import _extract_entries_from_encyclopedia_html
        entries = _extract_entries_from_encyclopedia_html(html_root)
        self.entries = entries
        self.title = encyclopedia_div[0].get('title', 'Encyclopedia')
    elif dictionary_div:
        # Dictionary format - use existing method
        return self.create_from_html_content(html_content)
    else:
        raise ValueError(
            f"File does not contain a valid encyclopedia or dictionary.\n"
            f"Expected div with role='ami_encyclopedia' or role='ami_dictionary'\n"
            f"File: {html_file}"
        )
    
    return self
```

**Pros:**
- Fixes the issue at the source
- Makes `create_from_html_file()` consistent with `_load_encyclopedia_from_html_file()`
- Tests can use standard method

**Cons:**
- Requires code change
- Need to import helper function

#### Option B: Update Tests to Use `_load_encyclopedia_from_html_file()`
Change tests to use the existing helper:

```python
# In test files:
from encyclopedia.cli.versioned_editor import _load_encyclopedia_from_html_file

def test_validation_from_real_file(self, verbose=False):
    html_file = Path(Resources.TEMP_DIR, "climate_encyclopedia.html")
    if not html_file.exists():
        pytest.skip(f"File {html_file} does not exist.")
    
    encyclopedia = _load_encyclopedia_from_html_file(html_file)
    # ... rest of test ...
```

**Pros:**
- No code changes needed
- Uses existing working function

**Cons:**
- Tests use internal helper function (not public API)
- Inconsistent API usage
- Other code may have same issue

**Recommendation:** Option A (update `create_from_html_file()`)

---

## Implementation Plan

### Step 1: Fix HTML Loading (Issue 2)
1. Update `AmiEncyclopedia.create_from_html_file()` to detect format
2. Handle both encyclopedia and dictionary formats
3. Re-run HTML structure tests

### Step 2: Fix Image Test (Issue 1)
1. Update `test_entry_without_images_gets_image_added` to mock `AmiEntry` methods
2. Set up proper element structure in mock
3. Re-run image test

### Step 3: Verify All Tests Pass
1. Run full test suite
2. Verify no regressions
3. Document changes

---

## Files to Modify

1. **`encyclopedia/core/encyclopedia.py`**
   - Update `create_from_html_file()` method

2. **`test/encyclopedia/test_batch_size_and_features.py`**
   - Update `test_entry_without_images_gets_image_added()` test

3. **`test/encyclopedia/test_html_description_and_image_validation.py`**
   - May need updates if using `create_from_html_file()` directly

4. **`test/encyclopedia/test_missing_descriptions_and_images_diagnostic.py`**
   - May need updates if using `create_from_html_file()` directly

---

## Testing Strategy

1. **Unit Tests:**
   - Test `create_from_html_file()` with both formats
   - Test `add_images_feature()` with mocked `AmiEntry`

2. **Integration Tests:**
   - Load real encyclopedia HTML files
   - Load real dictionary HTML files
   - Verify both work correctly

3. **Regression Tests:**
   - Ensure existing functionality still works
   - Verify no breaking changes
