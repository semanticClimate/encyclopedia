# Encyclopedia Browser - Design Document

**Date:** January 2026  
**Status:** Design Phase (Not Yet Implemented)

## Overview

An interactive web-based browser for exploring and searching encyclopedia entries. Designed to handle encyclopedias with up to 5,000 entries efficiently, with advanced search capabilities including stemming, fuzzy matching, and similarity search.

## Requirements

### Functional Requirements

1. **Search Capabilities**
   - Simple text search across entry terms and content
   - Stemming support (e.g., "climate" matches "climates", "climatic")
   - Fuzzy matching using Levenshtein distance
   - Regex pattern matching
   - Similarity search for finding related entries

2. **Display Features**
   - Display HTML content of entries (preserving formatting)
   - Show precise matches prominently
   - Display similar/related entries
   - Browse entries by category or alphabetically

3. **Performance**
   - Support up to 5,000 entries
   - Fast search response (< 500ms for typical queries)
   - Efficient rendering of HTML content

4. **User Interface**
   - Clean, modern web interface
   - Responsive design (works on desktop and mobile)
   - Real-time search as user types
   - Clear distinction between exact matches and similar results

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web Browser                          │
│  (React/Vue.js Frontend or Streamlit)                  │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/WebSocket
                     │
┌────────────────────▼────────────────────────────────────┐
│              Application Server                         │
│  (Flask/FastAPI or Streamlit)                           │
│  - Search API endpoints                                  │
│  - Entry retrieval                                      │
│  - HTML rendering                                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Search Engine Layer                        │
│  - Whoosh (full-text search)                            │
│  - FuzzyWuzzy (fuzzy matching)                          │
│  - NLTK/spaCy (stemming)                                │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Data Layer                                 │
│  - Encyclopedia HTML files                              │
│  - Indexed search data                                  │
│  - Entry metadata cache                                 │
└─────────────────────────────────────────────────────────┘
```

## Technology Stack

### Option 1: Streamlit (Recommended for Quick Development)

**Pros:**
- Rapid development
- Built-in UI components
- Python-native (matches existing codebase)
- Good for prototyping and internal tools

**Cons:**
- Less customizable than custom frontend
- Performance limitations for very large datasets
- Limited real-time interactivity

**Components:**
- `streamlit` - Main framework
- `whoosh` - Full-text search indexing
- `fuzzywuzzy` or `rapidfuzz` - Fuzzy string matching
- `nltk` or `spacy` - Stemming and NLP
- `lxml` / `BeautifulSoup` - HTML parsing and rendering

### Option 2: Flask/FastAPI + React/Vue.js (Recommended for Production)

**Pros:**
- Highly customizable
- Better performance
- Professional UI/UX
- Scalable architecture

**Cons:**
- More complex development
- Requires frontend and backend expertise
- Longer development time

**Backend Components:**
- `flask` or `fastapi` - Web framework
- `whoosh` - Full-text search
- `rapidfuzz` - Fast fuzzy matching
- `nltk` or `spacy` - Stemming

**Frontend Components:**
- `react` or `vue.js` - UI framework
- `axios` or `fetch` - API calls
- `react-markdown` or similar - HTML rendering

## Search Engine Design

### Index Structure

```python
# Whoosh Schema
schema = Schema(
    entry_id=ID(stored=True, unique=True),
    term=TEXT(stored=True, analyzer=StemmingAnalyzer()),
    search_terms=TEXT(stored=True, analyzer=StemmingAnalyzer()),
    canonical_term=TEXT(stored=True),
    wikidata_id=ID(stored=True),
    wikipedia_url=STORED,
    description_html=STORED,  # Full HTML content
    description_text=TEXT(analyzer=StemmingAnalyzer()),  # Plain text for search
    synonyms=KEYWORD(stored=True),
    category=KEYWORD(stored=True),
    # Metadata
    entry_index=NUMERIC(stored=True),
    created=STORED,
)
```

### Search Strategies

#### 1. Exact Match Search
- Direct term matching (case-insensitive)
- Fast lookup using Whoosh index
- Returns entries with exact term match

#### 2. Stemmed Search
- Uses NLTK Porter Stemmer or spaCy lemmatization
- "climate" matches "climates", "climatic", "climate's"
- Implemented via Whoosh StemmingAnalyzer

#### 3. Fuzzy/Levenshtein Search
- Uses RapidFuzz library (faster than FuzzyWuzzy)
- Calculates edit distance between query and terms
- Returns entries with similarity score > threshold (e.g., 80%)

```python
from rapidfuzz import fuzz, process

