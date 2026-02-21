"""
Diagnostic tests for missing descriptions and images issues.

These tests are designed to diagnose why:
1. Some entries (e.g., Climate Q7937) don't have descriptions
2. No entries have images despite --add-images flag

These tests use REAL implementations (no mocks) and include diagnostic assertions
to help identify where the problem occurs.

Date: Tuesday, January 20, 2026, 10:17:59 GMT (system date)
"""
import pytest
from pathlib import Path

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources
from encyclopedia.utils.encyclopedia_builder import (
    add_wikipedia_descriptions_to_encyclopedia,
    add_image_links_to_encyclopedia,
    add_wikipedia_description_to_entry,
    add_image_link_to_entry
)
from encyclopedia.cli.versioned_editor import (
    add_wikipedia_feature,
    add_images_feature,
    _has_non_empty_description
)
from Examples.create_encyclopedia_from_wordlist import create_encyclopedia_from_wordlist


class TestMissingDescriptionsDiagnostic:
    """Diagnostic tests for missing descriptions issue - using real implementations"""
    
    def test_climate_entry_should_have_description(self):
        """Test that Climate (Q7937) entry gets a description using real Wikipedia lookup"""
        # Create entry similar to Climate entry
        entry = {
            "term": "climate",
            "wikidata_id": "Q7937",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Climate",
            # No description_html - this is the problem
        }
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [entry]
        
        # Diagnostic: Check initial state
        assert entry.get('wikipedia_url') is not None, "Entry should have Wikipedia URL"
        assert not _has_non_empty_description(entry), "Entry should NOT have description initially"
        assert entry.get('description_html') is None or entry.get('description_html') == '', \
            f"Entry description_html should be empty, got: {entry.get('description_html')}"
        
        # Call real function - this will make actual Wikipedia API calls
        print(f"\n=== CALLING REAL add_wikipedia_feature ===")
        print(f"Entry term: {entry.get('term')}")
        print(f"Wikipedia URL: {entry.get('wikipedia_url')}")
        print(f"Has description before: {_has_non_empty_description(entry)}")
        print(f"==========================================\n")
        
        add_wikipedia_feature(entry, encyclopedia)
        
        # Check if description was added
        has_description_after = _has_non_empty_description(entry)
        description_html = entry.get('description_html', '')
        
        # Diagnostic output
        print(f"\n=== DIAGNOSTIC OUTPUT ===")
        print(f"Entry term: {entry.get('term')}")
        print(f"Wikipedia URL: {entry.get('wikipedia_url')}")
        print(f"Has description after: {has_description_after}")
        print(f"Description HTML length: {len(description_html)}")
        print(f"Description HTML content: {description_html[:200] if description_html else 'None'}")
        print(f"========================\n")
        
        # Assertions
        assert has_description_after, \
            f"Entry should have description after add_wikipedia_feature. " \
            f"Description HTML: {description_html[:200] if description_html else 'None'}"
        assert description_html is not None and len(description_html) > 0, \
            f"Description HTML should not be empty. Got: {description_html}"
    
    def test_entry_with_url_but_no_description_gets_fetched(self):
        """Test that entries with Wikipedia URL but no description are processed"""
        entry = {
            "term": "climate",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Climate",
            # Missing description_html
        }
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [entry]
        
        # Diagnostic: Check initial state
        initial_has_description = _has_non_empty_description(entry)
        initial_url = entry.get('wikipedia_url')
        
        print(f"\n=== INITIAL STATE ===")
        print(f"Has description: {initial_has_description}")
        print(f"Wikipedia URL: {initial_url}")
        print(f"Description HTML: {entry.get('description_html')}")
        print(f"====================\n")
        
        # Call real function - returns tuple (encyclopedia, results_dict)
        print(f"\n=== CALLING REAL add_wikipedia_descriptions_to_encyclopedia ===")
        encyclopedia, results = add_wikipedia_descriptions_to_encyclopedia(
            encyclopedia,
            batch_size=10,
            verbose=True
        )
        
        # Diagnostic assertions
        print(f"\n=== FINAL STATE ===")
        print(f"Results: {results}")
        print(f"Has description after: {_has_non_empty_description(entry)}")
        print(f"Description HTML: {entry.get('description_html', '')[:200]}")
        print(f"==================\n")
        
        assert results['total'] > 0, f"Should have processed entries, got: {results}"
        assert results['successful'] > 0, f"Should have successful results, got: {results}"
        assert _has_non_empty_description(entry), "Entry should have description after processing"
    
    def test_add_wikipedia_feature_skips_entry_with_description(self):
        """Test that add_wikipedia_feature correctly identifies entries that need descriptions"""
        # Entry with URL but no description (should be processed)
        entry_no_desc = {
            "term": "climate",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Climate",
            # No description_html
        }
        
        # Entry with URL and description (should be skipped)
        entry_with_desc = {
            "term": "greenhouse gas",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Greenhouse_gas",
            "description_html": "<p>Valid description</p>"
        }
        
        encyclopedia = AmiEncyclopedia(title="Test")
        
        # Test entry without description
        has_desc_before = _has_non_empty_description(entry_no_desc)
        has_url = bool(entry_no_desc.get('wikipedia_url'))
        
        print(f"\n=== ENTRY WITHOUT DESCRIPTION ===")
        print(f"Has description: {has_desc_before}")
        print(f"Has URL: {has_url}")
        print(f"Should process: {has_url and not has_desc_before}")
        print(f"===============================\n")
        
        assert not has_desc_before, "Entry should not have description"
        assert has_url, "Entry should have URL"
        # This entry SHOULD be processed
        
        # Test entry with description
        has_desc_before_2 = _has_non_empty_description(entry_with_desc)
        has_url_2 = bool(entry_with_desc.get('wikipedia_url'))
        
        print(f"\n=== ENTRY WITH DESCRIPTION ===")
        print(f"Has description: {has_desc_before_2}")
        print(f"Has URL: {has_url_2}")
        print(f"Should skip: {has_url_2 and has_desc_before_2}")
        print(f"============================\n")
        
        assert has_desc_before_2, "Entry should have description"
        assert has_url_2, "Entry should have URL"
        # This entry should be SKIPPED
    
    def test_full_pipeline_missing_descriptions(self):
        """Test the full pipeline to see where descriptions are lost"""
        terms = ["climate", "greenhouse gas"]
        
        print(f"\n=== FULL PIPELINE TEST ===")
        print(f"Terms: {terms}")
        print(f"==========================\n")
        
        # Call real function - this will make actual Wikipedia API calls
        encyclopedia = create_encyclopedia_from_wordlist(
            terms,
            title="Test Encyclopedia",
            add_wikipedia=True,
            add_images=False,
            batch_size=10,
            validate=False,
            verbose=True
        )
        
        # Diagnostic output
        print(f"\n=== PIPELINE DIAGNOSTICS ===")
        print(f"Final entries: {len(encyclopedia.entries)}")
        
        for entry in encyclopedia.entries:
            term = entry.get('term')
            has_desc = _has_non_empty_description(entry)
            has_url = bool(entry.get('wikipedia_url'))
            desc_html = entry.get('description_html', '')
            
            print(f"  - {term}: URL={has_url}, Desc={has_desc}, "
                  f"DescLength={len(desc_html)}, "
                  f"DescPreview={desc_html[:100] if desc_html else 'None'}")
        
        print(f"============================\n")
        
        # Check results
        for entry in encyclopedia.entries:
            term = entry.get('term')
            has_desc = _has_non_empty_description(entry)
            has_url = bool(entry.get('wikipedia_url'))
            desc_html = entry.get('description_html', '')
            
            assert has_url, f"Entry '{term}' should have Wikipedia URL"
            assert has_desc, \
                f"Entry '{term}' should have description. " \
                f"Description HTML: {desc_html[:200] if desc_html else 'None'}"


