"""
Validation utilities for encyclopedia completeness.

Provides functions to validate that encyclopedias have been properly
populated with definitions, images, descriptions, etc.
"""

from typing import Dict, List, Any
from encyclopedia.core.encyclopedia import AmiEncyclopedia


def validate_first_sentences_extracted(encyclopedia: AmiEncyclopedia) -> Dict[str, Any]:
    """
    Validate that first sentences/definitions have been extracted.
    
    Checks:
    - entry['definition_html'] exists and is non-empty
    - entry['definition_html'] contains <span class="first_sentence_definition">
    - First sentence is actually extracted (not just full description)
    
    Args:
        encyclopedia: Encyclopedia to validate
        
    Returns:
        Dictionary with:
        - total_entries: int
        - entries_with_definitions: int
        - entries_without_definitions: List[Dict] (entries missing definitions)
        - success_rate: float (percentage)
        - is_valid: bool
        - sample_with_definitions: List[Dict] (sample entries)
        - sample_without_definitions: List[Dict] (sample entries)
    """
    total = len(encyclopedia.entries)
    entries_with_definitions = []
    entries_without_definitions = []
    
    for entry in encyclopedia.entries:
        term = entry.get('term', entry.get('canonical_term', 'Unknown'))
        definition_html = entry.get('definition_html', '')
        description_html = entry.get('description_html', '')
        wikipedia_url = entry.get('wikipedia_url', '')
        
        # Check if definition exists and contains first sentence span
        has_definition = (
            definition_html and 
            'first_sentence_definition' in definition_html
        )
        
        if has_definition:
            entries_with_definitions.append({
                'term': term,
                'definition_preview': definition_html[:100] + '...' if len(definition_html) > 100 else definition_html,
                'wikipedia_url': wikipedia_url
            })
        else:
            entries_without_definitions.append({
                'term': term,
                'wikipedia_url': wikipedia_url,
                'has_description_html': bool(description_html),
                'has_definition_html': bool(definition_html),
                'description_preview': description_html[:50] + '...' if description_html and len(description_html) > 50 else (description_html or 'None')
            })
    
    success_rate = (len(entries_with_definitions) / total * 100) if total > 0 else 0.0
    
    return {
        'total_entries': total,
        'entries_with_definitions': len(entries_with_definitions),
        'entries_without_definitions': len(entries_without_definitions),
        'success_rate': success_rate,
        'is_valid': len(entries_without_definitions) == 0,
        'sample_with_definitions': entries_with_definitions[:5],
        'sample_without_definitions': entries_without_definitions[:10]
    }


def validate_image_links_added(encyclopedia: AmiEncyclopedia) -> Dict[str, Any]:
    """
    Validate that image links have been added.
    
    Checks:
    - entry['figure_html'] exists and is an element or HTML string
    - entry['figure_html'] contains link to Wikipedia File: page
    - entry['image_link'] URL exists
    
    Args:
        encyclopedia: Encyclopedia to validate
        
    Returns:
        Dictionary with:
        - total_entries: int
        - entries_with_images: int
        - entries_without_images: List[Dict] (entries missing images)
        - success_rate: float (percentage)
        - is_valid: bool
        - sample_with_images: List[Dict] (sample entries)
        - sample_without_images: List[Dict] (sample entries)
    """
    total = len(encyclopedia.entries)
    entries_with_images = []
    entries_without_images = []
    
    for entry in encyclopedia.entries:
        term = entry.get('term', entry.get('canonical_term', 'Unknown'))
        figure_html = entry.get('figure_html')
        image_link = entry.get('image_link')
        wikipedia_url = entry.get('wikipedia_url', '')
        
        # Check if image link exists
        has_image = False
        image_url = None
        
        if figure_html:
            # Check if it's an element
            if hasattr(figure_html, 'tag'):
                if figure_html.tag == 'a':
                    href = figure_html.get('href', '')
                    if '/wiki/File:' in href or '/File:' in href:
                        has_image = True
                        image_url = href
            # Check if it's HTML string
            elif isinstance(figure_html, str):
                if 'wikipedia-image-link' in figure_html or '/wiki/File:' in figure_html:
                    has_image = True
                    # Try to extract URL from HTML string
                    import re
                    url_match = re.search(r'href=["\']([^"\']*wiki/File:[^"\']*)["\']', figure_html)
                    if url_match:
                        image_url = url_match.group(1)
        
        if image_link and ('/wiki/File:' in image_link or '/File:' in image_link):
            has_image = True
            image_url = image_link
        
        if has_image:
            entries_with_images.append({
                'term': term,
                'image_url': image_url,
                'wikipedia_url': wikipedia_url
            })
        else:
            entries_without_images.append({
                'term': term,
                'wikipedia_url': wikipedia_url,
                'has_figure_html': figure_html is not None,
                'has_image_link': image_link is not None,
                'figure_html_type': type(figure_html).__name__ if figure_html else None
            })
    
    success_rate = (len(entries_with_images) / total * 100) if total > 0 else 0.0
    
    return {
        'total_entries': total,
        'entries_with_images': len(entries_with_images),
        'entries_without_images': len(entries_without_images),
        'success_rate': success_rate,
        'is_valid': len(entries_without_images) == 0,
        'sample_with_images': entries_with_images[:5],
        'sample_without_images': entries_without_images[:10]
    }


