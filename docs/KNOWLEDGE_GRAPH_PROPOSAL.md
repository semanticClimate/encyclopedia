# Knowledge Graph Creation Proposal

**Date:** March 2, 2026 (system date)  
**Status:** Proposal - Comments Only

## Overview

This proposal outlines the implementation of comprehensive knowledge graph creation from encyclopedia entries, extracting relationships from both Wikipedia descriptions and Wikidata properties. The knowledge graph will use Wikidata P and Q IDs as primary identifiers and support weighted edges based on relationship strength.

## Objectives

1. **Extract relationships from Wikipedia descriptions** - Parse HTML to find explicit links between entries
2. **Calculate link weights** - Based on shared Wikipedia links, co-occurrence, etc.
3. **Extract Wikidata relationships** - Including:
   - Ancestry relationships (instance of, subclass of)
   - Part-whole relationships (has part, part of)
   - Shared properties (with and without shared values)
4. **Use Wikidata IDs** - P IDs for properties, Q IDs for entities
5. **Export to standard formats** - GraphML, GEXF, RDF/Turtle

## Relationship Types

### 1. Wikipedia Description Links

**Type:** Explicit links found in HTML descriptions  
**Source:** `description_html` field in encyclopedia entries  
**Method:** Parse HTML `<a>` tags with Wikipedia URLs

**Example:**
```html
<p>Climate change is linked to <a href="/wiki/Greenhouse_gas">greenhouse gases</a> 
and <a href="/wiki/Carbon_dioxide">carbon dioxide</a>.</p>
```

**Edge Creation:**
- Source: Entry's Wikidata ID (Q ID)
- Target: Linked entry's Wikidata ID (Q ID)
- Relationship: `P31` (instance of) or custom `wikipedia_link`
- Weight: Number of times link appears in descriptions

**Edge Attributes:**
- `link_text`: The anchor text used
- `link_count`: Number of occurrences
- `source_description`: Excerpt from source entry
- `relationship_type`: `wikipedia_link`

### 2. Shared Wikipedia Links (Weight Calculation)

**Type:** Weighted edges based on shared Wikipedia article links  
**Source:** Multiple entries linking to the same Wikipedia articles  
**Method:** Count shared target articles

**Example:**
- Entry A links to: Greenhouse gas, Carbon dioxide, Methane
- Entry B links to: Greenhouse gas, Carbon dioxide, Atmosphere
- Shared links: Greenhouse gas (1), Carbon dioxide (1)
- Weight: 2 (number of shared links)

**Edge Creation:**
- Source: Entry A's Wikidata ID
- Target: Entry B's Wikidata ID
- Relationship: `shared_wikipedia_links`
- Weight: Number of shared Wikipedia articles

**Edge Attributes:**
- `shared_articles`: List of shared article names
- `shared_count`: Number of shared articles
- `jaccard_similarity`: Jaccard coefficient of shared links

### 3. Wikidata Ancestry Relationships

**Type:** Hierarchical relationships from Wikidata  
**Source:** Wikidata properties  
**Properties:**
- `P31` (instance of)
- `P279` (subclass of)
- `P361` (part of)

**Example:**
- Climate change (Q7942) `P31` Climate (Q7937)
- Greenhouse gas (Q131784) `P279` Gas (Q11421)

**Edge Creation:**
- Source: Entry's Wikidata ID
- Target: Related entity's Wikidata ID
- Relationship: Wikidata property ID (P31, P279, etc.)
- Weight: 1.0 (or property-specific weights)

**Edge Attributes:**
- `property_id`: Wikidata property ID (P31, P279, etc.)
- `property_label`: Human-readable property name
- `qualifiers`: Additional Wikidata qualifiers (if any)

### 4. Wikidata Part-Whole Relationships

**Type:** Part-whole relationships from Wikidata  
**Source:** Wikidata properties  
**Properties:**
- `P527` (has part)
- `P361` (part of)
- `P2670` (has part(s) of the class)

**Example:**
- Atmosphere (Q1151) `P527` Troposphere (Q131596)
- Carbon dioxide (Q1218) `P361` Greenhouse gas (Q131784)

**Edge Creation:**
- Source: Entry's Wikidata ID
- Target: Related entity's Wikidata ID
- Relationship: Wikidata property ID (P527, P361, etc.)
- Weight: 1.0

### 5. Shared Wikidata Properties

**Type:** Entries sharing the same property  
**Source:** Wikidata property values  
**Method:** Find entries with same property-value pairs

