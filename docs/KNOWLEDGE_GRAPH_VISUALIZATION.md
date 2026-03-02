# Knowledge Graph Visualization Guide

**Date:** March 2, 2026 (system date)

**Note:** Node labels are automatically cleaned to remove URL stems and use human-readable terms. The visualization script extracts clean labels from node data, preferring the `term` field and cleaning URL-based node IDs.

## Quick Start

### Using the Visualization Script

```bash
# Basic visualization
python Examples/visualize_knowledge_graph.py \
    --input temp/examples/knowledge_graphs/example_graph.graphml \
    --style basic

# Visualize with entry types colored
python Examples/visualize_knowledge_graph.py \
    --input temp/examples/knowledge_graphs/example_graph.graphml \
    --style entry-type \
    --output graph_visualization.png

# Visualize with relationship types colored
python Examples/visualize_knowledge_graph.py \
    --input temp/examples/knowledge_graphs/example_graph.graphml \
    --style relationship-type \
    --output graph_by_relationships.png

# Visualize with edge weights
python Examples/visualize_knowledge_graph.py \
    --input temp/examples/knowledge_graphs/example_graph.graphml \
    --style weighted \
    --output graph_weighted.png \
    --stats
```

## Python Code Examples

### Basic Visualization

```python
import networkx as nx
import matplotlib.pyplot as plt

# Load graph
graph = nx.read_graphml('temp/examples/knowledge_graphs/example_graph.graphml')

# Create figure
plt.figure(figsize=(12, 8))

# Use spring layout
pos = nx.spring_layout(graph, k=1, iterations=50)

# Draw graph
nx.draw(graph, pos,
        with_labels=True,
        node_color='lightblue',
        node_size=500,
        font_size=8,
        arrows=True,
        arrowsize=20)

plt.title("Knowledge Graph")
plt.show()
```

### Color Nodes by Entry Type

```python
import networkx as nx
import matplotlib.pyplot as plt

# Load graph
graph = nx.read_graphml('temp/examples/knowledge_graphs/example_graph.graphml')

plt.figure(figsize=(14, 10))
pos = nx.spring_layout(graph, k=1, iterations=50)

# Separate nodes by type
entry_nodes = [n for n, d in graph.nodes(data=True) 
               if d.get('entry_type') == 'entry']
external_nodes = [n for n, d in graph.nodes(data=True) 
                 if d.get('entry_type') == 'external']

# Draw external nodes (background)
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

# Draw labels for entry nodes only
labels = {n: d.get('term', n)[:20] for n, d in graph.nodes(data=True) 
          if d.get('entry_type') == 'entry'}
nx.draw_networkx_labels(graph, pos, labels, font_size=7)

plt.title("Knowledge Graph - Colored by Entry Type")
plt.legend()
plt.axis('off')
plt.tight_layout()
plt.show()
```

### Color Edges by Relationship Type

```python
import networkx as nx
import matplotlib.pyplot as plt

# Load graph
graph = nx.read_graphml('temp/examples/knowledge_graphs/example_graph.graphml')

plt.figure(figsize=(14, 10))
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

# Color map
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

# Draw labels (using clean labels without URL stems)
from Examples.visualize_knowledge_graph import clean_node_label
labels = {n: clean_node_label(n, d)[:15] for n, d in graph.nodes(data=True) 
          if d.get('entry_type') == 'entry'}
nx.draw_networkx_labels(graph, pos, labels, font_size=7)

plt.title("Knowledge Graph - Colored by Relationship Type")
plt.legend(loc='upper right', fontsize=8)
plt.axis('off')
plt.tight_layout()
plt.show()
```

### Edge Widths Proportional to Weight

```python
import networkx as nx
import matplotlib.pyplot as plt

# Load graph
graph = nx.read_graphml('temp/examples/knowledge_graphs/example_graph.graphml')

plt.figure(figsize=(14, 10))
pos = nx.spring_layout(graph, k=1, iterations=50)

# Draw nodes
nx.draw_networkx_nodes(graph, pos,
                      node_color='lightblue',
                      node_size=500,
                      alpha=0.7)

# Get edge weights
edges = graph.edges(data=True)
weights = [d.get('weight', 1.0) for u, v, d in edges]

# Normalize weights for visualization
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

# Draw labels (using clean labels without URL stems)
from Examples.visualize_knowledge_graph import clean_node_label
labels = {n: clean_node_label(n, d)[:15] for n, d in graph.nodes(data=True) 
          if d.get('entry_type') == 'entry'}
nx.draw_networkx_labels(graph, pos, labels, font_size=7)

plt.title("Knowledge Graph - Edge Widths Proportional to Weight")
plt.axis('off')
plt.tight_layout()
plt.show()
```

## Layout Options

### Spring Layout (Default)

```python
pos = nx.spring_layout(graph, k=1, iterations=50)
```

### Circular Layout

```python
pos = nx.circular_layout(graph)
```

### Kamada-Kawai Layout (Good for small graphs)

```python
pos = nx.kamada_kawai_layout(graph)
```

### Force-Directed Layout

```python
pos = nx.spring_layout(graph, k=2, iterations=100)
```