def validate_encyclopedia_completeness(encyclopedia: AmiEncyclopedia) -> Dict[str, Any]:
    """
    Comprehensive validation of encyclopedia completeness.
    
    Validates:
    - Definitions (first sentences)
    - Images
    - Wikipedia URLs
    - Wikidata IDs
    - Descriptions
    
    Args:
        encyclopedia: Encyclopedia to validate
        
    Returns:
        Dictionary with validation results for all aspects
    """
    definition_results = validate_first_sentences_extracted(encyclopedia)
    image_results = validate_image_links_added(encyclopedia)
    
    # Additional validations
    total = len(encyclopedia.entries)
    entries_with_wikipedia = sum(1 for e in encyclopedia.entries if e.get('wikipedia_url'))
    entries_with_wikidata = sum(1 for e in encyclopedia.entries if e.get('wikidata_id') and e.get('wikidata_id') not in ('no_wikidata_id', 'invalid_wikidata_id'))
    entries_with_descriptions = sum(1 for e in encyclopedia.entries if e.get('description_html'))
    
    return {
        'total_entries': total,
        'definitions': definition_results,
        'images': image_results,
        'wikipedia_urls': {
            'total': total,
            'with_urls': entries_with_wikipedia,
            'without_urls': total - entries_with_wikipedia,
            'success_rate': (entries_with_wikipedia / total * 100) if total > 0 else 0.0
        },
        'wikidata_ids': {
            'total': total,
            'with_ids': entries_with_wikidata,
            'without_ids': total - entries_with_wikidata,
            'success_rate': (entries_with_wikidata / total * 100) if total > 0 else 0.0
        },
        'descriptions': {
            'total': total,
            'with_descriptions': entries_with_descriptions,
            'without_descriptions': total - entries_with_descriptions,
            'success_rate': (entries_with_descriptions / total * 100) if total > 0 else 0.0
        },
        'overall_valid': (
            definition_results['is_valid'] and
            image_results['is_valid'] and
            entries_with_wikipedia > 0
        )
    }


def print_validation_report(results: Dict[str, Any], verbose: bool = True) -> None:
    """
    Print validation results in a readable format.
    
    Args:
        results: Results dictionary from validate_encyclopedia_completeness()
        verbose: If True, show detailed samples
    """
    print("\n" + "="*60)
    print("ENCYCLOPEDIA VALIDATION REPORT")
    print("="*60)
    
    total = results['total_entries']
    print(f"\nTotal entries: {total}")
    
    # Definitions
    def_results = results['definitions']
    print(f"\n📝 Definitions (First Sentences):")
    print(f"  ✓ With definitions: {def_results['entries_with_definitions']}/{total} ({def_results['success_rate']:.1f}%)")
    print(f"  ✗ Without definitions: {def_results['entries_without_definitions']}/{total}")
    
    if verbose and def_results['sample_without_definitions']:
        print(f"\n  Sample entries WITHOUT definitions:")
        for entry in def_results['sample_without_definitions'][:5]:
            print(f"    - {entry['term']}")
            if entry.get('wikipedia_url'):
                print(f"      Wikipedia: {entry['wikipedia_url']}")
            print(f"      Has description_html: {entry.get('has_description_html', False)}")
            print(f"      Has definition_html: {entry.get('has_definition_html', False)}")
    
    # Images
    img_results = results['images']
    print(f"\n🖼️  Image Links:")
    print(f"  ✓ With images: {img_results['entries_with_images']}/{total} ({img_results['success_rate']:.1f}%)")
    print(f"  ✗ Without images: {img_results['entries_without_images']}/{total}")
    
    if verbose and img_results['sample_without_images']:
        print(f"\n  Sample entries WITHOUT images:")
        for entry in img_results['sample_without_images'][:5]:
            print(f"    - {entry['term']}")
            if entry.get('wikipedia_url'):
                print(f"      Wikipedia: {entry['wikipedia_url']}")
            print(f"      Has figure_html: {entry.get('has_figure_html', False)}")
            print(f"      Has image_link: {entry.get('has_image_link', False)}")
    
    # Wikipedia URLs
    wiki_results = results['wikipedia_urls']
    print(f"\n🌐 Wikipedia URLs:")
    print(f"  ✓ With URLs: {wiki_results['with_urls']}/{total} ({wiki_results['success_rate']:.1f}%)")
    print(f"  ✗ Without URLs: {wiki_results['without_urls']}/{total}")
    
    # Wikidata IDs
    wd_results = results['wikidata_ids']
    print(f"\n🔗 Wikidata IDs:")
    print(f"  ✓ With IDs: {wd_results['with_ids']}/{total} ({wd_results['success_rate']:.1f}%)")
    print(f"  ✗ Without IDs: {wd_results['without_ids']}/{total}")
    
    # Descriptions
    desc_results = results['descriptions']
    print(f"\n📄 Descriptions:")
    print(f"  ✓ With descriptions: {desc_results['with_descriptions']}/{total} ({desc_results['success_rate']:.1f}%)")
    print(f"  ✗ Without descriptions: {desc_results['without_descriptions']}/{total}")
    
    # Overall
    print(f"\n{'='*60}")
    if results['overall_valid']:
        print("✅ VALIDATION PASSED: Encyclopedia is complete")
    else:
        print("⚠️  VALIDATION WARNINGS: Some entries are missing content")
        print("\nIssues found:")
        if not def_results['is_valid']:
            print(f"  - {def_results['entries_without_definitions']} entries missing definitions")
        if not img_results['is_valid']:
            print(f"  - {img_results['entries_without_images']} entries missing images")
        if wiki_results['without_urls'] > 0:
            print(f"  - {wiki_results['without_urls']} entries missing Wikipedia URLs")
    print("="*60 + "\n")
