# Knowledge Graph Implementation Decisions

**Date:** March 2, 2026 (system date)  
**Status:** Decisions Made

## 1. Wikidata API Approach: Library vs SPARQL

### Recommendation: **SPARQL** (with optional library wrapper)

### Why SPARQL?

**Advantages:**
1. **Direct Control:** You write queries exactly as needed - no library abstraction layer
2. **Efficiency:** Can fetch multiple properties for multiple entities in single query
3. **Flexibility:** Complex queries (e.g., "find all entities with P31=Q7937 AND P279=Q11421")
4. **Standard:** SPARQL is the standard query language for RDF/Wikidata
5. **Batch Queries:** Can query hundreds of entities at once
6. **No External Dependencies:** Uses standard HTTP requests (requests library)
7. **You Have Experience:** You've used SPARQL before, so less learning curve

**Example SPARQL Query:**
```sparql
SELECT ?entity ?property ?value WHERE {
  VALUES ?entity { wd:Q7942 wd:Q131784 wd:Q7937 }
  ?entity ?property ?value .
  FILTER(?property IN (wdt:P31, wdt:P279, wdt:P527, wdt:P361))
}
```

**Disadvantages:**
- More verbose than library calls
- Need to handle SPARQL syntax yourself
- Query construction can be complex

### Why NOT Library?

**Library Disadvantages:**
- **Rate Limiting:** Libraries often make one API call per entity/property
- **Less Efficient:** Can't batch queries easily
- **Dependency:** Another external package to maintain
- **Less Flexible:** Limited to library's API design
- **Slower:** Multiple HTTP requests vs single SPARQL query

**Library Advantages:**
- Simpler API for simple queries
- Handles authentication/rate limiting automatically
- More Pythonic interface

### Recommendation Implementation:

**Use SPARQL with a simple wrapper function:**

```python
def fetch_wikidata_properties_sparql(wikidata_ids: List[str], 
                                     property_ids: List[str] = None) -> Dict:
    """
    Fetch Wikidata properties for multiple entities using SPARQL.
    
    Args:
        wikidata_ids: List of Wikidata Q IDs (e.g., ["Q7942", "Q131784"])
        property_ids: List of property IDs to fetch (e.g., ["P31", "P279"])
                     If None, fetches all properties
    
    Returns:
        Dict mapping entity ID to dict of properties
        {
            "Q7942": {
                "P31": ["Q7937"],  # instance of Climate
                "P279": ["Q11421"]  # subclass of Gas
            }
        }
    """
    import requests
    
    # Build SPARQL query
    entity_list = " ".join([f"wd:{qid}" for qid in wikidata_ids])
    property_filter = ""
    if property_ids:
        prop_list = " ".join([f"wdt:{pid}" for pid in property_ids])
        property_filter = f"FILTER(?property IN ({prop_list}))"
    
    query = f"""
    SELECT ?entity ?property ?value WHERE {{
      VALUES ?entity {{ {entity_list} }}
      ?entity ?property ?value .
      {property_filter}
      FILTER(STRSTARTS(STR(?property), "http://www.wikidata.org/prop/direct/"))
    }}
    """
    
    # Execute query
    url = "https://query.wikidata.org/sparql"
    response = requests.get(url, params={'query': query, 'format': 'json'})
    results = response.json()
    
    # Parse results
    properties = {}
    for binding in results['results']['bindings']:
        entity = binding['entity']['value'].split('/')[-1]  # Extract Q ID
        prop = binding['property']['value'].split('/')[-1]  # Extract P ID
        value = binding['value']['value'].split('/')[-1]  # Extract Q ID
        
        if entity not in properties:
            properties[entity] = {}
        if prop not in properties[entity]:
            properties[entity][prop] = []
        properties[entity][prop].append(value)
    
    return properties
```

**Benefits:**
- Single HTTP request for multiple entities
- Can fetch all needed properties at once
- Efficient batch processing
- No external library dependency (just `requests`)

---

## 2. Caching Strategy

### Your Suggestion: Inverted Index for Hyperlinks

**Your idea:** Index where each Wikipedia hyperlink maps to list of encyclopedia entries containing it.

**Example:**
```python
{
    "/wiki/Greenhouse_gas": [entry_id_1, entry_id_2, entry_id_3],
    "/wiki/Carbon_dioxide": [entry_id_1, entry_id_4],
    ...
}
```

### Analysis: This is Excellent!

**Why Your Approach Works Well:**

1. **Fast Lookup:** O(1) lookup for "which entries link to X?"
2. **Shared Link Calculation:** Easy to find shared links between entries
3. **Weight Calculation:** Can quickly calculate Jaccard similarity
4. **Memory Efficient:** Only stores what's needed (links present in encyclopedia)

### Enhanced Caching Strategy

