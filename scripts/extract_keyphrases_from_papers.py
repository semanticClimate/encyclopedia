#!/usr/bin/env python3
"""
Extract keyphrases from a limited number of papers and create an encyclopedia.

WORKFLOW:
1. Find papers (PDFs or text files) in the input directory
2. Limit to first N papers (default: 10) to manage CPU-intensive processing
3. Convert PDFs to text if needed
4. Extract keyphrases from each paper using txt2phrases
5. Collect all unique keyphrases across papers
6. Create an encyclopedia from the extracted keyphrases

Usage:
    python scripts/extract_keyphrases_from_papers.py \
        --input Examples/blue_tea \
        --output blue_tea_encyclopedia.html \
        --max-papers 10 \
        --top-n 500

    Or with specific paper selection:
    python scripts/extract_keyphrases_from_papers.py \
        --input Examples/blue_tea \
        --output output.html \
        --max-papers 5 \
        --title "Blue Tea Research (5 papers)"
"""

from pathlib import Path
from typing import List, Set, Optional
import argparse
import pandas as pd
import shutil

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


def find_papers(input_path: Path, max_papers: int = 10, recursive: bool = True) -> List[Path]:
    """
    Find papers (PDFs or text files) and limit to max_papers.
    
    Args:
        input_path: Path to file or directory containing papers
        max_papers: Maximum number of papers to process
        recursive: If True, search recursively in subdirectories
        
    Returns:
        List of paper file paths (limited to max_papers)
    """
    papers = []
    
    if input_path.is_file():
        # Single file
        if input_path.suffix.lower() in ['.pdf', '.txt']:
            papers = [input_path]
    elif input_path.is_dir():
        # Find PDFs first (preferred)
        if recursive:
            pdf_files = sorted(list(input_path.rglob("*.pdf")))
        else:
            pdf_files = sorted(list(input_path.glob("*.pdf")))
        
        if pdf_files:
            papers = pdf_files[:max_papers]
        else:
            # If no PDFs, look for text files
            if recursive:
                txt_files = sorted(list(input_path.rglob("*.txt")))
            else:
                txt_files = sorted(list(input_path.glob("*.txt")))
            papers = txt_files[:max_papers]
    
    return papers


def convert_pdfs_to_text_limited(
    pdf_files: List[Path],
    text_output_dir: Path,
    max_papers: int = 10
) -> List[Path]:
    """
    Convert a limited number of PDF files to text.
    
    Args:
        pdf_files: List of PDF file paths
        text_output_dir: Directory to save converted text files
        max_papers: Maximum number of PDFs to convert
        
    Returns:
        List of converted text file paths
    """
    print(f"\n{'='*60}")
    print(f"Converting PDFs to text (limited to {max_papers} papers)...")
    print(f"{'='*60}\n")
    
    # Limit to max_papers
    pdf_files_to_convert = pdf_files[:max_papers]
    
    if not pdf_files_to_convert:
        print("  No PDF files to convert.")
        return []
    
    print(f"  Found {len(pdf_files)} PDF files, converting first {len(pdf_files_to_convert)}...")
    text_output_dir.mkdir(parents=True, exist_ok=True)
    
    converted_files = []
    for i, pdf_file in enumerate(pdf_files_to_convert, 1):
        try:
            print(f"  [{i}/{len(pdf_files_to_convert)}] Converting: {pdf_file.name}")
            txt_path = convert_pdf_to_text(pdf_file, text_output_dir)
            if txt_path:
                converted_files.append(Path(txt_path))
                print(f"      ✓ Saved: {Path(txt_path).name}")
            else:
                print(f"      ✗ Failed to convert")
        except Exception as e:
            print(f"      ✗ Error: {e}")
    
    print(f"\n  Successfully converted {len(converted_files)}/{len(pdf_files_to_convert)} PDF files")
    return converted_files


