import os
from bs4 import BeautifulSoup
import pandas as pd
from Keyword_extraction import KeywordExtraction  # your cleaned KeywordExtraction class
from classification import classify_keywords   # your TF-IDF classification function

class KeywordPipelineWrapper:
    """
    A wrapper class to process HTML files → TXT → Keyword Extraction → TF-IDF General/Specific classification.
    """

    def __init__(self, html_input_folder, txt_output_folder, keyword_output_folder, classified_output_folder,
                 top_n=3500, min_count=3, tfidf_threshold=0.6, tfidf_min_freq=5):
        self.html_input_folder = html_input_folder
        self.txt_output_folder = txt_output_folder
        self.keyword_output_folder = keyword_output_folder
        self.classified_output_folder = classified_output_folder

        self.top_n = top_n
        self.min_count = min_count
        self.tfidf_threshold = tfidf_threshold
        self.tfidf_min_freq = tfidf_min_freq

        # Ensure all folders exist
        os.makedirs(self.txt_output_folder, exist_ok=True)
        os.makedirs(self.keyword_output_folder, exist_ok=True)
        os.makedirs(self.classified_output_folder, exist_ok=True)

    # -----------------------------
    # Step 1: Convert HTML → TXT
    # -----------------------------
    def html_to_txt(self):
        html_files = [f for f in os.listdir(self.html_input_folder) if f.endswith(".html")]
        for filename in html_files:
            input_path = os.path.join(self.html_input_folder, filename)
            output_filename = os.path.splitext(filename)[0] + ".txt"
            output_path = os.path.join(self.txt_output_folder, output_filename)

            with open(input_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
                text = soup.get_text()

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"Converted: {filename} → {output_filename}")

    # -----------------------------
    # Step 2: Extract Keywords from TXT
    # -----------------------------
    def extract_keywords(self):
        txt_files = [f for f in os.listdir(self.txt_output_folder) if f.endswith(".txt")]
        for txt_file in txt_files:
            input_path = os.path.join(self.txt_output_folder, txt_file)
            base_name = os.path.splitext(txt_file)[0]
            output_filename = base_name + "_keywords.csv"

            print(f"\nProcessing keyword extraction: {txt_file} ...")

            extractor = KeywordExtraction(
                textfile=input_path,
                saving_path=self.keyword_output_folder,
                output_filename=output_filename,
                top_n=self.top_n,
            )
            extractor.extract_keywords()

    # -----------------------------
    # Step 3: Classify Keywords (TF-IDF)
    # -----------------------------
    def classify_keywords(self):
        classify_keywords(
            input_dir=self.keyword_output_folder,
            output_dir=self.classified_output_folder,
            threshold=self.tfidf_threshold,
            min_freq=self.tfidf_min_freq
        )

    # -----------------------------
    # Full pipeline execution
    # -----------------------------
    def run_pipeline(self):
        print("\nStep 1: Converting HTML to TXT ...")
        self.html_to_txt()

        print("\nStep 2: Extracting Keywords from TXT files ...")
        self.extract_keywords()

        print("\nStep 3: Classifying Keywords into General/Specific ...")
        self.classify_keywords()

        print("\nPipeline completed successfully!")


# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Full Keyword Extraction & Classification Pipeline")
    parser.add_argument("-i", "--html_input", required=True, help="Folder containing HTML files")
    parser.add_argument("-t", "--txt_output", required=True, help="Folder to save TXT files")
    parser.add_argument("-k", "--keyword_output", required=True, help="Folder to save extracted keyword CSVs")
    parser.add_argument("-c", "--classified_output", required=True, help="Folder to save classified CSVs")
    parser.add_argument("--top_n", type=int, default=3500, help="Top N keywords to extract")
    parser.add_argument("--tfidf_threshold", type=float, default=0.6, help="TF-IDF threshold for Specific keywords")
    parser.add_argument("--tfidf_min_freq", type=int, default=5, help="Minimum frequency to consider for TF-IDF")

    args = parser.parse_args()

    pipeline = KeywordPipelineWrapper(
        html_input_folder=args.html_input,
        txt_output_folder=args.txt_output,
        keyword_output_folder=args.keyword_output,
        classified_output_folder=args.classified_output,
        top_n=args.top_n,
        tfidf_threshold=args.tfidf_threshold,
        tfidf_min_freq=args.tfidf_min_freq
    )

    pipeline.run_pipeline()
