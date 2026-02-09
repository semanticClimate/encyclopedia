# Encyclopedia Refactoring Summary

**Date:** February 7, 2026  
**System Date:** Saturday Feb 7, 2026

## Summary of Encyclopedia Functionality

### In `../amilib` Project

The `amilib` project contains encyclopedia functionality that extends the dictionary (`--DICT`) functionality:

#### Core Components:

1. **`ami_encyclopedia.py`** (~1990 lines)
   - `AmiEncyclopedia` class - main encyclopedia management
   - Creates encyclopedia from HTML dictionary content
   - Normalizes entries by Wikidata ID
   - Merges synonyms (entries with same Wikidata ID)
   - Generates normalized HTML output
   - Manages metadata (created, last_edited, actions, hidden entries, disambiguation selections)
   - Entry classification and categorization

2. **`ami_encyclopedia_args.py`** (~280 lines)
   - CLI argument parsing for `--ENCYCLOPEDIA` operations
   - Integrated with main amilib CLI as subparser
   - Operations: create, normalize, merge, add figures, show statistics

3. **`ami_encyclopedia_cluster.py`** (~600 lines)
   - Clustering functionality for encyclopedia entries
   - Description similarity-based clustering
   - `AmiEncyclopediaClusterer` class

4. **`ami_encyclopedia_util.py`** (~390 lines)
   - Link extraction and validation utilities
   - `EncyclopediaLinkExtractor` - extracts links from entries
   - `LinkValidator` - validates Wikipedia links
   - `SynonymNormalizer` - normalizes terms for synonym detection

5. **`dict_args.py`**
   - CLI arguments for `--DICT` operations
   - Dictionary creation from words/files/CSV
   - Wikimedia content enhancement (Wikipedia, Wikidata, Wiktionary)

#### Key Functionality Flow:

1. **Dictionary Creation** (`AmiDictionary.create_dictionary_from_words()`)
   - Creates basic dictionary structure from terms
   - Each entry has: term, name, optional content

2. **Enhancement** (via `dict_args.py`)
   - Adds Wikipedia pages (first paragraphs, URLs)
   - Adds Wikidata IDs and descriptions
   - Adds Wiktionary definitions

3. **HTML Generation** (`AmiDictionary.create_html_dictionary()`)
   - Converts dictionary to HTML with semantic markup
   - Adds role attributes (`ami_dictionary`, `ami_entry`)

4. **Encyclopedia Creation** (`AmiEncyclopedia.create_from_html_content()`)
   - Parses HTML dictionary into encyclopedia entries
   - Extracts Wikidata IDs, Wikipedia URLs, descriptions

5. **Normalization** (`AmiEncyclopedia.normalize_by_wikidata_id()`)
   - Groups entries by Wikidata ID
   - Identifies synonyms (same Wikidata ID)

6. **Merging** (`AmiEncyclopedia.merge_synonyms_by_wikidata_id()`)
   - Merges synonyms into canonical entries
   - Aggregates terms and content

7. **Output** (`AmiEncyclopedia.generate_html()`)
   - Generates normalized HTML encyclopedia

#### Dependencies (remain in amilib):
- `ami_dict.py` - Dictionary creation and management
- `wikimedia.py` - Wikipedia/Wikidata/Wiktionary lookups
- `ami_html.py` - HTML processing utilities
- `file_lib.py`, `util.py`, `xml_lib.py` - General utilities

### In `./encyclopedia` Project

The `encyclopedia` project contains encyclopedia functionality that has been partially migrated or developed independently:

#### Core Components:

1. **`encyclopedia/core/encyclopedia.py`** (~2286 lines)
   - `AmiEncyclopedia` class (appears to be migrated from amilib)
   - Same core functionality as amilib version
   - Entry management, normalization, merging
   - Currently imports from `amilib` for dependencies

2. **`encyclopedia/cli/args.py`** (~302 lines)
   - `EncyclopediaArgs` class for CLI operations
   - Similar functionality to `ami_encyclopedia_args.py`

3. **`encyclopedia/cli/versioned_editor.py`**
   - Versioned editor functionality
   - Browser-based editing interface for encyclopedia entries

4. **`encyclopedia/utils/encyclopedia_builder.py`**
   - Utility functions for building encyclopedias
   - Wrapper functions around amilib dictionary creation

5. **`encyclopedia/utils/link_extractor.py`**
   - Link extraction utilities
   - Similar to `ami_encyclopedia_util.py` in amilib

6. **`encyclopedia/browser/`**
   - Web-based browser for searching encyclopedia entries
   - Streamlit-based interface
   - Search engine with indexing capabilities
   - Supports up to 5,000 entries

#### Additional Components:

