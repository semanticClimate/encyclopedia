import pandas as pd
import re
import requests
import os
import pycountry
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Load the public ClimateBERT detector model
model_name = "climatebert/distilroberta-base-climate-detector"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

def is_climate_related(keyword):
    # Encode the keyword
    inputs = tokenizer(keyword, return_tensors="pt", truncation=True)
    with torch.no_grad():
        logits = model(**inputs).logits
    predicted_class = torch.argmax(logits, dim=1).item()
    # In this model, class 1 = climate-related, class 0 = not climate-related
    return predicted_class == 1

def get_country_list():
    # Use pycountry to get all country names
    countries = {country.name for country in pycountry.countries}
    return countries

def is_acronym(word):
    return bool(re.fullmatch(r"[A-Z0-9]{2,5}", word))

def classify_keywords(input_file, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(input_file)
    keywords = df["keyword"].astype(str).tolist()

    countries = get_country_list()
    climate_words = []
    country_words = []
    acronyms = []
    others = []

    for kw in keywords:
        kw_clean = kw.strip()
        if kw_clean in countries:
            country_words.append(kw_clean)
        elif is_acronym(kw_clean):
            acronyms.append(kw_clean)
        elif is_climate_related(kw_clean):
            climate_words.append(kw_clean)
        else:
            others.append(kw_clean)

    # Save to CSVs
    pd.DataFrame(climate_words, columns=["keyword"]).to_csv(os.path.join(output_dir, "climate_words.csv"), index=False)
    pd.DataFrame(country_words, columns=["keyword"]).to_csv(os.path.join(output_dir, "country_words.csv"), index=False)
    pd.DataFrame(acronyms, columns=["keyword"]).to_csv(os.path.join(output_dir, "acronyms.csv"), index=False)
    pd.DataFrame(others, columns=["keyword"]).to_csv(os.path.join(output_dir, "others.csv"), index=False)

    print(f"Classification complete. Files saved in {output_dir}")

# ----------------- Command-line interface -----------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Classify keywords into climate, countries, acronyms, and others using public ClimateBERT")
    parser.add_argument("-i", "--input_file", required=True, help="Path to CSV file with keywords")
    parser.add_argument("-o", "--output_dir", required=True, help="Folder to save output CSV files")
    args = parser.parse_args()

    classify_keywords(args.input_file, args.output_dir)

