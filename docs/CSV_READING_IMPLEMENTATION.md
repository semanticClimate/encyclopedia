# CSV Reading Implementation

**Date:** March 2, 2026 (system date)  
**Status:** ✅ Complete

## Overview

Implemented CSV reading functionality for creating encyclopedias from CSV files containing phrases and counts. This allows users to read phrase lists from CSV files with flexible column selection (by name or number) and auto-detection capabilities.

## Components

### 1. CSV Reader Module (`encyclopedia/utils/csv_reader.py`)

**Purpose:** Read phrases and counts from CSV files with flexible column selection.

**Features:**
- ✅ Named columns: Support for column names (e.g., "phrase", "keyword", "count", "frequency")
- ✅ Column numbers: Support for 0-indexed column numbers
- ✅ Auto-detection: Automatically detects common column names if not specified
- ✅ Optional counts: Count column is optional
- ✅ Error handling: Clear error messages for missing/invalid columns
- ✅ Empty file handling: Handles empty CSV files gracefully

**Function Signature:**
```python
def read_phrases_from_csv(
    csv_file: Path,
    phrase_column: Optional[Union[str, int]] = None,
    count_column: Optional[Union[str, int]] = None
) -> Tuple[List[str], Optional[List[int]]]:
    """
    Read phrases and counts from a CSV file.
    
    Args:
        csv_file: Path to CSV file
        phrase_column: Column name (str), column number (int), or None for auto-detect
        count_column: Column name (str), column number (int), None for auto-detect, or omit for no counts
        
    Returns:
        Tuple of (phrases: List[str], counts: Optional[List[int]])
    """
```

**Auto-Detection:**
- **Phrase columns:** `phrase`, `phrases`, `keyword`, `keywords`, `keyphrase`, `keyphrases`, `term`, `terms`, `word`, `words`
- **Count columns:** `count`, `counts`, `frequency`, `freq`, `occurrences`, `occurrence`

**Note:** This module may be transferred to `../amilib` in the future if CSV reading functionality is needed there.

### 2. CLI Integration (`encyclopedia/cli/versioned_editor.py`)

**Updated:** `create` command now supports CSV files.

**New Parameters:**
- `--phrase-column`: Column name or number for phrases (auto-detects if not specified)
- `--count-column`: Column name or number for counts (optional, auto-detects if not specified)

**Usage:**
```bash
# CSV file with auto-detection
python -m encyclopedia.cli.versioned_editor create \
    --wordlist phrases.csv \
    --output encyclopedia.html \
    --title "My Encyclopedia"

# CSV file with specific columns
python -m encyclopedia.cli.versioned_editor create \
    --wordlist phrases.csv \
    --output encyclopedia.html \
    --phrase-column "keyword" \
    --count-column "frequency"

# CSV file using column numbers
python -m encyclopedia.cli.versioned_editor create \
    --wordlist phrases.csv \
    --output encyclopedia.html \
    --phrase-column 0 \
    --count-column 1

# Text file (backward compatible)
python -m encyclopedia.cli.versioned_editor create \
    --wordlist phrases.txt \
    --output encyclopedia.html
```

**Backward Compatibility:** Text files (one phrase per line) continue to work as before.

### 3. Dedicated Script (`Examples/create_encyclopedia_from_phraselist.py`)

**Purpose:** Standalone script for reading phrase lists (CSV or text) and creating encyclopedias.

**Features:**
- Supports CSV and text files
- Flexible column selection (names or numbers)
- Auto-detection of common column names
- Options for Wikipedia descriptions and images
- Comprehensive documentation

**Usage Examples:**

```bash
# CSV file with auto-detection
python Examples/create_encyclopedia_from_phraselist.py \
    --input phrases.csv \
    --output encyclopedia.html \
    --title "My Encyclopedia"

# CSV file with specific columns
python Examples/create_encyclopedia_from_phraselist.py \
    --input phrases.csv \
    --output encyclopedia.html \
    --phrase-column "keyword" \
    --count-column "frequency"

# CSV file using column numbers
python Examples/create_encyclopedia_from_phraselist.py \
    --input phrases.csv \
    --output encyclopedia.html \
    --phrase-column 0 \
    --count-column 1

# Text file (one phrase per line)
python Examples/create_encyclopedia_from_phraselist.py \
    --input phrases.txt \
    --output encyclopedia.html \
    --title "My Encyclopedia"

# With Wikipedia descriptions and images
python Examples/create_encyclopedia_from_phraselist.py \
    --input phrases.csv \
    --output encyclopedia.html \
    --add-wikipedia \
    --add-images \
    --batch-size 10 \
    --verbose
```

**Parameters:**
- `--input` / `-i`: Input CSV or text file (required)
- `--output` / `-o`: Output HTML file (required)
- `--title` / `-t`: Encyclopedia title (default: "Encyclopedia")
- `--phrase-column`: CSV column name or number for phrases (auto-detects if not specified)
- `--count-column`: CSV column name or number for counts (optional, auto-detects if not specified)
- `--add-wikipedia`: Add Wikipedia descriptions (default: False)
- `--add-images`: Add images from Wikipedia (default: False, can be slow)
- `--batch-size`: Number of entries to process at a time (default: 10)
- `--validate`: Validate encyclopedia completeness (default: False)
- `--verbose` / `-v`: Show detailed progress (default: False)

