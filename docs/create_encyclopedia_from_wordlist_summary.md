# Summary: Creating Encyclopedia from Wordlist

## Overview
The script `Examples/create_encyclopedia_from_wordlist.py` creates an encyclopedia from a list of terms through a 6-step pipeline that transforms raw terms into a normalized, merged encyclopedia with Wikipedia content.

## Main Entry Point

**File**: `Examples/create_encyclopedia_from_wordlist.py`  
**Function**: `main()` (lines 449-544)  
**Primary Function**: `create_encyclopedia_from_wordlist()` (lines 38-268)

---

## Major Steps

### Step 1: Create Dictionary from Terms
**Location**: Lines 53-70  
**Module**: `amilib.ami_dict.AmiDictionary`  
**Method**: `AmiDictionary.create_dictionary_from_words()`

```python
dictionary, _ = AmiDictionary.create_dictionary_from_words(
    terms=terms,
    title=title,
    wikidata=False,
    outdir=temp_path
)
```

**What it does**:
- Creates basic dictionary structure with entry elements for each term
- Initializes `AmiDictionary` object with `entry_by_term` dictionary
- Returns dictionary object and output path

**Output**: `AmiDictionary` instance with basic entries (term names only)

---

### Step 2: Enhance with Wikipedia Content
**Location**: Lines 72-104  
**Module**: `amilib.wikimedia.WikipediaPage`  
**Methods**: 
- `WikipediaPage.lookup_wikipedia_page_for_term(term)`
- `dictionary.add_wikipedia_page()` (if available)
- `ami_entry.add_wikipedia_page()` (if available)

**What it does**:
- Attempts to fetch Wikipedia pages for each term
- Extracts first paragraph descriptions
- Extracts Wikipedia URLs
- Extracts Wikidata IDs from Wikipedia pages
- Adds Wikipedia content to dictionary entries

**Output**: Dictionary entries enriched with Wikipedia descriptions and URLs

**Note**: This step is optional and may fail for some terms (handled gracefully)

---

### Step 3: Create HTML Dictionary
**Location**: Lines 106-240  
**Modules**: 
- `amilib.ami_dict.AmiDictionary` (method: `create_html_dictionary()`)
- `amilib.xml_lib.XmlLib` (for XML/HTML manipulation)
- `amilib.ami_html.HtmlLib` (for HTML structure creation)
- `lxml.etree` (for XML/HTML parsing)

**What it does**:
1. Calls `dictionary.create_html_dictionary()` to convert dictionary to HTML
2. Ensures complete HTML document structure:
   - Checks if result is complete HTML (`<html>` tag)
   - Checks if result is a fragment (`<div>` tag)
   - Checks if result is a string
3. Validates and fixes HTML structure:
   - Ensures `html/body/div[@role='ami_dictionary']` exists
   - Ensures `div[@role='ami_dictionary']` has `@title` attribute
   - Wraps fragments in complete HTML structure if needed
4. Saves HTML to temporary file

**Key Methods**:
- `dictionary.create_html_dictionary()` - Converts dictionary to HTML
- `HtmlLib.create_html_with_empty_head_body()` - Creates HTML skeleton
- `XmlLib.element_to_string()` - Serializes elements to HTML string
- `fromstring()` / `tostring()` - Parse/serialize HTML strings

**Output**: Temporary HTML file with complete dictionary structure

---

### Step 4: Create Encyclopedia from HTML File
**Location**: Lines 242-252  
**Module**: `encyclopedia.core.encyclopedia.AmiEncyclopedia`  
**Method**: `encyclopedia.create_from_html_file()`

```python
encyclopedia = AmiEncyclopedia(title=title)
encyclopedia.create_from_html_file(temp_html_path)
```

**What it does**:
1. Creates new `AmiEncyclopedia` instance
2. Reads HTML file and parses it using `AmiDictionary`
3. Extracts entries from dictionary:
   - Converts `AmiEntry` objects to dictionary format
   - Extracts `term`, `search_term`, `wikidata_id`, `wikipedia_url`
   - Extracts `description_html` from Wikipedia paragraphs
   - Extracts `figure_html` from images
