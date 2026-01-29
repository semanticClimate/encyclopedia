# Encyclopedia Project Style Guide

**Date:** January 23, 2026 (system date of generation)  
**Status:** Active

This style guide defines coding standards and best practices for the Encyclopedia project. It incorporates and extends rules from the amilib and pygetpapers style guides.

## Related Style Guides

This project follows the style conventions established in:

1. **amilib Style Guide**: `../amilib/docs/style_guide_compliance.md`
   - Import style (absolute imports with module prefixes)
   - Empty `__init__.py` files
   - No mocks in tests
   - No magic strings
   - Path construction rules

2. **pygetpapers Style Guide**: `../pygetpapers/docs/styleguide.md`
   - File naming conventions
   - Development protocol
   - Path construction
   - Date usage rules

**Important**: Always read the parent style guides before making changes. This guide extends them with encyclopedia-specific rules.

---

## Import Style

### Absolute Imports with Module Prefixes

**Rule:** Use absolute imports with module prefixes

**✅ CORRECT:**
```python
from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources
from amilib.ami_dict import AmiDictionary
from amilib.wikimedia import WikipediaPage
```

**❌ WRONG:**
```python
from .core.encyclopedia import AmiEncyclopedia  # Relative import
from ..utils.resources import Resources  # Relative import
```

**Rationale**: Absolute imports are explicit, avoid confusion about module hierarchy, and work consistently across different execution contexts.

### NO PYTHONPATH

**Rule:** Do not use PYTHONPATH environment variable or sys.path manipulation

- ✅ Tests should work without setting PYTHONPATH
- ✅ Use pytest.ini `pythonpath = .` configuration instead
- ✅ Use `--import-mode=importlib` in pytest configuration
- ❌ Do not manipulate `sys.path` in conftest.py or test files
- ❌ Do not require PYTHONPATH to be set manually

**Rationale**: Manipulating Python's import path is fragile and can cause import conflicts. Use proper package installation instead.

### NO ENVIRONMENT VARIABLES

**Rule:** Do not rely on environment variables for code execution

- ✅ Code should work without any environment variables set
- ✅ Use configuration files (pytest.ini, setup.py, etc.) instead
- ✅ Use command-line arguments or config files for runtime configuration
- ❌ Do not require environment variables to be set for tests or code to run
- ❌ Do not use `os.environ` for critical path or configuration
- ✅ Exception: Environment variables for secrets/API keys are acceptable if clearly documented

**Rationale**: Environment variables create dependencies that make code harder to test and deploy. Configuration files are more explicit and version-controlled.

---

## File Naming

### Alphanumeric Characters and Underscores Only

**Rule:** All filenames should only have alphanumeric characters and underscores

**✅ CORRECT:**
```python
test_encyclopedia.py
ami_encyclopedia.py
create_encyclopedia_from_wordlist.py
```

**❌ WRONG:**
```python
test-encyclopedia.py  # Hyphens not allowed
test.encyclopedia.py  # Dots not allowed
test encyclopedia.py  # Spaces not allowed
```

**Rationale**: Using only alphanumeric characters and underscores ensures maximum compatibility across different operating systems and avoids issues with special characters in file paths.

---

## Code Organization

### Empty `__init__.py` Files

**Rule:** All `__init__.py` files should be empty unless explicitly agreed

**✅ CORRECT:**
```python
# encyclopedia/__init__.py
# Empty file
```

**❌ WRONG:**
```python
# encyclopedia/__init__.py
from .core.encyclopedia import AmiEncyclopedia
from .utils.resources import Resources
```

**Rationale**: Empty `__init__.py` files keep the package structure clean and avoid circular import issues. Re-exports should only be added if explicitly agreed upon.

### Path Construction

**Rule:** Always use `Path()` constructor with comma-separated arguments. Never use string concatenation with "/" or isolated "/" characters.

**✅ CORRECT:**
```python
from pathlib import Path

# Use Path constructor with multiple arguments
file_path = Path(Resources.TEMP_DIR, "examples", "create_encyclopedia", "output.html")
output_dir = Path(Resources.TEMP_DIR, "scripts", "glossary_processor")

# Use Path.joinpath() for dynamic paths
base_path = Path("temp")
file_path = base_path.joinpath("dictionaries", "wg3", "annex-vi.html")
```

**❌ WRONG:**
```python
# Using string concatenation with "/"
file_path = "temp" + "/" + "examples" + "/" + "output.html"

# Using isolated "/" in Path
file_path = Path("temp/examples/output.html")

# Using / operator (prefer Path constructor)
file_path = Path("temp") / "examples" / "output.html"
```