**Example:**
- Climate change (Q7942) has `P31` Climate (Q7937)
- Global warming (Q7942) has `P31` Climate (Q7937)
- Both share property `P31` with value `Q7937`

**Edge Creation:**
- Source: Entry A's Wikidata ID
- Target: Entry B's Wikidata ID
- Relationship: `shared_property_{P_ID}`
- Weight: Number of shared property-value pairs

**Edge Attributes:**
- `shared_properties`: List of shared property IDs
- `shared_values`: Dictionary of property → value mappings
- `property_count`: Number of shared properties

### 6. Shared Property Values (Without Property Match)

**Type:** Entries with same property values but different properties  
**Source:** Wikidata property values  
**Method:** Find entries with overlapping property values

**Example:**
- Entry A has `P31` Climate (Q7937)
- Entry B has `P279` Climate (Q7937)
- Both reference Q7937 but via different properties

**Edge Creation:**
- Source: Entry A's Wikidata ID
- Target: Entry B's Wikidata ID
- Relationship: `shared_value_{Q_ID}`
- Weight: Number of shared values

**Edge Attributes:**
- `shared_values`: List of shared Wikidata Q IDs
- `value_count`: Number of shared values
- `source_properties`: Properties used by source entry
- `target_properties`: Properties used by target entry

## Implementation Architecture

### Module Structure

```
encyclopedia/utils/knowledge_graph/
├── __init__.py
├── graph_builder.py          # Main graph creation class
├── wikipedia_extractor.py    # Extract links from Wikipedia descriptions
├── wikidata_extractor.py     # Extract Wikidata relationships
├── weight_calculator.py      # Calculate edge weights
└── graph_exporter.py         # Export to various formats
```

### Core Classes

#### 1. `KnowledgeGraphBuilder`

**Purpose:** Main class for building knowledge graphs from encyclopedias

**Methods:**
```python
class KnowledgeGraphBuilder:
    def __init__(self, encyclopedia: AmiEncyclopedia):
        """Initialize with encyclopedia."""
    
    def build_graph(self, 
                   include_wikipedia_links: bool = True,
                   include_wikidata_ancestry: bool = True,
                   include_wikidata_parts: bool = True,
                   include_shared_properties: bool = True,
                   include_shared_values: bool = True) -> nx.DiGraph:
        """Build complete knowledge graph."""
    
    def add_wikipedia_links(self, graph: nx.DiGraph) -> nx.DiGraph:
        """Add edges from Wikipedia description links."""
    
    def add_shared_link_weights(self, graph: nx.DiGraph) -> nx.DiGraph:
        """Add weighted edges based on shared Wikipedia links."""
    
    def add_wikidata_ancestry(self, graph: nx.DiGraph) -> nx.DiGraph:
        """Add Wikidata ancestry relationships."""
    
    def add_wikidata_parts(self, graph: nx.DiGraph) -> nx.DiGraph:
        """Add Wikidata part-whole relationships."""
    
    def add_shared_properties(self, graph: nx.DiGraph) -> nx.DiGraph:
        """Add edges for entries sharing Wikidata properties."""
    
    def add_shared_values(self, graph: nx.DiGraph) -> nx.DiGraph:
        """Add edges for entries sharing Wikidata property values."""
```

#### 2. `WikipediaLinkExtractor`

**Purpose:** Extract links from Wikipedia descriptions

**Methods:**
```python
class WikipediaLinkExtractor:
    def extract_links_from_description(self, description_html: str) -> List[Dict]:
        """Extract Wikipedia links from HTML description.
        
        Returns:
            List of dicts with:
            - 'url': Wikipedia URL
            - 'text': Link text
            - 'target_term': Extracted term from URL
            - 'target_wikidata_id': Wikidata ID if found
        """
    
    def find_target_entry(self, url: str, encyclopedia: AmiEncyclopedia) -> Optional[Dict]:
        """Find encyclopedia entry matching Wikipedia URL."""
    
    def count_link_occurrences(self, source_entry: Dict, target_entry: Dict) -> int:
        """Count how many times source links to target."""
```

#### 3. `WikidataRelationshipExtractor`

**Purpose:** Extract relationships from Wikidata