4. Stores entries in `encyclopedia.entries` list

**Internal Flow** (`encyclopedia/core/encyclopedia.py`):
- `create_from_html_file()` → `create_from_html_content()` (lines 127-133)
- `create_from_html_content()` (lines 135-182):
  - Creates temporary file
  - Parses HTML with `HtmlUtil.parse_html_file_to_xml()`
  - Uses `AmiDictionary.create_from_html_file()` to parse entries
  - Converts `AmiEntry` objects to entry dictionaries
  - Extracts metadata (Wikidata IDs, Wikipedia URLs, descriptions)

**Output**: `AmiEncyclopedia` instance with populated `entries` list

---

### Step 5: Normalize by Wikidata ID
**Location**: Lines 254-257  
**Module**: `encyclopedia.core.encyclopedia.AmiEncyclopedia`  
**Method**: `encyclopedia.normalize_by_wikidata_id()`

**What it does**:
- Groups entries by Wikidata ID
- Identifies entries referring to the same entity
- Creates normalized entry groups
- Stores groups in `encyclopedia.normalized_entries` dictionary

**Output**: Entries grouped by Wikidata ID (normalized)

---

### Step 6: Merge Synonyms
**Location**: Lines 259-262  
**Module**: `encyclopedia.core.encyclopedia.AmiEncyclopedia`  
**Method**: `encyclopedia.merge()`

**What it does**:
- Merges entries with the same Wikidata ID into single entries
- Combines synonyms into synonym groups
- Merges descriptions, images, and other metadata
- Stores merged entries and synonym groups

**Output**: Final encyclopedia with merged entries and synonym groups

---

## Supporting Functions

### `display_entry()` (lines 271-293)
**Purpose**: Display a single entry in formatted output  
**Parameters**: `entry` (Dict), `index` (int)  
**Shows**: Term, Wikidata ID, Wikipedia URL, description preview

### `display_all_entries()` (lines 296-305)
**Purpose**: Display all entries in the encyclopedia  
**Parameters**: `encyclopedia` (AmiEncyclopedia)

### `interactive_delete_entries()` (lines 308-414)
**Purpose**: Interactive CLI for deleting unwanted entries  
**Parameters**: `encyclopedia` (AmiEncyclopedia)  
**Returns**: Modified `AmiEncyclopedia` instance  
**Features**:
- Display entries with numbers
- Accept comma-separated entry numbers to delete
- Commands: `done`, `skip`, `show`, `stats`, `all`
- Re-normalizes after deletion

### `save_encyclopedia()` (lines 417-446)
**Purpose**: Save encyclopedia to HTML file  
**Module**: `encyclopedia.core.encyclopedia.AmiEncyclopedia`  
**Method**: `encyclopedia.save_wiki_normalized_html(output_file)`  
**Location**: `encyclopedia/core/encyclopedia.py` (lines ~900-961)

**What it does**:
- Generates normalized HTML with merged entries
- Creates HTML structure with `role='ami_encyclopedia'`
- Classifies entries (disambiguation, redirect, etc.)
- Saves to file

**Note**: May make network requests to check disambiguation pages (can be slow)

---

## Module Locations

### Core Modules (from `amilib` package)
1. **`amilib.ami_dict.AmiDictionary`**
   - Location: External package (`../amilib/amilib/ami_dict.py`)
   - Purpose: Dictionary creation and management
   - Key methods:
     - `create_dictionary_from_words()` - Create from terms
     - `create_html_dictionary()` - Convert to HTML
     - `create_from_html_file()` - Parse HTML dictionary

2. **`amilib.wikimedia.WikipediaPage`**
   - Location: External package (`../amilib/amilib/wikimedia.py`)
   - Purpose: Wikipedia page lookup and content extraction
   - Key methods:
     - `lookup_wikipedia_page_for_term()` - Fetch Wikipedia page
     - `get_first_paragraph()` - Extract first paragraph
     - `extract_a_elem_with_image_from_infobox()` - Extract images

