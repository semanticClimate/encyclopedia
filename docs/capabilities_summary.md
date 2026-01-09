# Encyclopedia Project - Current Capabilities

## Brief Summary

The Encyclopedia project transforms **terms/words** into a **semantically enriched encyclopedia** with Wikipedia, Wikidata, and Wiktionary content. It also includes **link extraction and analysis** capabilities for encyclopedia entries.

## Core Capabilities

### 1. **Dictionary Creation** (via amilib)
- Create dictionary from list of terms/words
- Basic entry structure with term and name attributes

### 2. **Semantic Enhancement** (via amilib)
- **Wikipedia**: Lookup pages, extract first paragraphs, get URLs
- **Wikidata**: Lookup IDs, extract categories and descriptions
- **Wiktionary**: Lookup definitions

### 3. **Encyclopedia Generation** (encyclopedia package)
- Parse HTML dictionary into encyclopedia entries
- Normalize entries by Wikidata ID
- Merge synonyms (entries with same Wikidata ID)
- Generate structured HTML output

### 4. **Link Analysis** (test/text_links)
- Extract links from encyclopedia entries
- Classify link types (article, file, help, external)
- Build link graphs
- Analyze link density and shared links
- Validate link accessibility

### 5. **Keyword Extraction** (Keyword_extraction)
- AI-powered keyword extraction from documents
- Uses Hugging Face transformers
- Output to CSV format

## Input/Output

**Input**: List of terms/words (from documents, CSV, or text files)

**Output**: 
- Enhanced HTML dictionary
- Normalized encyclopedia with merged synonyms
- Link analysis reports (JSON, HTML)
- Keyword extraction results (CSV)


