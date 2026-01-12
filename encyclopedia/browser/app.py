"""
Streamlit app for encyclopedia browser.

Provides web interface for searching and browsing encyclopedia entries.
"""

import streamlit as st
from pathlib import Path
from typing import List

# Check for required dependencies before importing
try:
    import whoosh
except ImportError:
    st.error("""
    ## Missing Required Dependency: whoosh
    
    Please install required dependencies:
    ```bash
    pip install streamlit whoosh nltk lxml
    python -m nltk.downloader punkt stopwords
    ```
    
    Optional (for fuzzy search):
    ```bash
    pip install rapidfuzz
    ```
    """)
    st.stop()

try:
    from encyclopedia.browser.search_engine import EncyclopediaSearchEngine
    from encyclopedia.browser.models import SearchResult, EncyclopediaEntry
except ImportError as e:
    st.error(f"""
    ## Import Error
    
    {str(e)}
    
    Please install required dependencies:
    ```bash
    pip install streamlit whoosh nltk lxml
    python -m nltk.downloader punkt stopwords
    ```
    """)
    st.stop()


# Page configuration
st.set_page_config(
    page_title="Encyclopedia Browser",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'search_engine' not in st.session_state:
    st.session_state.search_engine = None
if 'encyclopedia_loaded' not in st.session_state:
    st.session_state.encyclopedia_loaded = False


def display_entry(entry: EncyclopediaEntry, show_html: bool = True):
    """Display an encyclopedia entry.
    
    Args:
        entry: EncyclopediaEntry to display
        show_html: Whether to render HTML content
    """
    with st.container():
        # Header with term and metadata
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(entry.term)
            if entry.canonical_term and entry.canonical_term != entry.term:
                st.caption(f"Canonical term: {entry.canonical_term}")
        
        with col2:
            if entry.wikidata_id:
                st.markdown(f"**Wikidata:** {entry.wikidata_id}")
            if entry.wikipedia_url:
                st.markdown(f"[Wikipedia]({entry.wikipedia_url})")
        
        # Synonyms
        if entry.synonyms:
            synonyms_text = ", ".join(entry.synonyms)
            st.caption(f"Synonyms: {synonyms_text}")
        
        # Description HTML
        if show_html and entry.description_html:
            st.markdown("---")
            st.markdown(entry.description_html, unsafe_allow_html=True)
        elif entry.description_text:
            st.markdown("---")
            st.markdown(entry.description_text)
        
        st.markdown("---")


def display_search_result(result: SearchResult):
    """Display a search result.
    
    Args:
        result: SearchResult to display
    """
    with st.expander(f"{result.entry.term} (Score: {result.score:.1f}, Type: {result.match_type})"):
        display_entry(result.entry, show_html=True)


def main():
    """Main application."""
    st.title("📚 Encyclopedia Browser")
    st.markdown("Search and browse encyclopedia entries")
    
    # Check for optional dependencies
    try:
        import rapidfuzz
    except ImportError:
        st.info("💡 **Tip:** Install `rapidfuzz` for fuzzy search: `pip install rapidfuzz`")
    
    # Sidebar for encyclopedia loading
    with st.sidebar:
        st.header("📖 Load Encyclopedia")
        
        uploaded_file = st.file_uploader(
            "Upload Encyclopedia HTML File",
            type=['html'],
            help="Upload an encyclopedia HTML file created by the encyclopedia tools"
        )
        
        file_path_input = st.text_input(
            "Or enter file path:",
            placeholder="/path/to/encyclopedia.html"
        )
        
        if st.button("Load Encyclopedia", type="primary"):
            html_file = None
            
            if uploaded_file is not None:
                # Save uploaded file temporarily
                import tempfile
                temp_path = Path(tempfile.gettempdir()) / uploaded_file.name
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                html_file = temp_path
            elif file_path_input:
                html_file = Path(file_path_input)
            
            if html_file and html_file.exists():
                try:
                    with st.spinner("Loading encyclopedia and building index..."):
                        search_engine = EncyclopediaSearchEngine()
                        search_engine.load_encyclopedia(html_file)
                        st.session_state.search_engine = search_engine
                        st.session_state.encyclopedia_loaded = True
                    st.success("Encyclopedia loaded successfully!")
                except Exception as e:
                    st.error(f"Error loading encyclopedia: {e}")
            else:
                st.error("Please upload a file or provide a valid file path.")
        
        st.markdown("---")
        
        # Search options
        if st.session_state.encyclopedia_loaded:
            st.header("🔍 Search Options")
            # Check if fuzzy search is available
            try:
                import rapidfuzz
                search_options = ["Auto", "Exact", "Stemmed", "Fuzzy"]
            except ImportError:
                search_options = ["Auto", "Exact", "Stemmed"]
                st.info("💡 Install rapidfuzz for fuzzy search: `pip install rapidfuzz`")
            
            search_type = st.radio(
                "Search Type",
                search_options,
                help="Auto: tries exact, then stemmed, then fuzzy (if available)"
            )
            st.session_state.search_type = search_type.lower()
    
    # Main content area
    if not st.session_state.encyclopedia_loaded:
        st.info("👈 Please load an encyclopedia file from the sidebar to get started.")
        st.markdown("""
        ### How to use:
        1. Create an encyclopedia using `create_encyclopedia_from_wordlist.py`
        2. Load the generated HTML file using the sidebar
        3. Search and browse entries
        """)
        return
    
    search_engine = st.session_state.search_engine
    
    # Search interface
    st.header("🔍 Search")
    search_query = st.text_input(
        "Enter search query:",
        placeholder="e.g., climate change",
        key="search_input"
    )
    
    # Browse/Search tabs
    tab1, tab2 = st.tabs(["Search Results", "Browse All"])
    
    with tab1:
        if search_query:
            search_type = st.session_state.get('search_type', 'auto')
            
            with st.spinner("Searching..."):
                results = search_engine.search(
                    search_query,
                    search_type=search_type,
                    limit=50
                )
            
            if results:
                # Separate exact matches from others
                exact_matches = [r for r in results if r.match_type == "exact"]
                other_matches = [r for r in results if r.match_type != "exact"]
                
                if exact_matches:
                    st.subheader(f"✓ Precise Matches ({len(exact_matches)})")
                    for result in exact_matches:
                        display_search_result(result)
                
                if other_matches:
                    st.subheader(f"📋 Other Results ({len(other_matches)})")
                    for result in other_matches:
                        display_search_result(result)
            else:
                st.info("No results found. Try a different search term or search type.")
        else:
            st.info("Enter a search query above to find entries.")
    
    with tab2:
        st.subheader("Browse All Entries")
        
        # Get all entries
        with st.spinner("Loading entries..."):
            all_entries = search_engine.get_all_entries(limit=1000)
        
        if all_entries:
            st.write(f"Showing {len(all_entries)} entries")
            
            # Simple pagination
            entries_per_page = 20
            total_pages = (len(all_entries) + entries_per_page - 1) // entries_per_page
            
            if total_pages > 1:
                page = st.number_input(
                    "Page",
                    min_value=1,
                    max_value=total_pages,
                    value=1,
                    step=1
                )
                start_idx = (page - 1) * entries_per_page
                end_idx = start_idx + entries_per_page
                page_entries = all_entries[start_idx:end_idx]
            else:
                page_entries = all_entries
            
            for entry in page_entries:
                display_entry(entry, show_html=False)
                st.markdown("---")
        else:
            st.info("No entries found in encyclopedia.")


if __name__ == "__main__":
    main()
