# pygetpaper.py
#!/usr/bin/env python3
"""
auto_pipeline.py
----------------
Automatically detects PyGetPapers output directories,
converts PDFs to TXT (one TXT per folder), and extracts keyphrases using txt2phrases.

Usage:
    python auto_pipeline.py -i pygetpapers_output -o output -n 100
"""

import os
import shutil
import multiprocessing
from pathlib import Path
from tqdm import tqdm
import subprocess
import argparse
import sys

# Add the current package to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from txt2phrases.pdf2txt import convert_pdf_to_text
from txt2phrases.keyword import KeywordExtraction

# -----------------------------
# Detect PyGetPapers structure
# -----------------------------
def detect_pygetpapers_structure(input_path: Path) -> bool:
    """Detect if input has PyGetPapers output (subfolders with fulltext.pdf)."""
    if not input_path.is_dir():
        return False
    for sub in input_path.iterdir():
        if sub.is_dir() and any(f.name.startswith("fulltext") and f.suffix == ".pdf" for f in sub.iterdir()):
            return True
    return False

# -----------------------------
# Find all PDFs
# -----------------------------
def find_pdfs(base_path: Path):
    pdfs = []
    for root, _, files in os.walk(base_path):
        for f in files:
            if f.lower().endswith(".pdf"):
                f_path = Path(root) / f
                pdfs.append(f_path)
                print("Found PDF:", f_path)
    return pdfs

# -----------------------------
# Convert PDF → TXT
# -----------------------------
def convert_pdf_to_txt(pdf_path: Path, txt_output_dir: Path):
    """
    Convert a single PDF to TXT.
    TXT file will be named after the parent folder (e.g., PMC12492443.txt).
    """
    txt_output_dir.mkdir(parents=True, exist_ok=True)
    folder_name = pdf_path.parent.name

    print(f"Converting: {pdf_path}")
    try:
        # Use the imported function directly instead of subprocess
        txt_path = convert_pdf_to_text(pdf_path, txt_output_dir)
        
        if txt_path:
            # Rename the output file to use the folder name
            original_txt_path = Path(txt_path)
            final_txt = txt_output_dir / f"{folder_name}.txt"
            
            if original_txt_path.exists():
                # If the file already has the correct name, no need to rename
                if original_txt_path.name != final_txt.name:
                    original_txt_path.rename(final_txt)
                    return final_txt
                return original_txt_path
            else:
                print(f" Expected output file not found for {pdf_path}")
                return None

        return None
    except Exception as e:
        print(f"Conversion failed for {pdf_path}: {e}")
        return None

# -----------------------------
# Multiprocessing conversion
# -----------------------------
def convert_single_pdf(args):
    pdf, txt_output_dir = args
    return convert_pdf_to_txt(pdf, txt_output_dir)

def convert_all_pdfs(pdfs, txt_output_dir, workers=4):
    if not pdfs:
        print("No PDF files to convert.")
        return []

    os.makedirs(txt_output_dir, exist_ok=True)
    print(f"\ Converting {len(pdfs)} PDFs to TXT...")

    args = [(pdf, txt_output_dir) for pdf in pdfs]

    try:
        with multiprocessing.Pool(processes=workers) as pool:
            results = list(
                tqdm(
                    pool.imap_unordered(convert_single_pdf, args),
                    total=len(pdfs),
                    desc="Converting PDFs",
                )
            )
    except Exception as e:
        print(f"⚠️ Multiprocessing failed ({e}), switching to sequential mode.")
        results = []
        for pdf in tqdm(pdfs, desc="Converting PDFs (sequential)"):
            results.append(convert_pdf_to_txt(pdf, txt_output_dir))

    return [r for r in results if r]

# -----------------------------
# Run Keyword Extraction
# -----------------------------
def run_keyword_extraction(input_path: Path, output_dir: Path, top_n: int):
    """Run keyword extraction directly using the imported class."""
    try:
        extractor = KeywordExtraction(
            input_path=str(input_path),
            output_folder=str(output_dir),
            top_n=top_n
        )
        extractor.extract()
    except Exception as e:
        print(f"Keyword extraction failed: {e}")

# -----------------------------
# Main Pipeline
# -----------------------------
def main(args=None):
    parser = argparse.ArgumentParser(
        description="Process PyGetPapers output (PDF → TXT → keyphrases)."
    )
    parser.add_argument("-i", "--input", required=True, help="Input folder (PyGetPapers output or PDFs)")
    parser.add_argument("-o", "--output", required=True, help="Output folder for TXT and keyword CSVs")
    parser.add_argument("-n", "--num_keywords", type=int, default=100, help="Number of top keywords to extract")
    
    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    if detect_pygetpapers_structure(input_path):
        print("Detected PyGetPapers-style folder structure.")
    else:
        print("Standard folder detected.")

    pdfs = find_pdfs(input_path)
    print(f"Found {len(pdfs)} PDFs.")

    if pdfs:
        txt_dir = output_path / "txt"
        converted_txts = convert_all_pdfs(pdfs, txt_dir)
        print(f"Converted {len(converted_txts)} PDFs to TXT.")

        print("\nRunning keyword extraction...")
        run_keyword_extraction(txt_dir, output_path, args.num_keywords)
        print("\nAuto-pipeline complete!")
    else:
        print("No PDF files found to process.")

if __name__ == "__main__":
    multiprocessing.freeze_support()  # Required for Windows
    main()




