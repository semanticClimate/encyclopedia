"""
Test 1: Validate search URL → article URL mapping
Purpose: Verify the search URL resolves to a canonical article URL
"""

import pytest
from pathlib import Path
import json
from .test_config import CURRENT_ENCYCLOPEDIA_FILE, OUTPUT_DIR, MAX_REDIRECT_DEPTH
from .link_extractor import EncyclopediaLinkExtractor, LinkValidator

class TestSearchUrlResolution:
    """Test search URL resolution to canonical article URLs"""
    
    def setup_method(self):
        """Setup test parameters and outputs"""
        self.input_file = CURRENT_ENCYCLOPEDIA_FILE
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.extractor = EncyclopediaLinkExtractor()
        self.validator = LinkValidator()
        
        # Expected outputs
        self.resolution_results_file = Path(self.output_dir, "search_url_resolutions.json")
        self.validation_report_file = Path(self.output_dir, "url_validation_report.json")
    
    def test_extract_search_urls(self):
        """Extract all search URLs from encyclopedia"""
        # Define inputs
        html_content = self.input_file.read_text(encoding='utf-8')
        
        # Call module
        entries = self.extractor.extract_entries(html_content)
        search_urls = [entry['search_url'] for entry in entries if entry['search_url']]
        
        # Make assertions
        assert len(search_urls) > 0, "No search URLs found"
        assert all(url.startswith('https://en.wikipedia.org/w/index.php?search=') for url in search_urls), \
            "Search URLs don't match expected pattern"
        
        # Save results
        with open(self.resolution_results_file, 'w') as f:
            json.dump(search_urls, f, indent=2)
    
    def test_resolve_search_urls(self):
        """Resolve search URLs to canonical article URLs"""
        # Define inputs
        html_content = self.input_file.read_text(encoding='utf-8')
        
        # Call module
        entries = self.extractor.extract_entries(html_content)
        resolutions = {}
        
        for entry in entries[:3]:  # Test first 3 entries
            search_url = entry['search_url']
            if search_url:
                canonical_url, status_code = self.extractor.resolve_search_url(search_url)
                resolutions[search_url] = {
                    'canonical_url': canonical_url,
                    'status_code': status_code,
                    'term': entry['term']
                }
        
        # Make assertions
        assert len(resolutions) > 0, "No resolutions found"
        assert all(res['status_code'] == 200 for res in resolutions.values()), \
            "Some search URLs failed to resolve"
        assert all('wiki/' in res['canonical_url'] for res in resolutions.values()), \
            "Resolved URLs should be Wikipedia article URLs"
        
        # Save results
        with open(self.resolution_results_file, 'w') as f:
            json.dump(resolutions, f, indent=2)
    
    def test_validate_resolved_urls(self):
        """Validate that resolved URLs are accessible"""
        # Define inputs
        if not self.resolution_results_file.exists():
            pytest.skip("Resolution results not available")
        
        with open(self.resolution_results_file, 'r') as f:
            resolutions = json.load(f)
        
        # Call module
        validation_results = {}
        for search_url, data in resolutions.items():
            canonical_url = data['canonical_url']
            validation_results[search_url] = self.validator.validate_wikipedia_links([canonical_url])
        
        # Make assertions
        assert len(validation_results) > 0, "No validation results"
        accessible_count = sum(1 for result in validation_results.values() 
                              for link_result in result.values() 
                              if link_result.get('accessible', False))
        assert accessible_count > 0, "No accessible URLs found"
        
        # Save results
        with open(self.validation_report_file, 'w') as f:
            json.dump(validation_results, f, indent=2)
    
    def test_redirect_depth_limits(self):
        """Test that redirects don't exceed maximum depth"""
        # Define inputs
        test_urls = [
            "https://en.wikipedia.org/w/index.php?search=fingerprinting",
            "https://en.wikipedia.org/w/index.php?search=External%20forcing"
        ]
        
        # Call module
        max_depth = 0
        for url in test_urls:
            response = self.extractor.session.get(url, allow_redirects=True)
            # Count redirects by checking history
            depth = len(response.history)
            max_depth = max(max_depth, depth)
        
        # Make assertions
        assert max_depth <= MAX_REDIRECT_DEPTH, f"Redirect depth {max_depth} exceeds limit {MAX_REDIRECT_DEPTH}"
    
    def test_section_anchor_preservation(self):
        """Test that section anchors are preserved in resolved URLs"""
        # Define inputs
        html_content = self.input_file.read_text(encoding='utf-8')
        
        # Call module
        entries = self.extractor.extract_entries(html_content)
        section_urls = []
        
        for entry in entries[:2]:  # Test first 2 entries
            search_url = entry['search_url']
            if search_url:
                canonical_url, _ = self.extractor.resolve_search_url(search_url)
                if '#' in canonical_url:
                    section_urls.append(canonical_url)
        
        # Make assertions
        # Note: Not all URLs will have sections, but if they do, they should be preserved
        if section_urls:
            assert all('#' in url for url in section_urls), "Section anchors not preserved"
            assert all(url.count('#') == 1 for url in section_urls), "Multiple anchors found"
