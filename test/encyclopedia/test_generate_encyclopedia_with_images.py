"""
Test to generate encyclopedia files with images for manual inspection.

This test creates encyclopedias with multiple entries (< 20) that all contain images,
saved to the temp directory for easy viewing.

Date: February 16, 2026
"""

import pytest
from pathlib import Path

from encyclopedia.utils.resources import Resources
from encyclopedia.utils.validation import (
    validate_image_links_added,
    validate_encyclopedia_completeness
)
from Examples.create_encyclopedia_from_wordlist import create_encyclopedia_from_wordlist


class TestGenerateEncyclopediaWithImages:
    """Generate encyclopedia files with images for manual inspection"""
    
    def test_generate_climate_encyclopedia_with_images(self):
        """Generate a climate-themed encyclopedia with ~10 entries, all with images"""
        # Climate-related terms that should have images on Wikipedia
        terms = [
            "climate change",
            "greenhouse gas",
            "carbon dioxide",
            "methane",
            "global warming",
            "ice sheet",
            "sea level rise",
            "ocean acidification",
            "atmosphere",
            "precipitation"
        ]
        
        # Create output directory in temp/
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "GeneratedWithImages")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create encyclopedia HTML file
        output_file = Path(output_dir, "climate_encyclopedia_with_images.html")
        
        print(f"\n{'='*60}")
        print(f"Generating Climate Encyclopedia with Images")
        print(f"{'='*60}")
        print(f"Terms ({len(terms)}): {', '.join(terms)}")
        print(f"Output file: {output_file}")
        print(f"{'='*60}\n")
        
        # Create encyclopedia with images enabled
        encyclopedia = create_encyclopedia_from_wordlist(
            terms=terms,
            title="Climate Encyclopedia with Images",
            add_wikipedia=True,
            add_images=True,  # Request images
            batch_size=10,
            validate=False,
            verbose=True
        )
        
        # Save encyclopedia
        print(f"\nSaving encyclopedia to: {output_file}")
        encyclopedia.save_wiki_normalized_html(output_file)
        print(f"✓ Encyclopedia saved")
        
        # Verify file was created
        assert output_file.exists(), \
            f"Encyclopedia file should exist at {output_file}"
        
        # Validate images
        print(f"\nValidating images...")
        image_results = validate_image_links_added(
            encyclopedia, 
            check_url_exists=False
        )
        
        print(f"\n{'='*60}")
        print(f"IMAGE VALIDATION RESULTS")
        print(f"{'='*60}")
        print(f"Total entries: {image_results['total_entries']}")
        print(f"Entries with images: {image_results['entries_with_images']}")
        print(f"Entries without images: {image_results['entries_without_images']}")
        print(f"Success rate: {image_results['success_rate']:.1f}%")
        print(f"{'='*60}\n")
        
        # Print entry details
        print(f"\nEntry Details:")
        for entry in encyclopedia.entries:
            term = entry.get('term', entry.get('canonical_term', 'Unknown'))
            has_image = bool(entry.get('figure_html') or entry.get('image_link'))
            print(f"  - {term}: Image={'✓' if has_image else '✗'}")
        
        print(f"\n{'='*60}")
        print(f"✓ Encyclopedia generated: {output_file}")
        print(f"{'='*60}\n")
        
        return output_file
    
    def test_generate_science_encyclopedia_with_images(self):
        """Generate a science-themed encyclopedia with ~12 entries, all with images"""
        # Science terms that should have images on Wikipedia
        terms = [
            "atom",
            "molecule",
            "DNA",
            "protein",
            "cell",
            "evolution",
            "photosynthesis",
            "ecosystem",
            "biodiversity",
            "genetics",
            "microscope",
            "telescope"
        ]
        
        # Create output directory in temp/
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "GeneratedWithImages")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create encyclopedia HTML file
        output_file = Path(output_dir, "science_encyclopedia_with_images.html")
        
        print(f"\n{'='*60}")
        print(f"Generating Science Encyclopedia with Images")
        print(f"{'='*60}")
        print(f"Terms ({len(terms)}): {', '.join(terms)}")
        print(f"Output file: {output_file}")
        print(f"{'='*60}\n")
        
        # Create encyclopedia with images enabled
        encyclopedia = create_encyclopedia_from_wordlist(
            terms=terms,
            title="Science Encyclopedia with Images",
            add_wikipedia=True,
            add_images=True,  # Request images
            batch_size=10,
            validate=False,
            verbose=True
        )
        
        # Save encyclopedia
        print(f"\nSaving encyclopedia to: {output_file}")
        encyclopedia.save_wiki_normalized_html(output_file)
        print(f"✓ Encyclopedia saved")
        
        # Verify file was created
        assert output_file.exists(), \
            f"Encyclopedia file should exist at {output_file}"
        
        # Validate images
        print(f"\nValidating images...")
        image_results = validate_image_links_added(
            encyclopedia, 
            check_url_exists=False
        )
        
        print(f"\n{'='*60}")
        print(f"IMAGE VALIDATION RESULTS")
        print(f"{'='*60}")
        print(f"Total entries: {image_results['total_entries']}")
        print(f"Entries with images: {image_results['entries_with_images']}")
        print(f"Entries without images: {image_results['entries_without_images']}")
        print(f"Success rate: {image_results['success_rate']:.1f}%")
        print(f"{'='*60}\n")
        
        # Print entry details
        print(f"\nEntry Details:")
        for entry in encyclopedia.entries:
            term = entry.get('term', entry.get('canonical_term', 'Unknown'))
            has_image = bool(entry.get('figure_html') or entry.get('image_link'))
            print(f"  - {term}: Image={'✓' if has_image else '✗'}")
        
        print(f"\n{'='*60}")
        print(f"✓ Encyclopedia generated: {output_file}")
        print(f"{'='*60}\n")
        
        return output_file
