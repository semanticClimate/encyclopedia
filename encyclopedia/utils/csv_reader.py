"""
CSV reading utilities for extracting phrases and counts from CSV files.

Supports:
- Reading CSV files with named columns (e.g., "phrase", "count")
- Reading CSV files using column numbers (0-indexed)
- Auto-detection of common column names
- Optional count columns

**Note**: This module may be transferred to ../amilib in the future if CSV reading
functionality is needed there. Consider this when making changes.

Date: March 2, 2026 (system date)
"""

from pathlib import Path
from typing import List, Tuple, Optional, Union
import pandas as pd


# Common column name patterns for auto-detection
PHRASE_COLUMN_NAMES = [
    'phrase', 'phrases',
    'keyword', 'keywords',
    'keyphrase', 'keyphrases',
    'term', 'terms',
    'word', 'words'
]

COUNT_COLUMN_NAMES = [
    'count', 'counts',
    'frequency', 'freq',
    'occurrences', 'occurrence'
]


def read_phrases_from_csv(
    csv_file: Path,
    phrase_column: Optional[Union[str, int]] = None,
    count_column: Optional[Union[str, int]] = None
) -> Tuple[List[str], Optional[List[int]]]:
    """
    Read phrases and counts from a CSV file.
    
    Supports:
    - Named columns: pass column name as string (e.g., "phrase", "count")
    - Column numbers: pass column index as int (0-indexed, e.g., 0, 1)
    - Auto-detection: pass None to auto-detect common column names
    
    Args:
        csv_file: Path to CSV file
        phrase_column: Column name (str), column number (int), or None for auto-detect
        count_column: Column name (str), column number (int), None for auto-detect, or omit for no counts
        
    Returns:
        Tuple of (phrases: List[str], counts: Optional[List[int]])
        - phrases: List of phrase strings
        - counts: List of integer counts, or None if count_column is None/omitted
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If column name/number not found or invalid
        pd.errors.EmptyDataError: If CSV file is empty (no data rows)
    """
    # Validate file exists
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file}")
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_file)
    except pd.errors.EmptyDataError:
        # Empty file - return empty lists
        return [], None
    
    # Validate CSV has data
    if len(df) == 0:
        return [], None
    
    # Auto-detect phrase column if not specified
    if phrase_column is None:
        phrase_column = _auto_detect_column(df, PHRASE_COLUMN_NAMES)
        if phrase_column is None:
            # Fallback: use first column
            phrase_column = 0
    
    # Auto-detect count column if not specified
    if count_column is None:
        count_column = _auto_detect_column(df, COUNT_COLUMN_NAMES)
        # count_column can remain None if not found (counts are optional)
    
    # Extract phrase column
    phrases = _extract_column(df, phrase_column, 'phrase')
    
    # Extract count column (if specified)
    counts = None
    if count_column is not None:
        counts = _extract_column(df, count_column, 'count', convert_to_int=True)
    
    return phrases, counts


def _auto_detect_column(df: pd.DataFrame, column_names: List[str]) -> Optional[Union[str, int]]:
    """
    Auto-detect column by trying common column names.
    
    Args:
        df: DataFrame to search
        column_names: List of column names to try
        
    Returns:
        Column name (str) if found, None otherwise
    """
    for col_name in column_names:
        if col_name in df.columns:
            return col_name
    return None


def _extract_column(
    df: pd.DataFrame,
    column: Union[str, int],
    column_type: str,
    convert_to_int: bool = False
) -> List[Union[str, int]]:
    """
    Extract column from DataFrame by name or number.
    
    Args:
        df: DataFrame to extract from
        column: Column name (str) or column number (int, 0-indexed)
        column_type: Type name for error messages (e.g., "phrase", "count")
        convert_to_int: If True, convert values to integers (for count columns)
        
    Returns:
        List of column values
        
    Raises:
        ValueError: If column name/number not found or invalid
    """
    # Handle column by name
    if isinstance(column, str):
        if column not in df.columns:
            raise ValueError(
                f"{column_type.capitalize()} column '{column}' not found in CSV. "
                f"Available columns: {list(df.columns)}"
            )
        values = df[column].dropna().astype(str).str.strip()
        values = values[values != '']
        values = values[values.str.lower() != 'nan'].tolist()
    
    # Handle column by number
    elif isinstance(column, int):
        if column < 0 or column >= len(df.columns):
            raise ValueError(
                f"{column_type.capitalize()} column number {column} is out of range. "
                f"CSV has {len(df.columns)} columns (0-{len(df.columns)-1})"
            )
        col_name = df.columns[column]
        values = df[col_name].dropna().astype(str).str.strip()
        values = values[values != '']
        values = values[values.str.lower() != 'nan'].tolist()
    
    else:
        raise ValueError(
            f"Invalid {column_type} column specification: {column}. "
            f"Must be column name (str) or column number (int)"
        )
    
    # Convert to integers if requested (for count columns)
    if convert_to_int:
        try:
            values = [int(float(val)) for val in values]
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Failed to convert {column_type} column values to integers: {e}. "
                f"Values: {values[:5]}"
            )
    
    return values
