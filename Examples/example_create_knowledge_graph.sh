#!/bin/bash
# Example script for creating knowledge graphs
# Date: March 2, 2026 (system date)

set -e  # Exit on error

echo "=== Knowledge Graph Creation Examples ==="
echo ""

# Check if we have an encyclopedia file
ENCYCLOPEDIA_FILE=""
if [ -f "encyclopedia_output.html" ]; then
    ENCYCLOPEDIA_FILE="encyclopedia_output.html"
    echo "✓ Found: encyclopedia_output.html"
elif [ -f "temp/test/encyclopedia/TestKnowledgeGraphBuilder/climate_encyclopedia.html" ]; then
    ENCYCLOPEDIA_FILE="temp/test/encyclopedia/TestKnowledgeGraphBuilder/climate_encyclopedia.html"
    echo "✓ Found test encyclopedia file"
else
    echo "⚠ No encyclopedia file found. Creating a small test encyclopedia first..."
    echo ""
    
    # Create a small test encyclopedia
    python -m encyclopedia.cli.versioned_editor create \
        --wordlist <(echo -e "climate change\ngreenhouse gas\ncarbon dioxide") \
        --output temp/example_encyclopedia.html \
        --title "Example Encyclopedia"
    
    echo ""
    echo "Adding Wikipedia descriptions..."
    python -m encyclopedia.cli.versioned_editor process \
        --input temp/example_encyclopedia.html \
        --feature wikipedia \
        --batch-size 3
    
    ENCYCLOPEDIA_FILE="temp/example_encyclopedia.html"
fi

echo ""
echo "Using encyclopedia file: $ENCYCLOPEDIA_FILE"
echo ""

# Create output directory
mkdir -p temp/examples/knowledge_graphs

echo "=== Example 1: GraphML Format (Standard) ==="
python -m encyclopedia.cli.versioned_editor graph \
    --input "$ENCYCLOPEDIA_FILE" \
    --output temp/examples/knowledge_graphs/example_graph.graphml \
    --format graphml \
    --include-wikipedia \
    --include-wikidata

echo ""
echo "✓ Created: temp/examples/knowledge_graphs/example_graph.graphml"
echo ""

echo "=== Example 2: GEXF Format (for Gephi) ==="
python -m encyclopedia.cli.versioned_editor graph \
    --input "$ENCYCLOPEDIA_FILE" \
    --output temp/examples/knowledge_graphs/example_graph.gexf \
    --format gexf \
    --include-wikipedia \
    --include-wikidata

echo ""
echo "✓ Created: temp/examples/knowledge_graphs/example_graph.gexf"
echo ""

echo "=== Example 3: JSON Format ==="
python Examples/create_knowledge_graph.py \
    --input "$ENCYCLOPEDIA_FILE" \
    --output temp/examples/knowledge_graphs/example_graph.json \
    --format json \
    --include-wikipedia \
    --include-wikidata \
    --verbose

echo ""
echo "✓ Created: temp/examples/knowledge_graphs/example_graph.json"
echo ""

echo "=== Example 4: RDF/Turtle Format ==="
python Examples/create_knowledge_graph.py \
    --input "$ENCYCLOPEDIA_FILE" \
    --output temp/examples/knowledge_graphs/example_graph.ttl \
    --format rdf \
    --include-wikidata \
    --verbose

echo ""
echo "✓ Created: temp/examples/knowledge_graphs/example_graph.ttl"
echo ""

echo "=== Example 5: Filtered Graph (High-Weight Edges Only) ==="
python Examples/create_knowledge_graph.py \
    --input "$ENCYCLOPEDIA_FILE" \
    --output temp/examples/knowledge_graphs/filtered_graph.graphml \
    --format graphml \
    --include-wikipedia \
    --min-weight 0.2 \
    --verbose

echo ""
echo "✓ Created: temp/examples/knowledge_graphs/filtered_graph.graphml"
echo ""

echo "=== Summary ==="
echo "All example graphs created in: temp/examples/knowledge_graphs/"
echo ""
echo "Files created:"
ls -lh temp/examples/knowledge_graphs/ 2>/dev/null || echo "  (check temp/examples/knowledge_graphs/ directory)"
echo ""
echo "To visualize:"
echo "  - GraphML: Open with yEd, Cytoscape, or NetworkX"
echo "  - GEXF: Open with Gephi (https://gephi.org/)"
echo "  - JSON: Use with web visualization tools or NetworkX"
echo "  - RDF/Turtle: Use with RDF tools or SPARQL endpoints"
