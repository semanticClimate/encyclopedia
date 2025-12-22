# Encyclopedia Pipeline Documentation

**Date:** December 22, 2025  
**System Date:** Mon Dec 22 08:15:59 GMT 2025

## Overview

This document describes the encyclopedia generation pipeline, which transforms a list of terms/words into a structured, semantically enriched encyclopedia with Wikipedia, Wikidata, and Wiktionary content.

## Codebase Structure

**Important**: The encyclopedia pipeline code is primarily located in the `../amilib` repository, not in this `encyclopedia` repository.

### Code in `../amilib` (amilib repository)
- **Dictionary Creation**: `amilib/ami_dict.py` - All dictionary creation and management
- **Encyclopedia Management**: `amilib/ami_encyclopedia.py` - Encyclopedia creation, normalization, merging
- **Wikimedia Integration**: `amilib/wikimedia.py` - Wikipedia, Wikidata, Wiktionary lookups
- **HTML Processing**: `amilib/ami_html.py` - HTML generation and processing

### Code in this repository (`encyclopedia`)
- **Keyword Extraction**: `Keyword_extraction/` - Extracts keywords from documents (can provide terms for dictionary)
- **Dictionary Storage**: `Dictionary/` - Stores processed keywords and documents
- **Tests**: `test/text_links/` - Tests for encyclopedia link extraction and analysis
- **Documentation**: `docs/` - This documentation and pipeline diagrams

**Note**: To use the encyclopedia pipeline, you need to import from `amilib`:
```python
from amilib.ami_dict import AmiDictionary
from amilib.ami_encyclopedia import AmiEncyclopedia
```

## Pipeline Diagram

The pipeline is visualized in:
- **Graphviz DOT**: `encyclopedia_pipeline.dot`
- **SVG**: `encyclopedia_pipeline.svg`

## Pipeline Stages

### Stage 1: Input - Terms/Words

**Input**: A list of terms, words, or phrases (from keyword extraction, CSV files, or text files)

**Location in codebase** (all in `../amilib`):
- `../amilib/amilib/ami_dict.py` - `create_dictionary_from_words()`
- `../amilib/amilib/ami_dict.py` - `create_dictionary_from_wordfile()`
- `../amilib/amilib/ami_dict.py` - `create_dictionary_from_csv()`

**Note**: Terms can come from:
- Keyword extraction in this repository (`Keyword_extraction/`)
- CSV files with extracted keywords
- Text files (one term per line)

### Stage 2: Create Dictionary

**Process**: Create basic dictionary structure with entry elements for each term

**Methods:**
- `AmiDictionary.create_dictionary_from_words(terms, title, ...)` - Creates dictionary from list of terms
- `add_entries_from_words(terms)` - Adds entries to dictionary
- `add_entry_element(term)` - Creates individual entry element

**Output**: XML dictionary with basic entries (term, name attributes only)

**Location in codebase** (in `../amilib`):
- `../amilib/amilib/ami_dict.py` lines 892-925
- `../amilib/amilib/ami_dict.py` lines 957-980

### Stage 3: Enhance Dictionary with Wikipedia/Wikidata/Wiktionary

This stage has three parallel enhancement processes:

#### 3a. Add Wikipedia Content

**Process**: Lookup Wikipedia pages for each term and add first paragraph

**Methods:**
- `lookup_and_add_wikipedia_page()` - Looks up Wikipedia page for term
- `WikipediaPage.lookup_wikipedia_page_for_term(term)` - Fetches Wikipedia page
- Extracts first paragraph (`wpage_first_para`)
- Extracts Wikipedia URL
- Extracts Wikidata ID from Wikipedia page

**Output**: Dictionary entries with Wikipedia descriptions and URLs

**Location in codebase** (in `../amilib`):
- `../amilib/amilib/ami_dict.py` lines 444-480
- `../amilib/amilib/wikimedia.py` - `WikipediaPage` class

#### 3b. Add Wikidata Content

**Process**: Lookup Wikidata IDs and descriptions for each term

**Methods:**
- `add_wikidata_from_terms()` - Processes all entries
- `lookup_and_add_wikidata_to_entry(entry)` - Looks up Wikidata for single entry
- `WikidataLookup.lookup_wikidata(term)` - Fetches Wikidata data
- Extracts Wikidata ID (Q/P numbers)
- Extracts Wikidata category/label
- Extracts descriptions

