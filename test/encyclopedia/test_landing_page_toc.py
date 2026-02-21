"""
Tests for Table of Contents (TOC) functionality on landing page.

Feature 1: Table of Contents

These tests will fail until landing page functionality is implemented.
"""

import pytest
import time
from collections import defaultdict

from encyclopedia.core.encyclopedia import AmiEncyclopedia


def _get_entry_count_by_letter(encyclopedia: AmiEncyclopedia) -> dict:
    """Helper: Count entries by first letter."""
    counts = defaultdict(int)
    for entry in encyclopedia.entries:
        if entry.get('term'):
            first_letter = entry['term'][0].upper()
            if first_letter.isalpha():
                counts[first_letter] += 1
            else:
                counts['0-9'] = counts.get('0-9', 0) + 1
    return counts


class TestTableOfContents:
    """Test suite for Table of Contents functionality"""
    
    def test_toc_generates_alphabetical_sections(self, small_encyclopedia: AmiEncyclopedia):
        """Verify TOC has sections for each letter (A-Z)"""
        # This will fail until landing_page module is implemented
        try:
            from encyclopedia.browser.landing_page import generate_toc
        except ImportError:
            pytest.skip("landing_page module not yet implemented")
        
        toc_sections = generate_toc(small_encyclopedia)
        assert toc_sections is not None, "TOC generation should return a result"
        
        # Check that we have sections for letters that exist
        letter_counts = _get_entry_count_by_letter(small_encyclopedia)
        for letter in letter_counts.keys():
            if letter != '0-9':
                assert letter in toc_sections, \
                    f"TOC should have section for letter {letter} which has {letter_counts[letter]} entries"
    
    def test_toc_shows_entry_counts_per_letter(self, small_encyclopedia: AmiEncyclopedia):
        """Verify each letter section shows correct count"""
        try:
            from encyclopedia.browser.landing_page import generate_toc
        except ImportError:
            pytest.skip("landing_page module not yet implemented")
        
        toc_sections = generate_toc(small_encyclopedia)
        letter_counts = _get_entry_count_by_letter(small_encyclopedia)
        
        for letter, expected_count in letter_counts.items():
            if letter != '0-9':
                assert letter in toc_sections, \
                    f"TOC should have section for letter {letter}"
                toc_count = toc_sections[letter].get('count', 0)
                assert toc_count == expected_count, \
                    f"Expected {expected_count} entries for letter {letter}, got {toc_count}"
    
    def test_toc_quick_jump_navigation(self, small_encyclopedia: AmiEncyclopedia):
        """Verify A-Z quick jump links work"""
        try:
            from encyclopedia.browser.landing_page import generate_quick_jump
        except ImportError:
            pytest.skip("landing_page module not yet implemented")
        
        quick_jump = generate_quick_jump(small_encyclopedia)
        assert quick_jump is not None, "Quick jump should be generated"
        
        # Check that letters with entries are in quick jump
        letter_counts = _get_entry_count_by_letter(small_encyclopedia)
        for letter in letter_counts.keys():
            if letter != '0-9':
                assert letter in quick_jump, \
                    f"Quick jump should include letter {letter} which has entries"
    
    def test_toc_collapsible_sections(self, small_encyclopedia: AmiEncyclopedia):
        """Verify sections can be expanded/collapsed"""
        try:
            from encyclopedia.browser.landing_page import generate_toc_html
        except ImportError:
            pytest.skip("landing_page module not yet implemented")
        
        toc_html = generate_toc_html(small_encyclopedia)
        assert toc_html is not None, "TOC HTML should be generated"
        assert 'collapse' in toc_html.lower() or 'toggle' in toc_html.lower() or 'expand' in toc_html.lower(), \
            "TOC HTML should include collapse/expand functionality"
    
    def test_toc_compact_vs_detailed_view(self, small_encyclopedia: AmiEncyclopedia):
        """Verify toggle between views works"""
        try:
            from encyclopedia.browser.landing_page import generate_toc
        except ImportError:
            pytest.skip("landing_page module not yet implemented")
        
        toc_compact = generate_toc(small_encyclopedia, view='compact')
        toc_detailed = generate_toc(small_encyclopedia, view='detailed')
        
        assert toc_compact is not None, "Compact view should be generated"
        assert toc_detailed is not None, "Detailed view should be generated"
        # They should differ in structure or content
        assert toc_compact != toc_detailed or str(toc_compact) != str(toc_detailed), \
            "Compact and detailed views should differ"
    
    def test_toc_entry_links_work(self, small_encyclopedia: AmiEncyclopedia):
        """Verify clicking entry scrolls to full entry"""
        try:
            from encyclopedia.browser.landing_page import generate_toc_html
        except ImportError:
            pytest.skip("landing_page module not yet implemented")
        
        toc_html = generate_toc_html(small_encyclopedia)
        
        # Check that entries have links/anchors
        for entry in small_encyclopedia.entries[:5]:  # Check first 5 entries
            term = entry.get('term', '')
            if term:
                # Entry should be referenced in TOC HTML
                assert term.lower() in toc_html.lower() or f"#{term.replace(' ', '-')}" in toc_html.lower(), \
                    f"Entry '{term}' should be linked in TOC HTML"
    
    def test_toc_visual_indicators(self, small_encyclopedia: AmiEncyclopedia):
        """Verify entries with images show image icon"""
        try:
            from encyclopedia.browser.landing_page import generate_toc_html
        except ImportError:
            pytest.skip("landing_page module not yet implemented")
        
        toc_html = generate_toc_html(small_encyclopedia)
        entries_with_images = [
            e for e in small_encyclopedia.entries
            if e.get('figure_html') is not None or e.get('image_link')
        ]
        
        if entries_with_images:
            # TOC should indicate entries with images
            for entry in entries_with_images[:3]:  # Check first 3 entries with images
                term = entry.get('term', '')
                if term:
                    # Should have some visual indicator (icon, emoji, class, etc.)
                    assert 'image' in toc_html.lower() or '📷' in toc_html or 'img' in toc_html.lower(), \
                        f"TOC should indicate entries with images (checked entry: {term})"
    
    def test_toc_handles_special_characters(self, small_encyclopedia: AmiEncyclopedia):
        """Verify entries starting with numbers (0-9) grouped correctly"""
        try:
            from encyclopedia.browser.landing_page import generate_toc
        except ImportError:
            pytest.skip("landing_page module not yet implemented")
        
        # Add a test entry starting with a number
        test_entry = {
            'term': '2D graphics',
            'canonical_term': '2D graphics',
            'wikidata_id': '',
            'wikipedia_url': '',
            'description_html': None,
            'definition_html': None,
            'synonyms': []
        }
        small_encyclopedia.entries.append(test_entry)
        
        toc_sections = generate_toc(small_encyclopedia)
        assert '0-9' in toc_sections or '#' in toc_sections, \
            "Should have section for entries starting with numbers"
    
    def test_toc_performance_large_encyclopedia(self, large_encyclopedia: AmiEncyclopedia):
        """Verify TOC generation completes in reasonable time"""
        try:
            from encyclopedia.browser.landing_page import generate_toc
        except ImportError:
            pytest.skip("landing_page module not yet implemented")
        
        start_time = time.time()
        toc = generate_toc(large_encyclopedia)
        elapsed = time.time() - start_time
        
        assert toc is not None, "TOC should be generated"
        assert elapsed < 1.0, \
            f"TOC generation took {elapsed:.2f}s, expected <1.0s for {len(large_encyclopedia.entries)} entries"
    
    def test_toc_updates_with_filtered_entries(self, small_encyclopedia: AmiEncyclopedia):
        """Verify TOC updates when filters applied"""
        try:
            from encyclopedia.browser.landing_page import generate_toc, filter_entries
        except ImportError:
            pytest.skip("landing_page module not yet implemented")
        
        # Filter entries with images
        filtered_entries = [
            e for e in small_encyclopedia.entries
            if e.get('figure_html') is not None or e.get('image_link')
        ]
        
        # Create filtered encyclopedia
        filtered_encyclopedia = AmiEncyclopedia(title=small_encyclopedia.title)
        filtered_encyclopedia.entries = filtered_entries
        
        toc = generate_toc(filtered_encyclopedia)
        assert toc is not None, "TOC should be generated for filtered entries"
        
        # Count entries in TOC
        total_in_toc = sum(
            section.get('count', len(section.get('entries', [])))
            for section in toc.values()
            if isinstance(section, dict)
        )
        assert total_in_toc == len(filtered_entries), \
            f"TOC should show {len(filtered_entries)} filtered entries, got {total_in_toc}"