**Rationale**: Using Path constructor with multiple arguments is explicit, clear, avoids platform-specific path separator issues, and makes path construction more readable.

---

## Temporary Files

### Use Resources.TEMP_DIR

**Rule:** All temporary files must be created under `<root>/temp`, which is defined in `Resources.TEMP_DIR`. Use subdirectories based on modules and classes.

**✅ CORRECT:**
```python
from pathlib import Path
from encyclopedia.utils.resources import Resources

# For test files - use Path constructor with multiple arguments
test_output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "EncyclopediaTest")
test_output_dir.mkdir(parents=True, exist_ok=True)
output_file = Path(test_output_dir, "test_output.html")

# For scripts
temp_dir = Path(Resources.TEMP_DIR, "scripts", "annotation")

# For examples
temp_dir = Path(Resources.TEMP_DIR, "examples", "create_encyclopedia")

# Use helper method
temp_dir = Resources.get_temp_dir("examples", "create_encyclopedia")
```

**❌ WRONG:**
```python
import tempfile

# Using system temp directory
temp_dir = Path(tempfile.mkdtemp())

# Using relative temp directory
temp_dir = Path("temp")

# Using / operator instead of Path constructor
temp_dir = Resources.TEMP_DIR / "test" / "encyclopedia"

# Writing to root directory
output_file = Path("output.html")
```

**Subdirectory Naming Conventions:**
- Tests: `Path(Resources.TEMP_DIR, "test", <module_name>, <class_name>)`
- Scripts: `Path(Resources.TEMP_DIR, "scripts", <script_name>)`
- Examples: `Path(Resources.TEMP_DIR, "examples", <example_name>)`
- Other modules: `Path(Resources.TEMP_DIR, <module_name>, <class_or_function>)`

**Rationale**: Using a centralized temp directory keeps all temporary files in one predictable location, makes cleanup easier, allows easy inspection of test outputs, and follows consistent directory structure based on modules/classes.

### Distinguish Between Fixture Temp Files and Human-Inspection Temp Artifacts

**Rule:** We use temporary files in two complementary ways:

1. **Test fixtures (ephemeral)**: Created for automated tests and cleaned up automatically.
2. **Human inspection artifacts (persisted)**: Written to `<root>/temp/` for manual validation after test runs.

- ✅ **Fixtures** should create isolated temporary directories/files (e.g., `tmp_path`, `TemporaryDirectory`, or project fixtures in `conftest.py`) and use them for assertions.
- ✅ **Human inspection outputs** may be written to `<root>/temp/...` (via `Resources.TEMP_DIR`) to support manual review.
- ✅ Human inspection outputs may **overwrite previous versions** (to avoid unbounded growth).
- ✅ The `<root>/temp/` directory is **not committed to GitHub** and is **not long-term storage**.
- ✅ Even if outputs are persisted for review, tests should still assert at least **existence** and **basic content/sanity** (e.g., non-empty HTML, expected tags/strings).
- ❌ Do not rely on environment variables to control this behavior.

**Rationale**: Fixture outputs keep tests deterministic and self-contained. Persisted artifacts in `<root>/temp/` enable visual/human QA for transformations (e.g., PDF→HTML) without polluting the repository or requiring commits of generated files.

---

## Constants and Magic Strings

### No Magic Strings

**Rule:** Do not use hardcoded string literals for values that represent constants, identifiers, or configuration. Use class constants or accessor methods instead.

**✅ CORRECT:**
```python
class AmiEncyclopedia:
    # Define constants as class attributes
    REASON_MISSING_WIKIPEDIA = "missing_wikipedia"
    REASON_GENERAL_TERM = "general_term"
    REASON_FALSE_WIKIPEDIA = "false_wikipedia"
    
    CATEGORY_TRUE_WIKIPEDIA = "true_wikipedia"
    CATEGORY_NO_WIKIPEDIA = "no_wikipedia"
    CATEGORY_DISAMBIGUATION = "disambiguation"
    
    @classmethod
    def get_valid_checkbox_reasons(cls) -> list:
        """Get list of valid checkbox reason values"""
        return [
            cls.REASON_MISSING_WIKIPEDIA,
            cls.REASON_GENERAL_TERM,
            cls.REASON_FALSE_WIKIPEDIA,
        ]
    
    def _add_hide_checkbox(self, container, entry_id: str, reason: str):
        # Use constant instead of string literal
        if reason == self.REASON_MISSING_WIKIPEDIA:
            # ...
```

