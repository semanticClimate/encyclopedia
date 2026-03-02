# Knowledge Graph Tests

**Date:** March 2, 2026 (system date)  
**Status:** Tests Created (TDD - Implementation Pending)

## Overview

Comprehensive test suite for knowledge graph creation functionality, following Test-Driven Development (TDD) principles. Tests are written first and will guide the implementation of the knowledge graph modules.

## Test File

**Location:** `test/encyclopedia/test_knowledge_graph.py`

**Total Tests:** 16 tests across 5 test classes

## Test Classes

### 1. `TestWikipediaLinkExtraction` (3 tests)

Tests for extracting Wikipedia links from HTML descriptions:

- **`test_extract_wikipedia_links_from_description`**
  - Extracts Wikipedia links from entry HTML descriptions
  - Verifies link structure (url, text)
  - Saves results to `temp/test/encyclopedia/TestWikipediaLinkExtraction/extracted_links.json`

- **`test_match_links_to_encyclopedia_entries`**
  - Matches extracted links to encyclopedia entries
  - Verifies matching logic
  - Saves results to `temp/test/encyclopedia/TestWikipediaLinkExtraction/matched_links.json`

- **`test_count_link_occurrences`**
  - Counts occurrences of links between entries
  - Verifies counting logic
  - Saves results to `temp/test/encyclopedia/TestWikipediaLinkExtraction/link_occurrences.json`

**Module to Implement:** `encyclopedia/utils/knowledge_graph/wikipedia_extractor.py`

**Class:** `WikipediaLinkExtractor`

**Methods:**
- `extract_links_from_description(description_html: str) -> List[Dict]`
- `find_target_entry(url: str, encyclopedia: AmiEncyclopedia) -> Optional[Dict]`
- `count_link_occurrences(source_entry: Dict, target_entry: Dict) -> int`

---

### 2. `TestSharedLinkWeights` (2 tests)

Tests for calculating weights based on shared Wikipedia links:

- **`test_calculate_shared_link_weight`**
  - Calculates Jaccard similarity based on shared Wikipedia links
  - Verifies weight is in [0, 1] range
  - Saves results to `temp/test/encyclopedia/TestSharedLinkWeights/shared_link_weight.json`

- **`test_calculate_jaccard_similarity`**
  - Tests Jaccard similarity calculation specifically
  - Verifies Jaccard properties
  - Saves results to `temp/test/encyclopedia/TestSharedLinkWeights/jaccard_similarity.json`

**Module to Implement:** `encyclopedia/utils/knowledge_graph/weight_calculator.py`

**Class:** `EdgeWeightCalculator`

**Methods:**
- `calculate_shared_link_weight(entry1: Dict, entry2: Dict, encyclopedia: AmiEncyclopedia) -> float`

---

### 3. `TestWikidataRelationships` (4 tests)

Tests for extracting Wikidata relationships:

- **`test_fetch_wikidata_properties`**
  - Fetches Wikidata properties for entries using SPARQL
  - Verifies property structure (P IDs, Q IDs)
  - Saves results to `temp/test/encyclopedia/TestWikidataRelationships/wikidata_properties.json`

- **`test_extract_ancestry_relationships`**
  - Extracts instance of (P31) and subclass of (P279) relationships
  - Verifies relationship structure
  - Saves results to `temp/test/encyclopedia/TestWikidataRelationships/ancestry_relationships.json`

- **`test_extract_part_relationships`**
  - Extracts part-whole relationships (P527, P361, P2670)
  - Verifies relationship structure and direction
  - Saves results to `temp/test/encyclopedia/TestWikidataRelationships/part_relationships.json`

- **`test_find_shared_properties`**
  - Finds shared Wikidata properties between entries
  - Verifies shared property structure
  - Saves results to `temp/test/encyclopedia/TestWikidataRelationships/shared_properties.json`

**Module to Implement:** `encyclopedia/utils/knowledge_graph/wikidata_extractor.py`

**Class:** `WikidataRelationshipExtractor`

**Methods:**
- `fetch_wikidata_properties(wikidata_id: str) -> Dict`
- `extract_ancestry_relationships(entry: Dict) -> List[Dict]`
- `extract_part_relationships(entry: Dict) -> List[Dict]`
- `find_shared_properties(entry1: Dict, entry2: Dict) -> List[Dict]`

---

### 4. `TestKnowledgeGraphBuilder` (3 tests)

Tests for building complete knowledge graphs:

- **`test_build_graph_with_wikipedia_links`**
  - Builds graph with only Wikipedia description links
  - Verifies graph structure (nodes, edges, attributes)
  - Saves statistics to `temp/test/encyclopedia/TestKnowledgeGraphBuilder/graph_statistics.json`

- **`test_build_graph_with_wikidata_relationships`**
  - Builds graph with only Wikidata relationships
  - Verifies Wikidata edge structure
  - Saves statistics to `temp/test/encyclopedia/TestKnowledgeGraphBuilder/wikidata_graph_statistics.json`

- **`test_build_complete_graph`**
  - Builds complete graph with all relationship types
  - Counts edges by type
  - Saves statistics to `temp/test/encyclopedia/TestKnowledgeGraphBuilder/complete_graph_statistics.json`

**Module to Implement:** `encyclopedia/utils/knowledge_graph/graph_builder.py`

**Class:** `KnowledgeGraphBuilder`

