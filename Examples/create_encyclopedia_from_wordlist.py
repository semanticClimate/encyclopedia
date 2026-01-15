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
    from encyclopedia.utils.resources import Resources
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


def create_encyclopedia_from_wordlist(
    terms: List[str], 
    title: str = "My Encyclopedia",
    add_wikipedia: bool = True,
    add_images: bool = False,
    batch_size: int = 10,
    validate: bool = True,
    verbose: bool = False
) -> AmiEncyclopedia:
    """
    Create an encyclopedia from a list of terms.
    
    Args:
        terms: List of terms/phrases to include in the encyclopedia
        title: Title for the encyclopedia
        add_wikipedia: If True, automatically add Wikipedia descriptions (default: True)
        add_images: If True, automatically add images from Wikipedia (default: False, can be slow)
        batch_size: Number of entries to process at a time (default: 10, good for slow connections)
        validate: If True, validate results at the end (default: True)
        verbose: If True, show detailed progress (default: False)
        
    Returns:
        AmiEncyclopedia instance with entries created from the terms
    """
    from encyclopedia.utils.encyclopedia_builder import (
        create_dictionary_from_terms,
        enhance_dictionary_with_wikipedia,
        convert_dictionary_to_encyclopedia,
        add_wikipedia_descriptions_to_encyclopedia,
        add_image_links_to_encyclopedia
    )
    from encyclopedia.utils.validation import (
        validate_encyclopedia_completeness,
        print_validation_report
    )
    
    print(f"\n{'='*60}")
    print(f"Creating encyclopedia '{title}' from {len(terms)} terms...")
    print(f"{'='*60}\n")
    
    # Create temporary directory
    temp_path = Resources.get_temp_dir("examples", "create_encyclopedia_from_wordlist")
    temp_path.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Create dictionary from words
    print("Step 1: Creating dictionary from terms...")
    dictionary = create_dictionary_from_terms(terms, title, temp_path)
    print(f"  ✓ Created dictionary with {len(dictionary.entry_by_term)} entries")
    
    # Step 2: Enhance with Wikipedia content (if requested)
    if add_wikipedia:
        print("\nStep 2: Enhancing with Wikipedia content...")
        dictionary = enhance_dictionary_with_wikipedia(dictionary, verbose=verbose)
    else:
        print("\nStep 2: Skipping Wikipedia content (--no-wikipedia flag)")
    
    # Step 3: Convert dictionary to encyclopedia
    print("\nStep 3: Converting dictionary to encyclopedia...")
    temp_html_path = Path(temp_path, "temp_dictionary.html")
    encyclopedia = convert_dictionary_to_encyclopedia(dictionary, temp_path, title=title)
    
    # Clean up temporary file
    try:
        temp_html_path.unlink()
    except Exception:
        pass  # Ignore cleanup errors
    print(f"  ✓ Encyclopedia created with {len(encyclopedia.entries)} entries")
    
    # Step 4: Normalize by Wikidata ID
    print("\nStep 4: Normalizing entries by Wikidata ID...")
    encyclopedia.normalize_by_wikidata_id()
    print("  ✓ Entries normalized")
    
    # Step 5: Merge synonyms
    print("\nStep 5: Merging synonyms...")
    encyclopedia.merge()
    print("  ✓ Synonyms merged")
    
    # Step 6: Add Wikipedia descriptions if requested (after encyclopedia creation)
    # This ensures descriptions are properly added even if dictionary conversion lost them
    wikipedia_results = None
    if add_wikipedia:
        print("\nStep 6: Adding Wikipedia descriptions to encyclopedia entries...")
        encyclopedia, wikipedia_results = add_wikipedia_descriptions_to_encyclopedia(
            encyclopedia, batch_size=batch_size, verbose=verbose
        )
        print(f"  ✓ Added Wikipedia descriptions: {wikipedia_results['successful']}/{wikipedia_results['total']} successful")
        print(f"    - {wikipedia_results['with_definitions']} with definitions (first sentences)")
        print(f"    - {wikipedia_results['with_descriptions']} with descriptions")
        if wikipedia_results['no_wikipedia']:
            print(f"    - {len(wikipedia_results['no_wikipedia'])} terms not found in Wikipedia")
    
    # Step 7: Add images if requested
    image_results = None
    if add_images:
        print("\nStep 7: Adding image links from Wikipedia...")
        encyclopedia, image_results = add_image_links_to_encyclopedia(
            encyclopedia, batch_size=batch_size, verbose=verbose
        )
        print(f"  ✓ Added image links: {image_results['successful']}/{image_results['total']} successful")
        print(f"    - {image_results['with_images']} entries with images")
        if image_results['no_images']:
            print(f"    - {len(image_results['no_images'])} entries without images")
    else:
        print("\nStep 7: Skipping images (use --add-images to enable)")
    
    # Step 8: Validate results
    if validate:
        print("\nStep 8: Validating encyclopedia completeness...")
        validation_results = validate_encyclopedia_completeness(encyclopedia)
        print_validation_report(validation_results, verbose=verbose)
    
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
    synonyms = entry.get('synonyms', [])
    
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
    
    # Show synonyms if this is a merged entry
    if synonyms and len(synonyms) > 1:
        other_synonyms = [s for s in synonyms if s != term]
        if other_synonyms:
            print(f"      Synonyms: {', '.join(other_synonyms)}")
    
    # Show links with spacing
    links_parts = []
    if wikipedia_url:
        links_parts.append(f"Wikipedia: {wikipedia_url}")
    else:
        links_parts.append("Wikipedia: (Not found)")
    
    if wikidata_id and wikidata_id not in ('', 'no_wikidata_id', 'invalid_wikidata_id'):
        links_parts.append(f"Wikidata: {wikidata_id}")
    else:
        links_parts.append("Wikidata: (Not found)")
    
    # Print links with spacing between them
    if links_parts:
        print(f"      {links_parts[0]}")
        if len(links_parts) > 1:
            print(f"      {links_parts[1]}")
    
    print(f"      Description: {text_only}")


