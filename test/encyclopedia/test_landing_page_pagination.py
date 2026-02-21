"""
Tests for Pagination & Browsing functionality on landing page.

Feature 5: Pagination & Browsing

These tests will fail until landing page pagination functionality is implemented.
"""

import pytest
import time

from encyclopedia.core.encyclopedia import AmiEncyclopedia


def _calculate_total_pages(total_entries: int, entries_per_page: int) -> int:
    """Helper: Calculate total pages."""
    if total_entries == 0:
        return 1
    return (total_entries + entries_per_page - 1) // entries_per_page


class TestPaginationBrowsing:
    """Test suite for Pagination & Browsing functionality"""
    
    # Pagination Controls
    
    def test_pagination_displays_correct_page(self, small_encyclopedia: AmiEncyclopedia):
        """Verify first page shows entries 1-20 (if 20 per page)"""
        try:
            from encyclopedia.browser.landing_page import create_pagination
        except ImportError:
            pytest.skip("landing_page pagination module not yet implemented")
        
        pagination = create_pagination(small_encyclopedia, entries_per_page=20)
        assert pagination is not None, "Pagination should be created"
        
        page_1_entries = pagination.get_page(1)
        assert len(page_1_entries) <= 20, \
            f"Page 1 should have at most 20 entries, got {len(page_1_entries)}"
        assert pagination.get_current_page() == 1, \
            f"Should start on page 1, got page {pagination.get_current_page()}"
    
    def test_pagination_next_previous_buttons(self, small_encyclopedia: AmiEncyclopedia):
        """Verify Next button advances to next page"""
        try:
            from encyclopedia.browser.landing_page import create_pagination
        except ImportError:
            pytest.skip("landing_page pagination module not yet implemented")
        
        if len(small_encyclopedia.entries) < 6:
            pytest.skip("Need at least 6 entries for pagination test")
        
        pagination = create_pagination(small_encyclopedia, entries_per_page=5)
        initial_page = pagination.get_current_page()
        
        pagination.click_next()
        assert pagination.get_current_page() == initial_page + 1, \
            "Should advance to next page"
        
        pagination.click_previous()
        assert pagination.get_current_page() == initial_page, \
            "Should return to previous page"
    
    def test_pagination_first_last_buttons(self, small_encyclopedia: AmiEncyclopedia):
        """Verify First button jumps to page 1"""
        try:
            from encyclopedia.browser.landing_page import create_pagination
        except ImportError:
            pytest.skip("landing_page pagination module not yet implemented")
        
        if len(small_encyclopedia.entries) < 11:
            pytest.skip("Need at least 11 entries for first/last test")
        
        pagination = create_pagination(small_encyclopedia, entries_per_page=5)
        pagination.go_to_page(3)
        pagination.click_first()
        assert pagination.get_current_page() == 1, "Should jump to first page"
        
        pagination.click_last()
        expected_last_page = _calculate_total_pages(
            len(small_encyclopedia.entries), 5
        )
        assert pagination.get_current_page() == expected_last_page, \
            f"Should jump to last page ({expected_last_page})"
    
    def test_pagination_page_numbers(self, medium_encyclopedia: AmiEncyclopedia):
        """Verify page numbers displayed (1, 2, 3, ...)"""
        try:
            from encyclopedia.browser.landing_page import create_pagination
        except ImportError:
            pytest.skip("landing_page pagination module not yet implemented")
        
        pagination = create_pagination(medium_encyclopedia, entries_per_page=10)
        page_numbers = pagination.get_page_numbers()
        
        assert len(page_numbers) > 0, "Should display page numbers"
        assert 1 in page_numbers, "Should include page 1"
        assert pagination.get_total_pages() in page_numbers, \
            "Should include last page number"
    
    def test_pagination_entries_per_page(self, small_encyclopedia: AmiEncyclopedia):
        """Verify dropdown/selector for entries per page"""
        try:
            from encyclopedia.browser.landing_page import create_pagination
        except ImportError:
            pytest.skip("landing_page pagination module not yet implemented")
        
        pagination = create_pagination(small_encyclopedia, entries_per_page=10)
        pagination.set_entries_per_page(20)
        
        assert pagination.get_entries_per_page() == 20, \
            "Should update entries per page to 20"
        
        expected_total_pages = _calculate_total_pages(
            len(small_encyclopedia.entries), 20
        )
        assert pagination.get_total_pages() == expected_total_pages, \
            f"Should recalculate total pages to {expected_total_pages}"
    
    def test_pagination_url_parameters(self, small_encyclopedia: AmiEncyclopedia):
        """Verify page number in URL (?page=2)"""
        try:
            from encyclopedia.browser.landing_page import create_pagination
        except ImportError:
            pytest.skip("landing_page pagination module not yet implemented")
        
        pagination = create_pagination(small_encyclopedia, entries_per_page=10)
        pagination.go_to_page(2)
        
        url_params = pagination.get_url_parameters()
        assert url_params.get('page') == '2' or url_params.get('page') == 2, \
            f"URL should contain page=2, got {url_params.get('page')}"
        assert url_params.get('per_page') == '10' or url_params.get('per_page') == 10, \
            f"URL should contain per_page=10, got {url_params.get('per_page')}"
    
    # Alphabetical Browsing
    
    def test_alphabetical_browse_letter_navigation(self, small_encyclopedia: AmiEncyclopedia):
        """Verify A-Z navigation bar displayed"""
        try:
            from encyclopedia.browser.landing_page import create_alphabetical_browse
        except ImportError:
            pytest.skip("landing_page browse module not yet implemented")
        
        browse = create_alphabetical_browse(small_encyclopedia)
        assert browse.has_letter_navigation(), "Should have A-Z navigation bar"
        
        # Find a letter that has entries
        from collections import defaultdict
        letter_counts = defaultdict(int)
        for entry in small_encyclopedia.entries:
            if entry.get('term'):
                first_letter = entry['term'][0].upper()
                if first_letter.isalpha():
                    letter_counts[first_letter] += 1
        
        if letter_counts:
            test_letter = list(letter_counts.keys())[0]
            browse.click_letter(test_letter)
            entries = browse.get_entries_for_letter(test_letter)
            assert len(entries) > 0, f"Should show entries for letter {test_letter}"
            assert all(e['term'][0].upper() == test_letter for e in entries), \
                f"All entries should start with letter {test_letter}"
    
    def test_alphabetical_browse_entry_counts(self, small_encyclopedia: AmiEncyclopedia):
        """Verify entry count shown for each letter"""
        try:
            from encyclopedia.browser.landing_page import create_alphabetical_browse
        except ImportError:
            pytest.skip("landing_page browse module not yet implemented")
        
        browse = create_alphabetical_browse(small_encyclopedia)
        
        from collections import defaultdict
        expected_counts = defaultdict(int)
        for entry in small_encyclopedia.entries:
            if entry.get('term'):
                first_letter = entry['term'][0].upper()
                if first_letter.isalpha():
                    expected_counts[first_letter] += 1
        
        for letter, expected_count in expected_counts.items():
            count = browse.get_entry_count_for_letter(letter)
            assert count == expected_count, \
                f"Expected {expected_count} entries for letter {letter}, got {count}"
    
    # Pagination with Filters
    
    def test_pagination_preserves_filters(self, small_encyclopedia: AmiEncyclopedia):
        """Apply filter (e.g., 'has images')"""
        try:
            from encyclopedia.browser.landing_page import create_pagination
        except ImportError:
            pytest.skip("landing_page pagination module not yet implemented")
        
        # Filter entries with images
        filtered_entries = [
            e for e in small_encyclopedia.entries
            if e.get('figure_html') is not None or e.get('image_link')
        ]
        
        if len(filtered_entries) < 6:
            pytest.skip("Need at least 6 filtered entries for pagination test")
        
        filtered_encyclopedia = AmiEncyclopedia(title=small_encyclopedia.title)
        filtered_encyclopedia.entries = filtered_entries
        
        pagination = create_pagination(filtered_encyclopedia, entries_per_page=5)
        pagination.go_to_page(2)
        
        current_entries = pagination.get_current_entries()
        assert len(current_entries) <= 5, \
            "Should show at most 5 entries on page 2"
        assert pagination.has_active_filter('has_image'), \
            "Should preserve filter when navigating pages"
    
    def test_pagination_preserves_search(self, small_encyclopedia: AmiEncyclopedia):
        """Perform search"""
        try:
            from encyclopedia.browser.landing_page import create_pagination, search_encyclopedia
        except ImportError:
            pytest.skip("landing_page pagination module not yet implemented")
        
        search_results = search_encyclopedia(small_encyclopedia, term="climate")
        
        if len(search_results) < 6:
            pytest.skip("Need at least 6 search results for pagination test")
        
        pagination = create_pagination(search_results, entries_per_page=5)
        pagination.go_to_page(2)
        
        assert pagination.get_current_query() == "climate", \
            "Should preserve search query"
        assert len(pagination.get_current_entries()) <= 5, \
            "Should paginate search results"
    
    # Pagination Performance
    
    def test_pagination_performance_small(self, small_encyclopedia: AmiEncyclopedia):
        """Verify pagination instant for small encyclopedia"""
        try:
            from encyclopedia.browser.landing_page import create_pagination
        except ImportError:
            pytest.skip("landing_page pagination module not yet implemented")
        
        start_time = time.time()
        pagination = create_pagination(small_encyclopedia, entries_per_page=10)
        pagination.go_to_page(2)
        elapsed = time.time() - start_time
        
        assert pagination is not None, "Pagination should be created"
        assert elapsed < 0.1, \
            f"Pagination should be instant, took {elapsed:.3f}s"
    
    def test_pagination_performance_medium(self, medium_encyclopedia: AmiEncyclopedia):
        """Verify pagination fast for medium encyclopedia"""
        try:
            from encyclopedia.browser.landing_page import create_pagination
        except ImportError:
            pytest.skip("landing_page pagination module not yet implemented")
        
        start_time = time.time()
        pagination = create_pagination(medium_encyclopedia, entries_per_page=20)
        pagination.go_to_page(3)
        elapsed = time.time() - start_time
        
        assert pagination is not None, "Pagination should be created"
        assert elapsed < 0.1, \
            f"Pagination should be fast, took {elapsed:.3f}s"
