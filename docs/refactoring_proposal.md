# Refactoring Proposal: `create_encyclopedia_from_wordlist.py`

## Problem Statement

Current issues:
1. **First sentences/definitions not being extracted** - Code exists but may not be working correctly
2. **Image links not being added** - Code exists but may not be working correctly
3. **No validation** - No way to verify that extraction and image addition succeeded
4. **Monolithic function** - `create_encyclopedia_from_wordlist()` is 700+ lines doing too many things
5. **Poor error visibility** - Exceptions are caught and swallowed without proper reporting

## Proposed Refactoring

### 1. Extract Core Steps into Separate Functions

Break down `create_encyclopedia_from_wordlist()` into focused, testable functions:

```python
# Core pipeline steps
def _create_dictionary_from_terms(terms: List[str], title: str, temp_path: Path) -> AmiDictionary:
    """Step 1: Create basic dictionary structure from terms."""
    pass

def _enhance_dictionary_with_wikipedia(dictionary: AmiDictionary) -> AmiDictionary:
    """Step 2: Add Wikipedia content to dictionary entries."""
    pass

def _convert_dictionary_to_encyclopedia(dictionary: AmiDictionary, temp_html_path: Path) -> AmiEncyclopedia:
    """Step 3: Convert dictionary HTML to encyclopedia."""
    pass

def _add_wikipedia_descriptions_to_encyclopedia(
    encyclopedia: AmiEncyclopedia, 
    batch_size: int = 10
) -> AmiEncyclopedia:
    """Step 5: Add Wikipedia descriptions (with first sentence extraction) to encyclopedia entries."""
    pass

def _add_image_links_to_encyclopedia(
    encyclopedia: AmiEncyclopedia,
    batch_size: int = 10
) -> AmiEncyclopedia:
    """Step 8: Add Wikipedia image links to encyclopedia entries."""
    pass
```

### 2. Create Validation Functions

Add validation functions to check results:

```python
def validate_first_sentences_extracted(encyclopedia: AmiEncyclopedia) -> Dict[str, Any]:
    """
    Validate that first sentences/definitions have been extracted.
    
    Returns:
        Dictionary with:
        - total_entries: int
        - entries_with_definitions: int
        - entries_without_definitions: List[Dict] (entries missing definitions)
        - success_rate: float (percentage)
        - is_valid: bool
    """
    pass

def validate_image_links_added(encyclopedia: AmiEncyclopedia) -> Dict[str, Any]:
    """
    Validate that image links have been added.
    
    Returns:
        Dictionary with:
        - total_entries: int
        - entries_with_images: int
        - entries_without_images: List[Dict] (entries missing images)
        - success_rate: float (percentage)
        - is_valid: bool
    """

def validate_encyclopedia_completeness(encyclopedia: AmiEncyclopedia) -> Dict[str, Any]:
    """
    Comprehensive validation of encyclopedia completeness.
    
    Returns:
        Dictionary with validation results for:
        - definitions (first sentences)
        - images
        - Wikipedia URLs
        - Wikidata IDs
        - descriptions
    """
    pass
```

### 3. Refactor Wikipedia Description Addition

Extract and improve the Wikipedia description logic:

```python
def _add_wikipedia_description_to_entry(
    entry: Dict,
    encyclopedia: AmiEncyclopedia,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Add Wikipedia description to a single entry, extracting first sentence.
    
    Returns:
        Dictionary with:
        - success: bool
        - has_definition: bool (first sentence extracted)
        - has_description: bool (full description)
        - wikipedia_url: str or None
        - error: str or None
    """
    pass

def _extract_and_store_first_sentence(
    entry: Dict,
    description_html: str,
    definition_html: str
) -> bool:
    """
    Extract first sentence from description and store as definition_html.
    
    Returns:
        True if first sentence was successfully extracted and stored
    """
    pass
```

### 4. Refactor Image Link Addition

Extract and improve the image link logic:

```python
def _add_image_link_to_entry(
    entry: Dict,
    encyclopedia: AmiEncyclopedia,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Add Wikipedia image link to a single entry.
    
    Returns:
        Dictionary with:
        - success: bool
        - has_image_link: bool
        - image_url: str or None
        - error: str or None
    """
    pass

def _create_wikipedia_image_link(image_element) -> Optional[ET.Element]:
    """
    Create a Wikipedia image link element from an image element.
    
    Returns:
        lxml Element (<a> tag) linking to Wikipedia File: page, or None
    """
    pass
```

### 5. Improve Error Handling and Reporting

Add structured error reporting:

