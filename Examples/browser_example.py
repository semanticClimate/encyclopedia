#!/usr/bin/env python3
"""
Simple example demonstrating Encyclopedia Browser usage.

This script shows how to:
1. Load an encyclopedia
2. Search entries
3. Display results
4. Browse entries

Run from project root:
    python Examples/browser_example.py
"""

from pathlib import Path
from encyclopedia.browser.search_engine import EncyclopediaSearchEngine


def main():
    """Demonstrate browser functionality."""
    
    print("=" * 60)
    print("Encyclopedia Browser - Example Usage")
    print("=" * 60)
    print()
    
    # Step 1: Initialize search engine
    print("Step 1: Initializing search engine...")
    search_engine = EncyclopediaSearchEngine()
    print("✓ Search engine initialized")
    print()
    
    # Step 2: Load encyclopedia
    encyclopedia_file = Path("my_encyclopedia.html")
    
    if not encyclopedia_file.exists():
        print(f"⚠ Warning: {encyclopedia_file} not found.")
        print("  Create an encyclopedia first:")
        print("    python -m Examples.create_encyclopedia_from_wordlist \\")
        print("        --wordlist Examples/my_terms.txt \\")
        print("        --output my_encyclopedia.html")
        print()
        return
    
    print(f"Step 2: Loading encyclopedia from {encyclopedia_file}...")
    try:
        search_engine.load_encyclopedia(encyclopedia_file)
        print("✓ Encyclopedia loaded and indexed")
        print()
    except Exception as e:
        print(f"✗ Error loading encyclopedia: {e}")
        return
    
    # Step 3: Search examples
    print("Step 3: Searching entries...")
    print()
    
    # Example 1: Exact search
    print("Example 1: Exact Search")
    print("-" * 60)
    query = "climate change"
    results = search_engine.search(query, search_type="exact", limit=5)
    print(f"Query: '{query}'")
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.entry.term} (score: {result.score:.1f}, type: {result.match_type})")
    print()
    
    # Example 2: Stemmed search
    print("Example 2: Stemmed Search")
    print("-" * 60)
    query = "climate"
    results = search_engine.search(query, search_type="stemmed", limit=5)
    print(f"Query: '{query}'")
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.entry.term} (score: {result.score:.1f}, type: {result.match_type})")
    print()
    
    # Example 3: Auto search
    print("Example 3: Auto Search (Recommended)")
    print("-" * 60)
    query = "greenhouse"
    results = search_engine.search(query, search_type="auto", limit=5)
    print(f"Query: '{query}'")
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.entry.term} (score: {result.score:.1f}, type: {result.match_type})")
    print()
    
    # Step 4: Browse entries
    print("Step 4: Browsing entries...")
    print("-" * 60)
    all_entries = search_engine.get_all_entries(limit=10)
    print(f"Total entries available: {len(all_entries)} (showing first 10)")
    for i, entry in enumerate(all_entries, 1):
        print(f"  {i}. {entry.term}")
        if entry.wikidata_id:
            print(f"     Wikidata: {entry.wikidata_id}")
        if entry.wikipedia_url:
            print(f"     Wikipedia: {entry.wikipedia_url}")
    print()
    
    # Step 5: Get specific entry
    if all_entries:
        print("Step 5: Getting specific entry...")
        print("-" * 60)
        first_entry = all_entries[0]
        entry_by_id = search_engine.get_entry_by_id(first_entry.entry_id)
        if entry_by_id:
            print(f"Entry: {entry_by_id.term}")
            print(f"Canonical: {entry_by_id.canonical_term}")
            if entry_by_id.synonyms:
                print(f"Synonyms: {', '.join(entry_by_id.synonyms)}")
            if entry_by_id.description_text:
                desc_preview = entry_by_id.description_text[:100]
                print(f"Description: {desc_preview}...")
        print()
    
    print("=" * 60)
    print("Example complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Try the web interface: python encyclopedia/browser/run_browser.py")
    print("  2. Experiment with different search queries")
    print("  3. See TUTORIAL.md for more examples")


if __name__ == "__main__":
    main()