**Methods:**
```python
class WikidataRelationshipExtractor:
    def fetch_wikidata_properties(self, wikidata_id: str) -> Dict:
        """Fetch Wikidata properties for an entity.
        
        Returns:
            Dict mapping property IDs (P31, P279, etc.) to lists of values (Q IDs)
        """
    
    def extract_ancestry_relationships(self, entry: Dict) -> List[Dict]:
        """Extract instance of, subclass of relationships.
        
        Returns:
            List of dicts with:
            - 'property_id': P31, P279, etc.
            - 'target_id': Target Wikidata Q ID
            - 'property_label': Human-readable name
        """
    
    def extract_part_relationships(self, entry: Dict) -> List[Dict]:
        """Extract part-whole relationships.
        
        Returns:
            List of dicts with:
            - 'property_id': P527, P361, etc.
            - 'target_id': Target Wikidata Q ID
            - 'direction': 'has_part' or 'part_of'
        """
    
    def find_shared_properties(self, entry1: Dict, entry2: Dict) -> List[Dict]:
        """Find shared properties between two entries.
        
        Returns:
            List of dicts with:
            - 'property_id': Shared property ID
            - 'value_id': Shared value ID
            - 'property_label': Human-readable name
        """
```

#### 4. `EdgeWeightCalculator`

**Purpose:** Calculate weights for graph edges

**Methods:**
```python
class EdgeWeightCalculator:
    def calculate_shared_link_weight(self, entry1: Dict, entry2: Dict) -> float:
        """Calculate weight based on shared Wikipedia links.
        
        Uses Jaccard similarity: |A ∩ B| / |A ∪ B|
        """
    
    def calculate_cooccurrence_weight(self, entry1: Dict, entry2: Dict) -> float:
        """Calculate weight based on co-occurrence in descriptions."""
    
    def calculate_property_similarity(self, entry1: Dict, entry2: Dict) -> float:
        """Calculate similarity based on shared Wikidata properties."""
    
    def normalize_weight(self, weight: float, min_weight: float = 0.0, 
                        max_weight: float = 1.0) -> float:
        """Normalize weight to [0, 1] range."""
```

#### 5. `GraphExporter`

**Purpose:** Export graphs to various formats

**Methods:**
```python
class GraphExporter:
    def export_graphml(self, graph: nx.DiGraph, output_path: Path) -> Path:
        """Export to GraphML format."""
    
    def export_gexf(self, graph: nx.DiGraph, output_path: Path) -> Path:
        """Export to GEXF format (for Gephi)."""
    
    def export_rdf_turtle(self, graph: nx.DiGraph, output_path: Path) -> Path:
        """Export to RDF/Turtle format."""
    
    def export_json(self, graph: nx.DiGraph, output_path: Path) -> Path:
        """Export to JSON format."""
```

## Data Structures

### Node Attributes

```python
{
    'wikidata_id': str,           # Q ID (e.g., "Q7942")
    'term': str,                  # Human-readable term
    'canonical_term': str,        # Canonical term
    'wikipedia_url': str,         # Wikipedia URL
    'description': str,           # First 200 chars of description
    'entry_type': str,            # 'entry' or 'external'
    'node_type': str              # 'entity'
}
```

### Edge Attributes

```python
{
    'relationship_type': str,     # 'wikipedia_link', 'P31', 'shared_property', etc.
    'property_id': str,           # Wikidata property ID (P31, P279, etc.) or None
    'weight': float,              # Edge weight (0.0 to 1.0)
    'link_count': int,            # Number of times link appears
    'link_text': str,             # Anchor text from Wikipedia link
    'shared_articles': List[str],  # List of shared Wikipedia articles
    'shared_properties': List[str], # List of shared property IDs
    'shared_values': List[str],    # List of shared value Q IDs
    'jaccard_similarity': float,  # Jaccard coefficient
    'source_description': str,    # Excerpt from source entry
    'qualifiers': Dict            # Wikidata qualifiers (if any)
}
```

## Implementation Details

### 1. Wikipedia Link Extraction

**Process:**
1. Parse `description_html` using `lxml.html`
2. Extract all `<a>` tags with `href` containing `wikipedia.org/wiki/`
3. Extract link text and URL
4. Normalize URL to extract term
5. Match term to encyclopedia entries (by Wikipedia URL or term)
6. Create edges with source and target Wikidata IDs

**Code Example:**
```python
from lxml.html import fromstring

def extract_wikipedia_links(description_html: str) -> List[Dict]:
    """Extract Wikipedia links from HTML description."""
    root = fromstring(description_html)
    links = []
    
    for a_tag in root.xpath('.//a[@href]'):
        href = a_tag.get('href', '')
        if 'wikipedia.org/wiki/' in href:
            link_text = a_tag.text_content()
            # Normalize URL to extract term
            term = href.split('/wiki/')[-1].replace('_', ' ')
            links.append({
                'url': href,
                'text': link_text,
                'term': term
            })
    
    return links
```

