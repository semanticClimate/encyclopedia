#!/usr/bin/env python3
"""
Print the first contexts for a few terms in the paper text.

This is a debugging view. It re-searches the plain text, ignores case, and
shows only the earliest contexts_to_show hits in each paper. The match count
is the total in that paper, so an unexpected early hit can be seen without
listing every occurrence.

    python Examples/search_term_contexts.py
    python Examples/search_term_contexts.py --contexts-to-show 1 --terms AMOC "climate change"

Date: October 4, 2026 (system date)
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from encyclopedia.pipeline.query_to_encyclopedia import search_term_in_text


DEFAULT_TERMS = ("AMOC", "climate change", "tipping")
DEFAULT_TEXT_DIR = Path(Path.home(), "temp", "amoc0", "texts")
DEFAULT_CONTEXTS_TO_SHOW = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show the first full-text contexts for a few terms."
    )
    parser.add_argument(
        "--terms",
        nargs="+",
        default=list(DEFAULT_TERMS),
        help="Terms to search. Case is ignored.",
    )
    parser.add_argument(
        "--text-dir",
        type=Path,
        default=DEFAULT_TEXT_DIR,
        help="Directory of plain-text papers.",
    )
    parser.add_argument(
        "--contexts-to-show",
        type=int,
        default=DEFAULT_CONTEXTS_TO_SHOW,
        help="How many of the earliest hits to print for each paper.",
    )
    parser.add_argument(
        "--max-papers",
        type=int,
        default=0,
        help="Stop after this many papers. 0 reads every text file.",
    )
    return parser.parse_args()


def highlight_match(record: dict) -> str:
    """Mark the matched term inside its sentence."""
    sentence = record["sentence"]
    start = record["start"]
    end = record["end"]
    if 0 <= start < end <= len(sentence):
        return f"{sentence[:start]}[{sentence[start:end]}]{sentence[end:]}"
    return sentence


def show_term_contexts(
    text_files: list,
    terms: list,
    contexts_to_show: int,
) -> None:
    """Print the earliest contexts for each term in each paper."""
    for term in terms:
        print(f"\n{term}")
        any_hit = False
        for text_path in text_files:
            text = Path(text_path).read_text(encoding="utf-8")
            records = search_term_in_text(
                text,
                term,
                Path(text_path).name,
                per_document=contexts_to_show,
                in_document_order=True,
            )
            if not records:
                continue
            any_hit = True
            total = records[0]["match_count"]
            shown = len(records)
            print(f"  {Path(text_path).name}  {total} hits, showing {shown}")
            for index, record in enumerate(records, start=1):
                print(
                    f"    {index}. {record['matched']!r} "
                    f"at {record['source_start']}-{record['source_end']}"
                )
                print(f"       {highlight_match(record)}")
        if not any_hit:
            print("  no hits")


def main() -> None:
    args = parse_args()
    text_dir = Path(args.text_dir)
    text_files = sorted(text_dir.glob("*.txt"))
    if args.max_papers > 0:
        text_files = text_files[: args.max_papers]
    if not text_files:
        raise FileNotFoundError(f"No text files in {text_dir}")
    show_term_contexts(text_files, args.terms, args.contexts_to_show)


if __name__ == "__main__":
    main()
