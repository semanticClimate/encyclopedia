# Knowledge Graph Examples

**Date:** March 2, 2026 (system date)

## Quick Start Examples

### Option 1: Python Script (Recommended)

Run the example script that creates graphs in multiple formats:

```bash
python Examples/example_create_knowledge_graph.py
```

This script will:
1. Find or create a test encyclopedia
2. Create knowledge graphs in multiple formats
3. Show edge type breakdowns
4. Create filtered graphs

**Output:** Graphs saved to `temp/examples/knowledge_graphs/`

### Option 2: Shell Script

Run the bash script for all examples:

```bash
bash Examples/example_create_knowledge_graph.sh
```

### Option 3: Manual CLI Commands

#### Basic Graph Creation

```bash
# Using CLI command
python -m encyclopedia.cli.versioned_editor graph \
    --input encyclopedia_output.html \
    --output knowledge_graph.graphml \
    --format graphml \
    --include-wikipedia \
    --include-wikidata

# Using standalone script
python Examples/create_knowledge_graph.py \
    --input encyclopedia_output.html \
    --output knowledge_graph.graphml \
    --format graphml \
    --include-wikipedia \
    --include-wikidata \
    --verbose
```

#### Create Test Encyclopedia First

If you don't have an encyclopedia file yet:

```bash
# Create a small test encyclopedia
python -m encyclopedia.cli.versioned_editor create \
    --wordlist <(echo -e "climate change\ngreenhouse gas\ncarbon dioxide") \
    --output temp/test_encyclopedia.html \
    --title "Test Encyclopedia"

# Add Wikipedia descriptions
python -m encyclopedia.cli.versioned_editor process \
    --input temp/test_encyclopedia.html \
    --feature wikipedia \
    --batch-size 3

# Create knowledge graph
python -m encyclopedia.cli.versioned_editor graph \
    --input temp/test_encyclopedia.html \
    --output temp/knowledge_graph.graphml \
    --include-wikipedia \
    --include-wikidata
```

## Example Outputs

### GraphML Format

```bash
python Examples/create_knowledge_graph.py \
    --input encyclopedia_output.html \
    --output graph.graphml \
    --format graphml \
    --include-wikipedia \
    --include-wikidata \
    --verbose
```

**Output:**
```
Loading encyclopedia from encyclopedia_output.html...
✓ Loaded 3 entries
Building knowledge graph...
  - Wikipedia links: True
  - Wikidata relationships: True
✓ Graph created: 5 nodes, 8 edges
Exporting graph to graph.graphml (graphml format)...
✓ Graph exported successfully to graph.graphml
  Format: graphml
  Nodes: 5
  Edges: 8

  Edge types:
    wikipedia_link: 4
    P31: 2
    shared_property_P31: 1
    shared_value: 1
```

### GEXF Format (for Gephi)

```bash
python Examples/create_knowledge_graph.py \
    --input encyclopedia_output.html \
    --output graph.gexf \
    --format gexf \
    --include-wikipedia \
    --include-wikidata
```

**Visualization:**
1. Download Gephi: https://gephi.org/
2. Open the `.gexf` file in Gephi
3. Apply layout (e.g., ForceAtlas2)
4. Color nodes by `entry_type`
5. Size edges by `weight`

### JSON Format

```bash
python Examples/create_knowledge_graph.py \
    --input encyclopedia_output.html \
    --output graph.json \
    --format json \
    --include-wikipedia \
    --include-wikidata \
    --verbose
```

**Python Usage:**
```python
import json
from pathlib import Path

# Load JSON graph
with open('graph.json', 'r') as f:
    graph_data = json.load(f)

print(f"Nodes: {len(graph_data['nodes'])}")
print(f"Edges: {len(graph_data['edges'])}")

# Access nodes
for node in graph_data['nodes']:
    print(f"  {node['id']}: {node.get('term', 'N/A')}")

# Access edges
for edge in graph_data['edges'][:5]:  # First 5 edges
    print(f"  {edge['source']} -> {edge['target']}: {edge['relationship_type']}")
```

### RDF/Turtle Format

```bash
python Examples/create_knowledge_graph.py \
    --input encyclopedia_output.html \
    --output graph.ttl \
    --format rdf \
    --include-wikidata
```

