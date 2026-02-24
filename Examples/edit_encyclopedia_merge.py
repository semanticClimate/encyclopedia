#!/usr/bin/env python3
"""
Script demonstrating how to merge two encyclopedias.

Usage:
    python Examples/edit_encyclopedia_merge.py --target my_encyclopedia.html --source other_encyclopedia.html --output merged_encyclopedia.html
"""

import argparse
from pathlib import Path
import json

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources


def main():
    parser = argparse.ArgumentParser(description="Merge two encyclopedias")
    parser.add_argument('--target', type=str, required=True, help='Target encyclopedia HTML file (to merge INTO)')
    parser.add_argument('--source', type=str, required=True, help='Source encyclopedia HTML file (to merge FROM)')
    parser.add_argument('--output', type=str, required=True, help='Output merged encyclopedia HTML file')
    parser.add_argument('--conflicts-file', type=str, help='JSON file with conflict resolution (term -> strategy)')
    
    args = parser.parse_args()
    
    target_file = Path(args.target)
    source_file = Path(args.source)
    output_file = Path(args.output)
    
    if not target_file.exists():
        print(f"Error: Target file not found: {target_file}")
        return 1
    
    if not source_file.exists():
        print(f"Error: Source file not found: {source_file}")
        return 1
    
    # Load encyclopedias
    print(f"Loading target encyclopedia from {target_file}...")
    target_encyclopedia = AmiEncyclopedia()
    target_encyclopedia.create_from_html_file(target_file)
    print(f"  Loaded {len(target_encyclopedia.entries)} entries")
    
    print(f"\nLoading source encyclopedia from {source_file}...")
    source_encyclopedia = AmiEncyclopedia()
    source_encyclopedia.create_from_html_file(source_file)
    print(f"  Loaded {len(source_encyclopedia.entries)} entries")
    
    # Load conflict resolution if provided
    conflict_resolution = {}
    if args.conflicts_file:
        conflicts_path = Path(args.conflicts_file)
        if conflicts_path.exists():
            with open(conflicts_path, 'r', encoding='utf-8') as f:
                conflict_resolution = json.load(f)
            print(f"\nLoaded conflict resolution from {conflicts_path}")
        else:
            print(f"Warning: Conflicts file not found: {conflicts_path}")
    
    # Merge
    print(f"\nMerging source into target...")
    result = target_encyclopedia.merge_encyclopedia(source_encyclopedia, conflict_resolution=conflict_resolution)
    
    print(f"✓ Merge completed!")
    print(f"  Entries added: {result.get('entries_added', 0)}")
    print(f"  Entries merged: {result.get('entries_merged', 0)}")
    print(f"  Conflicts detected: {len(result.get('conflicts', []))}")
    print(f"  Conflicts resolved: {len(result.get('resolved_conflicts', []))}")
    
    # Show conflicts if any
    conflicts = result.get('conflicts', [])
    if conflicts:
        print(f"\n⚠ Unresolved conflicts ({len(conflicts)}):")
        for conflict in conflicts:
            term = conflict.get('term')
            print(f"  - {term}")
            print(f"    Target: {conflict.get('target_entry', {}).get('wikipedia_url', 'N/A')}")
            print(f"    Source: {conflict.get('source_entry', {}).get('wikipedia_url', 'N/A')}")
        
        print("\nTo resolve conflicts, create a JSON file with:")
        print('  {')
        for conflict in conflicts[:3]:  # Show first 3 as examples
            term = conflict.get('term')
            print(f'    "{term}": "keep_target",  # or "replace_with_source", "merge", "skip"')
        if len(conflicts) > 3:
            print(f'    ... and {len(conflicts) - 3} more')
        print('  }')
        print("\nThen use --conflicts-file <file> to apply resolutions")
    
    # Save merged encyclopedia
    print(f"\nSaving merged encyclopedia to {output_file}...")
    target_encyclopedia.save_wiki_normalized_html(output_file)
    
    print(f"✓ Merged encyclopedia saved successfully")
    print(f"  Version: {target_encyclopedia.metadata.get('version')}")
    print(f"  Total entries: {len(target_encyclopedia.entries)}")
    
    return 0


if __name__ == "__main__":
    exit(main())
