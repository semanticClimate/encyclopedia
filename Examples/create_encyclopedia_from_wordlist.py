#!/usr/bin/env python3
"""
Example script: Create a small encyclopedia from a wordlist and delete unwanted entries interactively

This script demonstrates:
1. Creating an encyclopedia from a list of terms
2. Displaying entries for review
3. Interactively selecting entries to delete
4. Saving the cleaned encyclopedia

Usage:
    python create_encyclopedia_from_wordlist.py
    
    Or with custom wordlist:
    python create_encyclopedia_from_wordlist.py --wordlist my_terms.txt
"""

from pathlib import Path
from typing import List, Dict

try:
    from amilib.ami_dict import AmiDictionary
    from encyclopedia.core.encyclopedia import AmiEncyclopedia
except ImportError as e:
    print("=" * 60)
    print("IMPORT ERROR")
    print("=" * 60)
    print(f"Could not import required modules: {e}")
    print("\nTo fix this, run the script from the project root directory:")
    print("  cd /path/to/encyclopedia")
    print("  python Examples/create_encyclopedia_from_wordlist.py")
    print("\nOr install the package in development mode:")
    print("  pip install -e .")
    print("=" * 60)
    raise


def create_encyclopedia_from_wordlist(terms: List[str], title: str = "My Encyclopedia") -> AmiEncyclopedia:
    """
    Create an encyclopedia from a list of terms.
    
    Args:
        terms: List of terms/phrases to include in the encyclopedia
        title: Title for the encyclopedia
        
    Returns:
        AmiEncyclopedia instance with entries created from the terms
    """
    print(f"\n{'='*60}")
    print(f"Creating encyclopedia '{title}' from {len(terms)} terms...")
    print(f"{'='*60}\n")
    
    # Step 1: Create dictionary from words
    print("Step 1: Creating dictionary from terms...")
    
    # Use the class method to properly initialize the dictionary
    # Create a temporary directory for output (required by create_dictionary_from_words)
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create dictionary (basic structure only)
        dictionary, _ = AmiDictionary.create_dictionary_from_words(
            terms=terms,
            title=title,
            wikidata=False,  # We'll get Wikidata IDs from Wikipedia pages
            outdir=temp_path  # Temporary directory (file will be cleaned up)
        )
    
    print(f"  ✓ Created dictionary with {len(dictionary.entry_by_term)} entries")
    
    # Step 2: Enhance with Wikipedia content
    print("\nStep 2: Enhancing with Wikipedia content...")
    print("  (This may take a while as we fetch Wikipedia pages...)")
    
    # Try to add Wikipedia content using available methods
    try:
        # helper: requests.get with retries/backoff to improve reliability
        import requests
        import time

        def requests_get_with_retries(url, headers=None, timeout=10, retries=3, backoff=1.5):
            last_exc = None
            for attempt in range(1, retries + 1):
                try:
                    return requests.get(url, headers=headers, timeout=timeout)
                except Exception as e:
                    last_exc = e
                    if attempt < retries:
                        time.sleep(backoff * attempt)
                    else:
                        raise
        # Try add_wikipedia_from_terms if it exists
        if hasattr(dictionary, 'add_wikipedia_from_terms'):
            dictionary.add_wikipedia_from_terms()
            print(f"  ✓ Enhanced all entries with Wikipedia content")
        else:
            # Fallback: try adding Wikipedia page for each entry
            from amilib.wikimedia import WikipediaPage
            entries_processed = 0
            for term, ami_entry in dictionary.entry_by_term.items():
                try:
                    # Prefer using the Wikipedia REST Summary API (more reliable for summaries and thumbnails)
                    import requests
                    from urllib.parse import quote

                    title_for_api = term.replace(' ', '_')
                    rest_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title_for_api)}"
                    wp_url = None
                    qid = None
                    description_html = None
                    img_url = None

                    try:
                        headers = {'User-Agent': 'ami-encyclopedia/1.0 (https://github.com)'}
                        r = requests_get_with_retries(rest_url, headers=headers, timeout=10, retries=3)
                        if r.status_code == 200:
                            data = r.json()
                            # Canonical page URL
                            wp_url = data.get('content_urls', {}).get('desktop', {}).get('page') or f"https://en.wikipedia.org/wiki/{title_for_api}"
                            # Description HTML (extract_html) or plain extract
                            description_html = data.get('extract_html') or data.get('extract')
                            # Thumbnail or original image
                            thumb = data.get('thumbnail') or {}
                            orig = data.get('originalimage') or {}
                            img_url = orig.get('source') or thumb.get('source')
                        else:
                            # non-200 -> treat as no result
                            wp_url = None
                            description_html = None
                            img_url = None

                    except Exception:
                        # REST API failed; fall back to page HTML parsing if available
                        wp_url = None
                        description_html = None
                        img_url = None

                    # If we didn't get a QID from REST, try the pageprops endpoint
                    if wp_url:
                        try:
                            api_q = f"https://en.wikipedia.org/w/api.php?action=query&titles={quote(title_for_api)}&prop=pageprops&format=json"
                            rq = requests_get_with_retries(api_q, headers={'User-Agent': headers['User-Agent']}, timeout=10, retries=3)
                            if rq.status_code == 200:
                                j = rq.json()
                                pages = j.get('query', {}).get('pages', {})
                                for pid, page in pages.items():
                                    pprops = page.get('pageprops', {})
                                    qid = pprops.get('wikibase_item') or qid
                                    break
                        except Exception:
                            qid = qid

                    # If REST did not return content or returned plain text, fall back to existing HTML parser
                    # or call parse API to retrieve HTML lead section with links
                    if not description_html:
                        # try parse API to get HTML for lead section (section 0)
                        try:
                            parse_api = f"https://en.wikipedia.org/w/api.php?action=parse&page={quote(title_for_api)}&prop=text&section=0&format=json"
                            rp = requests_get_with_retries(parse_api, headers={'User-Agent': 'ami-encyclopedia/1.0 (https://github.com)'}, timeout=10, retries=3)
                            if rp.status_code == 200:
                                pj = rp.json()
                                text_html = pj.get('parse', {}).get('text', {}).get('*')
                                if text_html:
                                    description_html = text_html
                                    wp_url = wp_url or f"https://en.wikipedia.org/wiki/{title_for_api}"
                        except Exception:
                            pass

                    if not (description_html or img_url or qid or wp_url):
                        try:
                            wikipedia_page = WikipediaPage.lookup_wikipedia_page_for_term(term)
                        except Exception:
                            wikipedia_page = None
                        if wikipedia_page:
                            try:
                                wp_url = wp_url or getattr(wikipedia_page, 'url', None)
                                # existing extraction as fallback
                                try:
                                    qid = qid or wikipedia_page.get_qitem_from_wikipedia_page()
                                except Exception:
                                    raw = wikipedia_page.get_wikidata_item() if hasattr(wikipedia_page, 'get_wikidata_item') else None
                                    if raw:
                                        qid = raw.split('/')[-1]
                                try:
                                    first_para = wikipedia_page.create_first_wikipedia_para()
                                    if first_para is not None and hasattr(first_para, 'para_element') and first_para.para_element is not None:
                                        from amilib.xml_lib import XmlLib
                                        description_html = XmlLib.element_to_string(first_para.para_element, pretty_print=False)
                                except Exception:
                                    description_html = description_html
                                # infobox image
                                try:
                                    a_elem = wikipedia_page.extract_a_elem_with_image_from_infobox()
                                    if a_elem is not None:
                                        imgs = a_elem.xpath('.//img') if hasattr(a_elem, 'xpath') else []
                                        if imgs:
                                            src = imgs[0].attrib.get('src') or imgs[0].attrib.get('data-src')
                                            if src:
                                                img_url = src if src.startswith('http') else ('https:' + src if src.startswith('//') else src)
                                except Exception:
                                    pass
                            except Exception:
                                pass

                    # Attach fields directly to the underlying entry element so AmiDictionary/AmiEncyclopedia can pick them up later.
                    try:
                        from lxml import etree as ET

                        entry_elem = ami_entry.element if hasattr(ami_entry, 'element') and getattr(ami_entry, 'element') is not None else ami_entry

                        if wp_url:
                            entry_elem.attrib['wikipedia_url'] = wp_url
                        if qid:
                            entry_elem.attrib['wikidataID'] = qid

                        # Add description paragraph (preserve/convert links to absolute).
                        if description_html:
                            try:
                                from lxml.html import fromstring, fragment_fromstring
                                desc_root = None
                                try:
                                    # parse fragment (may be plain text or full HTML)
                                    desc_root = fromstring(description_html)
                                except Exception:
                                    try:
                                        # sometimes REST returns a fragment without root
                                        desc_root = fragment_fromstring(description_html, create_parent=True)
                                    except Exception:
                                        desc_root = None

                                # If parse produced a container, find the first meaningful <p>
                                desc_node = None
                                if desc_root is not None:
                                    if desc_root.tag in ('p', 'div'):
                                        # find first <p> descendant
                                        p_candidates = desc_root.xpath('.//p')
                                        if p_candidates:
                                            desc_node = p_candidates[0]
                                        else:
                                            # maybe the root is already a <p>
                                            if desc_root.tag == 'p':
                                                desc_node = desc_root
                                            else:
                                                # wrap text
                                                desc_node = ET.Element('p')
                                                desc_node.text = ''.join(desc_root.xpath('.//text()'))
                                    elif desc_root.tag == 'p':
                                        desc_node = desc_root
                                    else:
                                        # fallback: create para with text content
                                        desc_node = ET.Element('p')
                                        desc_node.text = ''.join(desc_root.xpath('.//text()'))
                                else:
                                    desc_node = ET.Element('p')
                                    desc_node.text = description_html

                                # Convert relative wiki links to absolute
                                try:
                                    for a in desc_node.xpath(".//a[@href]"):
                                        href = a.attrib.get('href')
                                        if href and href.startswith('/wiki/'):
                                            a.attrib['href'] = f"https://en.wikipedia.org{href}"
                                        elif href and href.startswith('//'):
                                            a.attrib['href'] = 'https:' + href
                                except Exception:
                                    pass

                                desc_node.attrib['class'] = 'wpage_first_para'
                                entry_elem.append(desc_node)
                            except Exception:
                                try:
                                    p = ET.SubElement(entry_elem, 'p')
                                    p.attrib['class'] = 'wpage_first_para'
                                    p.text = description_html
                                except Exception:
                                    pass

                        # Add image below description. Download and save the image locally under encyclopedia/images/.
                        if img_url:
                            try:
                                # create images dir (use pathlib module to avoid local name binding)
                                import pathlib
                                images_dir = pathlib.Path('encyclopedia') / 'images'
                                images_dir.mkdir(parents=True, exist_ok=True)

                                # determine filename
                                import os
                                parsed_name = img_url.split('/')[-1].split('?')[0]
                                if not parsed_name:
                                    parsed_name = f"{qid or title_for_api}.jpg"
                                # ensure extension
                                if not os.path.splitext(parsed_name)[1]:
                                    parsed_name = parsed_name + '.jpg'

                                local_path = images_dir / parsed_name
                                # download if not already present
                                if not local_path.exists():
                                    try:
                                        rimg = requests_get_with_retries(img_url, headers={'User-Agent': 'ami-encyclopedia/1.0'}, timeout=20, retries=3)
                                        if rimg.status_code == 200:
                                            with open(local_path, 'wb') as fh:
                                                fh.write(rimg.content)
                                    except Exception:
                                        # fallback: do not download
                                        local_path = None
                                # use local path if available, otherwise keep remote
                                img_src = str(local_path).replace('\\', '/') if local_path and local_path.exists() else img_url

                                try:
                                    fig = ET.SubElement(entry_elem, 'figure')
                                    img = ET.SubElement(fig, 'img')
                                    img.attrib['src'] = img_src
                                except Exception:
                                    try:
                                        entry_elem.attrib['image'] = img_src
                                    except Exception:
                                        pass
                            except Exception:
                                try:
                                    entry_elem.attrib['image'] = img_url
                                except Exception:
                                    pass
                    except Exception as e:
                        print(f"  Warning: could not attach fields to entry element for '{term}': {e}")
                    entries_processed += 1
                    if entries_processed % 5 == 0:
                        print(f"  Processed {entries_processed}/{len(dictionary.entry_by_term)} entries...")
                except Exception as e:
                    print(f"  Warning: Could not fetch Wikipedia page for '{term}': {e}")
            print(f"  ✓ Enhanced {entries_processed} entries with Wikipedia content")
    except Exception as e:
        print(f"  Warning: Could not add Wikipedia content: {e}")
        print("  Continuing without Wikipedia content...")
    
    # Step 3: Create HTML dictionary and save to temporary file
    print("\nStep 3: Creating HTML dictionary...")
    html_dict = dictionary.create_html_dictionary()
    
    # Ensure we have a complete HTML document structure
    from amilib.xml_lib import XmlLib
    import lxml.etree as ET
    from amilib.ami_html import HtmlLib
    
    if hasattr(html_dict, 'tag'):
        # It's an element - check if it's already a complete HTML document
        if html_dict.tag == 'html':
            # Already a complete HTML document - ensure it has the required structure
            body = html_dict.find('.//body')
            if body is not None:
                dict_div = body.find(".//div[@role='ami_dictionary']")
                if dict_div is not None:
                    # Ensure it has title attribute
                    if not dict_div.get('title'):
                        dict_div.attrib["title"] = title
                else:
                    # No dictionary div found - this shouldn't happen but handle it
                    print("  Warning: HTML document doesn't have dictionary div, creating one...")
                    dict_div = ET.SubElement(body, "div")
                    dict_div.attrib["role"] = "ami_dictionary"
                    dict_div.attrib["title"] = title
            html_content = XmlLib.element_to_string(html_dict, pretty_print=True)
        else:
            # It's just a div or fragment - wrap it in complete HTML structure
            html_root = HtmlLib.create_html_with_empty_head_body()
            body = HtmlLib.get_body(html_root)
            
            # Find or create the dictionary div
            if html_dict.tag == 'div' and html_dict.get('role') == 'ami_dictionary':
                # Ensure it has the title attribute
                if not html_dict.get('title'):
                    html_dict.attrib["title"] = title
                # Create a deep copy to avoid modifying the original
                import copy
                dict_div_copy = copy.deepcopy(html_dict)
                # Copy the dictionary div to the body
                body.append(dict_div_copy)
            else:
                # Wrap in a dictionary div
                dict_div = ET.SubElement(body, "div")
                dict_div.attrib["role"] = "ami_dictionary"
                dict_div.attrib["title"] = title
                # If html_dict is a div with entries, append its children
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
            # Check if it has the required structure
            body = parsed.find('.//body')
            if body is None:
                # Wrap in HTML structure
                html_root = HtmlLib.create_html_with_empty_head_body()
                body = HtmlLib.get_body(html_root)
                # Parse the string content and add to body
                content_elem = fromstring(f"<div>{html_dict}</div>")
                dict_div = ET.SubElement(body, "div")
                dict_div.attrib["role"] = "ami_dictionary"
                dict_div.attrib["title"] = title
                for child in content_elem:
                    dict_div.append(child)
                html_content = XmlLib.element_to_string(html_root, pretty_print=True)
            else:
                # Check for dictionary div
                dict_div = body.find(".//div[@role='ami_dictionary']")
                if dict_div is None:
                    # Wrap content in dictionary div
                    dict_div = ET.SubElement(body, "div")
                    dict_div.attrib["role"] = "ami_dictionary"
                    dict_div.attrib["title"] = title
                    # Move existing content
                    for child in list(body):
                        if child.tag != 'div' or child.get('role') != 'ami_dictionary':
                            dict_div.append(child)
                else:
                    # Ensure title attribute
                    if not dict_div.get('title'):
                        dict_div.attrib["title"] = title
                html_content = tostring(parsed, encoding='unicode', pretty_print=True)
        except Exception as e:
            print(f"  Warning: Could not parse HTML string: {e}")
            # Fallback: wrap in complete structure
            html_root = HtmlLib.create_html_with_empty_head_body()
            body = HtmlLib.get_body(html_root)
            dict_div = ET.SubElement(body, "div")
            dict_div.attrib["role"] = "ami_dictionary"
            dict_div.attrib["title"] = title
            dict_div.text = html_dict
            html_content = XmlLib.element_to_string(html_root, pretty_print=True)
    
    # Verify and fix HTML structure before saving
    from lxml.html import fromstring
    try:
        parsed = fromstring(html_content.encode('utf-8'))
        body = parsed.find('.//body')
        if body is not None:
            dict_div = body.find(".//div[@role='ami_dictionary']")
            if dict_div is None or not dict_div.get('title'):
                # Fix the structure
                if dict_div is None:
                    # Create dictionary div
                    dict_div = ET.SubElement(body, "div")
                    dict_div.attrib["role"] = "ami_dictionary"
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
        print(f"  Warning: Could not verify HTML structure: {e}")
    
    # Save to temporary file (create_from_html_file expects a file path)
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
        temp_html_path = Path(temp_file.name)
        temp_file.write(html_content)
    
    print("  ✓ HTML dictionary created")
    
    # Step 4: Create encyclopedia from HTML file
    print("\nStep 4: Creating encyclopedia from HTML dictionary...")
    encyclopedia = AmiEncyclopedia(title=title)
    encyclopedia.create_from_html_file(temp_html_path)
    
    # Clean up temporary file
    try:
        temp_html_path.unlink()
    except Exception:
        pass  # Ignore cleanup errors
    print(f"  ✓ Encyclopedia created with {len(encyclopedia.entries)} entries")
    
    # Step 5: Normalize by Wikidata ID
    print("\nStep 5: Normalizing entries by Wikidata ID...")
    # Before normalization: harmonize wikidata IDs for entries that point to the same Wikipedia URL.
    # This merges synonyms that resolve to the same wiki page even if their QIDs differ or are missing.
    try:
        url_to_q = {}
        for e in encyclopedia.entries:
            url = e.get('wikipedia_url') or e.get('wikipedia_url')
            q = e.get('wikidata_id')
            if url and q:
                # prefer first seen QID for this URL
                if url not in url_to_q:
                    url_to_q[url] = q

        # Assign canonical QID to entries that share the same wikipedia_url but lack or differ in wikidata_id
        for e in encyclopedia.entries:
            url = e.get('wikipedia_url')
            if url and url in url_to_q:
                e['wikidata_id'] = url_to_q[url]
    except Exception:
        pass

    encyclopedia.normalize_by_wikidata_id()
    print("  ✓ Entries normalized")
    
    # Step 6: Merge synonyms
    print("\nStep 6: Merging synonyms...")
    encyclopedia.merge()
    print("  ✓ Synonyms merged")
    
    print(f"\n{'='*60}")
    print(f"Encyclopedia creation complete!")
    print(f"{'='*60}\n")
    
    return encyclopedia


