# Test Commands List - HTML Description and Image Validation

**Date:** January 21, 2026  
**Purpose:** List of pytest commands to run validation tests from CLI

## Overview

These tests validate that:
1. Descriptions contain HTML markup (not just flat text)
2. Images are present and image URLs exist
3. Image URLs are normalized (spurious 'encyclopedia' prefix removed)

## Test File

**File:** `test/encyclopedia/test_html_description_and_image_validation.py`

## Test Commands

### Run All HTML Description and Image Validation Tests

```bash
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py -v
```

### Run Specific Test Classes

#### HTML Description Validation Tests

```bash
# Run all HTML description validation tests
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestHTMLDescriptionValidation -v

# Run specific test: Description with HTML markup passes
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestHTMLDescriptionValidation::test_description_with_html_markup_passes -v

# Run specific test: Description without HTML markup fails
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestHTMLDescriptionValidation::test_description_without_html_markup_fails -v

# Run specific test: Description with hyperlinks detected
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestHTMLDescriptionValidation::test_description_with_hyperlinks_detected -v

# Run specific test: Empty description fails
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestHTMLDescriptionValidation::test_empty_description_fails -v

# Run specific test: Full pipeline validates HTML descriptions
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestHTMLDescriptionValidation::test_full_pipeline_validates_html_descriptions -v -s
```

#### Image Validation Tests

```bash
# Run all image validation tests
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestImageValidation -v

# Run specific test: Image URL normalization removes encyclopedia prefix
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestImageValidation::test_image_url_normalization_removes_encyclopedia_prefix -v

# Run specific test: Entry with figure_html passes
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestImageValidation::test_entry_with_figure_html_passes -v

# Run specific test: Entry with image_link passes
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestImageValidation::test_entry_with_image_link_passes -v

# Run specific test: Entry without image fails
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestImageValidation::test_entry_without_image_fails -v

# Run specific test: Image URL with encyclopedia prefix normalized
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestImageValidation::test_image_url_with_encyclopedia_prefix_normalized -v

# Run specific test: Full pipeline validates images
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestImageValidation::test_full_pipeline_validates_images -v -s
```

#### Comprehensive Validation Tests

```bash
# Run all comprehensive validation tests
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestComprehensiveValidation -v

# Run specific test: Comprehensive validation includes HTML check
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestComprehensiveValidation::test_comprehensive_validation_includes_html_check -v

# Run specific test: Comprehensive validation includes image check
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestComprehensiveValidation::test_comprehensive_validation_includes_image_check -v

# Run specific test: Validation from real file
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py::TestComprehensiveValidation::test_validation_from_real_file -v -s
```

## Quick Test Commands

### Run All Tests with Output

```bash
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py -v -s
```

### Run Tests with Coverage

```bash
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py --cov=encyclopedia.utils.validation --cov-report=term-missing
```

### Run Tests and Stop on First Failure

```bash
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py -v -x
```

### Run Tests with Detailed Output

```bash
python -m pytest test/encyclopedia/test_html_description_and_image_validation.py -v -s --tb=long
```

## Test Summary

### Test Classes

1. **TestHTMLDescriptionValidation** (5 tests)
   - Validates HTML markup in descriptions
   - Checks for hyperlinks
   - Tests plain text detection

2. **TestImageValidation** (6 tests)
   - Validates image presence
   - Tests URL normalization
   - Checks for spurious 'encyclopedia' prefix

3. **TestComprehensiveValidation** (3 tests)
   - Tests comprehensive validation
   - Validates real file scenarios

### Total Tests: 14

## Notes

- Tests use **real implementations** (no mocks) per style guide
- Tests output to `temp/` directory using `Resources.TEMP_DIR`
- Some tests may fail if descriptions/images aren't being added correctly (this reveals bugs)
- Use `-s` flag to see print statements and diagnostic output
- Use `-v` flag for verbose output showing test names

## Related Tests

- `test/encyclopedia/test_missing_descriptions_and_images_diagnostic.py` - Diagnostic tests for missing descriptions/images
- `test/encyclopedia/test_batch_size_and_features.py` - Batch size and feature tests
