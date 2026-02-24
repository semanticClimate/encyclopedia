#!/usr/bin/env python3
"""
Script demonstrating how to add entries from Wikipedia search.

Usage:
    python Examples/edit_encyclopedia_add_from_wikipedia.py --input my_encyclopedia.html --output edited_encyclopedia.html --term "quantum mechanics"
"""

import argparse
from pathlib import Path

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources


def main():
    parser = argparse.ArgumentParser(description="Add entries from Wikipedia to encyclopedia")
    parser.add_argument('--input', type=str, required=True, help='Input encyclopedia HTML file')
    parser.add_argument('--output', type=str, required=True, help='Output encyclopedia HTML file')
    parser.add_argument('--term', type=str, help='Term to search on Wikipedia and add')
    parser.add_argument('--no-check-duplicates', action='store_true', help='Skip duplicate checking')
    
    args = parser.parse_args()
    
    input_file = Path(args.input)
    output_file = Path(args.output)
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return 1
    
    # Load encyclopedia
    print(f"Loading encyclopedia from {input_file}...")
    encyclopedia = AmiEncyclopedia()
    encyclopedia.create_from_html_file(input_file)
    
    print(f"Loaded {len(encyclopedia.entries)} entries")
    
    if not args.term:
        print("\nUsage: --term <term> to add an entry from Wikipedia")
        print("Example: --term 'quantum mechanics'")
        return 0
    
    # Add entry from Wikipedia
    print(f"\nSearching Wikipedia for: {args.term}")
    result = encyclopedia.add_entry_from_wikipedia(args.term, check_duplicates=not args.no_check_duplicates)
    
    if result.get('error'):
        print(f"✗ Error: {result['error']}")
        return 1
    
    if result.get('is_duplicate'):
        print(f"✗ Duplicate entry detected!")
        existing = result.get('existing_entry')
        match_type = result.get('match_type')
        if existing:
            print(f"  Existing entry: {existing.get('term')}")
            print(f"  Match type: {match_type}")
        print("\nUse --no-check-duplicates to add anyway (not recommended)")
        return 1
    
    if result.get('added'):
        entry = result.get('entry')
        print(f"✓ Entry added successfully!")
        print(f"  Term: {entry.get('term')}")
        print(f"  Wikipedia URL: {entry.get('wikipedia_url')}")
        print(f"  Wikidata ID: {entry.get('wikidata_id') or 'None'}")
        
        # Check if marked as needing editing
        entry_id = encyclopedia._generate_entry_id_from_entry(entry, len(encyclopedia.entries) - 1)
        needs_editing = entry.get('needs_editing', {})
        if needs_editing.get('flag'):
            print(f"  ⚠ Marked as needing editing: {needs_editing.get('reason')}")
    else:
        print(f"✗ Entry was not added")
        return 1
    
    # Save edited encyclopedia
    print(f"\nSaving edited encyclopedia to {output_file}...")
    encyclopedia.save_wiki_normalized_html(output_file)
    
    print(f"✓ Encyclopedia saved successfully")
    print(f"  Version: {encyclopedia.metadata.get('version')}")
    print(f"  Total entries: {len(encyclopedia.entries)}")
    
    return 0


if __name__ == "__main__":
    exit(main())
