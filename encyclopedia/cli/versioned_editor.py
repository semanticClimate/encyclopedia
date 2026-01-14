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


def add_wikipedia_feature(entry_dict: Dict, encyclopedia: AmiEncyclopedia):
    """Add Wikipedia description to entry.
    
    Args:
        entry_dict: Entry dictionary
        encyclopedia: Encyclopedia instance (for lookups)
    """
    term = entry_dict.get('term', entry_dict.get('canonical_term', ''))
    if not term:
        return
    
    # Check if already has Wikipedia description
    existing_desc = entry_dict.get('description_html', '').strip()
    existing_url = entry_dict.get('wikipedia_url', '').strip()
    
    # Remove empty paragraphs and whitespace-only content
    if existing_desc:
        # Check if it's just empty tags
        from lxml.html import fromstring
        try:
            desc_root = fromstring(existing_desc.encode('utf-8'))
            text_content = desc_root.text_content() if hasattr(desc_root, 'text_content') else ''
            if not text_content.strip():
                existing_desc = ''  # Treat as empty
        except Exception:
            pass
    
    if existing_desc and existing_url:
        print(f"  Entry '{term}' already has Wikipedia description")
        return
    
    # If we have URL but no description, we still want to add description
    if existing_url and not existing_desc:
        print(f"  Entry '{term}' has Wikipedia URL but no description, adding description...")
    
    try:
        from amilib.wikimedia import WikipediaPage
        
        # Lookup Wikipedia page
        print(f"  Looking up Wikipedia for '{term}'...")
        wikipedia_page = WikipediaPage.lookup_wikipedia_page_for_term(term)
        
        if wikipedia_page:
            # Get first paragraph from HTML element
            first_para = None
            first_para_html = None
            
            # Extract first paragraph from html_elem
            try:
                if hasattr(wikipedia_page, 'html_elem') and wikipedia_page.html_elem is not None:
                    # Look for first paragraph in the main content
                    # Try to find the first <p> in the main content area
                    first_p = wikipedia_page.html_elem.xpath(".//div[@id='mw-content-text']//p[1]")
                    if not first_p:
                        # Fallback: just get first <p> anywhere
                        first_p = wikipedia_page.html_elem.xpath(".//p[1]")
                    
                    if first_p:
                        from amilib.xml_lib import XmlLib
                        first_para_html = XmlLib.element_to_string(first_p[0])
                        # Extract text content
                        first_para = first_p[0].text_content() if hasattr(first_p[0], 'text_content') else (first_p[0].text or '')
                elif hasattr(wikipedia_page, 'get_first_paragraph'):
                    first_para = wikipedia_page.get_first_paragraph()
                elif hasattr(wikipedia_page, 'first_paragraph'):
                    first_para = wikipedia_page.first_paragraph
            except Exception as e:
                print(f"    Warning: Could not extract paragraph: {e}")
            
            if first_para or first_para_html:
                # Update entry with Wikipedia data
                entry_dict['wikipedia_url'] = wikipedia_page.url
                
                # Use HTML if available, otherwise create from text
                if first_para_html:
                    entry_dict['description_html'] = first_para_html
                elif first_para:
                    entry_dict['description_html'] = f"<p>{first_para}</p>"
                
                # Get Wikidata ID if available
                if not entry_dict.get('wikidata_id'):
                    try:
                        if hasattr(wikipedia_page, 'get_wikidata_id'):
                            wikidata_id = wikipedia_page.get_wikidata_id()
                        elif hasattr(wikipedia_page, 'wikidata_id'):
                            wikidata_id = wikipedia_page.wikidata_id
                        elif hasattr(wikipedia_page, 'get_wikidata_item'):
                            wikidata_url = wikipedia_page.get_wikidata_item()
                            if wikidata_url and '/wiki/' in wikidata_url:
                                wikidata_id = wikidata_url.split('/wiki/')[-1]
                            else:
                                wikidata_id = None
                        else:
                            wikidata_id = None
                        
                        if wikidata_id:
                            entry_dict['wikidata_id'] = wikidata_id
                    except Exception:
                        pass  # Wikidata ID is optional
                
                # Get page title
                try:
                    if hasattr(wikipedia_page, 'get_page_title'):
                        page_title = wikipedia_page.get_page_title()
                    elif hasattr(wikipedia_page, 'page_title'):
                        page_title = wikipedia_page.page_title
                    elif hasattr(wikipedia_page, 'title'):
                        page_title = wikipedia_page.title
                    else:
                        page_title = None
                    
                    if page_title and not entry_dict.get('canonical_term'):
                        entry_dict['canonical_term'] = page_title
                except Exception:
                    pass
                
                print(f"  ✓ Added Wikipedia description for '{term}'")
                print(f"    URL: {wikipedia_page.url}")
            else:
                print(f"  ⚠ No first paragraph found for '{term}'")
                # Still save URL even if no description
                entry_dict['wikipedia_url'] = wikipedia_page.url
        else:
            print(f"  ⚠ No Wikipedia page found for '{term}'")
            
    except Exception as e:
        print(f"  ✗ Error adding Wikipedia for '{term}': {e}")