def display_entry(entry: Dict, index: int) -> None:
    """Display a single entry in a formatted way."""
    term = entry.get('term', entry.get('search_term', 'N/A'))
    wikidata_id = entry.get('wikidata_id', '')
    wikipedia_url = entry.get('wikipedia_url', '')
    description = entry.get('description_html', '')
    
    # Truncate description for display
    if description:
        # Remove HTML tags for display
        import re
        text_only = re.sub(r'<[^>]+>', '', description)
        if len(text_only) > 150:
            text_only = text_only[:150] + "..."
    else:
        text_only = "(No description available)"
    
    print(f"\n  [{index}] {term}")
    if wikidata_id:
        print(f"      Wikidata ID: {wikidata_id}")
    if wikipedia_url:
        print(f"      Wikipedia: {wikipedia_url}")
    print(f"      Description: {text_only}")


def display_all_entries(encyclopedia: AmiEncyclopedia) -> None:
    """Display all entries in the encyclopedia."""
    print(f"\n{'='*60}")
    print(f"Encyclopedia Entries ({len(encyclopedia.entries)} total)")
    print(f"{'='*60}")
    
    for idx, entry in enumerate(encyclopedia.entries, 1):
        display_entry(entry, idx)
    
    print(f"\n{'='*60}\n")


