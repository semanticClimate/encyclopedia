# cli.py
import argparse
import sys
import os

# Add the parent directory to Python path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from txt2phrases.pdf2txt import convert_pdf_to_text
from txt2phrases.html2txt import convert_html_to_text
from txt2phrases.keyword import KeywordExtraction
from txt2phrases.pygetpaper import main as pygetpaper_main

def main():
    parser = argparse.ArgumentParser(
        description="txt2phrases CLI: PDF/HTML → TXT → keywords",
        prog="txt2phrases"  # Explicitly set the program name
    )
    subparsers = parser.add_subparsers(
        dest="command", 
        required=True,
        help="Available commands"
    )

    # PDF2TXT
    parser_pdf = subparsers.add_parser("pdf2txt", help="Convert PDF(s) to TXT")
    parser_pdf.add_argument("-i", "--input", required=True, help="Input PDF file or folder")
    parser_pdf.add_argument("-o", "--output", required=True, help="Output folder")

    # HTML2TXT
    parser_html = subparsers.add_parser("html2txt", help="Convert HTML(s) to TXT")
    parser_html.add_argument("-i", "--input", required=True, help="Input HTML file or folder")
    parser_html.add_argument("-o", "--output", required=True, help="Output folder")

    # Keyword Extraction
    parser_keyword = subparsers.add_parser("keyphrases", help="Extract keywords from TXT files")
    parser_keyword.add_argument("-i", "--input", required=True, help="Input TXT file or folder")
    parser_keyword.add_argument("-o", "--output", required=True, help="Output folder")
    parser_keyword.add_argument("-n", "--top_n", type=int, default=1000, help="Top N keywords")

    # Auto pipeline
    parser_auto = subparsers.add_parser("auto", help="Run full pipeline: PDF → TXT → keywords")
    parser_auto.add_argument("-i", "--input", required=True, help="Input folder (PDFs or PyGetPapers output)")
    parser_auto.add_argument("-o", "--output", required=True, help="Output folder for TXT and keywords")
    parser_auto.add_argument("-n", "--num_keywords", type=int, default=100, help="Number of top keywords to extract")

    args = parser.parse_args()

    if args.command == "pdf2txt":
        # Handle PDF conversion directly
        from pathlib import Path
        
        input_path = Path(args.input)
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if input_path.is_file() and input_path.suffix.lower() == ".pdf":
            convert_pdf_to_text(input_path, output_path)
            print(f"Converted {input_path} to TXT")
        elif input_path.is_dir():
            pdf_files = list(input_path.glob("*.pdf"))
            print(f"Found {len(pdf_files)} PDF files to convert")
            
            for pdf_file in pdf_files:
                convert_pdf_to_text(pdf_file, output_path)
            
            print(f"All PDF files converted to TXT in: {output_path}")
        else:
            print("No PDF files found.")
            
    elif args.command == "html2txt":
        # Handle HTML conversion directly
        from pathlib import Path
        
        input_path = Path(args.input)
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if input_path.is_file() and input_path.suffix.lower() == ".html":
            convert_html_to_text(input_path, output_path)
            print(f"Converted {input_path} to TXT")
        elif input_path.is_dir():
            html_files = list(input_path.glob("*.html"))
            print(f"Found {len(html_files)} HTML files to convert")
            
            for html_file in html_files:
                convert_html_to_text(html_file, output_path)
            
            print(f"All HTML files converted to TXT in: {output_path}")
        else:
            print("No HTML files found.")
            
    elif args.command == "keyphrases":
        extractor = KeywordExtraction(
            input_path=args.input,
            output_folder=args.output,
            top_n=args.top_n
        )
        extractor.extract()
        
    elif args.command == "auto":
        # Call pygetpaper_main with the parsed arguments
        pygetpaper_main(["-i", args.input, "-o", args.output, "-n", str(args.num_keywords)])

if __name__ == "__main__":
    main()