def add_images_feature(entry_dict: Dict, encyclopedia: AmiEncyclopedia):
    """Add images to entry from Wikipedia.
    
    Args:
        entry_dict: Entry dictionary
        encyclopedia: Encyclopedia instance
    """
    wikipedia_url = entry_dict.get('wikipedia_url')
    if not wikipedia_url:
        print(f"  Entry '{entry_dict.get('term')}' has no Wikipedia URL, skipping images")
        return
    
    try:
        from amilib.wikimedia import WikipediaPage
        
        # Get Wikipedia page
        wikipedia_page = WikipediaPage.lookup_wikipedia_page_for_url(wikipedia_url)
        if not wikipedia_page:
            return
        
        # Get images (if available in WikipediaPage API)
        # Note: This depends on WikipediaPage implementation
        images = []
        if hasattr(wikipedia_page, 'get_images'):
            images = wikipedia_page.get_images()
        elif hasattr(wikipedia_page, 'images'):
            images = wikipedia_page.images
        
        if images:
            # Add images to entry
            if 'images' not in entry_dict:
                entry_dict['images'] = []
            entry_dict['images'].extend(images[:3])  # Limit to 3 images
            print(f"  ✓ Added {len(images[:3])} images for '{entry_dict.get('term')}'")
        else:
            print(f"  ⚠ No images found for '{entry_dict.get('term')}'")
            
    except Exception as e:
        print(f"  ✗ Error adding images for '{entry_dict.get('term')}': {e}")


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
        # Check file exists and has content
        if not input_file.exists():
            print(f"Error: File not found: {input_file}")
            return 1
        
        file_size = input_file.stat().st_size
        if file_size == 0:
            print(f"Error: File is empty: {input_file}")
            return 1
        
        # Check file format
        html_content = input_file.read_text(encoding='utf-8')
        if not html_content.strip():
            print(f"Error: File appears to be empty: {input_file}")
            return 1
        
        # Check if it's encyclopedia format or dictionary format
        from lxml.html import fromstring
        try:
            html_root = fromstring(html_content.encode('utf-8'))
            encyclopedia_div = html_root.xpath(".//div[@role='ami_encyclopedia']")
            dictionary_div = html_root.xpath(".//div[@role='ami_dictionary']")
            
            if not encyclopedia_div and not dictionary_div:
                print(f"Error: File does not contain a valid encyclopedia or dictionary.")
                print(f"Expected div with role='ami_encyclopedia' or role='ami_dictionary'")
                print(f"\nFile: {input_file}")
                print(f"Size: {file_size} bytes")
                print(f"\nFirst 500 characters:")
                print(html_content[:500])
                return 1
        except Exception as e:
            print(f"Error parsing HTML file: {e}")
            print(f"\nFile: {input_file}")
            print(f"Size: {file_size} bytes")
            return 1
        
        # Load encyclopedia - handle both dictionary and encyclopedia formats
        encyclopedia = AmiEncyclopedia()
        
        # Check format and load accordingly
        html_root = fromstring(html_content.encode('utf-8'))
        encyclopedia_div = html_root.xpath(".//div[@role='ami_encyclopedia']")
        dictionary_div = html_root.xpath(".//div[@role='ami_dictionary']")
        
        if encyclopedia_div:
            # It's encyclopedia format - extract entries directly
            print("Detected encyclopedia format, extracting entries...")
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
                
                # Try p with class wpage_first_para
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
            
            encyclopedia.entries = entries
            encyclopedia.title = encyclopedia_div[0].get('title', 'Encyclopedia')
            print(f"Extracted {len(entries)} entries from encyclopedia format")
            
        elif dictionary_div:
            # It's dictionary format - use standard loading
            try:
                encyclopedia.create_from_html_file(input_file)
            except Exception as e:
                print(f"Error loading dictionary format: {e}")
                return 1
        else:
            print(f"Error: File does not contain a valid encyclopedia or dictionary.")
            return 1
        
        if not encyclopedia.entries:
            print(f"Warning: Encyclopedia loaded but has no entries")
            print(f"This might be a new/empty encyclopedia file")
            return 0
        
        print(f"Loaded encyclopedia with {len(encyclopedia.entries)} entries")
        
        # Get entries missing this feature
        entries_to_process = []
        for entry in encyclopedia.entries:
            # Check if entry needs this feature
            if feature == 'wikipedia':
                # Need Wikipedia if no description_html or no wikipedia_url
                if not entry.get('description_html') or not entry.get('wikipedia_url'):
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
            saved_encyclopedia = AmiEncyclopedia()
            saved_encyclopedia.create_from_html_file(input_file)
            
            entries_with_desc = sum(1 for e in saved_encyclopedia.entries if e.get('description_html', '').strip())
            print(f"  Entries with descriptions: {entries_with_desc}/{len(saved_encyclopedia.entries)}")
            
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
