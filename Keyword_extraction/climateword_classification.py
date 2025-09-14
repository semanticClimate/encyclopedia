import os
import time
import json
import requests
import pandas as pd
from tqdm import tqdm  # progress bar

# SPARQL endpoint for Wikidata
SPARQL_URL = "https://query.wikidata.org/sparql"
CACHE_FILE = "wikidata_cache.json"


# ------------------- Caching -------------------
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


# ------------------- Wikidata Query -------------------
def classify_with_wikidata(keyword, cache):
    """
    Query Wikidata SPARQL API to classify a keyword.
    Returns the 'instance of' (P31) label if available.
    Uses cache to avoid duplicate queries.
    """
    if keyword in cache:
        return cache[keyword]

    query = f"""
    SELECT ?item ?itemLabel ?class ?classLabel WHERE {{
      ?item rdfs:label "{keyword}"@en.
      ?item wdt:P31 ?class.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }} LIMIT 1
    """

    try:
        response = requests.get(
            SPARQL_URL,
            params={"query": query, "format": "json"},
            headers={"User-Agent": "KeywordClassifier/1.0 (https://example.org)"}
        )
        data = response.json()
        results = data.get("results", {}).get("bindings", [])
        if results:
            classification = results[0]["classLabel"]["value"]  # e.g., "country"
        else:
            classification = "Unknown"
    except Exception as e:
        classification = f"Error: {e}"

    # Save to cache
    cache[keyword] = classification
    return classification


# ------------------- Main Classification -------------------
def classify_keywords(input_file, output_dir, sleep_time=0.3):
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(input_file)
    if "keyword" not in df.columns:
        raise ValueError("CSV must contain a 'keyword' column")

    keywords = df["keyword"].astype(str).tolist()

    # Load cache
    cache = load_cache()

    results = []
    for kw in tqdm(keywords, desc="Classifying keywords"):
        classification = classify_with_wikidata(kw, cache)
        results.append([kw, classification])
        time.sleep(sleep_time)  # prevent API overload

    # Save cache after run
    save_cache(cache)

    # Save results
    output_df = pd.DataFrame(results, columns=["keyword", "wikidata_class"])
    output_df.to_csv(os.path.join(output_dir, "wikidata_classified.csv"), index=False)
    print(f"\n✅ Classification complete. Results saved in {output_dir}")


# ------------------- CLI -------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Classify keywords using Wikidata SPARQL API with caching & batching")
    parser.add_argument("-i", "--input_file", required=True, help="CSV with keywords (must have 'keyword' column)")
    parser.add_argument("-o", "--output_dir", required=True, help="Output folder")
    parser.add_argument("-s", "--sleep", type=float, default=0.3, help="Sleep time between requests (default=0.3s)")
    args = parser.parse_args()

    classify_keywords(args.input_file, args.output_dir, args.sleep)
