# Streamlit Landing Page Proposal

**Date:** February 21, 2026  
**Status:** Proposal

## Problem Statement

The custom HTML/CSS/JavaScript landing page requires manual maintenance and is prone to errors (e.g., backspace key handling). Using Streamlit would provide:

- **Better Maintainability**: Framework handles UI interactions
- **Less Error-Prone**: No manual event handling
- **Consistent UI**: Streamlit's built-in components
- **Easier Updates**: Python-based, easier to modify
- **Better Integration**: Works with existing Streamlit browser

## Current State

### Existing Streamlit Browser (`encyclopedia/browser/app.py`)
- ✅ Search functionality (exact, stemmed, fuzzy)
- ✅ Browse all entries (paginated)
- ✅ Entry display
- ✅ File upload
- ❌ Missing: Table of Contents
- ❌ Missing: Statistics dashboard
- ❌ Missing: Search target options (term/definition/description)
- ❌ Missing: Landing page layout

### Custom HTML Landing Page (`temp/examples/landing_page/encyclopedia_landing_page.html`)
- ✅ Table of Contents
- ✅ Statistics dashboard
- ✅ Search options (target, type)
- ✅ Landing page layout
- ❌ Requires manual JavaScript maintenance
- ❌ Error-prone (backspace issue demonstrated)
- ❌ No integration with existing browser

## Proposed Solution

**Enhance the existing Streamlit browser** (`encyclopedia/browser/app.py`) with landing page features:

### Phase 1: Add Landing Page Tab
- New "Landing Page" tab as default view
- Shows TOC, statistics, and search interface
- Uses Streamlit components (no custom JavaScript)

### Phase 2: Add Missing Features
- **Table of Contents**: Using Streamlit's expander components
- **Statistics Dashboard**: Using Streamlit's metric components
- **Enhanced Search**: Add search target options (term/definition/description)
- **Better Layout**: Use Streamlit columns and containers

### Phase 3: Remove Custom HTML Generator
- Deprecate `Examples/create_landing_page_example.py`
- All functionality in Streamlit browser

## Benefits

1. **Maintainability**: Streamlit handles UI interactions
2. **Consistency**: Single UI framework (Streamlit)
3. **Less Code**: No custom JavaScript to maintain
4. **Better UX**: Streamlit's responsive design
5. **Integration**: Works seamlessly with existing search engine

## Implementation Plan

### Step 1: Add Landing Page Tab
```python
# In encyclopedia/browser/app.py
tab1, tab2, tab3 = st.tabs(["Landing Page", "Search", "Browse All"])

with tab1:
    # Landing page content
    display_statistics()
    display_table_of_contents()
    display_search_interface()
```

### Step 2: Add Statistics Dashboard
```python
def display_statistics(encyclopedia):
    st.header("📊 Statistics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Entries", len(encyclopedia.entries))
    # ... etc
```

### Step 3: Add Table of Contents
```python
def display_table_of_contents(encyclopedia):
    st.header("📑 Table of Contents")
    # Group by letter
    for letter in sorted(entries_by_letter.keys()):
        with st.expander(f"{letter} ({len(entries_by_letter[letter])})"):
            for entry in entries_by_letter[letter]:
                st.write(f"- {entry.term}")
```

### Step 4: Enhance Search Options
```python
search_target = st.selectbox(
    "Search In:",
    ["All Fields", "Term Only", "Definition Only", "Description Only"]
)
```

## Migration Path

1. **Enhance Streamlit browser** with landing page features
2. **Test thoroughly** with existing encyclopedias
3. **Deprecate HTML generator** (keep for reference)
4. **Update documentation** to use Streamlit browser

## Recommendation

**Use Streamlit for landing page** instead of custom HTML:
- ✅ Better maintainability
- ✅ Less error-prone
- ✅ Consistent with existing browser
- ✅ Easier to extend

The custom HTML example can remain as a reference, but the primary landing page should be in Streamlit.
