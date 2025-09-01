# classification.py
import os
import pandas as pd
from collections import defaultdict
from argparse import ArgumentParser


def classify_keywords(input_dir, output_dir):
    """
    Classify keywords into general or specific and generate:
    - general_keywords.csv : global general words with all chapters
    - chapterX_specific_keywords.csv : specific words for each chapter
    - merged_keywords.csv : all words with chapter + category
    """

    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Build dictionary mapping keyword → chapters
    keyword_to_chapters = defaultdict(set)

    for file in os.listdir(input_dir):
        if file.endswith("_keywords.csv"):
            chapter_name = file.replace("_keywords.csv", "")
            df = pd.read_csv(os.path.join(input_dir, file))

            for kw in df['keyword'].dropna().unique():
                keyword_to_chapters[kw].add(chapter_name)

    # Step 2: Classify and collect records
    merged_records = []

    for file in os.listdir(input_dir):
        if file.endswith("_keywords.csv"):
            chapter_name = file.replace("_keywords.csv", "")
            df = pd.read_csv(os.path.join(input_dir, file))

            chapter_specific_records = []  # collect specific words for this chapter

            for kw in df['keyword'].dropna().unique():
                if len(keyword_to_chapters[kw]) > 1:
                    category = "general"
                else:
                    category = "specific"

                # Add to merged file
                merged_records.append({
                    "chapter": chapter_name,
                    "keyword": kw,
                    "category": category
                })

                # Add to chapter-specific file if specific
                if category == "specific":
                    chapter_specific_records.append({
                        "chapter": chapter_name,
                        "keyword": kw
                    })

            # Save specific file for this chapter only
            if chapter_specific_records:
                specific_df = pd.DataFrame(chapter_specific_records).drop_duplicates()
                specific_out = os.path.join(output_dir, f"{chapter_name}_specific_keywords.csv")
                specific_df.to_csv(specific_out, index=False)
                print(f"🔎 Specific keywords saved for {chapter_name}: {specific_out}")

    # Step 3: Save general keywords file (unique across all)
    general_keywords = {
        kw: sorted(list(chapters))
        for kw, chapters in keyword_to_chapters.items()
        if len(chapters) > 1
    }

    general_df = pd.DataFrame([
        {"keyword": kw, "chapters": ", ".join(chapters)}
        for kw, chapters in general_keywords.items()
    ])

    general_out = os.path.join(output_dir, "general_keywords.csv")
    general_df.to_csv(general_out, index=False)
    print(f"🌍 General keywords saved: {general_out}")

    # Step 4: Save merged file (all words with chapter + category)
    merged_df = pd.DataFrame(merged_records)
    merged_out = os.path.join(output_dir, "merged_keywords.csv")
    merged_df.to_csv(merged_out, index=False)
    print(f"📑 Merged keywords saved: {merged_out}")


# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    parser = ArgumentParser(description="Classify extracted keywords into general/specific")
    parser.add_argument("-i", "--input_dir", required=True, help="Path to folder with *_keywords.csv files")
    parser.add_argument("-o", "--output_dir", required=True, help="Path to save classified files")
    args = parser.parse_args()

    classify_keywords(args.input_dir, args.output_dir)




