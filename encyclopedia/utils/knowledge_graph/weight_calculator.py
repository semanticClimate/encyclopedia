"""
Calculate edge weights for knowledge graph relationships.

Date: March 2, 2026 (system date)
"""

from typing import Dict, Set
from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.knowledge_graph.wikipedia_extractor import WikipediaLinkExtractor


class EdgeWeightCalculator:
    """Calculate weights for graph edges."""
    
    def __init__(self):
        """Initialize weight calculator."""
        self.link_extractor = WikipediaLinkExtractor()
    
    def calculate_shared_link_weight(self, entry1: Dict, entry2: Dict, 
                                     encyclopedia: AmiEncyclopedia) -> float:
        """
        Calculate weight based on shared Wikipedia links using Jaccard similarity.
        
        Formula: |A ∩ B| / |A ∪ B|
        
        Args:
            entry1: First entry dict
            entry2: Second entry dict
            encyclopedia: Encyclopedia instance (for link extraction)
            
        Returns:
            Jaccard similarity coefficient (0.0 to 1.0)
        """
        if not entry1 or not entry2:
            return 0.0
        
        # Extract links from both entries
        links1 = self._extract_link_urls(entry1)
        links2 = self._extract_link_urls(entry2)
        
        if not links1 or not links2:
            return 0.0
        
        # Convert to sets for set operations
        set1 = set(links1)
        set2 = set(links2)
        
        # Calculate intersection and union
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        # Jaccard similarity
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _extract_link_urls(self, entry: Dict) -> Set[str]:
        """
        Extract normalized Wikipedia link URLs from entry description.
        
        Args:
            entry: Entry dict
            
        Returns:
            Set of normalized Wikipedia URLs
        """
        description_html = entry.get('description_html', '')
        if not description_html:
            return set()
        
        # Extract links
        links = self.link_extractor.extract_links_from_description(description_html)
        
        # Return set of normalized URLs
        return {link['url'] for link in links if link.get('url')}