def extract_keyphrases_from_papers(
    papers: List[Path],
    output_dir: Path,
    top_n: int = 500,
    max_papers: int = 10,
    max_terms: Optional[int] = None
) -> Set[str]:
    """
    Extract keyphrases from a limited number of papers using txt2phrases.
    
    Args:
        papers: List of paper file paths (PDFs or text files)
        output_dir: Directory to save keyword extraction results
        top_n: Number of top keyphrases to extract per paper
        max_papers: Maximum number of papers to process
        max_terms: Maximum number of terms to include in final encyclopedia (None = all)
        
    Returns:
        Set of unique keyphrases extracted from all papers (limited to max_terms if specified)
    """
    print(f"\n{'='*60}")
    print(f"Extracting keyphrases from papers (limited to {max_papers})...")
    print(f"{'='*60}\n")
    
    # Limit to max_papers
    papers_to_process = papers[:max_papers]
    
    if not papers_to_process:
        print("  No papers to process.")
        return set()
    
    print(f"  Processing {len(papers_to_process)} paper(s)...")
    print(f"  Extracting top {top_n} keyphrases per paper...")
    print(f"  Note: This is CPU-intensive and may take several minutes per paper.\n")
    
    keywords_output_dir = Path(output_dir, "keywords")
    keywords_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each paper individually
    for i, paper_file in enumerate(papers_to_process, 1):
        print(f"\n  [{i}/{len(papers_to_process)}] Processing: {paper_file.name}")
        
        # Create unique identifier for this paper
        # Use parent directory name if available, otherwise use paper name
        if paper_file.parent.name and paper_file.parent.name not in ['', '.']:
            paper_id = f"{paper_file.parent.name}_{paper_file.stem}"
        else:
            paper_id = f"paper_{i:03d}_{paper_file.stem}"
        
        # If it's a PDF, we need to convert it first
        if paper_file.suffix.lower() == '.pdf':
            # Convert this PDF to text with unique name
            temp_text_dir = Path(output_dir, "temp_texts")
            temp_text_dir.mkdir(parents=True, exist_ok=True)
            try:
                # Convert PDF to text
                txt_path = convert_pdf_to_text(paper_file, temp_text_dir)
                if not txt_path:
                    print(f"      ✗ Failed to convert PDF to text")
                    continue
                
                # Rename the converted file to use unique identifier
                original_text_file = Path(txt_path)
                unique_text_file = Path(temp_text_dir, f"{paper_id}.txt")
                if original_text_file != unique_text_file:
                    original_text_file.rename(unique_text_file)
                text_file = unique_text_file
            except Exception as e:
                print(f"      ✗ Error converting PDF: {e}")
                continue
        else:
            # For text files, copy to temp directory with unique name to avoid conflicts
            temp_text_dir = Path(output_dir, "temp_texts")
            temp_text_dir.mkdir(parents=True, exist_ok=True)
            unique_text_file = Path(temp_text_dir, f"{paper_id}.txt")
            try:
                shutil.copy2(paper_file, unique_text_file)
                text_file = unique_text_file
            except Exception as e:
                print(f"      ✗ Error copying text file: {e}")
                continue
        
        # Extract keyphrases from text file
        # Create a unique output directory per paper to avoid CSV overwrites
        paper_keywords_dir = Path(keywords_output_dir, paper_id)
        paper_keywords_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            extractor = KeywordExtraction(
                input_path=str(text_file),
                output_folder=str(paper_keywords_dir),
                top_n=top_n
            )
            extractor.extract()
            
            # Move/rename the CSV file to have unique name in main keywords directory
            # KeywordExtraction creates: {base_name}_keywords.csv
            expected_csv = Path(paper_keywords_dir, f"{text_file.stem}_keywords.csv")
            if expected_csv.exists():
                # Move to main keywords directory with unique name
                final_csv = Path(keywords_output_dir, f"{paper_id}_keywords.csv")
                expected_csv.rename(final_csv)
                print(f"      ✓ Keyphrases extracted: {final_csv.name}")
            else:
                # Look for any CSV file created
                csv_files_in_dir = list(paper_keywords_dir.glob("*.csv"))
                if csv_files_in_dir:
                    csv_file = csv_files_in_dir[0]
                    final_csv = Path(keywords_output_dir, f"{paper_id}_keywords.csv")
                    csv_file.rename(final_csv)
                    print(f"      ✓ Keyphrases extracted: {final_csv.name}")
                else:
                    print(f"      ⚠ Keyphrases extracted but CSV file not found")
        except Exception as e:
            print(f"      ✗ Error extracting keyphrases: {e}")
    
    # Merge CSV files and aggregate counts for common terms
    all_keyphrases: Set[str] = set()
    keyword_counts: dict = {}
    
    # Find all CSV files in keywords output directory
    csv_files = list(keywords_output_dir.glob("*_keywords.csv"))
    csv_files.extend(list(keywords_output_dir.glob("*keywords.csv")))
    csv_files.extend(list(keywords_output_dir.glob("*.csv")))
    csv_files = list(set(csv_files))  # Remove duplicates
    
    if not csv_files:
        print(f"\n  Warning: No keyword CSV files found in {keywords_output_dir}")
        return all_keyphrases
    
    print(f"\n  Merging keyphrases from {len(csv_files)} keyword file(s)...")
    
    # Read all CSV files and aggregate counts
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            # Check for different possible column names
            keyword_col = None
            count_col = None
            
            for col in ['keyword', 'keywords', 'keyphrase', 'keyphrases', 'phrase', 'phrases']:
                if col in df.columns:
                    keyword_col = col
                    break
            
            for col in ['count', 'counts', 'frequency', 'freq']:
                if col in df.columns:
                    count_col = col
                    break
            
            if keyword_col:
                # Process each row
                for _, row in df.iterrows():
                    keyword = str(row[keyword_col]).strip()
                    if keyword and keyword != '' and keyword.lower() != 'nan':
                        # Get count (default to 1 if no count column)
                        if count_col and pd.notna(row[count_col]):
                            count = int(row[count_col])
                        else:
                            count = 1
                        
                        # Aggregate counts for common terms
                        if keyword in keyword_counts:
                            keyword_counts[keyword] += count
                        else:
                            keyword_counts[keyword] = count
                        
                        all_keyphrases.add(keyword)
                
                print(f"      ✓ {csv_file.name}: {len(df)} keyphrases")
            else:
                print(f"      ⚠ {csv_file.name}: No keyword column found (columns: {list(df.columns)})")
        except Exception as e:
            print(f"      ✗ Error reading {csv_file.name}: {e}")
    
    # Create merged DataFrame with aggregated counts
    if keyword_counts:
        merged_data = [
            {'keyword': keyword, 'count': count}
            for keyword, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        merged_df = pd.DataFrame(merged_data)
        
        # Limit to max_terms if specified (take top N by count)
        if max_terms is not None and max_terms > 0:
            original_count = len(merged_df)
            merged_df = merged_df.head(max_terms)
            print(f"\n  Limiting to top {max_terms} terms by aggregated count")
            print(f"    (reduced from {original_count} unique keyphrases)")
        
        # Save merged CSV file
        merged_csv_path = Path(keywords_output_dir, "merged_keyphrases.csv")
        merged_df.to_csv(merged_csv_path, index=False)
        print(f"\n  ✓ Merged CSV saved: {merged_csv_path.name}")
        print(f"    Total unique keyphrases: {len(merged_df)}")
        print(f"    Total occurrences: {merged_df['count'].sum()}")
        
        # Show top keyphrases (up to 10 or max_terms, whichever is smaller)
        display_count = min(10, len(merged_df))
        print(f"    Top {display_count} keyphrases:")
        for i, row in merged_df.head(display_count).iterrows():
            print(f"      {i+1}. {row['keyword']}: {row['count']} occurrences")
        
        # Update all_keyphrases to only include the limited set
        all_keyphrases = set(merged_df['keyword'].tolist())
    
    print(f"\n  Total unique keyphrases for encyclopedia: {len(all_keyphrases)}")
    
    return all_keyphrases


def create_encyclopedia_from_keyphrases(
    keyphrases: Set[str],
    title: str = "Encyclopedia from Papers",
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
        description="Extract keyphrases from a limited number of papers and create an encyclopedia",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
WORKFLOW:
  1. Find papers (PDFs or text files) in input directory
  2. Limit to --max-papers (default: 10) to manage CPU load
  3. Convert PDFs to text if needed
  4. Extract keyphrases from each paper (CPU-intensive)
  5. Merge CSV files and aggregate counts for common terms
  6. Limit to top N terms by aggregated count (if --max-terms specified)
  7. Create encyclopedia from selected keyphrases

Examples:
  # Process 10 papers from blue_tea directory
  python scripts/extract_keyphrases_from_papers.py \\
      --input Examples/blue_tea \\
      --output blue_tea_encyclopedia.html \\
      --max-papers 10

  # Create demonstration encyclopedia with top 50 terms
  python scripts/extract_keyphrases_from_papers.py \\
      --input Examples/blue_tea \\
      --output demo_encyclopedia.html \\
      --max-papers 10 \\
      --max-terms 50

  # Process only 5 papers, limit to 30 terms
  python scripts/extract_keyphrases_from_papers.py \\
      --input Examples/blue_tea \\
      --output output.html \\
      --max-papers 5 \\
      --top-n 300 \\
      --max-terms 30

  # Skip Wikipedia lookups (faster)
  python scripts/extract_keyphrases_from_papers.py \\
      --input Examples/blue_tea \\
      --output output.html \\
      --max-papers 10 \\
      --max-terms 50 \\
      --no-wikipedia
        """
    )
    
    parser.add_argument(
        '--input',
        '-i',
        type=str,
        required=True,
        help='Path to directory containing papers (PDFs or text files)'
    )
    parser.add_argument(
        '--output',
        '-o',
        type=str,
        required=True,
        help='Output HTML file path for the encyclopedia'
    )
    parser.add_argument(
        '--max-papers',
        type=int,
        default=10,
        help='Maximum number of papers to process (default: 10, CPU-intensive)'
    )
    parser.add_argument(
        '--title',
        type=str,
        default='Encyclopedia from Papers',
        help='Title for the encyclopedia (default: "Encyclopedia from Papers")'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=500,
        help='Number of top keyphrases to extract per paper (default: 500)'
    )
    parser.add_argument(
        '--max-terms',
        type=int,
        default=None,
        help='Maximum number of terms to include in encyclopedia (default: None = all terms). Useful for demonstrations (e.g., --max-terms 50)'
    )
    parser.add_argument(
        '--work-dir',
        type=str,
        help='Working directory for temporary files (default: temp/scripts/extract_keyphrases_from_papers)'
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
    
    args = parser.parse_args()
    
    # Validate input path
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        return 1
    
    if not input_path.is_dir():
        print(f"Error: Input path must be a directory: {input_path}")
        return 1
    
    # Set up output paths
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Set up working directory
    if args.work_dir:
        work_dir = Path(args.work_dir)
    else:
        work_dir = Resources.get_temp_dir("scripts", "extract_keyphrases_from_papers")
    work_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Keyphrase Extraction and Encyclopedia Creation")
    print(f"{'='*60}")
    print(f"Input directory: {input_path}")
    print(f"Max papers: {args.max_papers}")
    print(f"Top N keyphrases per paper: {args.top_n}")
    print(f"Output file: {output_file}")
    print(f"Working directory: {work_dir}")
    print(f"{'='*60}\n")
    
    try:
        # Step 1: Find papers (limited to max_papers)
        print("Step 1: Finding papers...")
        papers = find_papers(input_path, max_papers=args.max_papers, recursive=args.recursive)
        
        if not papers:
            print(f"\nError: No papers found in {input_path}")
            print("Please check:")
            print("  1. Directory contains PDF or text files")
            print("  2. Files are readable")
            return 1
        
        print(f"  Found {len(papers)} paper(s) to process")
        for i, paper in enumerate(papers[:args.max_papers], 1):
            print(f"    [{i}] {paper.name}")
        
        # Step 2: Extract keyphrases from papers
        print(f"\nStep 2: Extracting keyphrases (CPU-intensive, may take time)...")
        if args.max_terms:
            print(f"  Note: Encyclopedia will be limited to top {args.max_terms} terms by aggregated count")
        keyphrases = extract_keyphrases_from_papers(
            papers=papers,
            output_dir=work_dir,
            top_n=args.top_n,
            max_papers=args.max_papers,
            max_terms=args.max_terms
        )
        
        if not keyphrases:
            print("\nError: No keyphrases extracted from papers.")
            print("Please check:")
            print("  1. Papers contain readable text content")
            print("  2. txt2phrases is properly installed")
            print("  3. Check working directory for errors: {work_dir}")
            return 1
        
        # Step 3: Create encyclopedia from keyphrases
        print(f"\nStep 3: Creating encyclopedia from {len(keyphrases)} keyphrases...")
        encyclopedia = create_encyclopedia_from_keyphrases(
            keyphrases=keyphrases,
            title=args.title,
            add_wikipedia=args.add_wikipedia,
            add_images=args.add_images,
            batch_size=args.batch_size,
            validate=args.validate,
            verbose=args.verbose
        )
        
        # Step 4: Save encyclopedia
        print(f"\nStep 4: Saving encyclopedia...")
        print(f"  Output file: {output_file}")
        
        try:
            encyclopedia.save_wiki_normalized_html(output_file)
            print(f"\n  ✓ Encyclopedia saved successfully!")
            print(f"    File: {output_file}")
            print(f"    Entries: {len(encyclopedia.entries)}")
            print(f"    Keyphrases extracted: {len(keyphrases)}")
            print(f"    Papers processed: {len(papers[:args.max_papers])}")
            print(f"    Working directory: {work_dir}")
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
