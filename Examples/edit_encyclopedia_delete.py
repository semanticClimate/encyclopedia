#!/usr/bin/env python3
"""
Script demonstrating how to delete entries from an encyclopedia.

Usage:
    python Examples/edit_encyclopedia_delete.py --input my_encyclopedia.html --output edited_encyclopedia.html
"""

import argparse
from pathlib import Path

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources


def main():
    parser = argparse.ArgumentParser(description="Delete entries from encyclopedia")
    parser.add_argument('--input', type=str, required=True, help='Input encyclopedia HTML file')
    parser.add_argument('--output', type=str, required=True, help='Output encyclopedia HTML file')
    parser.add_argument('--entry-id', type=str, help='Entry ID to delete (if not provided, will list entries)')
    parser.add_argument('--hard', action='store_true', help='Hard delete (remove from entries list) instead of soft delete')
    parser.add_argument('--list-deleted', action='store_true', help='List all deleted entries')
    parser.add_argument('--restore', type=str, help='Restore a deleted entry by entry ID')
    
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
    
    # List deleted entries
    if args.list_deleted:
        deleted = encyclopedia.get_deleted_entries()
        print(f"\nDeleted entries ({len(deleted)}):")
        for de in deleted:
            print(f"  - {de.get('term')} (ID: {de.get('entry_id')}, deleted at: {de.get('deleted_at')})")
        return 0
    
    # Restore entry
    if args.restore:
        print(f"\nRestoring entry: {args.restore}")
        result = encyclopedia.restore_entry(args.restore)
        if result:
            print(f"✓ Entry restored successfully")
        else:
            print(f"✗ Entry not found in deleted entries")
            return 1
    
    # Delete entry
    if args.entry_id:
        print(f"\nDeleting entry: {args.entry_id} (soft={not args.hard})")
        result = encyclopedia.delete_entry(args.entry_id, soft=not args.hard)
        if result:
            print(f"✓ Entry deleted successfully")
            if args.hard:
                print(f"  Entry removed from entries list")
            else:
                print(f"  Entry marked as deleted (recoverable)")
        else:
            print(f"✗ Entry not found")
            return 1
    else:
        # List entries for user to choose
        print("\nAvailable entries:")
        for idx, entry in enumerate(encyclopedia.entries[:20]):  # Show first 20
            entry_id = encyclopedia._generate_entry_id_from_entry(entry, idx)
            term = entry.get('term', 'Unknown')
            print(f"  {idx+1}. {term} (ID: {entry_id})")
        
        if len(encyclopedia.entries) > 20:
            print(f"  ... and {len(encyclopedia.entries) - 20} more entries")
        
        print("\nUse --entry-id <ID> to delete an entry")
        print("Use --list-deleted to see deleted entries")
        print("Use --restore <ID> to restore a deleted entry")
        return 0
    
    # Save edited encyclopedia
    print(f"\nSaving edited encyclopedia to {output_file}...")
    encyclopedia.save_wiki_normalized_html(output_file)
    
    print(f"✓ Encyclopedia saved successfully")
    print(f"  Version: {encyclopedia.metadata.get('version')}")
    print(f"  Total entries: {len(encyclopedia.entries)}")
    
    return 0


if __name__ == "__main__":
    exit(main())
