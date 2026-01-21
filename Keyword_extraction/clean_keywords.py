import pandas as pd
from nltk.corpus import wordnet as wn

input_file = "IPCC_AR6_WGIII_Chapter08_keywords.csv"
output_file = "IPCC_AR6_WGIII_Chapter08_keywords_cleaned.csv"

df = pd.read_csv(input_file)

df['keyword_clean'] = (
    df['keyword']
    .astype(str)
    .str.lower()
    .str.strip()
)

def get_synset(word):
    synsets = wn.synsets(word)
    return synsets[0].name() if synsets else word

df['synset'] = df['keyword_clean'].apply(get_synset)

final_df = (
    df.groupby('synset', as_index=False)
      .agg({'keyword': 'first', 'count': 'sum'})
)

final_df[['keyword', 'count']].to_csv(output_file, index=False)

print("DONE")
