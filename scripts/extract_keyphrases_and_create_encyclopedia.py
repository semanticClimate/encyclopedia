#!/usr/bin/env python3
"""
Extract keyphrases from articles and create an encyclopedia.

This script:
1. Extracts keyphrases from a series of article files using txt2phrases
2. Collects all unique keyphrases across articles
3. Creates an encyclopedia from the extracted keyphrases

Usage:
    python scripts/extract_keyphrases_and_create_encyclopedia.py \
        --input articles/ \
        --output encyclopedia_output.html \
        --title "My Encyclopedia" \
        --top-n 500

    Or with a single file:
    python scripts/extract_keyphrases_and_create_encyclopedia.py \
        --input article.txt \
        --output encyclopedia_output.html
"""

from pathlib import Path
from typing import List, Set, Optional
import argparse
import pandas as pd

try:
    from txt2phrases import KeywordExtraction, convert_pdf_to_text
    from encyclopedia.core.encyclopedia import AmiEncyclopedia
    from encyclopedia.utils.resources import Resources
    from Examples.create_encyclopedia_from_wordlist import create_encyclopedia_from_wordlist
except ImportError as e:
    print("=" * 60)
    print("IMPORT ERROR")
    print("=" * 60)
    print(f"Could not import required modules: {e}")
    print("\nTo fix this, ensure:")
    print("  1. txt2phrases is installed: pip install txt2phrases")
    print("  2. Run from project root directory")
    print("  3. Or install encyclopedia in development mode: pip install -e .")
    print("=" * 60)
    raise


def find_text_files(input_path: Path, recursive: bool = True) -> List[Path]:
    """
    Find all text files in the input path.
    
    Args:
        input_path: Path to file or directory
        recursive: If True, search recursively in subdirectories
        
    Returns:
        List of text file paths
    """
    text_files = []
    
    if input_path.is_file():
        if input_path.suffix.lower() == '.txt':
            text_files.append(input_path)
    elif input_path.is_dir():
        if recursive:
            text_files = list(input_path.rglob("*.txt"))
        else:
            text_files = list(input_path.glob("*.txt"))
    
    return text_files


def convert_pdfs_to_text(
    input_path: Path,
    text_output_dir: Path,
    recursive: bool = True
) -> List[Path]:
    """
    Convert PDF files to text files.
    
    Args:
        input_path: Path to PDF file or directory containing PDFs
        text_output_dir: Directory to save converted text files
        recursive: If True, search recursively for PDFs
        
    Returns:
        List of converted text file paths
    """
    print(f"\nConverting PDFs to text...")
    
    pdf_files = []
    if input_path.is_file() and input_path.suffix.lower() == '.pdf':
        pdf_files = [input_path]
    elif input_path.is_dir():
        if recursive:
            pdf_files = list(input_path.rglob("*.pdf"))
        else:
            pdf_files = list(input_path.glob("*.pdf"))
    
    if not pdf_files:
        print("  No PDF files found.")
        return []
    
    print(f"  Found {len(pdf_files)} PDF files")
    text_output_dir.mkdir(parents=True, exist_ok=True)
    
    converted_files = []
    for pdf_file in pdf_files:
        try:
            txt_path = convert_pdf_to_text(pdf_file, text_output_dir)
            if txt_path:
                converted_files.append(Path(txt_path))
                print(f"  ✓ Converted: {pdf_file.name}")
        except Exception as e:
            print(f"  ✗ Failed to convert {pdf_file.name}: {e}")
    
    print(f"  Successfully converted {len(converted_files)}/{len(pdf_files)} PDF files")
    return converted_files


