"""
Tests for Entry Display & Navigation functionality on landing page.

Feature 3: Entry Display & Navigation

These tests will fail until landing page entry display functionality is implemented.
"""

import pytest

from encyclopedia.core.encyclopedia import AmiEncyclopedia


class TestEntryDisplay:
    """Test suite for Entry Display functionality"""
    
    # Entry Card Layout
    
    def test_entry_card_displays_term(self, small_encyclopedia: AmiEncyclopedia):
        """Verify term shown prominently as heading"""
        try:
            from encyclopedia.browser.landing_page import render_entry_card
        except ImportError:
            pytest.skip("landing_page entry display module not yet implemented")
        
        entry = small_encyclopedia.entries[0]
        card = render_entry_card(entry)
        
        assert card is not None, "Entry card should be rendered"
        card_html = str(card) if not isinstance(card, str) else card
        assert entry['term'].lower() in card_html.lower(), \
            f"Card should display term '{entry['term']}'"
    
    def test_entry_card_displays_metadata(self, small_encyclopedia: AmiEncyclopedia):
        """Verify Wikidata ID displayed with link"""
        try:
            from encyclopedia.browser.landing_page import render_entry_card
        except ImportError:
            pytest.skip("landing_page entry display module not yet implemented")
        
        # Find entry with Wikidata ID
        entry_with_wikidata = None
        for entry in small_encyclopedia.entries:
            if entry.get('wikidata_id') and entry.get('wikidata_id') not in ('', 'no_wikidata_id'):
                entry_with_wikidata = entry
                break
        
        if entry_with_wikidata:
            card = render_entry_card(entry_with_wikidata)
            card_html = str(card) if not isinstance(card, str) else card
            assert entry_with_wikidata['wikidata_id'] in card_html, \
                f"Should display Wikidata ID: {entry_with_wikidata['wikidata_id']}"
            assert 'wikidata' in card_html.lower() or 'q' in card_html.lower(), \
                "Should include Wikidata reference"
    
    def test_entry_card_displays_description(self, small_encyclopedia: AmiEncyclopedia):
        """Verify description HTML rendered correctly"""
        try:
            from encyclopedia.browser.landing_page import render_entry_card
        except ImportError:
            pytest.skip("landing_page entry display module not yet implemented")
        
        # Find entry with description
        entry_with_desc = None
        for entry in small_encyclopedia.entries:
            if entry.get('description_html'):
                entry_with_desc = entry
                break
        
        if entry_with_desc:
            card = render_entry_card(entry_with_desc)
            card_html = str(card) if not isinstance(card, str) else card
            # Description should be in the card (at least partially)
            desc_text = entry_with_desc['description_html'][:50]
            assert desc_text.lower().replace('<', '').replace('>', '') in card_html.lower().replace('<', '').replace('>', ''), \
                "Should display description HTML"
    
    def test_entry_card_displays_image(self, small_encyclopedia: AmiEncyclopedia):
        """Verify image thumbnail displayed if available"""
        try:
            from encyclopedia.browser.landing_page import render_entry_card
        except ImportError:
            pytest.skip("landing_page entry display module not yet implemented")
        
        # Find entry with image
        entry_with_image = None
        for entry in small_encyclopedia.entries:
            if entry.get('figure_html') is not None or entry.get('image_link'):
                entry_with_image = entry
                break
        
        if entry_with_image:
            card = render_entry_card(entry_with_image)
            card_html = str(card) if not isinstance(card, str) else card
            assert 'img' in card_html.lower() or 'image' in card_html.lower() or \
                   entry_with_image.get('image_link', '') in card_html, \
                "Should display image thumbnail"
    
    def test_entry_card_displays_synonyms(self, small_encyclopedia: AmiEncyclopedia):
        """Verify synonyms list displayed"""
        try:
            from encyclopedia.browser.landing_page import render_entry_card
        except ImportError:
            pytest.skip("landing_page entry display module not yet implemented")
        
        # Find entry with synonyms
        entry_with_synonyms = None
        for entry in small_encyclopedia.entries:
            if entry.get('synonyms') and len(entry['synonyms']) > 1:
                entry_with_synonyms = entry
                break
        
        if entry_with_synonyms:
            card = render_entry_card(entry_with_synonyms)
            card_html = str(card) if not isinstance(card, str) else card
            # At least one synonym should be mentioned
            synonyms_found = any(
                syn.lower() in card_html.lower()
                for syn in entry_with_synonyms['synonyms']
                if syn != entry_with_synonyms['term']
            )
            assert synonyms_found or 'synonym' in card_html.lower(), \
                "Should display synonyms"
    
    def test_entry_card_missing_fields(self, small_encyclopedia: AmiEncyclopedia):
        """Verify entry without description handled gracefully"""
        try:
            from encyclopedia.browser.landing_page import render_entry_card
        except ImportError:
            pytest.skip("landing_page entry display module not yet implemented")
        
        # Find or create entry without description
        entry_without_desc = None
        for entry in small_encyclopedia.entries:
            if not entry.get('description_html'):
                entry_without_desc = entry
                break
        
        if entry_without_desc:
            card = render_entry_card(entry_without_desc)
            card_html = str(card) if not isinstance(card, str) else card
            # Card should still render even without description
            assert entry_without_desc['term'].lower() in card_html.lower(), \
                "Card should display even without description"
    
    # Entry Detail View
    
    def test_entry_detail_expandable(self, small_encyclopedia: AmiEncyclopedia):
        """Verify entry can be expanded to show full details"""
        try:
            from encyclopedia.browser.landing_page import render_entry_detail
        except ImportError:
            pytest.skip("landing_page entry display module not yet implemented")
        
        entry = small_encyclopedia.entries[0]
        detail_view = render_entry_detail(entry)
        detail_html = str(detail_view) if not isinstance(detail_view, str) else detail_view
        
        assert detail_view is not None, "Entry detail should be rendered"
        assert 'expand' in detail_html.lower() or 'more' in detail_html.lower() or \
               'collapse' in detail_html.lower(), \
            "Entry detail should be expandable"
    
    def test_entry_detail_full_description(self, small_encyclopedia: AmiEncyclopedia):
        """Verify full description shown when expanded"""
        try:
            from encyclopedia.browser.landing_page import render_entry_detail
        except ImportError:
            pytest.skip("landing_page entry display module not yet implemented")
        
        # Find entry with description
        entry_with_desc = None
        for entry in small_encyclopedia.entries:
            if entry.get('description_html'):
                entry_with_desc = entry
                break
        
        if entry_with_desc:
            detail_view = render_entry_detail(entry_with_desc, expanded=True)
            detail_html = str(detail_view) if not isinstance(detail_view, str) else detail_view
            # Full description should be visible
            desc_snippet = entry_with_desc['description_html'][:30]
            assert desc_snippet.lower().replace('<', '').replace('>', '') in \
                   detail_html.lower().replace('<', '').replace('>', ''), \
                "Should show full description when expanded"
    
    # Navigation Between Entries
    
    def test_entry_navigation_previous_next(self, small_encyclopedia: AmiEncyclopedia):
        """Verify Previous/Next buttons work"""
        try:
            from encyclopedia.browser.landing_page import create_entry_navigation
        except ImportError:
            pytest.skip("landing_page navigation module not yet implemented")
        
        if len(small_encyclopedia.entries) < 3:
            pytest.skip("Need at least 3 entries for navigation test")
        
        current_index = 1
        nav = create_entry_navigation(small_encyclopedia, current_index)
        
        next_entry = nav.get_next_entry()
        assert next_entry is not None, "Should have next entry"
        assert next_entry == small_encyclopedia.entries[current_index + 1], \
            "Should navigate to next entry"
        
        prev_entry = nav.get_previous_entry()
        assert prev_entry == small_encyclopedia.entries[current_index - 1], \
            "Should navigate to previous entry"
    
    def test_entry_deep_linking(self, small_encyclopedia: AmiEncyclopedia):
        """Verify URL fragment (#entry-id) navigates to entry"""
        try:
            from encyclopedia.browser.landing_page import get_entry_id, navigate_to_entry_id
        except ImportError:
            pytest.skip("landing_page navigation module not yet implemented")
        
        entry = small_encyclopedia.entries[0]
        entry_id = get_entry_id(entry)
        
        assert entry_id is not None, "Should generate entry ID"
        assert '#' in str(entry_id) or entry['term'].lower().replace(' ', '-') in str(entry_id).lower(), \
            f"Entry ID should be usable as URL fragment: {entry_id}"
        
        # Test navigation
        navigated_entry = navigate_to_entry_id(small_encyclopedia, entry_id)
        assert navigated_entry == entry, \
            f"Should navigate to correct entry via ID: {entry_id}"
    
    # Entry Actions
    
    def test_entry_copy_link(self, small_encyclopedia: AmiEncyclopedia):
        """Verify 'Copy Link' button works"""
        try:
            from encyclopedia.browser.landing_page import get_entry_link
        except ImportError:
            pytest.skip("landing_page entry actions module not yet implemented")
        
        entry = small_encyclopedia.entries[0]
        entry_link = get_entry_link(entry)
        
        assert entry_link is not None, "Should generate entry link"
        assert entry['term'].lower().replace(' ', '-') in entry_link.lower() or \
               '#' in entry_link, \
            f"Link should include entry reference: {entry_link}"
    
    def test_entry_export_json(self, small_encyclopedia: AmiEncyclopedia):
        """Verify 'Export as JSON' works"""
        try:
            from encyclopedia.browser.landing_page import export_entry_as_json
        except ImportError:
            pytest.skip("landing_page entry actions module not yet implemented")
        
        import json
        entry = small_encyclopedia.entries[0]
        json_data = export_entry_as_json(entry)
        
        assert json_data is not None, "Should export entry as JSON"
        # Should be valid JSON
        json_str = json.dumps(json_data) if not isinstance(json_data, str) else json_data
        parsed = json.loads(json_str)
        assert parsed.get('term') == entry['term'], \
            "JSON should contain term"