**❌ WRONG:**
```python
class AmiEncyclopedia:
    def _add_hide_checkbox(self, container, entry_id: str, reason: str):
        # Magic string - hard to maintain and error-prone
        if reason == "missing_wikipedia":
            # ...
```

**When to Use Constants:**
- Configuration values (e.g., checkbox reasons, entry categories)
- Status codes or state identifiers
- Attribute names that are used in multiple places
- Any string that represents a fixed set of possible values

**When String Literals Are Acceptable:**
- User-facing messages or labels
- Format strings or templates
- One-off string values that are not reused
- File extensions or MIME types (though constants are still preferred)

**Rationale**: Magic strings create several problems:
- **Typos**: Easy to make mistakes with string literals
- **Maintainability**: If a value changes, must update it in multiple places
- **Discoverability**: Hard to find all usages of a string value
- **Type safety**: No way to validate string values at development time
- **Refactoring**: Difficult to rename or change values across codebase

---

## Testing

### No sys.path Manipulation

**Rule:** Tests should rely on pytest configuration, not path manipulation

- ✅ Use pytest.ini `pythonpath = .` configuration
- ✅ Use `--import-mode=importlib` in pytest configuration
- ❌ Do not manipulate `sys.path` in conftest.py or test files
- ❌ Do not require PYTHONPATH to be set manually

### No Mocks

**Rule:** Do not use mocks or patches in tests. Tests should use real implementations and real services.

**✅ CORRECT:**
```python
def test_service_connection_basic(self):
    """Test basic service connection functionality."""
    result = FileLib.check_service_connection(
        service_url="https://httpbin.org/status/200",
        service_name="HTTPBin Test",
        timeout=10
    )
    # Handle both success and failure cases
    if result['connected']:
        self.assertEqual(result['status_code'], 200)
    else:
        self.assertIsNotNone(result['error'])
```

**❌ WRONG:**
```python
@patch('amilib.file_lib.requests.get')
def test_service_connection_basic(self, mock_get):
    """Test basic service connection functionality."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    # ... test code
```

**Rationale**: Tests should verify real behavior, not mocked behavior. Mocks hide integration issues and make tests less reliable. If external services are unreliable, tests should handle both success and failure cases gracefully.

### Meaningful Assertion Messages

**Rule:** All assertions should have human-meaningful messages that explain what failed and why.

**✅ CORRECT:**
```python
assert results['entries_with_html_descriptions'] == 1, \
    f"Expected 1 entry with HTML description, but got {results['entries_with_html_descriptions']}. " \
    f"Entries without HTML: {results['entries_without_html_descriptions']}"

assert normalized_url == expected_url, \
    f"URL normalization failed. Expected '{expected_url}', but got '{normalized_url}'. " \
    f"Original URL was '{original_url}'"
```

**❌ WRONG:**
```python
assert results['entries_with_html_descriptions'] == 1
assert normalized_url == expected_url
```

**Rationale**: Meaningful assertion messages help developers quickly understand what went wrong and why, reducing debugging time.

### Test Output to temp/

**Rule:** All tests should output to `temp/` directory. No tests should write to root directory unless specifically requested.

**✅ CORRECT:**
```python
from pathlib import Path
from encyclopedia.utils.resources import Resources

# Use Resources.TEMP_DIR with subdirectories
test_output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestClassName")
test_output_dir.mkdir(parents=True, exist_ok=True)
output_file = Path(test_output_dir, "test_output.html")
```

**❌ WRONG:**
```python
# Writing to root directory
output_file = Path("test_output.html")

# Using system temp directory
import tempfile
output_file = Path(tempfile.mkdtemp(), "test_output.html")
```

---

## Documentation

### Date Usage

**Rule:** Always use current system date. Run `date` command to get current date from system clock.

**✅ CORRECT:**
```markdown
**Date:** January 23, 2026 (system date of generation)
**Date:** 2026-01-23 (system date of generation)
```

**❌ WRONG:**
```markdown
**Date:** 2026-01-15  # Assumed date
**Date:** Today  # Vague
```

**Rule:** Document date sources explicitly.

**✅ CORRECT:**
- "January 23, 2026 (system date of generation)" - Date when code/document was created
- "2023-12-01 (extracted from source document)" - Date taken from source materials

