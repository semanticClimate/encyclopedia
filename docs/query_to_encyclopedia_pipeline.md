# Query to Encyclopedia Pipeline

**Date:** September 30, 2026 (system date of generation)

A literature query becomes an encyclopedia in four stages. Those stages already exist in three sibling repositories. The script and notebook below run them in order.

## How the pipeline works

### 1. Download

`pygetpapers` queries Europe PMC and writes one folder per paper: `PMC123/eupmc_result.json` plus `fulltext.xml` (and `fulltext.pdf` if you ask for it). The Python entry point is:

```python
run_pygetpapers("pygetpapers -q '...' -k 10 -o DIR -x")
```

The string Europe PMC searches is the `-q` argument. A plain-language description of the topic is not sent. For the eastern England floods example the command is:

```bash
pygetpapers -q 'flood* AND "eastern England"' -k 50 -o ~/temp/eeflood/pygetpapers --api europe_pmc -x
```

`flood*` matches flood and floods. `"eastern England"` is one phrase. `-k 50` is the paper limit. `-x` requests full-text XML. The encyclopedia then keeps at most 100 terms. The example is `Examples/eeflood_query_to_encyclopedia.py`. It has not been run.

The AMOC encyclopedia example uses a one-word query, 100 papers, and 100 entries. It is `Examples/amoc_encyclopedia.py`. Output is `~/temp/amoc`, which is separate from the earlier 50-paper corpus at `~/temp/amoc0`. The command is:

```bash
pygetpapers -q AMOC -k 100 -o ~/temp/amoc/pygetpapers --api europe_pmc -x
```

Candidate terms that occur only in an affiliation or a reference are removed before the 100 entries are chosen. Disambiguation then uses the remaining body sentences. The example has not been run.

Every pipeline run writes that `-q` value and the full command into `<work-dir>/pipeline_summary.json` as `query` and `pygetpapers_command`. For this example the file is `~/temp/eeflood/pipeline_summary.json`.

### Checking quotes and brackets

Three different kinds of marks get stacked, and newcomers often mix them up:

- Double quotes keep words in order: `"eastern England"`. A span in single quotes is searched as separate words.
- Parentheses group `AND`, `OR`, and `NOT`: `(flood* OR flooding)`.
- Square brackets mark a range: `FIRST_PDATE:[2020-01-01 TO 2024-12-31]`.
- The shell then wraps the whole `-q` value in one more pair of quotes.

`--check-query` prints the query Europe PMC receives, how each piece is read, and a suggested edit. It does not download anything. Put the query in a file when the shell would otherwise consume the quotes:

```bash
python scripts/query_to_encyclopedia.py --check-query --query-file query.txt
```

```bash
python scripts/query_to_encyclopedia.py --check-query \
    --query "'amoc' AND 'european climate' AND 'adaptation'"
```

That input is rewritten to `"amoc" AND "european climate" AND "adaptation"`. The shell form of the same query is `-q '"amoc" AND "european climate" AND "adaptation"'`. Add `--edit-query` on a real run to send the suggested form. Without that flag the pipeline still straightens curly quotes and removes a pair of quotes that wrapped the whole query, and it stops if a quote or bracket is left open.

A later natural-language parser can turn a plain sentence into a query string and then pass that string through this checker. The checker itself does not read plain English.

### 2. Corpus and review

`semantic_corpus` turns that folder into a BAGIT corpus and a review table. The function for the classic pygetpapers layout is `ingest_and_review_pygetpapers`. Each row starts as `review`. You set `include` or `exclude` by hand.

A separate function, `ingest_query_output_directory`, reads a different layout (`search_results.json` and flat `PMC123.xml` files) produced by `semantic_corpus`'s own Europe PMC search. The ocean-heatwaves demo used that second search, not the pygetpapers command.

### 3. Wordlist

Included full texts are reduced to terms.

- `txt2phrases` does this for plain text and PDFs (`scripts/extract_keyphrases_and_create_encyclopedia.py`).
- IPCC HTML uses `encyclopedia/ipcc/phase1_wordlist.py`.

Neither of those scripts starts from a pygetpapers download.

Spellings that differ only by case are one term. The plain text can be searched again for those terms so each hit keeps its sentence and a link back to the paper. See [Term context search](term_context_search.md).

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
