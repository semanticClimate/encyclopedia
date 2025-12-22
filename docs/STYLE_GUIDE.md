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

## Testing

- **No sys.path manipulation**: Tests should rely on pytest configuration
- **Normal imports**: Use standard Python imports, not path manipulation
- **TDD approach**: Write tests before implementation

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

