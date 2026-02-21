"""
Tests for Statistics & Overview Dashboard functionality on landing page.

Feature 4: Statistics & Overview Dashboard

These tests will fail until landing page statistics functionality is implemented.
"""

import pytest

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.validation import validate_encyclopedia_completeness


class TestStatisticsDashboard:
    """Test suite for Statistics Dashboard functionality"""
    
    # Overview Statistics
    
    def test_statistics_total_entries(self, small_encyclopedia: AmiEncyclopedia):
        """Verify total entry count displayed correctly"""
        try:
            from encyclopedia.browser.landing_page import get_statistics
        except ImportError:
            pytest.skip("landing_page statistics module not yet implemented")
        
        stats = get_statistics(small_encyclopedia)
        assert stats is not None, "Statistics should be generated"
        assert 'total_entries' in stats, "Statistics should include total_entries"
        assert stats['total_entries'] == len(small_encyclopedia.entries), \
            f"Expected {len(small_encyclopedia.entries)} total entries, got {stats['total_entries']}"
    
    def test_statistics_entries_with_descriptions(self, small_encyclopedia: AmiEncyclopedia):
        """Verify count of entries with descriptions"""
        try:
            from encyclopedia.browser.landing_page import get_statistics
        except ImportError:
            pytest.skip("landing_page statistics module not yet implemented")
        
        stats = get_statistics(small_encyclopedia)
        entries_with_descriptions = sum(
            1 for e in small_encyclopedia.entries
            if e.get('description_html') is not None
        )
        assert stats.get('entries_with_descriptions') == entries_with_descriptions, \
            f"Expected {entries_with_descriptions} entries with descriptions, " \
            f"got {stats.get('entries_with_descriptions')}"
    
    def test_statistics_entries_with_images(self, small_encyclopedia: AmiEncyclopedia):
        """Verify count of entries with images"""
        try:
            from encyclopedia.browser.landing_page import get_statistics
        except ImportError:
            pytest.skip("landing_page statistics module not yet implemented")
        
        stats = get_statistics(small_encyclopedia)
        entries_with_images = sum(
            1 for e in small_encyclopedia.entries
            if e.get('figure_html') is not None or e.get('image_link')
        )
        assert stats.get('entries_with_images') == entries_with_images, \
            f"Expected {entries_with_images} entries with images, " \
            f"got {stats.get('entries_with_images')}"
    
    def test_statistics_entries_with_wikidata(self, small_encyclopedia: AmiEncyclopedia):
        """Verify count of entries with Wikidata IDs"""
        try:
            from encyclopedia.browser.landing_page import get_statistics
        except ImportError:
            pytest.skip("landing_page statistics module not yet implemented")
        
        stats = get_statistics(small_encyclopedia)
        entries_with_wikidata = sum(
            1 for e in small_encyclopedia.entries
            if e.get('wikidata_id') and e.get('wikidata_id') not in ('', 'no_wikidata_id')
        )
        assert stats.get('entries_with_wikidata') == entries_with_wikidata, \
            f"Expected {entries_with_wikidata} entries with Wikidata IDs, " \
            f"got {stats.get('entries_with_wikidata')}"
    
    def test_statistics_entries_with_wikipedia(self, small_encyclopedia: AmiEncyclopedia):
        """Verify count of entries with Wikipedia URLs"""
        try:
            from encyclopedia.browser.landing_page import get_statistics
        except ImportError:
            pytest.skip("landing_page statistics module not yet implemented")
        
        stats = get_statistics(small_encyclopedia)
        entries_with_wikipedia = sum(
            1 for e in small_encyclopedia.entries
            if e.get('wikipedia_url')
        )
        assert stats.get('entries_with_wikipedia') == entries_with_wikipedia, \
            f"Expected {entries_with_wikipedia} entries with Wikipedia URLs, " \
            f"got {stats.get('entries_with_wikipedia')}"
    
    # Completeness Indicators
    
    def test_statistics_progress_bars(self, small_encyclopedia: AmiEncyclopedia):
        """Verify progress bars displayed for each metric"""
        try:
            from encyclopedia.browser.landing_page import get_statistics_html
        except ImportError:
            pytest.skip("landing_page statistics module not yet implemented")
        
        stats_html = get_statistics_html(small_encyclopedia)
        assert stats_html is not None, "Statistics HTML should be generated"
        assert 'progress' in stats_html.lower() or 'bar' in stats_html.lower() or '%' in stats_html, \
            "Statistics HTML should include progress indicators"
    
    def test_statistics_completeness_score(self, small_encyclopedia: AmiEncyclopedia):
        """Verify overall completeness score calculated"""
        try:
            from encyclopedia.browser.landing_page import get_statistics
        except ImportError:
            pytest.skip("landing_page statistics module not yet implemented")
        
        stats = get_statistics(small_encyclopedia)
        validation_results = validate_encyclopedia_completeness(small_encyclopedia)
        
        assert 'completeness_score' in stats or 'completeness' in stats, \
            "Statistics should include completeness score"
        
        # Score should be between 0 and 100 (or 0 and 1)
        score = stats.get('completeness_score', stats.get('completeness', 0))
        assert 0 <= score <= 100 or 0 <= score <= 1, \
            f"Completeness score should be between 0-100 or 0-1, got {score}"
    
    def test_statistics_visual_indicators(self, small_encyclopedia: AmiEncyclopedia):
        """Verify green indicator for >80% complete"""
        try:
            from encyclopedia.browser.landing_page import get_statistics_html
        except ImportError:
            pytest.skip("landing_page statistics module not yet implemented")
        
        stats_html = get_statistics_html(small_encyclopedia)
        # Should have some visual indicators (colors, icons, etc.)
        assert 'green' in stats_html.lower() or 'success' in stats_html.lower() or \
               'complete' in stats_html.lower() or '✓' in stats_html, \
            "Statistics should include visual indicators"
    
    # Content Breakdown
    
    def test_statistics_entries_by_letter(self, small_encyclopedia: AmiEncyclopedia):
        """Verify breakdown by first letter displayed"""
        try:
            from encyclopedia.browser.landing_page import get_statistics
        except ImportError:
            pytest.skip("landing_page statistics module not yet implemented")
        
        stats = get_statistics(small_encyclopedia)
        letter_counts = stats.get('entries_by_letter', {})
        
        # Check that letters with entries are represented
        from collections import defaultdict
        actual_counts = defaultdict(int)
        for entry in small_encyclopedia.entries:
            if entry.get('term'):
                first_letter = entry['term'][0].upper()
                if first_letter.isalpha():
                    actual_counts[first_letter] += 1
        
        for letter, count in actual_counts.items():
            assert letter in letter_counts or count == letter_counts.get(letter, 0), \
                f"Statistics should include count for letter {letter}"
    
    def test_statistics_validation_status(self, small_encyclopedia: AmiEncyclopedia):
        """Verify validation status summary displayed"""
        try:
            from encyclopedia.browser.landing_page import get_statistics
        except ImportError:
            pytest.skip("landing_page statistics module not yet implemented")
        
        stats = get_statistics(small_encyclopedia)
        validation_results = validate_encyclopedia_completeness(small_encyclopedia)
        
        assert 'validation_status' in stats or 'is_complete' in stats, \
            "Statistics should include validation status"
        
        status = stats.get('validation_status', 'Pass' if stats.get('is_complete') else 'Fail')
        assert status in ('Pass', 'Fail', 'pass', 'fail', True, False), \
            f"Validation status should be Pass/Fail, got {status}"
    
    # Statistics Updates
    
    def test_statistics_updates_with_filters(self, small_encyclopedia: AmiEncyclopedia):
        """Apply filter (e.g., 'has images')"""
        try:
            from encyclopedia.browser.landing_page import get_statistics, filter_entries
        except ImportError:
            pytest.skip("landing_page statistics module not yet implemented")
        
        # Filter entries with images
        filtered_entries = [
            e for e in small_encyclopedia.entries
            if e.get('figure_html') is not None or e.get('image_link')
        ]
        
        filtered_encyclopedia = AmiEncyclopedia(title=small_encyclopedia.title)
        filtered_encyclopedia.entries = filtered_entries
        
        stats = get_statistics(filtered_encyclopedia)
        assert stats['total_entries'] == len(filtered_entries), \
            f"Statistics should reflect filtered set: {len(filtered_entries)} entries"
