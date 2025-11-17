"""
Modular link extraction utilities for encyclopedia analysis
Reusable components for ../amilib integration
"""

import re
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
import time

class EncyclopediaLinkExtractor:
    """Extract and analyze links from encyclopedia HTML"""
    
    def __init__(self, base_url: str = "https://en.wikipedia.org/wiki/"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Encyclopedia Link Extractor/1.0'
        })
    
    def extract_entries(self, html_content: str) -> List[Dict]:
        """Extract all encyclopedia entries from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        dictionary = soup.find('div', {'role': 'ami_dictionary'})
        
        if not dictionary:
            raise ValueError("No dictionary container found")
        
        entries = []
        for entry_div in dictionary.find_all('div', {'role': 'ami_entry'}):
            entry = self._extract_single_entry(entry_div)
            if entry:
                entries.append(entry)
        
        return entries
    
    def _extract_single_entry(self, entry_div) -> Optional[Dict]:
        """Extract data from a single entry div"""
        try:
            term = entry_div.get('term', '')
            name = entry_div.get('name', '')
            
            # Extract search URL
            search_p = None
            for p in entry_div.find_all('p'):
                if p.get_text() and 'search term:' in p.get_text():
                    search_p = p
                    break
            
            search_url = ""
            if search_p:
                search_link = search_p.find('a', href=True)
                if search_link:
                    search_url = search_link['href']
            
            # Extract description
            desc_p = entry_div.find('p', class_='wpage_first_para')
            description_html = str(desc_p) if desc_p else ""
            
            # Extract links from description
            links = self._extract_description_links(desc_p) if desc_p else []
            
            return {
                'term': term,
                'name': name,
                'search_url': search_url,
                'description_html': description_html,
                'description_links': links
            }
        except Exception as e:
            print(f"Error extracting entry: {e}")
            return None
    
    def _extract_description_links(self, desc_element) -> List[Dict]:
        """Extract all links from description paragraph"""
        links = []
        if not desc_element:
            return links
        
        for link in desc_element.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            # Skip citation links
            if href.startswith('#cite'):
                continue
            
            link_info = {
                'href': href,
                'text': text,
                'title': link.get('title', ''),
                'class': link.get('class', [])
            }
            
            # Classify link type
            link_info['type'] = self._classify_link_type(href)
            links.append(link_info)
        
        return links
    
    def _classify_link_type(self, href: str) -> str:
        """Classify link type based on href pattern"""
        if href.startswith('/wiki/File:'):
            return 'file'
        elif href.startswith('/wiki/Help:'):
            return 'help'
        elif href.startswith('/wiki/'):
            return 'article'
        elif href.startswith('http'):
            return 'external'
        elif href.startswith('#'):
            return 'anchor'
        else:
            return 'unknown'
    
    def resolve_search_url(self, search_url: str, timeout: int = 30) -> Tuple[str, int]:
        """Follow search URL redirect to get canonical article URL"""
        try:
            response = self.session.get(search_url, timeout=timeout, allow_redirects=True)
            return response.url, response.status_code
        except requests.RequestException as e:
            print(f"Error resolving {search_url}: {e}")
            return search_url, 0
    
    def normalize_wikipedia_url(self, url: str) -> str:
        """Normalize Wikipedia URL to canonical format"""
        parsed = urlparse(url)
        if parsed.netloc == 'en.wikipedia.org':
            if parsed.path.startswith('/wiki/'):
                return f"https://en.wikipedia.org{parsed.path}{parsed.fragment}"
        return url
    
    def extract_all_link_targets(self, entries: List[Dict]) -> Dict[str, List[str]]:
        """Extract all unique link targets from entries"""
        targets = {
            'search_urls': [],
            'article_links': [],
            'file_links': [],
            'help_links': [],
            'external_links': []
        }
        
        for entry in entries:
            # Search URLs
            if entry.get('search_url'):
                targets['search_urls'].append(entry['search_url'])
            
            # Description links
            for link in entry.get('description_links', []):
                link_type = link.get('type', 'unknown')
                href = link['href']
                
                if link_type == 'article':
                    targets['article_links'].append(href)
                elif link_type == 'file':
                    targets['file_links'].append(href)
                elif link_type == 'help':
                    targets['help_links'].append(href)
                elif link_type == 'external':
                    targets['external_links'].append(href)
        
        # Remove duplicates
        for key in targets:
            targets[key] = list(set(targets[key]))
        
        return targets

    def find_shared_article_links(self, entries, min_occurrences=2):
        """Find article links that appear in multiple entries"""
        from collections import Counter
        import urllib.parse
        
        article_link_counter = Counter()
        link_to_entries = {}
        
        for entry in entries:
            entry_term = entry.get('term', '')
            for link in entry.get('description_links', []):
                if link.get('type') == 'article':
                    href = link.get('href', '')
                    # Normalize the link URL
                    normalized_href = self.normalize_wikipedia_url(
                        f"https://en.wikipedia.org{href}" if href.startswith('/wiki/') else href
                    )
                    
                    article_link_counter[normalized_href] += 1
                    
                    if normalized_href not in link_to_entries:
                        link_to_entries[normalized_href] = []
                    link_to_entries[normalized_href].append({
                        'term': entry_term,
                        'link_text': link.get('text', ''),
                        'title': link.get('title', '')
                    })
        
        # Find links that appear in multiple entries
        shared_links = {}
        for link_url, count in article_link_counter.items():
            if count >= min_occurrences:
                article_name = link_url.split('/wiki/')[-1] if '/wiki/' in link_url else link_url
                article_name = urllib.parse.unquote(article_name.replace('_', ' '))
                
                shared_links[link_url] = {
                    'occurrence_count': count,
                    'entries': link_to_entries[link_url],
                    'article_name': article_name
                }
        
        return {
            'article_link_counts': dict(article_link_counter),
            'shared_article_links': shared_links,
            'total_shared_links': len(shared_links)
        }

class LinkValidator:
    """Validate extracted links and their targets"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Encyclopedia Link Validator/1.0'
        })
    
    def validate_wikipedia_links(self, links: List[str], timeout: int = 10) -> Dict[str, Dict]:
        """Validate Wikipedia links and return status information"""
        results = {}
        
        for link in links:
            try:
                if link.startswith('/wiki/'):
                    full_url = f"https://en.wikipedia.org{link}"
                else:
                    full_url = link
                
                response = self.session.head(full_url, timeout=timeout)
                results[link] = {
                    'status_code': response.status_code,
                    'final_url': response.url,
                    'accessible': response.status_code == 200
                }
            except requests.RequestException as e:
                results[link] = {
                    'status_code': 0,
                    'final_url': link,
                    'accessible': False,
                    'error': str(e)
                }
        
        return results
    
    def check_link_consistency(self, search_url: str, canonical_url: str) -> bool:
        """Check if search URL resolves to expected canonical URL"""
        try:
            response = self.session.get(search_url, timeout=30, allow_redirects=True)
            return response.url == canonical_url
        except:
            return False
