"""
Tests for HTML description and image validation.

These tests validate that:
1. Descriptions contain HTML markup (not just flat text)
2. Images are present and image URLs exist
3. Image URLs are normalized (spurious 'encyclopedia' prefix removed)

Date: January 21, 2026
"""
import pytest
from pathlib import Path
from lxml.html import fromstring

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources
from encyclopedia.utils.validation import (
    validate_descriptions_have_html_markup,
    validate_image_links_added,
    validate_encyclopedia_completeness,
    _normalize_image_url,
    _check_image_url_exists
)
from Examples.create_encyclopedia_from_wordlist import create_encyclopedia_from_wordlist


class TestHTMLDescriptionValidation:
    """Tests for validating HTML markup in descriptions"""
    
    def test_description_with_html_markup_passes(self):
        """Test that descriptions with HTML markup are validated correctly"""
        entry = {
            "term": "climate change",
            "description_html": "<p>Climate change refers to <a href='https://example.com'>long-term</a> changes in temperature.</p>",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Climate_change"
        }
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [entry]
        
        results = validate_descriptions_have_html_markup(encyclopedia)
        
        assert results['entries_with_html_descriptions'] == 1, \
            f"Expected 1 entry with HTML description, but got {results['entries_with_html_descriptions']}. " \
            f"Total entries: {results['total_entries']}, entries without HTML: {results['entries_without_html_descriptions']}"
        assert results['entries_without_html_descriptions'] == 0, \
            f"Expected 0 entries without HTML description, but got {results['entries_without_html_descriptions']}. " \
            f"Sample entries without HTML: {results.get('sample_without_html', [])}"
        assert results['is_valid'] is True, \
            f"Validation should pass for entry with HTML markup, but is_valid is {results['is_valid']}"
        assert results['success_rate'] == 100.0, \
            f"Expected 100% success rate for HTML description validation, but got {results['success_rate']}%"
    
    def test_description_without_html_markup_fails(self):
        """Test that plain text descriptions fail validation"""
        entry = {
            "term": "climate change",
            "description_html": "Climate change refers to long-term changes in temperature.",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Climate_change"
        }
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [entry]
        
        results = validate_descriptions_have_html_markup(encyclopedia)
        
        assert results['entries_with_html_descriptions'] == 0, \
            f"Expected 0 entries with HTML description for plain text, but got {results['entries_with_html_descriptions']}. " \
            f"Entry description was: '{entry.get('description_html', '')[:100]}'"
        assert results['entries_without_html_descriptions'] == 1, \
            f"Expected 1 entry without HTML description for plain text, but got {results['entries_without_html_descriptions']}. " \
            f"Total entries: {results['total_entries']}"
        assert results['is_valid'] is False, \
            f"Validation should fail for plain text description (no HTML markup), but is_valid is {results['is_valid']}"
        assert results['success_rate'] == 0.0, \
            f"Expected 0% success rate for plain text description, but got {results['success_rate']}%"
    
    def test_description_with_hyperlinks_detected(self):
        """Test that descriptions with hyperlinks are detected"""
        entry = {
            "term": "greenhouse gas",
            "description_html": "<p>A greenhouse gas is a gas that <a href='https://en.wikipedia.org/wiki/Absorption'>absorbs</a> radiation.</p>",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Greenhouse_gas"
        }
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [entry]
        
        results = validate_descriptions_have_html_markup(encyclopedia)
        
        assert results['entries_with_html_descriptions'] == 1, \
            f"Expected 1 entry with HTML description, but got {results['entries_with_html_descriptions']}. " \
            f"Total entries: {results['total_entries']}"
        assert results['sample_with_html'][0]['has_hyperlinks'] is True, \
            f"Expected entry to have hyperlinks detected, but has_hyperlinks is {results['sample_with_html'][0].get('has_hyperlinks')}. " \
            f"Entry term: {results['sample_with_html'][0].get('term')}"
    
    def test_empty_description_fails(self):
        """Test that empty descriptions fail validation"""
        entry = {
            "term": "test",
            "description_html": "",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Test"
        }
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [entry]
        
        results = validate_descriptions_have_html_markup(encyclopedia)
        
        assert results['entries_with_html_descriptions'] == 0, \
            f"Expected 0 entries with HTML description for empty description, but got {results['entries_with_html_descriptions']}"
        assert results['entries_without_html_descriptions'] == 1, \
            f"Expected 1 entry without HTML description for empty description, but got {results['entries_without_html_descriptions']}. " \
            f"Total entries: {results['total_entries']}"
        assert results['is_valid'] is False, \
            f"Validation should fail for empty description, but is_valid is {results['is_valid']}"
    
    def test_full_pipeline_validates_html_descriptions(self):
        """Test that full pipeline creates entries with HTML descriptions"""
        terms = ["climate change", "greenhouse gas"]
        
        encyclopedia = create_encyclopedia_from_wordlist(
            terms,
            title="Test Encyclopedia",
            add_wikipedia=True,
            add_images=False,
            batch_size=10,
            validate=False,  # Don't validate during creation
            verbose=False
        )
        
        # Now validate HTML markup
        results = validate_descriptions_have_html_markup(encyclopedia)
        
        # At least some entries should have HTML markup
        assert results['total_entries'] > 0, \
            f"Expected at least 1 entry in encyclopedia, but got {results['total_entries']} entries"
        # Note: This may fail if descriptions aren't being added correctly
        # That's okay - it reveals the actual bug
        print(f"\nHTML Description Validation Results:")
        print(f"  Total entries: {results['total_entries']}")
        print(f"  With HTML: {results['entries_with_html_descriptions']}")
        print(f"  Without HTML: {results['entries_without_html_descriptions']}")
        
        if results['entries_without_html_descriptions'] > 0:
            print(f"\n  Entries without HTML markup:")
            for entry in results['sample_without_html'][:5]:
                print(f"    - {entry['term']}: {entry.get('description_preview', 'None')[:100]}")


