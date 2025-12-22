"""
Test 6: Validate article existence and accessibility
Purpose: Ensure linked articles exist and are accessible
"""

import pytest
from pathlib import Path
import json
import requests
from test.text_links.test_config import CURRENT_ENCYCLOPEDIA_FILE, OUTPUT_DIR, MAX_REDIRECT_DEPTH
from test.text_links.link_extractor import EncyclopediaLinkExtractor, LinkValidator

class TestArticleAccessibility:
    """Test article existence and accessibility"""
    
    def setup_method(self):
        """Setup test parameters and outputs"""
        self.input_file = CURRENT_ENCYCLOPEDIA_FILE
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.extractor = EncyclopediaLinkExtractor()
        self.validator = LinkValidator()
        
        # Expected outputs
        self.accessibility_report_file = Path(self.output_dir, "accessibility_report.json")
        self.http_status_file = Path(self.output_dir, "http_status_codes.json")
        self.error_report_file = Path(self.output_dir, "error_report.json")
    
    def test_validate_article_existence(self):
        """Validate that linked articles exist"""
        # Define inputs
        html_content = self.input_file.read_text(encoding='utf-8')
        
        # Call module
        entries = self.extractor.extract_entries(html_content)
        all_links = self.extractor.extract_all_link_targets(entries)
        
        # Test a subset of article links to avoid timeout
        test_article_links = all_links['article_links'][:5]  # Test first 5 links
        
        validation_results = self.validator.validate_wikipedia_links(test_article_links)
        
        # Make assertions
        assert len(validation_results) > 0, "No validation results"
        
        accessible_count = sum(1 for result in validation_results.values() 
                              if result.get('accessible', False))
        assert accessible_count > 0, "No accessible articles found"
        
        # Verify HTTP status codes
        status_codes = [result['status_code'] for result in validation_results.values()]
        assert all(code in [200, 301, 302, 404] for code in status_codes), \
            f"Unexpected status codes: {set(status_codes)}"
        
        # Save results
        with open(self.accessibility_report_file, 'w') as f:
            json.dump(validation_results, f, indent=2)
    
    def test_analyze_http_status_codes(self):
        """Analyze HTTP status codes from link validation"""
        # Define inputs
        if not self.accessibility_report_file.exists():
            pytest.skip("Accessibility report not available")
        
        with open(self.accessibility_report_file, 'r') as f:
            validation_results = json.load(f)
        
        # Call module
        status_analysis = {
            'status_codes': {},
            'accessible_links': [],
            'redirect_links': [],
            'error_links': [],
            'success_rate': 0
        }
        
        total_links = len(validation_results)
        accessible_count = 0
        
        for link, result in validation_results.items():
            status_code = result['status_code']
            status_analysis['status_codes'][status_code] = status_analysis['status_codes'].get(status_code, 0) + 1
            
            if status_code == 200:
                accessible_count += 1
                status_analysis['accessible_links'].append(link)
            elif status_code in [301, 302]:
                status_analysis['redirect_links'].append(link)
            else:
                status_analysis['error_links'].append(link)
        
        status_analysis['success_rate'] = accessible_count / total_links if total_links > 0 else 0
        
        # Make assertions
        assert len(status_analysis['status_codes']) > 0, "No status codes found"
        assert status_analysis['success_rate'] >= 0, "Invalid success rate"
        assert status_analysis['success_rate'] <= 1, "Success rate exceeds 100%"
        
        # Verify status code distribution
        assert 200 in status_analysis['status_codes'], "No 200 status codes found"
        
        # Save results
        with open(self.http_status_file, 'w') as f:
            json.dump(status_analysis, f, indent=2)
    
    def test_handle_redirects_properly(self):
        """Test proper handling of redirects (301/302)"""
        # Define inputs
        test_redirect_urls = [
            'https://httpbin.org/redirect/1',  # 302 redirect
            'https://httpbin.org/status/301',   # 301 redirect
        ]
        
        # Call module
        redirect_results = {}
        
        for url in test_redirect_urls:
            try:
                response = self.extractor.session.get(url, timeout=10, allow_redirects=True)
                redirect_results[url] = {
                    'status_code': response.status_code,
                    'final_url': response.url,
                    'redirect_count': len(response.history),
                    'is_redirect': len(response.history) > 0
                }
            except Exception as e:
                redirect_results[url] = {
                    'status_code': 0,
                    'error': str(e),
                    'is_redirect': False
                }
        
        # Make assertions
        assert len(redirect_results) == len(test_redirect_urls), "Not all URLs tested"
        
        # Verify redirect handling
        redirect_count = sum(1 for result in redirect_results.values() if result.get('is_redirect', False))
        assert redirect_count > 0, "No redirects detected"
        
        # Verify redirect limits
        max_redirects = max(result.get('redirect_count', 0) for result in redirect_results.values())
        assert max_redirects <= MAX_REDIRECT_DEPTH, f"Redirect depth {max_redirects} exceeds limit"
    
    def test_handle_404_errors(self):
        """Test handling of 404 errors"""
        # Define inputs
        test_404_urls = [
            'https://httpbin.org/status/404',
            'https://en.wikipedia.org/wiki/NonexistentArticle12345',
        ]
        
        # Call module
        error_results = {}
        
        for url in test_404_urls:
            try:
                response = self.extractor.session.head(url, timeout=10)
                error_results[url] = {
                    'status_code': response.status_code,
                    'is_404': response.status_code == 404,
                    'accessible': response.status_code == 200
                }
            except Exception as e:
                error_results[url] = {
                    'status_code': 0,
                    'is_404': False,
                    'accessible': False,
                    'error': str(e)
                }
        
        # Make assertions
        assert len(error_results) == len(test_404_urls), "Not all URLs tested"
        
        # Verify 404 detection
        error_404_count = sum(1 for result in error_results.values() if result.get('is_404', False))
        assert error_404_count > 0, "No 404 errors detected"
        
        # Verify accessibility flags
        accessible_count = sum(1 for result in error_results.values() if result.get('accessible', False))
        assert accessible_count == 0, "404 URLs should not be accessible"
    
    def test_handle_network_errors(self):
        """Test handling of network-related errors"""
        # Define inputs
        test_error_urls = [
            'https://nonexistent-domain-12345.com',
            'https://timeout-test.example.com',  # Will timeout
        ]
        
        # Call module
        network_error_results = {}
        
        for url in test_error_urls:
            try:
                response = self.extractor.session.get(url, timeout=2)  # Short timeout
                network_error_results[url] = {
                    'status_code': response.status_code,
                    'accessible': True,
                    'error_type': 'none'
                }
            except requests.exceptions.Timeout:
                network_error_results[url] = {
                    'status_code': 0,
                    'accessible': False,
                    'error_type': 'timeout'
                }
            except requests.exceptions.ConnectionError:
                network_error_results[url] = {
                    'status_code': 0,
                    'accessible': False,
                    'error_type': 'connection_error'
                }
            except Exception as e:
                network_error_results[url] = {
                    'status_code': 0,
                    'accessible': False,
                    'error_type': 'other',
                    'error': str(e)
                }
        
        # Make assertions
        assert len(network_error_results) == len(test_error_urls), "Not all URLs tested"
        
        # Verify error handling
        error_count = sum(1 for result in network_error_results.values() if not result.get('accessible', True))
        assert error_count > 0, "No network errors detected"
        
        # Verify error types
        error_types = [result.get('error_type', 'none') for result in network_error_results.values()]
        assert any(error_type != 'none' for error_type in error_types), "No error types detected"
    
    def test_generate_error_report(self):
        """Generate comprehensive error report"""
        # Define inputs
        test_urls = [
            'https://httpbin.org/status/200',   # Success
            'https://httpbin.org/status/404',   # 404
            'https://httpbin.org/status/500',   # Server error
            'https://nonexistent-domain-12345.com',  # Connection error
        ]
        
        # Call module
        error_report = {
            'total_tested': len(test_urls),
            'successful': 0,
            'failed': 0,
            'error_categories': {
                'client_errors': [],
                'server_errors': [],
                'network_errors': [],
                'timeout_errors': []
            },
            'detailed_results': {}
        }
        
        for url in test_urls:
            try:
                response = self.extractor.session.head(url, timeout=5)
                status_code = response.status_code
                
                if 200 <= status_code < 300:
                    error_report['successful'] += 1
                elif 400 <= status_code < 500:
                    error_report['failed'] += 1
                    error_report['error_categories']['client_errors'].append(url)
                elif 500 <= status_code < 600:
                    error_report['failed'] += 1
                    error_report['error_categories']['server_errors'].append(url)
                
                error_report['detailed_results'][url] = {
                    'status_code': status_code,
                    'accessible': 200 <= status_code < 300
                }
                
            except requests.exceptions.Timeout:
                error_report['failed'] += 1
                error_report['error_categories']['timeout_errors'].append(url)
                error_report['detailed_results'][url] = {
                    'status_code': 0,
                    'accessible': False,
                    'error': 'timeout'
                }
            except requests.exceptions.ConnectionError:
                error_report['failed'] += 1
                error_report['error_categories']['network_errors'].append(url)
                error_report['detailed_results'][url] = {
                    'status_code': 0,
                    'accessible': False,
                    'error': 'connection_error'
                }
        
        # Make assertions
        assert error_report['total_tested'] == len(test_urls), "Total tested count mismatch"
        assert error_report['successful'] + error_report['failed'] == error_report['total_tested'], \
            "Success/failure counts don't match total"
        
        # Verify error categories
        total_categorized_errors = sum(len(category) for category in error_report['error_categories'].values())
        assert total_categorized_errors == error_report['failed'], "Error categories don't match failed count"
        
        # Save results
        with open(self.error_report_file, 'w') as f:
            json.dump(error_report, f, indent=2)
