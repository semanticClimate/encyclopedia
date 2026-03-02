#!/usr/bin/env python3
"""
Visualize knowledge graph using NetworkX and matplotlib.

This script demonstrates various ways to visualize knowledge graphs
created from encyclopedia entries.

Date: March 2, 2026 (system date)
"""

import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
import json
import sys
import re


def clean_node_label(node_id: str, node_data: dict) -> str:
    """
    Get clean label for node, avoiding URL stems and preferring human-readable terms.
    
    Args:
        node_id: Node identifier (may be URL stem or Wikidata ID)
        node_data: Node data dictionary
        
    Returns:
        Clean label string
    """
    # Prefer term fields
    term = node_data.get('term', '') or node_data.get('canonical_term', '')
    
    if term and term.strip():
        # Use term if available
        return term.strip()
    
    # If node_id looks like a Wikidata ID (Q123), use it as-is
    if node_id.startswith('Q') and node_id[1:].isdigit():
        return node_id
    
    # If node_id looks like a URL stem (contains /wiki/ or http), extract term
    if '/wiki/' in node_id or 'wikipedia.org' in node_id or node_id.startswith('http'):
        # Try to extract term from URL
        if '/wiki/' in node_id:
            term_part = node_id.split('/wiki/')[-1].split('#')[0].split('?')[0]
            # Replace underscores with spaces and decode
            term_part = term_part.replace('_', ' ').replace('%20', ' ')
            if term_part:
                return term_part
    
    # If node_id starts with 'term_' or 'external_', remove prefix
    if node_id.startswith('term_'):
        return node_id[5:].replace('_', ' ')
    if node_id.startswith('external_'):
        # Extract from external URL if possible
        remaining = node_id[9:]
        if '/wiki/' in remaining:
            term_part = remaining.split('/wiki/')[-1].split('#')[0].split('?')[0]
            term_part = term_part.replace('_', ' ').replace('%20', ' ')
            if term_part:
                return term_part
        return remaining.replace('_', ' ')
    
    # Remove any URL-like patterns
    cleaned = re.sub(r'https?://[^\s]+', '', node_id)
    cleaned = re.sub(r'/[^/\s]+', '', cleaned)  # Remove path segments
    
    # Replace underscores with spaces
    cleaned = cleaned.replace('_', ' ')
    
    # If result is empty or just whitespace, use a generic label
    if not cleaned.strip():
        return f"Node {node_id[:10]}"
    
    return cleaned.strip()


def load_graph(graph_file: Path):
    """
    Load graph from file (supports GraphML, JSON, GEXF).
    
    Args:
        graph_file: Path to graph file
        
    Returns:
        NetworkX DiGraph
    """
    suffix = graph_file.suffix.lower()
    
    if suffix == '.graphml':
        return nx.read_graphml(str(graph_file))
    elif suffix == '.gexf':
        return nx.read_graphml(str(graph_file))  # GEXF is also XML-based
    elif suffix == '.json':
        with open(graph_file, 'r') as f:
            data = json.load(f)
        graph = nx.DiGraph()
        # Add nodes
        for node in data['nodes']:
            node_id = node.pop('id')
            graph.add_node(node_id, **node)
        # Add edges
        for edge in data['edges']:
            graph.add_edge(edge['source'], edge['target'], **{k: v for k, v in edge.items() 
                                                              if k not in ('source', 'target')})
        return graph
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def visualize_basic(graph: nx.DiGraph, output_file: Path = None):
    """
    Basic visualization with default layout.
    
    Args:
        graph: NetworkX graph
        output_file: Optional path to save figure
    """
    plt.figure(figsize=(12, 8))
    
    # Use spring layout
    pos = nx.spring_layout(graph, k=1, iterations=50)
    
    # Create clean labels
    labels = {n: clean_node_label(n, d) for n, d in graph.nodes(data=True)}
    
    # Draw graph
    nx.draw(graph, pos, 
            labels=labels,
            node_color='lightblue',
            node_size=500,
            font_size=8,
            font_weight='bold',
            arrows=True,
            arrowsize=20,
            edge_color='gray',
            width=1.0)
    
    plt.title("Knowledge Graph - Basic Visualization", fontsize=16)
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved to: {output_file}")
    else:
        plt.show()


