from bs4 import BeautifulSoup
from argparse import ArgumentParser

def html_to_text(input_html, output_txt):
    """
    Converts an HTML file into plain text and saves it as a .txt file.

    Parameters:
    - input_html (str): Path to the input HTML file.
    - output_txt (str): Path to the output TXT file.
    """
    # Load HTML and extract text
    with open(input_html, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    # Extract plain text from HTML
    text = soup.get_text()

    # Save extracted text into output file
    with open(output_txt, "w", encoding="utf-8") as output:
        output.write(text)

    print(f"✅ Extracted text saved to: {output_txt}")


if __name__ == "__main__":
    parser = ArgumentParser(description="Convert an HTML file into a plain text file.")
    parser.add_argument("-i", "--input_html", required=True, help="Path to the input HTML file")
    parser.add_argument("-o", "--output_txt", required=True, help="Path to save the extracted text file")
    args = parser.parse_args()

    html_to_text(args.input_html, args.output_txt)
