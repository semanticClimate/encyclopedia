"""
Export knowledge graphs to various formats.

Date: March 2, 2026 (system date)
"""

from pathlib import Path
from typing import Dict, Any, List
import json
import networkx as nx


class GraphExporter:
    """Export graphs to various formats."""
    
    def export_graphml(self, graph: nx.DiGraph, output_path: Path) -> Path:
        """
        Export graph to GraphML format.
        
        GraphML doesn't support list types, so we convert lists to JSON strings.
        
        Args:
            graph: NetworkX graph
            output_path: Output file path
            
        Returns:
            Path to exported file
        """
        # Create a copy of the graph to avoid modifying the original
        graph_copy = graph.copy()
        
        # Convert list attributes to JSON strings for GraphML compatibility
        self._convert_lists_to_strings(graph_copy)
        
        nx.write_graphml(graph_copy, str(output_path), encoding='utf-8')
        return output_path
    
    def _convert_lists_to_strings(self, graph: nx.DiGraph):
        """
        Convert list attributes to JSON strings for format compatibility.
        
        GraphML and GEXF don't support list types, so we serialize them as JSON strings.
        This preserves the data while making it compatible with XML-based formats.
        
        Args:
            graph: NetworkX graph (modified in place)
        """
        # Convert node attributes
        for node_id, node_data in graph.nodes(data=True):
            for key, value in list(node_data.items()):
                if isinstance(value, list):
                    node_data[key] = json.dumps(value)
        
        # Convert edge attributes
        for source, target, edge_data in graph.edges(data=True):
            for key, value in list(edge_data.items()):
                if isinstance(value, list):
                    edge_data[key] = json.dumps(value)
    
    def export_gexf(self, graph: nx.DiGraph, output_path: Path) -> Path:
        """
        Export graph to GEXF format (for Gephi).
        
        GEXF doesn't support list types, so we convert lists to JSON strings.
        
        Args:
            graph: NetworkX graph
            output_path: Output file path
            
        Returns:
            Path to exported file
        """
        # Create a copy of the graph to avoid modifying the original
        graph_copy = graph.copy()
        
        # Convert list attributes to JSON strings for GEXF compatibility
        self._convert_lists_to_strings(graph_copy)
        
        nx.write_gexf(graph_copy, str(output_path), encoding='utf-8')
        return output_path
    
    def export_json(self, graph: nx.DiGraph, output_path: Path) -> Path:
        """
        Export graph to JSON format.
        
        Args:
            graph: NetworkX graph
            output_path: Output file path
            
        Returns:
            Path to exported file
        """
        # Convert graph to JSON-serializable format
        data = {
            'nodes': [
                {
                    'id': node_id,
                    **node_data
                }
                for node_id, node_data in graph.nodes(data=True)
            ],
            'edges': [
                {
                    'source': source,
                    'target': target,
                    **edge_data
                }
                for source, target, edge_data in graph.edges(data=True)
            ]
        }
        
        # Write JSON
        output_path.write_text(
            json.dumps(data, indent=2, default=str),
            encoding='utf-8'
        )
        
        return output_path
    
    def export_rdf_turtle(self, graph: nx.DiGraph, output_path: Path) -> Path:
        """
        Export graph to RDF/Turtle format.
        
        Args:
            graph: NetworkX graph
            output_path: Output file path
            
        Returns:
            Path to exported file
        """
        lines = []
        
        # Add prefixes
        lines.append("@prefix wd: <http://www.wikidata.org/entity/> .")
        lines.append("@prefix wdt: <http://www.wikidata.org/prop/direct/> .")
        lines.append("@prefix kg: <http://example.org/kg/> .")
        lines.append("")
        
        # Add nodes
        for node_id, node_data in graph.nodes(data=True):
            wikidata_id = node_data.get('wikidata_id', '')
            term = node_data.get('term', '')
            
            if wikidata_id and wikidata_id.startswith('Q'):
                # Use Wikidata ID as subject
                subject = f"wd:{wikidata_id}"
            else:
                # Use node ID as subject (with kg: prefix)
                subject = f"kg:{node_id.replace(' ', '_')}"
            
            # Add term
            if term:
                lines.append(f"{subject} kg:term \"{term}\" .")
            
            # Add Wikipedia URL
            wikipedia_url = node_data.get('wikipedia_url', '')
            if wikipedia_url:
                lines.append(f"{subject} kg:wikipedia_url \"{wikipedia_url}\" .")
        
        lines.append("")
        
        # Add edges
        for source, target, edge_data in graph.edges(data=True):
            # Get source and target subjects
            source_data = graph.nodes[source]
            target_data = graph.nodes[target]
            
            source_wikidata = source_data.get('wikidata_id', '')
            target_wikidata = target_data.get('wikidata_id', '')
            
            if source_wikidata and source_wikidata.startswith('Q'):
                source_subject = f"wd:{source_wikidata}"
            else:
                source_subject = f"kg:{source.replace(' ', '_')}"
            
            if target_wikidata and target_wikidata.startswith('Q'):
                target_subject = f"wd:{target_wikidata}"
            else:
                target_subject = f"kg:{target.replace(' ', '_')}"
            
            # Get relationship type
            relationship_type = edge_data.get('relationship_type', '')
            property_id = edge_data.get('property_id', '')
            
            if property_id and property_id.startswith('P'):
                # Use Wikidata property
                predicate = f"wdt:{property_id}"
            elif relationship_type == 'wikipedia_link':
                predicate = "kg:wikipedia_link"
            elif relationship_type.startswith('shared_'):
                predicate = f"kg:{relationship_type}"
            else:
                predicate = f"kg:{relationship_type}"
            
            # Add edge
            weight = edge_data.get('weight', 1.0)
            lines.append(f"{source_subject} {predicate} {target_subject} .")
            
            # Add weight if not 1.0
            if weight != 1.0:
                lines.append(f"{source_subject} kg:weight \"{weight}\"^^xsd:double .")
        
        # Write Turtle file
        output_path.write_text('\n'.join(lines), encoding='utf-8')
        
        return output_path