# Example fuzzy matching
matches = process.extract(
    query_term,
    all_terms,
    scorer=fuzz.ratio,
    limit=10,
    score_cutoff=80
)
```

#### 4. Regex Search
- Pattern matching using Python `re` module
- Useful for advanced users
- Searches across terms and descriptions

#### 5. Similarity Search
- Find entries similar to a given entry
- Uses:
  - Shared Wikidata IDs (synonyms)
  - Term similarity (fuzzy matching)
  - Shared keywords in descriptions
  - Category matching

### Search Query Processing

```python
def process_search_query(query: str, search_type: str = "auto"):
    """
    Process search query and return results.
    
    Args:
        query: User search query
        search_type: "exact", "stemmed", "fuzzy", "regex", "similarity", "auto"
    
    Returns:
        List of results with scores and match types
    """
    results = []
    
    if search_type == "auto":
        # Try exact match first
        exact_results = exact_search(query)
        if exact_results:
            return exact_results
        
        # Fall back to stemmed search
        stemmed_results = stemmed_search(query)
        if stemmed_results:
            return stemmed_results
        
        # Then fuzzy search
        fuzzy_results = fuzzy_search(query)
        return fuzzy_results
    
    # ... other search types
```

## User Interface Design

### Main Components

#### 1. Search Bar
```
┌─────────────────────────────────────────────────────┐
│  [🔍 Search...]  [Exact] [Stemmed] [Fuzzy] [Regex]│
└─────────────────────────────────────────────────────┘
```

- Real-time search as user types (debounced)
- Search type selector (radio buttons or dropdown)
- Clear button to reset search

#### 2. Results Display

**Precise Hits Section:**
```
┌─────────────────────────────────────────────────────┐
│  Precise Matches (3)                                │
├─────────────────────────────────────────────────────┤
│  [Entry 1] Climate Change                           │
│  Wikidata: Q7942 | Wikipedia: [link]               │
│  [HTML content displayed here]                     │
│                                                     │
│  [Entry 2] ...                                      │
└─────────────────────────────────────────────────────┘
```

**Similar Results Section:**
```
┌─────────────────────────────────────────────────────┐
│  Similar Entries (12)                               │
├─────────────────────────────────────────────────────┤
│  • Global Warming (similarity: 85%)                 │
│  • Climate (similarity: 78%)                        │
│  • Greenhouse Effect (similarity: 72%)              │
│  ...                                                │
└─────────────────────────────────────────────────────┘
```

#### 3. Entry Detail View
- Full HTML rendering
- Expandable sections
- Links to Wikipedia/Wikidata
- Related entries sidebar
- Navigation (previous/next entry)

#### 4. Browse View
- Alphabetical listing (A-Z)
- Category filtering
- Pagination (50 entries per page)

### Streamlit UI Layout (Option 1)

```python
# Main layout
st.title("Encyclopedia Browser")

# Sidebar for filters
with st.sidebar:
    st.header("Filters")
    category_filter = st.multiselect("Categories", categories)
    search_type = st.radio("Search Type", 
                          ["Auto", "Exact", "Stemmed", "Fuzzy", "Regex"])

# Main area
search_query = st.text_input("Search", key="search")

if search_query:
    results = search_encyclopedia(search_query, search_type)
    
    # Precise matches
    if results['exact']:
        st.subheader(f"Precise Matches ({len(results['exact'])})")
        for entry in results['exact']:
            display_entry(entry)
    
    # Similar results
    if results['similar']:
        st.subheader(f"Similar Entries ({len(results['similar'])})")
        for entry in results['similar']:
            display_similar_entry(entry)
else:
    # Browse view
    display_browse_view()
```

## Data Structures

### Entry Representation

```python
@dataclass
class EncyclopediaEntry:
    """Represents a single encyclopedia entry."""
    entry_id: str
    term: str
    canonical_term: str
    search_terms: List[str]
    wikidata_id: str
    wikipedia_url: str
    description_html: str
    description_text: str  # Plain text version
    synonyms: List[str]
    category: str
    entry_index: int
    metadata: Dict[str, Any]
```

### Search Result

```python
@dataclass
class SearchResult:
    """Represents a search result."""
    entry: EncyclopediaEntry
    score: float  # Relevance score (0-100)
    match_type: str  # "exact", "stemmed", "fuzzy", "regex"
    matched_fields: List[str]  # Which fields matched
    highlights: Dict[str, List[str]]  # Highlighted snippets
```

## Performance Considerations

### Indexing Strategy

1. **Pre-build Index**
   - Build Whoosh index when encyclopedia is loaded
   - Store index on disk for persistence
   - Update index incrementally when entries change

2. **Caching**
   - Cache search results for common queries
   - Cache HTML rendering
   - Cache entry metadata

3. **Lazy Loading**
   - Load full HTML only when entry is viewed
   - Use pagination for browse view
   - Virtual scrolling for large result sets

### Optimization Techniques

```python
# Example: Cached index loading
@lru_cache(maxsize=1)
def get_search_index():
    """Load and cache search index."""
    return whoosh.open_dir("index_dir")

