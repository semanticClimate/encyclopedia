"""
Encyclopedia building utilities.

Provides functions for creating encyclopedias from wordlists with
Wikipedia integration, image links, and validation.
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import lxml.etree as ET

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources
from amilib.ami_dict import AmiDictionary


def create_dictionary_from_terms(
    terms: List[str],
    title: str,
    temp_path: Path
) -> AmiDictionary:
    """
    Step 1: Create basic dictionary structure from terms.
    
    Args:
        terms: List of terms to include
        title: Title for the dictionary
        temp_path: Temporary directory for output
        
    Returns:
        AmiDictionary instance with basic entries
    """
    dictionary, _ = AmiDictionary.create_dictionary_from_words(
        terms=terms,
        title=title,
        wikidata=False,  # We'll get Wikidata IDs from Wikipedia pages
        outdir=temp_path
    )
    return dictionary


def enhance_dictionary_with_wikipedia(
    dictionary: AmiDictionary,
    verbose: bool = False
) -> AmiDictionary:
    """
    Step 2: Enhance dictionary with Wikipedia content.
    
    Args:
        dictionary: Dictionary to enhance
        verbose: If True, show detailed progress
        
    Returns:
        Enhanced dictionary
    """
    from amilib.wikimedia import WikipediaPage
    
    enhanced_count = 0
    for term, ami_entry in dictionary.entry_by_term.items():
        try:
            wikipedia_page = WikipediaPage.lookup_wikipedia_page_for_term(term)
            if wikipedia_page:
                # Try to add Wikipedia page if method exists
                if hasattr(ami_entry, 'add_wikipedia_page'):
                    ami_entry.add_wikipedia_page(wikipedia_page)
                    enhanced_count += 1
                elif hasattr(dictionary, 'add_wikipedia_page'):
                    dictionary.add_wikipedia_page(ami_entry, wikipedia_page)
                    enhanced_count += 1
        except Exception as e:
            if verbose:
                print(f"  Warning: Could not enhance '{term}' with Wikipedia: {e}")
    
    if verbose:
        print(f"  ✓ Enhanced {enhanced_count}/{len(dictionary.entry_by_term)} entries with Wikipedia")
    
    return dictionary


def convert_dictionary_to_encyclopedia(
    dictionary: AmiDictionary,
    temp_path: Path,
    title: str = None
) -> AmiEncyclopedia:
    """
    Step 3: Convert dictionary to encyclopedia.
    
    Args:
        dictionary: Dictionary to convert
        temp_path: Temporary directory for HTML file
        title: Title for the dictionary (required for validation)
        
    Returns:
        AmiEncyclopedia instance
    """
    # Create HTML dictionary
    html_dict = dictionary.create_html_dictionary()
    
    # Ensure we have a complete HTML document structure
    from amilib.xml_lib import XmlLib
    import lxml.etree as ET
    from amilib.ami_html import HtmlLib
    
    # Get title from dictionary if not provided
    if title is None:
        title = getattr(dictionary, 'title', 'My Encyclopedia')
    
    if hasattr(html_dict, 'tag'):
        # It's an element - check if it's already a complete HTML document
        if html_dict.tag == 'html':
            # Already a complete HTML document - ensure title attribute
            body = html_dict.find('.//body')
            if body is not None:
                dict_div = body.find(".//div[@role='ami_dictionary']")
                if dict_div is not None:
                    if not dict_div.get('title'):
                        dict_div.attrib["title"] = title
            html_content = XmlLib.element_to_string(html_dict, pretty_print=True)
        else:
            # It's just a div or fragment - wrap it in complete HTML structure
            html_root = HtmlLib.create_html_with_empty_head_body()
            body = HtmlLib.get_body(html_root)
            
            # Find or create the dictionary div
            if html_dict.tag == 'div' and html_dict.get('role') == 'ami_dictionary':
                import copy
                dict_div_copy = copy.deepcopy(html_dict)
                # Ensure title attribute
                if not dict_div_copy.get('title'):
                    dict_div_copy.attrib["title"] = title
                body.append(dict_div_copy)
            else:
                # Wrap in a dictionary div
                dict_div = ET.SubElement(body, "div")
                dict_div.attrib["role"] = "ami_dictionary"
                dict_div.attrib["title"] = title
                import copy
                if hasattr(html_dict, '__iter__'):
                    for child in html_dict:
                        dict_div.append(copy.deepcopy(child))
                else:
                    dict_div.append(copy.deepcopy(html_dict))
            
            html_content = XmlLib.element_to_string(html_root, pretty_print=True)
    else:
        # It's already a string - parse it and ensure structure
        from lxml.html import fromstring, tostring
        try:
            parsed = fromstring(html_dict)
            body = parsed.find('.//body')
            if body is None:
                # Wrap in HTML structure
                html_root = HtmlLib.create_html_with_empty_head_body()
                body = HtmlLib.get_body(html_root)
                content_elem = fromstring(f"<div>{html_dict}</div>")
                dict_div = ET.SubElement(body, "div")
                dict_div.attrib["role"] = "ami_dictionary"
                dict_div.attrib["title"] = title
                for child in content_elem:
                    dict_div.append(child)
                html_content = XmlLib.element_to_string(html_root, pretty_print=True)
            else:
                # Ensure dictionary div has title attribute
                dict_div = body.find(".//div[@role='ami_dictionary']")
                if dict_div is not None:
                    if not dict_div.get('title'):
                        dict_div.attrib["title"] = title
                html_content = tostring(parsed, encoding='unicode', pretty_print=True)
        except Exception:
            # Fallback: wrap in complete structure
            html_root = HtmlLib.create_html_with_empty_head_body()
            body = HtmlLib.get_body(html_root)
            dict_div = ET.SubElement(body, "div")
            dict_div.attrib["role"] = "ami_dictionary"
            dict_div.attrib["title"] = title
            dict_div.text = html_dict
            html_content = XmlLib.element_to_string(html_root, pretty_print=True)
    
    # Verify HTML structure before saving
    from lxml.html import fromstring
    try:
        parsed = fromstring(html_content.encode('utf-8'))
        body = parsed.find('.//body')
        if body is not None:
            dict_div = body.find(".//div[@role='ami_dictionary']")
            if dict_div is None:
                # Create dictionary div
                dict_div = ET.SubElement(body, "div")
                dict_div.attrib["role"] = "ami_dictionary"
                dict_div.attrib["title"] = title
                # Move existing content into it
                for child in list(body):
                    if child.tag != 'div' or child.get('role') != 'ami_dictionary':
                        body.remove(child)
                        dict_div.append(child)
            # Ensure title attribute
            if not dict_div.get('title'):
                dict_div.attrib["title"] = title
            # Re-serialize
            html_content = XmlLib.element_to_string(parsed, pretty_print=True)
    except Exception as e:
        # If verification fails, log but continue
        pass
    
    # Save to temporary file
    temp_html_path = Path(temp_path, "temp_dictionary.html")
    temp_html_path.write_text(html_content, encoding='utf-8')
    
    # Load as encyclopedia (create instance first, then call method)
    encyclopedia = AmiEncyclopedia()
    encyclopedia.create_from_html_file(temp_html_path)
    
    return encyclopedia


def add_wikipedia_description_to_entry(
    entry: Dict,
    encyclopedia: AmiEncyclopedia,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Add Wikipedia description to a single entry, extracting first sentence.
    
    Args:
        entry: Entry dictionary to enhance
        encyclopedia: Encyclopedia instance (for lookups)
        verbose: If True, show detailed progress
        
    Returns:
        Dictionary with:
        - success: bool
        - has_definition: bool (first sentence extracted)
        - has_description: bool (full description)
        - wikipedia_url: str or None
        - error: str or None
    """
    from encyclopedia.cli.versioned_editor import (
        add_wikipedia_feature,
        _has_non_empty_description
    )
    
    term = entry.get('term', entry.get('canonical_term', ''))
    result = {
        'success': False,
        'has_definition': False,
        'has_description': False,
        'wikipedia_url': None,
        'error': None
    }
    
    try:
        # Check if already has description
        if _has_non_empty_description(entry) and entry.get('wikipedia_url'):
            result['success'] = True
            result['has_description'] = True
            result['wikipedia_url'] = entry.get('wikipedia_url')
            result['has_definition'] = bool(entry.get('definition_html'))
            return result
        
        # Add Wikipedia feature
        add_wikipedia_feature(entry, encyclopedia)
        
        # Check results
        if entry.get('wikipedia_url'):
            result['success'] = True
            result['wikipedia_url'] = entry.get('wikipedia_url')
            result['has_description'] = bool(entry.get('description_html'))
            result['has_definition'] = bool(entry.get('definition_html'))
            
            # Verify definition_html contains first sentence span
            definition_html = entry.get('definition_html', '')
            if definition_html and 'first_sentence_definition' in definition_html:
                result['has_definition'] = True
        else:
            result['error'] = f"No Wikipedia page found for '{term}'"
            
    except Exception as e:
        result['error'] = str(e)
        if verbose:
            print(f"    Error adding Wikipedia to '{term}': {e}")
    
    return result


