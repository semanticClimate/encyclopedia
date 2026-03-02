"""
Extract Wikidata relationships from encyclopedia entries.

Uses SPARQL queries to fetch Wikidata properties efficiently.

Date: March 2, 2026 (system date)
"""

from typing import List, Dict, Optional
import requests
from urllib.parse import urlparse


class WikidataRelationshipExtractor:
    """Extract relationships from Wikidata."""
    
    SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
    
    # Common property IDs
    PROPERTY_INSTANCE_OF = "P31"
    PROPERTY_SUBCLASS_OF = "P279"
    PROPERTY_HAS_PART = "P527"
    PROPERTY_PART_OF = "P361"
    PROPERTY_HAS_PART_OF_CLASS = "P2670"
    
    def __init__(self):
        """Initialize Wikidata extractor with caching."""
        self._properties_cache = {}  # Cache for fetched properties
    
    def fetch_wikidata_properties(self, wikidata_id: str) -> Dict:
        """
        Fetch Wikidata properties for an entity.
        
        Args:
            wikidata_id: Wikidata Q ID (e.g., "Q7942")
            
        Returns:
            Dict mapping property IDs to lists of values:
            {
                "P31": ["Q7937"],  # instance of
                "P279": ["Q11421"]  # subclass of
            }
        """
        if not wikidata_id or wikidata_id in ('', 'no_wikidata_id', 'invalid_wikidata_id'):
            return {}
        
        # Check cache
        if wikidata_id in self._properties_cache:
            return self._properties_cache[wikidata_id]
        
        # Fetch using SPARQL
        properties = self._fetch_properties_sparql([wikidata_id])
        
        # Cache result
        if wikidata_id in properties:
            self._properties_cache[wikidata_id] = properties[wikidata_id]
            return properties[wikidata_id]
        
        # Cache empty result to avoid repeated queries
        self._properties_cache[wikidata_id] = {}
        return {}
    
    def extract_ancestry_relationships(self, entry: Dict) -> List[Dict]:
        """
        Extract instance of and subclass of relationships.
        
        Args:
            entry: Entry dict with wikidata_id
            
        Returns:
            List of dicts with:
            - 'property_id': P31 or P279
            - 'target_id': Target Wikidata Q ID
            - 'property_label': Human-readable name
        """
        relationships = []
        
        wikidata_id = entry.get('wikidata_id', '')
        if not wikidata_id or wikidata_id in ('', 'no_wikidata_id', 'invalid_wikidata_id'):
            return relationships
        
        # Fetch properties
        properties = self.fetch_wikidata_properties(wikidata_id)
        
        # Extract P31 (instance of)
        if self.PROPERTY_INSTANCE_OF in properties:
            for value_id in properties[self.PROPERTY_INSTANCE_OF]:
                if value_id.startswith('Q'):
                    relationships.append({
                        'property_id': self.PROPERTY_INSTANCE_OF,
                        'target_id': value_id,
                        'property_label': 'instance of'
                    })
        
        # Extract P279 (subclass of)
        if self.PROPERTY_SUBCLASS_OF in properties:
            for value_id in properties[self.PROPERTY_SUBCLASS_OF]:
                if value_id.startswith('Q'):
                    relationships.append({
                        'property_id': self.PROPERTY_SUBCLASS_OF,
                        'target_id': value_id,
                        'property_label': 'subclass of'
                    })
        
        return relationships
    
    def extract_part_relationships(self, entry: Dict) -> List[Dict]:
        """
        Extract part-whole relationships.
        
        Args:
            entry: Entry dict with wikidata_id
            
        Returns:
            List of dicts with:
            - 'property_id': P527, P361, or P2670
            - 'target_id': Target Wikidata Q ID
            - 'direction': 'has_part' or 'part_of'
        """
        relationships = []
        
        wikidata_id = entry.get('wikidata_id', '')
        if not wikidata_id or wikidata_id in ('', 'no_wikidata_id', 'invalid_wikidata_id'):
            return relationships
        
        # Fetch properties
        properties = self.fetch_wikidata_properties(wikidata_id)
        
        # Extract P527 (has part)
        if self.PROPERTY_HAS_PART in properties:
            for value_id in properties[self.PROPERTY_HAS_PART]:
                if value_id.startswith('Q'):
                    relationships.append({
                        'property_id': self.PROPERTY_HAS_PART,
                        'target_id': value_id,
                        'direction': 'has_part'
                    })
        
        # Extract P361 (part of)
        if self.PROPERTY_PART_OF in properties:
            for value_id in properties[self.PROPERTY_PART_OF]:
                if value_id.startswith('Q'):
                    relationships.append({
                        'property_id': self.PROPERTY_PART_OF,
                        'target_id': value_id,
                        'direction': 'part_of'
                    })
        
        # Extract P2670 (has part(s) of the class)
        if self.PROPERTY_HAS_PART_OF_CLASS in properties:
            for value_id in properties[self.PROPERTY_HAS_PART_OF_CLASS]:
                if value_id.startswith('Q'):
                    relationships.append({
                        'property_id': self.PROPERTY_HAS_PART_OF_CLASS,
                        'target_id': value_id,
                        'direction': 'has_part'
                    })
        
        return relationships
    
    def find_shared_properties(self, entry1: Dict, entry2: Dict) -> List[Dict]:
        """
        Find shared properties between two entries.
        
        Args:
            entry1: First entry dict
            entry2: Second entry dict
            
        Returns:
            List of dicts with:
            - 'property_id': Shared property ID
            - 'value_id': Shared value ID
            - 'property_label': Human-readable name
        """
        shared = []
        
        wikidata_id1 = entry1.get('wikidata_id', '')
        wikidata_id2 = entry2.get('wikidata_id', '')
        
        if not wikidata_id1 or wikidata_id1 in ('', 'no_wikidata_id', 'invalid_wikidata_id'):
            return shared
        if not wikidata_id2 or wikidata_id2 in ('', 'no_wikidata_id', 'invalid_wikidata_id'):
            return shared
        
        # Fetch properties for both entries
        properties1 = self.fetch_wikidata_properties(wikidata_id1)
        properties2 = self.fetch_wikidata_properties(wikidata_id2)
        
        # Find shared property-value pairs
        for prop_id, values1 in properties1.items():
            if prop_id in properties2:
                values2 = properties2[prop_id]
                # Find intersection of values
                shared_values = set(values1) & set(values2)
                for value_id in shared_values:
                    if value_id.startswith('Q'):
                        shared.append({
                            'property_id': prop_id,
                            'value_id': value_id,
                            'property_label': self._get_property_label(prop_id)
                        })
        
        return shared
    
    def _fetch_properties_sparql(self, wikidata_ids: List[str], 
                                 property_ids: List[str] = None) -> Dict:
        """
        Fetch Wikidata properties for multiple entities using SPARQL.
        
        Args:
            wikidata_ids: List of Wikidata Q IDs
            property_ids: Optional list of property IDs to fetch (e.g., ["P31", "P279"])
                         If None, fetches all properties
        
        Returns:
            Dict mapping entity ID to dict of properties
        """
        if not wikidata_ids:
            return {}
        
        # Filter valid Q IDs
        valid_ids = [qid for qid in wikidata_ids if qid and qid.startswith('Q')]
        if not valid_ids:
            return {}
        
        # Build SPARQL query
        entity_list = " ".join([f"wd:{qid}" for qid in valid_ids])
        
        property_filter = ""
        if property_ids:
            prop_list = " ".join([f"wdt:{pid}" for pid in property_ids])
            property_filter = f"FILTER(?property IN ({prop_list}))"
        
        query = f"""
        SELECT ?entity ?property ?value WHERE {{
          VALUES ?entity {{ {entity_list} }}
          ?entity ?property ?value .
          {property_filter}
          FILTER(STRSTARTS(STR(?property), "http://www.wikidata.org/prop/direct/"))
          FILTER(STRSTARTS(STR(?value), "http://www.wikidata.org/entity/"))
        }}
        """
        
        try:
            # Execute query
            response = requests.get(
                self.SPARQL_ENDPOINT,
                params={'query': query, 'format': 'json'},
                headers={'User-Agent': 'Encyclopedia Knowledge Graph Builder'},
                timeout=30
            )
            response.raise_for_status()
            results = response.json()
            
            # Parse results
            properties = {}
            for binding in results.get('results', {}).get('bindings', []):
                entity_uri = binding.get('entity', {}).get('value', '')
                prop_uri = binding.get('property', {}).get('value', '')
                value_uri = binding.get('value', {}).get('value', '')
                
                # Extract Q/P IDs from URIs
                entity = self._extract_qid_from_uri(entity_uri)
                prop = self._extract_pid_from_uri(prop_uri)
                value = self._extract_qid_from_uri(value_uri)
                
                if entity and prop and value:
                    if entity not in properties:
                        properties[entity] = {}
                    if prop not in properties[entity]:
                        properties[entity][prop] = []
                    properties[entity][prop].append(value)
            
            return properties
        
        except Exception as e:
            # On error, return empty dict
            # In production, might want to log this
            return {}
    
    def _extract_qid_from_uri(self, uri: str) -> Optional[str]:
        """Extract Q ID from Wikidata URI."""
        if not uri:
            return None
        if uri.startswith('http://www.wikidata.org/entity/'):
            return uri.split('/')[-1]
        return None
    
    def _extract_pid_from_uri(self, uri: str) -> Optional[str]:
        """Extract P ID from Wikidata property URI."""
        if not uri:
            return None
        if 'prop/direct/' in uri:
            return uri.split('/')[-1]
        return None
    
    def _get_property_label(self, property_id: str) -> str:
        """Get human-readable label for property ID."""
        labels = {
            self.PROPERTY_INSTANCE_OF: 'instance of',
            self.PROPERTY_SUBCLASS_OF: 'subclass of',
            self.PROPERTY_HAS_PART: 'has part',
            self.PROPERTY_PART_OF: 'part of',
            self.PROPERTY_HAS_PART_OF_CLASS: 'has part(s) of the class',
        }
        return labels.get(property_id, property_id)
