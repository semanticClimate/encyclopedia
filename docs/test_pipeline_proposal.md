# Test Pipeline Proposal: Wordlist → Encyclopedia → Knowledge Graph

**Date:** January 23, 2026 (system date of generation)  
**Purpose:** Propose simple CLI-based tests for pipeline stages

## Test Overview

Three separate CLI-based tests, one for each stage of the pipeline:

1. **Test 1**: Read wordlist and create encyclopedia without description or images
2. **Test 2**: Add Wikipedia description and images to encyclopedia and normalize synonyms
3. **Test 3**: Create knowledge graph from encyclopedia

## Test Structure

- **Input**: Wordlists in `test/` directory
- **Output**: Results in `temp/` directory, structured to reflect input
  - Example: `test/wordlist_a.txt` → `temp/test/wordlist_a/encyclopedia.html`

## Test 1: Create Encyclopedia from Wordlist

**File:** `scripts/test_01_create_encyclopedia.py`

Simple CLI test that:
- Reads wordlist from `test/wordlist_a.txt`
- Creates basic encyclopedia using CLI command
- Outputs to `temp/test/wordlist_a/encyclopedia.html`
- No descriptions or images (basic structure only)

**Usage:**
```bash
python scripts/test_01_create_encyclopedia.py
```

## Test 2: Enhance Encyclopedia (Not Yet Implemented)

**File:** `scripts/test_02_enhance_encyclopedia.py` (to be created)

Will:
- Read encyclopedia from `temp/test/wordlist_a/encyclopedia.html`
- Add Wikipedia descriptions using CLI
- Add images using CLI
- Normalize synonyms
- Output to `temp/test/wordlist_a/encyclopedia_enhanced.html`

## Test 3: Create Knowledge Graph (Not Yet Implemented)

**File:** `scripts/test_03_create_knowledge_graph.py` (to be created)

Will:
- Read encyclopedia from `temp/test/wordlist_a/encyclopedia_enhanced.html`
- Create knowledge graph (GraphML)
- Output to `temp/test/wordlist_a/knowledge_graph.graphml`

## Previous Complex Test Script (Removed)

### Option A: CLI + Python Script (Current Capability)

**File:** `scripts/test_pipeline.py`

