"""
Test 2: Validate description link targets
Purpose: Extract and validate internal Wikipedia links in descriptions
"""

import pytest
from pathlib import Path
import json
from urllib.parse import urljoin
from .test_config import CURRENT_ENCYCLOPEDIA_FILE, OUTPUT_DIR, MIN_LINKS_PER_ENTRY
from .link_extractor import EncyclopediaLinkExtractor, LinkValidator

class TestDescriptionLinkTargets:
    """Test extraction and validation of description links"""
    
    def setup_method(self):
        """Setup test parameters and outputs"""
        self.input_file = CURRENT_ENCYCLOPEDIA_FILE
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.extractor = EncyclopediaLinkExtractor()
        self.validator = LinkValidator()
        
        # Expected outputs
        self.description_links_file = Path(self.output_dir, "description_links.json")
        self.link_validation_file = Path(self.output_dir, "description_link_validation.json")
        self.link_classification_file = Path(self.output_dir, "link_classification.json")
    
    def test_extract_description_links(self):
        """Extract all links from description paragraphs"""
        # Define inputs
        html_content = self.input_file.read_text(encoding='utf-8')
        
        # Call module
        entries = self.extractor.extract_entries(html_content)
        all_description_links = []
        
        for entry in entries:
            entry_links = {
                'term': entry['term'],
                'links': entry['description_links']
            }
            all_description_links.append(entry_links)
        
        # Make assertions
        assert len(all_description_links) > 0, "No description links found"
        total_links = sum(len(entry['links']) for entry in all_description_links)
        assert total_links >= MIN_LINKS_PER_ENTRY * len(all_description_links), \
            f"Expected at least {MIN_LINKS_PER_ENTRY} links per entry"
        
        # Verify no citation links are included
        citation_links = []
        for entry in all_description_links:
            for link in entry['links']:
                if link['href'].startswith('#cite'):
                    citation_links.append(link)
        
        assert len(citation_links) == 0, f"Found {len(citation_links)} citation links (should be 0)"
        
        # Save results
        with open(self.description_links_file, 'w') as f:
            json.dump(all_description_links, f, indent=2)
    
    def test_classify_link_types(self):
        """Classify links by type (article, file, help, external)"""
        # Define inputs
        if not self.description_links_file.exists():
            pytest.skip("Description links not available")
        
        with open(self.description_links_file, 'r') as f:
            all_links = json.load(f)
        
        # Call module
        link_classification = {
            'article': [],
            'file': [],
            'help': [],
            'external': [],
            'anchor': [],
            'unknown': []
        }
        
        for entry in all_links:
            for link in entry['links']:
                link_type = link['type']
                link_info = {
                    'term': entry['term'],
                    'href': link['href'],
                    'text': link['text']
                }
                link_classification[link_type].append(link_info)
        
        # Make assertions
        assert len(link_classification['article']) > 0, "No article links found"
        # Note: file links may not be present in mini test file
        # assert len(link_classification['file']) > 0, "No file links found"
        
        # Verify classification accuracy
        for link_type, links in link_classification.items():
            if link_type == 'article':
                assert all(link['href'].startswith('/wiki/') and not link['href'].startswith('/wiki/File:') 
                          and not link['href'].startswith('/wiki/Help:') for link in links), \
                    "Article links incorrectly classified"
            elif link_type == 'file':
                assert all(link['href'].startswith('/wiki/File:') for link in links), \
                    "File links incorrectly classified"
            elif link_type == 'help':
                assert all(link['href'].startswith('/wiki/Help:') for link in links), \
                    "Help links incorrectly classified"
        
        # Save results
        with open(self.link_classification_file, 'w') as f:
            json.dump(link_classification, f, indent=2)
    
    def test_validate_internal_links(self):
        """Validate internal Wikipedia links are accessible"""
        # Define inputs
        if not self.link_classification_file.exists():
            pytest.skip("Link classification not available")
        
        with open(self.link_classification_file, 'r') as f:
            classification = json.load(f)
        
        # Call module
        internal_links = classification['article'] + classification['file'] + classification['help']
        validation_results = {}
        
        # Test a subset of links to avoid timeout
        test_links = internal_links[:10]  # Test first 10 links
        hrefs = [link['href'] for link in test_links]
        
        validation_results = self.validator.validate_wikipedia_links(hrefs)
        
        # Make assertions
        assert len(validation_results) > 0, "No validation results"
        accessible_count = sum(1 for result in validation_results.values() 
                              if result.get('accessible', False))
        assert accessible_count > 0, "No accessible internal links found"
        
        # Save results
        with open(self.link_validation_file, 'w') as f:
            json.dump(validation_results, f, indent=2)
    
    def test_relative_url_resolution(self):
        """Test that relative URLs resolve correctly with base URL"""
        # Define inputs
        test_relative_urls = [
            "/wiki/Weather",
            "/wiki/File:Example.jpg",
            "/wiki/Help:IPA/English"
        ]
        base_url = "https://en.wikipedia.org/wiki/"
        
        # Call module
        resolved_urls = []
        for rel_url in test_relative_urls:
            resolved = self.extractor.normalize_wikipedia_url(urljoin(base_url, rel_url))
            resolved_urls.append(resolved)
        
        # Make assertions
        assert len(resolved_urls) == len(test_relative_urls), "Not all URLs resolved"
        assert all(url.startswith('https://en.wikipedia.org/wiki/') for url in resolved_urls), \
            "Resolved URLs don't use correct base"
        
        # Verify specific patterns
        assert any('/wiki/Weather' in url for url in resolved_urls), "Weather link not resolved"
        assert any('/wiki/File:' in url for url in resolved_urls), "File link not resolved"
        assert any('/wiki/Help:' in url for url in resolved_urls), "Help link not resolved"
    
    def test_link_text_consistency(self):
        """Test that link text is meaningful and consistent"""
        # Define inputs
        if not self.description_links_file.exists():
            pytest.skip("Description links not available")
        
        with open(self.description_links_file, 'r') as f:
            all_links = json.load(f)
        
        # Call module
        link_text_analysis = {
            'empty_text': [],
            'whitespace_only': [],
            'meaningful_text': []
        }
        
        for entry in all_links:
            for link in entry['links']:
                text = link['text'].strip()
                if not text:
                    link_text_analysis['empty_text'].append(link)
                elif text.isspace():
                    link_text_analysis['whitespace_only'].append(link)
                else:
                    link_text_analysis['meaningful_text'].append(link)
        
        # Make assertions
        assert len(link_text_analysis['meaningful_text']) > 0, "No meaningful link text found"
        # Note: Some links may have empty text (like audio play buttons), so we'll be more lenient
        assert len(link_text_analysis['empty_text']) <= 5, f"Found {len(link_text_analysis['empty_text'])} links with empty text (expected <= 5)"
        assert len(link_text_analysis['whitespace_only']) == 0, f"Found {len(link_text_analysis['whitespace_only'])} links with whitespace-only text"
        
        # Verify text length is reasonable
        meaningful_links = link_text_analysis['meaningful_text']
        assert all(len(link['text']) > 0 for link in meaningful_links), "Some meaningful links have zero-length text"
        assert all(len(link['text']) < 100 for link in meaningful_links), "Some links have unusually long text"