def interactive_delete_entries(encyclopedia: AmiEncyclopedia) -> AmiEncyclopedia:
    """
    Interactively allow user to delete unwanted entries.
    
    Args:
        encyclopedia: AmiEncyclopedia instance
        
    Returns:
        AmiEncyclopedia instance with deleted entries removed
    """
    print(f"\n{'='*60}")
    print("Interactive Entry Deletion")
    print(f"{'='*60}\n")
    print("You can now review entries and delete unwanted ones.")
    print("Commands:")
    print("  - Enter entry numbers (comma-separated) to delete them")
    print("  - Enter 'all' to delete all entries")
    print("  - Enter 'skip' or 'done' to finish without deleting")
    print("  - Enter 'show' to display all entries again")
    print("  - Enter 'stats' to show statistics")
    print()
    
    while True:
        # Display current entries
        display_all_entries(encyclopedia)
        
        # Get user input
        user_input = input("Enter entry numbers to delete (or 'done'/'skip' to finish, 'show' to refresh, 'stats' for statistics): ").strip()
        
        if user_input.lower() in ['done', 'skip', 'quit', 'exit', 'q']:
            print("\nFinishing deletion process...")
            break
        
        if user_input.lower() == 'show':
            continue  # Will display entries again at start of loop
        
        if user_input.lower() == 'stats':
            stats = encyclopedia.get_statistics()
            print(f"\n  Statistics:")
            print(f"    Total entries: {stats['total_entries']}")
            print(f"    Normalized groups: {stats['normalized_groups']}")
            print(f"    Total synonyms: {stats['total_synonyms']}")
            print(f"    Compression ratio: {stats['compression_ratio']:.2f}\n")
            continue
        
        if user_input.lower() == 'all':
            confirm = input("  Are you sure you want to delete ALL entries? (yes/no): ").strip().lower()
            if confirm == 'yes':
                encyclopedia.entries = []
                print("  ✓ All entries deleted")
                break
            else:
                print("  Cancelled")
                continue
        
        # Parse entry numbers
        try:
            # Split by comma and convert to integers
            indices_to_delete = [int(x.strip()) for x in user_input.split(',')]
            
            # Validate indices
            valid_indices = [idx for idx in indices_to_delete if 1 <= idx <= len(encyclopedia.entries)]
            
            if not valid_indices:
                print("  Error: No valid entry numbers provided")
                continue
            
            # Show which entries will be deleted
            print(f"\n  Entries to delete:")
            for idx in valid_indices:
                entry = encyclopedia.entries[idx - 1]
                term = entry.get('term', entry.get('search_term', 'N/A'))
                print(f"    [{idx}] {term}")
            
            confirm = input(f"\n  Delete {len(valid_indices)} entry/entries? (yes/no): ").strip().lower()
            
            if confirm == 'yes':
                # Delete entries (in reverse order to maintain indices)
                deleted_terms = []
                for idx in sorted(valid_indices, reverse=True):
                    entry = encyclopedia.entries[idx - 1]
                    term = entry.get('term', entry.get('search_term', 'N/A'))
                    deleted_terms.append(term)
                    del encyclopedia.entries[idx - 1]
                
                print(f"  ✓ Deleted {len(deleted_terms)} entries:")
                for term in deleted_terms:
                    print(f"      - {term}")
                
                # Re-normalize after deletion
                if encyclopedia.entries:
                    print("\n  Re-normalizing entries...")
                    encyclopedia.normalize_by_wikidata_id()
                    encyclopedia.merge()
                    print("  ✓ Entries re-normalized")
                else:
                    print("\n  Warning: No entries remaining!")
                    break
            else:
                print("  Cancelled")
        
        except ValueError:
            print("  Error: Invalid input. Please enter numbers separated by commas.")
        except Exception as e:
            print(f"  Error: {e}")
    
    return encyclopedia


