"""
Streamlit app for encyclopedia browser with landing page.

Provides web interface for searching and browsing encyclopedia entries.
Includes landing page with TOC, statistics, and enhanced search.
"""

import streamlit as st
from pathlib import Path
from typing import List, Dict
from collections import defaultdict
import re

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
if 'all_entries' not in st.session_state:
    st.session_state.all_entries = None


def extract_text_from_html(html: str) -> str:
    """Extract plain text from HTML."""
    if not html:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html)
    return text.strip()


def get_statistics(entries: List[EncyclopediaEntry]) -> Dict:
    """Calculate encyclopedia statistics.
    
    Args:
        entries: List of encyclopedia entries
        
    Returns:
        Dictionary with statistics
    """
    total = len(entries)
    with_descriptions = sum(1 for e in entries if e.description_html or e.description_text)
    with_images = sum(1 for e in entries if hasattr(e, 'image_link') and e.image_link)
    with_wikidata = sum(1 for e in entries if e.wikidata_id and e.wikidata_id not in ('', 'no_wikidata_id'))
    with_wikipedia = sum(1 for e in entries if e.wikipedia_url)
    
    return {
        'total_entries': total,
        'entries_with_descriptions': with_descriptions,
        'entries_with_images': with_images,
        'entries_with_wikidata': with_wikidata,
        'entries_with_wikipedia': with_wikipedia,
        'description_percentage': (with_descriptions * 100 // total) if total > 0 else 0,
        'image_percentage': (with_images * 100 // total) if total > 0 else 0,
        'wikidata_percentage': (with_wikidata * 100 // total) if total > 0 else 0,
    }


def get_entries_by_letter(entries: List[EncyclopediaEntry]) -> Dict[str, List[EncyclopediaEntry]]:
    """Group entries by first letter.
    
    Args:
        entries: List of encyclopedia entries
        
    Returns:
        Dictionary mapping letter to list of entries
    """
    entries_by_letter = defaultdict(list)
    for entry in entries:
        if entry.term:
            first_letter = entry.term[0].upper()
            if first_letter.isalpha():
                entries_by_letter[first_letter].append(entry)
            else:
                entries_by_letter['0-9'].append(entry)
    return dict(entries_by_letter)


def display_statistics(entries: List[EncyclopediaEntry]):
    """Display statistics dashboard.
    
    Args:
        entries: List of encyclopedia entries
    """
    stats = get_statistics(entries)
    
    st.header("📊 Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Entries", stats['total_entries'])
    
    with col2:
        st.metric(
            "With Descriptions",
            f"{stats['entries_with_descriptions']} ({stats['description_percentage']}%)"
        )
    
    with col3:
        st.metric(
            "With Images",
            f"{stats['entries_with_images']} ({stats['image_percentage']}%)"
        )
    
    with col4:
        st.metric(
            "With Wikidata",
            f"{stats['entries_with_wikidata']} ({stats['wikidata_percentage']}%)"
        )


def display_table_of_contents(entries: List[EncyclopediaEntry]):
    """Display table of contents.
    
    Args:
        entries: List of encyclopedia entries
    """
    st.header("📑 Table of Contents")
    
    entries_by_letter = get_entries_by_letter(entries)
    
    # Quick jump navigation
    letters = sorted([l for l in entries_by_letter.keys() if l != '0-9'])
    if '0-9' in entries_by_letter:
        letters.append('0-9')
    
    # Quick jump buttons
    cols = st.columns(min(len(letters), 26))
    for idx, letter in enumerate(letters[:26]):
        with cols[idx]:
            if st.button(letter, key=f"jump_{letter}", use_container_width=True):
                st.session_state[f"scroll_to_{letter}"] = True
    
    st.markdown("---")
    
    # Letter sections
    for letter in sorted(entries_by_letter.keys()):
        letter_entries = entries_by_letter[letter]
        
        with st.expander(f"{letter} ({len(letter_entries)} entries)", expanded=False):
            # Display entries in columns
            for i in range(0, len(letter_entries), 3):
                cols = st.columns(3)
                for j, entry in enumerate(letter_entries[i:i+3]):
                    with cols[j]:
                        has_image = "📷" if (hasattr(entry, 'image_link') and entry.image_link) else ""
                        has_desc = "📄" if (entry.description_html or entry.description_text) else ""
                        st.write(f"{has_image}{has_desc} **{entry.term}**")


def search_entries_by_target(
    entries: List[EncyclopediaEntry],
    query: str,
    search_target: str,
    search_type: str
) -> List[EncyclopediaEntry]:
    """Search entries with target filtering.
    
    Args:
        entries: List of entries to search
        query: Search query
        search_target: "all", "term", "definition", or "description"
        search_type: "partial", "exact", "word", or "regex"
        
    Returns:
        List of matching entries
    """
    if not query or not query.strip():
        return entries
    
    query = query.strip().lower()
    results = []
    
    # Build regex based on search type
    try:
        if search_type == 'exact':
            regex = re.compile(f'^{re.escape(query)}$', re.IGNORECASE)
        elif search_type == 'word':
            regex = re.compile(rf'\b{re.escape(query)}\b', re.IGNORECASE)
        elif search_type == 'regex':
            regex = re.compile(query, re.IGNORECASE)
        else:  # partial
            regex = re.compile(re.escape(query), re.IGNORECASE)
    except re.error:
        return []  # Invalid regex
    
    for entry in entries:
        term = entry.term.lower()
        definition_text = extract_text_from_html(entry.description_html or entry.description_text or "")
        description_text = definition_text.lower()
        
        matches = False
        
        if search_target == 'term':
            matches = bool(regex.search(term))
        elif search_target == 'definition':
            # Use first sentence as definition
            first_sentence = description_text.split('.')[0] if description_text else ""
            matches = bool(regex.search(first_sentence))
        elif search_target == 'description':
            matches = bool(regex.search(description_text))
        else:  # all
            matches = (
                bool(regex.search(term)) or
                bool(regex.search(description_text))
            )
        
        if matches:
            results.append(entry)
    
    return results


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
                st.markdown(f"**Wikidata:** [{entry.wikidata_id}](https://www.wikidata.org/wiki/{entry.wikidata_id})")
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
                        
                        # Load all entries for TOC and statistics
                        all_entries = search_engine.get_all_entries(limit=10000)
                        st.session_state.all_entries = all_entries
                    st.success("Encyclopedia loaded successfully!")
                except Exception as e:
                    st.error(f"Error loading encyclopedia: {e}")
            else:
                st.error("Please upload a file or provide a valid file path.")
        
        st.markdown("---")
        
        # Search options
        if st.session_state.encyclopedia_loaded:
            st.header("🔍 Search Options")
            
            # Search target
            search_target = st.selectbox(
                "Search In:",
                ["All Fields", "Term Only", "Definition Only", "Description Only"],
                help="Choose which fields to search"
            )
            st.session_state.search_target = search_target.lower().replace(' ', '_')
            
            # Search type
            try:
                import rapidfuzz
                search_type_options = ["Auto", "Exact", "Stemmed", "Fuzzy", "Partial", "Word", "Regex"]
            except ImportError:
                search_type_options = ["Auto", "Exact", "Stemmed", "Partial", "Word", "Regex"]
                st.info("💡 Install rapidfuzz for fuzzy search: `pip install rapidfuzz`")
            
            search_type = st.selectbox(
                "Search Type:",
                search_type_options,
                help="Choose search matching type"
            )
            st.session_state.search_type = search_type.lower()
    
    # Main content area
    if not st.session_state.encyclopedia_loaded:
        st.info("👈 Please load an encyclopedia file from the sidebar to get started.")
        st.markdown("""
        ### How to use:
        1. Create an encyclopedia using `create_encyclopedia_from_wordlist.py`
        2. Load the generated HTML file using the sidebar
        3. Explore the landing page, search, and browse entries
        """)
        return
    
    search_engine = st.session_state.search_engine
    all_entries = st.session_state.all_entries
    
    if not all_entries:
        all_entries = search_engine.get_all_entries(limit=10000)
        st.session_state.all_entries = all_entries
    
    # Main tabs: Landing Page, Search, Browse
    tab1, tab2, tab3 = st.tabs(["🏠 Landing Page", "🔍 Search", "📖 Browse All"])
    
    with tab1:
        # Landing Page Content
        st.header("Welcome to the Encyclopedia")
        
        # Statistics Dashboard
        display_statistics(all_entries)
        
        st.markdown("---")
        
        # Search Interface on Landing Page
        st.header("🔍 Search")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            landing_search_query = st.text_input(
                "Search entries:",
                placeholder="e.g., climate, atom, DNA",
                key="landing_search"
            )
        with col2:
            st.write("")  # Spacer
            st.write("")  # Spacer
            if st.button("Search", key="landing_search_button"):
                st.session_state.landing_search_executed = True
                st.session_state.landing_search_query = landing_search_query
        
        # Execute search if button clicked
        if st.session_state.get('landing_search_executed') and st.session_state.get('landing_search_query'):
            search_target = st.session_state.get('search_target', 'all_fields')
            search_type = st.session_state.get('search_type', 'auto')
            
            # Convert search_target to format used by search function
            target_map = {
                'all_fields': 'all',
                'term_only': 'term',
                'definition_only': 'definition',
                'description_only': 'description'
            }
            target = target_map.get(search_target, 'all')
            
            # Use search engine for advanced search, or simple filtering
            if search_type in ['auto', 'exact', 'stemmed', 'fuzzy']:
                # Use search engine
                with st.spinner("Searching..."):
                    results = search_engine.search(
                        st.session_state.landing_search_query,
                        search_type=search_type,
                        limit=50
                    )
                
                if results:
                    st.subheader(f"Found {len(results)} results")
                    for result in results:
                        display_search_result(result)
                else:
                    st.info("No results found.")
            else:
                # Use simple filtering
                filtered = search_entries_by_target(
                    all_entries,
                    st.session_state.landing_search_query,
                    target,
                    search_type
                )
                
                if filtered:
                    st.subheader(f"Found {len(filtered)} results")
                    for entry in filtered[:50]:  # Limit to 50
                        display_entry(entry, show_html=True)
                else:
                    st.info("No results found.")
        
        st.markdown("---")
        
        # Table of Contents
        display_table_of_contents(all_entries)
    
    with tab2:
        # Search Tab
        st.header("🔍 Search")
        
        search_query = st.text_input(
            "Enter search query:",
            placeholder="e.g., climate change",
            key="search_input"
        )
        
        if search_query:
            search_type = st.session_state.get('search_type', 'auto')
            search_target = st.session_state.get('search_target', 'all_fields')
            
            # Convert search_target
            target_map = {
                'all_fields': 'all',
                'term_only': 'term',
                'definition_only': 'definition',
                'description_only': 'description'
            }
            target = target_map.get(search_target, 'all')
            
            if search_type in ['auto', 'exact', 'stemmed', 'fuzzy']:
                # Use search engine
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
                # Use simple filtering
                filtered = search_entries_by_target(
                    all_entries,
                    search_query,
                    target,
                    search_type
                )
                
                if filtered:
                    st.subheader(f"Found {len(filtered)} results")
                    for entry in filtered[:50]:
                        display_entry(entry, show_html=True)
                else:
                    st.info("No results found.")
        else:
            st.info("Enter a search query above to find entries.")
    
    with tab3:
        # Browse All Tab
        st.subheader("Browse All Entries")
        
        if all_entries:
            st.write(f"Showing {len(all_entries)} entries")
            
            # Pagination
            entries_per_page = st.selectbox(
                "Entries per page:",
                [10, 20, 50, 100],
                index=1,
                key="browse_per_page"
            )
            
            total_pages = (len(all_entries) + entries_per_page - 1) // entries_per_page
            
            if total_pages > 1:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    page = st.number_input(
                        "Page",
                        min_value=1,
                        max_value=total_pages,
                        value=1,
                        step=1,
                        key="browse_page"
                    )
                start_idx = (page - 1) * entries_per_page
                end_idx = start_idx + entries_per_page
                page_entries = all_entries[start_idx:end_idx]
                
                st.caption(f"Showing entries {start_idx + 1}-{min(end_idx, len(all_entries))} of {len(all_entries)}")
            else:
                page_entries = all_entries
            
            for entry in page_entries:
                display_entry(entry, show_html=True)
        else:
            st.info("No entries found in encyclopedia.")


if __name__ == "__main__":
    main()
