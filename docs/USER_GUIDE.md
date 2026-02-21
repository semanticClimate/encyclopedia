# Encyclopedia User Guide

**Last Updated:** February 21, 2026

## Overview

The Encyclopedia project provides tools for creating, managing, and browsing structured encyclopedias with Wikipedia integration. It supports creating encyclopedias from wordlists, adding Wikipedia descriptions and images, normalizing entries by Wikidata ID, and generating interactive landing pages.

## Quick Start

### 1. Create an Encyclopedia from a Wordlist

The simplest way to create an encyclopedia is from a list of terms:

```bash
python -m Examples.create_encyclopedia_from_wordlist \
    --wordlist my_terms.txt \
    --output my_encyclopedia.html \
    --add-wikipedia \
    --add-images
```

**Input:** Text file with one term per line  
**Output:** HTML encyclopedia file with Wikipedia content and images

### 2. View Your Encyclopedia

**Option A: Landing Page (Recommended)**
```bash
python Examples/create_landing_page_example.py
# Opens: temp/examples/landing_page/encyclopedia_landing_page.html
```

**Option B: Streamlit Browser**
```bash
streamlit run encyclopedia/browser/app.py
# Then upload your encyclopedia HTML file in the sidebar
```

### 3. Process Existing Encyclopedia

Add features to an existing encyclopedia:

```bash
python -m encyclopedia.cli.versioned_editor process \
    my_encyclopedia.html \
    --feature wikipedia \
    --feature images \
    --batch-size 10
```

---

## Core Concepts

### Encyclopedia Structure

An encyclopedia consists of:

- **Entries**: Individual encyclopedia entries, each with:
  - Term (primary name)
  - Canonical term (normalized name)
  - Wikidata ID (unique identifier)
  - Wikipedia URL
  - Description HTML (first paragraph)
  - Definition HTML (first sentence)
  - Image links/figures
  - Synonyms (merged entries)

- **Normalization**: Entries with the same Wikidata ID are normalized (grouped together)

- **Synonym Merging**: Entries with the same Wikidata ID are merged, with synonyms listed

### File Formats

**Input Formats:**
- Text wordlist (one term per line)
- HTML dictionary (`div[@role='ami_dictionary']`)
- HTML encyclopedia (`div[@role='ami_encyclopedia']`)

**Output Format:**
- HTML encyclopedia (`div[@role='ami_encyclopedia']`)
- Landing page HTML (with TOC, search, statistics)

---

## Creating Encyclopedias

### From Wordlist

**Basic Usage:**
```python
from Examples.create_encyclopedia_from_wordlist import create_encyclopedia_from_wordlist

terms = ["climate change", "global warming", "greenhouse gas"]
encyclopedia = create_encyclopedia_from_wordlist(
    terms=terms,
    title="Climate Encyclopedia",
    add_wikipedia=True,
    add_images=True,
    batch_size=10
)
```

**Parameters:**
- `terms`: List of terms/phrases
- `title`: Encyclopedia title
- `add_wikipedia`: Add Wikipedia descriptions (default: True)
- `add_images`: Add images from Wikipedia (default: False, can be slow)
- `batch_size`: Entries processed at a time (default: 10)
- `validate`: Validate completeness at end (default: True)
- `verbose`: Show detailed progress (default: False)

### From HTML File

```python
from encyclopedia.core.encyclopedia import AmiEncyclopedia

encyclopedia = AmiEncyclopedia()
encyclopedia.create_from_html_file(Path("my_encyclopedia.html"))
```

### Programmatic Creation

```python
from encyclopedia.core.encyclopedia import AmiEncyclopedia

# Create empty encyclopedia
encyclopedia = AmiEncyclopedia(title="My Encyclopedia")

# Add entries manually
entry = {
    'term': 'climate change',
    'wikidata_id': 'Q7937',
    'wikipedia_url': 'https://en.wikipedia.org/wiki/Climate_change',
    'description_html': '<p>Climate change refers to...</p>',
    'synonyms': []
}
encyclopedia.entries.append(entry)

# Normalize and merge
encyclopedia.normalize_by_wikidata_id()
encyclopedia.merge()
```

---

## Adding Wikipedia Content