def visualize_by_entry_type(graph: nx.DiGraph, output_file: Path = None):
    """
    Visualize graph with nodes colored by entry type (entry vs external).
    
    Args:
        graph: NetworkX graph
        output_file: Optional path to save figure
    """
    plt.figure(figsize=(14, 10))
    
    # Use spring layout
    pos = nx.spring_layout(graph, k=1, iterations=50)
    
    # Separate nodes by type
    entry_nodes = [n for n, d in graph.nodes(data=True) 
                   if d.get('entry_type') == 'entry']
    external_nodes = [n for n, d in graph.nodes(data=True) 
                      if d.get('entry_type') == 'external']
    
    # Draw external nodes first (background)
    if external_nodes:
        nx.draw_networkx_nodes(graph, pos, 
                              nodelist=external_nodes,
                              node_color='lightgray',
                              node_size=300,
                              alpha=0.6,
                              label='External Entities')
    
    # Draw entry nodes (foreground)
    if entry_nodes:
        nx.draw_networkx_nodes(graph, pos,
                              nodelist=entry_nodes,
                              node_color='lightblue',
                              node_size=800,
                              alpha=0.8,
                              label='Encyclopedia Entries')
    
    # Draw edges
    nx.draw_networkx_edges(graph, pos,
                          edge_color='gray',
                          width=0.5,
                          alpha=0.5,
                          arrows=True,
                          arrowsize=15)
    
    # Draw labels for entry nodes only (to reduce clutter)
    labels = {n: clean_node_label(n, d)[:20] for n, d in graph.nodes(data=True) 
              if d.get('entry_type') == 'entry'}
    nx.draw_networkx_labels(graph, pos, labels, font_size=7)
    
    plt.title("Knowledge Graph - Colored by Entry Type", fontsize=16)
    plt.legend(loc='upper right')
    plt.axis('off')
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved to: {output_file}")
    else:
        plt.show()


def visualize_by_relationship_type(graph: nx.DiGraph, output_file: Path = None):
    """
    Visualize graph with edges colored by relationship type.
    
    Args:
        graph: NetworkX graph
        output_file: Optional path to save figure
    """
    plt.figure(figsize=(14, 10))
    
    # Use spring layout
    pos = nx.spring_layout(graph, k=1, iterations=50)
    
    # Draw nodes
    nx.draw_networkx_nodes(graph, pos,
                          node_color='lightblue',
                          node_size=500,
                          alpha=0.7)
    
    # Group edges by relationship type
    edge_types = {}
    for u, v, d in graph.edges(data=True):
        rel_type = d.get('relationship_type', 'unknown')
        if rel_type not in edge_types:
            edge_types[rel_type] = []
        edge_types[rel_type].append((u, v))
    
    # Color map for different relationship types
    colors = plt.cm.tab10(range(len(edge_types)))
    color_map = dict(zip(edge_types.keys(), colors))
    
    # Draw edges by type
    for rel_type, edges in edge_types.items():
        nx.draw_networkx_edges(graph, pos,
                              edgelist=edges,
                              edge_color=[color_map[rel_type]],
                              width=1.5,
                              alpha=0.6,
                              arrows=True,
                              arrowsize=15,
                              label=rel_type)
    
    # Draw labels
    labels = {n: clean_node_label(n, d)[:15] for n, d in graph.nodes(data=True) 
              if d.get('entry_type') == 'entry'}
    nx.draw_networkx_labels(graph, pos, labels, font_size=7)
    
    plt.title("Knowledge Graph - Colored by Relationship Type", fontsize=16)
    plt.legend(loc='upper right', fontsize=8)
    plt.axis('off')
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved to: {output_file}")
    else:
        plt.show()