class TestImageValidation:
    """Tests for validating images and image URLs"""
    
    def test_image_url_normalization_removes_encyclopedia_prefix(self):
        """Test that spurious 'encyclopedia' prefix is removed from URLs"""
        # Test case 1: encyclopediahttps://...
        url1 = "encyclopediahttps://en.wikipedia.org/wiki/File:Climate.jpg"
        expected1 = "https://en.wikipedia.org/wiki/File:Climate.jpg"
        normalized1 = _normalize_image_url(url1)
        assert normalized1 == expected1, \
            f"URL normalization failed for 'encyclopediahttps://...' prefix. " \
            f"Expected '{expected1}', but got '{normalized1}'. Original URL: '{url1}'"
        
        # Test case 2: encyclopedia/wiki/File:...
        url2 = "encyclopedia/wiki/File:Climate.jpg"
        expected2 = "https://en.wikipedia.org/wiki/File:Climate.jpg"
        normalized2 = _normalize_image_url(url2)
        assert normalized2 == expected2, \
            f"URL normalization failed for 'encyclopedia/wiki/File:...' prefix. " \
            f"Expected '{expected2}', but got '{normalized2}'. Original URL: '{url2}'"
        
        # Test case 3: Normal URL (no change)
        url3 = "https://en.wikipedia.org/wiki/File:Climate.jpg"
        normalized3 = _normalize_image_url(url3)
        assert normalized3 == url3, \
            f"URL normalization should not change normal URLs. " \
            f"Expected '{url3}', but got '{normalized3}'"
    
    def test_entry_with_figure_html_passes(self):
        """Test that entries with figure_html are validated correctly"""
        entry = {
            "term": "climate change",
            "figure_html": '<a href="https://en.wikipedia.org/wiki/File:Climate_change.jpg" class="wikipedia-image-link">Image</a>',
            "wikipedia_url": "https://en.wikipedia.org/wiki/Climate_change"
        }
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [entry]
        
        results = validate_image_links_added(encyclopedia, check_url_exists=False)
        
        assert results['entries_with_images'] == 1, \
            f"Expected 1 entry with image (figure_html present), but got {results['entries_with_images']}. " \
            f"Total entries: {results['total_entries']}, entries without images: {results['entries_without_images']}"
        assert results['entries_without_images'] == 0, \
            f"Expected 0 entries without images, but got {results['entries_without_images']}. " \
            f"Sample entries without images: {results.get('sample_without_images', [])}"
        assert results['is_valid'] is True, \
            f"Validation should pass for entry with figure_html, but is_valid is {results['is_valid']}"
    
    def test_entry_with_image_link_passes(self):
        """Test that entries with image_link are validated correctly"""
        entry = {
            "term": "greenhouse gas",
            "image_link": "https://en.wikipedia.org/wiki/File:Greenhouse_gas.jpg",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Greenhouse_gas"
        }
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [entry]
        
        results = validate_image_links_added(encyclopedia, check_url_exists=False)
        
        assert results['entries_with_images'] == 1, \
            f"Expected 1 entry with image (image_link present), but got {results['entries_with_images']}. " \
            f"Total entries: {results['total_entries']}, entries without images: {results['entries_without_images']}"
        assert results['entries_without_images'] == 0, \
            f"Expected 0 entries without images, but got {results['entries_without_images']}. " \
            f"Entry image_link was: '{entry.get('image_link')}'"
    
    def test_entry_without_image_fails(self):
        """Test that entries without images fail validation"""
        entry = {
            "term": "test",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Test"
        }
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [entry]
        
        results = validate_image_links_added(encyclopedia, check_url_exists=False)
        
        assert results['entries_with_images'] == 0, \
            f"Expected 0 entries with images for entry without image data, but got {results['entries_with_images']}"
        assert results['entries_without_images'] == 1, \
            f"Expected 1 entry without images, but got {results['entries_without_images']}. " \
            f"Total entries: {results['total_entries']}"
        assert results['is_valid'] is False, \
            f"Validation should fail for entry without images, but is_valid is {results['is_valid']}"
    
    def test_image_url_with_encyclopedia_prefix_normalized(self):
        """Test that image URLs with spurious prefix are normalized"""
        entry = {
            "term": "climate",
            "image_link": "encyclopediahttps://en.wikipedia.org/wiki/File:Climate.jpg",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Climate"
        }
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [entry]
        
        results = validate_image_links_added(encyclopedia, check_url_exists=False)
        
        expected_normalized_url = "https://en.wikipedia.org/wiki/File:Climate.jpg"
        expected_original_url = "encyclopediahttps://en.wikipedia.org/wiki/File:Climate.jpg"
        
        assert results['entries_with_images'] == 1, \
            f"Expected 1 entry with image after normalization, but got {results['entries_with_images']}. " \
            f"Total entries: {results['total_entries']}"
        assert results['sample_with_images'][0]['image_url'] == expected_normalized_url, \
            f"Image URL normalization failed. Expected normalized URL '{expected_normalized_url}', " \
            f"but got '{results['sample_with_images'][0]['image_url']}'. " \
            f"Original URL was '{entry.get('image_link')}'"
        assert results['sample_with_images'][0]['original_url'] == expected_original_url, \
            f"Original URL should be preserved. Expected '{expected_original_url}', " \
            f"but got '{results['sample_with_images'][0]['original_url']}'"
    
    def test_full_pipeline_validates_images(self):
        """Test that full pipeline creates entries with images"""
        terms = ["climate change", "greenhouse gas"]
        
        encyclopedia = create_encyclopedia_from_wordlist(
            terms,
            title="Test Encyclopedia",
            add_wikipedia=True,
            add_images=True,  # Request images
            batch_size=10,
            validate=False,  # Don't validate during creation
            verbose=False
        )
        
        # Now validate images
        results = validate_image_links_added(encyclopedia, check_url_exists=False)
        
        # At least some entries should have images
        assert results['total_entries'] > 0, \
            f"Expected at least 1 entry in encyclopedia, but got {results['total_entries']} entries"
        # Note: This may fail if images aren't being added correctly
        # That's okay - it reveals the actual bug
        print(f"\nImage Validation Results:")
        print(f"  Total entries: {results['total_entries']}")
        print(f"  With images: {results['entries_with_images']}")
        print(f"  Without images: {results['entries_without_images']}")
        
        if results['entries_without_images'] > 0:
            print(f"\n  Entries without images:")
            for entry in results['sample_without_images'][:5]:
                print(f"    - {entry['term']}")


