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
    Extracts the most important keywords from a text file using a model.
    """

    def __init__(self, textfile, saving_path, output_filename="keywords.csv", top_n=1000):
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

    def clean_text(self, text):
        """Basic cleaning: remove unwanted tokens, multiple spaces, etc."""
        text = re.sub(r'\s+', ' ', text)  # collapse multiple spaces
        text = re.sub(r'[^\w\s.,!?]', '', text)  # remove weird characters
        return text.strip()

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

            # Clean each chunk before feeding
            batch_lines = [self.clean_text(line) for line in batch_lines if line.strip()]

            if not batch_lines:
                continue

            try:
                batch_keyphrases_list = extractor(batch_lines)
                for keyphrases in batch_keyphrases_list:
                    self.keyphrases.extend(keyphrases)
            except Exception as e:
                print(f"\nSkipping batch {i // batch_size} due to error: {e}\n")
                continue

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

        print(f"Total unique keywords: {len(self.keyphrases)}")
        print(f"Top 10 keywords: {self.keyphrase_counts.most_common(10)}")
        return top_keywords


# -----------------------------
# CLI (Folder Only)
# -----------------------------
if __name__ == "__main__":
    parser = ArgumentParser(description="Extract keywords from all TXT files in a folder.")
    parser.add_argument("-f", "--input_folder", required=True, help="Folder containing TXT files")
    parser.add_argument("-o", "--output_folder", required=True, help="Folder to save outputs")
    parser.add_argument("-n", "--top_n", type=int, default=3500,
                        help="Number of top keywords to extract")

    args = parser.parse_args()

    os.makedirs(args.output_folder, exist_ok=True)

    # Process all files in the input folder
    txt_files = [f for f in os.listdir(args.input_folder) if f.endswith(".txt")]
    for txt_file in txt_files:
        input_path = os.path.join(args.input_folder, txt_file)
        base_name = os.path.splitext(txt_file)[0]
        output_filename = base_name + "_keywords.csv"

        print(f"\nProcessing {txt_file} ...")
        extractor = KeywordExtraction(
            textfile=input_path,
            saving_path=args.output_folder,
            output_filename=output_filename,
            top_n=args.top_n
        )
        extractor.extract_keywords()





