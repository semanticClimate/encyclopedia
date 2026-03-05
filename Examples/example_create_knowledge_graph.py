#!/usr/bin/env python3
"""
Quick example script for creating knowledge graphs.

This script demonstrates how to create knowledge graphs from an encyclopedia.
It will use an existing encyclopedia file or create a small test one.

Date: 2025-03-05 (system date)
"""

from pathlib import Path

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.knowledge_graph import KnowledgeGraphBuilder, GraphExporter


def find_encyclopedia_file():
    """Find an existing encyclopedia file or create a test one."""
    # Check common locations
    possible_files = [
        Path("encyclopedia_output.html"),
        Path("temp", "test", "encyclopedia", "TestKnowledgeGraphBuilder", "climate_encyclopedia.html"),
        Path("temp", "example_encyclopedia.html"),
    ]
    
    for file_path in possible_files:
        if file_path.exists():
            return file_path
    
    # Create a small test encyclopedia
    print("No encyclopedia file found. Creating a small test encyclopedia...")
    print()
    
    from Examples.create_encyclopedia_from_wordlist import create_encyclopedia_from_wordlist
    
    terms = ["climate change", "greenhouse gas", "carbon dioxide"]
    output_file = Path("temp", "example_encyclopedia.html")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    encyclopedia = create_encyclopedia_from_wordlist(
        terms,
        title="Example Encyclopedia",
        add_wikipedia=True,
        add_images=False,
        validate=False,
        verbose=True
    )
    
    encyclopedia.save_to_html_file(output_file)
    print(f"✓ Created: {output_file}")
    print()
    
    return output_file


def main():
    """Main example function."""
    print("=" * 60)
    print("Knowledge Graph Creation Example")
    print("=" * 60)
    print()
    
    # Find or create encyclopedia file
    encyclopedia_file = find_encyclopedia_file()
    print(f"Using encyclopedia file: {encyclopedia_file}")
    print()
    
    # Load encyclopedia
    print("Loading encyclopedia...")
    encyclopedia = AmiEncyclopedia()
    encyclopedia.create_from_html_file(encyclopedia_file)
    print(f"✓ Loaded {len(encyclopedia.entries)} entries")
    print()
    
    # Create output directory based on input file name
    input_stem = encyclopedia_file.stem
    output_dir = Path("temp", "knowledge_graphs", input_stem)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Example 1: GraphML format
    print("Example 1: Creating GraphML graph...")
    builder = KnowledgeGraphBuilder(encyclopedia)
    graph = builder.build_graph(
        include_wikipedia_links=True,
        include_wikidata_ancestry=True,
        include_wikidata_parts=True,
        include_shared_properties=True,
        include_shared_values=True
    )
    
    print(f"  Graph created: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    
    exporter = GraphExporter()
    graphml_file = Path(output_dir, f"{input_stem}.graphml")
    exporter.export_graphml(graph, graphml_file)
    print(f"  ✓ Exported to: {graphml_file}")
    print()
    
    # Example 2: JSON format
    print("Example 2: Creating JSON graph...")
    json_file = Path(output_dir, f"{input_stem}.json")
    exporter.export_json(graph, json_file)
    print(f"  ✓ Exported to: {json_file}")
    print()
    
    # Example 3: Show edge types
    print("Example 3: Edge type breakdown:")
    edge_types = {}
    for source, target, edge_data in graph.edges(data=True):
        rel_type = edge_data.get('relationship_type', 'unknown')
        edge_types[rel_type] = edge_types.get(rel_type, 0) + 1
    
    for rel_type, count in sorted(edge_types.items(), key=lambda x: -x[1]):
        print(f"  {rel_type}: {count} edges")
    print()
    
    # Example 4: Filtered graph (high-weight edges only)
    print("Example 4: Creating filtered graph (min weight 0.2)...")
    filtered_graph = graph.copy()
    edges_to_remove = [
        (u, v) for u, v, d in filtered_graph.edges(data=True)
        if d.get('weight', 0.0) < 0.2
    ]
    filtered_graph.remove_edges_from(edges_to_remove)
    
    print(f"  Filtered: {graph.number_of_edges()} → {filtered_graph.number_of_edges()} edges")
    
    filtered_file = Path(output_dir, f"{input_stem}_filtered.graphml")
    exporter.export_graphml(filtered_graph, filtered_file)
    print(f"  ✓ Exported to: {filtered_file}")
    print()
    
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"All graphs saved to: {output_dir}")
    print()
    print("Files created:")
    for file in sorted(output_dir.glob("*.graphml")) + sorted(output_dir.glob("*.json")):
        size_kb = file.stat().st_size / 1024
        print(f"  - {file.name} ({size_kb:.1f} KB)")
    print()
    print("To visualize:")
    print("  - GraphML: Open with yEd, Cytoscape, or use NetworkX")
    print("  - JSON: Use with web visualization tools or NetworkX")
    print()
    print("Example NetworkX visualization:")
    print(f"  import networkx as nx")
    print(f"  graph = nx.read_graphml('{graphml_file}')")
    print("  # Then visualize with matplotlib or other tools")


if __name__ == '__main__':
    main()
