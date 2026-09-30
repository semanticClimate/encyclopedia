#!/usr/bin/env python3
"""
Phase 1 runner: extract raw wordlist for a small IPCC subset.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List
import time
import re

from encyclopedia.ipcc.phase1_wordlist import (
    build_phase1_outputs,
    collect_keyword_csvs,
)


def _extract_keywords_with_txt2phrases(
    input_files: List[Path],
    keyword_output_dir: Path,
    top_n: int,
) -> None:
    """
    Run txt2phrases on each input file and write CSV outputs.
    """
    try:
        from txt2phrases import KeywordExtraction  # type: ignore
    except ImportError:
        try:
            from txt2phrases.keyword import KeywordExtraction  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "txt2phrases is required for phase 1 extraction. "
                "Install with: pip install txt2phrases"
            ) from exc
    except Exception as exc:
        raise ImportError(
            "txt2phrases is required for phase 1 extraction. "
            "Install with: pip install txt2phrases"
        ) from exc

    keyword_output_dir.mkdir(parents=True, exist_ok=True)
    for input_file in input_files:
        extractor = KeywordExtraction(
            input_path=str(input_file),
            output_folder=str(keyword_output_dir),
            top_n=top_n,
        )
        extractor.extract()


def _html_to_text(html_content: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", html_content)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _prepare_text_inputs(
    input_files: List[Path],
    prepared_text_dir: Path,
) -> List[Path]:
    prepared_text_dir.mkdir(parents=True, exist_ok=True)
    prepared_files: List[Path] = []
    for input_file in input_files:
        suffix = input_file.suffix.lower()
        if suffix == ".txt":
            prepared_files.append(input_file)
            continue
        if suffix not in {".html", ".htm"}:
            raise ValueError(f"Unsupported input type for phase 1: {input_file}")
        html_content = input_file.read_text(encoding="utf-8", errors="ignore")
        text_content = _html_to_text(html_content)
        out_path = Path(prepared_text_dir, f"{input_file.stem}.txt")
        out_path.write_text(text_content, encoding="utf-8")
        prepared_files.append(out_path)
    return prepared_files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 1: create raw wordlist from selected IPCC files"
    )
    parser.add_argument(
        "--input-files",
        nargs="+",
        required=True,
        help="One or more text files (e.g., SYR introduction + chapter file)",
    )
    parser.add_argument(
        "--main-subject",
        default="ipcc",
        help="Main subject namespace for temp output path (default: ipcc)",
    )
    parser.add_argument(
        "--output-subdir",
        default="phase1_wordlist",
        help="Subdirectory inside temp/<main_subject>/",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=500,
        help="Top keyphrases per file for txt2phrases",
    )
    parser.add_argument(
        "--min-term-words",
        type=int,
        default=1,
        help="Minimum words in output term",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=2,
        help="Minimum count threshold for final raw_wordlist.csv",
    )
    parser.add_argument(
        "--max-term-words",
        type=int,
        default=8,
        help="Maximum words in output term",
    )
    args = parser.parse_args()

    input_files = [Path(path).resolve() for path in args.input_files]
    missing = [str(path) for path in input_files if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Input file(s) not found: {missing}")

    start = time.perf_counter()
    temp_keyword_dir = Path(
        Path(__file__).resolve().parents[1],
        "temp",
        args.main_subject,
        args.output_subdir,
        "keyword_csv",
    )
    prepared_text_dir = Path(
        Path(__file__).resolve().parents[1],
        "temp",
        args.main_subject,
        args.output_subdir,
        "prepared_text",
    )
    prepared_files = _prepare_text_inputs(
        input_files=input_files,
        prepared_text_dir=prepared_text_dir,
    )

    _extract_keywords_with_txt2phrases(
        input_files=prepared_files,
        keyword_output_dir=temp_keyword_dir,
        top_n=args.top_n,
    )

    keyword_csv_paths = collect_keyword_csvs(temp_keyword_dir)
    result = build_phase1_outputs(
        keyword_csv_paths=keyword_csv_paths,
        source_files=input_files,
        main_subject=args.main_subject,
        output_subdir=args.output_subdir,
        min_count=args.min_count,
        min_term_words=args.min_term_words,
        max_term_words=args.max_term_words,
    )
    elapsed_seconds = time.perf_counter() - start

    print(f"Phase 1 completed in {elapsed_seconds:.2f} seconds")
    print(f"Raw wordlist: {result.raw_wordlist_csv}")
    print(f"Report: {result.extraction_report_json}")
    print(f"Terms: {result.terms_count}")
    print(f"Keyword CSV files: {result.keyword_csv_count}")


if __name__ == "__main__":
    main()
