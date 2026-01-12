"""
Search engine for encyclopedia entries.

Provides search functionality including exact, stemmed, and fuzzy matching.
"""

from pathlib import Path
from typing import List, Optional

# Check for required dependencies
try:
    from whoosh import index
    from whoosh.qparser import QueryParser, MultifieldParser
    from whoosh.query import FuzzyTerm
    WHOOSH_AVAILABLE = True
except ImportError:
    WHOOSH_AVAILABLE = False
    raise ImportError(
        "whoosh is required but not installed. "
        "Install with: pip install whoosh"
    )

# Check for optional dependencies
try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    # Provide helpful error message
    import warnings
    warnings.warn(
        "rapidfuzz not installed. Fuzzy search will be disabled. "
        "Install with: pip install rapidfuzz",
        ImportWarning
    )

from encyclopedia.browser.indexer import EncyclopediaIndexer
from encyclopedia.browser.models import EncyclopediaEntry, SearchResult


class EncyclopediaSearchEngine:
    """Search engine for encyclopedia entries."""
    
    def __init__(self, index_dir: Optional[Path] = None):
        """Initialize search engine.
        
        Args:
            index_dir: Directory containing search indexes
        """
        self.indexer = EncyclopediaIndexer(index_dir)
        self._index = None
        self._entries_cache = {}
    
    def load_encyclopedia(self, html_file: Path, index_name: str = "encyclopedia"):
        """Load encyclopedia and build search index.
        
        Args:
            html_file: Path to encyclopedia HTML file
            index_name: Name for the index
        """
        print(f"Loading encyclopedia from {html_file}...")
        index_path = self.indexer.build_index_from_html_file(html_file, index_name)
        self._index = self.indexer.get_index(index_name)
        print(f"Index built successfully at {index_path}")
    
    def search(self, query: str, search_type: str = "auto", 
               limit: int = 20, threshold: int = 80) -> List[SearchResult]:
        """Search encyclopedia entries.
        
        Args:
            query: Search query string
            search_type: "exact", "stemmed", "fuzzy", or "auto"
            limit: Maximum number of results to return
            threshold: Minimum similarity score for fuzzy search (0-100)
            
        Returns:
            List of SearchResult objects
        """
        if not query or not query.strip():
            return []
        
        query = query.strip()
        
        if self._index is None:
            raise ValueError("No index loaded. Call load_encyclopedia() first.")
        
        if search_type == "auto":
            # Try exact first, then stemmed, then fuzzy (if available)
            results = self._exact_search(query, limit)
            if results:
                return results
            
            results = self._stemmed_search(query, limit)
            if results:
                return results
            
            if RAPIDFUZZ_AVAILABLE:
                return self._fuzzy_search(query, limit, threshold)
            else:
                return []  # No fuzzy search available
        
        elif search_type == "exact":
            return self._exact_search(query, limit)
        elif search_type == "stemmed":
            return self._stemmed_search(query, limit)
        elif search_type == "fuzzy":
            if not RAPIDFUZZ_AVAILABLE:
                raise ImportError(
                    "Fuzzy search requires rapidfuzz. Install with: pip install rapidfuzz"
                )
            return self._fuzzy_search(query, limit, threshold)
        else:
            raise ValueError(f"Unknown search type: {search_type}")
    
    def _exact_search(self, query: str, limit: int) -> List[SearchResult]:
        """Perform exact term matching search.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of SearchResult objects
        """
        results = []
        
        # Search in term field (exact match)
        with self._index.searcher() as searcher:
            query_parser = QueryParser("term", self._index.schema)
            parsed_query = query_parser.parse(query)
            
            hits = searcher.search(parsed_query, limit=limit)
            
            for hit in hits:
                entry = self._hit_to_entry(hit)
                results.append(SearchResult(
                    entry=entry,
                    score=100.0,  # Exact match gets full score
                    match_type="exact",
                    matched_fields=["term"]
                ))
        
        return results
    
    def _stemmed_search(self, query: str, limit: int) -> List[SearchResult]:
        """Perform stemmed search (handles word variations).
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of SearchResult objects
        """
        results = []
        
        # Search across multiple fields with stemming
        with self._index.searcher() as searcher:
            query_parser = MultifieldParser(
                ["term", "search_terms", "canonical_term", "description_text"],
                self._index.schema
            )
            parsed_query = query_parser.parse(query)
            
            hits = searcher.search(parsed_query, limit=limit)
            
            for hit in hits:
                entry = self._hit_to_entry(hit)
                # Calculate score based on relevance
                score = hit.score * 10  # Convert to 0-100 scale
                results.append(SearchResult(
                    entry=entry,
                    score=min(100.0, score),
                    match_type="stemmed",
                    matched_fields=self._get_matched_fields(hit)
                ))
        
        return results
    
    def _fuzzy_search(self, query: str, limit: int, threshold: int) -> List[SearchResult]:
        """Perform fuzzy/Levenshtein distance search.
        
        Args:
            query: Search query
            limit: Maximum results
            threshold: Minimum similarity score (0-100)
            
        Returns:
            List of SearchResult objects
        """
        results = []
        
        # Get all terms from index for fuzzy matching
        all_terms = []
        term_to_entry = {}
        
        with self._index.searcher() as searcher:
            for hit in searcher.documents():
                term = hit.get("term", "")
                canonical_term = hit.get("canonical_term", "")
                search_terms = hit.get("search_terms", "")
                
                terms = [term, canonical_term, search_terms]
                for t in terms:
                    if t and t not in term_to_entry:
                        all_terms.append(t)
                        term_to_entry[t] = hit
        
        # Use RapidFuzz for fuzzy matching
        matches = process.extract(
            query,
            all_terms,
            scorer=fuzz.ratio,
            limit=limit * 2,  # Get more candidates
            score_cutoff=threshold
        )
        
        # Convert to SearchResult objects
        seen_entry_ids = set()
        for term, score, _ in matches:
            hit = term_to_entry.get(term)
            if hit:
                entry_id = hit.get("entry_id")
                if entry_id not in seen_entry_ids:
                    seen_entry_ids.add(entry_id)
                    entry = self._hit_to_entry(hit)
                    results.append(SearchResult(
                        entry=entry,
                        score=float(score),
                        match_type="fuzzy",
                        matched_fields=["term"]
                    ))
                    
                    if len(results) >= limit:
                        break
        
        return results
    
    def _hit_to_entry(self, hit) -> EncyclopediaEntry:
        """Convert Whoosh hit to EncyclopediaEntry.
        
        Args:
            hit: Whoosh search hit
            
        Returns:
            EncyclopediaEntry object
        """
        entry_id = hit.get("entry_id", "")
        
        # Check cache first
        if entry_id in self._entries_cache:
            return self._entries_cache[entry_id]
        
        # Parse synonyms
        synonyms_str = hit.get("synonyms", "")
        synonyms = [s.strip() for s in synonyms_str.split(",") if s.strip()] if synonyms_str else []
        
        entry = EncyclopediaEntry(
            entry_id=entry_id,
            term=hit.get("term", ""),
            canonical_term=hit.get("canonical_term", ""),
            search_terms=[hit.get("search_terms", "")],
            wikidata_id=hit.get("wikidata_id", ""),
            wikipedia_url=hit.get("wikipedia_url", ""),
            description_html=hit.get("description_html", ""),
            description_text=hit.get("description_text", ""),
            synonyms=synonyms,
            category=hit.get("category", ""),
            entry_index=hit.get("entry_index", 0),
        )
        
        # Cache entry
        self._entries_cache[entry_id] = entry
        
        return entry
    
    def _get_matched_fields(self, hit) -> List[str]:
        """Get list of fields that matched the query.
        
        Args:
            hit: Whoosh search hit
            
        Returns:
            List of field names that matched
        """
        # This is a simplified version - Whoosh doesn't directly tell us
        # which fields matched, so we'll return common fields
        return ["term", "description_text"]
    
    def get_entry_by_id(self, entry_id: str) -> Optional[EncyclopediaEntry]:
        """Get entry by ID.
        
        Args:
            entry_id: Entry identifier
            
        Returns:
            EncyclopediaEntry or None if not found
        """
        if self._index is None:
            return None
        
        with self._index.searcher() as searcher:
            hit = searcher.document(entry_id=entry_id)
            if hit:
                return self._hit_to_entry(hit)
        
        return None
    
    def get_all_entries(self, limit: Optional[int] = None) -> List[EncyclopediaEntry]:
        """Get all entries (for browsing).
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of EncyclopediaEntry objects
        """
        if self._index is None:
            return []
        
        entries = []
        with self._index.searcher() as searcher:
            for hit in searcher.documents():
                entry = self._hit_to_entry(hit)
                entries.append(entry)
                
                if limit and len(entries) >= limit:
                    break
        
        return entries
