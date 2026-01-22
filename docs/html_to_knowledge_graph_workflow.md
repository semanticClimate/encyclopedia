# Workflow: HTML with IDs → Wordlist → Dictionary → Encyclopedia → Knowledge Graph

## Overview

This document outlines the complete workflow for transforming an HTML chapter with IDs into a knowledge graph, passing through wordlist extraction, dictionary creation, and encyclopedia generation.

## Complete Pipeline

```
HTML Chapter (with IDs)
    ↓
1. Extract Wordlist
    ↓
2. Create Dictionary
    ↓
3. Create Encyclopedia
    ↓
4. Generate Knowledge Graph
```

---

## Step 1: HTML with IDs → Wordlist

### Option A: Extract Keywords from HTML Text

**Software**: `Keyword_extraction/Keyword_extraction.py`  
**Model**: `ml6team/keyphrase-extraction-kbir-inspec` (Hugging Face Transformers)

**Process**:
1. Convert HTML to text using `html_to_txt.py`
2. Extract keywords using transformer model
3. Output CSV with keywords and counts

**Command**:
```bash
# Step 1a: Convert HTML to text
python Keyword_extraction/html_to_txt.py \
    -i /path/to/html_folder \
    -o /path/to/txt_folder

# Step 1b: Extract keywords from text
python Keyword_extraction/Keyword_extraction.py \
    -i /path/to/txt_folder \
    -o /path/to/keywords_output \
    -n 1000  # top N keywords
```

**Parameters**:
- `-i, --input_folder`: Folder containing HTML files
- `-o, --output_folder`: Folder to save outputs
- `-n, --top_n`: Number of top keywords to extract (default: 3500)

**Output**: CSV file with columns: `keyword`, `count`

**Python API**:
```python
from Keyword_extraction.Keyword_extraction import KeywordExtraction

extractor = KeywordExtraction(
    textfile="input.txt",
    saving_path="output/",
    output_filename="keywords.csv",
    top_n=1000
)
top_keywords = extractor.extract_keywords()
```

### Option B: Extract IDs Directly from HTML

**Software**: `amilib.ami_html.HtmlLib`  
**Method**: `extract_ids_from_html_page()`

**Process**:
1. Parse HTML file
2. Extract IDs using regex pattern matching spans
3. Extract text content associated with IDs

**Python API**:
```python
from amilib.ami_html import HtmlLib
import re

# Extract IDs using regex (e.g., section numbers like "1.2.3")
regex_str = r'^(\d+\.\d+(?:\.\d+)?)'  # Matches section numbers
spans = HtmlLib.extract_ids_from_html_page(
    input_html_path="chapter.html",
    regex_str=regex_str,
    debug=True
)

# Extract terms from spans
terms = [span.text.strip() for span in spans]
```

**Parameters**:
- `input_html_path`: Path to HTML file
- `regex_str`: Regular expression pattern to match IDs
- `debug`: Print debug information (default: False)

**Output**: List of span elements matching the regex pattern

---

## Step 2: Wordlist → Dictionary

**Software**: `amilib.ami_dict.AmiDictionary`  
**Method**: `create_dictionary_from_words()` or `create_dictionary_from_wordfile()`

**Process**:
1. Read wordlist (list of terms or text file)
2. Create basic dictionary structure with entry elements
3. Initialize AmiDictionary object

**Command** (from Python):
```python
from amilib.ami_dict import AmiDictionary
from pathlib import Path

# Option A: From list of terms
terms = ["climate change", "greenhouse gas", "carbon cycle"]
dictionary, outpath = AmiDictionary.create_dictionary_from_words(
    terms=terms,
    title="climate_terms",
    wikidata=False,  # Set to True to add Wikidata IDs
    outdir=Path("output")
)

# Option B: From text file (one term per line)
dictionary, outpath = AmiDictionary.create_dictionary_from_wordfile(
    wordfile="wordlist.txt",
    title="my_dictionary",
    wikidata=False,
    outdir=Path("output"),
    max_entries=1000000
)
```

**Parameters**:
- `terms`: List of strings (for `create_dictionary_from_words`)
- `wordfile`: Path to text file (for `create_dictionary_from_wordfile`)
- `title`: Dictionary title (max 30 chars, lowercase, no spaces)
- `wikidata`: If True, lookup Wikidata IDs (default: False)
- `outdir`: Output directory for XML dictionary file
- `max_entries`: Maximum number of entries (default: 1000000)

**Output**: 
- `AmiDictionary` object with `entry_by_term` dictionary
- XML dictionary file at `outdir/title.xml`

**Enhancement Options** (after creation):
```python
# Add Wikipedia content
dictionary.add_wikipedia_page(term)

# Add Wikidata content
dictionary.add_wikidata_from_terms()

# Add Wiktionary content
dictionary.add_wiktionary_from_terms()
```

---