def add_wikipedia_descriptions_to_encyclopedia(
    encyclopedia: AmiEncyclopedia,
    batch_size: int = 10,
    verbose: bool = False
) -> Tuple[AmiEncyclopedia, Dict[str, Any]]:
    """
    Step 5: Add Wikipedia descriptions to encyclopedia entries.
    
    Args:
        encyclopedia: Encyclopedia to enhance
        batch_size: Number of entries to process at a time
        verbose: If True, show detailed progress
        
    Returns:
        Tuple of (enhanced_encyclopedia, results_dict)
    """
    entries_list = encyclopedia.entries
    total_entries = len(entries_list)
    
    results = {
        'total': total_entries,
        'successful': 0,
        'with_definitions': 0,
        'with_descriptions': 0,
        'failed': [],
        'no_wikipedia': []
    }
    
    if verbose:
        print(f"\nAdding Wikipedia descriptions to {total_entries} entries...")
        print(f"Processing in batches of {batch_size}...")
    
    # Process in batches
    for batch_start in range(0, total_entries, batch_size):
        batch_end = min(batch_start + batch_size, total_entries)
        batch = entries_list[batch_start:batch_end]
        
        if verbose:
            print(f"  Processing batch {batch_start // batch_size + 1}: entries {batch_start + 1}-{batch_end} of {total_entries}")
        
        for entry in batch:
            result = add_wikipedia_description_to_entry(entry, encyclopedia, verbose)
            
            if result['success']:
                results['successful'] += 1
                if result['has_description']:
                    results['with_descriptions'] += 1
                if result['has_definition']:
                    results['with_definitions'] += 1
            else:
                if result['error'] and 'No Wikipedia page' in result['error']:
                    results['no_wikipedia'].append({
                        'term': entry.get('term', entry.get('canonical_term', 'Unknown')),
                        'error': result['error']
                    })
                else:
                    results['failed'].append({
                        'term': entry.get('term', entry.get('canonical_term', 'Unknown')),
                        'error': result['error']
                    })
        
        if verbose:
            print(f"  ✓ Processed {batch_end}/{total_entries} entries "
                  f"({results['successful']} successful, {results['with_definitions']} with definitions)...")
    
    return encyclopedia, results


