#!/usr/bin/env python3
"""
Create encyclopedia from phrase list (CSV or text file).

This script reads phrases from a CSV file or text file and creates an encyclopedia.
Supports flexible CSV column selection and auto-detection.

Date: March 2, 2026 (system date)

Usage:
    # From CSV file with auto-detection
    python Examples/create_encyclopedia_from_phraselist.py \
        --input phrases.csv \
        --output encyclopedia.html \
        --title "My Encyclopedia"
    
    # From CSV file with specific columns
    python Examples/create_encyclopedia_from_phraselist.py \
        --input phrases.csv \
        --output encyclopedia.html \
        --phrase-column "keyword" \
        --count-column "frequency"
    
    # From CSV file using column numbers
    python Examples/create_encyclopedia_from_phraselist.py \
        --input phrases.csv \
        --output encyclopedia.html \
        --phrase-column 0 \
        --count-column 1
    
    # From text file (one phrase per line)
    python Examples/create_encyclopedia_from_phraselist.py \
        --input phrases.txt \
        --output encyclopedia.html \
        --title "My Encyclopedia"
    
    # With Wikipedia descriptions and images
    python Examples/create_encyclopedia_from_phraselist.py \
        --input phrases.csv \
        --output encyclopedia.html \
        --add-wikipedia \
        --add-images \
        --batch-size 10

Parameters:
    --input: Input CSV or text file (required)
    --output: Output HTML file (required)
    --title: Encyclopedia title (default: "Encyclopedia")
    --phrase-column: CSV column name or number for phrases (auto-detects if not specified)
    --count-column: CSV column name or number for counts (optional, auto-detects if not specified)
    --add-wikipedia: Add Wikipedia descriptions (default: False)
    --add-images: Add images from Wikipedia (default: False, can be slow)
    --batch-size: Number of entries to process at a time (default: 10)
    --validate: Validate encyclopedia completeness (default: False)
    --verbose: Show detailed progress (default: False)
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Union

try:
    from encyclopedia.core.encyclopedia import AmiEncyclopedia
    from encyclopedia.utils.csv_reader import read_phrases_from_csv
    from Examples.create_encyclopedia_from_wordlist import create_encyclopedia_from_wordlist
except ImportError as e:
    print("=" * 60)
    print("IMPORT ERROR")
    print("=" * 60)
    print(f"Could not import required modules: {e}")
    print("\nTo fix this, run the script from the project root directory:")
    print("  cd /path/to/encyclopedia")
    print("  python Examples/create_encyclopedia_from_phraselist.py")
    print("\nOr install the package in development mode:")
    print("  pip install -e .")
    print("=" * 60)
    sys.exit(1)


def read_phrases_from_file(
    input_file: Path,
    phrase_column: Optional[Union[str, int]] = None,
    count_column: Optional[Union[str, int]] = None
) -> tuple[List[str], Optional[List[int]]]:
    """
    Read phrases from CSV or text file.
    
    Args:
        input_file: Path to CSV or text file
        phrase_column: For CSV - column name (str), column number (int), or None for auto-detect
        count_column: For CSV - column name (str), column number (int), None for auto-detect, or omit
        
    Returns:
        Tuple of (phrases: List[str], counts: Optional[List[int]])
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Check if CSV file (by extension)
    if input_file.suffix.lower() == '.csv':
        # Read CSV file
        phrases, counts = read_phrases_from_csv(
            input_file,
            phrase_column=phrase_column,
            count_column=count_column
        )
        return phrases, counts
    else:
        # Read text file (one phrase per line)
        phrases = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                phrase = line.strip()
                if phrase and not phrase.startswith('#'):
                    phrases.append(phrase)
        return phrases, None


def main():
    """Main entry point for creating encyclopedia from phrase list."""
    parser = argparse.ArgumentParser(
        description='Create encyclopedia from phrase list (CSV or text file)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Required arguments
    parser.add_argument(
        '--input', '-i',
        type=Path,
        required=True,
        help='Input CSV or text file (one phrase per line for text files)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        required=True,
        help='Output HTML file for encyclopedia'
    )
    
    # Optional arguments
    parser.add_argument(
        '--title', '-t',
        type=str,
        default='Encyclopedia',
        help='Encyclopedia title (default: "Encyclopedia")'
    )
    
    # CSV column selection
    parser.add_argument(
        '--phrase-column',
        type=str,
        default=None,
        help='CSV column name (e.g., "phrase", "keyword") or column number (0-indexed). '
             'Auto-detects common column names if not specified.'
    )
    
    parser.add_argument(
        '--count-column',
        type=str,
        default=None,
        help='CSV column name (e.g., "count", "frequency") or column number. '
             'Auto-detects if not specified. Optional - counts are not used for encyclopedia creation.'
    )
    
    # Encyclopedia creation options
    parser.add_argument(
        '--add-wikipedia',
        action='store_true',
        help='Add Wikipedia descriptions (default: False)'
    )
    
    parser.add_argument(
        '--add-images',
        action='store_true',
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
        help='Validate encyclopedia completeness (default: False)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed progress (default: False)'
    )
    
    args = parser.parse_args()
    
    # Parse column arguments (can be int or str)
    phrase_col = None
    count_col = None
    if args.phrase_column:
        try:
            phrase_col = int(args.phrase_column)
        except ValueError:
            phrase_col = args.phrase_column
    if args.count_column:
        try:
            count_col = int(args.count_column)
        except ValueError:
            count_col = args.count_column
    
    # Read phrases from file
    print(f"\n{'='*60}")
    print(f"Reading phrases from: {args.input}")
    print(f"{'='*60}\n")
    
    try:
        phrases, counts = read_phrases_from_file(
            args.input,
            phrase_column=phrase_col,
            count_column=count_col
        )
    except Exception as e:
        print(f"Error reading input file: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    if not phrases:
        print(f"Error: No phrases found in {args.input}")
        return 1
    
    if counts:
        print(f"✓ Loaded {len(phrases)} phrases with counts from {args.input.name}")
        if args.verbose:
            print(f"  Count range: {min(counts)} - {max(counts)}")
    else:
        print(f"✓ Loaded {len(phrases)} phrases from {args.input.name}")
    
    # Create encyclopedia
    print(f"\n{'='*60}")
    print(f"Creating encyclopedia '{args.title}'...")
    print(f"{'='*60}\n")
    
    try:
        encyclopedia = create_encyclopedia_from_wordlist(
            phrases,
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
        return 1
    
    # Save encyclopedia
    print(f"\n{'='*60}")
    print(f"Saving encyclopedia to: {args.output}")
    print(f"{'='*60}\n")
    
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        encyclopedia.save_wiki_normalized_html(args.output)
        print(f"✓ Encyclopedia saved successfully")
        print(f"  File: {args.output}")
        print(f"  Entries: {len(encyclopedia.entries)}")
    except Exception as e:
        print(f"Error saving encyclopedia: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print(f"\n{'='*60}")
    print("Done!")
    print(f"{'='*60}\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
