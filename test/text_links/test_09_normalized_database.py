"""
Test 9: Build normalized link database
Purpose: Create a normalized database of all link targets
"""

import pytest
from pathlib import Path
import json
from collections import defaultdict
from .test_config import CURRENT_ENCYCLOPEDIA_FILE, OUTPUT_DIR
from .link_extractor import EncyclopediaLinkExtractor, LinkValidator

class TestNormalizedLinkDatabase:
    """Test building normalized link database"""
    
    def setup_method(self):
        """Setup test parameters and outputs"""
        self.input_file = CURRENT_ENCYCLOPEDIA_FILE
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.extractor = EncyclopediaLinkExtractor()
        self.validator = LinkValidator()
        
        # Expected outputs
        self.normalized_database_file = Path(self.output_dir, "normalized_link_database.json")
        self.link_metadata_file = Path(self.output_dir, "link_metadata.json")
        self.database_statistics_file = Path(self.output_dir, "database_statistics.json")
    
    def test_build_normalized_link_database(self):
        """Build normalized database of all link targets"""
        # Define inputs
        html_content = self.input_file.read_text(encoding='utf-8')
        
        # Call module
        entries = self.extractor.extract_entries(html_content)
        # Only process first 3 entries to avoid timeout
        entries = entries[:3]
        normalized_database = self._build_normalized_database(entries)
        
        # Make assertions
        assert len(normalized_database['canonical_urls']) > 0, "No canonical URLs found"
        assert len(normalized_database['link_metadata']) > 0, "No link metadata found"
        assert normalized_database['total_unique_links'] > 0, "No unique links found"
        
        # Verify normalization
        canonical_urls = normalized_database['canonical_urls']
        assert all(isinstance(url, str) for url in canonical_urls), "Canonical URLs should be strings"
        assert len(set(canonical_urls)) == len(canonical_urls), "Duplicate canonical URLs found"
        
        # Save results as JSON
        with open(self.normalized_database_file, 'w') as f:
            json.dump(normalized_database, f, indent=2)
        
        # Also save as HTML for easy browsing
        html_output = Path(self.output_dir, "normalized_link_database.html")
        self._save_as_html(normalized_database, html_output)
    
    def _build_normalized_database(self, entries):
        """Build normalized database from entries"""
        canonical_urls = set()
        link_metadata = {}
        
        for entry in entries:
            # Process search URL
            if entry['search_url']:
                canonical_url, status_code = self.extractor.resolve_search_url(entry['search_url'])
                normalized_url = self.extractor.normalize_wikipedia_url(canonical_url)
                canonical_urls.add(normalized_url)
                
                link_metadata[normalized_url] = {
                    'original_url': entry['search_url'],
                    'canonical_url': canonical_url,
                    'normalized_url': normalized_url,
                    'status_code': status_code,
                    'link_type': 'search',
                    'source_entry': entry['term'],
                    'context': 'search_term'
                }
            
            # Process description links
            for link in entry['description_links']:
                href = link['href']
                normalized_href = self._normalize_link_href(href)
                canonical_urls.add(normalized_href)
                
                if normalized_href not in link_metadata:
                    link_metadata[normalized_href] = {
                        'original_url': href,
                        'normalized_url': normalized_href,
                        'link_type': link['type'],
                        'source_entries': [],
                        'contexts': []
                    }
                
                # Ensure the entry exists before appending
                if 'source_entries' not in link_metadata[normalized_href]:
                    link_metadata[normalized_href]['source_entries'] = []
                if 'contexts' not in link_metadata[normalized_href]:
                    link_metadata[normalized_href]['contexts'] = []
                
                link_metadata[normalized_href]['source_entries'].append(entry['term'])
                link_metadata[normalized_href]['contexts'].append({
                    'entry': entry['term'],
                    'link_text': link['text'],
                    'title': link['title']
                })
        
        return {
            'canonical_urls': list(canonical_urls),
            'link_metadata': link_metadata,
            'total_unique_links': len(canonical_urls),
            'metadata_count': len(link_metadata)
        }
    
    def _normalize_link_href(self, href):
        """Normalize link href to canonical form"""
        if href.startswith('/wiki/'):
            return f"https://en.wikipedia.org{href}"
        elif href.startswith('https://en.wikipedia.org'):
            return href
        elif href.startswith('http'):
            return href
        else:
            return href
    
    def test_extract_link_metadata(self):
        """Extract comprehensive metadata for all links"""
        # Define inputs
        if not self.normalized_database_file.exists():
            pytest.skip("Normalized database not available")
        
        with open(self.normalized_database_file, 'r') as f:
            database = json.load(f)
        
        # Call module
        metadata_analysis = self._extract_link_metadata(database)
        
        # Make assertions
        assert len(metadata_analysis['metadata_fields']) > 0, "No metadata fields found"
        assert metadata_analysis['total_links_with_metadata'] > 0, "No links with metadata"
        assert metadata_analysis['completeness_rate'] >= 0, "Invalid completeness rate"
        assert metadata_analysis['completeness_rate'] <= 1, "Completeness rate exceeds 100%"
        
        # Verify metadata structure
        assert isinstance(metadata_analysis['metadata_fields'], list), "Metadata fields should be list"
        assert isinstance(metadata_analysis['field_completeness'], dict), "Field completeness should be dict"
        
        # Save results
        with open(self.link_metadata_file, 'w') as f:
            json.dump(metadata_analysis, f, indent=2)
    
    def _extract_link_metadata(self, database):
        """Extract comprehensive metadata for links"""
        link_metadata = database['link_metadata']
        
        # Analyze metadata fields
        all_fields = set()
        field_completeness = defaultdict(int)
        
        for url, metadata in link_metadata.items():
            for field in metadata.keys():
                all_fields.add(field)
                field_completeness[field] += 1
        
        # Calculate completeness
        total_links = len(link_metadata)
        completeness_rate = sum(field_completeness.values()) / (len(all_fields) * total_links) if total_links > 0 else 0
        
        return {
            'metadata_fields': list(all_fields),
            'field_completeness': dict(field_completeness),
            'total_links_with_metadata': total_links,
            'completeness_rate': completeness_rate,
            'most_complete_fields': sorted(field_completeness.items(), key=lambda x: x[1], reverse=True)[:5],
            'least_complete_fields': sorted(field_completeness.items(), key=lambda x: x[1])[:5]
        }
    
    def test_generate_database_statistics(self):
        """Generate comprehensive database statistics"""
        # Define inputs
        if not self.normalized_database_file.exists():
            pytest.skip("Normalized database not available")
        
        with open(self.normalized_database_file, 'r') as f:
            database = json.load(f)
        
        # Call module
        statistics = self._generate_database_statistics(database)
        
        # Make assertions
        assert statistics['total_unique_links'] > 0, "No unique links in statistics"
        assert statistics['link_type_distribution'] is not None, "No link type distribution"
        assert statistics['source_entry_distribution'] is not None, "No source entry distribution"
        
        # Verify statistics consistency
        assert statistics['total_unique_links'] == len(database['canonical_urls']), \
            "Total links mismatch"
        assert statistics['total_metadata_entries'] == len(database['link_metadata']), \
            "Metadata entries mismatch"
        
        # Save results
        with open(self.database_statistics_file, 'w') as f:
            json.dump(statistics, f, indent=2)
    
    def _generate_database_statistics(self, database):
        """Generate comprehensive database statistics"""
        canonical_urls = database['canonical_urls']
        link_metadata = database['link_metadata']
        
        # Analyze link types
        link_type_distribution = defaultdict(int)
        source_entry_distribution = defaultdict(int)
        
        for url, metadata in link_metadata.items():
            link_type = metadata.get('link_type', 'unknown')
            link_type_distribution[link_type] += 1
            
            source_entries = metadata.get('source_entries', [])
            for entry in source_entries:
                source_entry_distribution[entry] += 1
        
        # Calculate additional statistics
        wikipedia_links = sum(1 for url in canonical_urls if 'wikipedia.org' in url)
        external_links = len(canonical_urls) - wikipedia_links
        
        return {
            'total_unique_links': len(canonical_urls),
            'total_metadata_entries': len(link_metadata),
            'wikipedia_links': wikipedia_links,
            'external_links': external_links,
            'link_type_distribution': dict(link_type_distribution),
            'source_entry_distribution': dict(source_entry_distribution),
            'most_linked_entries': sorted(source_entry_distribution.items(), key=lambda x: x[1], reverse=True)[:10],
            'most_common_link_types': sorted(link_type_distribution.items(), key=lambda x: x[1], reverse=True)[:5],
            'average_links_per_entry': sum(source_entry_distribution.values()) / len(source_entry_distribution) if source_entry_distribution else 0
        }
    
    def test_validate_database_consistency(self):
        """Validate consistency of the normalized database"""
        # Define inputs
        if not self.normalized_database_file.exists():
            pytest.skip("Normalized database not available")
        
        with open(self.normalized_database_file, 'r') as f:
            database = json.load(f)
        
        # Call module
        consistency_report = self._validate_database_consistency(database)
        
        # Make assertions
        assert consistency_report['total_links'] > 0, "No links in consistency report"
        assert consistency_report['consistent_links'] >= 0, "Invalid consistent links count"
        assert consistency_report['inconsistent_links'] >= 0, "Invalid inconsistent links count"
        
        # Verify consistency calculations
        total = consistency_report['consistent_links'] + consistency_report['inconsistent_links']
        assert total == consistency_report['total_links'], "Consistency counts don't match total"
        
        # Verify consistency rate
        consistency_rate = consistency_report['consistency_rate']
        assert 0 <= consistency_rate <= 1, "Consistency rate should be between 0 and 1"
        
        # Save results
        with open(self.database_statistics_file, 'w') as f:
            json.dump(consistency_report, f, indent=2)
    
    def _validate_database_consistency(self, database):
        """Validate consistency of the normalized database"""
        canonical_urls = database['canonical_urls']
        link_metadata = database['link_metadata']
        
        consistent_links = 0
        inconsistent_links = 0
        consistency_issues = []
        
        for url in canonical_urls:
            if url in link_metadata:
                metadata = link_metadata[url]
                
                # Check for consistency issues
                issues = []
                
                # Check URL consistency
                if metadata.get('normalized_url') != url:
                    issues.append('url_mismatch')
                
                # Check required fields
                if not metadata.get('link_type'):
                    issues.append('missing_link_type')
                
                # Check source entries
                source_entries = metadata.get('source_entries', [])
                if not source_entries:
                    issues.append('no_source_entries')
                
                if issues:
                    inconsistent_links += 1
                    consistency_issues.append({
                        'url': url,
                        'issues': issues
                    })
                else:
                    consistent_links += 1
        
        consistency_rate = consistent_links / len(canonical_urls) if canonical_urls else 0
        
        return {
            'total_links': len(canonical_urls),
            'consistent_links': consistent_links,
            'inconsistent_links': inconsistent_links,
            'consistency_rate': consistency_rate,
            'consistency_issues': consistency_issues
        }
    
    def _save_as_html(self, database, output_file):
        """Save normalized database as HTML"""
        html_parts = ['<!DOCTYPE html>', '<html><head>',
                      '<title>Normalized Link Database</title>',
                      '<style>body { font-family: sans-serif; margin: 20px; }',
                      'table { border-collapse: collapse; width: 100%; }',
                      'th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }',
                      'th { background-color: #4CAF50; color: white; }',
                      'tr:nth-child(even) { background-color: #f2f2f2; }',
                      'a { color: #0066cc; }</style>',
                      '</head><body>',
                      f'<h1>Normalized Link Database</h1>',
                      f'<p>Total unique links: {database["total_unique_links"]}</p>',
                      '<table><tr><th>Link URL</th><th>Type</th><th>Source Entries</th><th>Contexts</th></tr>']
        
        for url, metadata in database['link_metadata'].items():
            source_entries = ', '.join(metadata.get('source_entries', []))
            contexts = len(metadata.get('contexts', []))
            row = (f'<tr><td><a href="{url}">{url}</a></td>'
                   f'<td>{metadata.get("link_type", "unknown")}</td>'
                   f'<td>{source_entries}</td>'
                   f'<td>{contexts} context(s)</td></tr>')
            html_parts.append(row)
        
        html_parts.extend(['</table></body></html>'])
        output_file.write_text('\n'.join(html_parts), encoding='utf-8')