```python
#!/usr/bin/env python3
"""
Test complete pipeline: Wordlist → Encyclopedia → Knowledge Graph

Tests the full workflow using CLI commands where available.
"""
import subprocess
import sys
from pathlib import Path
import networkx as nx
from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources


def run_cli_command(cmd, description):
    """Run CLI command and return success status."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Success")
        if result.stdout:
            print(result.stdout)
        return True
    else:
        print(f"❌ Failed (exit code: {result.returncode})")
        if result.stderr:
            print("Error output:")
            print(result.stderr)
        return False


def create_knowledge_graph(encyclopedia_file: Path, output_file: Path):
    """Create knowledge graph from encyclopedia HTML file."""
    print(f"\n{'='*60}")
    print("Step 3: Creating Knowledge Graph")
    print(f"{'='*60}")
    
    # Load encyclopedia
    print(f"Loading encyclopedia from: {encyclopedia_file}")
    encyclopedia = AmiEncyclopedia(title="Test Encyclopedia")
    encyclopedia.create_from_html_file(encyclopedia_file)
    
    print(f"Loaded {len(encyclopedia.entries)} entries")
    
    # Create graph
    G = nx.DiGraph()  # Directed graph
    
    # Add nodes (entities) from encyclopedia entries
    nodes_added = 0
    for entry in encyclopedia.entries:
        if entry.get('wikidata_id'):
            node_id = entry['wikidata_id']
            G.add_node(
                node_id,
                term=entry['term'],
                wikipedia_url=entry.get('wikipedia_url', ''),
                description=entry.get('description_html', '')[:200] if entry.get('description_html') else ''
            )
            nodes_added += 1
    
    print(f"Added {nodes_added} nodes to graph")
    
    # Add edges based on Wikipedia links in descriptions
    # Extract links from description_html and create edges
    edges_added = 0
    for entry in encyclopedia.entries:
        if entry.get('wikidata_id'):
            source_id = entry['wikidata_id']
            # Find other entries mentioned in description
            description = entry.get('description_html', '')
            if description:
                # Simple approach: check if other entry terms appear in description
                for other_entry in encyclopedia.entries:
                    if (other_entry.get('wikidata_id') and 
                        other_entry['wikidata_id'] != source_id and
                        other_entry['term'].lower() in description.lower()):
                        target_id = other_entry['wikidata_id']
                        if not G.has_edge(source_id, target_id):
                            G.add_edge(source_id, target_id, relationship='mentioned_in')
                            edges_added += 1
    
    print(f"Added {edges_added} edges to graph")
    
    # Save to GraphML
    output_file.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(G, str(output_file))
    print(f"✅ Saved GraphML: {output_file}")
    
    # Print graph statistics
    print(f"\nGraph Statistics:")
    print(f"  Nodes: {G.number_of_nodes()}")
    print(f"  Edges: {G.number_of_edges()}")
    print(f"  Is connected: {nx.is_weakly_connected(G)}")
    
    return True


def validate_outputs(wordlist_file: Path, encyclopedia_file: Path, graphml_file: Path):
    """Validate that all outputs were created correctly."""
    print(f"\n{'='*60}")
    print("Step 4: Validating Outputs")
    print(f"{'='*60}")
    
    errors = []
    
    # Check wordlist exists
    if not wordlist_file.exists():
        errors.append(f"Wordlist file not found: {wordlist_file}")
    else:
        wordlist_lines = len([l for l in wordlist_file.read_text().splitlines() if l.strip()])
        print(f"✅ Wordlist: {wordlist_file} ({wordlist_lines} terms)")
    
    # Check encyclopedia exists
    if not encyclopedia_file.exists():
        errors.append(f"Encyclopedia file not found: {encyclopedia_file}")
    else:
        content = encyclopedia_file.read_text()
        entry_count = content.count('role="ami_entry"')
        print(f"✅ Encyclopedia: {encyclopedia_file} ({entry_count} entries)")
        
        # Check for required attributes
        if 'role="ami_encyclopedia"' not in content:
            errors.append("Encyclopedia missing role='ami_encyclopedia'")
        if 'wikidataID' not in content and 'wikidataid' not in content:
            print("⚠️  Warning: No Wikidata IDs found in encyclopedia")
    
    # Check GraphML exists
    if not graphml_file.exists():
        errors.append(f"GraphML file not found: {graphml_file}")
    else:
        # Try to read GraphML
        try:
            G = nx.read_graphml(str(graphml_file))
            print(f"✅ GraphML: {graphml_file} ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")
        except Exception as e:
            errors.append(f"GraphML file exists but cannot be read: {e}")
    
    if errors:
        print("\n❌ Validation Errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\n✅ All outputs validated successfully")
        return True


def main():
    """Main test function."""
    print("="*60)
    print("Testing Pipeline: Wordlist → Encyclopedia → Knowledge Graph")
    print("="*60)
    
    # Setup paths
    project_root = Path(__file__).parent.parent
    test_dir = Path(project_root, "test")
    temp_dir = Path(Resources.TEMP_DIR, "test", "pipeline_test")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    wordlist_file = Path(test_dir, "wordlist_a.txt")
    encyclopedia_file = Path(temp_dir, "test_encyclopedia.html")
    graphml_file = Path(temp_dir, "test_knowledge_graph.graphml")
    
    # Step 1: Create Encyclopedia from Wordlist
    if not wordlist_file.exists():
        print(f"❌ Wordlist file not found: {wordlist_file}")
        return 1
    
    cmd_create = [
        sys.executable, "-m", "encyclopedia.cli.versioned_editor",
        "create",
        "--wordlist", str(wordlist_file),
        "--output", str(encyclopedia_file),
        "--title", "Test Encyclopedia"
    ]
    
    if not run_cli_command(cmd_create, "Step 1: Creating Encyclopedia from Wordlist"):
        return 1
    
    # Step 2: Enhance with Wikipedia (optional - can skip for faster test)
    enhance_wikipedia = True  # Set to False to skip Wikipedia enhancement
    if enhance_wikipedia:
        cmd_process = [
            sys.executable, "-m", "encyclopedia.cli.versioned_editor",
            "process",
            "--input", str(encyclopedia_file),
            "--feature", "wikipedia",
            "--batch-size", "5"  # Small batch for testing
        ]
        
        if not run_cli_command(cmd_process, "Step 2: Enhancing with Wikipedia Descriptions"):
            print("⚠️  Warning: Wikipedia enhancement failed, continuing anyway...")
    
    # Step 3: Create Knowledge Graph
    if not create_knowledge_graph(encyclopedia_file, graphml_file):
        return 1
    
    # Step 4: Validate Outputs
    if not validate_outputs(wordlist_file, encyclopedia_file, graphml_file):
        return 1
    
    print(f"\n{'='*60}")
    print("✅ Pipeline Test Completed Successfully!")
    print(f"{'='*60}")
    print(f"\nOutputs:")
    print(f"  Encyclopedia: {encyclopedia_file}")
    print(f"  Knowledge Graph: {graphml_file}")
    print(f"\nTo visualize the graph:")
    print(f"  - Open {graphml_file} in yEd Graph Editor")
    print(f"  - Or use Gephi: https://gephi.org/")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## Proposed CLI Command Addition

### Add `kg` (knowledge graph) command to versioned_editor

**Proposed addition to `encyclopedia/cli/versioned_editor.py`:**

```python
# Add to subparsers
kg_parser = subparsers.add_parser('kg', help='Create knowledge graph from encyclopedia')
kg_parser.add_argument('--input', type=Path, required=True, help='Input encyclopedia HTML file')
kg_parser.add_argument('--output', type=Path, required=True, help='Output GraphML file')
kg_parser.add_argument('--extract-relationships', action='store_true', 
                       help='Extract relationships from Wikipedia links in descriptions')