**Example Output:**
```turtle
@prefix wd: <http://www.wikidata.org/entity/> .
@prefix wdt: <http://www.wikidata.org/prop/direct/> .
@prefix kg: <http://example.org/kg/> .

wd:Q7942 kg:term "climate change" .
wd:Q7942 wdt:P31 wd:Q7937 .
wd:Q7942 kg:wikipedia_link wd:Q131784 .
```

## Using NetworkX for Visualization

```python
import networkx as nx
import matplotlib.pyplot as plt

# Load graph
graph = nx.read_graphml('temp/examples/knowledge_graphs/example_graph.graphml')

# Basic visualization
pos = nx.spring_layout(graph)
nx.draw(graph, pos, with_labels=True, node_size=500, font_size=8)
plt.title("Knowledge Graph")
plt.show()

# Node information
print("Nodes:")
for node_id, data in graph.nodes(data=True):
    print(f"  {node_id}: {data.get('term', 'N/A')}")

# Edge information
print("\nEdges:")
for source, target, data in list(graph.edges(data=True))[:10]:
    print(f"  {source} -> {target}: {data.get('relationship_type', 'N/A')} (weight: {data.get('weight', 0):.2f})")
```

## Filtered Graphs

Create graphs with only high-weight edges:

```bash
python Examples/create_knowledge_graph.py \
    --input encyclopedia_output.html \
    --output filtered_graph.graphml \
    --format graphml \
    --include-wikipedia \
    --include-wikidata \
    --min-weight 0.3 \
    --verbose
```

This filters out edges with weight < 0.3, keeping only strong relationships.

## Complete Workflow Example

```bash
# Step 1: Create encyclopedia from wordlist
python -m encyclopedia.cli.versioned_editor create \
    --wordlist terms.txt \
    --output my_encyclopedia.html \
    --title "My Encyclopedia"

# Step 2: Add Wikipedia descriptions
python -m encyclopedia.cli.versioned_editor process \
    --input my_encyclopedia.html \
    --feature wikipedia \
    --batch-size 10

# Step 3: Create knowledge graph
python Examples/create_knowledge_graph.py \
    --input my_encyclopedia.html \
    --output my_knowledge_graph.graphml \
    --format graphml \
    --include-wikipedia \
    --include-wikidata \
    --verbose

# Step 4: Visualize (using NetworkX)
python -c "
import networkx as nx
import matplotlib.pyplot as plt
graph = nx.read_graphml('my_knowledge_graph.graphml')
pos = nx.spring_layout(graph)
nx.draw(graph, pos, with_labels=True, node_size=1000, font_size=10)
plt.savefig('graph_visualization.png')
print('Saved to graph_visualization.png')
"
```

## Test Files Location

Example outputs are saved to:
- `temp/examples/knowledge_graphs/` - Example graphs
- `temp/test/encyclopedia/TestKnowledgeGraphBuilder/` - Test encyclopedia files

## Troubleshooting

### No Encyclopedia File Found

If you get "File not found" errors:

1. **Create a test encyclopedia:**
   ```bash
   python Examples/example_create_knowledge_graph.py
   ```

2. **Or use the test fixtures:**
   ```bash
   # Run tests to generate test encyclopedia
   pytest test/encyclopedia/test_knowledge_graph.py::TestKnowledgeGraphBuilder::test_build_graph_with_wikipedia_links -v
   
   # Then use the generated file
   python Examples/create_knowledge_graph.py \
       --input temp/test/encyclopedia/TestKnowledgeGraphBuilder/climate_encyclopedia.html \
       --output example.graphml \
       --include-wikipedia \
       --include-wikidata
   ```

### No Edges Created

If the graph has nodes but no edges:

1. Ensure entries have `description_html` (for Wikipedia links)
2. Ensure entries have valid `wikidata_id` (for Wikidata relationships)
3. Check that `--include-wikipedia` or `--include-wikidata` flags are set

### Network Errors (Wikidata)

If SPARQL queries fail:

1. Check internet connection
2. Verify Wikidata SPARQL endpoint is accessible
3. Try with `--include-wikipedia` only (no Wikidata)

## Next Steps

1. ✅ Run examples
2. ⏳ Visualize graphs in Gephi or NetworkX
3. ⏳ Analyze graph structure and relationships
4. ⏳ Export to other formats as needed
