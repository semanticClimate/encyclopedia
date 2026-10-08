#!/usr/bin/env python3
"""
Build an encyclopedia of the term AMOC from 100 Europe PMC papers.

This is separate from Examples/amoc_query_to_encyclopedia.py, which searched
for AMOC together with European climate and adaptation and kept the 50-paper
corpus at ~/temp/amoc0. This script writes a new corpus at ~/temp/amoc.

The query Europe PMC receives is AMOC. The command is:

    pygetpapers -q AMOC -k 100 -o ~/temp/amoc/pygetpapers --api europe_pmc -x

Up to 300 candidate terms are collected. A term is dropped when every saved
hit is an affiliation or a reference. The 100 most relevant remaining terms
become encyclopedia entries. Wikipedia disambiguation pages are resolved from
the body sentences of those terms.

The script does not run on import:

    python Examples/amoc_encyclopedia.py

Date: October 8, 2026 (system date)
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from encyclopedia.ipcc.phase1_wordlist import collect_keyword_csvs
from encyclopedia.pipeline.query_to_encyclopedia import (
    STOP_AFTER_WORDLIST,
    apply_false_positive_filter,
    build_encyclopedia_from_terms,
    build_pygetpapers_command,
    discover_paper_folders,
    run_query_to_encyclopedia,
    write_filtered_wordlist,
)


QUERY = "AMOC"
PAPER_LIMIT = 100
MAX_ENTRIES = 100
CANDIDATE_TERMS = 300
TITLE = "AMOC"

AMOC_ROOT = Path(Path.home(), "temp", "amoc")
PYGETPAPERS_DIR = Path(AMOC_ROOT, "pygetpapers")
CORPUS_DIR = Path(AMOC_ROOT, "corpus")
ENCYCLOPEDIA_HTML = Path(AMOC_ROOT, "encyclopedia", "amoc_encyclopedia.html")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a 100-entry AMOC encyclopedia from 100 papers."
    )
    parser.add_argument(
        "--max-terms",
        type=int,
        default=MAX_ENTRIES,
        help="Encyclopedia entries after false positives are removed (default: 100)",
    )
    return parser.parse_args()


def _write_candidate_wordlist(max_candidates: int):
    """Download when needed, then write a candidate wordlist larger than the encyclopedia."""
    wordlist_csv = Path(AMOC_ROOT, "wordlist.csv")
    keyword_csvs = collect_keyword_csvs(Path(AMOC_ROOT, "keywords"))
    if keyword_csvs:
        terms = write_filtered_wordlist(
            keyword_csvs,
            wordlist_csv,
            min_count=2,
            min_term_words=1,
            max_term_words=6,
            max_terms=max_candidates,
            text_dir=Path(AMOC_ROOT, "texts"),
        )
        print(f"Candidate wordlist: {wordlist_csv} ({len(terms)} terms)")
        return wordlist_csv

    existing_download = PYGETPAPERS_DIR if discover_paper_folders(PYGETPAPERS_DIR) else None
    run_query_to_encyclopedia(
        query=QUERY,
        pygetpapers_dir=existing_download,
        work_dir=AMOC_ROOT,
        corpus_dir=CORPUS_DIR,
        limit=PAPER_LIMIT,
        use_all_papers=True,
        max_terms=max_candidates,
        title=TITLE,
        stop_after=STOP_AFTER_WORDLIST,
    )
    return wordlist_csv


def build_amoc_encyclopedia(max_terms: int = MAX_ENTRIES):
    """Download up to 100 papers and write a 100-entry encyclopedia.

    Reuses ~/temp/amoc/pygetpapers and ~/temp/amoc/keywords when they already exist.
    Does not read ~/temp/amoc0.
    """
    command = build_pygetpapers_command(QUERY, PYGETPAPERS_DIR, PAPER_LIMIT)
    print(f"Query: {QUERY}")
    print(f"Command: {command}")
    wordlist_csv = _write_candidate_wordlist(max(max_terms, CANDIDATE_TERMS))
    filtered = apply_false_positive_filter(wordlist_csv, max_terms)
    print(f"False positives removed: {len(filtered.rejected)}")
    print(f"Wordlist: {wordlist_csv} ({len(filtered.terms)} terms)")
    build_encyclopedia_from_terms(
        filtered.terms,
        TITLE,
        ENCYCLOPEDIA_HTML,
        add_wikipedia=True,
        contexts_by_term=filtered.contexts_by_term,
    )
    print(f"Encyclopedia: {ENCYCLOPEDIA_HTML}")
    print(f"Entries: {len(filtered.terms)}")
    return filtered


def main() -> None:
    args = parse_args()
    build_amoc_encyclopedia(max_terms=args.max_terms)


if __name__ == "__main__":
    main()