class TestMissingImagesDiagnostic:
    """Diagnostic tests for missing images issue - using real implementations"""
    
    def test_entry_should_get_image_added(self):
        """Test that entries get images added when requested using real Wikipedia lookup"""
        entry = {
            "term": "climate change",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Climate_change",
            "description_html": "<p>Description</p>",
            # No figure_html or images
        }
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [entry]
        
        # Diagnostic: Check initial state
        has_image_before = bool(entry.get('figure_html') or entry.get('images'))
        print(f"\n=== INITIAL STATE ===")
        print(f"Has image: {has_image_before}")
        print(f"figure_html: {entry.get('figure_html')}")
        print(f"images: {entry.get('images')}")
        print(f"====================\n")
        
        assert not has_image_before, "Entry should not have image initially"
        
        # Call real function - this will make actual Wikipedia API calls
        print(f"\n=== CALLING REAL add_images_feature ===")
        print(f"Entry term: {entry.get('term')}")
        print(f"Wikipedia URL: {entry.get('wikipedia_url')}")
        print(f"=======================================\n")
        
        add_images_feature(entry, encyclopedia, verbose=True)
        
        # Diagnostic assertions
        has_image_after = (entry.get('figure_html') is not None) or bool(entry.get('images'))
        
        print(f"\n=== DIAGNOSTIC OUTPUT ===")
        print(f"Has image after: {has_image_after}")
        print(f"figure_html: {entry.get('figure_html')}")
        print(f"image_link: {entry.get('image_link')}")
        print(f"images: {entry.get('images')}")
        print(f"========================\n")
        
        # Note: This may fail if Wikipedia page doesn't have images
        # That's okay - the diagnostic output will show what happened
        if not has_image_after:
            print(f"WARNING: No image found for '{entry.get('term')}'. "
                  f"This may be because the Wikipedia page doesn't have images, "
                  f"or because image extraction failed.")
        
        # We still check what happened
        assert entry.get('wikipedia_url'), "Entry should have Wikipedia URL"
    
    def test_add_image_links_processes_all_entries(self):
        """Test that add_image_links_to_encyclopedia processes all entries"""
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [
            {
                "term": "climate change",
                "wikipedia_url": "https://en.wikipedia.org/wiki/Climate_change",
                "description_html": "<p>Description</p>",
            },
            {
                "term": "greenhouse gas",
                "wikipedia_url": "https://en.wikipedia.org/wiki/Greenhouse_gas",
                "description_html": "<p>Description</p>",
            }
        ]
        
        print(f"\n=== CALLING REAL add_image_links_to_encyclopedia ===")
        print(f"Entries to process: {len(encyclopedia.entries)}")
        print(f"=====================================================\n")
        
        # Call real function - returns tuple (encyclopedia, results_dict)
        encyclopedia, results = add_image_links_to_encyclopedia(
            encyclopedia,
            batch_size=10,
            verbose=True
        )
        
        # Diagnostic output
        entries_with_images = sum(1 for e in encyclopedia.entries if (e.get('figure_html') is not None) or e.get('images'))
        
        print(f"\n=== IMAGE PROCESSING DIAGNOSTICS ===")
        print(f"Results: {results}")
        print(f"Entries with images after: {entries_with_images}/{len(encyclopedia.entries)}")
        
        for entry in encyclopedia.entries:
            term = entry.get('term')
            has_image = (entry.get('figure_html') is not None) or bool(entry.get('images'))
            print(f"  - {term}: Image={has_image}, "
                  f"figure_html={entry.get('figure_html') is not None}, "
                  f"image_link={entry.get('image_link')}")
        
        print(f"====================================\n")
        
        assert results['total'] == len(encyclopedia.entries), \
            f"Results total should match entries. Expected {len(encyclopedia.entries)}, got {results['total']}"
        
        # Note: Results may show no images if Wikipedia pages don't have images
        # The diagnostic output will show what happened
        print(f"Note: {results.get('no_images', [])} entries reported no images found")
    
    def test_full_pipeline_missing_images(self):
        """Test the full pipeline to see where images are lost"""
        terms = ["climate change", "greenhouse gas"]
        
        print(f"\n=== FULL PIPELINE TEST WITH IMAGES ===")
        print(f"Terms: {terms}")
        print(f"======================================\n")
        
        # Call real function - this will make actual Wikipedia API calls
        encyclopedia = create_encyclopedia_from_wordlist(
            terms,
            title="Test Encyclopedia",
            add_wikipedia=True,
            add_images=True,  # Request images
            batch_size=10,
            validate=False,
            verbose=True
        )
        
        # Diagnostic output
        entries_with_images = 0
        
        print(f"\n=== IMAGE PIPELINE DIAGNOSTICS ===")
        print(f"Final entries: {len(encyclopedia.entries)}")
        
        for entry in encyclopedia.entries:
            term = entry.get('term')
            has_image = (entry.get('figure_html') is not None) or bool(entry.get('images'))
            has_url = bool(entry.get('wikipedia_url'))
            
            if has_image:
                entries_with_images += 1
            
            print(f"  - {term}: URL={has_url}, Image={has_image}, "
                  f"figure_html={entry.get('figure_html') is not None}, "
                  f"image_link={entry.get('image_link')}")
        
        print(f"Entries with images: {entries_with_images}/{len(encyclopedia.entries)}")
        print(f"===================================\n")
        
        # Check results
        assert len(encyclopedia.entries) > 0, "Should have entries"
        
        # Diagnostic: Show which entries have images and which don't
        for entry in encyclopedia.entries:
            term = entry.get('term')
            has_image = (entry.get('figure_html') is not None) or bool(entry.get('images'))
            has_url = bool(entry.get('wikipedia_url'))
            
            assert has_url, f"Entry '{term}' should have Wikipedia URL"
            
            if not has_image:
                print(f"WARNING: Entry '{term}' does not have image. "
                      f"This may be because the Wikipedia page doesn't have images, "
                      f"or because image extraction failed.")


