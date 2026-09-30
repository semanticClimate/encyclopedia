#!/usr/bin/env python3
"""
Build an encyclopedia from a literature query.

Stages: pygetpapers download, semantic_corpus review table, keyphrase wordlist,
Wikipedia-enriched encyclopedia HTML.

Examples:
  python scripts/query_to_encyclopedia.py \\
      --query '"marine heatwave" AND "ocean current"' \\
      --limit 10 \\
      --stop-after wordlist

  python scripts/query_to_encyclopedia.py \\
      --pygetpapers-dir temp/queries/ocean_heatwaves/pygetpapers \\
      --review-table corpora/ocean/analysis/review/review_table.json \\
      --output encyclopedia.html
"""

from __future__ import annotations

import argparse
from pathlib import Path

from encyclopedia.pipeline.query_to_encyclopedia import (
    STOP_AFTER_ENCYCLOPEDIA,
    STOP_AFTER_VALUES,
    run_query_to_encyclopedia,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download literature with pygetpapers and build an encyclopedia."
    )
    parser.add_argument("--query", default="", help="Europe PMC query string")
    parser.add_argument(
        "--pygetpapers-dir",
        type=Path,
        help="Existing pygetpapers output directory (skips the live query)",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        help="Directory for texts, keywords, wordlist, and summary JSON",
    )
    parser.add_argument("--corpus-dir", type=Path, help="BAGIT corpus directory")
    parser.add_argument("--limit", type=int, default=10, help="Maximum papers to download")
    parser.add_argument("--pdf", action="store_true", help="Also download PDFs")
    parser.add_argument(
        "--review-table",
        type=Path,
        help="Review table JSON; only rows marked include are used for the wordlist",
    )
    parser.add_argument(
        "--use-all-papers",
        action="store_true",
        help="Ignore review status and extract terms from every downloaded paper",
    )
    parser.add_argument("--top-n", type=int, default=50, help="Keyphrases kept per paper")
    parser.add_argument("--max-terms", type=int, default=30, help="Terms sent to the encyclopedia")
    parser.add_argument("--min-count", type=int, default=2, help="Minimum aggregated term count")
    parser.add_argument("--title", default="", help="Encyclopedia title")
    parser.add_argument("--output", type=Path, help="Encyclopedia HTML path")
    parser.add_argument(
        "--no-wikipedia",
        action="store_true",
        help="Skip Wikipedia lookups when building the encyclopedia",
    )
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Do not rebuild the corpus; requires --review-table",
    )
    parser.add_argument(
        "--stop-after",
        choices=STOP_AFTER_VALUES,
        default=STOP_AFTER_ENCYCLOPEDIA,
        help="Last stage to run (default: encyclopedia)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_query_to_encyclopedia(
        query=args.query,
        pygetpapers_dir=args.pygetpapers_dir,
        work_dir=args.work_dir,
        corpus_dir=args.corpus_dir,
        limit=args.limit,
        download_pdf=args.pdf,
        review_table=args.review_table,
        use_all_papers=args.use_all_papers,
        top_n=args.top_n,
        max_terms=args.max_terms,
        min_count=args.min_count,
        title=args.title,
        encyclopedia_html=args.output,
        add_wikipedia=not args.no_wikipedia,
        stop_after=args.stop_after,
        skip_ingest=args.skip_ingest,
    )
    print(f"Stopped after: {result.stop_after}")
    print(f"Papers: {result.paper_count}")
    print(f"pygetpapers: {result.pygetpapers_dir}")
    if result.review_json:
        print(f"Review table: {result.review_json}")
    if result.wordlist_csv:
        print(f"Wordlist ({result.term_count} terms): {result.wordlist_csv}")
    if result.encyclopedia_html:
        print(f"Encyclopedia: {result.encyclopedia_html}")


if __name__ == "__main__":
    main()
