# Query to Encyclopedia Pipeline

**Date:** September 30, 2026 (system date of generation)

A literature query becomes an encyclopedia in four stages. Those stages already exist in three sibling repositories. The script and notebook below run them in order.

## How the pipeline works

### 1. Download

`pygetpapers` queries Europe PMC and writes one folder per paper: `PMC123/eupmc_result.json` plus `fulltext.xml` (and `fulltext.pdf` if you ask for it). The Python entry point is:

```python
run_pygetpapers("pygetpapers -q '...' -k 10 -o DIR -x")
```

### 2. Corpus and review

`semantic_corpus` turns that folder into a BAGIT corpus and a review table. The function for the classic pygetpapers layout is `ingest_and_review_pygetpapers`. Each row starts as `review`. You set `include` or `exclude` by hand.

A separate function, `ingest_query_output_directory`, reads a different layout (`search_results.json` and flat `PMC123.xml` files) produced by `semantic_corpus`'s own Europe PMC search. The ocean-heatwaves demo used that second search, not the pygetpapers command.

### 3. Wordlist

Included full texts are reduced to terms.

- `txt2phrases` does this for plain text and PDFs (`scripts/extract_keyphrases_and_create_encyclopedia.py`).
- IPCC HTML uses `encyclopedia/ipcc/phase1_wordlist.py`.

Neither of those scripts starts from a pygetpapers download.

### 4. Encyclopedia

`Examples/create_encyclopedia_from_wordlist.py` builds an `amilib` dictionary, adds Wikipedia text, then normalizes and merges entries by Wikidata id in `encyclopedia/utils/encyclopedia_builder.py`. The HTML encyclopedia is the output.

Chatbot export (`export_reviewed_corpus_for_chatbot`) sits beside stage 4. It uses the same `include` rows, but it does not build the encyclopedia.

## Glue script and notebook

`scripts/query_to_encyclopedia.py` runs the four stages. `notebooks/query_to_encyclopedia.ipynb` is the same flow for Colab or a local Jupyter session.

First pass, all downloaded papers, stop at the wordlist so you can curate before any Wikipedia calls:

```bash
python scripts/query_to_encyclopedia.py \
    --query '("marine heatwave") AND (current OR circulation)' \
    --limit 10 \
    --use-all-papers \
    --stop-after wordlist
```

After you mark `include` in the review JSON, build the encyclopedia without downloading or ingesting again:

```bash
python scripts/query_to_encyclopedia.py \
    --pygetpapers-dir temp/query_to_encyclopedia/<slug>/pygetpapers \
    --review-table temp/query_to_encyclopedia/<slug>/corpus/analysis/review/review_table.json \
    --skip-ingest \
    --output encyclopedia.html
```

`--stop-after` accepts `download`, `review`, `wordlist`, or `encyclopedia`.

`amilib` and `txt2phrases` import in the encyclopedia environment. `pygetpapers` and `semantic_corpus` still need `pip install -e` from their sibling checkouts before a live query.

The tests in `test/encyclopedia/test_query_to_encyclopedia.py` cover command building, include-filtering, XML text extraction, and wordlist limits. They do not call Europe PMC or Wikipedia.
