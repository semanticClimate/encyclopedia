# Encyclopedia Browser - Tutorial

## Overview

The Encyclopedia Browser is a web-based tool for searching and browsing encyclopedia entries. It supports up to 5,000 entries with fast search capabilities including exact matching, stemming, and fuzzy matching.

## Installation

### Prerequisites

- Python 3.8 or higher
- An encyclopedia HTML file (created using `create_encyclopedia_from_wordlist.py`)

### Check Your Python Environment

**Important:** Make sure you're using the correct Python interpreter. Check which Python you're using:

```bash
which python
python --version
```

If you're using conda/anaconda, activate your environment first:
```bash
conda activate base  # or your environment name
```

### Install Dependencies

Install dependencies using the **same Python** that will run the browser:

```bash
# Check which Python will be used
python --version

# Install required dependencies
python -m pip install streamlit whoosh nltk lxml

# Optional: For fuzzy search (recommended)
python -m pip install rapidfuzz
```

**Note:** Use `python -m pip` instead of just `pip` to ensure you're installing to the correct Python environment.

### Download NLTK Data (for stemming)

```bash
python -m nltk.downloader punkt stopwords
```

### Verify Installation

Check that all dependencies are installed correctly:

```bash
python encyclopedia/browser/check_dependencies.py
```

This will show which packages are installed and which are missing.

## Quick Start

### 1. Create an Encyclopedia

First, create an encyclopedia HTML file using the wordlist script:

```bash
# From project root
python -m Examples.create_encyclopedia_from_wordlist --wordlist Examples/my_terms.txt --output my_encyclopedia.html
```

### 2. Launch the Browser

```bash
# From project root
streamlit run encyclopedia/browser/app.py
```

The browser will open in your default web browser at `http://localhost:8501`

### 3. Load Your Encyclopedia

1. In the sidebar, click "Upload Encyclopedia HTML File"
2. Select your `my_encyclopedia.html` file
3. Click "Load Encyclopedia"
4. Wait for the index to build (this may take a few seconds)

### 4. Search Entries

1. Enter a search term in the search box (e.g., "climate")
2. Select a search type:
   - **Auto**: Tries exact match first, then stemmed, then fuzzy
   - **Exact**: Matches exact term only
   - **Stemmed**: Matches word variations (e.g., "climate" matches "climates")
   - **Fuzzy**: Finds similar terms using Levenshtein distance
3. View results in the "Search Results" tab

### 5. Browse All Entries

Click the "Browse All" tab to see all entries paginated (20 per page).

## Features

### Search Types

#### Exact Search
Matches the exact term as entered. Fastest search type.

**Example:**
- Query: "climate change"
- Matches: Only entries with exact term "climate change"

#### Stemmed Search
Matches word variations using stemming. Handles plurals, verb forms, etc.

**Example:**
- Query: "climate"
- Matches: "climate", "climates", "climatic", "climatology"

#### Fuzzy Search
Finds similar terms using Levenshtein distance (edit distance). Useful for typos or partial matches.

**Example:**
- Query: "climat chang"
- Matches: "climate change" (similarity: 85%)

#### Auto Search
Automatically tries search types in order: exact → stemmed → fuzzy. Recommended for most use cases.

### Display Features

- **Entry Details**: Shows term, canonical term, Wikidata ID, Wikipedia link
- **Synonyms**: Displays related terms
- **HTML Content**: Renders full HTML descriptions with formatting
- **Score Display**: Shows relevance score and match type for each result

## Usage Examples

### Example 1: Basic Search

1. Load encyclopedia
2. Enter "greenhouse" in search box
3. Select "Auto" search type
4. View results showing entries about greenhouse gases, greenhouse effect, etc.

### Example 2: Finding Similar Terms

1. Enter "carbon diox" (partial/misspelled)
2. Select "Fuzzy" search type
3. Find "carbon dioxide" entry with similarity score

### Example 3: Browsing by Category

1. Go to "Browse All" tab
2. Scroll through entries
3. Use page navigation to browse through all entries

## Programmatic Usage

You can also use the search engine programmatically:

```python
from pathlib import Path
from encyclopedia.browser.search_engine import EncyclopediaSearchEngine

# Initialize search engine
search_engine = EncyclopediaSearchEngine()

# Load encyclopedia
search_engine.load_encyclopedia(Path("my_encyclopedia.html"))

# Search
results = search_engine.search("climate change", search_type="auto")

# Display results
for result in results:
    print(f"Term: {result.entry.term}")
    print(f"Score: {result.score}")
    print(f"Match Type: {result.match_type}")
    print(f"Description: {result.entry.description_text[:100]}...")
    print()
```

## Troubleshooting

### Index Build Fails

- Ensure the HTML file is a valid encyclopedia file
- Check that the file path is correct
- Verify all dependencies are installed

### Search Returns No Results

- Try different search terms
- Try "Fuzzy" search type for partial matches
- Check that the encyclopedia was loaded successfully

### Slow Performance

- For large encyclopedias (>1000 entries), indexing may take time
- Search should be fast after initial indexing
- Consider limiting results if needed

### HTML Not Rendering

- Ensure `lxml` is installed: `pip install lxml`
- Check browser console for errors
- Some HTML may not render perfectly in Streamlit

## Advanced Usage

### Custom Index Location

```python
from pathlib import Path
from encyclopedia.browser.search_engine import EncyclopediaSearchEngine

# Specify custom index directory
index_dir = Path("/path/to/index")
search_engine = EncyclopediaSearchEngine(index_dir=index_dir)
search_engine.load_encyclopedia(Path("encyclopedia.html"))
```

### Batch Searching

```python
queries = ["climate", "greenhouse", "carbon"]
all_results = {}

for query in queries:
    results = search_engine.search(query, limit=10)
    all_results[query] = results
```

## Limitations

- Maximum recommended: 5,000 entries
- Initial index build time increases with entry count
- HTML rendering in Streamlit has some limitations
- Fuzzy search may be slower for very large encyclopedias

## Next Steps

- Try different search queries
- Explore the browse view
- Experiment with different search types
- Check out the design document for future enhancements

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the design document: `docs/encyclopedia_browser_design.md`
3. Check that all dependencies are correctly installed
