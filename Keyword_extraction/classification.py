import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from argparse import ArgumentParser


def classify_keywords_tfidf(input_dir, output_dir, threshold=0.6):
    """
    Classify keywords into general or specific using TF-IDF.
    - general_keywords.csv : words distributed across multiple chapters
    - chapterX_specific_keywords.csv : words strongly specific to one chapter
    - merged_keywords.csv : all words with chapter + category
    """

    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Load all chapter keyword files
    chapter_docs = {}
    for file in os.listdir(input_dir):
        if file.endswith("_keywords.csv"):
            chapter_name = file.replace("_keywords.csv", "")
            df = pd.read_csv(os.path.join(input_dir, file))
            keywords = df["keyword"].dropna().tolist()
            chapter_docs[chapter_name] = " ".join(keywords)

    chapters = list(chapter_docs.keys())
    documents = list(chapter_docs.values())

    # Step 2: TF-IDF vectorization
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)
    terms = vectorizer.get_feature_names_out()

    tfidf_df = pd.DataFrame(tfidf_matrix.toarray(), index=chapters, columns=terms)

    # Step 3: Classify keywords
    merged_records = []
    general_records = []

    for term in terms:
        scores = tfidf_df[term]
        top_chapter = scores.idxmax()
        top_score = scores.max()

        if top_score >= threshold:
            category = "specific"
            merged_records.append({"chapter": top_chapter, "keyword": term, "category": category})
        else:
            category = "general"
            general_records.append({"keyword": term, "chapters": ", ".join(scores[scores > 0].index)})
            for chapter, score in scores.items():
                if score > 0:
                    merged_records.append({"chapter": chapter, "keyword": term, "category": category})

    # Step 4: Save outputs
    # General
    general_df = pd.DataFrame(general_records).drop_duplicates()
    general_out = os.path.join(output_dir, "general_keywords.csv")
    general_df.to_csv(general_out, index=False)
    print(f"🌍 General keywords saved: {general_out}")

    # Specific (per chapter)
    merged_df = pd.DataFrame(merged_records)
    for chapter in chapters:
        chapter_specific = merged_df[(merged_df["chapter"] == chapter) & (merged_df["category"] == "specific")]
        if not chapter_specific.empty:
            specific_out = os.path.join(output_dir, f"{chapter}_specific_keywords.csv")
            chapter_specific.to_csv(specific_out, index=False)
            print(f"🔎 Specific keywords saved for {chapter}: {specific_out}")

    # Merged
    merged_out = os.path.join(output_dir, "merged_keywords.csv")
    merged_df.to_csv(merged_out, index=False)
    print(f"📑 Merged keywords saved: {merged_out}")


# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    parser = ArgumentParser(description="Classify extracted keywords into general/specific using TF-IDF")
    parser.add_argument("-i", "--input_dir", required=True, help="Path to folder with *_keywords.csv files")
    parser.add_argument("-o", "--output_dir", required=True, help="Path to save classified files")
    parser.add_argument("-t", "--threshold", type=float, default=0.6, help="TF-IDF threshold for specific classification")
    args = parser.parse_args()

    classify_keywords_tfidf(args.input_dir, args.output_dir, args.threshold)





