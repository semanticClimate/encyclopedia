"""
Phase 1 wordlist extraction for IPCC/SYR workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple
import json

import pandas as pd

from encyclopedia.utils.resources import Resources


KEYWORD_COLUMNS: Tuple[str, ...] = (
    "keyword",
    "keywords",
    "keyphrase",
    "keyphrases",
    "phrase",
    "phrases",
)

COUNT_COLUMNS: Tuple[str, ...] = (
    "count",
    "counts",
    "frequency",
    "freq",
)


@dataclass(frozen=True)
class Phase1Result:
    """Outputs produced by phase 1."""

    output_dir: Path
    raw_wordlist_csv: Path
    extraction_report_json: Path
    terms_count: int
    source_files_count: int
    keyword_csv_count: int


def _normalize_text(value: object) -> str:
    text = str(value).strip()
    return " ".join(text.split())


def _find_column(df: pd.DataFrame, candidates: Sequence[str]) -> Optional[str]:
    columns = {column.lower(): column for column in df.columns}
    for candidate in candidates:
        if candidate in columns:
            return columns[candidate]
    return None


def _read_keyword_csv(csv_path: Path) -> List[Tuple[str, int]]:
    df = pd.read_csv(csv_path)
    keyword_column = _find_column(df=df, candidates=KEYWORD_COLUMNS)
    if keyword_column is None:
        return []

    count_column = _find_column(df=df, candidates=COUNT_COLUMNS)
    pairs: List[Tuple[str, int]] = []
    for _, row in df.iterrows():
        term = _normalize_text(row[keyword_column])
        if not term:
            continue
        if count_column is None:
            count = 1
        else:
            try:
                count = int(float(row[count_column]))
            except (TypeError, ValueError):
                count = 1
        if count <= 0:
            continue
        pairs.append((term, count))
    return pairs


def collect_keyword_csvs(path: Path) -> List[Path]:
    """Collect keyword CSV files from a file or directory."""
    if path.is_file() and path.suffix.lower() == ".csv":
        return [path]
    if not path.is_dir():
        return []

    csv_paths = sorted(path.rglob("*.csv"))
    keyword_paths: List[Path] = []
    for csv_path in csv_paths:
        lower_name = csv_path.name.lower()
        if "keyword" in lower_name or "keyphrase" in lower_name:
            keyword_paths.append(csv_path)
    return keyword_paths


def aggregate_keyword_counts(keyword_csv_paths: Iterable[Path]) -> Dict[str, int]:
    """Aggregate term counts from keyword CSV files."""
    counts: Dict[str, int] = {}
    for csv_path in keyword_csv_paths:
        for term, count in _read_keyword_csv(csv_path=csv_path):
            counts[term] = counts.get(term, 0) + count
    return counts


def build_phase1_outputs(
    keyword_csv_paths: Sequence[Path],
    source_files: Sequence[Path],
    main_subject: str,
    output_subdir: str = "phase1_wordlist",
    min_count: int = 2,
    min_term_words: int = 1,
    max_term_words: int = 8,
) -> Phase1Result:
    """Create Phase 1 output files under temp/<main_subject>/."""
    output_dir = Path(Resources.TEMP_DIR, main_subject, output_subdir)
    output_dir.mkdir(parents=True, exist_ok=True)

    aggregated_counts = aggregate_keyword_counts(keyword_csv_paths=keyword_csv_paths)

    filtered_items: List[Tuple[str, int]] = []
    for term, count in aggregated_counts.items():
        if count < min_count:
            continue
        token_count = len(term.split())
        if token_count < min_term_words or token_count > max_term_words:
            continue
        filtered_items.append((term, count))

    filtered_items.sort(key=lambda item: (-item[1], item[0].lower()))

    raw_wordlist_csv = Path(output_dir, "raw_wordlist.csv")
    raw_df = pd.DataFrame(filtered_items, columns=["term", "count"])
    raw_df["manual_delete"] = "No"
    raw_df.to_csv(raw_wordlist_csv, index=False)

    report = {
        "stage": "phase_1_wordlist",
        "main_subject": main_subject,
        "source_files_count": len(source_files),
        "source_files": [str(path) for path in source_files],
        "keyword_csv_count": len(keyword_csv_paths),
        "keyword_csv_files": [str(path) for path in keyword_csv_paths],
        "unique_terms_before_filtering": len(aggregated_counts),
        "terms_after_filtering": len(filtered_items),
        "min_count": min_count,
        "min_term_words": min_term_words,
        "max_term_words": max_term_words,
        "outputs": {"raw_wordlist_csv": str(raw_wordlist_csv)},
    }

    extraction_report_json = Path(output_dir, "extraction_report.json")
    extraction_report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return Phase1Result(
        output_dir=output_dir,
        raw_wordlist_csv=raw_wordlist_csv,
        extraction_report_json=extraction_report_json,
        terms_count=len(filtered_items),
        source_files_count=len(source_files),
        keyword_csv_count=len(keyword_csv_paths),
    )


def discover_source_files(path: Path) -> List[Path]:
    """Discover source files for reporting."""
    if path.is_file():
        return [path]
    if not path.is_dir():
        return []
    source_paths: List[Path] = []
    for suffix in (".txt", ".html", ".htm", ".pdf", ".xml"):
        source_paths.extend(path.rglob(f"*{suffix}"))
    return sorted(set(source_paths))