**Multi-Level Caching:**

#### Level 1: Wikipedia Link Index (Your Suggestion)
```python
wikipedia_link_index = {
    "/wiki/Greenhouse_gas": {
        'entries': [entry_id_1, entry_id_2, entry_id_3],
        'count': 3,
        'entry_terms': ['climate change', 'global warming', 'atmosphere']
    },
    ...
}
```

**Use Cases:**
- Find entries linking to specific Wikipedia article
- Calculate shared links between entries
- Count link occurrences

#### Level 2: Wikidata Properties Cache
```python
wikidata_properties_cache = {
    "Q7942": {
        "P31": ["Q7937"],  # instance of
        "P279": ["Q11421"],  # subclass of
        "fetched_at": "2026-03-02T12:00:00Z"
    },
    ...
}
```

**Use Cases:**
- Avoid repeated SPARQL queries for same entity
- Extract ancestry relationships
- Find shared properties

#### Level 3: Entry-to-Entry Link Cache
```python
entry_link_cache = {
    (entry_id_1, entry_id_2): {
        'wikipedia_links': 3,
        'shared_articles': ['Greenhouse_gas', 'Carbon_dioxide'],
        'jaccard_similarity': 0.5,
        'calculated_at': "2026-03-02T12:00:00Z"
    },
    ...
}
```

**Use Cases:**
- Cache calculated edge weights
- Avoid recalculating Jaccard similarity
- Store pre-computed relationships

### Implementation Strategy

**Build Indexes During Graph Creation:**

```python
class KnowledgeGraphBuilder:
    def __init__(self, encyclopedia: AmiEncyclopedia):
        self.encyclopedia = encyclopedia
        self.wikipedia_link_index = {}  # Your inverted index
        self.wikidata_cache = {}
        self.edge_cache = {}
    
    def build_indexes(self):
        """Build all indexes before graph creation."""
        # Build Wikipedia link index
        for entry in self.encyclopedia.entries:
            links = self._extract_wikipedia_links(entry)
            for link_url in links:
                if link_url not in self.wikipedia_link_index:
                    self.wikipedia_link_index[link_url] = {
                        'entries': [],
                        'count': 0
                    }
                self.wikipedia_link_index[link_url]['entries'].append(entry['id'])
                self.wikipedia_link_index[link_url]['count'] += 1
        
        # Build Wikidata properties cache (batch SPARQL query)
        wikidata_ids = [e['wikidata_id'] for e in self.encyclopedia.entries 
                       if e.get('wikidata_id')]
        self.wikidata_cache = fetch_wikidata_properties_sparql(wikidata_ids)
```