### Hierarchical Layout (for directed graphs)

```python
pos = nx.nx_agraph.graphviz_layout(graph, prog='dot')
# Requires: pip install pygraphviz
```

## Filtering and Subgraphs

### Filter by Relationship Type

```python
# Create subgraph with only Wikipedia links
wikipedia_edges = [(u, v) for u, v, d in graph.edges(data=True)
                   if d.get('relationship_type') == 'wikipedia_link']
subgraph = graph.edge_subgraph(wikipedia_edges)

# Visualize subgraph
pos = nx.spring_layout(subgraph)
nx.draw(subgraph, pos, with_labels=True)
plt.show()
```

### Filter by Weight

```python
# Create subgraph with high-weight edges only
high_weight_edges = [(u, v) for u, v, d in graph.edges(data=True)
                    if d.get('weight', 0) > 0.5]
subgraph = graph.edge_subgraph(high_weight_edges)

# Visualize
pos = nx.spring_layout(subgraph)
nx.draw(subgraph, pos, with_labels=True)
plt.show()
```

### Filter by Entry Type

```python
# Create subgraph with only encyclopedia entries
entry_nodes = [n for n, d in graph.nodes(data=True)
               if d.get('entry_type') == 'entry']
subgraph = graph.subgraph(entry_nodes)

# Visualize
pos = nx.spring_layout(subgraph)
nx.draw(subgraph, pos, with_labels=True)
plt.show()
```

## Interactive Visualization with Plotly

For interactive visualizations, use Plotly:

```python
import networkx as nx
import plotly.graph_objects as go
import numpy as np

# Load graph
graph = nx.read_graphml('temp/examples/knowledge_graphs/example_graph.graphml')

# Get layout
pos = nx.spring_layout(graph)

# Create edge traces
edge_x = []
edge_y = []
for edge in graph.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

edge_trace = go.Scatter(x=edge_x, y=edge_y,
                        line=dict(width=0.5, color='#888'),
                        hoverinfo='none',
                        mode='lines')

# Create node traces
node_x = []
node_y = []
node_text = []
for node in graph.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    node_text.append(f"{node}: {graph.nodes[node].get('term', 'N/A')}")

node_trace = go.Scatter(x=node_x, y=node_y,
                        mode='markers+text',
                        hoverinfo='text',
                        text=node_text,
                        marker=dict(size=10,
                                  color='lightblue',
                                  line=dict(width=2)))

# Create figure
fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(title='Knowledge Graph',
                               showlegend=False,
                               hovermode='closest',
                               margin=dict(b=20,l=5,r=5,t=40),
                               xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                               yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))

fig.show()
```

## Graph Statistics

```python
import networkx as nx

# Load graph
graph = nx.read_graphml('temp/examples/knowledge_graphs/example_graph.graphml')

# Basic statistics
print(f"Nodes: {graph.number_of_nodes()}")
print(f"Edges: {graph.number_of_edges()}")
print(f"Directed: {graph.is_directed()}")

# Node types
entry_nodes = sum(1 for n, d in graph.nodes(data=True) 
                 if d.get('entry_type') == 'entry')
external_nodes = graph.number_of_nodes() - entry_nodes
print(f"Encyclopedia entries: {entry_nodes}")
print(f"External entities: {external_nodes}")

# Edge types
edge_types = {}
for u, v, d in graph.edges(data=True):
    rel_type = d.get('relationship_type', 'unknown')
    edge_types[rel_type] = edge_types.get(rel_type, 0) + 1

print("\nEdge Types:")
for rel_type, count in sorted(edge_types.items(), key=lambda x: -x[1]):
    print(f"  {rel_type}: {count}")

# Centrality measures
degree_centrality = nx.degree_centrality(graph)
betweenness_centrality = nx.betweenness_centrality(graph)

print("\nMost Central Nodes (by degree):")
for node, centrality in sorted(degree_centrality.items(), 
                               key=lambda x: -x[1])[:10]:
    term = graph.nodes[node].get('term', 'N/A')
    print(f"  {node} ({term}): {centrality:.3f}")
```

## Saving Visualizations

```python
# Save as PNG
plt.savefig('graph_visualization.png', dpi=300, bbox_inches='tight')

# Save as PDF
plt.savefig('graph_visualization.pdf', bbox_inches='tight')

# Save as SVG
plt.savefig('graph_visualization.svg', bbox_inches='tight')
```

## Tips

1. **For Large Graphs:** Use filtering to create subgraphs before visualization
2. **For Better Layouts:** Try different layout algorithms (spring, kamada-kawai, etc.)
3. **For Clarity:** Only label entry nodes, not external entities
4. **For Performance:** Use `iterations` parameter to control layout computation time
5. **For Colors:** Use `plt.cm.tab10` or `plt.cm.Set3` for distinct colors

## Dependencies

```bash
pip install networkx matplotlib
# Optional: for interactive visualization
pip install plotly
```

## References

- **NetworkX Visualization:** https://networkx.org/documentation/stable/reference/drawing.html
- **Matplotlib:** https://matplotlib.org/
- **Plotly:** https://plotly.com/python/