### Add Descriptions

```python
from encyclopedia.utils.encyclopedia_builder import add_wikipedia_descriptions_to_encyclopedia

encyclopedia, results = add_wikipedia_descriptions_to_encyclopedia(
    encyclopedia,
    batch_size=10,
    verbose=True
)

print(f"Added descriptions: {results['successful']}/{results['total']}")
```

### Add Images

```python
from encyclopedia.utils.encyclopedia_builder import add_image_links_to_encyclopedia

encyclopedia, results = add_image_links_to_encyclopedia(
    encyclopedia,
    batch_size=10,
    verbose=True
)

print(f"Added images: {results['with_images']}/{results['total']}")
```

### Using CLI

```bash
# Add Wikipedia descriptions
python -m encyclopedia.cli.versioned_editor process \
    my_encyclopedia.html \
    --feature wikipedia \
    --batch-size 10

# Add images
python -m encyclopedia.cli.versioned_editor process \
    my_encyclopedia.html \
    --feature images \
    --batch-size 10
```

---

## Normalization and Merging

### Normalize by Wikidata ID

Groups entries with the same Wikidata ID:

```python
normalized = encyclopedia.normalize_by_wikidata_id()
# Returns dict mapping Wikidata ID to list of entries
```

### Merge Synonyms

Merges entries with the same Wikidata ID, keeping synonyms:

```python
merged = encyclopedia.merge()
# Returns AmiEncyclopedia with merged entries
```

**Example:**
- Entry 1: term="climate change", wikidata_id="Q7937"
- Entry 2: term="global warming", wikidata_id="Q7937"
- After merge: Single entry with term="climate change", synonyms=["global warming"]

---

## Saving and Loading

### Save Encyclopedia

```python
# Save as HTML
encyclopedia.save_wiki_normalized_html(Path("output.html"))

# Or get HTML string
html_content = encyclopedia.create_wiki_normalized_html()
```

### Load Encyclopedia

```python
from encyclopedia.core.encyclopedia import AmiEncyclopedia

# From HTML file
encyclopedia = AmiEncyclopedia()
encyclopedia.create_from_html_file(Path("my_encyclopedia.html"))

# From HTML content string
encyclopedia.create_from_html_content(html_string)
```

---

## Landing Page

### Generate Landing Page

Create an interactive landing page with TOC, search, and statistics:

```python
from Examples.create_landing_page_example import create_landing_page_html

landing_page_html = create_landing_page_html(encyclopedia)
Path("landing_page.html").write_text(landing_page_html, encoding='utf-8')
```

**Features:**
- **Table of Contents**: Alphabetical organization with quick jump
- **Search**: Real-time client-side search
- **Statistics**: Entry counts, completeness metrics
- **Entry Display**: Cards with metadata, descriptions, images
- **Navigation**: Smooth scrolling, deep linking

### Using the Script

```bash
python Examples/create_landing_page_example.py
# Output: temp/examples/landing_page/encyclopedia_landing_page.html
```

---

## Validation

### Validate Completeness

```python
from encyclopedia.utils.validation import validate_encyclopedia_completeness

results = validate_encyclopedia_completeness(encyclopedia)

print(f"Total entries: {results['total_entries']}")
print(f"With descriptions: {results['entries_with_descriptions']}")
print(f"With images: {results['entries_with_images']}")
print(f"With Wikidata: {results['entries_with_wikidata']}")
print(f"Is complete: {results['is_complete']}")
```

### Validate Images

```python
from encyclopedia.utils.validation import validate_image_links_added

results = validate_image_links_added(
    encyclopedia,
    check_url_exists=True  # Verify URLs are accessible
)

print(f"Entries with images: {results['entries_with_images']}")
print(f"Valid image URLs: {results['valid_image_urls']}")
```

---

## Search Functionality

### Using Search Engine

```python
from encyclopedia.browser.search_engine import EncyclopediaSearchEngine
from pathlib import Path

# Load encyclopedia and build index
engine = EncyclopediaSearchEngine()
engine.load_encyclopedia(Path("my_encyclopedia.html"))

# Search
results = engine.search("climate change", search_type="auto", limit=20)

for result in results:
    print(f"{result.entry.term} (score: {result.score:.1f})")
```