def visualize_weighted(graph: nx.DiGraph, output_file: Path = None):
    """
    Visualize graph with edge widths proportional to weight.
    
    Args:
        graph: NetworkX graph
        output_file: Optional path to save figure
    """
    plt.figure(figsize=(14, 10))
    
    # Use spring layout
    pos = nx.spring_layout(graph, k=1, iterations=50)
    
    # Draw nodes
    nx.draw_networkx_nodes(graph, pos,
                          node_color='lightblue',
                          node_size=500,
                          alpha=0.7)
    
    # Get edge weights
    edges = graph.edges(data=True)
    weights = [d.get('weight', 1.0) for u, v, d in edges]
    
    # Normalize weights for visualization (min 0.5, max 5.0)
    if weights:
        min_weight = min(weights)
        max_weight = max(weights)
        if max_weight > min_weight:
            normalized_weights = [0.5 + 4.5 * (w - min_weight) / (max_weight - min_weight) 
                                 for w in weights]
        else:
            normalized_weights = [2.0] * len(weights)
    else:
        normalized_weights = [1.0] * len(edges)
    
    # Draw edges with varying widths
    nx.draw_networkx_edges(graph, pos,
                          edge_color='gray',
                          width=normalized_weights,
                          alpha=0.6,
                          arrows=True,
                          arrowsize=15)
    
    # Draw labels
    labels = {n: clean_node_label(n, d)[:15] for n, d in graph.nodes(data=True) 
              if d.get('entry_type') == 'entry'}
    nx.draw_networkx_labels(graph, pos, labels, font_size=7)
    
    plt.title("Knowledge Graph - Edge Widths Proportional to Weight", fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved to: {output_file}")
    else:
        plt.show()


def print_graph_statistics(graph: nx.DiGraph):
    """Print statistics about the graph."""
    print("\n" + "=" * 60)
    print("Graph Statistics")
    print("=" * 60)
    print(f"Nodes: {graph.number_of_nodes()}")
    print(f"Edges: {graph.number_of_edges()}")
    print(f"Directed: {graph.is_directed()}")
    
    # Node types
    entry_nodes = sum(1 for n, d in graph.nodes(data=True) 
                     if d.get('entry_type') == 'entry')
    external_nodes = graph.number_of_nodes() - entry_nodes
    print(f"\nNode Types:")
    print(f"  Encyclopedia entries: {entry_nodes}")
    print(f"  External entities: {external_nodes}")
    
    # Edge types
    edge_types = {}
    for u, v, d in graph.edges(data=True):
        rel_type = d.get('relationship_type', 'unknown')
        edge_types[rel_type] = edge_types.get(rel_type, 0) + 1
    
    print(f"\nEdge Types:")
    for rel_type, count in sorted(edge_types.items(), key=lambda x: -x[1]):
        print(f"  {rel_type}: {count}")
    
    # Sample nodes
    print(f"\nSample Nodes (first 10):")
    for i, (node_id, node_data) in enumerate(list(graph.nodes(data=True))[:10]):
        label = clean_node_label(node_id, node_data)
        entry_type = node_data.get('entry_type', 'N/A')
        print(f"  {node_id}: {label} ({entry_type})")
    
    # Sample edges
    print(f"\nSample Edges (first 10):")
    for i, (source, target, edge_data) in enumerate(list(graph.edges(data=True))[:10]):
        rel_type = edge_data.get('relationship_type', 'N/A')
        weight = edge_data.get('weight', 'N/A')
        print(f"  {source} -> {target}: {rel_type} (weight: {weight})")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Visualize knowledge graph using NetworkX',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--input',
        type=Path,
        required=True,
        help='Input graph file (GraphML, JSON, or GEXF)'
    )
    
    parser.add_argument(
        '--style',
        choices=['basic', 'entry-type', 'relationship-type', 'weighted'],
        default='basic',
        help='Visualization style (default: basic)'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        help='Output image file (if not specified, saves to temp/ directory)'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Print graph statistics'
    )
    
    args = parser.parse_args()
    
    # Load graph
    if not args.input.exists():
        print(f"Error: File not found: {args.input}")
        return 1
    
    print(f"Loading graph from {args.input}...")
    try:
        graph = load_graph(args.input)
        print(f"✓ Loaded graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    except Exception as e:
        print(f"Error loading graph: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Determine output file path
    if args.output:
        output_file = args.output
        # Ensure output is in temp/ if not explicitly specified elsewhere
        if not str(output_file).startswith('temp/'):
            # Extract input name for output directory
            input_stem = args.input.stem
            output_dir = Path("temp/visualizations") / input_stem
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / output_file.name
    else:
        # Create output directory based on input file name
        input_stem = args.input.stem
        output_dir = Path("temp/visualizations") / input_stem
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{input_stem}_{args.style}.png"
    
    # Print statistics if requested
    if args.stats:
        print_graph_statistics(graph)
    
    # Visualize
    print(f"\nVisualizing with style: {args.style}")
    
    try:
        if args.style == 'basic':
            visualize_basic(graph, output_file)
        elif args.style == 'entry-type':
            visualize_by_entry_type(graph, output_file)
        elif args.style == 'relationship-type':
            visualize_by_relationship_type(graph, output_file)
        elif args.style == 'weighted':
            visualize_weighted(graph, output_file)
        
        print(f"✓ Visualization saved to {output_file}")
    
    except Exception as e:
        print(f"Error visualizing graph: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