**Methods:**
- `__init__(encyclopedia: AmiEncyclopedia)`
- `build_graph(include_wikipedia_links: bool, include_wikidata_ancestry: bool, include_wikidata_parts: bool, include_shared_properties: bool, include_shared_values: bool) -> nx.DiGraph`

---

### 5. `TestGraphExport` (4 tests)

Tests for exporting graphs to various formats:

- **`test_export_graphml`**
  - Exports graph to GraphML format
  - Verifies XML structure
  - Output: `temp/test/encyclopedia/TestGraphExport/test_graph.graphml`

- **`test_export_gexf`**
  - Exports graph to GEXF format (for Gephi)
  - Verifies XML structure
  - Output: `temp/test/encyclopedia/TestGraphExport/test_graph.gexf`

- **`test_export_json`**
  - Exports graph to JSON format
  - Verifies JSON structure
  - Output: `temp/test/encyclopedia/TestGraphExport/test_graph.json`

- **`test_export_rdf_turtle`**
  - Exports graph to RDF/Turtle format
  - Verifies RDF prefixes (wd:, wdt:)
  - Output: `temp/test/encyclopedia/TestGraphExport/test_graph.ttl`

**Module to Implement:** `encyclopedia/utils/knowledge_graph/graph_exporter.py`

**Class:** `GraphExporter`

**Methods:**
- `export_graphml(graph: nx.DiGraph, output_path: Path) -> Path`
- `export_gexf(graph: nx.DiGraph, output_path: Path) -> Path`
- `export_json(graph: nx.DiGraph, output_path: Path) -> Path`
- `export_rdf_turtle(graph: nx.DiGraph, output_path: Path) -> Path`

---

## Test Output Structure

All test outputs follow the style guide requirement:

```
temp/
└── test/
    └── encyclopedia/
        ├── TestWikipediaLinkExtraction/
        │   ├── extracted_links.json
        │   ├── matched_links.json
        │   └── link_occurrences.json
        ├── TestSharedLinkWeights/
        │   ├── shared_link_weight.json
        │   └── jaccard_similarity.json
        ├── TestWikidataRelationships/
        │   ├── wikidata_properties.json
        │   ├── ancestry_relationships.json
        │   ├── part_relationships.json
        │   └── shared_properties.json
        ├── TestKnowledgeGraphBuilder/
        │   ├── graph_statistics.json
        │   ├── wikidata_graph_statistics.json
        │   └── complete_graph_statistics.json
        └── TestGraphExport/
            ├── test_graph.graphml
            ├── test_graph.gexf
            ├── test_graph.json
            └── test_graph.ttl
```

## Test Fixtures

Tests use existing fixtures from `test/encyclopedia/conftest.py`:

- **`small_encyclopedia`** - Function-scoped fixture providing fresh `AmiEncyclopedia` instance

## Style Guide Compliance

✅ **System Date:** Tests use system date (March 2, 2026) in docstring  
✅ **Path Construction:** Uses `Path()` constructor for all file paths  
✅ **Output Location:** All outputs in `temp/test/encyclopedia/TestClassName/` subdirectories  
✅ **No Mocks:** Tests use real implementations (will use real Wikidata API, real HTML parsing)  
✅ **Human-Inspectable:** All tests save JSON outputs for human inspection  
✅ **Absolute Imports:** Uses `from encyclopedia.utils.knowledge_graph.*` imports  

## Expected Test Failures

All tests are expected to fail initially (TDD approach) with:

- `ModuleNotFoundError: No module named 'encyclopedia.utils.knowledge_graph.*'`

This is expected and will guide the implementation.

## Implementation Order

Recommended implementation order:

1. **Wikipedia Link Extractor** (`wikipedia_extractor.py`)
   - Start with `test_extract_wikipedia_links_from_description`
   - Then `test_match_links_to_encyclopedia_entries`
   - Finally `test_count_link_occurrences`

2. **Weight Calculator** (`weight_calculator.py`)
   - Implement `calculate_shared_link_weight` for Jaccard similarity

3. **Wikidata Extractor** (`wikidata_extractor.py`)
   - Start with SPARQL wrapper function
   - Then `fetch_wikidata_properties`
   - Then `extract_ancestry_relationships` and `extract_part_relationships`
   - Finally `find_shared_properties`

4. **Graph Builder** (`graph_builder.py`)
   - Implement `KnowledgeGraphBuilder` class
   - Build graph with Wikipedia links first
   - Then add Wikidata relationships

5. **Graph Exporter** (`graph_exporter.py`)
   - Implement export methods for each format
   - Use NetworkX built-in exporters where possible

## Dependencies

Tests will require these dependencies (to be added to `requirements.txt`):

- `networkx` - Graph creation and manipulation
- `requests` - SPARQL queries to Wikidata
- `lxml` - HTML parsing (already dependency)
- `rdflib` - RDF/Turtle export (optional, can use NetworkX)

## Running Tests

```bash
# Run all knowledge graph tests
pytest test/encyclopedia/test_knowledge_graph.py -v

# Run specific test class
pytest test/encyclopedia/test_knowledge_graph.py::TestWikipediaLinkExtraction -v

# Run with output inspection
pytest test/encyclopedia/test_knowledge_graph.py -v -s
```

## Next Steps

1. ✅ Tests created (current step)
2. ⏳ Implement modules (following TDD)
3. ⏳ Run tests and fix failures
4. ⏳ Add CLI integration
5. ⏳ Create usage scripts
6. ⏳ Document implementation
