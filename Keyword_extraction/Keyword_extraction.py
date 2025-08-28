import os
import re
from collections import Counter
import pandas as pd
from tqdm import tqdm
from argparse import ArgumentParser
from bs4 import BeautifulSoup
from transformers import (
    TokenClassificationPipeline,
    AutoModelForTokenClassification,
    AutoTokenizer,
)
from transformers.pipelines import AggregationStrategy


# -----------------------------
# Keyphrase Extraction Pipeline
# -----------------------------
class KeyphraseExtractionPipeline(TokenClassificationPipeline):
    """
    A customized Hugging Face TokenClassificationPipeline
    for extracting keywords/keyphrases.
    """

    def __init__(self, model_name, *args, **kwargs):
        super().__init__(
            model=AutoModelForTokenClassification.from_pretrained(model_name),
            tokenizer=AutoTokenizer.from_pretrained(model_name),
            *args,
            **kwargs
        )

    def postprocess(self, *args, **kwargs):
        results = super().postprocess(
            *args,
            aggregation_strategy=AggregationStrategy.SIMPLE,
            **kwargs
        )
        return [result.get("word").strip() for result in results if result.get("word")]


# -----------------------------
# Keyword Extraction Class
# -----------------------------
class KeywordExtraction:
    """
    Extracts the most important keywords from a text file using a model.
    """

    def __init__(self, textfile, saving_path, output_filename="top_keywords.csv", top_n=1000):
        self.text = []
        self.keyphrases = []
        self.output_filename = output_filename
        self.top_n = top_n

        if textfile and os.path.isfile(textfile) and textfile.endswith(".txt"):
            self.textfile = textfile
        else:
            raise ValueError('Please provide a valid text file path ending with ".txt"')

        if os.path.isdir(saving_path):
            self.saving_path = saving_path
        else:
            raise ValueError('Please provide a valid saving path')

    # -----------------------------
    # Read and split text file
    # -----------------------------
    def read_from_text_file(self, method="sentence"):
        with open(self.textfile, encoding="utf-8") as f:
            full_text = f.read().strip()

        if method == "sentence":
            self.text = re.split(r'(?<=[.!?])\s+', full_text)
        elif method == "chunk":
            words = full_text.split()
            chunk_size = 300
            self.text = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        else:
            self.text = [full_text]

        print(f"Total text chunks to process: {len(self.text)}")
        print(f"First chunk preview: {self.text[0][:200]}...\n")

    # -----------------------------
    # Extract Keywords in batches
    # -----------------------------
    def extract_keywords(self, batch_size=16):
        self.read_from_text_file(method="sentence")

        model_name = "ml6team/keyphrase-extraction-kbir-inspec"
        extractor = KeyphraseExtractionPipeline(model_name=model_name)

        for i in tqdm(range(0, len(self.text), batch_size), desc="Extracting keywords"):
            batch_lines = self.text[i:i + batch_size]
            batch_keyphrases_list = extractor(batch_lines)
            for keyphrases in batch_keyphrases_list:
                self.keyphrases.extend(keyphrases)

        # Count keywords
        self.keyphrase_counts = Counter(self.keyphrases)
        self.keyphrases = list(set(self.keyphrases))

        # Top N
        top_keywords = [kw for kw, _ in self.keyphrase_counts.most_common(self.top_n)]

        # Save CSV
        os.makedirs(self.saving_path, exist_ok=True)
        output_file = os.path.join(self.saving_path, self.output_filename)
        df = pd.DataFrame(self.keyphrase_counts.most_common(self.top_n), columns=["keyword", "count"])
        df.to_csv(output_file, index=False)
        print(f"\nCSV saved successfully: {output_file}")

        # Save keywords-only file
        keywords_only_file = os.path.join(self.saving_path, "top_keywords_only.txt")
        with open(keywords_only_file, "w", encoding="utf-8") as f:
            for kw in top_keywords:
                f.write(kw + "\n")
        print(f"Keywords-only text file saved: {keywords_only_file}")

        print(f"Total unique keywords: {len(self.keyphrases)}")
        print(f"Top 10 keywords: {self.keyphrase_counts.most_common(10)}")
        return top_keywords


# -----------------------------
# HTML to Text Converter
# -----------------------------
def html_to_text(input_html, output_txt):
    with open(input_html, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")
    text = soup.get_text()
    with open(output_txt, "w", encoding="utf-8") as output:
        output.write(text)
    print(f"✅ Extracted text saved to: {output_txt}")


# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    parser = ArgumentParser(description="Convert HTML to text and extract keywords.")
    parser.add_argument("-i", "--input_html", required=True, help="Path to input HTML file")
    parser.add_argument("-s", "--saving_path", required=True, help="Path to save outputs")
    parser.add_argument("-o", "--output_filename", default="top_keywords.csv",
                        help="Name of the output CSV file (default: top_keywords.csv)")
    parser.add_argument("-n", "--top_n", type=int, default=1000,
                        help="Number of top keywords to extract")
    args = parser.parse_args()

    # Convert HTML -> TXT
    txt_file = os.path.join(args.saving_path, "chapter_text.txt")
    html_to_text(args.input_html, txt_file)

    # Extract Keywords
    extractor = KeywordExtraction(
        textfile=txt_file,
        saving_path=args.saving_path,
        output_filename=args.output_filename,
        top_n=args.top_n
    )
    extractor.extract_keywords()

