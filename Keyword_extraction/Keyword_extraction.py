import os
import re
from collections import Counter
import pandas as pd
from tqdm import tqdm
from argparse import ArgumentParser
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
    KeywordExtraction
    -----------------
    Extracts the most important keywords from a text file
    using a machine learning model.

    Parameters:
    - textfile: Path to the .txt file you want to analyze.
    - saving_path: Folder where the results (CSV file) will be saved.
    - output_filename: Name of the output CSV file (default: "top_keywords.csv").
    - top_n: Number of top keywords to keep (default: 1000).
    """

    def __init__(self, textfile="", saving_path="", output_filename="top_keywords.csv", top_n=1000):
        self.text = []
        self.keyphrases = []
        self.output_filename = output_filename
        self.top_n = top_n

        # Validate text file
        if textfile and os.path.isfile(textfile) and textfile.endswith(".txt"):
            self.textfile = textfile
        else:
            raise ValueError('Please provide a valid text file path ending with ".txt"')

        # Validate saving path
        if os.path.isdir(saving_path):
            self.saving_path = saving_path
        else:
            raise ValueError('Please provide a valid saving path')

    # -----------------------------
    # Read and split text file
    # -----------------------------
    def read_from_text_file(self, method="sentence"):
        """
        Reads text from the file and splits it into smaller pieces.

        Options for splitting:
        - "sentence": Breaks text into sentences using punctuation (. ? !).
        - "chunk": Breaks text into groups of 300 words each.
        - otherwise: Treats the whole file as one single block of text.
        """
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
        """
        Main function to extract keywords.

        Steps:
        1. Reads and splits your text file into smaller parts.
        2. Loads a pre-trained keyword extraction model.
        3. Processes the text in groups (batch_size = how many chunks at once).
        4. Collects all keywords and counts how often they appear.
        5. Keeps only the top N keywords (N is user-defined).
        6. Saves them into a CSV file.

        Returns:
        - A list of top keywords found in the text.
        """
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

        # Top N keywords
        top_keywords = [kw for kw, _ in self.keyphrase_counts.most_common(self.top_n)]

        # Save CSV safely
        os.makedirs(self.saving_path, exist_ok=True)
        output_file = os.path.join(self.saving_path, self.output_filename)
        df = pd.DataFrame(self.keyphrase_counts.most_common(self.top_n), columns=["keyword", "count"])
        df.to_csv(output_file, index=False)
        print(f"\nCSV saved successfully: {output_file}")

        print(f"Total unique keywords: {len(self.keyphrases)}")
        print(f"Top 10 keywords: {self.keyphrase_counts.most_common(10)}")
        return top_keywords

    def main(self):
        return self.extract_keywords()


# -----------------------------
# Command Line Interface
# -----------------------------
if __name__ == "__main__":
    parser = ArgumentParser(description="Extract top keywords from a text file using AI.")
    parser.add_argument('-t', '--text_file', required=True, help='Path to text file (.txt)')
    parser.add_argument('-s', '--saving_path', required=True, help='Path to save CSV output')
    parser.add_argument('-o', '--output_filename', default="top_keywords.csv",
                        help='Name of the output CSV file (default: top_keywords.csv)')
    parser.add_argument('-n', '--top_n', type=int, default=1000,
                        help='Number of top keywords to extract (default: 1000)')
    args = parser.parse_args()

    extractor = KeywordExtraction(
        textfile=args.text_file,
        saving_path=args.saving_path,
        output_filename=args.output_filename,
        top_n=args.top_n
    )
    extractor.main()