### 2. Wikidata Property Fetching

**Process:**
1. Use Wikidata SPARQL API or Python library (e.g., `wikidata` package)
2. Query for properties: P31, P279, P527, P361, etc.
3. Cache results to avoid repeated API calls
4. Handle missing Wikidata IDs gracefully

**Code Example:**
```python
from wikidata.client import Client

def fetch_wikidata_properties(wikidata_id: str) -> Dict:
    """Fetch Wikidata properties for an entity."""
    client = Client()
    entity = client.get(wikidata_id, load=True)
    
    properties = {}
    for prop_id, claims in entity.data.get('claims', {}).items():
        values = []
        for claim in claims:
            if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                value = claim['mainsnak']['datavalue']['value']
                if 'id' in value:  # Q ID
                    values.append(value['id'])
        if values:
            properties[prop_id] = values
    
    return properties
```

### 3. Weight Calculation

**Shared Link Weight (Jaccard Similarity):**
```python
def calculate_shared_link_weight(entry1: Dict, entry2: Dict) -> float:
    """Calculate Jaccard similarity based on shared Wikipedia links."""
    links1 = set(entry1.get('wikipedia_links', []))
    links2 = set(entry2.get('wikipedia_links', []))
    
    if not links1 or not links2:
        return 0.0
    
    intersection = len(links1 & links2)
    union = len(links1 | links2)
    
    return intersection / union if union > 0 else 0.0
```

**Property Similarity:**
```python
def calculate_property_similarity(entry1: Dict, entry2: Dict) -> float:
    """Calculate similarity based on shared Wikidata properties."""
    props1 = set(entry1.get('wikidata_properties', {}).keys())
    props2 = set(entry2.get('wikidata_properties', {}).keys())
    
    if not props1 or not props2:
        return 0.0
    
    intersection = len(props1 & props2)
    union = len(props1 | props2)
    
    return intersection / union if union > 0 else 0.0
```

## Integration Points

### 1. CLI Integration

**Add to `encyclopedia/cli/versioned_editor.py`:**

```python
# New command: graph
graph_parser = subparsers.add_parser('graph', help='Create knowledge graph from encyclopedia')
graph_parser.add_argument('--input', type=Path, required=True, help='Input encyclopedia HTML file')
graph_parser.add_argument('--output', type=Path, required=True, help='Output graph file')
graph_parser.add_argument('--format', choices=['graphml', 'gexf', 'rdf', 'json'], 
                          default='graphml', help='Output format')
graph_parser.add_argument('--include-wikipedia', action='store_true', 
                          help='Include Wikipedia description links')
graph_parser.add_argument('--include-wikidata', action='store_true', 
                          help='Include Wikidata relationships')
graph_parser.add_argument('--min-weight', type=float, default=0.0,
                          help='Minimum edge weight to include')
```

### 2. Script Integration

**Create `Examples/create_knowledge_graph.py`:**

```python
#!/usr/bin/env python3
"""
Create knowledge graph from encyclopedia.

Usage:
    python Examples/create_knowledge_graph.py \
        --input encyclopedia.html \
        --output knowledge_graph.graphml \
        --format graphml \
        --include-wikipedia \
        --include-wikidata
"""

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.knowledge_graph import KnowledgeGraphBuilder
from pathlib import Path
import argparse

def main():
    parser = argparse.ArgumentParser(description='Create knowledge graph from encyclopedia')
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--format', choices=['graphml', 'gexf', 'rdf', 'json'], 
                       default='graphml')
    parser.add_argument('--include-wikipedia', action='store_true')
    parser.add_argument('--include-wikidata', action='store_true')
    parser.add_argument('--min-weight', type=float, default=0.0)
    
    args = parser.parse_args()
    
    # Load encyclopedia
    encyclopedia = AmiEncyclopedia()
    encyclopedia.create_from_html_file(args.input)
    
    # Build graph
    builder = KnowledgeGraphBuilder(encyclopedia)
    graph = builder.build_graph(
        include_wikipedia_links=args.include_wikipedia,
        include_wikidata_ancestry=args.include_wikidata,
        include_wikidata_parts=args.include_wikidata,
        include_shared_properties=args.include_wikidata,
        include_shared_values=args.include_wikidata
    )
    
    # Filter by minimum weight
    if args.min_weight > 0.0:
        graph = filter_graph_by_weight(graph, args.min_weight)
    
    # Export
    exporter = GraphExporter()
    if args.format == 'graphml':
        exporter.export_graphml(graph, args.output)
    elif args.format == 'gexf':
        exporter.export_gexf(graph, args.output)
    # ... etc

if __name__ == '__main__':
    main()
```

