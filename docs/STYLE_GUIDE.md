# Encyclopedia Project Style Guide

This style guide defines coding standards and best practices for the Encyclopedia project.

## Import Style

- **Absolute imports**: Use absolute imports with module prefixes
  ```python
  from encyclopedia.core.encyclopedia import AmiEncyclopedia  # ✅ CORRECT
  from .core.encyclopedia import AmiEncyclopedia  # ❌ WRONG - relative import
  ```

- **NO PYTHONPATH**: Do not use PYTHONPATH environment variable or sys.path manipulation
  - ✅ Tests should work without setting PYTHONPATH
  - ✅ Use pytest.ini `pythonpath = .` configuration instead
  - ✅ Use `--import-mode=importlib` in pytest configuration
  - ❌ Do not manipulate `sys.path` in conftest.py or test files
  - ❌ Do not require PYTHONPATH to be set manually

- **NO ENVIRONMENT VARIABLES**: Do not rely on environment variables for code execution
  - ✅ Code should work without any environment variables set
  - ✅ Use configuration files (pytest.ini, setup.py, etc.) instead
  - ✅ Use command-line arguments or config files for runtime configuration
  - ❌ Do not require environment variables to be set for tests or code to run
  - ❌ Do not use `os.environ` for critical path or configuration
  - ✅ Exception: Environment variables for secrets/API keys are acceptable if clearly documented

## File Naming

- **Alphanumeric characters and underscores only**
- Use lowercase with underscores: `test_encyclopedia.py`, `ami_encyclopedia.py`

## Code Organization

- **Empty `__init__.py` files**: All `__init__.py` files should be empty (except for top-level package exports if needed)
- **Path construction**: Use `Path()` constructor with comma-separated arguments
  ```python
  output_file = Path(self.output_dir, "results.json")  # ✅ CORRECT
  output_file = self.output_dir / "results.json"  # ❌ WRONG - uses / operator
  ```

## Temporary Files

- **All temporary files to temp/**: All temporary files must be created under `<root>/temp`, which is defined in `Resources.TEMP_DIR`
- **Use Resources.TEMP_DIR**: Always use `Resources.TEMP_DIR` for temporary file locations
  ```python
  from pathlib import Path
  from encyclopedia.utils.resources import Resources
  
  # ✅ CORRECT: Use Resources.TEMP_DIR with subdirectories
  temp_dir = Path(Resources.TEMP_DIR, "examples", "create_encyclopedia")
  temp_dir.mkdir(parents=True, exist_ok=True)
  output_file = Path(temp_dir, "output.html")
  
  # ✅ CORRECT: Use Resources.get_temp_dir() helper
  temp_dir = Resources.get_temp_dir("examples", "create_encyclopedia")
  
  # ❌ WRONG: Writing to root directory
  output_file = Path("output.html")
  
  # ❌ WRONG: Using system temp directory
  import tempfile
  temp_dir = Path(tempfile.mkdtemp())
  
  # ❌ WRONG: Using / operator
  temp_dir = Resources.TEMP_DIR / "examples" / "create_encyclopedia"
  ```
- **Subdirectory naming conventions**:
  - Tests: `Path(Resources.TEMP_DIR, "test", <module_name>, <class_name>)`
  - Scripts: `Path(Resources.TEMP_DIR, "scripts", <script_name>)`
  - Examples: `Path(Resources.TEMP_DIR, "examples", <example_name>)`
  - Other modules: `Path(Resources.TEMP_DIR, <module_name>, <class_or_function>)`
- **No root directory output**: Output should never be sent to the root directory. Use `temp/` directory for all non-permanent output

## Testing

- **No sys.path manipulation**: Tests should rely on pytest configuration
- **Normal imports**: Use standard Python imports, not path manipulation
- **TDD approach**: Write tests before implementation
- **No mocks**: Do not use mocks or patches in tests. Tests should use real implementations and real services
- **Test output to temp/**: All tests should output to `temp/` directory. No tests should write to root directory unless specifically requested
- **Meaningful assertion messages**: All assertions should have human-meaningful messages that explain what failed and why
  ```python
  # ✅ CORRECT: Assertion with meaningful message
  assert results['entries_with_html_descriptions'] == 1, \
      f"Expected 1 entry with HTML description, but got {results['entries_with_html_descriptions']}. " \
      f"Entries without HTML: {results['entries_without_html_descriptions']}"
  
  # ❌ WRONG: Assertion without message
  assert results['entries_with_html_descriptions'] == 1
  
  # ✅ CORRECT: Assertion with context about what is being tested
  assert normalized_url == expected_url, \
      f"URL normalization failed. Expected '{expected_url}', but got '{normalized_url}'. " \
      f"Original URL was '{original_url}'"
  
  # ❌ WRONG: Assertion without context
  assert normalized_url == expected_url
  ```
  ```python
  from pathlib import Path
  from encyclopedia.utils.resources import Resources
  
  # ✅ CORRECT: Use Resources.TEMP_DIR with subdirectories
  test_output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestClassName")
  test_output_dir.mkdir(parents=True, exist_ok=True)
  output_file = Path(test_output_dir, "test_output.html")
  
  # ❌ WRONG: Writing to root directory
  output_file = Path("test_output.html")
  
  # ❌ WRONG: Using system temp directory
  import tempfile
  output_file = Path(tempfile.mkdtemp(), "test_output.html")
  
  # ❌ WRONG: Using / operator
  test_output_dir = Resources.TEMP_DIR / "test" / "encyclopedia"
  ```
- **Test subdirectory naming**: Use `Path(Resources.TEMP_DIR, "test", <module_name>, <class_name>)` for test outputs

## Documentation

- **Comprehensive README files**: All components should have README files
- **Docstrings**: All public methods should have docstrings
- **Inline comments**: Complex logic should have explanatory comments

## Constants and Magic Strings

- **No magic strings**: Use class constants instead of hardcoded strings
- **Constants at class level**: Define constants as class attributes

## Best Practices

- **Always propose changes** before implementation
- **Work in small, testable steps**
- **Maintain clean project structure**
- **Follow established naming conventions**
- **Document all decisions and changes**

