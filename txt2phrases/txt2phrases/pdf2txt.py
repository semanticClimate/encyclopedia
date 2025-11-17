# pdf2txt.py
import os
import argparse
from pathlib import Path
from PyPDF2 import PdfReader
from tqdm import tqdm

def convert_pdf_to_text(pdf_path, output_folder):
    """
    Convert a single PDF file to a TXT file and save it.
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        txt_path = os.path.join(output_folder, base_name + ".txt")

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        return txt_path
    except Exception as e:
        print(f"[ERROR] Failed to process {pdf_path}: {e}")
        return None

def main(args=None):
    parser = argparse.ArgumentParser(description="Convert PDF to TXT")
    parser.add_argument("-i", "--input", required=True, help="PDF file or folder")
    parser.add_argument("-o", "--output", required=True, help="Output folder")
    
    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        result = convert_pdf_to_text(input_path, output_path)
        if result:
            print(f"Successfully converted {input_path} to TXT")
        else:
            print(f"Failed to convert {input_path}")
    elif input_path.is_dir():
        pdf_files = list(input_path.glob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files to convert")
        
        successful_conversions = 0
        for pdf_file in tqdm(pdf_files, desc="Converting PDFs"):
            result = convert_pdf_to_text(pdf_file, output_path)
            if result:
                successful_conversions += 1
        
        print(f"Successfully converted {successful_conversions}/{len(pdf_files)} PDF files to TXT in: {output_path}")
    else:
        print("No PDF files found.")

if __name__ == "__main__":
    main()