**Benefits:**
- Build once, use many times
- Fast lookups during graph creation
- Can save indexes to disk for reuse
- Memory efficient (only stores what's needed)

---

## 3. Weight Normalization Approach

### Recommendation: **Per-Relationship-Type Normalization**

**Why:** Different relationship types have different weight scales:
- Wikipedia link counts: 1-10 typically
- Shared link Jaccard: 0.0-1.0
- Shared property count: 1-5 typically

### Normalization Strategy

**Option A: Per-Type Normalization (Recommended)**
```python
def normalize_weight(weight: float, relationship_type: str) -> float:
    """
    Normalize weight based on relationship type.
    
    Each relationship type has its own normalization:
    - wikipedia_link: Count → [0, 1] using log normalization
    - shared_links: Jaccard → Already [0, 1]
    - shared_properties: Count → [0, 1] using max normalization
    """
    if relationship_type == 'wikipedia_link':
        # Log normalization: log(1 + count) / log(1 + max_count)
        return math.log(1 + weight) / math.log(1 + 10)  # Assume max 10 links
    
    elif relationship_type == 'shared_links':
        # Already normalized (Jaccard similarity)
        return weight
    
    elif relationship_type.startswith('shared_property'):
        # Max normalization: count / max_count
        return min(weight / 5.0, 1.0)  # Assume max 5 shared properties
    
    elif relationship_type.startswith('P'):  # Wikidata property
        # Binary or count-based
        return 1.0 if weight > 0 else 0.0
    
    return weight
```

**Option B: Global Normalization**
```python
def normalize_weight_global(weight: float, all_weights: List[float]) -> float:
    """Normalize weight globally across all edges."""
    min_weight = min(all_weights)
    max_weight = max(all_weights)
    if max_weight == min_weight:
        return 1.0
    return (weight - min_weight) / (max_weight - min_weight)
```

**Recommendation:** Use **Option A (Per-Type)** because:
- Preserves meaning of each relationship type
- Easier to interpret weights
- Can combine different relationship types meaningfully
- More intuitive for users

**Combining Multiple Weights:**
```python
def combine_edge_weights(weights: Dict[str, float]) -> float:
    """
    Combine weights from multiple relationship types.
    
    Args:
        weights: Dict mapping relationship_type to normalized weight
    
    Returns:
        Combined weight (weighted average)
    """
    # Weight each relationship type differently
    type_weights = {
        'wikipedia_link': 0.3,
        'shared_links': 0.4,
        'shared_properties': 0.2,
        'P31': 0.1,  # instance of
        'P279': 0.1,  # subclass of
    }
    
    combined = 0.0
    total_weight = 0.0
    for rel_type, weight in weights.items():
        type_weight = type_weights.get(rel_type, 0.1)
        combined += weight * type_weight
        total_weight += type_weight
    
    return combined / total_weight if total_weight > 0 else 0.0
```

---

## 4. External Entities Inclusion

### What Are External Entities?

**External entities** = Wikidata entities (Q IDs) that are:
- Referenced in relationships (e.g., P31=Q7937)
- Linked from Wikipedia descriptions
- **BUT** not present as entries in the encyclopedia itself

### Examples:

**Scenario 1: Instance Of**
- Encyclopedia entry: "Climate change" (Q7942)
- Wikidata property: `P31` (instance of) = `Q7937` (Climate)
- **Q7937 (Climate) is NOT in encyclopedia** → External entity

**Scenario 2: Wikipedia Link**
- Encyclopedia entry: "Greenhouse gas" (Q131784)
- Wikipedia description links to "Atmosphere" (Q1151)
- **Q1151 (Atmosphere) is NOT in encyclopedia** → External entity

### Should We Include Them?

**Option A: Include External Entities (Recommended)**

**Pros:**
- **Complete Graph:** Shows full relationships, not just internal ones
- **Context:** External entities provide important context
- **Discovery:** Users can discover related concepts not in encyclopedia
- **Standard Practice:** Knowledge graphs typically include referenced entities

**Cons:**
- **Larger Graph:** More nodes and edges
- **Missing Data:** External entities won't have full encyclopedia metadata
- **Clutter:** May make graph harder to navigate

**Implementation:**
```python
# Include external entities as nodes
if target_wikidata_id not in encyclopedia_entry_ids:
    # External entity - add as node with minimal data
    graph.add_node(
        target_wikidata_id,
        term=extracted_term,  # From Wikipedia URL or Wikidata
        wikipedia_url=target_url,
        entry_type='external',  # Mark as external
        node_type='entity'
    )
```

**Option B: Exclude External Entities**

**Pros:**
- **Smaller Graph:** Only entries in encyclopedia
- **Complete Data:** All nodes have full encyclopedia metadata
- **Focused:** Graph shows only curated content

**Cons:**
- **Incomplete Relationships:** Missing important connections
- **Broken Links:** Edges pointing to non-existent nodes
- **Less Useful:** Can't see full relationship network

### Recommendation: **Include External Entities** (Option A)

**Rationale:**
1. Knowledge graphs are meant to show relationships, including external ones
2. External entities provide valuable context
3. Can filter them out during visualization if needed
4. Standard practice in knowledge graph construction

**With Filtering Option:**
```python
# CLI parameter
parser.add_argument('--include-external', action='store_true',
                   help='Include external Wikidata entities (not in encyclopedia)')

# Implementation
if args.include_external or target_wikidata_id in encyclopedia_entry_ids:
    graph.add_node(...)
```

**Default:** Include external entities, but allow filtering

---

## 5. Property Filtering

**Decision:** Wait for data

**Rationale:**
- Need to see which properties are actually present
- Some properties may be too common (e.g., P31 appears everywhere)
- Some properties may be domain-specific
- Can optimize based on actual usage patterns

**Approach:**
- Start with common properties: P31, P279, P527, P361
- Collect statistics on property frequency
- Filter based on:
  - Frequency (too common = less informative)
  - Domain relevance
  - User feedback

---

## 6. Performance Optimization

**Decision:** Wait for data

**Rationale:**
- Optimization depends on:
  - Encyclopedia size (10 entries vs 1000 entries)
  - Number of relationships per entry
  - Wikidata API response times
  - Available memory/CPU

**Potential Optimizations (to consider later):**
- Parallel SPARQL queries
- Incremental graph building
- Lazy loading of external entities
- Graph compression techniques
- Index optimization

---

## Summary of Decisions

1. **Wikidata API:** Use **SPARQL** with wrapper function (batch queries, efficient)
2. **Caching:** Use **inverted index** for Wikipedia links + Wikidata properties cache
3. **Weight Normalization:** **Per-relationship-type** normalization (preserves meaning)
4. **External Entities:** **Include** by default, allow filtering
5. **Property Filtering:** **Wait for data** - start with common properties
6. **Performance:** **Wait for data** - optimize based on actual usage
