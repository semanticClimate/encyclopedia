#!/usr/bin/env python3
"""
Build an encyclopedia from a literature query.

Stages: pygetpapers download, semantic_corpus review table, keyphrase wordlist,
Wikipedia-enriched encyclopedia HTML.

Examples:
  python scripts/query_to_encyclopedia.py --check-query \\
      --query "'amoc' AND 'european climate' AND 'adaptation'"

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
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from encyclopedia.pipeline.query_quotes import (
    check_query_quotes,
    format_query_quote_report,
    query_to_send,
    read_query_text,
)
from encyclopedia.pipeline.query_to_encyclopedia import (
    STOP_AFTER_ENCYCLOPEDIA,
    STOP_AFTER_VALUES,
    build_pygetpapers_command,
    run_query_to_encyclopedia,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download literature with pygetpapers and build an encyclopedia."
    )
    parser.add_argument("--query", default="", help="Europe PMC query string")
    parser.add_argument(
        "--query-file",
        type=Path,
        help="Read the query from a file, so the shell does not eat the quotes. Use - for stdin.",
    )
    parser.add_argument(
        "--check-query",
        action="store_true",
        help="Explain the quotes and brackets, print a suggested query, and exit",
    )
    parser.add_argument(
        "--edit-query",
        action="store_true",
        help="Send the suggested query (double quotes for phrases, capitals for AND/OR/NOT)",
    )
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
    return parser.parse_args(argv)


def _checked_query(args: argparse.Namespace) -> str:
    """Resolve --query/--query-file and stop when the quotes are not usable."""
    try:
        query = read_query_text(args.query, args.query_file)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    except OSError as exc:
        raise SystemExit(f"Could not read the query file: {exc}") from exc
    if not query.strip():
        if args.check_query:
            raise SystemExit("Pass a query with --query or --query-file.")
        return ""

    report = check_query_quotes(query)
    command = ""
    if report.suggested:
        output = args.pygetpapers_dir
        if output is None:
            output = Path(args.work_dir, "pygetpapers") if args.work_dir else Path("OUTPUT")
        command = build_pygetpapers_command(
            report.suggested,
            output,
            args.limit,
            download_pdf=args.pdf,
        )
    if args.check_query:
        print(format_query_quote_report(report, command=command))
        raise SystemExit(0 if report.ok else 1)
    if not report.ok:
        print(format_query_quote_report(report, command=command))
        raise SystemExit(1)
    chosen = query_to_send(report, edit=args.edit_query)
    if chosen != query or any(issue.severity == "edit" for issue in report.issues):
        print(f"Sending:   {chosen}")
        if not args.edit_query and report.edited != chosen:
            print(f"Suggested: {report.edited}")
            print("Add --edit-query to send the suggested query, or --check-query to read it.")
    return chosen


def main() -> None:
    args = parse_args()
    query = _checked_query(args)
    result = run_query_to_encyclopedia(
        query=query,
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
