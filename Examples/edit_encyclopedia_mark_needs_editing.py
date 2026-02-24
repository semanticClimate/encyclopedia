#!/usr/bin/env python3
"""
Script demonstrating how to mark entries as needing editing.

Usage:
    python Examples/edit_encyclopedia_mark_needs_editing.py --input my_encyclopedia.html --output edited_encyclopedia.html --entry-id <id> --reason disambiguation
"""

import argparse
from pathlib import Path

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources


def main():
    parser = argparse.ArgumentParser(description="Mark entries as needing editing")
    parser.add_argument('--input', type=str, required=True, help='Input encyclopedia HTML file')
    parser.add_argument('--output', type=str, required=True, help='Output encyclopedia HTML file')
    parser.add_argument('--entry-id', type=str, help='Entry ID to mark')
    parser.add_argument('--reason', type=str, choices=['disambiguation', 'incomplete', 'error', 'user_marked'],
                       help='Reason for marking')
    parser.add_argument('--notes', type=str, default='', help='Notes about why it needs editing')
    parser.add_argument('--resolve', type=str, help='Resolve editing flag for entry ID')
    parser.add_argument('--list', action='store_true', help='List all entries needing editing')
    parser.add_argument('--filter-reason', type=str, help='Filter by reason when listing')
    
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
    
    # List entries needing editing
    if args.list:
        reason_filter = args.filter_reason if args.filter_reason else None
        needing_editing = encyclopedia.get_entries_needing_editing(reason=reason_filter)
        
        if reason_filter:
            print(f"\nEntries needing editing (reason: {reason_filter}) ({len(needing_editing)}):")
        else:
            print(f"\nEntries needing editing ({len(needing_editing)}):")
        
        for entry in needing_editing:
            entry_id = encyclopedia._generate_entry_id_from_entry(entry, encyclopedia.entries.index(entry))
            needs_editing = entry.get('needs_editing', {})
            reason = needs_editing.get('reason', 'unknown')
            notes = needs_editing.get('notes', '')
            print(f"  - {entry.get('term')} (ID: {entry_id})")
            print(f"    Reason: {reason}")
            if notes:
                print(f"    Notes: {notes}")
        return 0
    
    # Resolve editing flag
    if args.resolve:
        print(f"\nResolving editing flag for entry: {args.resolve}")
        result = encyclopedia.resolve_entry_editing(args.resolve)
        if result:
            print(f"✓ Editing flag resolved successfully")
        else:
            print(f"✗ Entry not found or not marked as needing editing")
            return 1
    
    # Mark entry
    if args.entry_id and args.reason:
        print(f"\nMarking entry: {args.entry_id}")
        print(f"  Reason: {args.reason}")
        if args.notes:
            print(f"  Notes: {args.notes}")
        
        result = encyclopedia.mark_entry_needs_editing(args.entry_id, args.reason, args.notes)
        if result:
            print(f"✓ Entry marked successfully")
        else:
            print(f"✗ Entry not found")
            return 1
    else:
        # List entries for user to choose
        print("\nAvailable entries:")
        for idx, entry in enumerate(encyclopedia.entries[:20]):  # Show first 20
            entry_id = encyclopedia._generate_entry_id_from_entry(entry, idx)
            term = entry.get('term', 'Unknown')
            needs_editing = entry.get('needs_editing', {})
            status = ""
            if needs_editing.get('flag'):
                status = f" (needs editing: {needs_editing.get('reason')})"
            print(f"  {idx+1}. {term} (ID: {entry_id}){status}")
        
        if len(encyclopedia.entries) > 20:
            print(f"  ... and {len(encyclopedia.entries) - 20} more entries")
        
        print("\nUse --entry-id <ID> --reason <reason> to mark an entry")
        print("  Reasons: disambiguation, incomplete, error, user_marked")
        print("Use --resolve <ID> to resolve editing flag")
        print("Use --list to see all entries needing editing")
        return 0
    
    # Save edited encyclopedia
    print(f"\nSaving edited encyclopedia to {output_file}...")
    encyclopedia.save_wiki_normalized_html(output_file)
    
    print(f"✓ Encyclopedia saved successfully")
    print(f"  Version: {encyclopedia.metadata.get('version')}")
    print(f"  Entries needing editing: {len(encyclopedia.get_entries_needing_editing())}")
    
    return 0


if __name__ == "__main__":
    exit(main())
