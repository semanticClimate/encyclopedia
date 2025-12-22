"""
Integration tests for encyclopedia pipeline.

Tests the full workflow from terms to encyclopedia.
"""
import pytest

from encyclopedia.core.encyclopedia import AmiEncyclopedia


class TestEncyclopediaIntegration:
    """Integration tests for full encyclopedia workflow"""
    
    def test_full_pipeline_from_html(self):
        """Test full pipeline: HTML dictionary -> Encyclopedia -> Normalize -> Merge -> HTML"""
        # Create sample HTML dictionary
        html_content = """
        <html>
        <head><base href="https://en.wikipedia.org/wiki/"></head>
        <body>
        <div role="ami_dictionary" title="test_dict">
            <div role="ami_entry" term="climate change" name="climate change">
                <p>search term: climate change <a href="https://en.wikipedia.org/wiki/Climate_change">Wikipedia Page</a></p>
                <p class="wpage_first_para">Climate change refers to long-term shifts in temperatures and weather patterns.</p>
            </div>
            <div role="ami_entry" term="global warming" name="global warming">
                <p>search term: global warming <a href="https://en.wikipedia.org/wiki/Global_warming">Wikipedia Page</a></p>
                <p class="wpage_first_para">Global warming is the long-term heating of Earth's climate system.</p>
            </div>
        </div>
        </body>
        </html>
        """
        
        # Create encyclopedia
        encyclopedia = AmiEncyclopedia(title="Test Encyclopedia")
        encyclopedia.create_from_html_content(html_content)
        
        # Verify entries were created
        assert len(encyclopedia.entries) == 2
        assert encyclopedia.entries[0]['term'] in ['climate change', 'global warming']
        
        # Normalize by Wikidata ID
        normalized = encyclopedia.normalize_by_wikidata_id()
        assert isinstance(normalized, dict)
        
        # Merge synonyms
        merged = encyclopedia.merge()
        assert isinstance(merged, AmiEncyclopedia)
        
        # Generate HTML
        html_output = encyclopedia.create_wiki_normalized_html()
        assert isinstance(html_output, str)
        assert "ami_encyclopedia" in html_output or "ami_entry" in html_output
    
    def test_normalize_and_merge_with_same_wikidata_id(self):
        """Test that entries with same Wikidata ID are merged"""
        html_content = """
        <html>
        <body>
        <div role="ami_dictionary" title="test">
            <div role="ami_entry" term="term1" wikidataID="Q123">
                <p>search term: term1</p>
                <p class="wpage_first_para">Description 1</p>
            </div>
            <div role="ami_entry" term="term2" wikidataID="Q123">
                <p>search term: term2</p>
                <p class="wpage_first_para">Description 2</p>
            </div>
        </div>
        </body>
        </html>
        """
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.create_from_html_content(html_content)
        
        # Normalize
        normalized = encyclopedia.normalize_by_wikidata_id()
        
        # Check that both entries are grouped under Q123
        assert "Q123" in normalized
        assert len(normalized["Q123"]) == 2
        
        # Merge
        encyclopedia.merge()
        
        # Check that synonym groups were created
        assert len(encyclopedia.synonym_groups) > 0
        assert "Q123" in encyclopedia.synonym_groups

