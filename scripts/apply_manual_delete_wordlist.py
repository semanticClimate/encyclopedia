#!/usr/bin/env python3
"""
Apply manual_delete decisions to a phase-1 wordlist CSV.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


def _is_yes(value: object) -> bool:
    return str(value).strip().lower() in {"yes", "y", "true", "1"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply manual_delete column (Yes/No) to wordlist CSV"
    )
    parser.add_argument("--input-csv", required=True, help="Input wordlist CSV")
    parser.add_argument(
        "--mode",
        choices=["delete", "hide"],
        default="delete",
        help="delete = remove rows; hide = keep rows with hidden=yes column",
    )
    parser.add_argument(
        "--output-csv",
        default=None,
        help="Optional output CSV path (default: <input>_curated.csv)",
    )
    parser.add_argument(
        "--deleted-csv",
        default=None,
        help="Optional path for rows marked Yes (default: <input>_deleted.csv)",
    )
    args = parser.parse_args()

    input_csv = Path(args.input_csv).resolve()
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    df = pd.read_csv(input_csv)
    if "manual_delete" not in df.columns:
        raise ValueError("Input CSV must contain 'manual_delete' column")

    mask_delete = df["manual_delete"].apply(_is_yes)
    deleted_df = df[mask_delete].copy()
    kept_df = df[~mask_delete].copy()

    if args.mode == "hide":
        out_df = df.copy()
        out_df["hidden"] = mask_delete.map(lambda value: "yes" if value else "no")
    else:
        out_df = kept_df

    output_csv = (
        Path(args.output_csv).resolve()
        if args.output_csv
        else Path(input_csv.parent, f"{input_csv.stem}_curated.csv")
    )
    deleted_csv = (
        Path(args.deleted_csv).resolve()
        if args.deleted_csv
        else Path(input_csv.parent, f"{input_csv.stem}_deleted.csv")
    )

    out_df.to_csv(output_csv, index=False)
    deleted_df.to_csv(deleted_csv, index=False)

    print(f"Input rows: {len(df)}")
    print(f"Marked manual_delete=Yes: {len(deleted_df)}")
    print(f"Output rows: {len(out_df)}")
    print(f"Curated CSV: {output_csv}")
    print(f"Deleted/hidden CSV: {deleted_csv}")


if __name__ == "__main__":
    main()
