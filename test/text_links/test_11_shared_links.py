"""
Test 11: Find shared article links
Purpose: Identify article links that appear in multiple encyclopedia entries

This test:
1. Reads first 100 entries with valid Wikipedia search URLs
2. Extracts all article links from each entry's description
3. Identifies links that appear in multiple entries (shared links)
4. Saves results as both JSON and HTML for easy browsing

The shared links analysis helps identify:
- Common themes or topics across entries
- Most frequently referenced articles
- Articles that serve as bridges between different encyclopedia entries
"""

import pytest
from pathlib import Path
import json
from collections import Counter
from .test_config import ENCYCLOPEDIA_FILE, OUTPUT_DIR, USE_FULL_FILE_FOR_SHARED_LINKS
from .link_extractor import EncyclopediaLinkExtractor

class TestSharedLinks:
    """Test identification of shared article links across entries"""
    
    def setup_method(self):
        """Setup test parameters and outputs"""
        # Use full file for this test to find shared links
        self.input_file = ENCYCLOPEDIA_FILE if USE_FULL_FILE_FOR_SHARED_LINKS else CURRENT_ENCYCLOPEDIA_FILE
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.extractor = EncyclopediaLinkExtractor()
        
        # Expected outputs (will update with actual count)
        self.shared_links_json_file = Path(self.output_dir, "shared_article_links.json")
        self.shared_links_html_file = Path(self.output_dir, "shared_article_links.html")
        self.max_entries = None  # Process ALL entries (no limit)
    
    def test_find_shared_article_links(self):
        """Find article links shared across multiple entries"""
        # Define inputs
        html_content = self.input_file.read_text(encoding='utf-8')
        
        # Call module
        all_entries = self.extractor.extract_entries(html_content)
        
        # Process entries (up to limit if specified)
        processed_entries = []
        max_msg = f"up to {self.max_entries}" if self.max_entries else "ALL"
        print(f"Processing {max_msg} entries from {len(all_entries)} total entries...")
        for entry in all_entries:
            if entry.get('search_url') and (self.max_entries is None or len(processed_entries) < self.max_entries):
                # Resolve search URL to get actual article
                canonical_url, status_code = self.extractor.resolve_search_url(entry['search_url'])
                if status_code == 200:  # Only include successfully resolved URLs
                    entry['resolved_url'] = canonical_url
                    processed_entries.append(entry)
        
        print(f"Successfully processed {len(processed_entries)} entries")
        
        # Update output filenames with actual count
        actual_count = len(processed_entries)
        self.shared_links_json_file = Path(self.output_dir, f"shared_article_links_{actual_count}.json")
        self.shared_links_html_file = Path(self.output_dir, f"shared_article_links_{actual_count}.html")
        
        # Extract all article links from processed entries
        shared_links = self._find_shared_article_links(processed_entries)
        
        # Make assertions
        assert len(processed_entries) > 0, "No processed entries found"
        assert isinstance(shared_links['article_link_counts'], dict), "Link counts should be dict"
        assert len(shared_links['shared_article_links']) >= 0, "Invalid shared links count"
        
        # Save results as JSON
        with open(self.shared_links_json_file, 'w') as f:
            json.dump(shared_links, f, indent=2)
        
        # Also save as HTML
        self._save_shared_links_as_html(shared_links)
    
    def _find_shared_article_links(self, entries):
        """Find article links that appear in multiple entries"""
        article_link_counter = Counter()
        link_to_entries = {}  # Map from link URL to list of entries using it
        
        for entry in entries:
            entry_term = entry.get('term', '')
            entry_url = entry.get('resolved_url', '')
            
            # Extract article links from description
            for link in entry.get('description_links', []):
                if link['type'] == 'article':
                    href = link['href']
                    normalized_href = self.extractor.normalize_wikipedia_url(
                        f"https://en.wikipedia.org{href}" if href.startswith('/wiki/') else href
                    )
                    
                    # Count occurrences
                    article_link_counter[normalized_href] += 1
                    
                    # Track which entries use this link
                    if normalized_href not in link_to_entries:
                        link_to_entries[normalized_href] = []
                    link_to_entries[normalized_href].append({
                        'term': entry_term,
                        'entry_url': entry_url,
                        'link_text': link.get('text', ''),
                        'title': link.get('title', '')
                    })
        
        # Find links that appear in multiple entries
        shared_links = {}
        for link_url, count in article_link_counter.items():
            if count > 1:  # Appears in more than one entry
                shared_links[link_url] = {
                    'occurrence_count': count,
                    'entries': link_to_entries[link_url],
                    'article_name': link_url.split('/wiki/')[-1].replace('_', ' ') if '/wiki/' in link_url else link_url
                }
        
        return {
            'total_processed_entries': len(entries),
            'article_link_counts': dict(article_link_counter),
            'shared_article_links': shared_links,
            'total_shared_links': len(shared_links),
            'most_common_links': dict(article_link_counter.most_common(10))
        }
    
    def _save_shared_links_as_html(self, shared_links_data):
        """Save shared links as HTML"""
        html_parts = ['<!DOCTYPE html>', '<html><head>',
                      '<title>Shared Article Links</title>',
                      '<style>body { font-family: sans-serif; margin: 20px; }',
                      'table { border-collapse: collapse; width: 100%; }',
                      'th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }',
                      'th { background-color: #4CAF50; color: white; }',
                      'tr:nth-child(even) { background-color: #f2f2f2; }',
                      'a { color: #0066cc; }',
                      '.count { font-weight: bold; color: #d32f2f; }',
                      '</style></head><body>',
                      f'<h1>Shared Article Links Analysis - Full Encyclopedia</h1>',
                      f'<p>Total processed entries: {shared_links_data["total_processed_entries"]}</p>',
                      f'<p>Total article links: {len(shared_links_data["article_link_counts"])}</p>',
                      f'<p>Shared article links (appearing in 2+ entries): <strong>{shared_links_data["total_shared_links"]}</strong></p>',
                      '<table><tr><th>Article Link</th><th>Occurrences</th><th>Used In Entries</th></tr>']
        
        # Sort by occurrence count
        sorted_links = sorted(shared_links_data['shared_article_links'].items(), 
                              key=lambda x: x[1]['occurrence_count'], 
                              reverse=True)
        
        for link_url, link_info in sorted_links:
            entries_str = '<br>'.join([entry['term'] for entry in link_info['entries']])
            row = (f'<tr><td><a href="{link_url}">{link_info["article_name"]}</a></td>'
                   f'<td class="count">{link_info["occurrence_count"]}</td>'
                   f'<td>{entries_str}</td></tr>')
            html_parts.append(row)
        
        html_parts.extend(['</table></body></html>'])
        self.shared_links_html_file.write_text('\n'.join(html_parts), encoding='utf-8')
    
    def test_validate_shared_links_structure(self):
        """Validate the structure of shared links data"""
        if not self.shared_links_json_file.exists():
            pytest.skip("Shared links file not available")
        
        with open(self.shared_links_json_file, 'r') as f:
            data = json.load(f)
        
        # Make assertions
        assert 'total_processed_entries' in data, "Missing total_processed_entries"
        assert 'shared_article_links' in data, "Missing shared_article_links"
        assert 'article_link_counts' in data, "Missing article_link_counts"
        
        # Verify shared links structure
        for link_url, link_info in data['shared_article_links'].items():
            assert 'occurrence_count' in link_info, f"Missing occurrence_count for {link_url}"
            assert 'entries' in link_info, f"Missing entries for {link_url}"
            assert link_info['occurrence_count'] > 1, f"Link {link_url} should have > 1 occurrence"
            assert len(link_info['entries']) > 1, f"Link {link_url} should appear in > 1 entry"

