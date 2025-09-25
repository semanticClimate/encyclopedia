import os
import argparse
from bs4 import BeautifulSoup

def html_to_txt_folder(input_folder, output_folder):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Loop through all files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith(".html"):
            input_path = os.path.join(input_folder, filename)
            output_filename = os.path.splitext(filename)[0] + ".txt"
            output_path = os.path.join(output_folder, output_filename)

            # Read and parse HTML
            with open(input_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
                text = soup.get_text()

            # Write plain text to new file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"Converted: {filename} → {output_filename}")

def main():
    import argparse
    from .html2txt import html_to_txt_folder  # your existing function

    parser = argparse.ArgumentParser(
        description="Convert HTML files to TXT files"
    )
    parser.add_argument(
        "-i", "--input", required=True, help="Input folder containing HTML files"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Output folder for TXT files"
    )

    args = parser.parse_args()
    html_to_txt_folder(args.input, args.output)


if __name__ == "__main__":
    main()
