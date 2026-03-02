# Knowledge Graph Usage Guide

**Date:** March 2, 2026 (system date)  
**Status:** Complete

## Overview

This guide explains how to create knowledge graphs from encyclopedia HTML files using either the CLI command or the standalone script.

## CLI Command

### Basic Usage

```bash
# Create GraphML graph with all relationships
python -m encyclopedia.cli.versioned_editor graph \
    --input encyclopedia.html \
    --output knowledge_graph.graphml \
    --format graphml \
    --include-wikipedia \
    --include-wikidata

# Create GEXF graph (for Gephi) with only Wikipedia links
python -m encyclopedia.cli.versioned_editor graph \
    --input encyclopedia.html \
    --output graph.gexf \
    --format gexf \
    --include-wikipedia

# Create JSON graph with minimum weight filter
python -m encyclopedia.cli.versioned_editor graph \
    --input encyclopedia.html \
    --output graph.json \
    --format json \
    --include-wikipedia \
    --include-wikidata \
    --min-weight 0.1
```

### Command Options

- `--input`: Input encyclopedia HTML file (required)
- `--output`: Output graph file (required)
- `--format`: Output format - `graphml`, `gexf`, `json`, or `rdf` (default: `graphml`)
- `--include-wikipedia`: Include Wikipedia description links
- `--include-wikidata`: Include Wikidata relationships (ancestry, parts, shared properties)
- `--min-weight`: Minimum edge weight to include (default: 0.0, include all)

**Note:** If neither `--include-wikipedia` nor `--include-wikidata` is specified, both are included by default.

## Standalone Script

### Basic Usage

```bash
# Create GraphML graph with all relationships
python Examples/create_knowledge_graph.py \
    --input encyclopedia.html \
    --output knowledge_graph.graphml \
    --format graphml \
    --include-wikipedia \
    --include-wikidata \
    --verbose

# Create RDF/Turtle graph
python Examples/create_knowledge_graph.py \
    --input encyclopedia.html \
    --output graph.ttl \
    --format rdf \
    --include-wikidata
```

### Script Options

Same as CLI command, plus:
- `--verbose`: Show detailed progress and edge type breakdown

## Output Formats

### GraphML (`.graphml`)

**Standard XML format for graphs**
- Compatible with many graph visualization tools
- Preserves all node and edge attributes
- Good for general-purpose use

**Tools:** yEd, Cytoscape, NetworkX

### GEXF (`.gexf`)

**Gephi Exchange Format**
- Optimized for Gephi visualization software
- Supports dynamic graphs and advanced styling
- Best for interactive visualization

**Tools:** Gephi

### JSON (`.json`)

**Custom JSON format**
- Human-readable structure
- Easy to parse programmatically
- Good for web applications

**Structure:**
```json
{
  "nodes": [
    {
      "id": "Q7942",
      "wikidata_id": "Q7942",
      "term": "climate change",
      ...
    }
  ],
  "edges": [
    {
      "source": "Q7942",
      "target": "Q131784",
      "relationship_type": "wikipedia_link",
      "weight": 0.5,
      ...
    }
  ]
}
```

### RDF/Turtle (`.ttl`)

**Semantic Web format**
- Uses Wikidata prefixes (`wd:`, `wdt:`)
- Compatible with RDF tools and SPARQL endpoints
- Best for semantic web applications

**Example:**
```turtle
@prefix wd: <http://www.wikidata.org/entity/> .
@prefix wdt: <http://www.wikidata.org/prop/direct/> .
@prefix kg: <http://example.org/kg/> .

wd:Q7942 kg:term "climate change" .
wd:Q7942 wdt:P31 wd:Q7937 .
wd:Q7942 kg:wikipedia_link wd:Q131784 .
```

## Relationship Types

### Wikipedia Links

**Type:** `wikipedia_link`

**Source:** Links found in HTML descriptions of entries

**Attributes:**
- `link_count`: Number of times link appears
- `link_text`: Anchor text from Wikipedia link
- `weight`: Normalized weight (count / 10.0, max 1.0)

### Wikidata Ancestry

**Types:** `P31` (instance of), `P279` (subclass of)

**Source:** Wikidata properties

**Attributes:**
- `property_id`: Wikidata property ID (P31, P279)
- `property_label`: Human-readable name
- `weight`: 1.0 (binary relationship)

### Wikidata Parts

**Types:** `P527` (has part), `P361` (part of), `P2670` (has part(s) of class)

**Source:** Wikidata properties

**Attributes:**
- `property_id`: Wikidata property ID
- `direction`: 'has_part' or 'part_of'
- `weight`: 1.0 (binary relationship)

### Shared Properties

**Type:** `shared_property_{P_ID}`

**Source:** Entries sharing the same Wikidata property-value pairs

**Attributes:**
- `property_id`: Shared property ID
- `shared_values`: List of shared value Q IDs
- `shared_count`: Number of shared values
- `weight`: Normalized weight (count / 5.0, max 1.0)

### Shared Values

**Type:** `shared_value`

