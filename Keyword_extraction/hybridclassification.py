import os
import pandas as pd
import requests
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm
import time
import pickle

# ---------------- Wikidata Setup ----------------
SPARQL_URL = "https://query.wikidata.org/sparql"
wikidata_cache_file = "wikidata_cache.pkl"

# Load cache if exists
if os.path.exists(wikidata_cache_file):
    with open(wikidata_cache_file, "rb") as f:
        wikidata_cache = pickle.load(f)
else:
    wikidata_cache = {}

def classify_with_wikidata(keyword):
    """
    Query Wikidata SPARQL API to classify a keyword.
    Uses caching to avoid repeated queries.
    """
    if keyword in wikidata_cache:
        return wikidata_cache[keyword]

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
            headers={"User-Agent": "HybridClassifier/1.0 (https://example.org)"}
        )
        data = response.json()
        results = data.get("results", {}).get("bindings", [])
        if results:
            classification = results[0]["classLabel"]["value"]
        else:
            classification = "Unknown"
    except Exception as e:
        classification = f"Error: {e}"

    wikidata_cache[keyword] = classification
    # Save cache after each keyword to be resumable
    with open(wikidata_cache_file, "wb") as f:
        pickle.dump(wikidata_cache, f)

    return classification

# ---------------- ML Model Setup ----------------
MODEL_NAME = "climatebert/distilroberta-base-climate-detector"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.eval()  # Set to evaluation mode

def classify_with_ml(keywords, batch_size=32):
    """
    Batch-classify a list of keywords using ClimateBERT.
    Returns a list of "climate-related" / "not climate-related".
    """
    results = []
    for i in range(0, len(keywords), batch_size):
        batch = keywords[i:i+batch_size]
        inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            logits = model(**inputs).logits
        preds = torch.argmax(logits, dim=1).tolist()
        results.extend(["climate-related" if p == 1 else "not climate-related" for p in preds])
    return results

# ---------------- Hybrid Classifier ----------------
def hybrid_classify(keywords, sleep_time=0.2):
    """
    Hybrid classification: Wikidata first, ML as fallback.
    Returns list of classifications aligned with keywords.
    """
    classifications = []
    ml_batch = []
    ml_indices = []

    for idx, kw in enumerate(tqdm(keywords, desc="Classifying keywords")):
        wikidata_result = classify_with_wikidata(kw)
        if wikidata_result in ["Unknown"] or wikidata_result.startswith("Error"):
            ml_batch.append(kw)
            ml_indices.append(idx)
            classifications.append(None)  # placeholder
        else:
            classifications.append(wikidata_result)
        time.sleep(sleep_time)  # avoid Wikidata rate limits

    if ml_batch:
        ml_results = classify_with_ml(ml_batch)
        for idx, res in zip(ml_indices, ml_results):
            classifications[idx] = res

    return classifications

# ---------------- Main Pipeline (Updated) ----------------
def classify_keywords(input_file, output_dir, sleep_time=0.2):
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(input_file)
    if "keyword" not in df.columns:
        raise ValueError("CSV must contain a 'keyword' column")

    keywords = df["keyword"].astype(str).tolist()
    classifications = hybrid_classify(keywords, sleep_time=sleep_time)

    # Only keep keyword and classification in output
    output_df = pd.DataFrame({
        "keyword": keywords,
        "classification": classifications
    })

    output_path = os.path.join(output_dir, "hybrid_classified.csv")
    output_df.to_csv(output_path, index=False)
    print(f"\n✅ Hybrid classification complete. Saved to {output_path}")

# ---------------- CLI ----------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hybrid Wikidata + ClimateBERT keyword classification")
    parser.add_argument("-i", "--input_file", required=True, help="CSV with 'keyword' column")
    parser.add_argument("-o", "--output_dir", required=True, help="Folder to save output")
    parser.add_argument("--sleep", type=float, default=0.2, help="Sleep time between Wikidata requests (sec)")
    args = parser.parse_args()

    classify_keywords(args.input_file, args.output_dir, sleep_time=args.sleep)


