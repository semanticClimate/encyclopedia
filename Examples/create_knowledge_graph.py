#!/usr/bin/env python3
"""
Create knowledge graph from encyclopedia.

This script creates a knowledge graph from an encyclopedia HTML file,
extracting relationships from Wikipedia descriptions and Wikidata properties.

Usage:
    # Create GraphML graph with all relationships
    python Examples/create_knowledge_graph.py \
        --input encyclopedia.html \
        --output knowledge_graph.graphml \
        --format graphml \
        --include-wikipedia \
        --include-wikidata
    
    # Create GEXF graph (for Gephi) with only Wikipedia links
    python Examples/create_knowledge_graph.py \
        --input encyclopedia.html \
        --output graph.gexf \
        --format gexf \
        --include-wikipedia
    
    # Create JSON graph with minimum weight filter
    python Examples/create_knowledge_graph.py \
        --input encyclopedia.html \
        --output graph.json \
        --format json \
        --include-wikipedia \
        --include-wikidata \
        --min-weight 0.1
    
    # Create RDF/Turtle graph
    python Examples/create_knowledge_graph.py \
        --input encyclopedia.html \
        --output graph.ttl \
        --format rdf \
        --include-wikidata

Date: March 2, 2026 (system date)
"""

import argparse
from pathlib import Path

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.knowledge_graph import KnowledgeGraphBuilder, GraphExporter


def main():
    """Main function for creating knowledge graph."""
    parser = argparse.ArgumentParser(
        description='Create knowledge graph from encyclopedia',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--input',
        type=Path,
        required=True,
        help='Input encyclopedia HTML file'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Output graph file'
    )
    
    parser.add_argument(
        '--format',
        choices=['graphml', 'gexf', 'json', 'rdf'],
        default='graphml',
        help='Output format (default: graphml)'
    )
    
    parser.add_argument(
        '--include-wikipedia',
        action='store_true',
        help='Include Wikipedia description links'
    )
    
    parser.add_argument(
        '--include-wikidata',
        action='store_true',
        help='Include Wikidata relationships (ancestry, parts, shared properties)'
    )
    
    parser.add_argument(
        '--min-weight',
        type=float,
        default=0.0,
        help='Minimum edge weight to include (default: 0.0, include all)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed progress'
    )
    
    args = parser.parse_args()
    
    # Validate input file
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    # Determine which relationship types to include
    # If neither flag is set, include all by default
    include_wikipedia = args.include_wikipedia
    include_wikidata = args.include_wikidata
    
    if not include_wikipedia and not include_wikidata:
        include_wikipedia = True
        include_wikidata = True
        if args.verbose:
            print("No relationship types specified, including all by default")
    
    # Load encyclopedia
    if args.verbose:
        print(f"Loading encyclopedia from {args.input}...")
    
    try:
        encyclopedia = AmiEncyclopedia()
        encyclopedia.create_from_html_file(args.input)
        
        if args.verbose:
            print(f"✓ Loaded {len(encyclopedia.entries)} entries")
    except Exception as e:
        print(f"Error loading encyclopedia: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Build graph
    if args.verbose:
        print("Building knowledge graph...")
        print(f"  - Wikipedia links: {include_wikipedia}")
        print(f"  - Wikidata relationships: {include_wikidata}")
    
    try:
        builder = KnowledgeGraphBuilder(encyclopedia)
        graph = builder.build_graph(
            include_wikipedia_links=include_wikipedia,
            include_wikidata_ancestry=include_wikidata,
            include_wikidata_parts=include_wikidata,
            include_shared_properties=include_wikidata,
            include_shared_values=include_wikidata
        )
        
        print(f"✓ Graph created: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        
        # Filter by minimum weight if specified
        if args.min_weight > 0.0:
            initial_edges = graph.number_of_edges()
            edges_to_remove = [
                (u, v) for u, v, d in graph.edges(data=True)
                if d.get('weight', 0.0) < args.min_weight
            ]
            graph.remove_edges_from(edges_to_remove)
            
            if args.verbose:
                print(f"  Filtered: {initial_edges} → {graph.number_of_edges()} edges (min weight: {args.min_weight})")
        
    except Exception as e:
        print(f"Error building graph: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Determine output file path (ensure it's in temp/ directory)
    input_stem = args.input.stem
    output_path = Path(args.output)
    if len(output_path.parts) > 0 and output_path.parts[0] == "temp":
        # Already under temp/, use as-is but ensure directory exists
        output_file = args.output
        output_file.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Create output directory based on input file name
        output_dir = Path("temp", "knowledge_graphs", input_stem)
        output_dir.mkdir(parents=True, exist_ok=True)
        # Use input stem + format for output filename
        format_extensions = {
            'graphml': '.graphml',
            'gexf': '.gexf',
            'json': '.json',
            'rdf': '.ttl'
        }
        ext = format_extensions.get(args.format, args.output.suffix)
        output_file = Path(output_dir, f"{input_stem}{ext}")
    
    # Adjust output file extension for RDF format if needed
    if args.format == 'rdf' and output_file.suffix != '.ttl':
        output_file = output_file.with_suffix('.ttl')
    
    # Export graph
    if args.verbose:
        print(f"Exporting graph to {output_file} ({args.format} format)...")
    
    try:
        exporter = GraphExporter()
        
        if args.format == 'graphml':
            exporter.export_graphml(graph, output_file)
        elif args.format == 'gexf':
            exporter.export_gexf(graph, output_file)
        elif args.format == 'json':
            exporter.export_json(graph, output_file)
        elif args.format == 'rdf':
            exporter.export_rdf_turtle(graph, output_file)
        
        print(f"✓ Graph exported successfully to {output_file}")
        print(f"  Format: {args.format}")
        print(f"  Nodes: {graph.number_of_nodes()}")
        print(f"  Edges: {graph.number_of_edges()}")
        
        # Show edge type breakdown if verbose
        if args.verbose:
            edge_types = {}
            for source, target, edge_data in graph.edges(data=True):
                rel_type = edge_data.get('relationship_type', 'unknown')
                edge_types[rel_type] = edge_types.get(rel_type, 0) + 1
            
            print("\n  Edge types:")
            for rel_type, count in sorted(edge_types.items(), key=lambda x: -x[1]):
                print(f"    {rel_type}: {count}")
        
        return 0
        
    except Exception as e:
        print(f"Error exporting graph: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
