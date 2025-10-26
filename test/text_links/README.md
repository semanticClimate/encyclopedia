# Text Links Analysis Test Suite

This test suite provides comprehensive testing for encyclopedia link extraction and analysis, designed for integration with the `../amilib` library.

## Overview

The test suite analyzes the encyclopedia structure from `wg1chap03_dict.html` and validates:
- Search URL resolution to canonical article URLs
- Description link extraction and classification
- External link identification
- Link graph construction
- Article accessibility validation
- Citation target analysis (excluding #cite links as requested)
- Multilingual link detection
- Normalized database creation

## Structure

```
test/text_links/
├── __init__.py
├── test_config.py              # Test configuration and constants
├── link_extractor.py           # Reusable link extraction modules
├── test_01_search_url_resolution.py
├── test_02_description_link_targets.py
├── test_03_link_type_classification.py
├── test_04_external_link_targets.py
├── test_05_link_graph.py
├── test_06_article_accessibility.py
├── test_07_link_density.py
├── test_08_citation_targets.py
├── test_09_normalized_database.py
├── test_10_multilingual_links.py
├── test_utilities.py           # Common utilities and validators
└── run_tests.py               # Main test runner
```

## Test Modules

### 1. Search URL Resolution (`test_01_search_url_resolution.py`)
- **Purpose**: Validate search URL → article URL mapping
- **Key Tests**:
  - Extract search URLs from encyclopedia
  - Resolve search URLs to canonical article URLs
  - Validate resolved URLs are accessible
  - Test redirect depth limits
  - Preserve section anchors

### 2. Description Link Targets (`test_02_description_link_targets.py`)
- **Purpose**: Extract and validate internal Wikipedia links in descriptions
- **Key Tests**:
  - Extract links from description paragraphs
  - Classify links by type (article, file, help, external)
  - Validate internal links are accessible
  - Test relative URL resolution
  - Verify link text consistency

### 3. Link Type Classification (`test_03_link_type_classification.py`)
- **Purpose**: Categorize links by target type
- **Key Tests**:
  - Classify all link types
  - Analyze link patterns
  - Generate target summary
  - Validate classification accuracy

### 4. External Link Targets (`test_04_external_link_targets.py`)
- **Purpose**: Identify non-Wikipedia external links
- **Key Tests**:
  - Extract external links
  - Analyze external domains
  - Classify links by domain type
  - Validate external link accessibility
  - Extract link context

### 5. Link Graph (`test_05_link_graph.py`)
- **Purpose**: Build inter-entry link graph
- **Key Tests**:
  - Build inter-entry link graph
  - Analyze link statistics
  - Identify link clusters
  - Analyze link direction patterns

### 6. Article Accessibility (`test_06_article_accessibility.py`)
- **Purpose**: Ensure linked articles exist and are accessible
- **Key Tests**:
  - Validate article existence
  - Analyze HTTP status codes
  - Handle redirects properly
  - Handle 404 errors
  - Handle network errors
  - Generate error report

### 7. Link Density (`test_07_link_density.py`)
- **Purpose**: Analyze linking patterns and density
- **Key Tests**:
  - Analyze link density across entries
  - Analyze link frequency
  - Identify entry clusters by links
  - Analyze link distribution patterns

### 8. Citation Targets (`test_08_citation_targets.py`)
- **Purpose**: Identify and validate citation targets (excluding #cite links)
- **Key Tests**:
  - Extract citation patterns
  - Analyze reference patterns
  - Validate citation completeness
  - Extract citation context
  - Analyze citation networks

### 9. Normalized Database (`test_09_normalized_database.py`)
- **Purpose**: Create normalized database of all link targets
- **Key Tests**:
  - Build normalized link database
  - Extract link metadata
  - Generate database statistics
  - Validate database consistency

### 10. Multilingual Links (`test_10_multilingual_links.py`)
- **Purpose**: Detect and handle multilingual Wikipedia links
- **Key Tests**:
  - Detect multilingual links
  - Analyze language patterns
  - Validate interlanguage links
  - Analyze language consistency
  - Generate multilingual summary

## Usage

### Running Individual Tests
```bash
cd test/text_links
python -m pytest test_01_search_url_resolution.py -v
```

### Running All Tests
```bash
cd test/text_links
python run_tests.py
```

### Using with pytest
```bash
cd test/text_links
pytest -v
```

## Configuration

Test configuration is defined in `test_config.py`:
- Input/output paths
- Test parameters
- URL patterns
- Expected output structure
- Test assertions

## Output

All test outputs are saved to `temp/text_links_output/`:
- JSON files with extracted data
- Validation reports
- Error reports
- Summary statistics
- Markdown test report

## Integration with amilib

The modules are designed for easy integration with `../amilib`:
- Modular design with clear interfaces
- Reusable components (`EncyclopediaLinkExtractor`, `LinkValidator`)
- Configurable parameters
- Comprehensive error handling
- Structured output formats

## Key Features

- **Modular Design**: Each test is self-contained with clear inputs/outputs
- **Reusable Components**: Core functionality can be extracted to amilib
- **Comprehensive Coverage**: Tests all aspects of link extraction and analysis
- **Error Handling**: Robust handling of network errors, malformed data
- **Validation**: Extensive validation of extracted data and results
- **Documentation**: Clear documentation and reporting

## Dependencies

- `pytest` - Test framework
- `requests` - HTTP requests for link validation
- `beautifulsoup4` - HTML parsing
- `pathlib` - File path handling
- `json` - Data serialization
- `collections` - Data structures
- `urllib.parse` - URL parsing
- `re` - Regular expressions

## Style Guide Compliance

This test suite follows the pygetpapers style guide:
- ✅ **No wildcard imports** - All imports are explicit
- ✅ **Path construction** - Always use `Path()` with comma-separated arguments
- ✅ **Modular design** - Reusable components for integration with `../amilib`
- ✅ **Clear test structure** - Define inputs → call module → make assertions

**Example of correct path usage:**
```python
output_file = Path(self.output_dir, "results.json")  # ✅ CORRECT - comma-separated arguments
output_file = self.output_dir / "results.json"  # ❌ WRONG - uses / operator
output_file = str(self.output_dir) + "/results.json"  # ❌ WRONG - string concatenation
```

**According to style guide:** Use clean Path construction with comma-separated arguments

## Notes

- Citation links (`#cite`) are explicitly excluded as requested
- All outputs are saved to `temp/` directory for easy cleanup
- Tests use symbols for strings where appropriate
- Modular structure allows easy integration into amilib
- Comprehensive error handling and validation throughout