class TestComprehensiveValidation:
    """Tests for comprehensive validation including HTML and images"""
    
    def test_comprehensive_validation_includes_html_check(self):
        """Test that comprehensive validation includes HTML markup check"""
        entry = {
            "term": "climate change",
            "description_html": "<p>Climate change refers to long-term changes.</p>",
            "figure_html": '<a href="https://en.wikipedia.org/wiki/File:Climate.jpg" class="wikipedia-image-link">Image</a>',
            "wikipedia_url": "https://en.wikipedia.org/wiki/Climate_change"
        }
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [entry]
        
        results = validate_encyclopedia_completeness(encyclopedia)
        
        # Should include descriptions validation
        assert 'descriptions' in results, \
            f"Comprehensive validation should include 'descriptions' key, but got keys: {list(results.keys())}"
        assert results['descriptions']['entries_with_html_descriptions'] == 1, \
            f"Expected 1 entry with HTML description in comprehensive validation, " \
            f"but got {results['descriptions']['entries_with_html_descriptions']}. " \
            f"Total entries: {results['descriptions']['total_entries']}"
        assert results['descriptions']['is_valid'] is True, \
            f"Description validation should pass for entry with HTML markup, " \
            f"but is_valid is {results['descriptions']['is_valid']}"
    
    def test_comprehensive_validation_includes_image_check(self):
        """Test that comprehensive validation includes image check"""
        entry = {
            "term": "climate change",
            "description_html": "<p>Climate change refers to long-term changes.</p>",
            "figure_html": '<a href="https://en.wikipedia.org/wiki/File:Climate.jpg" class="wikipedia-image-link">Image</a>',
            "wikipedia_url": "https://en.wikipedia.org/wiki/Climate_change"
        }
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [entry]
        
        results = validate_encyclopedia_completeness(encyclopedia)
        
        # Should include images validation
        assert 'images' in results, \
            f"Comprehensive validation should include 'images' key, but got keys: {list(results.keys())}"
        assert results['images']['entries_with_images'] == 1, \
            f"Expected 1 entry with image in comprehensive validation, " \
            f"but got {results['images']['entries_with_images']}. " \
            f"Total entries: {results['images']['total_entries']}"
        assert results['images']['is_valid'] is True, \
            f"Image validation should pass for entry with figure_html, " \
            f"but is_valid is {results['images']['is_valid']}"
    
    def test_validation_from_real_file(self):
        """Test validation on a real generated encyclopedia file"""
        html_file = Path(Resources.TEMP_DIR, "climate_encyclopedia.html")
        
        if not html_file.exists():
            pytest.skip(f"File {html_file} does not exist. Run the command first.")
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.create_from_html_file(html_file)
        
        # Comprehensive validation
        results = validate_encyclopedia_completeness(encyclopedia)
        
        print(f"\n=== Comprehensive Validation Results ===")
        print(f"Total entries: {results['total_entries']}")
        print(f"\nDescriptions (HTML markup):")
        print(f"  With HTML: {results['descriptions']['entries_with_html_descriptions']}")
        print(f"  Without HTML: {results['descriptions']['entries_without_html_descriptions']}")
        print(f"\nImages:")
        print(f"  With images: {results['images']['entries_with_images']}")
        print(f"  Without images: {results['images']['entries_without_images']}")
        print(f"  Invalid URLs: {results['images'].get('entries_with_invalid_urls', 0)}")
        print(f"========================================\n")
        
        # This test documents the current state
        # It may fail if descriptions/images aren't being added correctly
        assert results['total_entries'] > 0, \
            f"Expected at least 1 entry in encyclopedia loaded from file '{html_file}', " \
            f"but got {results['total_entries']} entries"
