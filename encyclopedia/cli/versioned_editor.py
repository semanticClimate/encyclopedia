#!/usr/bin/env python3
"""
Command-line interface for versioned encyclopedia editing.

Supports incremental processing, feature addition, and entry management.
Can also launch Streamlit interface.

Usage:
    # Create encyclopedia from wordlist
    python -m encyclopedia.cli.versioned_editor create --wordlist test/wordlist_a.txt --output test/encyclopedia_a.html
    
    # Process next batch of entries
    python -m encyclopedia.cli.versioned_editor process --input test/encyclopedia_a.html --feature wikipedia --batch-size 10
    
    # Show next unprocessed entry
    python -m encyclopedia.cli.versioned_editor next --input test/encyclopedia_a.html
    
    # Launch Streamlit interface
    python -m encyclopedia.cli.versioned_editor streamlit --input test/encyclopedia_a.html
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, List, Callable, Dict

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from Examples.create_encyclopedia_from_wordlist import create_encyclopedia_from_wordlist


def create_encyclopedia(wordlist_file: Path, output_file: Path, title: str = "Encyclopedia"):
    """Create new encyclopedia from wordlist.
    
    Args:
        wordlist_file: Path to wordlist text file
        output_file: Path to output HTML file
        title: Encyclopedia title
    """
    print(f"Creating encyclopedia from {wordlist_file}...")
    
    # Read wordlist
    if not wordlist_file.exists():
        print(f"Error: Wordlist file not found: {wordlist_file}")
        return 1
    
    terms = []
    with open(wordlist_file, 'r', encoding='utf-8') as f:
        for line in f:
            term = line.strip()
            if term and not term.startswith('#'):
                terms.append(term)
    
    if not terms:
        print(f"Error: No terms found in {wordlist_file}")
        return 1
    
    print(f"Found {len(terms)} terms")
    
    # Create encyclopedia (without Wikipedia descriptions - use 'process' command to add them)
    try:
        encyclopedia = create_encyclopedia_from_wordlist(
            terms, 
            title=title,
            add_wikipedia=False,  # Don't fetch Wikipedia descriptions - use 'process' command instead
            add_images=False
        )
        
        # Save
        print(f"Saving to {output_file}...")
        encyclopedia.save_wiki_normalized_html(output_file)
        
        print(f"✓ Encyclopedia created with {len(encyclopedia.entries)} entries")
        print(f"  Note: Use 'process --feature wikipedia' to add Wikipedia descriptions")
        return 0
        
    except Exception as e:
        print(f"Error creating encyclopedia: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _has_non_empty_description(entry_dict: Dict) -> bool:
    """Check if entry has a non-empty description.
    
    Args:
        entry_dict: Entry dictionary
        
    Returns:
        True if entry has non-empty description HTML
    """
    description_html = entry_dict.get('description_html', '').strip()
    if not description_html:
        return False
    
    # Check if it's just empty tags
    from lxml.html import fromstring
    try:
        desc_root = fromstring(description_html.encode('utf-8'))
        text_content = desc_root.text_content() if hasattr(desc_root, 'text_content') else ''
        return bool(text_content.strip())
    except Exception:
        # If parsing fails, assume it has content
        return True


def _get_wikipedia_page_for_entry(entry_dict: Dict):
    """Get WikipediaPage object for entry.
    
    Args:
        entry_dict: Entry dictionary
        
    Returns:
        WikipediaPage object or None
    """
    from amilib.wikimedia import WikipediaPage
    
    # Try using existing URL first (more efficient)
    wikipedia_url = entry_dict.get('wikipedia_url', '').strip()
    if wikipedia_url:
        try:
            return WikipediaPage.lookup_wikipedia_page_for_url(wikipedia_url)
        except Exception:
            pass
    
    # Fallback to term lookup
    term = entry_dict.get('term', entry_dict.get('canonical_term', ''))
    if term:
        try:
            return WikipediaPage.lookup_wikipedia_page_for_term(term)
        except Exception:
            pass
    
    return None


def _extract_wikidata_id_from_wikipedia_page(wikipedia_page) -> Optional[str]:
    """Extract Wikidata ID from WikipediaPage object.
    
    Args:
        wikipedia_page: WikipediaPage object
        
    Returns:
        Wikidata ID (Q/P format) or None
    """
    try:
        wikidata_url = wikipedia_page.get_wikidata_item()
        if wikidata_url and '/wiki/' in wikidata_url:
            return wikidata_url.split('/wiki/')[-1]
    except Exception:
        pass
    return None


def _filter_wikipedia_messages(text: str) -> bool:
    """Check if text contains Wikipedia error/redirect messages that should be filtered.
    
    Args:
        text: Text to check
        
    Returns:
        True if text should be filtered out (contains error messages)
    """
    if not text:
        return True  # Filter empty text
    
    text_stripped = text.strip()
    if not text_stripped or len(text_stripped) < 10:
        return True  # Filter very short text (likely empty or just whitespace)
    
    text_lower = text_stripped.lower()
    
    # Strong filter patterns (always filter)
    strong_patterns = [
        "other reasons this message may be displayed",
        "this is an accepted version of this page",
        "this is the latest accepted revision",
        "page version status",
    ]
    
    for pattern in strong_patterns:
        if pattern in text_lower:
            return True
    
    # Weak filter patterns (only filter if text is short - likely disambiguation)
    # Longer paragraphs with these patterns might be legitimate content
    weak_patterns = [
        "this page was last edited",
        "you may be looking for",
        "redirected from",
    ]
    
    # Only filter weak patterns if text is short (likely disambiguation message)
    if len(text_stripped) < 150:
        for pattern in weak_patterns:
            if pattern in text_lower:
                return True
        
        # Filter "this article is about" only if it's a short disambiguation message
        if "this article is about" in text_lower and len(text_stripped) < 200:
            # Check if it's clearly a disambiguation (contains "for" and "see")
            if " for " in text_lower and " see " in text_lower:
                return True
    
    return False


def _extract_definition_from_paragraph(para_elem) -> tuple:
    """Extract definition (first sentence) separately from description.
    
    Preserves HTML structure and wraps first sentence in span with class "first_sentence_definition".
    Uses paragraph element from amilib (already filtered and processed).
    
    Args:
        para_elem: Paragraph element from Wikipedia (from amilib's create_first_wikipedia_para)
        
    Returns:
        Tuple of (definition_html, description_html) where:
        - definition_html: First sentence wrapped in <span class="first_sentence_definition">
        - description_html: Full paragraph HTML (preserved with all HTML structure)
    """
    from amilib.xml_lib import XmlLib
    import lxml.etree as ET
    import re
    
    # Get text content
    para_text = para_elem.text_content() if hasattr(para_elem, 'text_content') else ''
    
    # Filter out obvious Wikipedia error messages (safety check)
    # amilib already filters by length, but check for error message patterns
    if _filter_wikipedia_messages(para_text):
        return None, None
    
    # Extract first sentence (ends with period followed by space or end)
    first_sentence_match = re.match(r'^([^.]*\.)(?:\s|$)', para_text)
    
    if first_sentence_match:
        first_sentence_text = first_sentence_match.group(1).strip()
        
        # Create definition span with first sentence
        definition_span = ET.Element("span")
        definition_span.attrib["class"] = "first_sentence_definition"
        definition_span.text = first_sentence_text
        
        # Ensure paragraph has wpage_first_para class (amilib should set this, but ensure it)
        if not para_elem.get('class') or 'wpage_first_para' not in para_elem.get('class', ''):
            para_elem.set('class', 'wpage_first_para')
        
        description_html = XmlLib.element_to_string(para_elem)
        definition_html = XmlLib.element_to_string(definition_span)
        return definition_html, description_html
    
    # If no clear first sentence, return full paragraph as description
    # Ensure paragraph has wpage_first_para class
    if not para_elem.get('class') or 'wpage_first_para' not in para_elem.get('class', ''):
        para_elem.set('class', 'wpage_first_para')
    
    description_html = XmlLib.element_to_string(para_elem)
    return None, description_html


def _get_first_paragraph_html_from_wikipedia_page(wikipedia_page) -> tuple:
    """Get first paragraph HTML from WikipediaPage using amilib methods.
    
    Uses amilib's create_first_wikipedia_para() method which handles filtering
    and extraction. If that fails, falls back to manual extraction using
    amilib's get_main_element() method.
    
    Args:
        wikipedia_page: WikipediaPage object
        
    Returns:
        Tuple of (definition_html, description_html) where:
        - definition_html: First sentence as span (or None)
        - description_html: Full paragraph HTML (or None)
    """
    from amilib.xml_lib import XmlLib
    import lxml.etree as ET
    
    # Primary method: Use amilib's create_first_wikipedia_para() - it handles filtering and extraction
    # This method uses get_main_element() which cleans the page and filters paragraphs
    para_obj = None
    try:
        para_obj = wikipedia_page.create_first_wikipedia_para()
    except Exception as e:
        # If amilib method raises exception, fall back to manual extraction
        pass
    
    if para_obj is not None and para_obj.para_element is not None:
        # Use the paragraph element from amilib (already filtered and processed)
        para_elem = para_obj.para_element
        
        # Extract definition and description from the paragraph
        # The paragraph already has class 'wpage_first_para' set by amilib
        result = _extract_definition_from_paragraph(para_elem)
        # Only return if extraction succeeded (not filtered out)
        if result[0] is not None or result[1] is not None:
            return result
        # If extraction filtered it out, continue to fallback
    
    # Fallback: If create_first_wikipedia_para() fails or returns None para_element,
    # use get_main_element() and extract manually
    # This handles edge cases where amilib's method doesn't find a paragraph
    main_elem = None
    try:
        main_elem = wikipedia_page.get_main_element()
    except Exception as e:
        # If get_main_element fails, return None
        return None, None
    
    if main_elem is None:
        return None, None
    
    # Try to find first valid paragraph in main content
    # Look for paragraphs in the main content area (similar to amilib's logic)
    paragraphs = main_elem.xpath(".//div[@id='mw-content-text']//p | .//main//p")
    
    # Try first few paragraphs (amilib typically checks first 3-5)
    for para_elem in paragraphs[:5]:
        if para_elem is None:
            continue
        
        # Get text content
        para_text = para_elem.text_content() if hasattr(para_elem, 'text_content') else ''
        
        # Apply same filtering as amilib (length check + message filtering)
        # amilib filters paragraphs shorter than ~50 characters
        if not para_text or len(para_text.strip()) < 50:
            continue
        
        # Apply Wikipedia message filtering
        if _filter_wikipedia_messages(para_text):
            continue
        
        # Found valid paragraph - process it
        # Set class to match amilib's standard
        para_elem.set('class', 'wpage_first_para')
        
        # Extract definition and description
        return _extract_definition_from_paragraph(para_elem)
    
    # No valid paragraph found
    return None, None


def add_wikipedia_feature(entry_dict: Dict, encyclopedia: AmiEncyclopedia):
    """Add Wikipedia description to entry using amilib methods.
    
    Uses WikipediaPage.create_first_wikipedia_para() or similar amilib methods
    to extract the first paragraph with proper wpage_first_para class.
    
    Args:
        entry_dict: Entry dictionary
        encyclopedia: Encyclopedia instance (for lookups)
    """
    term = entry_dict.get('term', entry_dict.get('canonical_term', ''))
    if not term:
        return
    
    # Check if already has Wikipedia description - only skip if BOTH description AND URL exist
    # If URL exists but description is missing/empty, we should still try to add it
    has_description = _has_non_empty_description(entry_dict)
    has_url = entry_dict.get('wikipedia_url')
    
    if has_description and has_url:
        print(f"  Entry '{term}' already has Wikipedia description")
        return
    
    # If we have URL but no description, try to re-fetch (might be a redirect/disambiguation issue)
    if has_url and not has_description:
        print(f"  Entry '{term}' has Wikipedia URL but no description, re-fetching...")
    
    # Get Wikipedia page - always try to fetch, even if URL exists
    print(f"  Looking up Wikipedia for '{term}'...")
    wikipedia_page = _get_wikipedia_page_for_entry(entry_dict)
    
    # Track diagnostic information
    entry_dict['wikipedia_page_retrieved'] = False
    entry_dict['first_paragraph_retrieved'] = False
    
    if not wikipedia_page:
        print(f"  ⚠ No Wikipedia page found for '{term}'")
        # If we had a URL but lookup failed, clear it
        if has_url:
            print(f"    Warning: Previous URL {entry_dict.get('wikipedia_url')} is no longer valid")
        return
    
    # Wikipedia page was retrieved
    entry_dict['wikipedia_page_retrieved'] = True
    page_url = wikipedia_page.url if hasattr(wikipedia_page, 'url') else 'N/A'
    original_url = entry_dict.get('wikipedia_url', '')
    
    print(f"  ✓ Wikipedia page retrieved: {page_url}")
    if original_url and original_url != page_url:
        print(f"    DEBUG: URL changed from {original_url} to {page_url} (possible redirect)")
    
    # Check for redirect indicators in the page
    if hasattr(wikipedia_page, 'html_elem') and wikipedia_page.html_elem is not None:
        redirect_indicators = wikipedia_page.html_elem.xpath(".//div[@class='redirectMsg'] | .//span[@class='mw-redirect']")
        if redirect_indicators:
            print(f"    DEBUG: Found redirect indicators in page HTML")
    
    # Save downloaded page HTML for debugging
    try:
        from encyclopedia.utils.resources import Resources
        from pathlib import Path
        debug_dir = Resources.get_temp_dir("debug", "wikipedia_pages")
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        # Create safe filename from term
        safe_term = term.replace(' ', '_').replace('/', '_')[:50]
        debug_file = Path(debug_dir, f"{safe_term}.html")
        
        # Save HTML if html_elem exists
        if hasattr(wikipedia_page, 'html_elem') and wikipedia_page.html_elem is not None:
            from amilib.xml_lib import XmlLib
            html_content = XmlLib.element_to_string(wikipedia_page.html_elem)
            debug_file.write_text(html_content, encoding='utf-8')
            print(f"    DEBUG: Saved downloaded page HTML to: {debug_file}")
        elif hasattr(wikipedia_page, 'html') and wikipedia_page.html:
            debug_file.write_text(wikipedia_page.html, encoding='utf-8')
            print(f"    DEBUG: Saved downloaded page HTML to: {debug_file}")
        else:
            print(f"    DEBUG: No HTML content available to save")
    except Exception as e:
        print(f"    DEBUG: Could not save page HTML: {e}")
    
    # Extract definition and description separately using amilib methods
    definition_html, description_html = _get_first_paragraph_html_from_wikipedia_page(wikipedia_page)
    
    if description_html or definition_html:
        # First paragraph was retrieved
        entry_dict['first_paragraph_retrieved'] = True
        print(f"  ✓ First paragraph retrieved")
        # Ensure description_html has the wpage_first_para class for proper identification
        if description_html and 'wpage_first_para' not in description_html:
            # Parse and add class if missing
            try:
                from lxml.etree import fromstring
                from amilib.xml_lib import XmlLib
                desc_root = fromstring(description_html.encode('utf-8'))
                # Set class on root element if it's a p tag
                if desc_root.tag == 'p':
                    desc_root.set('class', 'wpage_first_para')
                    description_html = XmlLib.element_to_string(desc_root)
                elif desc_root.tag == 'span':
                    # If it's a span, wrap in p with class
                    p_elem = fromstring('<p class="wpage_first_para"></p>')
                    p_elem.append(desc_root)
                    description_html = XmlLib.element_to_string(p_elem)
            except Exception as e:
                print(f"    Warning: Could not ensure wpage_first_para class: {e}")
        
        # Update entry with Wikipedia data
        entry_dict['wikipedia_url'] = getattr(wikipedia_page, 'url', None) or entry_dict.get('wikipedia_url', '')
        
        # Store definition and description separately
        if definition_html:
            entry_dict['definition_html'] = definition_html
        if description_html:
            entry_dict['description_html'] = description_html
        elif definition_html:
            # If only definition, use it as description too
            entry_dict['description_html'] = definition_html
        
        # Get Wikidata ID if available
        if not entry_dict.get('wikidata_id'):
            wikidata_id = _extract_wikidata_id_from_wikipedia_page(wikipedia_page)
            if wikidata_id:
                entry_dict['wikidata_id'] = wikidata_id
        
        print(f"  ✓ Added Wikipedia description for '{term}'")
        page_url = getattr(wikipedia_page, 'url', None) or entry_dict.get('wikipedia_url', 'N/A')
        print(f"    URL: {page_url}")
    else:
        # Wikipedia page retrieved but no paragraph extracted
        entry_dict['first_paragraph_retrieved'] = False
        print(f"  ⚠ No description extracted for '{term}'")
        print(f"    Page URL: {wikipedia_page.url if hasattr(wikipedia_page, 'url') else 'N/A'}")
        print(f"    Wikipedia page retrieved: ✓")
        print(f"    First paragraph retrieved: ✗")
        print(f"    This may indicate:")
        print(f"      - Page exists but has no readable first paragraph")
        print(f"      - Page is a disambiguation or redirect")
        print(f"      - Extraction method failed (check amilib version)")
        # Still save URL even if no description
        entry_dict['wikipedia_url'] = getattr(wikipedia_page, 'url', None) or entry_dict.get('wikipedia_url', '')
        # Clear any empty description_html that might exist
        if not entry_dict.get('description_html') or not _has_non_empty_description(entry_dict):
            entry_dict.pop('description_html', None)
        # Clear any empty description_html that might exist
        if not entry_dict.get('description_html') or not _has_non_empty_description(entry_dict):
            entry_dict.pop('description_html', None)


def _extract_images_from_wikipedia_page(wikipedia_page, verbose: bool = False) -> List:
    """Extract images from WikipediaPage using amilib methods.
    
    Uses amilib's extract_a_elem_with_image_from_infobox() method first,
    then falls back to finding <figure> elements if no infobox image is found.
    This matches the strategy used by amilib's AmiEntry.add_figures_from_wikipedia().
    
    Args:
        wikipedia_page: WikipediaPage object
        verbose: If True, show detailed progress
        
    Returns:
        List of image elements (<a> tags or <figure> elements)
    """
    images = []
    
    # Step 1: Try to get <a> element with image from infobox
    img_elem = wikipedia_page.extract_a_elem_with_image_from_infobox()
    
    if img_elem is not None:
        images.append(img_elem)
        if verbose:
            print(f"    ✓ Found image via amilib extract_a_elem_with_image_from_infobox()")
    else:
        # Step 2: Fallback - look for <figure> elements if no infobox image
        if hasattr(wikipedia_page, 'html_elem') and wikipedia_page.html_elem is not None:
            figures = wikipedia_page.html_elem.xpath(".//figure")
            if len(figures) > 0:
                images.append(figures[0])
                if verbose:
                    print(f"    ✓ Found image via fallback <figure> element")
            elif verbose:
                print(f"    ⚠ No images found (no infobox image, no <figure> elements)")
        elif verbose:
            print(f"    ⚠ No images found (no infobox image, no html_elem available)")
    
    return images


def _fix_image_urls(element):
    """Fix relative image URLs to absolute Wikimedia URLs.
    
    Converts:
    - `/wiki/File:X.jpg` -> `https://en.wikipedia.org/wiki/File:X.jpg`
    - `//upload.wikimedia.org/...` -> `https://upload.wikimedia.org/...`
    - Relative paths -> Absolute Wikipedia URLs
    
    Args:
        element: lxml element containing images
    """
    wikipedia_base = "https://en.wikipedia.org"
    
    # Fix img src attributes (these point to actual image files)
    img_elements = element.xpath(".//img[@src]")
    for img in img_elements:
        src = img.get('src', '')
        if src:
            # Convert protocol-relative URL (//upload.wikimedia.org/...) to https://
            if src.startswith('//'):
                img.set('src', f"https:{src}")
            # Convert relative URL to absolute
            elif not src.startswith('http'):
                if src.startswith('/'):
                    # Absolute path on Wikipedia
                    img.set('src', f"{wikipedia_base}{src}")
                else:
                    # Relative path - prepend Wikipedia base
                    img.set('src', f"{wikipedia_base}/{src}")
        
        # Fix srcset attributes too (for responsive images)
        srcset = img.get('srcset', '')
        if srcset:
            # Replace // with https:// in srcset
            fixed_srcset = srcset.replace('//upload.wikimedia.org', 'https://upload.wikimedia.org')
            img.set('srcset', fixed_srcset)
    
    # Fix a href attributes that point to File: pages or Wikipedia pages
    a_elements = element.xpath(".//a[@href]")
    for a in a_elements:
        href = a.get('href', '')
        if href and not href.startswith('http'):
            # Convert protocol-relative URL
            if href.startswith('//'):
                a.set('href', f"https:{href}")
            # Convert relative Wikipedia URLs
            elif href.startswith('/'):
                a.set('href', f"{wikipedia_base}{href}")
            # Convert relative paths (wiki/File:, File:, etc.)
            elif 'File:' in href or href.startswith('wiki/'):
                if not href.startswith('/'):
                    href = '/' + href
                a.set('href', f"{wikipedia_base}{href}")


def add_images_feature(entry_dict: Dict, encyclopedia: AmiEncyclopedia, verbose: bool = False):
    """Add figures to entry from Wikipedia using _extract_images_from_wikipedia_page().
    
    Uses _extract_images_from_wikipedia_page() which calls amilib's 
    extract_a_elem_with_image_from_infobox() method to extract images.
    
    Args:
        entry_dict: Entry dictionary
        encyclopedia: Encyclopedia instance
        verbose: If True, show detailed progress
    """
    import copy
    
    term = entry_dict.get('term', entry_dict.get('canonical_term', ''))
    
    # Check if already has images or figure_html
    if entry_dict.get('images') or entry_dict.get('figure_html'):
        if verbose:
            print(f"  Entry '{term}' already has images")
        return
    
    # Get Wikipedia page
    if verbose:
        print(f"  Looking up Wikipedia page for '{term}' to extract images...")
    wikipedia_page = _get_wikipedia_page_for_entry(entry_dict)
    if not wikipedia_page:
        if verbose:
            print(f"  ⚠ Entry '{term}' has no Wikipedia page, skipping images")
        return
    
    page_url = getattr(wikipedia_page, 'url', None) or 'N/A'
    if verbose:
        print(f"  ✓ Wikipedia page retrieved: {page_url}")
    
    # Extract images using helper function
    if verbose:
        print(f"  Extracting images for '{term}' using amilib methods...")
    
    try:
        # Use _extract_images_from_wikipedia_page() helper function
        image_elements = _extract_images_from_wikipedia_page(wikipedia_page, verbose=verbose)
        
        if image_elements:
            # Use the first image element
            figure_elem = image_elements[0]
            
            try:
                # Fix relative URLs to absolute (ensure images load correctly)
                _fix_image_urls(figure_elem)
                
                # Store the figure element using copy.deepcopy()
                entry_dict['figure_html'] = copy.deepcopy(figure_elem)
                
                # Extract image_link URL for reference
                # Handle both <a> elements and <figure> elements
                image_url = None
                
                # Try to get href from <a> element (if figure_elem is an <a> tag)
                if hasattr(figure_elem, 'get') and hasattr(figure_elem, 'tag'):
                    if figure_elem.tag == 'a':
                        href = figure_elem.get('href', '')
                        if href:
                            # Ensure it's a full Wikipedia URL
                            if not href.startswith('http'):
                                if href.startswith('/wiki/File:') or href.startswith('/wiki/'):
                                    href = f"https://en.wikipedia.org{href}"
                                elif href.startswith('/'):
                                    href = f"https://en.wikipedia.org{href}"
                            image_url = href
                
                # If no href found, try to find img src in the element (works for both <a> and <figure>)
                if not image_url:
                    img_elem = figure_elem.xpath(".//img[@src]")
                    if img_elem:
                        img_src = img_elem[0].get('src', '')
                        if img_src:
                            image_url = img_src
                    else:
                        # For <figure> elements, also check for <a> tags inside
                        a_elem = figure_elem.xpath(".//a[@href]")
                        if a_elem:
                            href = a_elem[0].get('href', '')
                            if href:
                                if not href.startswith('http'):
                                    if href.startswith('/wiki/File:') or href.startswith('/wiki/'):
                                        href = f"https://en.wikipedia.org{href}"
                                    elif href.startswith('/'):
                                        href = f"https://en.wikipedia.org{href}"
                                image_url = href
                
                if image_url:
                    entry_dict['image_link'] = image_url
                
                if verbose:
                    print(f"  ✓ Added figure for '{term}'")
                    if entry_dict.get('image_link'):
                        print(f"    Link: {entry_dict['image_link']}")
            except Exception as e:
                # If we got an image element but failed to process it, still store it
                # This ensures figure_html is set even if URL fixing fails
                if 'figure_html' not in entry_dict:
                    entry_dict['figure_html'] = copy.deepcopy(figure_elem)
                if verbose:
                    print(f"  ⚠ Warning: Error processing image element for '{term}': {e}")
                    import traceback
                    traceback.print_exc()
        else:
            if verbose:
                print(f"  ⚠ No images found for '{term}'")
                
    except Exception as e:
        if verbose:
            print(f"  ⚠ Error extracting images for '{term}': {e}")
            import traceback
            traceback.print_exc()
        # Re-raise to ensure test failures are visible
        raise


def _extract_entries_from_encyclopedia_html(html_root) -> List[Dict]:
    """Extract entry dictionaries from encyclopedia format HTML.
    
    Args:
        html_root: Parsed HTML root element
        
    Returns:
        List of entry dictionaries
    """
    entries = []
    entry_divs = html_root.xpath(".//div[@role='ami_entry']")
    
    for entry_div in entry_divs:
        entry_dict = {}
        entry_dict['term'] = entry_div.get('term', '')
        entry_dict['canonical_term'] = entry_dict['term']
        entry_dict['wikidata_id'] = entry_div.get('wikidataID') or entry_div.get('wikidataid') or ''
        entry_dict['wikipedia_url'] = ''
        
        # Extract Wikipedia URL from links
        wiki_links = entry_div.xpath(".//a[contains(@href, 'wikipedia.org/wiki/')]")
        if wiki_links:
            entry_dict['wikipedia_url'] = wiki_links[0].get('href', '')
        
        # Extract diagnostic attributes (initialize to False if not present)
        wikipedia_page_retrieved = entry_div.get('data-wikipedia-page-retrieved')
        if wikipedia_page_retrieved:
            entry_dict['wikipedia_page_retrieved'] = wikipedia_page_retrieved.lower() == 'true'
        else:
            entry_dict['wikipedia_page_retrieved'] = False  # Default: not retrieved
        
        first_paragraph_retrieved = entry_div.get('data-first-paragraph-retrieved')
        if first_paragraph_retrieved:
            entry_dict['first_paragraph_retrieved'] = first_paragraph_retrieved.lower() == 'true'
        else:
            entry_dict['first_paragraph_retrieved'] = False  # Default: not retrieved
        
        # Extract description HTML - check multiple possible locations
        description_html = ''
        
        # Try p with class wpage_first_para (amilib standard)
        desc_elems = entry_div.xpath(".//p[@class='wpage_first_para']")
        if desc_elems:
            from amilib.xml_lib import XmlLib
            description_html = XmlLib.element_to_string(desc_elems[0])
        else:
            # Try any p element with actual text content (not empty)
            # Skip p with class mw-empty-elt (empty paragraphs)
            desc_ps = entry_div.xpath(".//p[text() and not(@class='mw-empty-elt')]")
            if desc_ps:
                from amilib.xml_lib import XmlLib
                # Get first non-empty paragraph
                for p_elem in desc_ps:
                    p_text = p_elem.text_content() if hasattr(p_elem, 'text_content') else (p_elem.text or '')
                    if p_text.strip():
                        description_html = XmlLib.element_to_string(p_elem)
                        break
            else:
                # Try getting text content from all p elements
                all_ps = entry_div.xpath(".//p")
                for p_elem in all_ps:
                    # Skip empty paragraphs
                    if p_elem.get('class') == 'mw-empty-elt':
                        continue
                    p_text = p_elem.text_content() if hasattr(p_elem, 'text_content') else (p_elem.text or '')
                    if p_text.strip():
                        from amilib.xml_lib import XmlLib
                        description_html = XmlLib.element_to_string(p_elem)
                        break
        
        entry_dict['description_html'] = description_html
        
        # Extract figure_html/image HTML - check for div[@title="figure"] wrapper (amilib standard)
        figure_html = ''
        figure_divs = entry_div.xpath(".//div[@title='figure']")
        if figure_divs:
            from amilib.xml_lib import XmlLib
            # Get the actual figure element (first child of the wrapper div)
            figure_children = figure_divs[0].xpath('./*')
            if figure_children:
                # Use the first child (the actual figure element: <a> or <figure>)
                figure_html = XmlLib.element_to_string(figure_children[0])
            else:
                # If no children, use the div itself
                figure_html = XmlLib.element_to_string(figure_divs[0])
        else:
            # Fallback: look for <figure> elements directly
            figure_elems = entry_div.xpath(".//figure")
            if figure_elems:
                from amilib.xml_lib import XmlLib
                figure_html = XmlLib.element_to_string(figure_elems[0])
            else:
                # Fallback: look for image links with wikipedia-image-link class
                img_links = entry_div.xpath(".//a[contains(@class, 'wikipedia-image-link')]")
                if img_links:
                    from amilib.xml_lib import XmlLib
                    figure_html = XmlLib.element_to_string(img_links[0])
        
        if figure_html:
            entry_dict['figure_html'] = figure_html
            # Also extract image_link URL if available
            if figure_divs:
                # Try to get href from <a> tag inside figure div
                a_elem = figure_divs[0].xpath(".//a[@href]")
                if a_elem:
                    href = a_elem[0].get('href', '')
                    if href:
                        if not href.startswith('http'):
                            if href.startswith('/wiki/File:') or href.startswith('/wiki/'):
                                href = f"https://en.wikipedia.org{href}"
                            elif href.startswith('/'):
                                href = f"https://en.wikipedia.org{href}"
                        entry_dict['image_link'] = href
                else:
                    # Try to get img src
                    img_elem = figure_divs[0].xpath(".//img[@src]")
                    if img_elem:
                        entry_dict['image_link'] = img_elem[0].get('src', '')
        
        entries.append(entry_dict)
    
    return entries


def _load_encyclopedia_from_html_file(input_file: Path) -> AmiEncyclopedia:
    """Load encyclopedia from HTML file, handling both dictionary and encyclopedia formats.
    
    Args:
        input_file: Path to HTML file
        
    Returns:
        AmiEncyclopedia instance
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is empty or invalid format
    """
    # Validate file exists
    if not input_file.exists():
        raise FileNotFoundError(f"Encyclopedia file not found: {input_file}")
    
    # Validate file has content
    file_size = input_file.stat().st_size
    if file_size == 0:
        raise ValueError(f"File is empty: {input_file}")
    
    # Read and validate HTML content
    html_content = input_file.read_text(encoding='utf-8')
    if not html_content.strip():
        raise ValueError(f"File appears to be empty: {input_file}")
    
    # Parse HTML and validate format
    from lxml.html import fromstring
    try:
        html_root = fromstring(html_content.encode('utf-8'))
        encyclopedia_div = html_root.xpath(".//div[@role='ami_encyclopedia']")
        dictionary_div = html_root.xpath(".//div[@role='ami_dictionary']")
        
        if not encyclopedia_div and not dictionary_div:
            raise ValueError(
                f"File does not contain a valid encyclopedia or dictionary.\n"
                f"Expected div with role='ami_encyclopedia' or role='ami_dictionary'\n"
                f"File: {input_file}\n"
                f"Size: {file_size} bytes\n"
                f"First 500 characters:\n{html_content[:500]}"
            )
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Error parsing HTML file: {e}\nFile: {input_file}\nSize: {file_size} bytes")
    
    # Load encyclopedia based on format
    encyclopedia = AmiEncyclopedia()
    
    if encyclopedia_div:
        # It's encyclopedia format - extract entries directly
        print("Detected encyclopedia format, extracting entries...")
        entries = _extract_entries_from_encyclopedia_html(html_root)
        encyclopedia.entries = entries
        encyclopedia.title = encyclopedia_div[0].get('title', 'Encyclopedia')
        print(f"Extracted {len(entries)} entries from encyclopedia format")
    elif dictionary_div:
        # It's dictionary format - use standard loading
        try:
            encyclopedia.create_from_html_file(input_file)
        except Exception as e:
            raise ValueError(f"Error loading dictionary format: {e}")
    
    return encyclopedia


def _find_entries_needing_feature(encyclopedia: AmiEncyclopedia, feature: str, batch_size: int) -> List[Dict]:
    """Find entries that need a specific feature added.
    
    Args:
        encyclopedia: Encyclopedia instance
        feature: Feature name (e.g., 'wikipedia', 'images')
        batch_size: Maximum number of entries to return
        
    Returns:
        List of entry dictionaries that need the feature
    """
    entries_to_process = []
    
    for entry in encyclopedia.entries:
        # Check if entry needs this feature
        if feature == 'wikipedia':
            # Need Wikipedia if no description_html or no wikipedia_url
            if not _has_non_empty_description(entry) or not entry.get('wikipedia_url'):
                entries_to_process.append(entry)
        elif feature == 'images':
            # Need images if has Wikipedia but no images
            if entry.get('wikipedia_url') and not entry.get('images'):
                entries_to_process.append(entry)
        else:
            # For other features, check if feature is missing
            if feature not in entry.get('features', []):
                entries_to_process.append(entry)
        
        if len(entries_to_process) >= batch_size:
            break
    
    return entries_to_process


def get_feature_handler(feature: str):
    """Get feature handler function.
    
    Args:
        feature: Feature name
        
    Returns:
        Handler function or None
    """
    handlers = {
        'wikipedia': add_wikipedia_feature,
        'images': add_images_feature,
    }
    return handlers.get(feature.lower())


def process_batch(input_file: Path, feature: str, batch_size: int = 10, 
                  feature_handler: Optional[Callable] = None, resume: bool = True):
    """Process batch of entries with feature.
    
    Args:
        input_file: Path to encyclopedia HTML file
        feature: Feature name to add (e.g., 'wikipedia', 'images')
        batch_size: Number of entries to process (default: 10, good for slow connections)
        feature_handler: Function to add feature (if None, uses default handler)
        resume: If True, skip entries that already have the feature (default: True)
    """
    print(f"Processing batch: {batch_size} entries, feature: {feature}")
    if resume:
        print("  (Resume mode: skipping entries that already have this feature)")
    
    # Check file exists
    if not input_file.exists():
        print(f"Error: Encyclopedia file not found: {input_file}")
        print(f"\nPlease create the encyclopedia first:")
        print(f"  python -m encyclopedia.cli.versioned_editor create \\")
        print(f"      --wordlist test/wordlist_a.txt \\")
        print(f"      --output {input_file}")
        return 1
    
    try:
        # Load encyclopedia - handle both dictionary and encyclopedia formats
        try:
            encyclopedia = _load_encyclopedia_from_html_file(input_file)
        except Exception as e:
            print(f"Error loading encyclopedia: {e}")
            return 1
        
        if not encyclopedia.entries:
            print(f"Warning: Encyclopedia loaded but has no entries")
            print(f"This might be a new/empty encyclopedia file")
            return 0
        
        print(f"Loaded encyclopedia with {len(encyclopedia.entries)} entries")
        
        # Find ALL entries needing this feature (for progress calculation)
        all_entries_needing_feature = []
        for entry in encyclopedia.entries:
            if feature == 'wikipedia':
                if not _has_non_empty_description(entry) or not entry.get('wikipedia_url'):
                    all_entries_needing_feature.append(entry)
            elif feature == 'images':
                if entry.get('wikipedia_url') and not entry.get('images') and not entry.get('figure_html'):
                    all_entries_needing_feature.append(entry)
            else:
                if feature not in entry.get('features', []):
                    all_entries_needing_feature.append(entry)
        
        total_needing = len(all_entries_needing_feature)
        
        if not all_entries_needing_feature:
            print(f"✓ All entries already have feature '{feature}'")
            return 0
        
        # Get batch to process
        entries_to_process = all_entries_needing_feature[:batch_size]
        
        print(f"Found {total_needing} entries missing feature '{feature}'")
        print(f"Processing next {len(entries_to_process)} entries...")
        print(f"Progress: {len(encyclopedia.entries) - total_needing}/{len(encyclopedia.entries)} entries complete ({100 * (len(encyclopedia.entries) - total_needing) / len(encyclopedia.entries):.1f}%)")
        
        # Get handler
        if feature_handler:
            handler = feature_handler
        else:
            handler = get_feature_handler(feature)
            if not handler:
                print(f"Error: No handler found for feature '{feature}'")
                print(f"Available features: wikipedia, images")
                return 1
        
        # Process entries
        processed_count = 0
        successful_count = 0
        
        for idx, entry in enumerate(entries_to_process, 1):
            term = entry.get('term', entry.get('canonical_term', 'Unknown'))
            
            # Check if already has feature (resume mode)
            if resume:
                if feature == 'wikipedia':
                    if _has_non_empty_description(entry) and entry.get('wikipedia_url'):
                        print(f"  [{idx}/{len(entries_to_process)}] '{term}' already has Wikipedia, skipping...")
                        continue
                elif feature == 'images':
                    if entry.get('images') or entry.get('figure_html'):
                        print(f"  [{idx}/{len(entries_to_process)}] '{term}' already has images, skipping...")
                        continue
            
            print(f"\n  [{idx}/{len(entries_to_process)}] Processing: {term}")
            
            # Track state before processing
            had_feature_before = False
            if feature == 'wikipedia':
                had_feature_before = _has_non_empty_description(entry) and entry.get('wikipedia_url')
            elif feature == 'images':
                had_feature_before = bool(entry.get('images') or entry.get('figure_html'))
            
            # Add feature
            # Pass verbose=True for images feature to get debug output
            if feature == 'images':
                handler(entry, encyclopedia, verbose=True)
            else:
                handler(entry, encyclopedia)
            processed_count += 1
            
            # Check if feature was added
            has_feature_after = False
            if feature == 'wikipedia':
                has_feature_after = _has_non_empty_description(entry) and entry.get('wikipedia_url')
            elif feature == 'images':
                has_feature_after = bool(entry.get('images') or entry.get('figure_html'))
            
            if has_feature_after and not had_feature_before:
                successful_count += 1
            
            # Show progress
            remaining = total_needing - (len(encyclopedia.entries) - total_needing + idx)
            if remaining > 0:
                progress_pct = 100 * (len(encyclopedia.entries) - total_needing + idx) / len(encyclopedia.entries)
                print(f"    Progress: {len(encyclopedia.entries) - total_needing + idx}/{len(encyclopedia.entries)} ({progress_pct:.1f}%), {remaining} remaining")
        
        # Clear normalized entries cache so save regenerates with our changes
        encyclopedia.normalized_entries = {}
        encyclopedia.synonym_groups = {}
        
        # Save - this will regenerate HTML from the entries
        print(f"\nSaving encyclopedia...")
        try:
            encyclopedia.save_wiki_normalized_html(input_file)
            print(f"✓ Saved to {input_file}")
            
            # Verify what was saved
            print(f"\nVerifying saved entries...")
            try:
                saved_encyclopedia = _load_encyclopedia_from_html_file(input_file)
                entries_with_desc = sum(1 for e in saved_encyclopedia.entries if _has_non_empty_description(e))
                print(f"  Entries with descriptions: {entries_with_desc}/{len(saved_encyclopedia.entries)}")
            except Exception as e:
                print(f"  Warning: Could not verify saved entries: {e}")
            
        except Exception as e:
            print(f"Error saving encyclopedia: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        print(f"\n✓ Processed {processed_count} entries")
        print(f"  Successfully added '{feature}' to {successful_count} entries")
        if total_needing - successful_count > 0:
            remaining = total_needing - successful_count
            print(f"  {remaining} entries still need '{feature}' (run again to continue)")
        return 0
        
    except Exception as e:
        print(f"Error processing batch: {e}")
        import traceback
        traceback.print_exc()
        return 1


def show_next_entry(input_file: Path):
    """Show next unprocessed entry.
    
    Args:
        input_file: Path to encyclopedia HTML file
    """
    print("Finding next unprocessed entry...")
    
    if not input_file.exists():
        print(f"Error: Encyclopedia file not found: {input_file}")
        return 1
    
    try:
        encyclopedia = AmiEncyclopedia()
        encyclopedia.create_from_html_file(input_file)
        
        # Find next unprocessed entry
        # TODO: Implement when versioned system is ready
        unprocessed = []
        for entry in encyclopedia.entries:
            # Check status
            # For now, just show first entry
            unprocessed.append(entry)
            break
        
        if not unprocessed:
            print("No unprocessed entries found")
            return 0
        
        entry = unprocessed[0]
        print("\n" + "=" * 60)
        print("Next Entry:")
        print("=" * 60)
        print(f"Term: {entry.get('term', 'N/A')}")
        print(f"Canonical Term: {entry.get('canonical_term', 'N/A')}")
        print(f"Wikidata ID: {entry.get('wikidata_id', 'N/A')}")
        print(f"Wikipedia URL: {entry.get('wikipedia_url', 'N/A')}")
        if entry.get('description_html'):
            desc = entry.get('description_html', '')[:200]
            print(f"Description: {desc}...")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def show_stats(input_file: Path):
    """Show encyclopedia statistics.
    
    Args:
        input_file: Path to encyclopedia HTML file
    """
    if not input_file.exists():
        print(f"Error: Encyclopedia file not found: {input_file}")
        return 1
    
    try:
        encyclopedia = AmiEncyclopedia()
        encyclopedia.create_from_html_file(input_file)
        
        print("\n" + "=" * 60)
        print("Encyclopedia Statistics")
        print("=" * 60)
        print(f"Title: {encyclopedia.title}")
        print(f"Total Entries: {len(encyclopedia.entries)}")
        
        # Count entries with Wikipedia
        with_wikipedia = sum(1 for e in encyclopedia.entries if e.get('wikipedia_url'))
        print(f"Entries with Wikipedia: {with_wikipedia}")
        
        # Count entries with Wikidata
        with_wikidata = sum(1 for e in encyclopedia.entries if e.get('wikidata_id'))
        print(f"Entries with Wikidata: {with_wikidata}")
        
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def show_status(input_file: Path):
    """Show detailed status and progress for encyclopedia features.
    
    Shows progress for each feature (Wikipedia descriptions, images, etc.)
    and indicates how many entries still need processing.
    
    Args:
        input_file: Path to encyclopedia HTML file
    """
    if not input_file.exists():
        print(f"Error: Encyclopedia file not found: {input_file}")
        return 1
    
    try:
        encyclopedia = _load_encyclopedia_from_html_file(input_file)
        
        if not encyclopedia.entries:
            print("Encyclopedia has no entries")
            return 0
        
        total = len(encyclopedia.entries)
        
        print("\n" + "=" * 60)
        print("Encyclopedia Status")
        print("=" * 60)
        print(f"Title: {encyclopedia.title}")
        print(f"Total Entries: {total}")
        print()
        
        # Wikipedia descriptions
        with_wikipedia_desc = sum(1 for e in encyclopedia.entries 
                                 if _has_non_empty_description(e) and e.get('wikipedia_url'))
        without_wikipedia_desc = total - with_wikipedia_desc
        wikipedia_pct = (with_wikipedia_desc / total * 100) if total > 0 else 0
        
        print("Wikipedia Descriptions:")
        print(f"  ✓ Complete: {with_wikipedia_desc}/{total} ({wikipedia_pct:.1f}%)")
        if without_wikipedia_desc > 0:
            print(f"  ⚠ Missing: {without_wikipedia_desc} entries")
            print(f"  → Run: python -m encyclopedia.cli.versioned_editor process --input {input_file} --feature wikipedia")
        else:
            print(f"  ✓ All entries have Wikipedia descriptions")
        print()
        
        # Images
        with_images = sum(1 for e in encyclopedia.entries 
                         if e.get('images') or e.get('figure_html'))
        without_images = total - with_images
        images_pct = (with_images / total * 100) if total > 0 else 0
        
        print("Images:")
        print(f"  ✓ Complete: {with_images}/{total} ({images_pct:.1f}%)")
        if without_images > 0:
            print(f"  ⚠ Missing: {without_images} entries")
            print(f"  → Run: python -m encyclopedia.cli.versioned_editor process --input {input_file} --feature images")
        else:
            print(f"  ✓ All entries have images")
        print()
        
        # Wikidata IDs
        with_wikidata = sum(1 for e in encyclopedia.entries if e.get('wikidata_id'))
        without_wikidata = total - with_wikidata
        wikidata_pct = (with_wikidata / total * 100) if total > 0 else 0
        
        print("Wikidata IDs:")
        print(f"  ✓ Complete: {with_wikidata}/{total} ({wikidata_pct:.1f}%)")
        if without_wikidata > 0:
            print(f"  ⚠ Missing: {without_wikidata} entries")
        else:
            print(f"  ✓ All entries have Wikidata IDs")
        print()
        
        # Overall progress
        overall_complete = sum(1 for e in encyclopedia.entries 
                              if (_has_non_empty_description(e) and e.get('wikipedia_url')) and
                                 (e.get('images') or e.get('figure_html')) and
                                 e.get('wikidata_id'))
        overall_pct = (overall_complete / total * 100) if total > 0 else 0
        
        print("Overall Progress:")
        print(f"  Fully complete: {overall_complete}/{total} ({overall_pct:.1f}%)")
        print()
        
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def launch_streamlit(input_file: Path, port: int = 8501):
    """Launch Streamlit interface.
    
    Args:
        input_file: Path to encyclopedia HTML file
        port: Port to run Streamlit on
    """
    import subprocess
    
    # Check if streamlit is available
    try:
        import streamlit
    except ImportError:
        print("Error: Streamlit not installed. Install with: pip install streamlit")
        return 1
    
    # Get path to streamlit app
    # Use Path constructor with multiple arguments per style guide
    app_path = Path(Path(__file__).parent.parent, "browser", "app.py")
    
    if not app_path.exists():
        print(f"Error: Streamlit app not found: {app_path}")
        return 1
    
    print(f"Launching Streamlit interface...")
    print(f"Encyclopedia: {input_file}")
    print(f"Port: {port}")
    print(f"Open http://localhost:{port} in your browser")
    
    # Set environment variable for encyclopedia file
    import os
    env = os.environ.copy()
    env['ENCYCLOPEDIA_FILE'] = str(input_file.absolute())
    
    # Launch streamlit
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(port)
    ]
    
    try:
        subprocess.run(cmd, env=env, check=True)
        return 0
    except KeyboardInterrupt:
        print("\nStreamlit stopped.")
        return 0
    except Exception as e:
        print(f"Error launching Streamlit: {e}")
        return 1


def main():
    """Main CLI entry point."""
    from encyclopedia import __version__
    
    parser = argparse.ArgumentParser(
        description="Versioned Encyclopedia Editor - CLI and Streamlit interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create encyclopedia from wordlist
  python -m encyclopedia.cli.versioned_editor create --wordlist test/wordlist_a.txt --output test/encyclopedia_a.html
  
  # Process next batch
  python -m encyclopedia.cli.versioned_editor process --input test/encyclopedia_a.html --feature wikipedia --batch-size 10
  
  # Show next entry
  python -m encyclopedia.cli.versioned_editor next --input test/encyclopedia_a.html
  
  # Show statistics
  python -m encyclopedia.cli.versioned_editor stats --input test/encyclopedia_a.html
  
  # Show detailed status and progress
  python -m encyclopedia.cli.versioned_editor status --input test/encyclopedia_a.html
  
  # Launch Streamlit
  python -m encyclopedia.cli.versioned_editor streamlit --input test/encyclopedia_a.html
        """
    )
    
    parser.add_argument('--version', action='version', version=f'encyclopedia {__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create new encyclopedia from wordlist')
    create_parser.add_argument('--wordlist', type=Path, required=True, help='Wordlist file')
    create_parser.add_argument('--output', type=Path, required=True, help='Output HTML file')
    create_parser.add_argument('--title', type=str, default='Encyclopedia', help='Encyclopedia title')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process batch of entries')
    process_parser.add_argument('--input', type=Path, required=True, help='Input encyclopedia HTML file')
    process_parser.add_argument('--feature', type=str, required=True, help='Feature name to add')
    process_parser.add_argument('--batch-size', type=int, default=10, help='Number of entries to process (default: 10, good for slow connections)')
    process_parser.add_argument('--no-resume', action='store_false', dest='resume', default=True, help='Process all entries, even if they already have the feature')
    
    # Next command
    next_parser = subparsers.add_parser('next', help='Show next unprocessed entry')
    next_parser.add_argument('--input', type=Path, required=True, help='Input encyclopedia HTML file')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show encyclopedia statistics')
    stats_parser.add_argument('--input', type=Path, required=True, help='Input encyclopedia HTML file')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show detailed status and progress for features')
    status_parser.add_argument('--input', type=Path, required=True, help='Input encyclopedia HTML file')
    
    # Streamlit command
    streamlit_parser = subparsers.add_parser('streamlit', help='Launch Streamlit interface')
    streamlit_parser.add_argument('--input', type=Path, required=True, help='Input encyclopedia HTML file')
    streamlit_parser.add_argument('--port', type=int, default=8501, help='Port to run Streamlit on')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    if args.command == 'create':
        return create_encyclopedia(args.wordlist, args.output, args.title)
    elif args.command == 'process':
        return process_batch(args.input, args.feature, args.batch_size, resume=args.resume)
    elif args.command == 'next':
        return show_next_entry(args.input)
    elif args.command == 'stats':
        return show_stats(args.input)
    elif args.command == 'status':
        return show_status(args.input)
    elif args.command == 'streamlit':
        return launch_streamlit(args.input, args.port)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