**Output**: Dictionary entries with Wikidata IDs and metadata

**Location in codebase** (in `../amilib`):
- `../amilib/amilib/ami_dict.py` lines 1474-1505
- `../amilib/amilib/wikimedia.py` - `WikidataLookup` class

#### 3c. Add Wiktionary Content

**Process**: Lookup Wiktionary pages for definitions

**Methods:**
- `add_wiktionary_from_terms()` - Processes all entries
- `lookup_and_add_wiktionary_to_entry(entry)` - Looks up Wiktionary for single entry
- `WiktionaryPage.create_wiktionary_page(term)` - Fetches Wiktionary page
- Extracts definitions

**Output**: Dictionary entries with Wiktionary definitions

**Location in codebase** (in `../amilib`):
- `../amilib/amilib/ami_dict.py` lines 1506-1522
- `../amilib/amilib/wikimedia.py` - `WiktionaryPage` class

### Stage 4: Create HTML Dictionary

**Process**: Convert XML dictionary to HTML format with semantic markup

**Methods:**
- `create_html_dictionary()` - Creates HTML structure
- `add_html_entries(dictionary_div)` - Adds entries as HTML divs
- `create_semantic_div()` - Creates semantic HTML entry elements
- Adds role attributes (`ami_dictionary`, `ami_entry`)
- Adds search term paragraphs with Wikipedia links

**Output**: HTML dictionary with semantic markup

**Location in codebase** (in `../amilib`):
- `../amilib/amilib/ami_dict.py` lines 1930-1991

### Stage 5: Create Encyclopedia

**Process**: Parse HTML dictionary and extract entries with full metadata

**Methods:**
- `AmiEncyclopedia.create_from_html_content(html_content)` - Parses HTML
- `AmiDictionary.create_from_html_file()` - Parses dictionary structure
- Extracts entries with:
  - Terms
  - Wikipedia URLs
  - Wikidata IDs
  - Descriptions (first paragraphs)
  - Metadata

**Output**: Encyclopedia object with processed entries

**Location in codebase** (in `../amilib`):
- `../amilib/amilib/ami_encyclopedia.py` lines 132-310

### Stage 6: Normalize by Wikidata ID

**Process**: Group entries by Wikidata ID to identify synonyms

**Methods:**
- `normalize_by_wikidata_id()` - Groups entries by Wikidata ID
- Creates normalized_entries dictionary
- Identifies entries with same Wikidata ID (synonyms)
- Handles entries without Wikidata IDs separately

**Output**: Normalized entries grouped by Wikidata ID

**Location in codebase** (in `../amilib`):
- `../amilib/amilib/ami_encyclopedia.py` lines 330-348

### Stage 7: Merge Synonyms

**Process**: Merge entries with identical Wikidata IDs into single canonical entries

**Methods:**
- `merge_synonyms_by_wikidata_id()` - Merges synonym groups
- `aggregate_synonyms_by_wikidata_id()` - Aggregates synonym data
- Creates canonical term from synonyms
- Merges Wikipedia URLs, descriptions
- Preserves all term variants

**Output**: Merged entries with canonical terms and aggregated data

**Location in codebase** (in `../amilib`):
- `../amilib/amilib/ami_encyclopedia.py` lines 425-530

### Stage 8: Generate Encyclopedia HTML

**Process**: Generate final HTML encyclopedia with structured entries

**Methods:**
- `generate_html()` - Creates final HTML output
- `_generate_entry_div()` - Creates entry HTML elements
- Adds semantic markup
- Adds links and references
- Adds interactive features (checkboxes, disambiguation selectors)

**Output**: Complete HTML encyclopedia

**Location in codebase** (in `../amilib`):
- `../amilib/amilib/ami_encyclopedia.py` lines 800-1000 (approximately)

## Data Flow

```
Terms/Words (Input)
  ↓
Create Dictionary (Basic entries)
  ↓
Enhance with Wikipedia/Wikidata/Wiktionary (Parallel)
  ↓
Create HTML Dictionary (Semantic markup)
  ↓
Create Encyclopedia (Extract & process)
  ↓
Normalize by Wikidata ID (Group synonyms)
  ↓
Merge Synonyms (Canonical entries)
  ↓
Generate Encyclopedia HTML (Final output)
```

