#!/usr/bin/env python3
"""
Build a complete encyclopedia from an Europe PMC query about AMOC.

This example is not executed when the file is imported. Run it from the
project root when you want the live download and Wikipedia lookups:

    python Examples/amoc_query_to_encyclopedia.py --max-terms 100

If ~/temp/amoc0/wordlist.csv already exists, extraction is skipped and the
encyclopedia uses the highest-count terms in that file. The directory was
renamed from ~/temp/amoc.

Date: October 1, 2026 (system date)
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from encyclopedia.ipcc.phase1_wordlist import collect_keyword_csvs
from encyclopedia.pipeline.wikipedia_disambiguation import load_context_sentences
from encyclopedia.pipeline.query_to_encyclopedia import (
    STOP_AFTER_ENCYCLOPEDIA,
    build_encyclopedia_from_terms,
    discover_paper_folders,
    run_query_to_encyclopedia,
    write_filtered_wordlist,
)


QUERY = "'amoc' AND 'european climate' AND 'adaptation'"
PAPER_LIMIT = 50
MAX_TERMS = 100
TITLE = "AMOC, European climate, and adaptation"

AMOC_ROOT = Path(Path.home(), "temp", "amoc0")
PYGETPAPERS_DIR = Path(AMOC_ROOT, "pygetpapers")
CORPUS_DIR = Path(AMOC_ROOT, "corpus")
ENCYCLOPEDIA_DIR = Path(AMOC_ROOT, "encyclopedia")
ENCYCLOPEDIA_HTML = Path(ENCYCLOPEDIA_DIR, "amoc_encyclopedia.html")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an AMOC encyclopedia from the highest-relevance terms."
    )
    parser.add_argument(
        "--max-terms",
        type=int,
        default=MAX_TERMS,
        help="How many terms to include, highest count first (default: 100)",
    )
    return parser.parse_args()


def build_amoc_encyclopedia(max_terms: int = MAX_TERMS):
    """Download up to 50 papers and write the corpus and encyclopedia.

    Reuses ~/temp/amoc0/pygetpapers when that directory already contains papers.
    Reuses ~/temp/amoc0/wordlist.csv when it exists. Each kept term becomes one
    encyclopedia entry after a single Wikipedia download (article link, Wikidata
    link, description, and image).
    """
    wordlist_csv = Path(AMOC_ROOT, "wordlist.csv")
    keyword_csvs = collect_keyword_csvs(Path(AMOC_ROOT, "keywords"))
    if keyword_csvs:
        terms = write_filtered_wordlist(
            keyword_csvs,
            wordlist_csv,
            min_count=2,
            min_term_words=1,
            max_term_words=6,
            max_terms=max_terms,
            text_dir=Path(AMOC_ROOT, "texts"),
        )
        print(f"Wordlist: {wordlist_csv} ({len(terms)} terms)")
        contexts = load_context_sentences(Path(AMOC_ROOT, "wordlist_contexts.jsonl"))
        build_encyclopedia_from_terms(
            terms,
            TITLE,
            ENCYCLOPEDIA_HTML,
            add_wikipedia=True,
            contexts_by_term=contexts,
        )
        print(f"Wordlist: {wordlist_csv}")
        print(f"Encyclopedia: {ENCYCLOPEDIA_HTML}")
        print(f"Terms: {len(terms)}")
        return None

    existing_download = PYGETPAPERS_DIR if discover_paper_folders(PYGETPAPERS_DIR) else None
    return run_query_to_encyclopedia(
        query=QUERY,
        pygetpapers_dir=existing_download,
        work_dir=AMOC_ROOT,
        corpus_dir=CORPUS_DIR,
        limit=PAPER_LIMIT,
        use_all_papers=True,
        max_terms=max_terms,
        title=TITLE,
        encyclopedia_html=ENCYCLOPEDIA_HTML,
        add_wikipedia=True,
        stop_after=STOP_AFTER_ENCYCLOPEDIA,
    )


def main() -> None:
    args = parse_args()
    result = build_amoc_encyclopedia(max_terms=args.max_terms)
    if result is None:
        return
    print(f"Corpus: {result.corpus_dir}")
    print(f"Encyclopedia: {result.encyclopedia_html}")
    print(f"Papers: {result.paper_count}")
    print(f"Terms: {result.term_count}")


if __name__ == "__main__":
    main()
