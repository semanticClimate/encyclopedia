# Encyclopedia Browser - Quick Tutorial

## 🚀 Quick Start (5 minutes)

### Step 1: Install Dependencies

```bash
# Required dependencies
pip install streamlit whoosh nltk lxml

# Optional: For fuzzy search (recommended)
pip install rapidfuzz

# Download NLTK data
python -m nltk.downloader punkt stopwords
```

**Note:** The browser works without `rapidfuzz`, but fuzzy search will be disabled. Install it for full functionality.

### Step 2: Create an Encyclopedia

```bash
# From project root
python -m Examples.create_encyclopedia_from_wordlist \
    --wordlist Examples/my_terms.txt \
    --output my_encyclopedia.html
```

### Step 3: Launch the Browser

```bash
# Option 1: Using the launcher script
python encyclopedia/browser/run_browser.py

# Option 2: Direct Streamlit command
streamlit run encyclopedia/browser/app.py
```

### Step 4: Load and Search

1. **Load Encyclopedia**: In the sidebar, upload `my_encyclopedia.html`
2. **Search**: Type "climate" in the search box
3. **Browse**: Click "Browse All" tab to see all entries

## 📖 Detailed Tutorial

### Understanding Search Types

#### 1. Exact Search
**Best for:** Known exact terms

**Example:**
- Query: `climate change`
- Finds: Only entries with exact term "climate change"
- Speed: ⚡ Fastest

#### 2. Stemmed Search  
**Best for:** Finding word variations

**Example:**
- Query: `climate`
- Finds: "climate", "climates", "climatic", "climatology"
- Speed: ⚡⚡ Fast

**How it works:** Uses stemming to match word roots. "climate" matches "climates" because they share the same stem.

#### 3. Fuzzy Search
**Best for:** Typos, partial matches, similar terms

**Example:**
- Query: `climat chang` (missing 'e')
- Finds: "climate change" (similarity: 92%)
- Speed: ⚡⚡⚡ Moderate

**How it works:** Uses Levenshtein distance to find similar strings. Useful when you're not sure of exact spelling.

#### 4. Auto Search (Recommended)
**Best for:** General use

**How it works:**
1. Tries exact match first
2. Falls back to stemmed search
3. Falls back to fuzzy search if needed

**Example:**
- Query: `climate`
- Tries exact → finds nothing
- Tries stemmed → finds "climate", "climates", etc.

### Search Tips

#### Tip 1: Use Specific Terms
- ✅ Good: `greenhouse gas`
- ❌ Less specific: `gas`

#### Tip 2: Try Different Search Types
- If exact search finds nothing → try stemmed
- If stemmed finds nothing → try fuzzy
- Auto search does this automatically!

#### Tip 3: Use Partial Terms
- `carbon` will find "carbon dioxide", "carbon cycle", etc.
- Fuzzy search handles partial matches well

### Browsing Entries

The "Browse All" tab shows all entries paginated (20 per page).

**Features:**
- Navigate pages using the page number input
- View entry summaries (HTML not shown in browse view)
- Click on entries to see full details

### Understanding Results

#### Precise Matches
- Shown first
- Exact or very close matches
- Score: 100 (exact) or high scores (stemmed)

#### Other Results
- Similar entries
- Lower scores but still relevant
- Useful for discovery

#### Result Information
- **Score**: Relevance score (0-100)
- **Match Type**: How it matched (exact/stemmed/fuzzy)
- **Term**: Entry term
- **Wikidata ID**: Unique identifier
- **Wikipedia Link**: Link to Wikipedia page
- **Synonyms**: Related terms
- **Description**: Full HTML content

## 🎯 Common Use Cases

### Use Case 1: Find a Specific Entry

1. Enter exact term: `IPCC`
2. Select "Exact" search type
3. View precise match

### Use Case 2: Explore Related Topics

1. Enter term: `climate`
2. Select "Stemmed" search type
3. Browse all climate-related entries

### Use Case 3: Handle Typos

1. Enter misspelled term: `climat chang`
2. Select "Fuzzy" search type
3. Find "climate change" with similarity score

### Use Case 4: Discover New Entries

1. Enter broad term: `carbon`
2. Select "Auto" search type
3. Explore all carbon-related entries

## 🔧 Troubleshooting

### Problem: "No index loaded"

**Solution:** Load an encyclopedia file first using the sidebar upload button.

### Problem: Search returns no results

**Solutions:**
1. Try "Fuzzy" search type
2. Check spelling
3. Try broader terms
4. Verify encyclopedia was loaded successfully

### Problem: Slow search

**Solutions:**
1. Wait for initial index build to complete
2. Limit results if needed
3. Use exact search for fastest results

### Problem: HTML not displaying

**Solutions:**
1. Ensure `lxml` is installed: `pip install lxml`
2. Check browser console for errors
3. Some HTML may not render perfectly in Streamlit

## 📊 Example Workflow

### Complete Workflow: Creating and Browsing an Encyclopedia

```bash
# 1. Create encyclopedia from wordlist
python -m Examples.create_encyclopedia_from_wordlist \
    --wordlist Examples/my_terms.txt \
    --output climate_encyclopedia.html

# 2. Launch browser
streamlit run encyclopedia/browser/app.py

# 3. In browser:
#    - Upload climate_encyclopedia.html
#    - Search for "greenhouse"
#    - Browse all entries
#    - Explore related topics
```

## 🎓 Learning Path

1. **Start Simple**: Use "Auto" search with common terms
2. **Explore**: Try different search types to see differences
3. **Browse**: Use Browse All to see what's available
4. **Advanced**: Experiment with fuzzy search for discovery

## 💡 Pro Tips

1. **Use Auto Search**: It's smart and handles most cases
2. **Check Synonyms**: Entries show related terms
3. **Follow Links**: Click Wikipedia links for more info
4. **Browse First**: Use Browse All to get familiar with content
5. **Combine Terms**: Try multiple searches to explore

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check the [design document](../../docs/encyclopedia_browser_design.md) for architecture
- Experiment with different search queries
- Try creating larger encyclopedias

## 🆘 Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Review error messages carefully
3. Ensure all dependencies are installed
4. Verify your encyclopedia file is valid

Happy browsing! 🎉