# Add to command execution
elif args.command == 'kg':
    return create_knowledge_graph_cli(args.input, args.output, args.extract_relationships)
```

**Implementation:**

```python
def create_knowledge_graph_cli(input_file: Path, output_file: Path, extract_relationships: bool = False):
    """Create knowledge graph from encyclopedia HTML file."""
    import networkx as nx
    from encyclopedia.core.encyclopedia import AmiEncyclopedia
    
    print(f"Loading encyclopedia from: {input_file}")
    encyclopedia = AmiEncyclopedia(title="Encyclopedia")
    encyclopedia.create_from_html_file(input_file)
    
    print(f"Loaded {len(encyclopedia.entries)} entries")
    
    # Create graph
    G = nx.DiGraph()
    
    # Add nodes
    nodes_added = 0
    for entry in encyclopedia.entries:
        if entry.get('wikidata_id'):
            G.add_node(
                entry['wikidata_id'],
                term=entry['term'],
                wikipedia_url=entry.get('wikipedia_url', ''),
                description=entry.get('description_html', '')[:200] if entry.get('description_html') else ''
            )
            nodes_added += 1
    
    print(f"Added {nodes_added} nodes")
    
    # Add edges if requested
    if extract_relationships:
        edges_added = 0
        for entry in encyclopedia.entries:
            if entry.get('wikidata_id'):
                source_id = entry['wikidata_id']
                description = entry.get('description_html', '').lower()
                for other_entry in encyclopedia.entries:
                    if (other_entry.get('wikidata_id') and 
                        other_entry['wikidata_id'] != source_id and
                        other_entry['term'].lower() in description):
                        target_id = other_entry['wikidata_id']
                        if not G.has_edge(source_id, target_id):
                            G.add_edge(source_id, target_id, relationship='mentioned_in')
                            edges_added += 1
        print(f"Added {edges_added} edges")
    
    # Save GraphML
    output_file.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(G, str(output_file))
    print(f"✅ Saved GraphML: {output_file}")
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    return 0
```

## Complete CLI Test Workflow

### With Proposed CLI Command

```bash
#!/bin/bash
# Complete pipeline test using CLI commands

