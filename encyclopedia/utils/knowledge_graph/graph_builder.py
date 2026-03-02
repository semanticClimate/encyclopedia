"""
Build knowledge graphs from encyclopedia entries.

Date: March 2, 2026 (system date)
"""

from typing import Dict, Set, Optional
import networkx as nx

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.knowledge_graph.wikipedia_extractor import WikipediaLinkExtractor
from encyclopedia.utils.knowledge_graph.wikidata_extractor import WikidataRelationshipExtractor
from encyclopedia.utils.knowledge_graph.weight_calculator import EdgeWeightCalculator


class KnowledgeGraphBuilder:
    """Build knowledge graphs from encyclopedia entries."""
    
    def __init__(self, encyclopedia: AmiEncyclopedia):
        """
        Initialize graph builder.
        
        Args:
            encyclopedia: Encyclopedia instance
        """
        self.encyclopedia = encyclopedia
        self.wikipedia_extractor = WikipediaLinkExtractor()
        self.wikidata_extractor = WikidataRelationshipExtractor()
        self.weight_calculator = EdgeWeightCalculator()
        
        # Caches
        self._wikipedia_link_index = {}  # Inverted index: URL -> list of entry IDs
        self._entry_id_map = {}  # Map entry IDs to entries
    
    def build_graph(self,
                   include_wikipedia_links: bool = True,
                   include_wikidata_ancestry: bool = True,
                   include_wikidata_parts: bool = True,
                   include_shared_properties: bool = True,
                   include_shared_values: bool = True) -> nx.DiGraph:
        """
        Build complete knowledge graph.
        
        Args:
            include_wikipedia_links: Include Wikipedia description links
            include_wikidata_ancestry: Include ancestry relationships (P31, P279)
            include_wikidata_parts: Include part-whole relationships (P527, P361)
            include_shared_properties: Include shared property relationships
            include_shared_values: Include shared value relationships
            
        Returns:
            NetworkX DiGraph with nodes and edges
        """
        # Create directed graph
        graph = nx.DiGraph()
        
        # Build indexes
        self._build_indexes()
        
        # Add nodes for all entries
        self._add_entry_nodes(graph)
        
        # Add edges based on selected relationship types
        if include_wikipedia_links:
            self._add_wikipedia_links(graph)
        
        if include_wikidata_ancestry:
            self._add_wikidata_ancestry(graph)
        
        if include_wikidata_parts:
            self._add_wikidata_parts(graph)
        
        if include_shared_properties:
            self._add_shared_properties(graph)
        
        if include_shared_values:
            self._add_shared_values(graph)
        
        return graph
    
    def _build_indexes(self):
        """Build indexes for efficient lookups."""
        # Build entry ID map
        self._entry_id_map = {}
        for entry in self.encyclopedia.entries:
            entry_id = self._get_entry_id(entry)
            self._entry_id_map[entry_id] = entry
        
        # Build Wikipedia link index (inverted index)
        self._wikipedia_link_index = {}
        for entry in self.encyclopedia.entries:
            entry_id = self._get_entry_id(entry)
            links = self.wikipedia_extractor.extract_links_from_description(
                entry.get('description_html', '')
            )
            for link in links:
                url = link.get('url', '')
                if url:
                    if url not in self._wikipedia_link_index:
                        self._wikipedia_link_index[url] = []
                    self._wikipedia_link_index[url].append(entry_id)
    
    def _add_entry_nodes(self, graph: nx.DiGraph):
        """Add nodes for all encyclopedia entries."""
        for entry in self.encyclopedia.entries:
            node_id = self._get_entry_id(entry)
            
            # Node attributes
            node_data = {
                'wikidata_id': entry.get('wikidata_id', ''),
                'term': entry.get('term', ''),
                'canonical_term': entry.get('canonical_term', ''),
                'wikipedia_url': entry.get('wikipedia_url', ''),
                'description': entry.get('description', '')[:200] if entry.get('description') else '',
                'entry_type': 'entry',
                'node_type': 'entity'
            }
            
            graph.add_node(node_id, **node_data)
    
    def _add_wikipedia_links(self, graph: nx.DiGraph):
        """Add edges from Wikipedia description links."""
        for entry in self.encyclopedia.entries:
            source_id = self._get_entry_id(entry)
            
            links = self.wikipedia_extractor.extract_links_from_description(
                entry.get('description_html', '')
            )
            
            for link in links:
                target_entry = self.wikipedia_extractor.find_target_entry(
                    link['url'],
                    self.encyclopedia
                )
                
                if target_entry:
                    target_id = self._get_entry_id(target_entry)
                    
                    # Count occurrences
                    count = self.wikipedia_extractor.count_link_occurrences(entry, target_entry)
                    
                    # Add edge
                    graph.add_edge(
                        source_id,
                        target_id,
                        relationship_type='wikipedia_link',
                        weight=min(count / 10.0, 1.0),  # Normalize: max 10 links = weight 1.0
                        link_count=count,
                        link_text=link.get('text', '')
                    )
                else:
                    # External entity - add as node if not exists
                    normalized_url = self.wikipedia_extractor._normalize_wikipedia_url(link['url'])
                    if normalized_url:
                        external_id = f"external_{normalized_url}"
                        if external_id not in graph:
                            graph.add_node(
                                external_id,
                                wikidata_id='',
                                term=link.get('target_term', ''),
                                wikipedia_url=normalized_url,
                                entry_type='external',
                                node_type='entity'
                            )
                        
                        # Add edge to external entity
                        count = self.wikipedia_extractor.count_link_occurrences(entry, {'wikipedia_url': normalized_url})
                        graph.add_edge(
                            source_id,
                            external_id,
                            relationship_type='wikipedia_link',
                            weight=min(count / 10.0, 1.0),
                            link_count=count,
                            link_text=link.get('text', '')
                        )
    
    def _add_wikidata_ancestry(self, graph: nx.DiGraph):
        """Add Wikidata ancestry relationships (P31, P279)."""
        for entry in self.encyclopedia.entries:
            source_id = self._get_entry_id(entry)
            
            relationships = self.wikidata_extractor.extract_ancestry_relationships(entry)
            
            for rel in relationships:
                target_id = rel['target_id']
                
                # Add target node if it doesn't exist (external entity)
                if target_id not in graph:
                    graph.add_node(
                        target_id,
                        wikidata_id=target_id,
                        term='',  # Could fetch from Wikidata if needed
                        entry_type='external',
                        node_type='entity'
                    )
                
                # Add edge
                graph.add_edge(
                    source_id,
                    target_id,
                    relationship_type=rel['property_id'],
                    property_id=rel['property_id'],
                    weight=1.0,
                    property_label=rel.get('property_label', '')
                )
    
    def _add_wikidata_parts(self, graph: nx.DiGraph):
        """Add Wikidata part-whole relationships (P527, P361, P2670)."""
        for entry in self.encyclopedia.entries:
            source_id = self._get_entry_id(entry)
            
            relationships = self.wikidata_extractor.extract_part_relationships(entry)
            
            for rel in relationships:
                target_id = rel['target_id']
                
                # Add target node if it doesn't exist (external entity)
                if target_id not in graph:
                    graph.add_node(
                        target_id,
                        wikidata_id=target_id,
                        term='',
                        entry_type='external',
                        node_type='entity'
                    )
                
                # Add edge
                graph.add_edge(
                    source_id,
                    target_id,
                    relationship_type=rel['property_id'],
                    property_id=rel['property_id'],
                    weight=1.0,
                    direction=rel.get('direction', '')
                )
    
    def _add_shared_properties(self, graph: nx.DiGraph):
        """Add edges for entries sharing Wikidata properties."""
        entries = self.encyclopedia.entries
        
        # Compare all pairs
        for i, entry1 in enumerate(entries):
            source_id = self._get_entry_id(entry1)
            
            for entry2 in entries[i+1:]:
                target_id = self._get_entry_id(entry2)
                
                # Find shared properties
                shared = self.wikidata_extractor.find_shared_properties(entry1, entry2)
                
                if shared:
                    # Group by property
                    shared_by_property = {}
                    for prop in shared:
                        prop_id = prop['property_id']
                        if prop_id not in shared_by_property:
                            shared_by_property[prop_id] = []
                        shared_by_property[prop_id].append(prop['value_id'])
                    
                    # Add edge for each shared property
                    for prop_id, value_ids in shared_by_property.items():
                        weight = min(len(value_ids) / 5.0, 1.0)  # Normalize: max 5 shared = weight 1.0
                        
                        graph.add_edge(
                            source_id,
                            target_id,
                            relationship_type=f'shared_property_{prop_id}',
                            property_id=prop_id,
                            weight=weight,
                            shared_values=value_ids,
                            shared_count=len(value_ids)
                        )
    
    def _add_shared_values(self, graph: nx.DiGraph):
        """Add edges for entries sharing Wikidata property values."""
        entries = self.encyclopedia.entries
        
        # Compare all pairs
        for i, entry1 in enumerate(entries):
            source_id = self._get_entry_id(entry1)
            
            wikidata_id1 = entry1.get('wikidata_id', '')
            if not wikidata_id1 or wikidata_id1 in ('', 'no_wikidata_id', 'invalid_wikidata_id'):
                continue
            
            properties1 = self.wikidata_extractor.fetch_wikidata_properties(wikidata_id1)
            
            # Collect all value Q IDs from entry1
            values1 = set()
            for prop_values in properties1.values():
                values1.update([v for v in prop_values if v.startswith('Q')])
            
            for entry2 in entries[i+1:]:
                target_id = self._get_entry_id(entry2)
                
                wikidata_id2 = entry2.get('wikidata_id', '')
                if not wikidata_id2 or wikidata_id2 in ('', 'no_wikidata_id', 'invalid_wikidata_id'):
                    continue
                
                properties2 = self.wikidata_extractor.fetch_wikidata_properties(wikidata_id2)
                
                # Collect all value Q IDs from entry2
                values2 = set()
                for prop_values in properties2.values():
                    values2.update([v for v in prop_values if v.startswith('Q')])
                
                # Find shared values
                shared_values = values1 & values2
                
                if shared_values:
                    weight = min(len(shared_values) / 5.0, 1.0)  # Normalize
                    
                    graph.add_edge(
                        source_id,
                        target_id,
                        relationship_type='shared_value',
                        weight=weight,
                        shared_values=list(shared_values),
                        value_count=len(shared_values)
                    )
    
    def _get_entry_id(self, entry: Dict) -> str:
        """
        Get unique identifier for entry (prefer Wikidata ID, fallback to term).
        
        Args:
            entry: Entry dict
            
        Returns:
            Unique identifier string
        """
        wikidata_id = entry.get('wikidata_id', '')
        if wikidata_id and wikidata_id not in ('', 'no_wikidata_id', 'invalid_wikidata_id'):
            return wikidata_id
        
        # Fallback to term (normalized)
        term = entry.get('term', entry.get('canonical_term', ''))
        if term:
            return f"term_{term.lower().replace(' ', '_')}"
        
        # Last resort: use index
        return f"entry_{id(entry)}"
