import os
import pandas as pd
from collections import defaultdict
from argparse import ArgumentParser
from sklearn.feature_extraction.text import TfidfTransformer


def classify_keywords_split_files(input_dir, output_dir, threshold=0.6, min_freq=5):
    """
    For each chapter, create a separate CSV listing keywords that are 'specific' to it
    according to TF-IDF >= threshold. Also, create a single CSV with general/specific chapters.

    Input: multiple chapter CSVs in `input_dir`, each with columns: keyword, count
    Output:
        - <chapter>_specific_keywords.csv in `output_dir`
        - general_specific_keywords.csv in `output_dir`
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
        if not {"keyword", "count"}.issubset(df.columns):
            raise ValueError(f"{file} must contain 'keyword' and 'count' columns")
        df = df[df["count"] >= min_freq]
        for _, row in df.iterrows():
            keyword_chapter_freq[str(row["keyword"])][chapter] = int(row["count"])

    chapters = sorted(chapters)
    keywords = list(keyword_chapter_freq.keys())

    if not keywords:
        # create empty files if no keywords pass min_freq
        for chapter in chapters:
            pd.DataFrame(columns=["keyword", "tfidf", "count"]).to_csv(
                os.path.join(output_dir, f"{chapter}_specific_keywords.csv"), index=False
            )
        pd.DataFrame(columns=["keyword", "General", "Specific"]).to_csv(
            os.path.join(output_dir, "general_specific_keywords.csv"), index=False
        )
        print("No keywords passed min_freq. Empty files created.")
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

    # --- For each chapter, collect specific keywords ---
    for j, chapter in enumerate(chapters):
        rows = []
        for i, keyword in enumerate(df_matrix.index):
            score = tfidf_matrix[i, j]
            freq_in_chapter = int(df_matrix.iloc[i, j])
            if score >= threshold and freq_in_chapter > 0:
                rows.append((keyword, float(score), freq_in_chapter))
        rows.sort(key=lambda x: (x[1], x[2]), reverse=True)
        pd.DataFrame(rows, columns=["keyword", "tfidf", "count"]).to_csv(
            os.path.join(output_dir, f"{chapter}_specific_keywords.csv"), index=False
        )
        print(f"Saved {chapter}_specific_keywords.csv ({len(rows)} keywords)")

    # --- Generate general/specific keywords file ---
    general_specific_rows = []
    for i, keyword in enumerate(df_matrix.index):
        specific_chapters = []
        general_chapters = []
        for j, chapter in enumerate(chapters):
            score = tfidf_matrix[i, j]
            if score >= threshold:
                specific_chapters.append(chapter)
            else:
                general_chapters.append(chapter)
        general_specific_rows.append((
            keyword,
            " ".join(general_chapters),
            " ".join(specific_chapters)
        ))

    out_df = pd.DataFrame(general_specific_rows, columns=["keyword", "General", "Specific"])
    out_path = os.path.join(output_dir, "general_specific_keywords.csv")
    out_df.to_csv(out_path, index=False)
    print(f"Saved general_specific_keywords.csv ({len(out_df)} keywords)")


def main():
    """
    Command-line interface for generating per-chapter specific keywords
    and a general/specific keywords CSV.
    """
    import argparse
    from .classify_specific import classify_keywords_split_files
    import os
    parser = argparse.ArgumentParser(
        description="Create per-chapter files of TF-IDF-specific keywords "
                    "and a general/specific keywords CSV"
    )
    parser.add_argument(
        "-i", "--input_dir", required=True,
        help="Path to folder with chapter CSVs (keyword,count)"
    )
    parser.add_argument(
        "-o", "--output_dir", required=True,
        help="Path to save per-chapter specific and general/specific keyword files"
    )
    parser.add_argument(
        "-t", "--threshold", type=float, default=0.6,
        help="TF-IDF threshold for specificity (default: 0.6)"
    )
    parser.add_argument(
        "-f", "--min_freq", type=int, default=5,
        help="Minimum frequency of keywords to consider (default: 5)"
    )

    args = parser.parse_args()

    classify_keywords_split_files(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        threshold=args.threshold,
        min_freq=args.min_freq
    )

if __name__ == "__main__":
    main()