def extract_keyphrases_from_articles(
    input_path: Path,
    output_dir: Path,
    top_n: int = 500,
    convert_pdfs: bool = True,
    recursive: bool = True
) -> Set[str]:
    """
    Extract keyphrases from article files using txt2phrases.
    
    Args:
        input_path: Path to article file or directory containing article files
        output_dir: Directory to save keyword extraction results
        top_n: Number of top keyphrases to extract per article
        convert_pdfs: If True, convert PDFs to text first
        recursive: If True, search recursively for files
        
    Returns:
        Set of unique keyphrases extracted from all articles
    """
    print(f"\n{'='*60}")
    print(f"Extracting keyphrases from articles...")
    print(f"{'='*60}\n")
    
    # Step 1: Convert PDFs to text if needed
    text_files_dir = None
    if convert_pdfs:
        # Check if there are PDFs
        pdf_files = []
        if input_path.is_file() and input_path.suffix.lower() == '.pdf':
            pdf_files = [input_path]
        elif input_path.is_dir():
            if recursive:
                pdf_files = list(input_path.rglob("*.pdf"))
            else:
                pdf_files = list(input_path.glob("*.pdf"))
        
        if pdf_files:
            text_files_dir = Path(output_dir, "converted_texts")
            converted_files = convert_pdfs_to_text(input_path, text_files_dir, recursive)
            if converted_files:
                print(f"\nUsing converted text files for keyphrase extraction...")
                input_path = text_files_dir
    
    # Step 2: Find all text files
    text_files = find_text_files(input_path, recursive)
    
    if not text_files:
        print(f"\nWarning: No text files found in {input_path}")
        if convert_pdfs:
            print("PDF conversion may have failed. Check errors above.")
        return set()
    
    print(f"\nFound {len(text_files)} text file(s) to process")
    
    # Step 3: Extract keyphrases using txt2phrases
    # KeywordExtraction only processes top-level directory files (not recursive)
    # So we'll process files individually to handle recursive structure
    keywords_output_dir = Path(output_dir, "keywords")
    keywords_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each text file individually
    # This ensures we handle files in subdirectories correctly
    print(f"\nExtracting keyphrases from {len(text_files)} text file(s)...")
    print(f"Extracting top {top_n} keyphrases per article...")
    
    for text_file in text_files:
        try:
            extractor = KeywordExtraction(
                input_path=str(text_file),
                output_folder=str(keywords_output_dir),
                top_n=top_n
            )
            extractor.extract()
        except Exception as e:
            print(f"  ✗ Error processing {text_file.name}: {e}")
    
    # Step 4: Collect all unique keyphrases from CSV files
    all_keyphrases: Set[str] = set()
    
    # Find all CSV files in keywords output directory (recursively)
    csv_files = list(keywords_output_dir.rglob("*_keywords.csv"))
    # Also check for files named just "keywords.csv" or similar patterns
    csv_files.extend(list(keywords_output_dir.rglob("*keywords.csv")))
    csv_files.extend(list(keywords_output_dir.rglob("*.csv")))
    
    # Remove duplicates
    csv_files = list(set(csv_files))
    
    if not csv_files:
        print(f"\nWarning: No keyword CSV files found in {keywords_output_dir}")
        print("This may indicate that no text files were found or extraction failed.")
        return all_keyphrases
    
    print(f"\nCollecting keyphrases from {len(csv_files)} keyword files...")
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            # Check for different possible column names
            keyword_col = None
            for col in ['keyword', 'keywords', 'keyphrase', 'keyphrases', 'phrase', 'phrases']:
                if col in df.columns:
                    keyword_col = col
                    break
            
            if keyword_col:
                keyphrases = df[keyword_col].dropna().astype(str).str.strip()
                keyphrases = keyphrases[keyphrases != '']
                all_keyphrases.update(keyphrases.tolist())
                print(f"  ✓ {csv_file.name}: {len(keyphrases)} keyphrases")
            else:
                print(f"  ⚠ {csv_file.name}: No keyword column found (columns: {list(df.columns)})")
        except Exception as e:
            print(f"  ✗ Error reading {csv_file.name}: {e}")
    
    print(f"\nTotal unique keyphrases collected: {len(all_keyphrases)}")
    
    return all_keyphrases


