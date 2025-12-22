"""
Tests for AmiEncyclopedia class.

Following TDD approach - tests written before implementation.
"""
import pytest
from lxml import etree as ET

from encyclopedia.core.encyclopedia import AmiEncyclopedia


class TestAmiEncyclopedia:
    """Test suite for AmiEncyclopedia class"""
    
    def test_encyclopedia_initialization(self):
        """Test that AmiEncyclopedia can be initialized"""
        encyclopedia = AmiEncyclopedia(title="Test Encyclopedia")
        assert encyclopedia.title == "Test Encyclopedia"
        assert encyclopedia.dictionary is None
        assert encyclopedia.entries == []
        assert encyclopedia.normalized_entries == {}
        assert encyclopedia.synonym_groups == {}
    
    def test_encyclopedia_constants(self):
        """Test that constants are defined correctly"""
        assert AmiEncyclopedia.REASON_MISSING_WIKIPEDIA == "missing_wikipedia"
        assert AmiEncyclopedia.REASON_GENERAL_TERM == "general_term"
        assert AmiEncyclopedia.REASON_FALSE_WIKIPEDIA == "false_wikipedia"
        assert AmiEncyclopedia.CATEGORY_TRUE_WIKIPEDIA == "true_wikipedia"
        assert AmiEncyclopedia.CATEGORY_NO_WIKIPEDIA == "no_wikipedia"
        assert AmiEncyclopedia.CATEGORY_DISAMBIGUATION == "disambiguation"
    
    def test_create_from_html_content_basic(self):
        """Test creating encyclopedia from basic HTML content"""
        html_content = """
        <html>
        <body>
        <div role="ami_dictionary" title="test_dict">
            <div role="ami_entry" term="test_term" name="test_term">
                <p>search term: test_term <a href="https://en.wikipedia.org/wiki/Test_term">Wikipedia Page</a></p>
                <p class="wpage_first_para">Test description</p>
            </div>
        </div>
        </body>
        </html>
        """
        encyclopedia = AmiEncyclopedia(title="Test")
        result = encyclopedia.create_from_html_content(html_content)
        
        assert result is not None
        assert isinstance(result, AmiEncyclopedia)
        assert len(encyclopedia.entries) > 0
    
    def test_normalize_by_wikidata_id(self):
        """Test normalizing entries by Wikidata ID"""
        encyclopedia = AmiEncyclopedia(title="Test")
        
        # Add test entries with Wikidata IDs
        encyclopedia.entries = [
            {"term": "term1", "wikidata_id": "Q123"},
            {"term": "term2", "wikidata_id": "Q123"},  # Same Wikidata ID
            {"term": "term3", "wikidata_id": "Q456"},
            {"term": "term4", "wikidata_id": ""},  # No Wikidata ID
        ]
        
        normalized = encyclopedia.normalize_by_wikidata_id()
        
        assert isinstance(normalized, dict)
        assert "Q123" in normalized
        assert "Q456" in normalized
        assert "no_wikidata_id" in normalized
        assert len(normalized["Q123"]) == 2  # Two entries with Q123
    
    def test_merge_synonyms(self):
        """Test merging synonyms using merge() method"""
        encyclopedia = AmiEncyclopedia(title="Test")
        
        # Set up entries with same Wikidata ID
        encyclopedia.entries = [
            {"term": "term1", "wikidata_id": "Q123", "wikipedia_url": "https://en.wikipedia.org/wiki/Term1"},
            {"term": "term2", "wikidata_id": "Q123", "wikipedia_url": "https://en.wikipedia.org/wiki/Term2"},
            {"term": "term3", "wikidata_id": "Q456"},
        ]
        
        # Normalize first
        encyclopedia.normalize_by_wikidata_id()
        
        # Then merge
        merged = encyclopedia.merge()
        
        assert isinstance(merged, AmiEncyclopedia)
        assert len(encyclopedia.synonym_groups) > 0
    
    def test_get_valid_checkbox_reasons(self):
        """Test getting valid checkbox reasons"""
        reasons = AmiEncyclopedia.get_valid_checkbox_reasons()
        
        assert isinstance(reasons, list)
        assert AmiEncyclopedia.REASON_MISSING_WIKIPEDIA in reasons
        assert AmiEncyclopedia.REASON_GENERAL_TERM in reasons
        assert AmiEncyclopedia.REASON_FALSE_WIKIPEDIA in reasons


class TestAmiEncyclopediaHTML:
    """Test suite for HTML generation"""
    
    def test_create_wiki_normalized_html_basic(self):
        """Test generating HTML from encyclopedia"""
        encyclopedia = AmiEncyclopedia(title="Test Encyclopedia")
        encyclopedia.entries = [
            {
                "term": "test_term",
                "wikidata_id": "Q123",
                "wikipedia_url": "https://en.wikipedia.org/wiki/Test_term",
                "description_html": "<p>Test description</p>",
            }
        ]
        
        # Normalize and merge first
        encyclopedia.normalize_by_wikidata_id()
        encyclopedia.merge()
        
        html = encyclopedia.create_wiki_normalized_html()
        
        assert html is not None
        # Should return HTML string
        assert isinstance(html, str)
        assert "ami_encyclopedia" in html or "ami_entry" in html
    
    def test_create_wiki_normalized_html_with_synonyms(self):
        """Test generating HTML with synonym groups"""
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [
            {"term": "term1", "wikidata_id": "Q123", "wikipedia_url": "https://en.wikipedia.org/wiki/Term1"},
            {"term": "term2", "wikidata_id": "Q123", "wikipedia_url": "https://en.wikipedia.org/wiki/Term2"},
        ]
        
        # Normalize and merge
        encyclopedia.normalize_by_wikidata_id()
        encyclopedia.merge()
        
        html = encyclopedia.create_wiki_normalized_html()
        
        assert html is not None
        assert isinstance(html, str)