def display_all_entries(encyclopedia: AmiEncyclopedia) -> None:
    """Display all entries in the encyclopedia."""
    print(f"\n{'='*60}")
    print(f"Encyclopedia Entries ({len(encyclopedia.entries)} total)")
    
    # Count entries with/without Wikipedia
    with_wikipedia = sum(1 for e in encyclopedia.entries if e.get('wikipedia_url'))
    without_wikipedia = len(encyclopedia.entries) - with_wikipedia
    
    if without_wikipedia > 0:
        print(f"  ({with_wikipedia} with Wikipedia, {without_wikipedia} without)")
    
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
    parser.add_argument(
        '--add-wikipedia',
        action='store_true',
        default=True,
        help='Add Wikipedia descriptions (default: True)'
    )
    parser.add_argument(
        '--no-wikipedia',
        action='store_false',
        dest='add_wikipedia',
        help='Skip Wikipedia descriptions'
    )
    parser.add_argument(
        '--add-images',
        action='store_true',
        default=False,
        help='Add images from Wikipedia (default: False, can be slow)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of entries to process at a time (default: 10, good for slow connections)'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        default=True,
        help='Validate encyclopedia completeness at the end (default: True)'
    )
    parser.add_argument(
        '--no-validate',
        action='store_false',
        dest='validate',
        help='Skip validation at the end'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        default=False,
        help='Show detailed progress and validation reports (default: False)'
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
            "atmosphere",
            "cutx",
            "Methane",
        ]
        print(f"Using example terms: {len(terms)} terms")
    
    # Create encyclopedia
    try:
        encyclopedia = create_encyclopedia_from_wordlist(
            terms, 
            title=args.title,
            add_wikipedia=args.add_wikipedia,
            add_images=args.add_images,
            batch_size=args.batch_size,
            validate=args.validate,
            verbose=args.verbose
        )
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
    