def create_encyclopedia_from_keyphrases(
    keyphrases: Set[str],
    title: str = "Encyclopedia from Articles",
    add_wikipedia: bool = True,
    add_images: bool = False,
    batch_size: int = 10,
    validate: bool = True,
    verbose: bool = False
) -> AmiEncyclopedia:
    """
    Create an encyclopedia from extracted keyphrases.
    
    Args:
        keyphrases: Set of keyphrases to include in encyclopedia
        title: Title for the encyclopedia
        add_wikipedia: If True, add Wikipedia descriptions
        add_images: If True, add images from Wikipedia
        batch_size: Number of entries to process at a time
        validate: If True, validate results at the end
        verbose: If True, show detailed progress
        
    Returns:
        AmiEncyclopedia instance
    """
    # Convert set to sorted list for consistent ordering
    keyphrase_list = sorted(list(keyphrases))
    
    print(f"\n{'='*60}")
    print(f"Creating encyclopedia from {len(keyphrase_list)} keyphrases...")
    print(f"{'='*60}\n")
    
    # Use the existing function to create encyclopedia
    encyclopedia = create_encyclopedia_from_wordlist(
        terms=keyphrase_list,
        title=title,
        add_wikipedia=add_wikipedia,
        add_images=add_images,
        batch_size=batch_size,
        validate=validate,
        verbose=verbose
    )
    
    return encyclopedia


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(
        description="Extract keyphrases from articles and create an encyclopedia",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a directory of articles
  python scripts/extract_keyphrases_and_create_encyclopedia.py \\
      --input articles/ \\
      --output my_encyclopedia.html \\
      --top-n 500

  # Process a single article file
  python scripts/extract_keyphrases_and_create_encyclopedia.py \\
      --input article.txt \\
      --output encyclopedia.html \\
      --title "Climate Science Encyclopedia"

  # Skip Wikipedia lookups (faster)
  python scripts/extract_keyphrases_and_create_encyclopedia.py \\
      --input articles/ \\
      --output output.html \\
      --no-wikipedia
        """
    )
    
    parser.add_argument(
        '--input',
        '-i',
        type=str,
        required=True,
        help='Path to article file or directory containing article files (.txt files)'
    )
    parser.add_argument(
        '--output',
        '-o',
        type=str,
        required=True,
        help='Output HTML file path for the encyclopedia'
    )
    parser.add_argument(
        '--title',
        type=str,
        default='Encyclopedia from Articles',
        help='Title for the encyclopedia (default: "Encyclopedia from Articles")'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=500,
        help='Number of top keyphrases to extract per article (default: 500)'
    )
    parser.add_argument(
        '--keywords-output',
        type=str,
        help='Directory to save keyword extraction CSV files (default: temp/scripts/extract_keyphrases)'
    )
    parser.add_argument(
        '--convert-pdfs',
        action='store_true',
        default=True,
        help='Convert PDF files to text before extraction (default: True)'
    )
    parser.add_argument(
        '--no-convert-pdfs',
        action='store_false',
        dest='convert_pdfs',
        help='Skip PDF conversion (assume text files only)'
    )
    parser.add_argument(
        '--recursive',
        '-r',
        action='store_true',
        default=True,
        help='Search recursively in subdirectories (default: True)'
    )
    parser.add_argument(
        '--no-recursive',
        action='store_false',
        dest='recursive',
        help='Only search in top-level directory'
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
        help='Number of entries to process at a time (default: 10)'
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
        '-v',
        action='store_true',
        default=False,
        help='Show detailed progress (default: False)'
    )
    
    args = parser.parse_args()
    
    # Validate input path
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        return 1
    
    # Set up output paths
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Set up keywords output directory
    if args.keywords_output:
        keywords_output_dir = Path(args.keywords_output)
    else:
        keywords_output_dir = Resources.get_temp_dir("scripts", "extract_keyphrases")
    keywords_output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Extract keyphrases from articles
        keyphrases = extract_keyphrases_from_articles(
            input_path=input_path,
            output_dir=keywords_output_dir,
            top_n=args.top_n,
            convert_pdfs=args.convert_pdfs,
            recursive=args.recursive
        )
        
        if not keyphrases:
            print("\nError: No keyphrases extracted from articles.")
            print("Please check:")
            print("  1. Input path contains .txt files")
            print("  2. Files contain readable text content")
            print("  3. txt2phrases is properly installed")
            return 1
        
        # Step 2: Create encyclopedia from keyphrases
        encyclopedia = create_encyclopedia_from_keyphrases(
            keyphrases=keyphrases,
            title=args.title,
            add_wikipedia=args.add_wikipedia,
            add_images=args.add_images,
            batch_size=args.batch_size,
            validate=args.validate,
            verbose=args.verbose
        )
        
        # Step 3: Save encyclopedia
        print(f"\n{'='*60}")
        print(f"Saving encyclopedia to: {output_file}")
        print(f"{'='*60}\n")
        
        try:
            encyclopedia.save_wiki_normalized_html(output_file)
            print(f"✓ Encyclopedia saved successfully!")
            print(f"  File: {output_file}")
            print(f"  Entries: {len(encyclopedia.entries)}")
            print(f"  Keyphrases extracted: {len(keyphrases)}")
            print(f"  Keyword CSV files: {keywords_output_dir}")
        except KeyboardInterrupt:
            print("\n  Save operation interrupted by user (Ctrl+C).")
            print("  Partial file may have been created.")
            return 1
        except Exception as e:
            print(f"\n  Error saving encyclopedia: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        print(f"\n{'='*60}")
        print("Done!")
        print(f"{'='*60}\n")
        
        return 0
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
