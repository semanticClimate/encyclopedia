"""
Extract Wikipedia links from encyclopedia entry descriptions.

Date: March 2, 2026 (system date)
"""

from typing import List, Dict, Optional
from urllib.parse import urlparse, unquote
from lxml.html import fromstring, tostring

from encyclopedia.core.encyclopedia import AmiEncyclopedia


class WikipediaLinkExtractor:
    """Extract Wikipedia links from HTML descriptions."""
    
    def extract_links_from_description(self, description_html: str) -> List[Dict]:
        """
        Extract Wikipedia links from HTML description.
        
        Args:
            description_html: HTML string containing description
            
        Returns:
            List of dicts with:
            - 'url': Wikipedia URL (normalized)
            - 'text': Link text
            - 'target_term': Extracted term from URL
        """
        if not description_html:
            return []
        
        links = []
        try:
            # Parse HTML
            root = fromstring(description_html)
            
            # Find all <a> tags with href attributes
            for a_tag in root.xpath('.//a[@href]'):
                href = a_tag.get('href', '')
                if not href:
                    continue
                
                # Skip citation links
                if href.startswith('#cite'):
                    continue
                
                # Check if it's a Wikipedia link
                normalized_url = self._normalize_wikipedia_url(href)
                if normalized_url and ('wikipedia.org/wiki/' in normalized_url or '/wiki/' in normalized_url):
                    # Extract link text
                    link_text = a_tag.text_content().strip() if a_tag.text_content() else ''
                    
                    # Extract term from URL
                    target_term = self._extract_term_from_url(normalized_url)
                    
                    links.append({
                        'url': normalized_url,
                        'text': link_text,
                        'target_term': target_term
                    })
        
        except Exception as e:
            # If parsing fails, return empty list
            # In production, might want to log this
            pass
        
        return links
    
    def find_target_entry(self, url: str, encyclopedia: AmiEncyclopedia) -> Optional[Dict]:
        """
        Find encyclopedia entry matching Wikipedia URL.
        
        Args:
            url: Wikipedia URL
            encyclopedia: Encyclopedia instance
            
        Returns:
            Entry dict if found, None otherwise
        """
        if not url or not encyclopedia:
            return None
        
        # Normalize the URL
        normalized_url = self._normalize_wikipedia_url(url)
        if not normalized_url:
            return None
        
        # Extract page title from URL for matching
        page_title = self._extract_term_from_url(normalized_url)
        normalized_page_title = page_title.lower().replace('_', ' ').strip() if page_title else ''
        
        # Try to match by Wikipedia URL (exact match)
        for entry in encyclopedia.entries:
            entry_url = entry.get('wikipedia_url', '')
            if entry_url:
                normalized_entry_url = self._normalize_wikipedia_url(entry_url)
                if normalized_entry_url == normalized_url:
                    return entry
        
        # Try to match by term extracted from URL (exact match)
        if normalized_page_title:
            for entry in encyclopedia.entries:
                entry_term = entry.get('term', '').lower().strip()
                canonical_term = entry.get('canonical_term', '').lower().strip()
                
                # Exact match
                if entry_term == normalized_page_title or canonical_term == normalized_page_title:
                    return entry
                
                # Partial match (if page title contains entry term or vice versa)
                # This handles cases like "Chemical element" matching "element"
                if entry_term and normalized_page_title:
                    if entry_term in normalized_page_title or normalized_page_title in entry_term:
                        # Prefer longer matches
                        return entry
        
        # Try fuzzy matching by checking if any word in page title matches entry term
        if normalized_page_title:
            page_words = set(normalized_page_title.split())
            for entry in encyclopedia.entries:
                entry_term = entry.get('term', '').lower().strip()
                canonical_term = entry.get('canonical_term', '').lower().strip()
                
                if entry_term:
                    entry_words = set(entry_term.split())
                    # If significant overlap (at least 50% of words match)
                    if page_words and entry_words:
                        overlap = len(page_words & entry_words)
                        if overlap >= min(len(page_words), len(entry_words)) * 0.5:
                            return entry
        
        return None
    
    def count_link_occurrences(self, source_entry: Dict, target_entry: Dict) -> int:
        """
        Count how many times source entry links to target entry.
        
        Args:
            source_entry: Source entry dict
            target_entry: Target entry dict
            
        Returns:
            Number of occurrences
        """
        if not source_entry or not target_entry:
            return 0
        
        description_html = source_entry.get('description_html', '')
        if not description_html:
            return 0
        
        # Extract all links from source description
        links = self.extract_links_from_description(description_html)
        
        # Get target URL for comparison
        target_url = target_entry.get('wikipedia_url', '')
        if not target_url:
            return 0
        
        normalized_target_url = self._normalize_wikipedia_url(target_url)
        if not normalized_target_url:
            return 0
        
        # Count matches
        count = 0
        for link in links:
            normalized_link_url = self._normalize_wikipedia_url(link['url'])
            if normalized_link_url == normalized_target_url:
                count += 1
        
        return count
    
    def _normalize_wikipedia_url(self, url: str) -> Optional[str]:
        """
        Normalize Wikipedia URL to canonical format.
        
        Args:
            url: Wikipedia URL (can be relative or absolute)
            
        Returns:
            Normalized URL or None if not a Wikipedia URL
        """
        if not url:
            return None
        
        # Handle relative URLs
        if url.startswith('/wiki/'):
            url = f"https://en.wikipedia.org{url}"
        elif url.startswith('wiki/'):
            url = f"https://en.wikipedia.org/{url}"
        
        # Parse URL
        parsed = urlparse(url)
        
        # Check if it's a Wikipedia URL
        if 'wikipedia.org' in parsed.netloc or parsed.path.startswith('/wiki/'):
            # Extract path
            path = parsed.path
            
            # Ensure it starts with /wiki/
            if not path.startswith('/wiki/'):
                return None
            
            # Remove fragment and query
            path = path.split('#')[0].split('?')[0]
            
            # Build normalized URL
            if parsed.netloc:
                return f"https://{parsed.netloc}{path}"
            else:
                return f"https://en.wikipedia.org{path}"
        
        return None
    
    def _extract_term_from_url(self, url: str) -> str:
        """
        Extract term from Wikipedia URL.
        
        Args:
            url: Wikipedia URL
            
        Returns:
            Extracted term (with underscores/spaces normalized)
        """
        if not url:
            return ''
        
        # Extract page title from URL
        if '/wiki/' in url:
            page_title = url.split('/wiki/')[-1].split('#')[0].split('?')[0]
            # Decode URL encoding and replace underscores with spaces
            term = unquote(page_title).replace('_', ' ')
            return term
        
        return ''
