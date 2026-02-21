# Encyclopedia Quick Reference

**Last Updated:** February 21, 2026

## Most Common Tasks

### Create Encyclopedia from Wordlist
```bash
python -m Examples.create_encyclopedia_from_wordlist \
    --wordlist terms.txt \
    --output encyclopedia.html \
    --add-wikipedia \
    --add-images
```

### Generate Landing Page
```bash
python Examples/create_landing_page_example.py
# Output: temp/examples/landing_page/encyclopedia_landing_page.html
```

### Add Wikipedia Descriptions
```bash
python -m encyclopedia.cli.versioned_editor process \
    encyclopedia.html \
    --feature wikipedia \
    --batch-size 10
```

### Add Images
```bash
python -m encyclopedia.cli.versioned_editor process \
    encyclopedia.html \
    --feature images \
    --batch-size 10
```

### View in Browser
```bash
streamlit run encyclopedia/browser/app.py
# Then upload encyclopedia.html in sidebar
```

---

## Python API Quick Reference

### Create Encyclopedia
```python
from Examples.create_encyclopedia_from_wordlist import create_encyclopedia_from_wordlist

encyclopedia = create_encyclopedia_from_wordlist(
    terms=["climate change", "global warming"],
    title="Climate Encyclopedia",
    add_wikipedia=True,
    add_images=True
)
```

### Load Encyclopedia
```python
from encyclopedia.core.encyclopedia import AmiEncyclopedia
from pathlib import Path

encyclopedia = AmiEncyclopedia()
encyclopedia.create_from_html_file(Path("encyclopedia.html"))
```

### Save Encyclopedia
```python
encyclopedia.save_wiki_normalized_html(Path("output.html"))
```

### Normalize and Merge
```python
encyclopedia.normalize_by_wikidata_id()
encyclopedia.merge()
```

### Add Wikipedia Content
```python
from encyclopedia.utils.encyclopedia_builder import (
    add_wikipedia_descriptions_to_encyclopedia,
    add_image_links_to_encyclopedia
)

# Add descriptions
encyclopedia, results = add_wikipedia_descriptions_to_encyclopedia(encyclopedia)

# Add images
encyclopedia, results = add_image_links_to_encyclopedia(encyclopedia)
```

### Search
```python
from encyclopedia.browser.search_engine import EncyclopediaSearchEngine
from pathlib import Path

engine = EncyclopediaSearchEngine()
engine.load_encyclopedia(Path("encyclopedia.html"))
results = engine.search("climate", search_type="auto")
```

### Validate
```python
from encyclopedia.utils.validation import validate_encyclopedia_completeness

results = validate_encyclopedia_completeness(encyclopedia)
print(f"Complete: {results['is_complete']}")
```

---

## File Locations

**Input:**
- Wordlists: `Examples/terms.txt`
- HTML files: Any location

**Output:**
- Encyclopedias: `encyclopedia.html`
- Landing pages: `temp/examples/landing_page/`
- Test fixtures: `test/encyclopedia/fixtures/cache/`
- Temp files: `temp/`

---

## Common Parameters

**`batch_size`**: Entries processed at once (default: 10)
- Smaller = slower but more reliable
- Larger = faster but may timeout

**`add_wikipedia`**: Add Wikipedia descriptions (default: True)
- Requires internet connection
- May fail for some terms (handled gracefully)

**`add_images`**: Add images from Wikipedia (default: False)
- Slower than descriptions
- Some entries may not have images

**`validate`**: Validate completeness (default: True)
- Checks for descriptions, images, Wikidata IDs
- Provides statistics

**`verbose`**: Show detailed progress (default: False)
- Useful for debugging
- Shows which terms succeed/fail

---

## Troubleshooting Quick Fixes

**Wikipedia lookups fail:**
- Reduce `batch_size` to 5-10
- Check internet connection
- Some terms may not have Wikipedia pages (normal)

**Images not loading:**
- Ensure `add_images=True` when creating
- Check `validate_image_links_added()` results
- Image URLs require internet to view

**Entries not merging:**
- Run `normalize_by_wikidata_id()` before `merge()`
- Ensure entries have Wikidata IDs
- Check that IDs match exactly

**Landing page not displaying:**
- Open in modern browser (Chrome, Firefox, Safari)
- Check browser console for errors
- Ensure file path is correct

---

## Test Fixtures (For Development)

```python
from test.encyclopedia.fixtures.small_encyclopedia import create_small_encyclopedia

# Uses cache if available (fast)
encyclopedia = create_small_encyclopedia(use_cache=True)
```

**Available Fixtures:**
- `create_small_encyclopedia()` - 10 entries
- `create_medium_encyclopedia()` - 60 entries
- `create_large_encyclopedia()` - 500 entries

---

## See Also

- **Full User Guide**: `docs/USER_GUIDE.md`
- **Landing Page Features**: `docs/landing_page_features_proposal.md`
- **Test Documentation**: `test/encyclopedia/LANDING_PAGE_TESTS_SUMMARY.md`
- **Browser Tutorial**: `encyclopedia/browser/TUTORIAL.md`
