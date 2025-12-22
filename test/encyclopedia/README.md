# Encyclopedia Tests

## Running Tests

Tests can be run directly **without setting PYTHONPATH**. The `pytest.ini` configuration and `conftest.py` files automatically handle the Python path setup.

### Basic Usage
```bash
cd /Users/pm286/workspace/encyclopedia
python -m pytest test/encyclopedia/ -v
```

### Run specific test
```bash
python -m pytest test/encyclopedia/test_encyclopedia.py::TestAmiEncyclopedia::test_encyclopedia_initialization -v
```

### Run all tests
```bash
python -m pytest test/encyclopedia/ -v
```

### Install package in editable mode (optional)
```bash
pip install -e .
python -m pytest test/encyclopedia/ -v
```

## Test Structure

- `test_encyclopedia.py` - Unit tests for AmiEncyclopedia class
- `test_integration.py` - Integration tests for full pipeline

## Known Issues

1. **Sandbox restrictions**: Some tests may fail due to SSL/permission errors when importing `amilib` (this is a sandbox limitation, not a code issue)
2. **Network dependencies**: Tests that require Wikipedia/Wikidata lookups may need mocking or network access
3. **Import path**: Tests add project root to sys.path automatically, but may need PYTHONPATH set in some environments

## Test Coverage

### Unit Tests
- ✅ Encyclopedia initialization
- ✅ Constants validation
- ✅ HTML content creation
- ✅ Normalization by Wikidata ID
- ✅ Synonym merging
- ✅ HTML generation

### Integration Tests
- ✅ Full pipeline: HTML → Encyclopedia → Normalize → Merge → HTML
- ✅ Normalize and merge with same Wikidata ID