# Example: Debounced search
from streamlit.runtime.scriptrunner import get_script_run_ctx

def debounced_search(query, delay=300):
    """Debounce search input."""
    # Implementation depends on framework
    pass
```

## Implementation Phases

### Phase 1: Basic Search (MVP)
- [ ] Load encyclopedia from HTML file
- [ ] Build Whoosh index
- [ ] Implement exact and stemmed search
- [ ] Display results in simple list
- [ ] Render HTML content

### Phase 2: Advanced Search
- [ ] Add fuzzy/Levenshtein matching
- [ ] Add regex search
- [ ] Implement similarity search
- [ ] Add search result highlighting

### Phase 3: UI Enhancement
- [ ] Improve result display (precise vs similar)
- [ ] Add entry detail view
- [ ] Implement browse view
- [ ] Add filters and sorting

### Phase 4: Performance & Polish
- [ ] Optimize indexing
- [ ] Add caching
- [ ] Improve UI/UX
- [ ] Add keyboard shortcuts
- [ ] Mobile responsiveness

## File Structure

```
encyclopedia/
├── browser/
│   ├── __init__.py
│   ├── app.py                 # Streamlit app (if using Streamlit)
│   ├── search_engine.py       # Search functionality
│   ├── indexer.py             # Whoosh index building
│   ├── matchers.py            # Fuzzy/regex matching
│   ├── renderer.py            # HTML rendering
│   └── models.py              # Data models
├── Examples/
│   └── create_encyclopedia_from_wordlist.py
└── docs/
    └── encyclopedia_browser_design.md
```

## Dependencies

### Required Packages

```txt
# Search
whoosh>=2.7.4              # Full-text search engine
rapidfuzz>=3.0.0           # Fast fuzzy string matching
nltk>=3.8                  # Stemming (or spacy>=3.5)

# Web Framework (choose one)
streamlit>=1.28.0          # Option 1: Streamlit
flask>=2.3.0               # Option 2: Flask
fastapi>=0.104.0           # Option 2: FastAPI

# HTML Processing
lxml>=4.9.0                # HTML parsing
beautifulsoup4>=4.12.0    # HTML processing

# Utilities
python-Levenshtein>=0.21.0 # Optional: C extension for Levenshtein
```

## Example Usage

### Loading Encyclopedia

```python
from encyclopedia.browser.search_engine import EncyclopediaSearchEngine

# Load encyclopedia and build index
search_engine = EncyclopediaSearchEngine()
search_engine.load_encyclopedia("path/to/encyclopedia.html")
search_engine.build_index()
```

### Searching

```python
# Exact search
results = search_engine.search("climate change", search_type="exact")

# Fuzzy search
results = search_engine.search("climat chang", search_type="fuzzy", threshold=80)

# Stemmed search
results = search_engine.search("climate", search_type="stemmed")

# Regex search
results = search_engine.search("climat.*chang", search_type="regex")
```

### Displaying Results

```python
for result in results:
    print(f"Term: {result.entry.term}")
    print(f"Score: {result.score}")
    print(f"Match Type: {result.match_type}")
    print(f"HTML: {result.entry.description_html}")
```

## Open Source Tools Used

1. **Whoosh** - Pure Python full-text search library
   - No external dependencies
   - Fast indexing and searching
   - Supports stemming analyzers
   - License: BSD 2-Clause

2. **RapidFuzz** - Fast string matching library
   - Faster than FuzzyWuzzy
   - Supports Levenshtein, ratio, partial ratio
   - License: MIT

3. **NLTK** - Natural Language Toolkit
   - Stemming (Porter Stemmer)
   - Tokenization
   - License: Apache 2.0

4. **Streamlit** (if chosen)
   - Rapid web app development
   - Built-in UI components
   - License: Apache 2.0

## Future Enhancements

1. **Advanced Features**
   - Multi-language support
   - Search history
   - Saved searches
   - Export functionality
   - Collaborative editing

2. **Analytics**
   - Search analytics
   - Popular entries tracking
   - User behavior metrics

3. **Integration**
   - API endpoints for external access
   - Embedding in other applications
   - Command-line interface

## Notes

- Design prioritizes performance for up to 5,000 entries
- Uses open-source tools exclusively
- Modular design allows easy extension
- Can be implemented incrementally (MVP first, then enhancements)
- Compatible with existing encyclopedia format