3. **`amilib.xml_lib.XmlLib`**
   - Location: External package (`../amilib/amilib/xml_lib.py`)
   - Purpose: XML/HTML manipulation utilities
   - Key methods:
     - `element_to_string()` - Serialize elements to HTML

4. **`amilib.ami_html.HtmlLib`**
   - Location: External package (`../amilib/amilib/ami_html.py`)
   - Purpose: HTML structure creation
   - Key methods:
     - `create_html_with_empty_head_body()` - Create HTML skeleton
     - `get_body()` - Get body element

### Encyclopedia Modules (local)
1. **`encyclopedia.core.encyclopedia.AmiEncyclopedia`**
   - Location: `encyclopedia/core/encyclopedia.py`
   - Purpose: Encyclopedia management, normalization, merging
   - Key methods:
     - `create_from_html_file()` - Load from HTML file
     - `create_from_html_content()` - Load from HTML string
     - `normalize_by_wikidata_id()` - Group by Wikidata ID
     - `merge()` - Merge synonyms
     - `save_wiki_normalized_html()` - Save to HTML file
     - `get_statistics()` - Get encyclopedia statistics

---

## Data Flow

```
Wordlist (List[str])
    ↓
Step 1: AmiDictionary.create_dictionary_from_words()
    ↓
AmiDictionary (with entry_by_term)
    ↓
Step 2: WikipediaPage.lookup_wikipedia_page_for_term()
    ↓
AmiDictionary (enriched with Wikipedia content)
    ↓
Step 3: dictionary.create_html_dictionary()
    ↓
HTML Dictionary (temporary file)
    ↓
Step 4: AmiEncyclopedia.create_from_html_file()
    ↓
AmiEncyclopedia (with entries list)
    ↓
Step 5: encyclopedia.normalize_by_wikidata_id()
    ↓
AmiEncyclopedia (with normalized_entries)
    ↓
Step 6: encyclopedia.merge()
    ↓
Final AmiEncyclopedia (merged entries)
    ↓
save_wiki_normalized_html()
    ↓
HTML Encyclopedia File
```

---

## Entry Dictionary Structure

Each entry in `encyclopedia.entries` is a dictionary with:

```python
{
    'term': str,                    # Primary term
    'search_term': str,             # Search term (may differ from term)
    'wikidata_id': str,             # Wikidata Q/P ID (e.g., "Q1997")
    'wikipedia_url': str,           # Full Wikipedia URL
    'description_html': str,        # HTML description (first paragraph)
    'figure_html': Element,         # Image element (lxml)
    'images': List[str],            # List of image HTML strings
    # ... other metadata
}
```

---

## Usage Example

```bash
# From project root directory
python Examples/create_encyclopedia_from_wordlist.py \
    --wordlist Examples/my_terms.txt \
    --title "Climate Terms" \
    --output my_encyclopedia.html
```

Or run as module:
```bash
python -m Examples.create_encyclopedia_from_wordlist \
    --wordlist Examples/my_terms.txt \
    --title "Climate Terms"
```

---

## Key Design Decisions

1. **Temporary Files**: Uses temporary files for HTML dictionary because `AmiDictionary.create_dictionary_from_words()` requires an output directory, and `AmiEncyclopedia.create_from_html_file()` expects a file path.

2. **HTML Structure Validation**: Extensive validation ensures the HTML has the required `html/body/div[@role='ami_dictionary' and @title]` structure that `AmiDictionary` expects.

3. **Graceful Degradation**: Wikipedia enhancement is optional - if it fails, the script continues with basic entries.

4. **Two-Phase Processing**: Dictionary creation (amilib) → Encyclopedia creation (encyclopedia.core) separates concerns between basic dictionary structure and advanced normalization/merging.

5. **Normalization Pipeline**: Normalization (grouping) happens before merging to ensure all synonyms are identified before combining entries.