def add_image_link_to_entry(
    entry: Dict,
    encyclopedia: AmiEncyclopedia,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Add Wikipedia image link to a single entry.
    
    Args:
        entry: Entry dictionary to enhance
        encyclopedia: Encyclopedia instance
        verbose: If True, show detailed progress
        
    Returns:
        Dictionary with:
        - success: bool
        - has_image_link: bool
        - image_url: str or None
        - error: str or None
    """
    from encyclopedia.cli.versioned_editor import add_images_feature
    
    term = entry.get('term', entry.get('canonical_term', ''))
    result = {
        'success': False,
        'has_image_link': False,
        'image_url': None,
        'error': None
    }
    
    try:
        # Check if already has image
        if entry.get('images') or entry.get('figure_html'):
            result['success'] = True
            result['has_image_link'] = True
            result['image_url'] = entry.get('image_link')
            return result
        
        # Add image feature
        add_images_feature(entry, encyclopedia)
        
        # Check results
        figure_html = entry.get('figure_html')
        image_link = entry.get('image_link')
        
        if figure_html or image_link:
            result['success'] = True
            result['has_image_link'] = True
            
            # Extract URL from figure_html if it's an element
            if figure_html and hasattr(figure_html, 'get'):
                result['image_url'] = figure_html.get('href') or image_link
            else:
                result['image_url'] = image_link
        else:
            result['error'] = f"No images found for '{term}'"
            
    except Exception as e:
        result['error'] = str(e)
        if verbose:
            print(f"    Error adding image to '{term}': {e}")
    
    return result


def add_image_links_to_encyclopedia(
    encyclopedia: AmiEncyclopedia,
    batch_size: int = 10,
    verbose: bool = False
) -> Tuple[AmiEncyclopedia, Dict[str, Any]]:
    """
    Step 8: Add Wikipedia image links to encyclopedia entries.
    
    Args:
        encyclopedia: Encyclopedia to enhance
        batch_size: Number of entries to process at a time
        verbose: If True, show detailed progress
        
    Returns:
        Tuple of (enhanced_encyclopedia, results_dict)
    """
    entries_list = encyclopedia.entries
    total_entries = len(entries_list)
    
    results = {
        'total': total_entries,
        'successful': 0,
        'with_images': 0,
        'failed': [],
        'no_images': []
    }
    
    if verbose:
        print(f"\nAdding image links to {total_entries} entries...")
        print(f"Processing in batches of {batch_size}...")
    
    # Process in batches
    for batch_start in range(0, total_entries, batch_size):
        batch_end = min(batch_start + batch_size, total_entries)
        batch = entries_list[batch_start:batch_end]
        
        if verbose:
            print(f"  Processing batch {batch_start // batch_size + 1}: entries {batch_start + 1}-{batch_end} of {total_entries}")
        
        for entry in batch:
            result = add_image_link_to_entry(entry, encyclopedia, verbose)
            
            if result['success']:
                results['successful'] += 1
                if result['has_image_link']:
                    results['with_images'] += 1
            else:
                if result['error'] and 'No images found' in result['error']:
                    results['no_images'].append({
                        'term': entry.get('term', entry.get('canonical_term', 'Unknown')),
                        'wikipedia_url': entry.get('wikipedia_url', '')
                    })
                else:
                    results['failed'].append({
                        'term': entry.get('term', entry.get('canonical_term', 'Unknown')),
                        'error': result['error']
                    })
        
        if verbose:
            print(f"  ✓ Processed {batch_end}/{total_entries} entries "
                  f"({results['successful']} successful, {results['with_images']} with images)...")
    
    return encyclopedia, results