**Search Types:**
- `"exact"`: Exact term matching
- `"stemmed"`: Word variation matching
- `"fuzzy"`: Similarity matching (typos, partial)
- `"auto"`: Tries exact → stemmed → fuzzy (recommended)

### Using Streamlit Browser

```bash
streamlit run encyclopedia/browser/app.py
```

Then:
1. Upload encyclopedia HTML file
2. Select search type
3. Enter search query
4. Browse results

---

## Best Practices

### 1. Batch Processing

For large encyclopedias, use batch processing:

```python
encyclopedia, results = add_wikipedia_descriptions_to_encyclopedia(
    encyclopedia,
    batch_size=20  # Process 20 at a time
)
```

### 2. Error Handling

Wikipedia lookups may fail. Handle gracefully:

```python
try:
    encyclopedia, results = add_wikipedia_descriptions_to_encyclopedia(encyclopedia)
    print(f"Success: {results['successful']}/{results['total']}")
    if results.get('no_wikipedia'):
        print(f"Not found: {results['no_wikipedia']}")
except Exception as e:
    print(f"Error: {e}")
```

### 3. Caching

Use cached encyclopedias for testing:

```python
from test.encyclopedia.fixtures.small_encyclopedia import create_small_encyclopedia

# Uses cache if available
encyclopedia = create_small_encyclopedia(use_cache=True)
```

### 4. Validation

Always validate after creation:

```python
results = validate_encyclopedia_completeness(encyclopedia)
if not results['is_complete']:
    print("Warning: Encyclopedia is incomplete")
    print(f"Missing descriptions: {results['entries_without_descriptions']}")
```

---

## Common Tasks

### Task 1: Create Encyclopedia from Research Terms

```python
research_terms = [
    "climate change",
    "greenhouse effect",
    "carbon dioxide",
    "global warming"
]

encyclopedia = create_encyclopedia_from_wordlist(
    terms=research_terms,
    title="Climate Research Encyclopedia",
    add_wikipedia=True,
    add_images=True
)

encyclopedia.save_wiki_normalized_html(Path("climate_research.html"))
```

### Task 2: Add Missing Descriptions

```python
# Load existing encyclopedia
encyclopedia = AmiEncyclopedia()
encyclopedia.create_from_html_file(Path("my_encyclopedia.html"))

# Add descriptions to entries missing them
encyclopedia, results = add_wikipedia_descriptions_to_encyclopedia(encyclopedia)

# Save updated version
encyclopedia.save_wiki_normalized_html(Path("my_encyclopedia_updated.html"))
```

### Task 3: Generate Landing Page

```python
# Load encyclopedia
encyclopedia = AmiEncyclopedia()
encyclopedia.create_from_html_file(Path("my_encyclopedia.html"))

# Generate landing page
from Examples.create_landing_page_example import create_landing_page_html
landing_html = create_landing_page_html(encyclopedia)

# Save
Path("landing_page.html").write_text(landing_html, encoding='utf-8')
```

### Task 4: Search and Filter

```python
from encyclopedia.browser.search_engine import EncyclopediaSearchEngine

engine = EncyclopediaSearchEngine()
engine.load_encyclopedia(Path("my_encyclopedia.html"))

# Search
results = engine.search("climate", search_type="auto")

# Filter results
entries_with_images = [
    r.entry for r in results
    if r.entry.get('figure_html') or r.entry.get('image_link')
]
```

---

## Troubleshooting

### Problem: Wikipedia Lookups Fail

**Solutions:**
- Check internet connection
- Reduce `batch_size` (try 5-10)
- Some terms may not have Wikipedia pages (handled gracefully)
- Use `verbose=True` to see which terms fail

### Problem: Images Not Loading

**Solutions:**
- Verify `add_images=True` when creating
- Check `validate_image_links_added()` to see which entries have images
- Some entries may not have images on Wikipedia
- Image URLs may require internet access to view

### Problem: Entries Not Merging

**Solutions:**
- Ensure entries have Wikidata IDs
- Run `normalize_by_wikidata_id()` before `merge()`
- Check that Wikidata IDs match exactly

