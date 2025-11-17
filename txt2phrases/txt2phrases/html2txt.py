import os
import argparse
from bs4 import BeautifulSoup
from tqdm import tqdm

def convert_html_to_text(html_path, output_folder):
    """
    Convert a single HTML file to plain text and save it.
    """
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator="\n", strip=True)

        base_name = os.path.splitext(os.path.basename(html_path))[0]
        txt_path = os.path.join(output_folder, base_name + ".txt")

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        return txt_path
    except Exception as e:
        print(f"[ERROR] Failed to process {html_path}: {e}")
        return None


def main(args=None):
    parser = argparse.ArgumentParser(description="Convert HTML files to TXT automatically")
    parser.add_argument(
        "-i", "--input", required=True,
        help="Path to an HTML file or a folder containing multiple HTML files"
    )
    parser.add_argument(
        "-o", "--output", required=True,
        help="Folder to save converted TXT files"
    )

    args = parser.parse_args()

    input_path = args.input
    output_folder = args.output
    os.makedirs(output_folder, exist_ok=True)

    # Single file mode
    if os.path.isfile(input_path) and input_path.lower().endswith(".html"):
        print(f"Converting single file: {os.path.basename(input_path)}")
        txt_path = convert_html_to_text(input_path, output_folder)
        if txt_path:
            print(f"[DONE] Saved: {txt_path}")

    # Folder mode
    elif os.path.isdir(input_path):
        html_files = [f for f in os.listdir(input_path) if f.lower().endswith(".html")]
        print(f"Found {len(html_files)} HTML files to convert.\n")

        for html_file in tqdm(html_files, desc="Converting HTML files"):
            html_path = os.path.join(input_path, html_file)
            convert_html_to_text(html_path, output_folder)

        print(f"\nAll HTML files converted to TXT in: {output_folder}")

    else:
        print("[ERROR] Please provide a valid HTML file or folder path.")


if __name__ == "__main__":
    main()