## Testing Strategy

### Test Cases

1. **Wikipedia Link Extraction:**
   - Extract links from HTML descriptions
   - Match links to encyclopedia entries
   - Count link occurrences
   - Handle missing target entries

2. **Shared Link Weight Calculation:**
   - Calculate Jaccard similarity
   - Handle empty link sets
   - Normalize weights

3. **Wikidata Relationship Extraction:**
   - Fetch properties from Wikidata API
   - Extract ancestry relationships
   - Extract part-whole relationships
   - Handle missing Wikidata IDs

4. **Shared Property Detection:**
   - Find entries with shared properties
   - Find entries with shared values
   - Calculate property similarity

5. **Graph Export:**
   - Export to GraphML
   - Export to GEXF
   - Export to RDF/Turtle
   - Verify graph structure

### Test Fixtures

- Small encyclopedia with known Wikipedia links
- Entries with Wikidata IDs and properties
- Test data with shared properties/values

## Dependencies

**New Dependencies:**
- `networkx` - Graph creation and manipulation (may already be dependency)
- `wikidata` or `wikidata-api` - Wikidata API access
- `rdflib` - RDF/Turtle export (optional)

**Existing Dependencies:**
- `lxml` - HTML parsing (already used)
- `pandas` - Data manipulation (already used)

## Output Formats

### GraphML Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="wikidata_id" for="node" attr.name="wikidata_id" attr.type="string"/>
  <key id="term" for="node" attr.name="term" attr.type="string"/>
  <key id="relationship_type" for="edge" attr.name="relationship_type" attr.type="string"/>
  <key id="property_id" for="edge" attr.name="property_id" attr.type="string"/>
  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>
  
  <graph id="G" edgedefault="directed">
    <node id="Q7942">
      <data key="wikidata_id">Q7942</data>
      <data key="term">climate change</data>
    </node>
    <node id="Q131784">
      <data key="wikidata_id">Q131784</data>
      <data key="term">greenhouse gas</data>
    </node>
    
    <edge source="Q7942" target="Q131784">
      <data key="relationship_type">wikipedia_link</data>
      <data key="weight">0.5</data>
      <data key="link_count">3</data>
    </edge>
    
    <edge source="Q7942" target="Q7937">
      <data key="relationship_type">P31</data>
      <data key="property_id">P31</data>
      <data key="weight">1.0</data>
    </edge>
  </graph>
</graphml>
```

### RDF/Turtle Example

```turtle
@prefix wd: <http://www.wikidata.org/entity/> .
@prefix wdt: <http://www.wikidata.org/prop/direct/> .
@prefix kg: <http://example.org/kg/> .

wd:Q7942 kg:term "climate change" .
wd:Q7942 wdt:P31 wd:Q7937 .
wd:Q7942 kg:wikipedia_link wd:Q131784 .
wd:Q7942 kg:weight "0.5"^^xsd:double .
```

## Performance Considerations

1. **Caching:** Cache Wikidata API responses to avoid repeated calls
2. **Batch Processing:** Process entries in batches for large encyclopedias
3. **Parallel Processing:** Use multiprocessing for Wikidata API calls
4. **Incremental Updates:** Support adding relationships to existing graphs

## Future Enhancements

1. **Relationship Inference:** Infer transitive relationships (e.g., if A is instance of B, and B is instance of C, then A is instance of C)
2. **Temporal Relationships:** Extract temporal relationships from Wikidata
3. **Geographic Relationships:** Extract geographic relationships
4. **Visualization:** Integration with graph visualization tools
5. **Query Interface:** SPARQL endpoint for querying the graph

## Questions for Discussion

1. **Wikidata API:** Should we use the Wikidata Python library or direct SPARQL queries?
2. **Caching Strategy:** How should we cache Wikidata data? File-based or in-memory?
3. **Weight Normalization:** Should weights be normalized globally or per relationship type?
4. **External Entities:** Should we include external Wikidata entities (not in encyclopedia) as nodes?
5. **Property Filtering:** Which Wikidata properties should we include/exclude?
6. **Performance:** What's the expected size of encyclopedias? Should we optimize for large graphs?

## References

- **NetworkX Documentation:** https://networkx.org/documentation/
- **Wikidata API:** https://www.wikidata.org/wiki/Wikidata:Data_access
- **GraphML Specification:** http://graphml.graphdrawing.org/
- **RDF/Turtle:** https://www.w3.org/TR/turtle/