### Problem: Landing Page Not Displaying

**Solutions:**
- Open HTML file in modern browser (Chrome, Firefox, Safari)
- Check browser console for JavaScript errors
- Ensure file path is correct
- Try generating new landing page

---

## File Locations

### Input Files
- Wordlists: `Examples/my_terms.txt`
- HTML dictionaries: Any location
- HTML encyclopedias: Any location

### Output Files
- Encyclopedias: `my_encyclopedia.html`
- Landing pages: `temp/examples/landing_page/`
- Cached test fixtures: `test/encyclopedia/fixtures/cache/`
- Temp files: `temp/` directory

### Configuration
- Test fixtures: `test/encyclopedia/fixtures/`
- Examples: `Examples/`
- Browser: `encyclopedia/browser/`

---

## Advanced Usage

### Custom Entry Creation

```python
from test.encyclopedia.fixtures.helpers import create_entry_with_all_fields

entry = create_entry_with_all_fields(
    term="custom term",
    wikidata_id="Q1234",
    wikipedia_url="https://en.wikipedia.org/wiki/Custom_term",
    description_html="<p>Custom description</p>",
    image_link="https://example.com/image.jpg",
    synonyms=["synonym1", "synonym2"]
)

encyclopedia.entries.append(entry)
```

### Programmatic Search

```python
# Search by term
results = [e for e in encyclopedia.entries if "climate" in e['term'].lower()]

# Search by description text
import re
def search_in_description(encyclopedia, query):
    results = []
    for entry in encyclopedia.entries:
        if entry.get('description_html'):
            text = re.sub(r'<[^>]+>', '', entry['description_html'])
            if query.lower() in text.lower():
                results.append(entry)
    return results

results = search_in_description(encyclopedia, "temperature")
```

### Export to Other Formats

```python
# Export as JSON
import json
entries_json = json.dumps(encyclopedia.entries, indent=2)
Path("encyclopedia.json").write_text(entries_json, encoding='utf-8')

# Export as CSV
import csv
with open("encyclopedia.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=['term', 'wikidata_id', 'wikipedia_url'])
    writer.writeheader()
    for entry in encyclopedia.entries:
        writer.writerow({
            'term': entry.get('term', ''),
            'wikidata_id': entry.get('wikidata_id', ''),
            'wikipedia_url': entry.get('wikipedia_url', '')
        })
```

---

## API Reference

### AmiEncyclopedia Class

**Main Methods:**
- `create_from_html_file(html_file)` - Load from HTML file
- `create_from_html_content(html_content)` - Load from HTML string
- `normalize_by_wikidata_id()` - Normalize entries by Wikidata ID
- `merge()` - Merge synonyms
- `save_wiki_normalized_html(output_file)` - Save as HTML
- `create_wiki_normalized_html()` - Get HTML string
- `get_statistics()` - Get encyclopedia statistics

**Properties:**
- `title` - Encyclopedia title
- `entries` - List of entry dictionaries
- `normalized_entries` - Dict of normalized entries
- `synonym_groups` - Dict of synonym groups

### Entry Dictionary Structure

```python
{
    'term': str,                    # Primary term
    'canonical_term': str,          # Canonical term
    'wikidata_id': str,             # Wikidata Q/P ID
    'wikipedia_url': str,           # Full Wikipedia URL
    'description_html': str,        # HTML description
    'definition_html': str,        # HTML definition (first sentence)
    'figure_html': Element,        # Image element (lxml) or None
    'image_link': str,             # Image URL or None
    'synonyms': List[str],         # List of synonym terms
}
```

---

## Examples

See `Examples/` directory for:
- `create_encyclopedia_from_wordlist.py` - Create from wordlist
- `create_landing_page_example.py` - Generate landing page
- `browser_example.py` - Use search engine programmatically

---

## Support

For issues, questions, or contributions:
- Check `docs/` for detailed documentation
- Review `test/` for usage examples
- See `docs/landing_page_features_proposal.md` for planned features

---

## Version History

- **February 2026**: Landing page support, test fixtures, caching
- **January 2026**: Wikipedia integration, image support, normalization
- **Initial Release**: Basic encyclopedia creation and HTML generation
