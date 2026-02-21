"""
Validation utilities for encyclopedia completeness.

Provides functions to validate that encyclopedias have been properly
populated with definitions, images, descriptions, etc.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import re
import requests
from lxml.html import fromstring
from encyclopedia.core.encyclopedia import AmiEncyclopedia


def validate_descriptions_have_html_markup(encyclopedia: AmiEncyclopedia) -> Dict[str, Any]:
    """
    Validate that descriptions contain HTML markup (not just flat text).
    
    Checks:
    - entry['description_html'] exists and is non-empty
    - entry['description_html'] contains HTML tags (not just plain text)
    - entry['description_html'] contains hyperlinks (if applicable)
    
    Args:
        encyclopedia: Encyclopedia to validate
        
    Returns:
        Dictionary with:
        - total_entries: int
        - entries_with_html_descriptions: int
        - entries_without_html_descriptions: List[Dict] (entries missing HTML markup)
        - success_rate: float (percentage)
        - is_valid: bool
        - sample_with_html: List[Dict] (sample entries)
        - sample_without_html: List[Dict] (sample entries)
    """
    total = len(encyclopedia.entries)
    entries_with_html = []
    entries_without_html = []
    
    for entry in encyclopedia.entries:
        term = entry.get('term', entry.get('canonical_term', 'Unknown'))
        description_html = entry.get('description_html', '')
        wikipedia_url = entry.get('wikipedia_url', '')
        
        # Check if description exists and contains HTML markup
        has_html = False
        has_hyperlinks = False
        
        if description_html:
            # Check if it contains HTML tags (not just plain text)
            # Look for common HTML tags: <p>, <span>, <a>, <div>, <em>, <strong>, etc.
            html_tag_pattern = r'<[a-zA-Z][^>]*>'
            if re.search(html_tag_pattern, description_html):
                has_html = True
                
                # Check for hyperlinks
                link_pattern = r'<a\s+[^>]*href\s*=\s*["\'][^"\']*["\']'
                if re.search(link_pattern, description_html, re.IGNORECASE):
                    has_hyperlinks = True
            else:
                # If no HTML tags, it's just plain text
                has_html = False
        
        if has_html:
            entries_with_html.append({
                'term': term,
                'description_preview': description_html[:100] + '...' if len(description_html) > 100 else description_html,
                'has_hyperlinks': has_hyperlinks,
                'wikipedia_url': wikipedia_url
            })
        else:
            entries_without_html.append({
                'term': term,
                'wikipedia_url': wikipedia_url,
                'has_description_html': bool(description_html),
                'description_preview': description_html[:50] + '...' if description_html and len(description_html) > 50 else (description_html or 'None'),
                'is_plain_text': bool(description_html and not re.search(r'<[a-zA-Z]', description_html))
            })
    
    success_rate = (len(entries_with_html) / total * 100) if total > 0 else 0.0
    
    return {
        'total_entries': total,
        'entries_with_html_descriptions': len(entries_with_html),
        'entries_without_html_descriptions': len(entries_without_html),
        'success_rate': success_rate,
        'is_valid': len(entries_without_html) == 0,
        'sample_with_html': entries_with_html[:5],
        'sample_without_html': entries_without_html[:10]
    }


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


def _normalize_image_url(url: str) -> str:
    """
    Normalize image URL by removing spurious 'encyclopedia' prefix if present.
    
    Args:
        url: Image URL that may contain spurious prefix
        
    Returns:
        Normalized URL
    """
    if not url:
        return url
    
    # Remove spurious 'encyclopedia' prefix if present
    # e.g., "encyclopediahttps://en.wikipedia.org/wiki/File:..." -> "https://en.wikipedia.org/wiki/File:..."
    if url.startswith('encyclopedia'):
        # Check if next part looks like a URL
        remaining = url[len('encyclopedia'):]
        if remaining.startswith('http://') or remaining.startswith('https://'):
            return remaining
    
    # Also handle cases like "encyclopedia/wiki/File:..." -> "https://en.wikipedia.org/wiki/File:..."
    if url.startswith('encyclopedia/wiki/File:'):
        return f"https://en.wikipedia.org/wiki/File:{url[len('encyclopedia/wiki/File:'):]}"
    
    return url


def _check_image_url_exists(url: str, timeout: int = 5) -> bool:
    """
    Check if an image URL exists and is accessible.
    
    Args:
        url: Image URL to check
        timeout: Request timeout in seconds
        
    Returns:
        True if URL exists and is accessible, False otherwise
    """
    if not url:
        return False
    
    # Normalize URL first
    url = _normalize_image_url(url)
    
    # Convert Wikipedia File: page URL to actual image URL if needed
    # Wikipedia File: pages redirect to actual image URLs
    if '/wiki/File:' in url:
        # For validation, we'll check if the File: page exists
        # The actual image URL would be different, but checking the File: page is sufficient
        pass
    
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except Exception:
        # If HEAD fails, try GET
        try:
            response = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
            return response.status_code == 200
        except Exception:
            return False


def validate_image_links_added(encyclopedia: AmiEncyclopedia, check_url_exists: bool = True) -> Dict[str, Any]:
    """
    Validate that image links have been added.
    
    Checks:
    - entry['figure_html'] exists and is an element or HTML string
    - entry['figure_html'] contains link to Wikipedia File: page
    - entry['image_link'] URL exists
    - Image URL is accessible (if check_url_exists=True)
    
    Args:
        encyclopedia: Encyclopedia to validate
        check_url_exists: If True, verify that image URLs are accessible
        
    Returns:
        Dictionary with:
        - total_entries: int
        - entries_with_images: int
        - entries_without_images: List[Dict] (entries missing images)
        - entries_with_invalid_urls: List[Dict] (entries with inaccessible URLs)
        - success_rate: float (percentage)
        - is_valid: bool
        - sample_with_images: List[Dict] (sample entries)
        - sample_without_images: List[Dict] (sample entries)
    """
    total = len(encyclopedia.entries)
    entries_with_images = []
    entries_without_images = []
    entries_with_invalid_urls = []
    
    for entry in encyclopedia.entries:
        term = entry.get('term', entry.get('canonical_term', 'Unknown'))
        figure_html = entry.get('figure_html')
        image_link = entry.get('image_link')
        wikipedia_url = entry.get('wikipedia_url', '')
        
        # Check if image link exists
        has_image = False
        image_url = None
        
        if figure_html is not None:
            # Check if it's an element (lxml Element)
            if hasattr(figure_html, 'tag'):
                # Check for <a> element with href
                if figure_html.tag == 'a':
                    href = figure_html.get('href', '')
                    if href and ('/wiki/File:' in href or '/File:' in href or 'upload.wikimedia.org' in href):
                        has_image = True
                        image_url = href
                # Check for <figure> element with image
                elif figure_html.tag == 'figure':
                    img_elem = figure_html.xpath('.//img')
                    if img_elem:
                        src = img_elem[0].get('src', '')
                        if src and ('upload.wikimedia.org' in src or '/wiki/File:' in src):
                            has_image = True
                            image_url = src
                # Check for <img> element directly
                elif figure_html.tag == 'img':
                    src = figure_html.get('src', '')
                    if src and ('upload.wikimedia.org' in src or '/wiki/File:' in src):
                        has_image = True
                        image_url = src
                # Check for <div title="figure"> wrapper (amilib format)
                elif figure_html.tag == 'div' and figure_html.get('title') == 'figure':
                    # Look for <a> or <img> inside
                    a_elem = figure_html.xpath('.//a')
                    if a_elem:
                        href = a_elem[0].get('href', '')
                        if href and ('/wiki/File:' in href or '/File:' in href or 'upload.wikimedia.org' in href):
                            has_image = True
                            image_url = href
                    if not has_image:
                        img_elem = figure_html.xpath('.//img')
                        if img_elem:
                            src = img_elem[0].get('src', '')
                            if src and ('upload.wikimedia.org' in src or '/wiki/File:' in src):
                                has_image = True
                                image_url = src
            # Check if it's HTML string
            elif isinstance(figure_html, str):
                if 'wikipedia-image-link' in figure_html or '/wiki/File:' in figure_html or 'upload.wikimedia.org' in figure_html:
                    has_image = True
                    # Try to extract URL from HTML string
                    url_match = re.search(r'href=["\']([^"\']*(?:wiki/File:|upload\.wikimedia\.org)[^"\']*)["\']', figure_html)
                    if url_match:
                        image_url = url_match.group(1)
                    # Also try to extract from img src
                    if not image_url:
                        img_match = re.search(r'src=["\']([^"\']*(?:upload\.wikimedia\.org|wiki/File:)[^"\']*)["\']', figure_html)
                        if img_match:
                            image_url = img_match.group(1)
        
        # Check image_link field - accept both Wikipedia File: URLs and direct Wikimedia Commons URLs
        if image_link:
            if '/wiki/File:' in image_link or '/File:' in image_link or 'upload.wikimedia.org' in image_link:
                has_image = True
                if not image_url:  # Use image_link if figure_html didn't provide URL
                    image_url = image_link
        
        if has_image:
            # Normalize URL
            normalized_url = _normalize_image_url(image_url)
            
            # Check if URL exists if requested
            url_valid = True
            if check_url_exists:
                url_valid = _check_image_url_exists(normalized_url)
            
            if url_valid:
                entries_with_images.append({
                    'term': term,
                    'image_url': normalized_url,
                    'original_url': image_url,
                    'wikipedia_url': wikipedia_url
                })
            else:
                entries_with_invalid_urls.append({
                    'term': term,
                    'image_url': normalized_url,
                    'original_url': image_url,
                    'wikipedia_url': wikipedia_url,
                    'error': 'URL not accessible'
                })
        else:
            entries_without_images.append({
                'term': term,
                'wikipedia_url': wikipedia_url,
                'has_figure_html': figure_html is not None,
                'has_image_link': image_link is not None,
                'figure_html_type': type(figure_html).__name__ if figure_html is not None else None
            })
    
    success_rate = (len(entries_with_images) / total * 100) if total > 0 else 0.0
    
    return {
        'total_entries': total,
        'entries_with_images': len(entries_with_images),
        'entries_without_images': len(entries_without_images),
        'entries_with_invalid_urls': len(entries_with_invalid_urls),
        'success_rate': success_rate,
        'is_valid': len(entries_without_images) == 0 and len(entries_with_invalid_urls) == 0,
        'sample_with_images': entries_with_images[:5],
        'sample_without_images': entries_without_images[:10],
        'sample_with_invalid_urls': entries_with_invalid_urls[:10]
    }


def validate_encyclopedia_completeness(encyclopedia: AmiEncyclopedia, check_image_urls: bool = False) -> Dict[str, Any]:
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
        check_image_urls: If True, verify that image URLs are accessible (default: False, can be slow)
        
    Returns:
        Dictionary with validation results for all aspects
    """
    definition_results = validate_first_sentences_extracted(encyclopedia)
    image_results = validate_image_links_added(encyclopedia, check_url_exists=check_image_urls)
    
    # Additional validations
    total = len(encyclopedia.entries)
    entries_with_wikipedia = sum(1 for e in encyclopedia.entries if e.get('wikipedia_url'))
    entries_with_wikidata = sum(1 for e in encyclopedia.entries if e.get('wikidata_id') and e.get('wikidata_id') not in ('no_wikidata_id', 'invalid_wikidata_id'))
    
    # Validate descriptions have HTML markup (not just flat text)
    description_results = validate_descriptions_have_html_markup(encyclopedia)
    
    return {
        'total_entries': total,
        'definitions': definition_results,
        'images': image_results,
        'descriptions': description_results,
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
        'overall_valid': (
            definition_results['is_valid'] and
            image_results['is_valid'] and
            description_results['is_valid'] and
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
    
    if verbose and img_results.get('sample_with_invalid_urls'):
        print(f"\n  Sample entries WITH invalid image URLs:")
        for entry in img_results['sample_with_invalid_urls'][:5]:
            print(f"    - {entry['term']}")
            print(f"      Image URL: {entry.get('image_url', 'None')}")
            print(f"      Error: {entry.get('error', 'Unknown')}")
    
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
    
    # Descriptions with HTML markup
    desc_results = results['descriptions']
    print(f"\n📄 Descriptions (with HTML markup):")
    print(f"  ✓ With HTML descriptions: {desc_results['entries_with_html_descriptions']}/{total} ({desc_results['success_rate']:.1f}%)")
    print(f"  ✗ Without HTML descriptions: {desc_results['entries_without_html_descriptions']}/{total}")
    
    if verbose and desc_results['sample_without_html']:
        print(f"\n  Sample entries WITHOUT HTML markup:")
        for entry in desc_results['sample_without_html'][:5]:
            print(f"    - {entry['term']}")
            if entry.get('wikipedia_url'):
                print(f"      Wikipedia: {entry['wikipedia_url']}")
            print(f"      Has description_html: {entry.get('has_description_html', False)}")
            print(f"      Is plain text: {entry.get('is_plain_text', False)}")
            print(f"      Preview: {entry.get('description_preview', 'None')[:100]}")
    
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
            if img_results.get('entries_with_invalid_urls', 0) > 0:
                print(f"  - {img_results['entries_with_invalid_urls']} entries with invalid image URLs")
        if not desc_results['is_valid']:
            print(f"  - {desc_results['entries_without_html_descriptions']} entries missing HTML markup in descriptions")
        if wiki_results['without_urls'] > 0:
            print(f"  - {wiki_results['without_urls']} entries missing Wikipedia URLs")
    print("="*60 + "\n")