## Key Components

All key components are in the `../amilib` repository:

### AmiDictionary (`../amilib/amilib/ami_dict.py`)
- **Purpose**: Create and manage dictionary structure
- **Key Methods**:
  - `create_dictionary_from_words()` - Create from terms
  - `add_wikidata_from_terms()` - Add Wikidata content
  - `add_wikipedia_page()` - Add Wikipedia content
  - `add_wiktionary_from_terms()` - Add Wiktionary content
  - `create_html_dictionary()` - Convert to HTML

### AmiEncyclopedia (`../amilib/amilib/ami_encyclopedia.py`)
- **Purpose**: Create and manage encyclopedia with normalization
- **Key Methods**:
  - `create_from_html_content()` - Parse HTML dictionary
  - `normalize_by_wikidata_id()` - Group by Wikidata ID
  - `merge_synonyms_by_wikidata_id()` - Merge synonyms
  - `generate_html()` - Generate final output

### Wikimedia (`../amilib/amilib/wikimedia.py`)
- **Purpose**: Interface with Wikipedia, Wikidata, Wiktionary
- **Key Classes**:
  - `WikipediaPage` - Wikipedia page lookup
  - `WikidataLookup` - Wikidata ID lookup
  - `WiktionaryPage` - Wiktionary page lookup

## Example Workflows

### Create Dictionary from Terms
```python
from amilib.ami_dict import AmiDictionary

# Create dictionary from list of terms
terms = ["climate change", "greenhouse gas", "carbon cycle"]
dictionary, outpath = AmiDictionary.create_dictionary_from_words(
    terms=terms,
    title="climate_terms",
    wikidata=True,  # Add Wikidata
    outdir=Path("output")
)
```

### Create Dictionary from File
```python
# Create dictionary from text file (one term per line)
dictionary, outpath = AmiDictionary.create_dictionary_from_wordfile(
    wordfile="terms.txt",
    title="my_dictionary",
    wikidata=True,
    outdir=Path("output")
)
```

### Create Encyclopedia from Dictionary
```python
from amilib.ami_encyclopedia import AmiEncyclopedia

# Create HTML dictionary first
html_dict = dictionary.create_html_dictionary()
html_content = str(html_dict)

# Create encyclopedia from HTML
encyclopedia = AmiEncyclopedia(title="My Encyclopedia")
encyclopedia.create_from_html_content(html_content)

# Normalize and merge
encyclopedia.normalize_by_wikidata_id()
encyclopedia.merge_synonyms_by_wikidata_id()

# Generate final HTML
final_html = encyclopedia.generate_html()
```

## Style Guide Compliance

This pipeline follows the encyclopedia style guide:
- ✅ Absolute imports with module prefixes (`from amilib.ami_dict import AmiDictionary`)
- ✅ **NO PYTHONPATH**: Tests work without PYTHONPATH environment variable
- ✅ **NO ENVIRONMENT VARIABLES**: Code works without requiring environment variables
- ✅ Empty `__init__.py` files
- ✅ Path construction using `Path()` constructor
- ✅ No magic strings (use constants)
- ✅ Comprehensive documentation
- **See**: [STYLE_GUIDE.md](STYLE_GUIDE.md) for complete style guide

## References

All references are to the `../amilib` repository:

- **Style Guide**: `../amilib/docs/style_guide_compliance.md`
- **AmiDictionary**: `../amilib/amilib/ami_dict.py`
- **AmiEncyclopedia**: `../amilib/amilib/ami_encyclopedia.py`
- **Wikimedia**: `../amilib/amilib/wikimedia.py`
- **Workflow**: `../amilib/workflow/README.md`

## Integration with This Repository

This `encyclopedia` repository can provide **input terms** to the pipeline:
- **Keyword Extraction** (`Keyword_extraction/`) extracts keywords from documents
- These keywords can be used as input terms for `AmiDictionary.create_dictionary_from_words()`
- The resulting dictionary can then be enhanced and converted to an encyclopedia using the `amilib` code
