# HTML to Knowledge Graph Workflow

## Overview

This directory contains documentation and visualizations for the complete workflow from HTML chapters with IDs to knowledge graphs.

## Files

1. **`html_to_knowledge_graph_workflow.md`** - Complete workflow documentation with:
   - Step-by-step instructions
   - Software used and parameters
   - Code examples
   - Command-line usage

2. **`html_to_knowledge_graph_workflow.dot`** - Graphviz source file with:
   - Complete workflow diagram
   - Hyperlinks to relevant code and documentation
   - Color-coded stages

3. **`html_to_knowledge_graph_workflow.svg`** - Vector diagram (scalable, with clickable links)

4. **`html_to_knowledge_graph_workflow.png`** - Raster diagram (for presentations)

## Quick Start

### View the Workflow Diagram

**SVG (recommended - clickable links)**:
- Open `html_to_knowledge_graph_workflow.svg` in a web browser
- Click on any node to navigate to relevant documentation or code

**PNG (for presentations)**:
- Open `html_to_knowledge_graph_workflow.png` in any image viewer

### Read the Documentation

See [`html_to_knowledge_graph_workflow.md`](html_to_knowledge_graph_workflow.md) for:
- Complete workflow description
- Software requirements
- Code examples
- Parameter descriptions

## Workflow Summary

```
HTML Chapter (with IDs)
    ↓
1. Extract Wordlist
    ├─ Option A: Extract text → Extract keywords (Transformers)
    └─ Option B: Extract IDs directly (Regex)
    ↓
2. Create Dictionary
    ├─ Create basic dictionary structure
    └─ Enhance with Wikipedia content
    ↓
3. Create Encyclopedia
    ├─ Convert to HTML dictionary
    ├─ Parse and extract entries
    ├─ Normalize by Wikidata ID
    └─ Merge synonyms
    ↓
4. Generate Knowledge Graph
    ├─ Extract entities (Wikidata IDs)
    ├─ Extract relationships
    └─ Export to GraphML format
```

## Regenerating Diagrams

To regenerate the SVG and PNG files from the DOT source:

```bash
cd docs
dot -Tsvg html_to_knowledge_graph_workflow.dot -o html_to_knowledge_graph_workflow.svg
dot -Tpng html_to_knowledge_graph_workflow.dot -o html_to_knowledge_graph_workflow.png
```

**Requirements**: Graphviz must be installed (`brew install graphviz` on macOS)

## Related Documentation

- [Encyclopedia Pipeline Documentation](encyclopedia_pipeline_documentation.md)
- [Create Encyclopedia from Wordlist Summary](create_encyclopedia_from_wordlist_summary.md)
- [Encyclopedia Creation Review](encyclopedia_creation_review.md)