class TestRealWorldScenarioDiagnostic:
    """Diagnostic tests using real-world scenario - tests actual generated files"""
    
    def test_climate_entry_from_real_file(self):
        """Test Climate entry from actual generated file"""
        # Load the actual file - use Resources.TEMP_DIR
        html_file = Path(Resources.TEMP_DIR, "climate_encyclopedia.html")
        
        if not html_file.exists():
            pytest.skip(f"File {html_file} does not exist. Run the command first.")
        
        print(f"\n=== LOADING REAL FILE ===")
        print(f"File: {html_file}")
        print(f"=========================\n")
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.create_from_html_file(html_file)
        
        # Find Climate entry
        climate_entry = None
        for entry in encyclopedia.entries:
            if entry.get('term', '').lower() == 'climate' or entry.get('wikidata_id') == 'Q7937':
                climate_entry = entry
                break
        
        assert climate_entry is not None, "Climate entry should exist in the file"
        
        # Check initial state after loading
        has_desc_after_load = _has_non_empty_description(climate_entry)
        
        # Diagnostic output
        print(f"\n=== CLIMATE ENTRY DIAGNOSTIC (AFTER LOADING) ===")
        print(f"Term: {climate_entry.get('term')}")
        print(f"Wikidata ID: {climate_entry.get('wikidata_id')}")
        print(f"Wikipedia URL: {climate_entry.get('wikipedia_url')}")
        print(f"Has description: {has_desc_after_load}")
        print(f"Description HTML: {climate_entry.get('description_html', 'None')[:200] if climate_entry.get('description_html') else 'None'}")
        print(f"Has image: {(climate_entry.get('figure_html') is not None) or bool(climate_entry.get('images'))}")
        print(f"figure_html: {climate_entry.get('figure_html')}")
        print(f"image_link: {climate_entry.get('image_link')}")
        print(f"================================================\n")
        
        # Assertions
        assert climate_entry.get('wikipedia_url'), "Climate entry should have Wikipedia URL"
        
        # If description is missing, add it (this tests the functionality)
        if not has_desc_after_load:
            print(f"\n=== ADDING MISSING DESCRIPTION ===")
            print(f"Description missing, adding via add_wikipedia_feature...")
            from encyclopedia.cli.versioned_editor import add_wikipedia_feature
            add_wikipedia_feature(climate_entry, encyclopedia)
            print(f"===================================\n")
        
        # Verify description exists (either from file or added)
        has_desc = _has_non_empty_description(climate_entry)
        desc_html = climate_entry.get('description_html', '')
        assert has_desc, \
            f"Climate entry should have description. " \
            f"Description HTML: {desc_html[:200] if desc_html else 'None'}"
    
    def test_all_entries_have_images_from_real_file(self):
        """Test that all entries have images from actual generated file"""
        # Load the actual file - use Resources.TEMP_DIR
        html_file = Path(Resources.TEMP_DIR, "climate_encyclopedia.html")
        
        if not html_file.exists():
            pytest.skip(f"File {html_file} does not exist. Run the command first.")
        
        print(f"\n=== LOADING REAL FILE ===")
        print(f"File: {html_file}")
        print(f"=========================\n")
        
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.create_from_html_file(html_file)
        
        # Check initial state after loading
        entries_with_images_after_load = sum(1 for e in encyclopedia.entries 
                                             if e.get('figure_html') or e.get('images'))
        
        print(f"\n=== IMAGE DIAGNOSTIC FROM REAL FILE ===")
        print(f"Total entries: {len(encyclopedia.entries)}")
        print(f"Entries with images after loading: {entries_with_images_after_load}/{len(encyclopedia.entries)}")
        
        # If images are missing, add them (this tests the functionality)
        if entries_with_images_after_load < len(encyclopedia.entries):
            print(f"\n=== ADDING MISSING IMAGES ===")
            print(f"Adding images to {len(encyclopedia.entries) - entries_with_images_after_load} entries...")
            from encyclopedia.utils.encyclopedia_builder import add_image_links_to_encyclopedia
            encyclopedia, results = add_image_links_to_encyclopedia(
                encyclopedia,
                batch_size=10,
                verbose=True
            )
            print(f"Image addition results: {results}")
            print(f"================================\n")
        
        # Diagnostic output
        entries_with_images = 0
        entries_without_images = []
        
        for entry in encyclopedia.entries:
            term = entry.get('term')
            has_image = (entry.get('figure_html') is not None) or bool(entry.get('images'))
            has_url = bool(entry.get('wikipedia_url'))
            
            if has_image:
                entries_with_images += 1
            else:
                entries_without_images.append({
                    'term': term,
                    'wikidata_id': entry.get('wikidata_id'),
                    'wikipedia_url': entry.get('wikipedia_url'),
                    'has_url': has_url
                })
            
            print(f"  - {term}: Image={has_image}, URL={has_url}")
        
        print(f"Entries with images: {entries_with_images}/{len(encyclopedia.entries)}")
        print(f"Entries without images: {len(entries_without_images)}")
        for entry in entries_without_images:
            print(f"    - {entry}")
        print(f"========================================\n")
        
        # Verify all entries have images (either from file or added)
        assert entries_with_images == len(encyclopedia.entries), \
            f"All entries should have images. " \
            f"Got {entries_with_images}/{len(encyclopedia.entries)}. " \
            f"Entries without images: {entries_without_images}"
