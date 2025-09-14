import os
from bs4 import BeautifulSoup
import pandas as pd
from Keyword_extraction import KeywordExtraction  # your cleaned KeywordExtraction class
from classification import classify_keywords_split_files  # TF-IDF General/Specific classification
from hybridclassification import classify_keywords as hybrid_classify  # Hybrid Wikidata + ML classifier

class KeywordPipelineWrapper:
    """
    A wrapper class to process HTML files → TXT → Keyword Extraction → 
    TF-IDF General/Specific classification → Hybrid Wikidata/ML classification.
    """

    def __init__(self, html_input_folder, txt_output_folder, keyword_output_folder,
                 tfidf_output_folder, hybrid_output_folder, top_n=3500, min_count=3,
                 tfidf_threshold=0.6, tfidf_min_freq=5):
        self.html_input_folder = html_input_folder
        self.txt_output_folder = txt_output_folder
        self.keyword_output_folder = keyword_output_folder
        self.tfidf_output_folder = tfidf_output_folder
        self.hybrid_output_folder = hybrid_output_folder

        self.top_n = top_n
        self.min_count = min_count
        self.tfidf_threshold = tfidf_threshold
        self.tfidf_min_freq = tfidf_min_freq

        # Ensure all folders exist
        os.makedirs(self.txt_output_folder, exist_ok=True)
        os.makedirs(self.keyword_output_folder, exist_ok=True)
        os.makedirs(self.tfidf_output_folder, exist_ok=True)
        os.makedirs(self.hybrid_output_folder, exist_ok=True)

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
    # Step 3: TF-IDF General/Specific Classification
    # -----------------------------
    def classify_keywords_tfidf(self):
        print("\nRunning TF-IDF General/Specific classification ...")
        classify_keywords_split_files(
            input_dir=self.keyword_output_folder,
            output_dir=self.tfidf_output_folder,
            threshold=self.tfidf_threshold,
            min_freq=self.tfidf_min_freq
        )

    # -----------------------------
    # Step 4: Hybrid Wikidata + ML Classification
    # -----------------------------
    def classify_keywords_hybrid(self):
        csv_files = [f for f in os.listdir(self.keyword_output_folder) if f.endswith(".csv")]
        for csv_file in csv_files:
            input_path = os.path.join(self.keyword_output_folder, csv_file)
            print(f"\nRunning Hybrid classification on: {csv_file} ...")
            hybrid_classify(
                input_file=input_path,
                output_dir=self.hybrid_output_folder,
                sleep_time=0.2
            )

    # -----------------------------
    # Full pipeline execution
    # -----------------------------
    def run_pipeline(self):
        print("\nStep 1: Converting HTML to TXT ...")
        self.html_to_txt()

        print("\nStep 2: Extracting Keywords from TXT files ...")
        self.extract_keywords()

        print("\nStep 3: TF-IDF General/Specific classification ...")
        self.classify_keywords_tfidf()

        print("\nStep 4: Hybrid Wikidata + ML classification ...")
        self.classify_keywords_hybrid()

        print("\nPipeline completed successfully!")


# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Full Keyword Extraction & Dual Classification Pipeline")
    parser.add_argument("-i", "--html_input", required=True, help="Folder containing HTML files")
    parser.add_argument("-t", "--txt_output", required=True, help="Folder to save TXT files")
    parser.add_argument("-k", "--keyword_output", required=True, help="Folder to save extracted keyword CSVs")
    parser.add_argument("-g", "--tfidf_output", required=True, help="Folder to save TF-IDF classified CSVs")
    parser.add_argument("-h", "--hybrid_output", required=True, help="Folder to save Hybrid classified CSVs")
    parser.add_argument("--top_n", type=int, default=3500, help="Top N keywords to extract")
    parser.add_argument("--tfidf_threshold", type=float, default=0.6, help="TF-IDF threshold for specificity")
    parser.add_argument("--tfidf_min_freq", type=int, default=5, help="Minimum frequency for TF-IDF")

    args = parser.parse_args()

    pipeline = KeywordPipelineWrapper(
        html_input_folder=args.html_input,
        txt_output_folder=args.txt_output,
        keyword_output_folder=args.keyword_output,
        tfidf_output_folder=args.tfidf_output,
        hybrid_output_folder=args.hybrid_output,
        top_n=args.top_n,
        tfidf_threshold=args.tfidf_threshold,
        tfidf_min_freq=args.tfidf_min_freq
    )

    pipeline.run_pipeline()