# Setup
WORDLIST="test/wordlist_a.txt"
ENCYCLOPEDIA="temp/test/pipeline_test/test_encyclopedia.html"
GRAPHML="temp/test/pipeline_test/test_knowledge_graph.graphml"

# Step 1: Create Encyclopedia
echo "Step 1: Creating Encyclopedia..."
python -m encyclopedia.cli.versioned_editor create \
    --wordlist "$WORDLIST" \
    --output "$ENCYCLOPEDIA" \
    --title "Test Encyclopedia"

# Step 2: Enhance with Wikipedia (optional)
echo "Step 2: Enhancing with Wikipedia..."
python -m encyclopedia.cli.versioned_editor process \
    --input "$ENCYCLOPEDIA" \
    --feature wikipedia \
    --batch-size 5

# Step 3: Create Knowledge Graph (proposed CLI command)
echo "Step 3: Creating Knowledge Graph..."
python -m encyclopedia.cli.versioned_editor kg \
    --input "$ENCYCLOPEDIA" \
    --output "$GRAPHML" \
    --extract-relationships

# Step 4: Validate
echo "Step 4: Validating outputs..."
python scripts/test_pipeline.py --validate-only \
    --wordlist "$WORDLIST" \
    --encyclopedia "$ENCYCLOPEDIA" \
    --graphml "$GRAPHML"
```

## Test Validation Criteria

### Success Criteria

1. **Wordlist → Encyclopedia**
   - ✅ Encyclopedia HTML file created
   - ✅ Contains entries with `role="ami_entry"`
   - ✅ Has `role="ami_encyclopedia"` container
   - ✅ Entries have terms

2. **Encyclopedia Enhancement**
   - ✅ Wikipedia descriptions added (if enabled)
   - ✅ Wikidata IDs present
   - ✅ Wikipedia URLs present

3. **Encyclopedia → Knowledge Graph**
   - ✅ GraphML file created
   - ✅ Contains nodes (one per entry with Wikidata ID)
   - ✅ Contains edges (if relationships extracted)
   - ✅ GraphML is valid XML
   - ✅ Can be loaded by NetworkX
   - ✅ Can be opened in yEd/Gephi

### Expected Outputs

- **Encyclopedia HTML**: `temp/test/pipeline_test/test_encyclopedia.html`
- **Knowledge Graph GraphML**: `temp/test/pipeline_test/test_knowledge_graph.graphml`

## Test Execution

### Option 1: Python Script (Current - No CLI for KG yet)

```bash
# Run complete test
python scripts/test_pipeline.py
```

### Option 2: CLI Commands (After adding kg command)

```bash
# Step-by-step CLI execution
python -m encyclopedia.cli.versioned_editor create --wordlist test/wordlist_a.txt --output temp/test/encyclopedia.html --title "Test"
python -m encyclopedia.cli.versioned_editor process --input temp/test/encyclopedia.html --feature wikipedia --batch-size 5
python -m encyclopedia.cli.versioned_editor kg --input temp/test/encyclopedia.html --output temp/test/kg.graphml --extract-relationships
```

## Recommendations

1. **Immediate**: Create `scripts/test_pipeline.py` (Python script for complete test)
2. **Short-term**: Add `kg` command to `versioned_editor.py` CLI
3. **Validation**: Add validation function to check outputs
4. **Documentation**: Update workflow docs with CLI examples

## Files to Create/Modify

1. **Create**: `scripts/test_pipeline.py` - Complete pipeline test script
2. **Modify**: `encyclopedia/cli/versioned_editor.py` - Add `kg` command
3. **Create**: `test/test_pipeline_cli.py` - Unit test for pipeline
4. **Update**: `docs/html_to_knowledge_graph_workflow.md` - Add CLI examples