## Test Coverage

**Test File:** `test/encyclopedia/test_csv_reading.py`

**Test Cases (8 tests, all passing):**
1. ✅ `test_read_csv_with_named_columns_phrase_count` - Named columns "phrase" and "count"
2. ✅ `test_read_csv_with_named_columns_keyword_frequency` - Named columns "keyword" and "frequency"
3. ✅ `test_read_csv_with_column_numbers` - Column numbers (0-indexed)
4. ✅ `test_read_csv_without_count_column` - Only phrase column, no counts
5. ✅ `test_read_csv_auto_detect_columns` - Auto-detection of common column names
6. ✅ `test_read_csv_empty_file` - Handle empty CSV files
7. ✅ `test_read_csv_missing_column_error` - Error handling for missing columns
8. ✅ `test_read_csv_invalid_column_number_error` - Error handling for invalid column numbers

**Test Output:** All test outputs saved to `temp/test/encyclopedia/TestCSVReading/` for human inspection.

## Implementation Details

### Dependencies
- **pandas**: Used for CSV reading (already a dependency via amilib)
- **pathlib.Path**: For file path handling (style guide compliant)

### Style Guide Compliance
- ✅ Uses system date (March 2, 2026)
- ✅ Uses `Path` constructor (no string concatenation)
- ✅ No mocks in tests (real CSV files)
- ✅ Outputs saved to `temp/` directory
- ✅ Comprehensive documentation

### Error Handling
- Clear error messages for missing columns
- Validation of column numbers (range checking)
- Graceful handling of empty files
- Type conversion errors for count columns

## CSV File Formats Supported

### Format 1: Named Columns
```csv
phrase,count
climate change,42
greenhouse gas,35
carbon dioxide,28
```

### Format 2: Different Column Names
```csv
keyword,frequency
atom,100
molecule,85
```

### Format 3: Column Numbers
```csv
term,frequency,other
DNA,50,extra
protein,45,extra
```

### Format 4: Text File (One Phrase Per Line)
```
climate change
greenhouse gas
carbon dioxide
```

## Comparison with amilib

**amilib has:** `AmiDictionary.create_dictionary_from_csv(csv_term_file, col_name=None, title=None)`

**Differences:**
- amilib's method creates a dictionary (not just reads CSV)
- amilib's method only supports column names (not numbers)
- amilib's method doesn't support count columns
- amilib's method doesn't have auto-detection

**Our implementation:**
- Reads CSV and returns phrases/counts (more flexible)
- Supports both column names and numbers
- Supports count columns
- Has auto-detection
- Can be used independently or integrated into encyclopedia creation

**Note:** The CSV reader module (`encyclopedia/utils/csv_reader.py`) may be transferred to `../amilib` in the future if CSV reading functionality is needed there.

## Files Created/Modified

### Created:
1. `encyclopedia/utils/csv_reader.py` - CSV reading module
2. `test/encyclopedia/test_csv_reading.py` - Test suite (8 tests)
3. `Examples/create_encyclopedia_from_phraselist.py` - Dedicated script
4. `docs/CSV_READING_IMPLEMENTATION.md` - This documentation

### Modified:
1. `encyclopedia/cli/versioned_editor.py` - Added CSV support to `create` command
2. `encyclopedia/core/encyclopedia.py` - Fixed syntax error (`if para_obj is and` → `if para_obj and`)

## Usage Workflow

### Typical Workflow:
1. **Extract keywords/phrases** → CSV file with columns (e.g., `keyword`, `count`)
2. **Read CSV** → Use `read_phrases_from_csv()` or script
3. **Create encyclopedia** → Use `create_encyclopedia_from_wordlist()` with phrases
4. **Enhance** → Add Wikipedia descriptions, images, etc.

### Example:
```python
from encyclopedia.utils.csv_reader import read_phrases_from_csv
from Examples.create_encyclopedia_from_wordlist import create_encyclopedia_from_wordlist
from pathlib import Path

# Read CSV
phrases, counts = read_phrases_from_csv(
    Path("keywords.csv"),
    phrase_column="keyword",  # or None for auto-detect
    count_column="count"       # or None to omit
)

# Create encyclopedia
encyclopedia = create_encyclopedia_from_wordlist(
    phrases,
    title="My Encyclopedia",
    add_wikipedia=True,
    add_images=False
)

# Save
encyclopedia.save_wiki_normalized_html(Path("encyclopedia.html"))
```

## Future Enhancements

Potential improvements:
- Support for multiple phrase columns
- Support for filtering by count threshold
- Support for sorting by count
- Integration with keyword extraction scripts
- Additional CSV formats (TSV, etc.)

## References

- **CSV Reader Module:** `encyclopedia/utils/csv_reader.py`
- **Tests:** `test/encyclopedia/test_csv_reading.py`
- **Script:** `Examples/create_encyclopedia_from_phraselist.py`
- **CLI:** `encyclopedia/cli/versioned_editor.py`
- **Style Guide:** `docs/STYLE_GUIDE.md`