## Step 3: Dictionary → Encyclopedia

**Software**: `encyclopedia.core.encyclopedia.AmiEncyclopedia`  
**Methods**: `create_from_html_content()`, `normalize_by_wikidata_id()`, `merge()`

**Process**:
1. Convert dictionary to HTML format
2. Parse HTML dictionary and extract entries
3. Normalize entries by Wikidata ID (group synonyms)
4. Merge entries with same Wikidata ID
5. Generate final HTML encyclopedia

**Command** (from Python):
```python
from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.encyclopedia_builder import (
    create_dictionary_from_terms,
    enhance_dictionary_with_wikipedia,
    convert_dictionary_to_encyclopedia
)

# Step 3a: Enhance dictionary with Wikipedia (optional)
dictionary = enhance_dictionary_with_wikipedia(dictionary, verbose=True)

# Step 3b: Convert dictionary to encyclopedia
encyclopedia = convert_dictionary_to_encyclopedia(
    dictionary=dictionary,
    temp_path=Path("temp"),
    title="My Encyclopedia"
)

# Step 3c: Normalize by Wikidata ID
encyclopedia.normalize_by_wikidata_id()

# Step 3d: Merge synonyms
encyclopedia.merge()

# Step 3e: Save to HTML
encyclopedia.save_wiki_normalized_html("encyclopedia.html")
```

**Alternative: Direct from HTML Content**:
```python
# If you already have HTML dictionary
encyclopedia = AmiEncyclopedia(title="My Encyclopedia")
encyclopedia.create_from_html_content(html_content)
encyclopedia.normalize_by_wikidata_id()
encyclopedia.merge()
```

**Parameters**:
- `dictionary`: AmiDictionary object
- `temp_path`: Temporary directory for HTML file
- `title`: Title for the encyclopedia
- `html_content`: HTML string (if using `create_from_html_content`)

**Output**: 
- `AmiEncyclopedia` object with:
  - `entries`: List of entry dictionaries
  - `normalized_entries`: Dictionary grouped by Wikidata ID
  - `merged_entries`: Merged entries with synonyms

**Entry Dictionary Structure**:
```python
{
    'term': str,                    # Primary term
    'search_term': str,             # Search term (may differ)
    'wikidata_id': str,             # Wikidata Q/P ID (e.g., "Q1997")
    'wikipedia_url': str,           # Full Wikipedia URL
    'description_html': str,        # HTML description (first paragraph)
    'figure_html': Element,         # Image element (lxml)
    'images': List[str],            # List of image HTML strings
}
```

**Complete Example Script**:
```python
from pathlib import Path
from encyclopedia.core.encyclopedia import AmiEncyclopedia
from Examples.create_encyclopedia_from_wordlist import create_encyclopedia_from_wordlist

# Read wordlist from file
with open("wordlist.txt", "r") as f:
    terms = [line.strip() for line in f if line.strip()]

# Create encyclopedia
encyclopedia = create_encyclopedia_from_wordlist(
    terms=terms,
    title="Climate Encyclopedia",
    add_wikipedia=True,
    add_images=False,
    batch_size=10,
    validate=True,
    verbose=False
)

# Save to HTML
encyclopedia.save_wiki_normalized_html("output.html")
```

---

## Step 4: Encyclopedia → Knowledge Graph

**Software**: `amilib.ami_graph.AmiGraph` or `networkx`  
**Format**: GraphML (XML-based graph format)

**Process**:
1. Extract entities from encyclopedia (terms with Wikidata IDs)
2. Extract relationships (from Wikipedia links, Wikidata properties)
3. Create graph structure (nodes = entities, edges = relationships)
4. Export to GraphML format

**Command** (from Python):
```python
import networkx as nx
from encyclopedia.core.encyclopedia import AmiEncyclopedia

# Load encyclopedia
encyclopedia = AmiEncyclopedia(title="My Encyclopedia")
encyclopedia.create_from_html_file("encyclopedia.html")

# Create graph
G = nx.DiGraph()  # Directed graph

# Add nodes (entities) from encyclopedia entries
for entry in encyclopedia.entries:
    if entry.get('wikidata_id'):
        node_id = entry['wikidata_id']
        G.add_node(
            node_id,
            term=entry['term'],
            wikipedia_url=entry.get('wikipedia_url', ''),
            description=entry.get('description_html', '')[:200]  # First 200 chars
        )

# Add edges (relationships) - example: Wikipedia links
for entry in encyclopedia.entries:
    if entry.get('wikidata_id'):
        source = entry['wikidata_id']
        # Extract links from description_html and add edges
        # (This is simplified - you'd parse HTML to extract actual links)
        # For now, we'll add edges based on shared categories or manual relationships

# Save to GraphML
nx.write_graphml(G, "knowledge_graph.graphml")
print(f"✅ Saved GraphML: knowledge_graph.graphml")
```

