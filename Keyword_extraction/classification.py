import os
import pandas as pd
from collections import defaultdict
from argparse import ArgumentParser
from sklearn.feature_extraction.text import TfidfTransformer

def classify_keywords(input_dir, output_dir, threshold=0.6):
    """
    Classify keywords into 'General' or 'Specific' using TF-IDF.
    Output CSV will contain: keyword, chapter, category
    """

    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Load all CSV files
    chapter_files = [f for f in os.listdir(input_dir) if f.endswith(".csv")]
    keyword_chapter_freq = defaultdict(dict)

    for file in chapter_files:
        chapter = os.path.splitext(file)[0]  # chapter name = filename without extension
        df = pd.read_csv(os.path.join(input_dir, file))

        # Expecting columns: keyword, frequency
        for _, row in df.iterrows():
            keyword = row["keyword"]
            freq = row["count"]
            keyword_chapter_freq[keyword][chapter] = freq

    # Step 2: Build keyword-chapter frequency matrix
    chapters = sorted(chapter_files)
    keywords = list(keyword_chapter_freq.keys())

    data = []
    for keyword in keywords:
        row = []
        for file in chapters:
            chapter = os.path.splitext(file)[0]
            row.append(keyword_chapter_freq[keyword].get(chapter, 0))
        data.append(row)

    df_matrix = pd.DataFrame(data, index=keywords, columns=[os.path.splitext(f)[0] for f in chapters])

    # Step 3: Compute TF-IDF
    transformer = TfidfTransformer()
    tfidf_matrix = transformer.fit_transform(df_matrix)

    # Step 4: Assign categories
    results = []
    for i, keyword in enumerate(df_matrix.index):
        for j, chapter in enumerate(df_matrix.columns):
            score = tfidf_matrix[i, j]
            category = "Specific" if score >= threshold else "General"
            results.append([keyword, chapter, category])

    # Step 5: Save final CSV
    output_df = pd.DataFrame(results, columns=["keyword", "chapter", "category"])
    output_file = os.path.join(output_dir, "classified_keywords.csv")
    output_df.to_csv(output_file, index=False)

    print(f"Classification saved to {output_file}")


if __name__ == "__main__":
    parser = ArgumentParser(description="Classify extracted keywords into general/specific using TF-IDF")
    parser.add_argument("-i", "--input_dir", required=True, help="Path to folder with *_keywords.csv files")
    parser.add_argument("-o", "--output_dir", required=True, help="Path to save classified files")
    parser.add_argument("-t", "--threshold", type=float, default=0.6, help="TF-IDF threshold for specific classification")
    args = parser.parse_args()

    classify_keywords(args.input_dir, args.output_dir, args.threshold)