```python
class EncyclopediaCreationError(Exception):
    """Base exception for encyclopedia creation errors."""
    pass

class WikipediaExtractionError(EncyclopediaCreationError):
    """Error extracting Wikipedia content."""
    pass

class ImageExtractionError(EncyclopediaCreationError):
    """Error extracting images."""
    pass

def _report_processing_results(
    step_name: str,
    total: int,
    successful: int,
    failed: List[Dict],
    verbose: bool = True
) -> None:
    """Report processing results in a structured way."""
    pass
```

### 6. Refactored Main Function Structure

```python
def create_encyclopedia_from_wordlist(
    terms: List[str],
    title: str = "My Encyclopedia",
    add_wikipedia: bool = True,
    add_images: bool = False,
    batch_size: int = 10,
    validate: bool = True,
    verbose: bool = False
) -> AmiEncyclopedia:
    """
    Create an encyclopedia from a list of terms.
    
    Args:
        terms: List of terms/phrases to include
        title: Title for the encyclopedia
        add_wikipedia: If True, add Wikipedia descriptions
        add_images: If True, add Wikipedia image links
        batch_size: Number of entries to process at a time
        validate: If True, validate results at the end
        verbose: If True, show detailed progress
        
    Returns:
        AmiEncyclopedia instance
        
    Raises:
        EncyclopediaCreationError: If critical steps fail
    """
    # Step 1: Create dictionary
    dictionary = _create_dictionary_from_terms(terms, title, temp_path)
    
    # Step 2: Enhance with Wikipedia (optional)
    if add_wikipedia:
        dictionary = _enhance_dictionary_with_wikipedia(dictionary)
    
    # Step 3: Convert to encyclopedia
    encyclopedia = _convert_dictionary_to_encyclopedia(dictionary, temp_html_path)
    
    # Step 4: Normalize by Wikidata ID
    encyclopedia.normalize_by_wikidata_id()
    
    # Step 5: Merge synonyms
    encyclopedia.merge()
    
    # Step 6: Add Wikipedia descriptions (if requested)
    if add_wikipedia:
        encyclopedia = _add_wikipedia_descriptions_to_encyclopedia(
            encyclopedia, batch_size
        )
    
    # Step 7: Add image links (if requested)
    if add_images:
        encyclopedia = _add_image_links_to_encyclopedia(
            encyclopedia, batch_size
        )
    
    # Step 8: Validate results (if requested)
    if validate:
        validation_results = validate_encyclopedia_completeness(encyclopedia)
        _report_validation_results(validation_results, verbose)
    
    return encyclopedia
```

## File Structure

### Proposed New File: `encyclopedia/utils/encyclopedia_builder.py`

Move core building logic here:

```python
"""
Encyclopedia building utilities.

Provides functions for creating encyclopedias from wordlists with
Wikipedia integration, image links, and validation.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import lxml.etree as ET

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from amilib.ami_dict import AmiDictionary

# Core building functions
def create_dictionary_from_terms(...): ...
def enhance_with_wikipedia(...): ...
def convert_to_encyclopedia(...): ...

# Wikipedia functions
def add_wikipedia_descriptions(...): ...
def extract_first_sentence(...): ...

# Image functions
def add_image_links(...): ...
def create_image_link(...): ...

# Validation functions
def validate_definitions(...): ...
def validate_images(...): ...
def validate_completeness(...): ...
```

### Proposed New File: `encyclopedia/utils/validation.py`

```python
"""
Validation utilities for encyclopedia completeness.

Provides functions to validate that encyclopedias have been properly
populated with definitions, images, descriptions, etc.
"""

from typing import Dict, List, Any
from encyclopedia.core.encyclopedia import AmiEncyclopedia

def validate_first_sentences_extracted(encyclopedia: AmiEncyclopedia) -> Dict[str, Any]:
    """Validate that first sentences have been extracted."""
    pass

def validate_image_links_added(encyclopedia: AmiEncyclopedia) -> Dict[str, Any]:
    """Validate that image links have been added."""
    pass

def validate_encyclopedia_completeness(encyclopedia: AmiEncyclopedia) -> Dict[str, Any]:
    """Comprehensive validation."""
    pass

def print_validation_report(results: Dict[str, Any]) -> None:
    """Print validation results in a readable format."""
    pass
```

## Validation Implementation Details

### `validate_first_sentences_extracted()`