**Using amilib.ami_graph** (if available):
```python
from amilib.ami_graph import AmiGraph

# Create graph from encyclopedia
graph = AmiGraph.create_from_encyclopedia(encyclopedia)

# Export to GraphML
graphml_path = "output/knowledge_graph.graphml"
graph.export_graphml(graphml_path)
```

**Parameters**:
- `encyclopedia`: AmiEncyclopedia object
- `output_path`: Path to save GraphML file

**Output**: GraphML file (`.graphml`) containing:
- Nodes: Entities (terms) with Wikidata IDs
- Edges: Relationships between entities
- Attributes: Term names, Wikipedia URLs, descriptions

**GraphML Format**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="term" for="node" attr.name="term" attr.type="string"/>
  <key id="wikidata_id" for="node" attr.name="wikidata_id" attr.type="string"/>
  <graph id="G" edgedefault="directed">
    <node id="Q7942">
      <data key="term">climate change</data>
      <data key="wikidata_id">Q7942</data>
    </node>
    <!-- More nodes... -->
    <edge source="Q7942" target="Q13138">
      <data key="relationship">related_to</data>
    </edge>
    <!-- More edges... -->
  </graph>
</graphml>
```

**Visualization**:
GraphML files can be visualized using:
- **yEd Graph Editor**: https://www.yworks.com/products/yed
- **Gephi**: https://gephi.org/
- **Cytoscape**: https://cytoscape.org/
- **NetworkX** (Python): `nx.read_graphml()` then visualize with matplotlib

---

## Complete Workflow Example

```python
#!/usr/bin/env python3
"""
Complete workflow: HTML → Wordlist → Dictionary → Encyclopedia → Knowledge Graph
"""

from pathlib import Path
import networkx as nx
from amilib.ami_dict import AmiDictionary
from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.encyclopedia_builder import (
    create_dictionary_from_terms,
    enhance_dictionary_with_wikipedia,
    convert_dictionary_to_encyclopedia
)

# Step 1: Extract wordlist from HTML
# (Assuming you've already extracted terms using Keyword_extraction.py)
terms = ["climate change", "greenhouse gas", "carbon cycle", "global warming"]

# Step 2: Create dictionary
temp_path = Path("temp")
temp_path.mkdir(exist_ok=True)

dictionary, _ = AmiDictionary.create_dictionary_from_words(
    terms=terms,
    title="climate_terms",
    wikidata=False,
    outdir=temp_path
)

# Step 3: Enhance with Wikipedia
dictionary = enhance_dictionary_with_wikipedia(dictionary, verbose=True)

# Step 4: Convert to encyclopedia
encyclopedia = convert_dictionary_to_encyclopedia(
    dictionary=dictionary,
    temp_path=temp_path,
    title="Climate Encyclopedia"
)

# Step 5: Normalize and merge
encyclopedia.normalize_by_wikidata_id()
encyclopedia.merge()

# Step 6: Save encyclopedia HTML
encyclopedia.save_wiki_normalized_html("climate_encyclopedia.html")

# Step 7: Create knowledge graph
G = nx.DiGraph()

for entry in encyclopedia.entries:
    if entry.get('wikidata_id'):
        node_id = entry['wikidata_id']
        G.add_node(
            node_id,
            term=entry['term'],
            wikipedia_url=entry.get('wikipedia_url', ''),
            description=entry.get('description_html', '')[:200]
        )

# Step 8: Save GraphML
nx.write_graphml(G, "climate_knowledge_graph.graphml")
print("✅ Complete! Created:")
print("  - climate_encyclopedia.html")
print("  - climate_knowledge_graph.graphml")
```

---

## Software Dependencies

### Required Packages

```bash
pip install amilib
pip install transformers
pip install beautifulsoup4
pip install networkx
pip install lxml
pip install pandas
pip install tqdm
```

### Key Modules

1. **amilib** (external package):
   - `amilib.ami_dict.AmiDictionary`
   - `amilib.ami_html.HtmlLib`
   - `amilib.wikimedia.WikipediaPage`
   - `amilib.ami_graph.AmiGraph` (if available)

2. **encyclopedia** (local package):
   - `encyclopedia.core.encyclopedia.AmiEncyclopedia`
   - `encyclopedia.utils.encyclopedia_builder`

3. **Keyword_extraction** (local):
   - `Keyword_extraction.Keyword_extraction.KeywordExtraction`
   - `Keyword_extraction.html_to_txt.html_to_txt_folder`

---

## References

- [Encyclopedia Pipeline Documentation](encyclopedia_pipeline_documentation.md)
- [Create Encyclopedia from Wordlist Summary](create_encyclopedia_from_wordlist_summary.md)
- [Encyclopedia Creation Review](encyclopedia_creation_review.md)
- [Examples README](../Examples/README_create_encyclopedia.md)