**Source:** Entries with overlapping Wikidata property values

**Attributes:**
- `shared_values`: List of shared Wikidata Q IDs
- `value_count`: Number of shared values
- `weight`: Normalized weight (count / 5.0, max 1.0)

## Examples

### Example 1: Basic Graph Creation

```bash
# Load encyclopedia and create graph
python -m encyclopedia.cli.versioned_editor graph \
    --input temp/test/encyclopedia/TestKnowledgeGraphBuilder/climate_encyclopedia.html \
    --output knowledge_graph.graphml \
    --include-wikipedia \
    --include-wikidata
```

**Output:**
```
Loading encyclopedia from temp/test/encyclopedia/TestKnowledgeGraphBuilder/climate_encyclopedia.html...
Loaded 3 entries
Building knowledge graph...
Graph created: 5 nodes, 8 edges
Exporting graph to knowledge_graph.graphml (graphml format)...
✓ Graph exported successfully to knowledge_graph.graphml
  Nodes: 5
  Edges: 8
```

### Example 2: Filtered Graph (High-Weight Edges Only)

```bash
# Create graph with only strong relationships
python Examples/create_knowledge_graph.py \
    --input encyclopedia.html \
    --output filtered_graph.gexf \
    --format gexf \
    --include-wikipedia \
    --min-weight 0.3 \
    --verbose
```

**Output:**
```
Loading encyclopedia from encyclopedia.html...
✓ Loaded 10 entries
Building knowledge graph...
  - Wikipedia links: True
  - Wikidata relationships: False
✓ Graph created: 12 nodes, 25 edges
  Filtered: 25 → 8 edges (min weight: 0.3)
Exporting graph to filtered_graph.gexf (gexf format)...
✓ Graph exported successfully to filtered_graph.gexf
  Format: gexf
  Nodes: 12
  Edges: 8

  Edge types:
    wikipedia_link: 8
```

### Example 3: Wikidata-Only Graph

```bash
# Create graph with only Wikidata relationships
python -m encyclopedia.cli.versioned_editor graph \
    --input encyclopedia.html \
    --output wikidata_graph.json \
    --format json \
    --include-wikidata
```

## Integration with Other Commands

### Complete Workflow

```bash
# 1. Create encyclopedia from wordlist
python -m encyclopedia.cli.versioned_editor create \
    --wordlist terms.txt \
    --output encyclopedia.html \
    --title "My Encyclopedia"

# 2. Add Wikipedia descriptions
python -m encyclopedia.cli.versioned_editor process \
    --input encyclopedia.html \
    --feature wikipedia \
    --batch-size 10

# 3. Create knowledge graph
python -m encyclopedia.cli.versioned_editor graph \
    --input encyclopedia.html \
    --output knowledge_graph.graphml \
    --include-wikipedia \
    --include-wikidata
```

## Visualization

### Using Gephi

1. Export graph as GEXF:
   ```bash
   python Examples/create_knowledge_graph.py \
       --input encyclopedia.html \
       --output graph.gexf \
       --format gexf \
       --include-wikipedia \
       --include-wikidata
   ```

2. Open GEXF file in Gephi
3. Apply layout (e.g., ForceAtlas2)
4. Color nodes by `entry_type` (entry vs external)
5. Size edges by `weight`
6. Filter edges by `relationship_type`

### Using Python/NetworkX

```python
import networkx as nx
import matplotlib.pyplot as plt

# Load graph
graph = nx.read_graphml("knowledge_graph.graphml")

# Visualize
pos = nx.spring_layout(graph)
nx.draw(graph, pos, with_labels=True, node_size=500)
plt.show()
```

### Using Cytoscape

1. Export graph as GraphML
2. Import into Cytoscape
3. Use built-in layouts and styling options

## Troubleshooting

### No Edges Created

**Problem:** Graph has nodes but no edges

**Solutions:**
- Ensure entries have `description_html` for Wikipedia links
- Ensure entries have `wikidata_id` for Wikidata relationships
- Check that `--include-wikipedia` or `--include-wikidata` flags are set

### SPARQL Query Failures

**Problem:** Wikidata relationships not being extracted

**Solutions:**
- Check internet connection (SPARQL queries require network access)
- Verify Wikidata IDs are valid (start with 'Q')
- Check for rate limiting (Wikidata may throttle requests)

### Large Graph Files

**Problem:** Graph files are very large

**Solutions:**
- Use `--min-weight` to filter weak relationships
- Export to compressed formats (GraphML supports compression)
- Consider processing in batches for very large encyclopedias

## Performance Tips

1. **Use Caching:** Wikidata properties are cached automatically
2. **Filter Early:** Use `--min-weight` to reduce graph size
3. **Batch Processing:** For large encyclopedias, process in batches
4. **Format Choice:** JSON is fastest to write, GraphML is most compatible

## References

- **NetworkX Documentation:** https://networkx.org/documentation/
- **Wikidata SPARQL:** https://query.wikidata.org/
- **Gephi:** https://gephi.org/
- **GraphML Specification:** http://graphml.graphdrawing.org/
