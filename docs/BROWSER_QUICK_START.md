# Browser Quick Start Guide

**Date:** February 21, 2026

## Two Browser Options

The encyclopedia project provides two ways to browse entries:

### 1. HTML Browser (Casual Users)

**No installation required** - just open an HTML file!

```bash
# Generate HTML landing page
python Examples/create_landing_page_example.py

# Output: temp/examples/landing_page/encyclopedia_landing_page.html
# Double-click to open in any browser
```

**Best for:**
- ✅ Casual browsing
- ✅ No installation
- ✅ Offline access
- ✅ Easy sharing

### 2. Streamlit Browser (Advanced Users)

**Requires installation** - but provides advanced features!

```bash
# Install dependencies (one-time)
pip install streamlit whoosh nltk lxml
python -m nltk.downloader punkt stopwords

# Optional: fuzzy search
pip install rapidfuzz

# Launch browser
streamlit run encyclopedia/browser/app.py

# Opens at: http://localhost:8501
# Upload your encyclopedia HTML file in the sidebar
```

**Best for:**
- ✅ Advanced search
- ✅ Complex operations
- ✅ Future editing features
- ✅ Team collaboration

## Which Should I Use?

**Use HTML Browser if:**
- You just want to browse entries
- You don't want to install anything
- You need offline access
- You want to share with others easily

**Use Streamlit Browser if:**
- You need advanced search features
- You want to edit entries (future feature)
- You need complex filtering/sorting
- You're comfortable with Python installations

## More Information

- **Detailed Comparison:** See `BROWSER_COMPARISON.md`
- **Streamlit Tutorial:** See `encyclopedia/browser/README.md`
- **User Guide:** See `USER_GUIDE.md`
