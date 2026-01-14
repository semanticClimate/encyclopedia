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
    
    # Create encyclopedia
    try:
        encyclopedia = create_encyclopedia_from_wordlist(terms, title=title)
        
        # Save
        print(f"Saving to {output_file}...")
        encyclopedia.save_wiki_normalized_html(output_file)
        
        print(f"✓ Encyclopedia created with {len(encyclopedia.entries)} entries")
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


def _get_first_paragraph_html_from_wikipedia_page(wikipedia_page) -> Optional[str]:
    """Get first paragraph HTML from WikipediaPage using amilib methods.
    
    Args:
        wikipedia_page: WikipediaPage object
        
    Returns:
        HTML string of first paragraph (with wpage_first_para class) or None
    """
    try:
        # Use create_first_wikipedia_para (returns WikipediaPara object)
        # This is the recommended amilib method
        if hasattr(wikipedia_page, 'create_first_wikipedia_para'):
            para_obj = wikipedia_page.create_first_wikipedia_para()
            if para_obj is not None:
                # WikipediaPara has para_element property that gives us the actual paragraph element
                if hasattr(para_obj, 'para_element') and para_obj.para_element is not None:
                    from amilib.xml_lib import XmlLib
                    # Ensure the paragraph has the wpage_first_para class
                    para_elem = para_obj.para_element
                    if para_elem.get('class') != 'wpage_first_para':
                        para_elem.set('class', 'wpage_first_para')
                    return XmlLib.element_to_string(para_elem)
        
        # Fallback: Try to extract from html_elem directly
        if hasattr(wikipedia_page, 'html_elem') and wikipedia_page.html_elem is not None:
            # Look for first paragraph in the main content area
            first_p = wikipedia_page.html_elem.xpath(".//div[@id='mw-content-text']//p[1]")
            if not first_p:
                # Fallback: just get first <p> anywhere
                first_p = wikipedia_page.html_elem.xpath(".//p[1]")
            
            if first_p:
                from amilib.xml_lib import XmlLib
                para_elem = first_p[0]
                # Ensure it has the wpage_first_para class
                if para_elem.get('class') != 'wpage_first_para':
                    para_elem.set('class', 'wpage_first_para')
                return XmlLib.element_to_string(para_elem)
    except Exception as e:
        print(f"    Warning: Could not extract paragraph using amilib methods: {e}")
    
    return None


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
    
    # Check if already has Wikipedia description
    if _has_non_empty_description(entry_dict) and entry_dict.get('wikipedia_url'):
        print(f"  Entry '{term}' already has Wikipedia description")
        return
    
    # Get Wikipedia page
    print(f"  Looking up Wikipedia for '{term}'...")
    wikipedia_page = _get_wikipedia_page_for_entry(entry_dict)
    
    if not wikipedia_page:
        print(f"  ⚠ No Wikipedia page found for '{term}'")
        return
    
    # Extract first paragraph using amilib methods
    description_html = _get_first_paragraph_html_from_wikipedia_page(wikipedia_page)
    
    if description_html:
        # Update entry with Wikipedia data
        entry_dict['wikipedia_url'] = wikipedia_page.url
        entry_dict['description_html'] = description_html
        
        # Get Wikidata ID if available
        if not entry_dict.get('wikidata_id'):
            wikidata_id = _extract_wikidata_id_from_wikipedia_page(wikipedia_page)
            if wikidata_id:
                entry_dict['wikidata_id'] = wikidata_id
        
        print(f"  ✓ Added Wikipedia description for '{term}'")
        print(f"    URL: {wikipedia_page.url}")
    else:
        print(f"  ⚠ No first paragraph found for '{term}'")
        # Still save URL even if no description
        entry_dict['wikipedia_url'] = wikipedia_page.url


