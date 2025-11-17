import os
import re
from collections import Counter
import pandas as pd
from tqdm import tqdm
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
    Customized Hugging Face TokenClassificationPipeline
    optimized for extracting keyphrases.
    """

    def __init__(self, model_name):
        super().__init__(
            model=AutoModelForTokenClassification.from_pretrained(model_name),
            tokenizer=AutoTokenizer.from_pretrained(model_name),
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
    Extracts keywords from a TXT file or folder of TXT files.
    """

    def __init__(self, input_path, output_folder, top_n=1000):
        self.input_path = input_path
        self.output_folder = output_folder
        self.top_n = top_n
        os.makedirs(self.output_folder, exist_ok=True)

        self.model_name = "ml6team/keyphrase-extraction-kbir-inspec"
        self.extractor = KeyphraseExtractionPipeline(model_name=self.model_name)

    def _read_text(self, file_path, method="sentence"):
        """
        Read a single TXT file and split into chunks/sentences.
        """
        with open(file_path, encoding="utf-8") as f:
            full_text = f.read().strip()

        if method == "sentence":
            text = re.split(r'(?<=[.!?])\s+', full_text)
        elif method == "chunk":
            words = full_text.split()
            chunk_size = 300
            text = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
        else:
            text = [full_text]

        return text

    def _process_single_file(self, file_path):
        """
        Extract keywords from a single TXT file.
        """
        text_chunks = self._read_text(file_path, method="sentence")
        keyphrases = []

        for i in tqdm(range(0, len(text_chunks), 16), desc=f"Extracting {os.path.basename(file_path)}"):
            batch = text_chunks[i:i + 16]
            batch_phrases_list = self.extractor(batch, batch_size=16)
            for phrases in batch_phrases_list:
                keyphrases.extend(phrases)

        counts = Counter(keyphrases)
        top_keywords = counts.most_common(self.top_n)

        df = pd.DataFrame(top_keywords, columns=["keyword", "count"])
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_csv = os.path.join(self.output_folder, f"{base_name}_keywords.csv")
        df.to_csv(output_csv, index=False)

        print(f"Saved: {output_csv}")
        return output_csv

    def extract(self):
        """
        Handle single file or folder input automatically.
        """
        if os.path.isfile(self.input_path) and self.input_path.lower().endswith(".txt"):
            self._process_single_file(self.input_path)

        elif os.path.isdir(self.input_path):
            txt_files = [f for f in os.listdir(self.input_path) if f.lower().endswith(".txt")]
            print(f"Found {len(txt_files)} text files to process.\n")

            for txt_file in txt_files:
                file_path = os.path.join(self.input_path, txt_file)
                self._process_single_file(file_path)

            print(f"\nAll keyword CSVs saved in: {self.output_folder}")
        else:
            raise ValueError(" Please provide a valid TXT file or folder path.")


# -----------------------------
# CLI
# -----------------------------
def main(args=None):
    import argparse

    parser = argparse.ArgumentParser(description="Extract keywords from TXT files (fast mode)")
    parser.add_argument("-i", "--input", required=True, help="Path to TXT file or folder containing TXT files")
    parser.add_argument("-o", "--output", required=True, help="Folder to save keyword CSVs")
    parser.add_argument("-n", "--top_n", type=int, default=1000, help="Number of top keywords to extract")

    args = parser.parse_args()

    extractor = KeywordExtraction(
        input_path=args.input,
        output_folder=args.output,
        top_n=args.top_n
    )
    extractor.extract()


if __name__ == "__main__":
    main()