# Encyclopedia Browser - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies

```bash
# Install required packages
pip install streamlit whoosh nltk lxml rapidfuzz

# Download NLTK data
python -m nltk.downloader punkt stopwords

# Install encyclopedia package
pip install -e .
```

### Step 2: Create an Encyclopedia

```bash
# Create from wordlist
python -m Examples.create_encyclopedia_from_wordlist \
    --wordlist Examples/my_terms.txt \
    --output my_encyclopedia.html
```

### Step 3: Launch Browser

```bash
# Launch the browser
python encyclopedia/browser/run_browser.py

# Browser opens at http://localhost:8501
```

## 📖 Basic Usage

1. **Load Encyclopedia**: Upload `my_encyclopedia.html` in the sidebar
2. **Search**: Type a term (e.g., "climate") and press Enter
3. **Browse**: Click "Browse All" tab to see all entries

## 🔍 Search Examples

### Example 1: Exact Search
```
Query: "IPCC"
Result: Finds exact match for "IPCC"
```

### Example 2: Stemmed Search
```
Query: "climate"
Result: Finds "climate", "climates", "climatic", "climatology"
```

### Example 3: Fuzzy Search
```
Query: "climat chang" (typo)
Result: Finds "climate change" (similarity: 92%)
```

### Example 4: Auto Search (Recommended)
```
Query: "greenhouse"
Result: Tries exact → stemmed → fuzzy automatically
```

## 💻 Programmatic Example

```python
from pathlib import Path
from encyclopedia.browser.search_engine import EncyclopediaSearchEngine

# Load encyclopedia
engine = EncyclopediaSearchEngine()
engine.load_encyclopedia(Path("my_encyclopedia.html"))

# Search
results = engine.search("climate change", search_type="auto")

# Display
for result in results:
    print(f"{result.entry.term} (score: {result.score:.1f})")
```

## 🆘 Troubleshooting

**Check dependencies:**
```bash
python encyclopedia/browser/check_dependencies.py
```

**Install missing packages:**
```bash
pip install whoosh rapidfuzz  # etc.
```

**Verify encyclopedia package:**
```bash
pip install -e .
```

## 📚 More Information

- **Full Tutorial**: See `TUTORIAL.md`
- **Documentation**: See `README.md`
- **Design**: See `../../docs/encyclopedia_browser_design.md`