def _extract_images_from_wikipedia_page(wikipedia_page) -> List:
    """Extract images from WikipediaPage using amilib methods.
    
    Args:
        wikipedia_page: WikipediaPage object
        
    Returns:
        List of image elements or image data
    """
    images = []
    
    try:
        # Primary method: extract_a_elem_with_image_from_infobox (returns <a> element with image)
        # This is the recommended amilib method
        if hasattr(wikipedia_page, 'extract_a_elem_with_image_from_infobox'):
            try:
                img_elem = wikipedia_page.extract_a_elem_with_image_from_infobox()
                if img_elem is not None:
                    images.append(img_elem)
                    return images  # Success, return early
            except Exception as e:
                print(f"    Warning: extract_a_elem_with_image_from_infobox failed: {e}")
        
        # Fallback: Try get_infobox and extract images from it
        if hasattr(wikipedia_page, 'get_infobox'):
            try:
                infobox = wikipedia_page.get_infobox()
                if infobox is not None:
                    # Extract image links from infobox (these are <a> tags linking to File: pages)
                    img_links = infobox.xpath(".//a[contains(@href, '/wiki/File:')]")
                    if img_links:
                        images.extend(img_links[:3])  # Limit to 3 from infobox
                        return images  # Success, return early
            except Exception as e:
                print(f"    Warning: get_infobox failed: {e}")
        
        # Fallback: try to find images directly in html_elem
        if hasattr(wikipedia_page, 'html_elem') and wikipedia_page.html_elem is not None:
            try:
                # Look for images in infobox table
                infobox_imgs = wikipedia_page.html_elem.xpath(".//table[contains(@class, 'infobox')]//img")
                if infobox_imgs:
                    # Wrap img tags in <a> tags if needed
                    for img in infobox_imgs[:3]:
                        # Check if img is already inside an <a> tag
                        parent = img.getparent()
                        if parent is not None and parent.tag == 'a':
                            images.append(parent)
                        else:
                            # Create an <a> wrapper
                            import lxml.etree as ET
                            a_elem = ET.Element("a")
                            a_elem.set("href", img.get('src', ''))
                            a_elem.append(img)
                            images.append(a_elem)
                    if images:
                        return images
                
                # If still no images, try main content area (first image)
                if not images:
                    main_images = wikipedia_page.html_elem.xpath(".//div[@id='mw-content-text']//img[1]")
                    if main_images:
                        img = main_images[0]
                        parent = img.getparent()
                        if parent is not None and parent.tag == 'a':
                            images.append(parent)
                        else:
                            import lxml.etree as ET
                            a_elem = ET.Element("a")
                            a_elem.set("href", img.get('src', ''))
                            a_elem.append(img)
                            images.append(a_elem)
            except Exception as e:
                print(f"    Warning: Error extracting from html_elem: {e}")
    
    except Exception as e:
        print(f"    Warning: Error extracting images: {e}")
    
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


