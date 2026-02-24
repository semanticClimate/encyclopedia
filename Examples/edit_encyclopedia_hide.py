#!/usr/bin/env python3
"""
Script demonstrating how to hide/show entries in an encyclopedia.

Usage:
    python Examples/edit_encyclopedia_hide.py --input my_encyclopedia.html --output edited_encyclopedia.html --hide <entry_id>
    python Examples/edit_encyclopedia_hide.py --input my_encyclopedia.html --output edited_encyclopedia.html --show <entry_id>
"""

import argparse
from pathlib import Path

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources


def main():
    parser = argparse.ArgumentParser(description="Hide/show entries in encyclopedia")
    parser.add_argument('--input', type=str, required=True, help='Input encyclopedia HTML file')
    parser.add_argument('--output', type=str, required=True, help='Output encyclopedia HTML file')
    parser.add_argument('--hide', type=str, help='Entry ID to hide')
    parser.add_argument('--show', type=str, help='Entry ID to show')
    parser.add_argument('--list-hidden', action='store_true', help='List all hidden entries')
    
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
    
    # List hidden entries
    if args.list_hidden:
        hidden = encyclopedia.get_hidden_entries()
        print(f"\nHidden entries ({len(hidden)}):")
        for entry_id in hidden:
            # Find entry by ID
            for idx, entry in enumerate(encyclopedia.entries):
                e_id = encyclopedia._generate_entry_id_from_entry(entry, idx)
                if e_id == entry_id:
                    print(f"  - {entry.get('term')} (ID: {entry_id})")
                    break
        return 0
    
    # Show entry
    if args.show:
        print(f"\nShowing entry: {args.show}")
        result = encyclopedia.show_entry(args.show)
        if result:
            print(f"✓ Entry shown successfully")
        else:
            print(f"✗ Entry not found in hidden entries")
            return 1
    
    # Hide entry
    if args.hide:
        print(f"\nHiding entry: {args.hide}")
        result = encyclopedia.hide_entry(args.hide)
        if result:
            print(f"✓ Entry hidden successfully")
        else:
            print(f"✗ Entry not found")
            return 1
    else:
        # List entries for user to choose
        print("\nAvailable entries:")
        for idx, entry in enumerate(encyclopedia.entries[:20]):  # Show first 20
            entry_id = encyclopedia._generate_entry_id_from_entry(entry, idx)
            term = entry.get('term', 'Unknown')
            hidden = entry_id in encyclopedia.get_hidden_entries()
            status = " (hidden)" if hidden else ""
            print(f"  {idx+1}. {term} (ID: {entry_id}){status}")
        
        if len(encyclopedia.entries) > 20:
            print(f"  ... and {len(encyclopedia.entries) - 20} more entries")
        
        print("\nUse --hide <ID> to hide an entry")
        print("Use --show <ID> to show a hidden entry")
        print("Use --list-hidden to see all hidden entries")
        return 0
    
    # Save edited encyclopedia
    print(f"\nSaving edited encyclopedia to {output_file}...")
    encyclopedia.save_wiki_normalized_html(output_file)
    
    print(f"✓ Encyclopedia saved successfully")
    print(f"  Version: {encyclopedia.metadata.get('version')}")
    print(f"  Hidden entries: {len(encyclopedia.get_hidden_entries())}")
    
    return 0


if __name__ == "__main__":
    exit(main())