def save_encyclopedia(encyclopedia: AmiEncyclopedia, output_file: Path) -> None:
    """Save encyclopedia to HTML file.
    
    Note: This operation may make network requests to check disambiguation pages,
    which can take time or hang if there are network issues. Press Ctrl+C to cancel.
    
    Args:
        encyclopedia: AmiEncyclopedia instance to save
        output_file: Path to save the HTML file
    """
    print(f"\n{'='*60}")
    print(f"Saving encyclopedia to: {output_file}")
    print(f"{'='*60}\n")
    print("  Note: This may take a while as it checks disambiguation pages.")
    print("  If it hangs, press Ctrl+C to cancel and try again.\n")
    
    try:
        encyclopedia.save_wiki_normalized_html(output_file)
        print(f"✓ Encyclopedia saved successfully!")
        print(f"  File: {output_file}")
        print(f"  Entries: {len(encyclopedia.entries)}")
    except KeyboardInterrupt:
        print("\n  Save operation interrupted by user (Ctrl+C).")
        print("  Partial file may have been created.")
        raise
    except Exception as e:
        print(f"\n  Error saving encyclopedia: {e}")
        print("  This may be due to network timeouts when checking disambiguation pages.")
        print("  Try running again, or check your network connection.")
        raise


def main():
    """Main function to run the example."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create encyclopedia from wordlist and delete unwanted entries interactively"
    )
    parser.add_argument(
        '--wordlist',
        type=str,
        help='Path to text file with one term per line (default: uses example terms)'
    )
    parser.add_argument(
        '--title',
        type=str,
        default='My Encyclopedia',
        help='Title for the encyclopedia (default: "My Encyclopedia")'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output HTML file path (default: encyclopedia_output.html)'
    )
    parser.add_argument(
        '--skip-deletion',
        action='store_true',
        help='Skip interactive deletion step'
    )
    
    args = parser.parse_args()
    
    # Get terms
    if args.wordlist:
        wordlist_path = Path(args.wordlist)
        if not wordlist_path.exists():
            print(f"Error: Wordlist file not found: {wordlist_path}")
            return
        terms = [line.strip() for line in wordlist_path.read_text().splitlines() if line.strip()]
        print(f"Loaded {len(terms)} terms from {wordlist_path}")
    else:
        # Use example terms
        terms = [
            "climate change",
            "greenhouse gas",
            "carbon dioxide",
            "global warming",
            "renewable energy",
            "fossil fuels",
            "methane",
            "IPCC",
            "greenhouse effect",
            "atmosphere"
        ]
        print(f"Using example terms: {len(terms)} terms")
    
    # Create encyclopedia
    try:
        encyclopedia = create_encyclopedia_from_wordlist(terms, title=args.title)
    except Exception as e:
        print(f"\nError creating encyclopedia: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Interactive deletion
    if not args.skip_deletion:
        try:
            encyclopedia = interactive_delete_entries(encyclopedia)
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Saving current state...")
        except Exception as e:
            print(f"\nError during deletion: {e}")
            import traceback
            traceback.print_exc()
    
    # Save encyclopedia
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = Path("encyclopedia_output.html")
    
    try:
        save_encyclopedia(encyclopedia, output_file)
    except Exception as e:
        print(f"\nError saving encyclopedia: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"\n{'='*60}")
    print("Done!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
