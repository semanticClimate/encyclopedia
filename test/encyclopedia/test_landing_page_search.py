"""
Tests for Search functionality on landing page.

Feature 2: Search Functionality
Includes: term, synonym, text in definition, text in description, presence of image

These tests will fail until landing page search functionality is implemented.
"""

import pytest
import time
import re

from encyclopedia.core.encyclopedia import AmiEncyclopedia


def _extract_text_from_html(html: str) -> str:
    """Helper: Extract plain text from HTML."""
    if not html:
        return ""
    # Simple text extraction (remove HTML tags)
    text = re.sub(r'<[^>]+>', '', html)
    return text.strip()


class TestSearchFunctionality:
    """Test suite for Search functionality"""
    
    # Search Option: Term Search
    
    def test_search_by_term_exact_match(self, small_encyclopedia: AmiEncyclopedia):
        """Search for exact term"""
        try:
            from encyclopedia.browser.landing_page import search_encyclopedia
        except ImportError:
            pytest.skip("landing_page search module not yet implemented")
        
        # Find a term that exists
        test_term = small_encyclopedia.entries[0]['term'] if small_encyclopedia.entries else "climate"
        results = search_encyclopedia(small_encyclopedia, term=test_term)
        
        assert len(results) > 0, \
            f"Should find at least one result for term '{test_term}'"
        assert any(r.get('term', '').lower() == test_term.lower() for r in results), \
            f"Should find exact match for '{test_term}'"
    
    def test_search_by_term_partial_match(self, small_encyclopedia: AmiEncyclopedia):
        """Search for partial term"""
        try:
            from encyclopedia.browser.landing_page import search_encyclopedia
        except ImportError:
            pytest.skip("landing_page search module not yet implemented")
        
        # Use first few characters of a term
        if small_encyclopedia.entries:
            full_term = small_encyclopedia.entries[0]['term']
            partial_term = full_term[:4] if len(full_term) > 4 else full_term[:2]
            results = search_encyclopedia(small_encyclopedia, term=partial_term)
            
            assert len(results) > 0, \
                f"Should find partial matches for '{partial_term}'"
            terms_found = [r.get('term', '').lower() for r in results]
            assert any(partial_term.lower() in term for term in terms_found), \
                f"Should find terms containing '{partial_term}', got: {terms_found[:5]}"
    
    def test_search_by_term_multiple_words(self, small_encyclopedia: AmiEncyclopedia):
        """Search for multi-word term"""
        try:
            from encyclopedia.browser.landing_page import search_encyclopedia
        except ImportError:
            pytest.skip("landing_page search module not yet implemented")
        
        # Find a multi-word term
        multi_word_terms = [e['term'] for e in small_encyclopedia.entries if ' ' in e.get('term', '')]
        if multi_word_terms:
            test_term = multi_word_terms[0]
            results = search_encyclopedia(small_encyclopedia, term=test_term)
            
            assert len(results) > 0, f"Should find multi-word term '{test_term}'"
            assert any(r.get('term', '').lower() == test_term.lower() for r in results), \
                f"Should find exact match for multi-word term '{test_term}'"
    
    def test_search_by_term_no_results(self, small_encyclopedia: AmiEncyclopedia):
        """Search for non-existent term"""
        try:
            from encyclopedia.browser.landing_page import search_encyclopedia
        except ImportError:
            pytest.skip("landing_page search module not yet implemented")
        
        results = search_encyclopedia(small_encyclopedia, term="nonexistenttermxyz123")
        assert len(results) == 0, \
            "Should return no results for non-existent term"
    
    # Search Option: Synonym Search
    
    def test_search_by_synonym_finds_canonical(self, small_encyclopedia: AmiEncyclopedia):
        """Search for synonym term"""
        try:
            from encyclopedia.browser.landing_page import search_encyclopedia
        except ImportError:
            pytest.skip("landing_page search module not yet implemented")
        
        # Find entry with synonyms
        entry_with_synonyms = None
        for entry in small_encyclopedia.entries:
            if entry.get('synonyms') and len(entry['synonyms']) > 1:
                entry_with_synonyms = entry
                break
        
        if entry_with_synonyms:
            synonym = entry_with_synonyms['synonyms'][0]
            if synonym != entry_with_synonyms['term']:
                results = search_encyclopedia(small_encyclopedia, synonym=synonym)
                assert len(results) > 0, \
                    f"Should find entry via synonym: {synonym}"
                assert any(r.get('term') == entry_with_synonyms['term'] for r in results), \
                    f"Should find canonical term '{entry_with_synonyms['term']}' via synonym '{synonym}'"
    
    def test_search_by_synonym_case_insensitive(self, small_encyclopedia: AmiEncyclopedia):
        """Verify synonym matching is case-insensitive"""
        try:
            from encyclopedia.browser.landing_page import search_encyclopedia
        except ImportError:
            pytest.skip("landing_page search module not yet implemented")
        
        # Find entry with synonyms
        entry_with_synonyms = None
        for entry in small_encyclopedia.entries:
            if entry.get('synonyms') and len(entry['synonyms']) > 0:
                entry_with_synonyms = entry
                break
        
        if entry_with_synonyms:
            synonym = entry_with_synonyms['synonyms'][0].upper()  # Uppercase
            results = search_encyclopedia(small_encyclopedia, synonym=synonym)
            assert len(results) > 0, \
                "Should find synonyms case-insensitively"
    
    # Search Option: Text in Definition
    
    def test_search_by_definition_text(self, small_encyclopedia: AmiEncyclopedia):
        """Search for text that appears in first sentence definition"""
        try:
            from encyclopedia.browser.landing_page import search_encyclopedia
        except ImportError:
            pytest.skip("landing_page search module not yet implemented")
        
        # Find entry with definition
        entry_with_def = None
        for entry in small_encyclopedia.entries:
            if entry.get('definition_html'):
                entry_with_def = entry
                break
        
        if entry_with_def:
            def_text = _extract_text_from_html(entry_with_def['definition_html'])
            if def_text and len(def_text) > 10:
                search_text = def_text[:10].strip()
                results = search_encyclopedia(small_encyclopedia, definition_contains=search_text)
                assert len(results) > 0, \
                    f"Should find entry via definition text: '{search_text}'"
    
    def test_search_by_definition_partial_text(self, small_encyclopedia: AmiEncyclopedia):
        """Search for partial phrase from definition"""
        try:
            from encyclopedia.browser.landing_page import search_encyclopedia
        except ImportError:
            pytest.skip("landing_page search module not yet implemented")
        
        # Search for common word that might appear in definitions
        results = search_encyclopedia(small_encyclopedia, definition_contains="is")
        entries_with_defs = [e for e in small_encyclopedia.entries if e.get('definition_html')]
        if entries_with_defs:
            assert len(results) > 0, \
                "Should find entries with 'is' in definition"
    
    # Search Option: Text in Description
    
    def test_search_by_description_text(self, small_encyclopedia: AmiEncyclopedia):
        """Search for text that appears in description paragraph"""
        try:
            from encyclopedia.browser.landing_page import search_encyclopedia
        except ImportError:
            pytest.skip("landing_page search module not yet implemented")
        
        # Find entry with description
        entry_with_desc = None
        for entry in small_encyclopedia.entries:
            if entry.get('description_html'):
                entry_with_desc = entry
                break
        
        if entry_with_desc:
            desc_text = _extract_text_from_html(entry_with_desc['description_html'])
            if desc_text and len(desc_text) > 10:
                search_text = desc_text[:10].strip()
                results = search_encyclopedia(small_encyclopedia, description_contains=search_text)
                assert len(results) > 0, \
                    f"Should find entry via description text: '{search_text}'"
    
    def test_search_by_description_multiple_matches(self, small_encyclopedia: AmiEncyclopedia):
        """Search for common word appearing in multiple descriptions"""
        try:
            from encyclopedia.browser.landing_page import search_encyclopedia
        except ImportError:
            pytest.skip("landing_page search module not yet implemented")
        
        results = search_encyclopedia(small_encyclopedia, description_contains="the")
        entries_with_descs = [e for e in small_encyclopedia.entries if e.get('description_html')]
        if entries_with_descs:
            assert len(results) > 0, \
                "Should find multiple entries with common word in description"
    
    # Search Option: Presence of Image
    
    def test_search_by_image_presence(self, small_encyclopedia: AmiEncyclopedia):
        """Filter/search for entries with images"""
        try:
            from encyclopedia.browser.landing_page import search_encyclopedia
        except ImportError:
            pytest.skip("landing_page search module not yet implemented")
        
        results = search_encyclopedia(small_encyclopedia, has_image=True)
        entries_with_images = [
            e for e in small_encyclopedia.entries
            if e.get('figure_html') is not None or e.get('image_link')
        ]
        
        if entries_with_images:
            assert len(results) > 0, \
                f"Should find entries with images (expected {len(entries_with_images)})"
            for result in results:
                assert result.get('figure_html') is not None or result.get('image_link'), \
                    f"Result '{result.get('term')}' should have image"
    
    def test_search_by_image_absence(self, small_encyclopedia: AmiEncyclopedia):
        """Filter/search for entries without images"""
        try:
            from encyclopedia.browser.landing_page import search_encyclopedia
        except ImportError:
            pytest.skip("landing_page search module not yet implemented")
        
        results = search_encyclopedia(small_encyclopedia, has_image=False)
        entries_without_images = [
            e for e in small_encyclopedia.entries
            if e.get('figure_html') is None and not e.get('image_link')
        ]
        
        if entries_without_images:
            assert len(results) > 0, \
                f"Should find entries without images (expected {len(entries_without_images)})"
            for result in results:
                assert result.get('figure_html') is None and not result.get('image_link'), \
                    f"Result '{result.get('term')}' should not have image"
    
    def test_search_by_image_combined_with_text(self, small_encyclopedia: AmiEncyclopedia):
        """Search for term AND has image"""
        try:
            from encyclopedia.browser.landing_page import search_encyclopedia
        except ImportError:
            pytest.skip("landing_page search module not yet implemented")
        
        # Find a term that might have an image
        term_with_image = None
        for entry in small_encyclopedia.entries:
            if (entry.get('figure_html') is not None or entry.get('image_link')) and entry.get('term'):
                term_with_image = entry['term']
                break
        
        if term_with_image:
            # Use partial term to test combined search
            partial_term = term_with_image.split()[0] if ' ' in term_with_image else term_with_image[:4]
            results = search_encyclopedia(
                small_encyclopedia,
                term=partial_term,
                has_image=True
            )
            assert len(results) > 0, \
                f"Should find entries matching '{partial_term}' AND has image"
            for result in results:
                assert partial_term.lower() in result.get('term', '').lower() or \
                       any(partial_term.lower() in s.lower() for s in result.get('synonyms', [])), \
                    f"Result '{result.get('term')}' should contain '{partial_term}'"
                assert result.get('figure_html') is not None or result.get('image_link'), \
                    f"Result '{result.get('term')}' should have image"
    
    # Combined Search Options
    
    def test_search_multiple_options_and(self, small_encyclopedia: AmiEncyclopedia):
        """Search: term AND has_image"""
        try:
            from encyclopedia.browser.landing_page import search_encyclopedia
        except ImportError:
            pytest.skip("landing_page search module not yet implemented")
        
        test_term = small_encyclopedia.entries[0]['term'] if small_encyclopedia.entries else "climate"
        results = search_encyclopedia(
            small_encyclopedia,
            term=test_term,
            has_image=True,
            logic="AND"
        )
        assert results is not None, "Search should return results (possibly empty)"
        for result in results:
            assert test_term.lower() in result.get('term', '').lower(), \
                f"Result should match term '{test_term}'"
            assert result.get('figure_html') is not None or result.get('image_link'), \
                f"Result should have image"
    
    # Search Performance
    
    def test_search_performance_small_encyclopedia(self, small_encyclopedia: AmiEncyclopedia):
        """Verify search completes in <100ms for small encyclopedia"""
        try:
            from encyclopedia.browser.landing_page import search_encyclopedia
        except ImportError:
            pytest.skip("landing_page search module not yet implemented")
        
        start_time = time.time()
        results = search_encyclopedia(small_encyclopedia, term="climate")
        elapsed = time.time() - start_time
        
        assert results is not None, "Search should return results"
        assert elapsed < 0.1, \
            f"Search took {elapsed:.3f}s, expected <0.1s for {len(small_encyclopedia.entries)} entries"
    
    def test_search_performance_medium_encyclopedia(self, medium_encyclopedia: AmiEncyclopedia):
        """Verify search completes in <500ms for medium encyclopedia"""
        try:
            from encyclopedia.browser.landing_page import search_encyclopedia
        except ImportError:
            pytest.skip("landing_page search module not yet implemented")
        
        start_time = time.time()
        results = search_encyclopedia(medium_encyclopedia, term="climate")
        elapsed = time.time() - start_time
        
        assert results is not None, "Search should return results"
        assert elapsed < 0.5, \
            f"Search took {elapsed:.3f}s, expected <0.5s for {len(medium_encyclopedia.entries)} entries"