**Rationale**: Using incorrect dates in documentation creates confusion and reduces credibility. Always verify the current date from the system.

### Comprehensive Documentation

**Rule:** All components should have comprehensive documentation.

- ✅ **README files**: All major components should have README files
- ✅ **Docstrings**: All public methods should have docstrings
- ✅ **Inline comments**: Complex logic should have explanatory comments
- ✅ **Workflow documentation**: Document complete workflows (see `docs/html_to_knowledge_graph_workflow.md`)

---

## Development Protocol

### Before Any Code Changes

**Rule:** Follow strict development protocol for all code changes.

1. **Full schema design** - Define exact output structure, file naming, directory layout
2. **Validation tool** - Create tool to verify output conforms to schema and prevent regression
3. **File change plan** - List exactly what files will be edited/created/deleted
4. **User approval** - Wait for explicit agreement before proceeding
5. **Small steps** - Make minimal changes, show diffs on demand

**For Any Code Project:**
1. **Propose changes** - "I will edit X, create Y, delete Z"
2. **Get agreement** - Wait for "proceed" or "modify plan"
3. **Show diffs** - On demand, show exactly what will change
4. **Test thoroughly** - Ensure existing functionality remains intact

**Rationale**: This protocol prevents breaking working systems, ensures user control over changes, and maintains code quality through systematic validation and testing.

### Never Write Code Without Explicit User Approval

**Rule:** Always propose changes, wait for approval, then implement.

- ✅ **Good**: Propose changes, wait for approval, then implement
- ❌ **Bad**: Writing code immediately without user agreement

**Rationale**: Users have invested significant time in building working systems. All changes must be approved to prevent regression and maintain trust.

### Always Commit Before Making Changes and Test After

**Rule:** Before any code changes, make a commit, then make changes, then run tests.

**Before Any Code Changes:**
1. **Make a commit** - Save current state so we can revert if necessary
2. **Make the changes** - Implement the approved modifications
3. **Run relevant tests** - Execute tests that cover the changed functionality
4. **Report results** - Inform user of test outcomes before proceeding

**Rationale**: This protocol ensures we can always revert to a working state and validates that changes don't break existing functionality.

### Never Use Destructive Commands Without Explicit Approval

**Rule:** Never use destructive commands without explicit approval.

- ✅ **Good**: Use `git clean -n` to preview what would be deleted, then ask for approval
- ✅ **Good**: Commit important work before using any destructive commands
- ❌ **Bad**: Using `git clean -fd`, `rm -rf`, or other destructive commands without understanding consequences
- ❌ **Bad**: Using force flags (`-f`) without checking what will be affected

**Rationale**: Destructive commands can permanently delete hours of work. Always preview, understand, and get explicit approval before using them.

---

## Encyclopedia-Specific Rules

### Always Use amilib Routines Where Possible

**Rule:** Always use routines from amilib where possible. Prefer amilib methods over custom implementations.

**✅ CORRECT:**
```python
from amilib.wikimedia import WikipediaPage

# Use amilib method for first paragraph
para_obj = wikipedia_page.create_first_wikipedia_para()
if para_obj and para_obj.para_element:
    para_elem = para_obj.para_element
    # Use the paragraph element from amilib

# Use amilib method for images
img_elem = wikipedia_page.extract_a_elem_with_image_from_infobox()
if img_elem:
    # Use the image element from amilib
```

**❌ WRONG:**
```python
# Manual extraction instead of using amilib methods
paragraphs = wikipedia_page.html_elem.xpath(".//div[@id='mw-content-text']//p[1]")
# This bypasses amilib's built-in filtering and processing
```

**Rationale**: amilib routines are tested, handle edge cases, and are maintained. Using them reduces bugs and ensures consistency with other projects that use amilib.

**When to Use amilib Methods:**
- ✅ Wikipedia page lookup: `WikipediaPage.lookup_wikipedia_page_for_term()`
- ✅ First paragraph extraction: `wikipedia_page.create_first_wikipedia_para()`
- ✅ Image extraction: `wikipedia_page.extract_a_elem_with_image_from_infobox()`
- ✅ Infobox extraction: `wikipedia_page.get_infobox()`
- ✅ Wikidata ID extraction: `wikipedia_page.get_wikidata_item()`

**When Custom Code is Acceptable:**
- Processing results from amilib methods (e.g., formatting HTML output)
- Adding encyclopedia-specific features not in amilib
- Fallback only when amilib method is unavailable (check with `hasattr()`)

### Entry Dictionary Structure

