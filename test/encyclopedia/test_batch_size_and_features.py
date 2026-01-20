"""
Tests for batch-size functionality, missing descriptions, and missing images.

Tests verify:
1. Batch-size is respected when processing entries
2. Missing descriptions are properly fetched
3. Missing images are properly added
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.encyclopedia_builder import (
    add_wikipedia_descriptions_to_encyclopedia,
    add_image_links_to_encyclopedia
)
from encyclopedia.cli.versioned_editor import (
    add_wikipedia_feature,
    add_images_feature,
    _has_non_empty_description
)


class TestBatchSize:
    """Test batch-size functionality"""
    
    def test_batch_size_respected_for_wikipedia_descriptions(self):
        """Test that batch_size parameter controls how many entries are processed at once"""
        # Create encyclopedia with multiple entries
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [
            {"term": f"term_{i}", "wikipedia_url": f"https://en.wikipedia.org/wiki/Term_{i}"}
            for i in range(10)
        ]
        
        batch_size = 3
        call_times = []
        
        def mock_add_description(entry, enc, verbose=False):
            """Track when entries are processed"""
            call_times.append(time.time())
            # Don't call time.sleep here - it will be counted by the mock
            # Just simulate processing without actual sleep
            entry['description_html'] = f"<p>Description for {entry['term']}</p>"
            return {
                'success': True,
                'has_description': True,
                'has_definition': False,
                'wikipedia_url': entry.get('wikipedia_url'),
                'error': None
            }
        
        # Mock the add_wikipedia_description_to_entry function
        with patch('encyclopedia.utils.encyclopedia_builder.add_wikipedia_description_to_entry', 
                   side_effect=mock_add_description):
            with patch('time.sleep') as mock_sleep:
                encyclopedia, results = add_wikipedia_descriptions_to_encyclopedia(
                    encyclopedia, 
                    batch_size=batch_size, 
                    verbose=False
                )
                
                # Verify batch_size was respected
                # Should have processed all 10 entries
                assert results['total'] == 10
                assert results['successful'] == 10
                
                # Verify delays were added between batches (not within batches)
                # With batch_size=3 and 10 entries, we have 4 batches (3, 3, 3, 1)
                # So 3 delays between batches (after batches 1, 2, and 3, but not after batch 4)
                assert mock_sleep.call_count == 3  # 3 delays between 4 batches
    
    def test_batch_size_respected_for_images(self):
        """Test that batch_size parameter controls image processing"""
        # Create encyclopedia with multiple entries
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [
            {
                "term": f"term_{i}", 
                "wikipedia_url": f"https://en.wikipedia.org/wiki/Term_{i}",
                "description_html": f"<p>Description {i}</p>"
            }
            for i in range(8)
        ]
        
        batch_size = 2
        
        def mock_add_image(entry, enc, verbose=False):
            """Mock image addition"""
            entry['figure_html'] = Mock()
            entry['image_link'] = f"https://en.wikipedia.org/wiki/File:Image_{entry['term']}.jpg"
            return {
                'success': True,
                'has_image_link': True,
                'image_url': entry['image_link'],
                'error': None
            }
        
        with patch('encyclopedia.utils.encyclopedia_builder.add_image_link_to_entry',
                   side_effect=mock_add_image):
            with patch('time.sleep') as mock_sleep:
                encyclopedia, results = add_image_links_to_encyclopedia(
                    encyclopedia,
                    batch_size=batch_size,
                    verbose=False
                )
                
                # Verify all entries were processed
                assert results['total'] == 8
                assert results['successful'] == 8
                
                # With batch_size=2, we should have 4 batches (2, 2, 2, 2)
                # So 3 delays between batches
                assert mock_sleep.call_count == 3


class TestMissingDescriptions:
    """Test handling of missing descriptions"""
    
    def test_entry_with_url_but_no_description_gets_fetched(self):
        """Test that entries with Wikipedia URL but no description are re-fetched"""
        encyclopedia = AmiEncyclopedia(title="Test")
        entry = {
            "term": "climate",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Climate",
            # No description_html - this should trigger a fetch
        }
        encyclopedia.entries = [entry]
        
        # Mock Wikipedia page
        mock_wikipedia_page = Mock()
        mock_wikipedia_page.url = "https://en.wikipedia.org/wiki/Climate"
        mock_wikipedia_page.create_first_wikipedia_para.return_value = Mock(
            para_element=Mock(),
            get_definition=lambda: "Climate is the long-term pattern of weather."
        )
        
        # Mock the helper functions
        with patch('encyclopedia.cli.versioned_editor._get_wikipedia_page_for_entry',
                   return_value=mock_wikipedia_page):
            with patch('encyclopedia.cli.versioned_editor._get_first_paragraph_html_from_wikipedia_page',
                       return_value=(
                           '<span class="first_sentence_definition">Climate is the long-term pattern.</span>',
                           '<p class="wpage_first_para">Climate is the long-term pattern of weather.</p>'
                       )):
                add_wikipedia_feature(entry, encyclopedia)
        
        # Verify description was added
        assert 'description_html' in entry
        assert entry['description_html'] is not None
        assert len(entry['description_html']) > 0
    
    def test_entry_with_empty_description_gets_fetched(self):
        """Test that entries with empty description_html are re-fetched"""
        encyclopedia = AmiEncyclopedia(title="Test")
        entry = {
            "term": "greenhouse gas",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Greenhouse_gas",
            "description_html": ""  # Empty description
        }
        encyclopedia.entries = [entry]
        
        # Mock Wikipedia page
        mock_wikipedia_page = Mock()
        mock_wikipedia_page.url = "https://en.wikipedia.org/wiki/Greenhouse_gas"
        
        with patch('encyclopedia.cli.versioned_editor._get_wikipedia_page_for_entry',
                   return_value=mock_wikipedia_page):
            with patch('encyclopedia.cli.versioned_editor._get_first_paragraph_html_from_wikipedia_page',
                       return_value=(
                           '<span class="first_sentence_definition">A greenhouse gas is a gas.</span>',
                           '<p class="wpage_first_para">A greenhouse gas is a gas that absorbs and emits radiation.</p>'
                       )):
                add_wikipedia_feature(entry, encyclopedia)
        
        # Verify description was updated
        assert 'description_html' in entry
        assert len(entry['description_html']) > 0
        assert "greenhouse gas" in entry['description_html'].lower() or "gas" in entry['description_html'].lower()
    
    def test_has_non_empty_description_check(self):
        """Test the _has_non_empty_description helper function"""
        # Entry with valid description
        entry1 = {"description_html": "<p>This is a valid description.</p>"}
        assert _has_non_empty_description(entry1) is True
        
        # Entry with empty description
        entry2 = {"description_html": ""}
        assert _has_non_empty_description(entry2) is False
        
        # Entry with no description_html key
        entry3 = {}
        assert _has_non_empty_description(entry3) is False
        
        # Entry with only whitespace/empty tags
        entry4 = {"description_html": "<p></p>"}
        assert _has_non_empty_description(entry4) is False
        
        # Entry with whitespace only
        entry5 = {"description_html": "   "}
        assert _has_non_empty_description(entry5) is False
    
    def test_add_wikipedia_descriptions_handles_missing_descriptions(self):
        """Test that add_wikipedia_descriptions_to_encyclopedia handles missing descriptions"""
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [
            {
                "term": "climate",
                "wikipedia_url": "https://en.wikipedia.org/wiki/Climate",
                # Missing description_html
            },
            {
                "term": "greenhouse gas",
                "wikipedia_url": "https://en.wikipedia.org/wiki/Greenhouse_gas",
                "description_html": ""  # Empty description
            },
            {
                "term": "carbon dioxide",
                "wikipedia_url": "https://en.wikipedia.org/wiki/Carbon_dioxide",
                "description_html": "<p>Valid description</p>"  # Already has description
            }
        ]
        
        def mock_add_description(entry, enc, verbose=False):
            """Mock adding description"""
            if not _has_non_empty_description(entry):
                entry['description_html'] = f"<p>Description for {entry['term']}</p>"
            return {
                'success': True,
                'has_description': True,
                'has_definition': False,
                'wikipedia_url': entry.get('wikipedia_url'),
                'error': None
            }
        
        with patch('encyclopedia.utils.encyclopedia_builder.add_wikipedia_description_to_entry',
                   side_effect=mock_add_description):
            encyclopedia, results = add_wikipedia_descriptions_to_encyclopedia(
                encyclopedia,
                batch_size=10,
                verbose=False
            )
        
        # Verify all entries were processed
        assert results['total'] == 3
        assert results['successful'] == 3
        assert results['with_descriptions'] == 3
        
        # Verify descriptions were added to entries that needed them
        assert _has_non_empty_description(encyclopedia.entries[0])  # climate
        assert _has_non_empty_description(encyclopedia.entries[1])  # greenhouse gas
        assert _has_non_empty_description(encyclopedia.entries[2])  # carbon dioxide


class TestMissingImages:
    """Test handling of missing images"""
    
    def test_entry_without_images_gets_image_added(self):
        """Test that entries without images get images added"""
        encyclopedia = AmiEncyclopedia(title="Test")
        entry = {
            "term": "climate change",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Climate_change",
            "description_html": "<p>Description</p>",
            # No figure_html or images
        }
        encyclopedia.entries = [entry]
        
        # Mock Wikipedia page with image
        mock_wikipedia_page = Mock()
        mock_wikipedia_page.url = "https://en.wikipedia.org/wiki/Climate_change"
        
        # Mock image element
        mock_image_link = Mock()
        mock_image_link.tag = 'a'
        mock_image_link.get.return_value = "https://en.wikipedia.org/wiki/File:Climate_change_image.jpg"
        
        with patch('encyclopedia.cli.versioned_editor._get_wikipedia_page_for_entry',
                   return_value=mock_wikipedia_page):
            with patch('encyclopedia.cli.versioned_editor._extract_images_from_wikipedia_page',
                       return_value=[mock_image_link]):
                add_images_feature(entry, encyclopedia, verbose=False)
        
        # Verify image was added
        assert 'figure_html' in entry
        assert entry['figure_html'] is not None
        assert 'image_link' in entry
        assert entry['image_link'] is not None
    
    def test_entry_with_existing_images_skipped(self):
        """Test that entries with existing images are skipped"""
        encyclopedia = AmiEncyclopedia(title="Test")
        entry = {
            "term": "climate change",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Climate_change",
            "figure_html": Mock(),  # Already has image
        }
        encyclopedia.entries = [entry]
        
        call_count = [0]
        
        def mock_extract_images(wikipedia_page, verbose=False):
            call_count[0] += 1
            return []
        
        with patch('encyclopedia.cli.versioned_editor._get_wikipedia_page_for_entry',
                   return_value=Mock()):
            with patch('encyclopedia.cli.versioned_editor._extract_images_from_wikipedia_page',
                       side_effect=mock_extract_images):
                add_images_feature(entry, encyclopedia, verbose=False)
        
        # Should not have called extract_images since entry already has image
        assert call_count[0] == 0
    
    def test_add_image_links_handles_missing_images(self):
        """Test that add_image_links_to_encyclopedia handles missing images"""
        encyclopedia = AmiEncyclopedia(title="Test")
        encyclopedia.entries = [
            {
                "term": "climate change",
                "wikipedia_url": "https://en.wikipedia.org/wiki/Climate_change",
                "description_html": "<p>Description</p>",
                # No images
            },
            {
                "term": "greenhouse gas",
                "wikipedia_url": "https://en.wikipedia.org/wiki/Greenhouse_gas",
                "description_html": "<p>Description</p>",
                # No images
            },
            {
                "term": "carbon dioxide",
                "wikipedia_url": "https://en.wikipedia.org/wiki/Carbon_dioxide",
                "description_html": "<p>Description</p>",
                "figure_html": Mock(),  # Already has image
            }
        ]
        
        def mock_add_image(entry, enc, verbose=False):
            """Mock adding image"""
            if not entry.get('figure_html') and not entry.get('images'):
                entry['figure_html'] = Mock()
                entry['image_link'] = f"https://en.wikipedia.org/wiki/File:Image_{entry['term']}.jpg"
            return {
                'success': True,
                'has_image_link': bool(entry.get('figure_html') or entry.get('image_link')),
                'image_url': entry.get('image_link'),
                'error': None
            }
        
        with patch('encyclopedia.utils.encyclopedia_builder.add_image_link_to_entry',
                   side_effect=mock_add_image):
            encyclopedia, results = add_image_links_to_encyclopedia(
                encyclopedia,
                batch_size=10,
                verbose=False
            )
        
        # Verify all entries were processed
        assert results['total'] == 3
        assert results['successful'] == 3
        assert results['with_images'] == 3  # All should have images (2 added, 1 already had)
        
        # Verify images were added to entries that needed them
        assert 'figure_html' in encyclopedia.entries[0]  # climate change
        assert 'figure_html' in encyclopedia.entries[1]  # greenhouse gas
        assert 'figure_html' in encyclopedia.entries[2]  # carbon dioxide (already had)
    
    def test_image_extraction_handles_missing_wikipedia_page(self):
        """Test that image extraction handles missing Wikipedia pages gracefully"""
        encyclopedia = AmiEncyclopedia(title="Test")
        entry = {
            "term": "nonexistent term",
            "wikipedia_url": "",
            "description_html": "<p>Description</p>",
        }
        
        with patch('encyclopedia.cli.versioned_editor._get_wikipedia_page_for_entry',
                   return_value=None):
            add_images_feature(entry, encyclopedia, verbose=False)
        
        # Should not have added images
        assert 'figure_html' not in entry or entry.get('figure_html') is None
    
    def test_image_extraction_handles_no_images_found(self):
        """Test that image extraction handles cases where no images are found"""
        encyclopedia = AmiEncyclopedia(title="Test")
        entry = {
            "term": "abstract concept",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Abstract_concept",
            "description_html": "<p>Description</p>",
        }
        
        mock_wikipedia_page = Mock()
        mock_wikipedia_page.url = "https://en.wikipedia.org/wiki/Abstract_concept"
        
        with patch('encyclopedia.cli.versioned_editor._get_wikipedia_page_for_entry',
                   return_value=mock_wikipedia_page):
            with patch('encyclopedia.cli.versioned_editor._extract_images_from_wikipedia_page',
                       return_value=[]):  # No images found
                add_images_feature(entry, encyclopedia, verbose=False)
        
        # Should not have added images
        assert 'figure_html' not in entry or entry.get('figure_html') is None


class TestIntegration:
    """Integration tests combining batch-size, descriptions, and images"""
    
    def test_full_workflow_with_batch_size(self):
        """Test full workflow with batch-size for both descriptions and images"""
        encyclopedia = AmiEncyclopedia(title="Test")
        # Create entries with missing descriptions and images
        encyclopedia.entries = [
            {
                "term": f"term_{i}",
                "wikipedia_url": f"https://en.wikipedia.org/wiki/Term_{i}",
                # Missing description_html and images
            }
            for i in range(6)
        ]
        
        batch_size = 2
        
        def mock_add_description(entry, enc, verbose=False):
            entry['description_html'] = f"<p>Description for {entry['term']}</p>"
            return {
                'success': True,
                'has_description': True,
                'has_definition': False,
                'wikipedia_url': entry.get('wikipedia_url'),
                'error': None
            }
        
        def mock_add_image(entry, enc, verbose=False):
            entry['figure_html'] = Mock()
            entry['image_link'] = f"https://en.wikipedia.org/wiki/File:Image_{entry['term']}.jpg"
            return {
                'success': True,
                'has_image_link': True,
                'image_url': entry['image_link'],
                'error': None
            }
        
        with patch('encyclopedia.utils.encyclopedia_builder.add_wikipedia_description_to_entry',
                   side_effect=mock_add_description):
            with patch('encyclopedia.utils.encyclopedia_builder.add_image_link_to_entry',
                       side_effect=mock_add_image):
                with patch('time.sleep') as mock_sleep:
                    # Add descriptions - returns tuple (encyclopedia, results_dict)
                    encyclopedia, desc_results = add_wikipedia_descriptions_to_encyclopedia(
                        encyclopedia,
                        batch_size=batch_size,
                        verbose=False
                    )
                    
                    # Add images - returns tuple (encyclopedia, results_dict)
                    encyclopedia, img_results = add_image_links_to_encyclopedia(
                        encyclopedia,
                        batch_size=batch_size,
                        verbose=False
                    )
        
        # Verify descriptions were added
        assert desc_results['total'] == 6
        assert desc_results['successful'] == 6
        
        # Verify images were added
        assert img_results['total'] == 6
        assert img_results['successful'] == 6
        
        # Verify batch delays were added
        # With batch_size=2 and 6 entries:
        # - Descriptions: 3 batches (2, 2, 2) = 2 delays between batches
        # - Images: 3 batches (2, 2, 2) = 2 delays between batches
        # Total = 4 delays (not 6, since we don't delay after the last batch)
        assert mock_sleep.call_count == 4
        
        # Verify all entries have descriptions and images
        for entry in encyclopedia.entries:
            assert _has_non_empty_description(entry)
            assert entry.get('figure_html') is not None