- **`Keyword_extraction/`** - AI-powered keyword extraction (separate concern)
- **`Dictionary/`** - Storage for processed keywords and documents
- **`txt2phrases/`** - Text to phrases conversion (needs removal - see below)

## Key Differences: DICT vs ENCYCLOPEDIA

### AmiDictionary (`--DICT`):
- **Purpose**: Creates a list of entries from terms
- **Structure**: Flat list of entries
- **Content**: Each entry has term, name, optional Wikipedia/Wikidata/Wiktionary content
- **Output**: HTML dictionary with entries
- **Use Case**: Basic term-to-content mapping

### AmiEncyclopedia (`--ENCYCLOPEDIA`):
- **Purpose**: Semantic, normalized knowledge base
- **Structure**: Normalized entries grouped by Wikidata ID
- **Content**: Same as dictionary, plus:
  - Wikidata ID-based normalization
  - Synonym merging
  - Metadata tracking (actions, hidden entries, disambiguation)
- **Output**: Normalized HTML encyclopedia with merged entries
- **Use Case**: Knowledge base with semantic linking

**Key Insight**: An `AmiDictionary` is essentially a list of encyclopedia entries. `AmiEncyclopedia` adds normalization, merging, and metadata on top of dictionary functionality. The HTML output formats are very similar, with encyclopedia adding normalization indicators.

## Issues Addressed

### 1. txt2phrases Removal

**Current State**: `txt2phrases/` directory exists in `encyclopedia` project

**Purpose**: 
- Converts PDF/HTML to text
- Extracts keywords using AI models (Hugging Face transformers)
- Classifies keywords using TF-IDF
- Creates wordlists from documents

**Why Remove**:
- Separate concern from encyclopedia creation
- Main purpose is wordlist creation (precursor to encyclopedia, but not encyclopedia itself)
- Should be its own project
- Currently used by encyclopedia scripts but can be external dependency

**Action**: Move to separate project, update imports in encyclopedia scripts

### 2. DICT vs ENCYCLOPEDIA Overlap

**Current State**: Both exist in amilib with significant overlap

**Analysis**:
- `AmiDictionary` creates entries from terms
- `AmiEncyclopedia` uses `AmiDictionary` internally (composition)
- HTML output formats are very similar
- Main difference is normalization and merging in encyclopedia

**Future Direction**: 
- Focus on encyclopedias going forward
- Dictionary creation remains in amilib as utility
- Encyclopedia becomes primary output format

### 3. wikimedia.py Location

**Current State**: `amilib/wikimedia.py` contains Wikipedia/Wikidata/Wiktionary integration

**Decision**: **Keep in amilib**
- Used by both dictionary and encyclopedia creation
- General-purpose Wikimedia integration
- Will continue to be developed for encyclopedia needs
- Shared utility across projects

### 4. Future Features

**Planned Enhancements**:
- **Search capabilities**: Partially implemented in `encyclopedia/browser/`, needs integration into core `AmiEncyclopedia`
- **Link creation**: Link extraction exists, need to create links between entries
- **Knowledge graph**: Generate graph from encyclopedia links

**Current State**:
- Browser-based search exists (`encyclopedia/browser/`)
- Link extraction exists (`encyclopedia/utils/link_extractor.py`, `amilib/ami_encyclopedia_util.py`)
- Knowledge graph functionality not yet implemented

## Proposed Strategy Overview

See `docs/refactoring_strategy.md` for detailed plan. Summary:

### Phase 1: Remove txt2phrases (Week 1)
- Extract to separate project
- Update encyclopedia scripts to use external package

### Phase 2: Consolidate Encyclopedia Code (Weeks 2-3)
- Move all encyclopedia code from amilib to encyclopedia
- Merge duplicate functionality
- Update imports to use amilib as dependency

### Phase 3: Deprecate in amilib (Week 4)
- Add deprecation warnings
- Redirect imports to encyclopedia package
- Maintain for 1-2 release cycles

### Phase 4: Enhance Features (Weeks 5-6)
- Integrate search capabilities
- Enhance link management
- Implement knowledge graph foundation

### Phase 5: Documentation (Week 7)
- Update all documentation
- Create migration guide
- Comprehensive testing

## Key Decisions

1. **wikimedia.py stays in amilib** - Shared utility, continues development
2. **Dictionary creation stays in amilib** - Utility function, encyclopedia uses it
3. **Encyclopedia becomes primary focus** - All encyclopedia-specific code moves to encyclopedia project
4. **txt2phrases becomes separate project** - Different concern, can be dependency
5. **Future: Search and knowledge graph** - Core features for encyclopedia project

## Next Steps

1. Review `docs/refactoring_strategy.md` for detailed plan
2. Resolve questions about txt2phrases location
3. Get approval for approach
4. Begin Phase 1 when approved
