"""
Create bipartite network graph from encyclopedia shared links
Output formats: GEXF (recommended), GraphML, JSON, CSV
"""

import networkx as nx
import json
from pathlib import Path
from typing import Dict, Set, Tuple

def create_bipartite_graph_from_json(json_file: Path) -> Tuple[nx.Graph, Set[str], Set[str]]:
    """
    Load shared links JSON and create bipartite network graph.
    
    Args:
        json_file: Path to shared_article_links.json
        
    Returns:
        Tuple of (Graph, entry_names, target_articles)
    """
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Create bipartite graph
    B = nx.Graph()
    entry_names = set()
    target_articles = set()
    
    # Add nodes and edges
    for link_url, link_info in data['shared_article_links'].items():
        article_name = link_info['article_name']
        target_articles.add(article_name)
        
        # Add target node with metadata
        if not B.has_node(article_name):
            B.add_node(article_name, bipartite=1, node_type='target', 
                      occurrence_count=link_info['occurrence_count'])
        
        for entry in link_info['entries']:
            entry_term = entry['term']
            entry_names.add(entry_term)
            
            # Add entry node
            if not B.has_node(entry_term):
                B.add_node(entry_term, bipartite=0, node_type='entry')
            
            # Add edge with weight
            if B.has_edge(entry_term, article_name):
                B[entry_term][article_name]['weight'] += 1
            else:
                B.add_edge(entry_term, article_name, weight=1,
                           link_text=entry.get('link_text', ''),
                           title=entry.get('title', ''))
    
    return B, entry_names, target_articles


def export_to_multiple_formats(graph: nx.Graph, base_path: Path):
    """Export network graph to multiple formats"""
    
    # 1. GEXF (recommended for Gephi)
    gexf_file = Path(str(base_path).replace('.json', '.gexf'))
    nx.write_gexf(graph, gexf_file)
    print(f"✓ GEXF format: {gexf_file}")
    
    # 2. GraphML (generic graph format)
    graphml_file = Path(str(base_path).replace('.json', '.graphml'))
    nx.write_graphml(graph, graphml_file)
    print(f"✓ GraphML format: {graphml_file}")
    
    # 3. Edge list CSV
    csv_file = Path(str(base_path).replace('.json', '_edges.csv'))
    nx.write_edgelist(graph, csv_file, delimiter=',')
    print(f"✓ Edge list CSV: {csv_file}")
    
    # 4. Multi-line adjacency list
    adjlist_file = Path(str(base_path).replace('.json', '_adjlist.txt'))
    nx.write_multiline_adjlist(graph, adjlist_file)
    print(f"✓ Adjacency list: {adjlist_file}")
    
    # 5. Network statistics
    stats_file = Path(str(base_path).replace('.json', '_network_stats.json'))
    stats = {
        'total_nodes': graph.number_of_nodes(),
        'total_edges': graph.number_of_edges(),
        'is_bipartite': nx.is_bipartite(graph),
        'density': nx.density(graph),
        'average_clustering': nx.average_clustering(graph),
        'number_connected_components': nx.number_connected_components(graph),
    }
    
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✓ Network statistics: {stats_file}")
    
    return gexf_file, graphml_file, csv_file, adjlist_file, stats_file


def create_filtered_graph(json_file: Path, min_occurrences: int = 5) -> nx.Graph:
    """Create filtered graph with only highly-shared articles"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    B = nx.Graph()
    entry_names = set()
    target_articles = set()
    
    # Filter by minimum occurrences
    for link_url, link_info in data['shared_article_links'].items():
        if link_info['occurrence_count'] >= min_occurrences:
            article_name = link_info['article_name']
            target_articles.add(article_name)
            
            B.add_node(article_name, bipartite=1, node_type='target',
                      occurrence_count=link_info['occurrence_count'])
            
            for entry in link_info['entries']:
                entry_term = entry['term']
                entry_names.add(entry_term)
                
                if not B.has_node(entry_term):
                    B.add_node(entry_term, bipartite=0, node_type='entry')
                
                if B.has_edge(entry_term, article_name):
                    B[entry_term][article_name]['weight'] += 1
                else:
                    B.add_edge(entry_term, article_name, weight=1)
    
    return B, entry_names, target_articles


def main():
    """Main function to create network graphs from existing JSON files"""
    
    # Find all shared links JSON files
    output_dir = Path('temp/text_links_output')
    json_files = list(output_dir.glob('shared_article_links_*.json'))
    
    print(f"Found {len(json_files)} shared links JSON files")
    
    for json_file in json_files:
        try:
            # Validate file structure
            with open(json_file, 'r') as f:
                data = json.load(f)
            if 'shared_article_links' not in data:
                print(f"Skipping {json_file.name} - not a shared links file")
                continue
        except json.JSONDecodeError:
            print(f"Skipping {json_file.name} - not valid JSON")
            continue
        
        print(f"\nProcessing: {json_file}")
        
        # Create full bipartite graph
        B, entries, targets = create_bipartite_graph_from_json(json_file)
        print(f"Nodes: {B.number_of_nodes()} (entries: {len(entries)}, targets: {len(targets)})")
        print(f"Edges: {B.number_of_edges()}")
        
        # Export to all formats
        export_to_multiple_formats(B, json_file)
        
        # Create filtered versions (only highly-shared articles)
        for min_occ in [10, 20]:
            B_filtered, _, _ = create_filtered_graph(json_file, min_occurrences=min_occ)
            if B_filtered.number_of_nodes() > 0:
                filtered_file = json_file.parent / json_file.stem
                filtered_gexf = f"{filtered_file}_filtered_{min_occ}.gexf"
                print(f"\nFiltered graph (min {min_occ} occurrences):")
                print(f"Nodes: {B_filtered.number_of_nodes()}, Edges: {B_filtered.number_of_edges()}")
                nx.write_gexf(B_filtered, filtered_gexf)
                print(f"✓ Filtered GEXF: {filtered_gexf}")


if __name__ == '__main__':
    main()