```python
def validate_first_sentences_extracted(encyclopedia: AmiEncyclopedia) -> Dict[str, Any]:
    """
    Check that entries have definition_html (first sentence) extracted.
    
    Looks for:
    - entry['definition_html'] exists and is non-empty
    - entry['definition_html'] contains <span class="first_sentence_definition">
    - First sentence is actually extracted (not just full description)
    """
    total = len(encyclopedia.entries)
    entries_with_definitions = []
    entries_without_definitions = []
    
    for entry in encyclopedia.entries:
        term = entry.get('term', entry.get('canonical_term', 'Unknown'))
        definition_html = entry.get('definition_html', '')
        
        # Check if definition exists and contains first sentence span
        has_definition = (
            definition_html and 
            'first_sentence_definition' in definition_html
        )
        
        if has_definition:
            entries_with_definitions.append({
                'term': term,
                'definition_html': definition_html[:100] + '...' if len(definition_html) > 100 else definition_html
            })
        else:
            entries_without_definitions.append({
                'term': term,
                'wikipedia_url': entry.get('wikipedia_url', ''),
                'description_html': entry.get('description_html', '')[:50] + '...' if entry.get('description_html') else None
            })
    
    success_rate = (len(entries_with_definitions) / total * 100) if total > 0 else 0.0
    
    return {
        'total_entries': total,
        'entries_with_definitions': len(entries_with_definitions),
        'entries_without_definitions': len(entries_without_definitions),
        'success_rate': success_rate,
        'is_valid': len(entries_without_definitions) == 0,
        'entries_with_definitions': entries_with_definitions[:10],  # Sample
        'entries_without_definitions': entries_without_definitions[:10]  # Sample
    }
```

### `validate_image_links_added()`

```python
def validate_image_links_added(encyclopedia: AmiEncyclopedia) -> Dict[str, Any]:
    """
    Check that entries have image links added.
    
    Looks for:
    - entry['figure_html'] exists and is an element or HTML string
    - entry['figure_html'] contains link to Wikipedia File: page
    - entry['image_link'] URL exists
    """
    total = len(encyclopedia.entries)
    entries_with_images = []
    entries_without_images = []
    
    for entry in encyclopedia.entries:
        term = entry.get('term', entry.get('canonical_term', 'Unknown'))
        figure_html = entry.get('figure_html')
        image_link = entry.get('image_link')
        
        # Check if image link exists
        has_image = False
        if figure_html:
            # Check if it's an element
            if hasattr(figure_html, 'tag'):
                if figure_html.tag == 'a':
                    href = figure_html.get('href', '')
                    if '/wiki/File:' in href or '/File:' in href:
                        has_image = True
            # Check if it's HTML string
            elif isinstance(figure_html, str):
                if 'wikipedia-image-link' in figure_html or '/wiki/File:' in figure_html:
                    has_image = True
        
        if image_link and ('/wiki/File:' in image_link or '/File:' in image_link):
            has_image = True
        
        if has_image:
            entries_with_images.append({
                'term': term,
                'image_link': image_link or (figure_html.get('href') if hasattr(figure_html, 'get') else None)
            })
        else:
            entries_without_images.append({
                'term': term,
                'wikipedia_url': entry.get('wikipedia_url', ''),
                'has_figure_html': figure_html is not None,
                'has_image_link': image_link is not None
            })
    
    success_rate = (len(entries_with_images) / total * 100) if total > 0 else 0.0
    
    return {
        'total_entries': total,
        'entries_with_images': len(entries_with_images),
        'entries_without_images': len(entries_without_images),
        'success_rate': success_rate,
        'is_valid': len(entries_without_images) == 0,
        'entries_with_images': entries_with_images[:10],  # Sample
        'entries_without_images': entries_without_images[:10]  # Sample
    }
```

## Benefits of Refactoring

1. **Testability**: Each function can be tested independently
2. **Debuggability**: Easier to identify where failures occur
3. **Maintainability**: Smaller, focused functions are easier to understand and modify
4. **Validation**: Clear validation shows what worked and what didn't
5. **Reusability**: Functions can be reused in other contexts
6. **Error Visibility**: Structured error reporting makes issues visible

## Migration Strategy

1. **Phase 1**: Create new utility files with extracted functions
2. **Phase 2**: Update `create_encyclopedia_from_wordlist.py` to use new functions
3. **Phase 3**: Add validation functions
4. **Phase 4**: Add comprehensive tests
5. **Phase 5**: Update documentation

## Testing Strategy

After refactoring, add tests:

```python
def test_extract_first_sentence():
    """Test that first sentence is extracted correctly."""
    pass

def test_create_image_link():
    """Test that image links are created correctly."""
    pass

def test_validate_definitions():
    """Test validation of definition extraction."""
    pass

def test_validate_images():
    """Test validation of image links."""
    pass
```

## Summary

This refactoring will:
- ✅ Break down the monolithic function into smaller, testable pieces
- ✅ Add validation to verify definitions and images are extracted
- ✅ Improve error handling and reporting
- ✅ Make debugging easier by isolating concerns
- ✅ Provide clear feedback on what succeeded and what failed

The key insight is that **validation is essential** - we need to know if definitions and images were actually extracted, not just that the code ran without exceptions.