def add_images_feature(entry_dict: Dict, encyclopedia: AmiEncyclopedia):
    """Add images to entry from Wikipedia using amilib methods.
    
    Uses WikipediaPage.extract_a_elem_with_image_from_infobox() or similar
    amilib methods to extract images.
    
    Args:
        entry_dict: Entry dictionary
        encyclopedia: Encyclopedia instance
    """
    term = entry_dict.get('term', entry_dict.get('canonical_term', ''))
    
    # Check if already has images or figure_html
    if entry_dict.get('images') or entry_dict.get('figure_html'):
        print(f"  Entry '{term}' already has images")
        return
    
    # Get Wikipedia page
    wikipedia_page = _get_wikipedia_page_for_entry(entry_dict)
    if not wikipedia_page:
        print(f"  Entry '{term}' has no Wikipedia page, skipping images")
        return
    
    # Extract images using amilib methods
    print(f"  Extracting images for '{term}'...")
    images = _extract_images_from_wikipedia_page(wikipedia_page)
    
    if images:
        # Convert image elements to HTML and store as figure_html
        # The encyclopedia save code expects figure_html (element or HTML string)
        from amilib.xml_lib import XmlLib
        import lxml.etree as ET
        import copy
        
        # Get first image (or create a container for multiple)
        first_img = images[0]
        
        try:
            if hasattr(first_img, 'tag'):  # It's an element
                # Create a figure div container
                figure_div = ET.Element("div")
                figure_div.attrib["class"] = "figure"
                
                # Deep copy the element to avoid issues with element trees
                if first_img.tag == 'a':
                    # It's already an <a> element with image - copy it
                    copied_elem = copy.deepcopy(first_img)
                    figure_div.append(copied_elem)
                elif first_img.tag == 'img':
                    # Wrap img in an <a> tag if needed
                    a_elem = ET.SubElement(figure_div, "a")
                    copied_img = copy.deepcopy(first_img)
                    a_elem.append(copied_img)
                else:
                    copied_elem = copy.deepcopy(first_img)
                    figure_div.append(copied_elem)
                
                # Fix image URLs to be absolute Wikimedia URLs
                _fix_image_urls(figure_div)
                
                # Store as figure_html (element) - this is what save_wiki_normalized_html expects
                entry_dict['figure_html'] = figure_div
                
                # Also store as images list for compatibility
                image_htmls = []
                for img in images[:3]:
                    if hasattr(img, 'tag'):
                        image_htmls.append(XmlLib.element_to_string(img))
                if image_htmls:
                    entry_dict['images'] = image_htmls
                
                print(f"  ✓ Added image for '{term}'")
            else:
                # If it's a string, store as HTML string
                entry_dict['figure_html'] = str(first_img)
                entry_dict['images'] = [str(img) for img in images[:3]]
                print(f"  ✓ Added {len(images[:3])} images for '{term}'")
        except Exception as e:
            print(f"  ⚠ Could not convert images to HTML for '{term}': {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"  ⚠ No images found for '{term}'")


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


def process_batch(input_file: Path, feature: str, batch_size: int = 100, 
                  feature_handler: Optional[Callable] = None):
    """Process batch of entries with feature.
    
    Args:
        input_file: Path to encyclopedia HTML file
        feature: Feature name to add (e.g., 'wikipedia', 'images')
        batch_size: Number of entries to process
        feature_handler: Function to add feature (if None, uses default handler)
    """
    print(f"Processing batch: {batch_size} entries, feature: {feature}")
    
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
        
        # Find entries needing this feature
        entries_to_process = _find_entries_needing_feature(encyclopedia, feature, batch_size)
        
        if not entries_to_process:
            print(f"No entries found missing feature '{feature}'")
            return 0
        
        print(f"Found {len(entries_to_process)} entries to process...")
        
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
        for entry in entries_to_process:
            term = entry.get('term', entry.get('canonical_term', 'Unknown'))
            print(f"\nProcessing: {term}")
            
            # Add feature
            handler(entry, encyclopedia)
            processed_count += 1
        
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
        
        print(f"\n✓ Processed {processed_count} entries with feature '{feature}'")
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
    app_path = Path(__file__).parent.parent / "browser" / "app.py"
    
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
  
  # Launch Streamlit
  python -m encyclopedia.cli.versioned_editor streamlit --input test/encyclopedia_a.html
        """
    )
    
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
    process_parser.add_argument('--batch-size', type=int, default=100, help='Number of entries to process')
    
    # Next command
    next_parser = subparsers.add_parser('next', help='Show next unprocessed entry')
    next_parser.add_argument('--input', type=Path, required=True, help='Input encyclopedia HTML file')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show encyclopedia statistics')
    stats_parser.add_argument('--input', type=Path, required=True, help='Input encyclopedia HTML file')
    
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
        return process_batch(args.input, args.feature, args.batch_size)
    elif args.command == 'next':
        return show_next_entry(args.input)
    elif args.command == 'stats':
        return show_stats(args.input)
    elif args.command == 'streamlit':
        return launch_streamlit(args.input, args.port)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
