import os
import pandas as pd
from collections import defaultdict
from argparse import ArgumentParser
from sklearn.feature_extraction.text import TfidfTransformer


def classify_keywords_split_files(input_dir, output_dir, threshold=0.6, min_freq=5):
    """
    For each chapter, create a separate CSV listing keywords that are 'specific' to it
    according to TF-IDF >= threshold.

    Input: multiple chapter CSVs in `input_dir`, each with columns: keyword, count
    Output: one file per chapter in `output_dir`: <chapter>_specific_keywords.csv
            columns -> keyword, tfidf, count
    """

    os.makedirs(output_dir, exist_ok=True)

    # --- Load per-chapter frequencies (with min_freq filtering) ---
    chapter_files = [f for f in os.listdir(input_dir) if f.endswith(".csv")]
    if not chapter_files:
        print(f"No CSV files found in {input_dir}")
        return

    keyword_chapter_freq = defaultdict(dict)  # {keyword: {chapter: count}}
    chapters = []

    for file in chapter_files:
        chapter = os.path.splitext(file)[0]
        chapters.append(chapter)
        df = pd.read_csv(os.path.join(input_dir, file))
        # Ensure required columns exist
        if not {"keyword", "count"}.issubset(df.columns):
            raise ValueError(f"{file} must contain 'keyword' and 'count' columns")

        # Filter by min frequency
        df = df[df["count"] >= min_freq]

        for _, row in df.iterrows():
            keyword = str(row["keyword"])
            freq = int(row["count"])
            keyword_chapter_freq[keyword][chapter] = freq

    chapters = sorted(chapters)
    keywords = list(keyword_chapter_freq.keys())

    # Handle edge case: no keywords survive min_freq
    if not keywords:
        # still create empty files per chapter with headers
        for chapter in chapters:
            out_path = os.path.join(output_dir, f"{chapter}_specific_keywords.csv")
            pd.DataFrame(columns=["keyword", "tfidf", "count"]).to_csv(out_path, index=False)
            print(f"Saved (empty) {out_path}")
        return

    # --- Build keyword x chapter matrix ---
    data = []
    for kw in keywords:
        row = [keyword_chapter_freq[kw].get(ch, 0) for ch in chapters]
        data.append(row)
    df_matrix = pd.DataFrame(data, index=keywords, columns=chapters)

    # --- TF-IDF over (keywords x chapters) ---
    transformer = TfidfTransformer()
    tfidf_matrix = transformer.fit_transform(df_matrix)  # sparse

    # --- For each chapter, collect keywords specific to it ---
    for j, chapter in enumerate(chapters):
        rows = []
        for i, keyword in enumerate(df_matrix.index):
            score = tfidf_matrix[i, j]
            if score >= threshold:
                freq_in_chapter = int(df_matrix.iloc[i, j])
                # Optionally skip if freq is zero (rare when score >= threshold, but safe):
                if freq_in_chapter > 0:
                    rows.append((keyword, float(score), freq_in_chapter))

        # Sort by TF-IDF descending, then by frequency descending
        rows.sort(key=lambda x: (x[1], x[2]), reverse=True)

        out_df = pd.DataFrame(rows, columns=["keyword", "tfidf", "count"])
        out_path = os.path.join(output_dir, f"{chapter}_specific_keywords.csv")
        out_df.to_csv(out_path, index=False)
        print(f"Saved {out_path} ({len(out_df)} keywords)")


if __name__ == "__main__":
    parser = ArgumentParser(description="Create per-chapter files of TF-IDF-specific keywords")
    parser.add_argument("-i", "--input_dir", required=True, help="Path to folder with chapter CSVs (keyword,count)")
    parser.add_argument("-o", "--output_dir", required=True, help="Path to save per-chapter specific keyword files")
    parser.add_argument("-t", "--threshold", type=float, default=0.6, help="TF-IDF threshold for specificity")
    parser.add_argument("-f", "--min_freq", type=int, default=5, help="Minimum frequency of keywords to consider")
    args = parser.parse_args()

    classify_keywords_split_files(args.input_dir, args.output_dir, args.threshold, args.min_freq)