**Rule:** Encyclopedia entries should follow a consistent dictionary structure.

**Standard Entry Dictionary:**
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

### Wikidata ID as Primary Identifier

**Rule:** Use Wikidata ID as the primary identifier for normalization and merging.

- ✅ Normalize entries by Wikidata ID to identify synonyms
- ✅ Merge entries with the same Wikidata ID
- ✅ Handle entries without Wikidata IDs separately

### HTML Output Structure

**Rule:** Encyclopedia HTML output should follow semantic markup conventions.

- ✅ Use `role="ami_encyclopedia"` for encyclopedia container
- ✅ Use `role="ami_entry"` for entry divs
- ✅ Include `wikidataID` attribute on entry divs
- ✅ Use semantic HTML structure

### Batch Processing

**Rule:** When processing large numbers of entries, use batch processing with progress reporting.

**✅ CORRECT:**
```python
def process_batch(entries, batch_size=10, verbose=False):
    """Process entries in batches with progress reporting."""
    total = len(entries)
    for i in range(0, total, batch_size):
        batch = entries[i:i+batch_size]
        # Process batch
        if verbose:
            print(f"Processed {min(i+batch_size, total)}/{total} entries")
```

**Rationale**: Batch processing prevents overwhelming external services (like Wikipedia API) and provides better user feedback.

---

## Best Practices Summary

### Before Making Changes

1. **Read the style guide** - Always check this guide and parent guides
2. **Examine existing code** - Look at how similar patterns are implemented
3. **Follow established conventions** - Don't assume common patterns apply
4. **Ask for clarification** - If unsure about style rules, ask before proceeding

### During Development

1. **Use absolute imports** - Always with module prefix (`encyclopedia.`, `amilib.`)
2. **Keep __init__.py empty** - Unless explicitly agreed otherwise
3. **Use Resources.TEMP_DIR** - For all temporary files
4. **Use Path constructor** - With comma-separated arguments
5. **Use constants** - Instead of magic strings
6. **Test thoroughly** - Ensure changes don't break existing functionality
7. **Document decisions** - Record why certain style choices were made

### After Changes

1. **Verify compliance** - Double-check all changes follow style guide
2. **Run tests** - Ensure functionality is maintained
3. **Update documentation** - Keep style guide current with new rules
4. **Review with team** - Get feedback on style compliance

---

## References

- **amilib Style Guide**: `../amilib/docs/style_guide_compliance.md`
- **pygetpapers Style Guide**: `../pygetpapers/docs/styleguide.md`
- **Encyclopedia Pipeline Documentation**: `docs/encyclopedia_pipeline_documentation.md`
- **HTML to Knowledge Graph Workflow**: `docs/html_to_knowledge_graph_workflow.md`

---

## Version Management

### Single Source of Truth

**Rule:** The version number must be stored in `encyclopedia/__init__.py` as `__version__`. This is the single source of truth.

**✅ CORRECT:**
```python
# encyclopedia/__init__.py
__version__ = "0.0.1"  # 2026-01-23
```

**❌ WRONG:**
```python
# Hardcoding version in setup.py
version = "0.0.1"  # Don't hardcode here
```

**Rationale**: Having a single source of truth prevents version mismatches and makes it easy to find and update the version.

### Version Format

**Rule:** Version numbers use semantic versioning format: `major.minor.point` (e.g., `0.0.1`, `0.1.0`, `1.0.0`).

**Version Numbering:**
- ✅ **Starting version**: `0.0.1` (major.minor.point)
- ✅ **Point increments**: `0.0.1` → `0.0.2` → `0.0.3` (each commit)
- ✅ **Minor increments**: `0.0.9` → `0.1.0` (significant feature additions)
- ✅ **Major increments**: `0.9.9` → `1.0.0` (major releases or breaking changes)

**Examples:**
- `0.0.1` - Initial version
- `0.0.2` - First commit after initial version
- `0.0.15` - 15th commit
- `0.1.0` - Minor version bump (new feature set)
- `1.0.0` - Major release

**Rationale**: Starting at `0.0.1` follows semantic versioning conventions for pre-1.0 releases. Point version increments on each commit provide clear tracking of changes.

### Version Increment on Every Commit

**Rule:** Each commit must increase the point version number.

- ✅ **Good**: Increment point version for every commit (e.g., `0.0.1` → `0.0.2`)
- ❌ **Bad**: Making multiple commits without version bumps

**Implementation Options:**

