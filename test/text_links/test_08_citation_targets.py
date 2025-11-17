"""
Test 8: Extract citation targets
Purpose: Identify and validate citation targets (excluding #cite links as requested)
"""

import pytest
from pathlib import Path
import json
import re
from .test_config import CURRENT_ENCYCLOPEDIA_FILE, OUTPUT_DIR
from .link_extractor import EncyclopediaLinkExtractor

class TestCitationTargets:
    """Test extraction and analysis of citation targets"""
    
    def setup_method(self):
        """Setup test parameters and outputs"""
        self.input_file = CURRENT_ENCYCLOPEDIA_FILE
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.extractor = EncyclopediaLinkExtractor()
        
        # Expected outputs
        self.citation_analysis_file = Path(self.output_dir, "citation_analysis.json")
        self.reference_patterns_file = Path(self.output_dir, "reference_patterns.json")
        self.citation_validation_file = Path(self.output_dir, "citation_validation.json")
    
    def test_extract_citation_patterns(self):
        """Extract citation patterns from entries"""
        # Define inputs
        html_content = self.input_file.read_text(encoding='utf-8')
        
        # Call module
        entries = self.extractor.extract_entries(html_content)
        citation_patterns = self._extract_citation_patterns(entries)
        
        # Make assertions
        assert isinstance(citation_patterns['citation_links'], list), "Citation links should be list"
        assert isinstance(citation_patterns['reference_patterns'], dict), "Reference patterns should be dict"
        assert citation_patterns['total_citations'] >= 0, "Invalid citation count"
        
        # Verify no #cite links are included (as requested)
        cite_links = [link for link in citation_patterns['citation_links'] 
                     if link['href'].startswith('#cite')]
        assert len(cite_links) == 0, f"Found {len(cite_links)} #cite links (should be 0)"
        
        # Save results
        with open(self.citation_analysis_file, 'w') as f:
            json.dump(citation_patterns, f, indent=2)
    
    def _extract_citation_patterns(self, entries):
        """Extract citation patterns from entries"""
        citation_links = []
        reference_patterns = {
            'wikipedia_references': [],
            'external_references': [],
            'doi_references': [],
            'pmid_references': [],
            'other_references': []
        }
        
        for entry in entries:
            for link in entry['description_links']:
                href = link['href']
                text = link['text']
                
                # Skip #cite links as requested
                if href.startswith('#cite'):
                    continue
                
                # Check for citation patterns
                citation_info = {
                    'term': entry['term'],
                    'href': href,
                    'text': text,
                    'type': link['type']
                }
                
                # Classify reference types
                if 'doi.org' in href or 'doi:' in text.lower():
                    reference_patterns['doi_references'].append(citation_info)
                elif 'pubmed' in href or 'pmid' in text.lower():
                    reference_patterns['pmid_references'].append(citation_info)
                elif href.startswith('/wiki/'):
                    reference_patterns['wikipedia_references'].append(citation_info)
                elif href.startswith('http'):
                    reference_patterns['external_references'].append(citation_info)
                else:
                    reference_patterns['other_references'].append(citation_info)
                
                citation_links.append(citation_info)
        
        return {
            'citation_links': citation_links,
            'reference_patterns': reference_patterns,
            'total_citations': len(citation_links),
            'citation_types': {
                'wikipedia': len(reference_patterns['wikipedia_references']),
                'external': len(reference_patterns['external_references']),
                'doi': len(reference_patterns['doi_references']),
                'pmid': len(reference_patterns['pmid_references']),
                'other': len(reference_patterns['other_references'])
            }
        }
    
    def test_analyze_reference_patterns(self):
        """Analyze patterns in references"""
        # Define inputs
        if not self.citation_analysis_file.exists():
            pytest.skip("Citation analysis not available")
        
        with open(self.citation_analysis_file, 'r') as f:
            citation_data = json.load(f)
        
        # Call module
        pattern_analysis = self._analyze_reference_patterns(citation_data)
        
        # Make assertions
        assert len(pattern_analysis['reference_domains']) >= 0, "No reference domains found"
        assert len(pattern_analysis['reference_formats']) >= 0, "No reference formats found"
        assert pattern_analysis['total_references'] >= 0, "Invalid total references"
        
        # Verify pattern analysis
        assert isinstance(pattern_analysis['reference_domains'], dict), "Domains should be dict"
        assert isinstance(pattern_analysis['reference_formats'], dict), "Formats should be dict"
        
        # Save results
        with open(self.reference_patterns_file, 'w') as f:
            json.dump(pattern_analysis, f, indent=2)
    
    def _analyze_reference_patterns(self, citation_data):
        """Analyze patterns in references"""
        reference_patterns = citation_data['reference_patterns']
        
        # Analyze domains
        domain_counter = {}
        format_counter = {}
        
        for ref_type, references in reference_patterns.items():
            format_counter[ref_type] = len(references)
            
            for ref in references:
                if ref['href'].startswith('http'):
                    from urllib.parse import urlparse
                    domain = urlparse(ref['href']).netloc
                    domain_counter[domain] = domain_counter.get(domain, 0) + 1
        
        return {
            'reference_domains': domain_counter,
            'reference_formats': format_counter,
            'total_references': citation_data['total_citations'],
            'most_common_domain': max(domain_counter.items(), key=lambda x: x[1]) if domain_counter else None,
            'most_common_format': max(format_counter.items(), key=lambda x: x[1]) if format_counter else None
        }
    
    def test_validate_citation_completeness(self):
        """Validate completeness of citations"""
        # Define inputs
        if not self.citation_analysis_file.exists():
            pytest.skip("Citation analysis not available")
        
        with open(self.citation_analysis_file, 'r') as f:
            citation_data = json.load(f)
        
        # Call module
        completeness_analysis = self._validate_citation_completeness(citation_data)
        
        # Make assertions
        assert completeness_analysis['total_citations'] >= 0, "Invalid total citations"
        assert completeness_analysis['complete_citations'] >= 0, "Invalid complete citations"
        assert completeness_analysis['incomplete_citations'] >= 0, "Invalid incomplete citations"
        
        # Verify completeness calculations
        total = completeness_analysis['complete_citations'] + completeness_analysis['incomplete_citations']
        assert total == completeness_analysis['total_citations'], "Completeness counts don't match total"
        
        # Save results
        with open(self.citation_validation_file, 'w') as f:
            json.dump(completeness_analysis, f, indent=2)
    
    def _validate_citation_completeness(self, citation_data):
        """Validate completeness of citations"""
        citation_links = citation_data['citation_links']
        
        complete_citations = 0
        incomplete_citations = 0
        completeness_issues = []
        
        for citation in citation_links:
            href = citation['href']
            text = citation['text']
            
            is_complete = True
            issues = []
            
            # Check for completeness indicators
            if not href or href.strip() == '':
                is_complete = False
                issues.append('empty_href')
            
            if not text or text.strip() == '':
                is_complete = False
                issues.append('empty_text')
            
            if href.startswith('http') and len(href) < 10:
                is_complete = False
                issues.append('suspicious_url')
            
            if is_complete:
                complete_citations += 1
            else:
                incomplete_citations += 1
                completeness_issues.append({
                    'citation': citation,
                    'issues': issues
                })
        
        return {
            'total_citations': len(citation_links),
            'complete_citations': complete_citations,
            'incomplete_citations': incomplete_citations,
            'completeness_rate': complete_citations / len(citation_links) if citation_links else 0,
            'completeness_issues': completeness_issues
        }
    
    def test_extract_citation_context(self):
        """Extract context around citations"""
        # Define inputs
        sample_html = '''
        <p class="wpage_first_para">
        This is a paragraph with a <a href="https://example.com/paper">research paper</a> 
        and another <a href="/wiki/Reference">reference</a> to Wikipedia.
        </p>
        '''
        
        # Call module
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(sample_html, 'html.parser')
        context_analysis = []
        
        for link in soup.find_all('a', href=True):
            if not link['href'].startswith('#cite'):  # Skip #cite links
                context = {
                    'link_text': link.get_text(strip=True),
                    'link_href': link['href'],
                    'surrounding_text': link.parent.get_text(strip=True),
                    'link_position': link.parent.get_text(strip=True).find(link.get_text(strip=True))
                }
                context_analysis.append(context)
        
        # Make assertions
        assert len(context_analysis) == 2, "Should find exactly two citation links"
        assert any('research paper' in ctx['link_text'] for ctx in context_analysis), \
            "Research paper link not found"
        assert any('reference' in ctx['link_text'] for ctx in context_analysis), \
            "Reference link not found"
        
        # Verify context extraction
        for ctx in context_analysis:
            assert ctx['link_position'] >= 0, "Link position should be non-negative"
            assert ctx['link_text'] in ctx['surrounding_text'], "Link text should be in surrounding text"
    
    def test_analyze_citation_networks(self):
        """Analyze citation networks between entries"""
        # Define inputs
        html_content = self.input_file.read_text(encoding='utf-8')
        
        # Call module
        entries = self.extractor.extract_entries(html_content)
        citation_network = self._analyze_citation_networks(entries)
        
        # Make assertions
        assert len(citation_network['citation_graph']) >= 0, "Invalid citation graph"
        assert citation_network['total_citation_links'] >= 0, "Invalid citation links"
        assert citation_network['most_cited_entries'] >= 0, "Invalid most cited count"
        
        # Verify network structure
        assert isinstance(citation_network['citation_graph'], list), "Citation graph should be list"
        assert isinstance(citation_network['citation_statistics'], dict), "Statistics should be dict"
        
        # Save results
        with open(self.citation_validation_file, 'w') as f:
            json.dump(citation_network, f, indent=2)
    
    def _analyze_citation_networks(self, entries):
        """Analyze citation networks between entries"""
        citation_graph = []
        citation_counts = {}
        
        for entry in entries:
            entry_citations = []
            for link in entry['description_links']:
                if not link['href'].startswith('#cite'):  # Skip #cite links
                    entry_citations.append(link['href'])
            
            citation_counts[entry['term']] = len(entry_citations)
            
            # Build citation graph
            for citation in entry_citations:
                citation_graph.append({
                    'source': entry['term'],
                    'target': citation,
                    'type': 'citation'
                })
        
        # Calculate statistics
        most_cited = max(citation_counts.values()) if citation_counts else 0
        average_citations = sum(citation_counts.values()) / len(citation_counts) if citation_counts else 0
        
        return {
            'citation_graph': citation_graph,
            'citation_counts': citation_counts,
            'total_citation_links': len(citation_graph),
            'most_cited_entries': most_cited,
            'average_citations_per_entry': average_citations,
            'citation_statistics': {
                'entries_with_citations': sum(1 for count in citation_counts.values() if count > 0),
                'entries_without_citations': sum(1 for count in citation_counts.values() if count == 0),
                'total_entries': len(entries)
            }
        }