**Option 1: Manual Increment (Recommended for now)**
- Developer manually increments version in `encyclopedia/__init__.py` before committing
- Simple and explicit
- Requires discipline to remember

**Option 2: Pre-commit Hook (Future enhancement)**
- Git pre-commit hook automatically increments version
- Requires hook setup and version parsing logic
- Can be bypassed if needed

**Option 3: Commit Message Hook**
- Post-commit hook reads commit message and increments version
- More complex, requires parsing commit messages
- Less reliable than pre-commit

**Current Approach:** Manual increment (Option 1) - developer updates `__version__` in `encyclopedia/__init__.py` before each commit.

**Rationale**: Each commit should represent a version increment. This provides clear version tracking and prevents confusion with cached installations.

### Reading Version in setup.py

**Rule:** `setup.py` should read the version from `encyclopedia/__init__.py`, not hardcode it.

**✅ CORRECT (following amilib pattern):**
```python
# setup.py
import re
from pathlib import Path

parent = Path(__file__).parent
with open(str(Path(parent, "encyclopedia", "__init__.py"))) as f:
    content = f.read()
version = re.search(r'__version__ = ["\']([^"\']+)["\']', content).group(1)

setup(
    name="encyclopedia",
    version=version,  # Read from __init__.py
    # ...
)
```

**❌ WRONG:**
```python
# setup.py
version = "1.0.0"  # Hardcoded - violates single source of truth
```

**Rationale**: Reading from `__init__.py` ensures consistency and maintains a single source of truth.

### Commits Must Include Version Number

**Rule:** All commits should reference the version number in the commit message.

**✅ CORRECT:**
```bash
git commit -m "Add HTML to Knowledge Graph workflow documentation (v0.0.2)

- Created comprehensive workflow documentation
- Added Graphviz diagrams with hyperlinks
- Version: 0.0.2"
```

**✅ CORRECT (shorter):**
```bash
git commit -m "Fix path construction in versioned_editor (v0.0.3)"
```

**❌ WRONG:**
```bash
git commit -m "Add HTML to Knowledge Graph workflow documentation"
# Missing version number
```

**Rationale**: Including version numbers in commit messages makes it easy to track which version introduced which changes and helps with release management.

### --version Flag

**Rule:** All CLI commands must support a `--version` flag that displays the current version.

**✅ CORRECT:**
```python
# In CLI argument parser
parser.add_argument('--version', action='version', 
                   version=f'%(prog)s {__version__}',
                   help='Show version number and exit')
```

**Usage:**
```bash
python -m encyclopedia.cli.versioned_editor --version
# Output: encyclopedia.cli.versioned_editor 0.0.1

encyclopedia --version
# Output: encyclopedia 0.0.1
```

**Rationale**: The `--version` flag allows users and scripts to check the installed version, which is essential for debugging and compatibility checking.

### Version Update Process

**Rule:** Follow this process when making changes:

1. **Before making changes**: Note current version from `encyclopedia/__init__.py`
2. **Make code changes**: Implement the approved modifications
3. **Increment point version**: Update `__version__` in `encyclopedia/__init__.py` (e.g., `0.0.1` → `0.0.2`)
4. **Commit with version**: Include version number in commit message
5. **Verify**: Ensure `setup.py` reads version correctly (if using pattern from amilib)
6. **Test --version flag**: Verify `--version` flag displays correct version

**Example:**
```python
# Before: encyclopedia/__init__.py
__version__ = "0.0.1"  # 2026-01-23

# After changes: encyclopedia/__init__.py
__version__ = "0.0.2"  # 2026-01-23
```

```bash
# Commit with version number
git commit -m "Add style guide version management rules (v0.0.2)"

# Verify version flag works
python -m encyclopedia.cli.versioned_editor --version
# Should output: encyclopedia.cli.versioned_editor 0.0.2
```

**Manual Increment Process:**
1. Open `encyclopedia/__init__.py`
2. Find `__version__ = "X.Y.Z"`
3. Increment the point version: `Z` → `Z+1`
4. Save the file
5. Commit with version number in message

**Note:** Currently, version incrementing is **manual**. Future enhancements could include:
- Pre-commit hook to auto-increment
- Script to bump version
- CI/CD integration for version management

---

## Version History

- **January 23, 2026**: Created comprehensive style guide incorporating amilib and pygetpapers rules with encyclopedia-specific additions
- **January 23, 2026**: Added version management rules following amilib pattern

---

*This style guide will be updated as new conventions are established and patterns evolve.*
