"""
Tests for reading CSV files with phrase and count columns.

Tests CSV reading functionality with:
- Named columns (e.g., "phrase", "count")
- Column numbers (e.g., column 0, column 1)
- Various CSV formats and edge cases

Date: March 2, 2026 (system date)
"""

import pytest
import csv
from pathlib import Path
from typing import List, Dict, Tuple

from encyclopedia.utils.resources import Resources


class TestCSVReading:
    """Tests for reading CSV files with phrase and count columns."""
    
    def test_read_csv_with_named_columns_phrase_count(self):
        """Test reading CSV with 'phrase' and 'count' column names."""
        # Create test CSV file
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestCSVReading")
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_file = Path(output_dir, "test_phrase_count.csv")
        
        # Write test CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['phrase', 'count'])
            writer.writeheader()
            writer.writerow({'phrase': 'climate change', 'count': '42'})
            writer.writerow({'phrase': 'greenhouse gas', 'count': '35'})
            writer.writerow({'phrase': 'carbon dioxide', 'count': '28'})
        
        # Read CSV using function (to be implemented)
        from encyclopedia.utils.csv_reader import read_phrases_from_csv
        phrases, counts = read_phrases_from_csv(
            csv_file,
            phrase_column='phrase',
            count_column='count'
        )
        
        # Verify results
        assert len(phrases) == 3, f"Expected 3 phrases, got {len(phrases)}"
        assert phrases[0] == 'climate change', f"Expected 'climate change', got '{phrases[0]}'"
        assert phrases[1] == 'greenhouse gas', f"Expected 'greenhouse gas', got '{phrases[1]}'"
        assert phrases[2] == 'carbon dioxide', f"Expected 'carbon dioxide', got '{phrases[2]}'"
        
        assert len(counts) == 3, f"Expected 3 counts, got {len(counts)}"
        assert counts[0] == 42, f"Expected count 42, got {counts[0]}"
        assert counts[1] == 35, f"Expected count 35, got {counts[1]}"
        assert counts[2] == 28, f"Expected count 28, got {counts[2]}"
        
        # Save results for human inspection
        results_file = Path(output_dir, "test_phrase_count_results.json")
        import json
        results_file.write_text(
            json.dumps({
                'phrases': phrases,
                'counts': counts,
                'total': len(phrases)
            }, indent=2),
            encoding='utf-8'
        )
        
        assert results_file.exists(), f"Results file should exist at {results_file}"
    
    def test_read_csv_with_named_columns_keyword_frequency(self):
        """Test reading CSV with 'keyword' and 'frequency' column names."""
        # Create test CSV file
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestCSVReading")
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_file = Path(output_dir, "test_keyword_frequency.csv")
        
        # Write test CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['keyword', 'frequency'])
            writer.writeheader()
            writer.writerow({'keyword': 'atom', 'frequency': '100'})
            writer.writerow({'keyword': 'molecule', 'frequency': '85'})
        
        # Read CSV using function (to be implemented)
        from encyclopedia.utils.csv_reader import read_phrases_from_csv
        phrases, counts = read_phrases_from_csv(
            csv_file,
            phrase_column='keyword',
            count_column='frequency'
        )
        
        # Verify results
        assert len(phrases) == 2, f"Expected 2 phrases, got {len(phrases)}"
        assert phrases[0] == 'atom', f"Expected 'atom', got '{phrases[0]}'"
        assert phrases[1] == 'molecule', f"Expected 'molecule', got '{phrases[1]}'"
        
        assert len(counts) == 2, f"Expected 2 counts, got {len(counts)}"
        assert counts[0] == 100, f"Expected count 100, got {counts[0]}"
        assert counts[1] == 85, f"Expected count 85, got {counts[1]}"
    
    def test_read_csv_with_column_numbers(self):
        """Test reading CSV using column numbers (0-indexed)."""
        # Create test CSV file
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestCSVReading")
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_file = Path(output_dir, "test_column_numbers.csv")
        
        # Write test CSV (phrase in column 0, count in column 1)
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['term', 'frequency', 'other'])  # Header
            writer.writerow(['DNA', '50', 'extra'])
            writer.writerow(['protein', '45', 'extra'])
        
        # Read CSV using column numbers (to be implemented)
        from encyclopedia.utils.csv_reader import read_phrases_from_csv
        phrases, counts = read_phrases_from_csv(
            csv_file,
            phrase_column=0,  # First column
            count_column=1    # Second column
        )
        
        # Verify results
        assert len(phrases) == 2, f"Expected 2 phrases, got {len(phrases)}"
        assert phrases[0] == 'DNA', f"Expected 'DNA', got '{phrases[0]}'"
        assert phrases[1] == 'protein', f"Expected 'protein', got '{phrases[1]}'"
        
        assert len(counts) == 2, f"Expected 2 counts, got {len(counts)}"
        assert counts[0] == 50, f"Expected count 50, got {counts[0]}"
        assert counts[1] == 45, f"Expected count 45, got {counts[1]}"
    
    def test_read_csv_without_count_column(self):
        """Test reading CSV with only phrase column (no count column)."""
        # Create test CSV file
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestCSVReading")
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_file = Path(output_dir, "test_no_count.csv")
        
        # Write test CSV (only phrases, no counts)
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['phrase'])
            writer.writeheader()
            writer.writerow({'phrase': 'ecosystem'})
            writer.writerow({'phrase': 'biodiversity'})
            writer.writerow({'phrase': 'photosynthesis'})
        
        # Read CSV without count column (to be implemented)
        from encyclopedia.utils.csv_reader import read_phrases_from_csv
        phrases, counts = read_phrases_from_csv(
            csv_file,
            phrase_column='phrase',
            count_column=None  # No count column
        )
        
        # Verify results
        assert len(phrases) == 3, f"Expected 3 phrases, got {len(phrases)}"
        assert 'ecosystem' in phrases, "Expected 'ecosystem' in phrases"
        assert 'biodiversity' in phrases, "Expected 'biodiversity' in phrases"
        assert 'photosynthesis' in phrases, "Expected 'photosynthesis' in phrases"
        
        # Counts should be empty list or None when not provided
        assert counts is None or len(counts) == 0, \
            f"Expected no counts when count_column=None, got {counts}"
    
    def test_read_csv_auto_detect_columns(self):
        """Test reading CSV with automatic column detection."""
        # Create test CSV file
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestCSVReading")
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_file = Path(output_dir, "test_auto_detect.csv")
        
        # Write test CSV with common column names
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['keyword', 'count'])
            writer.writeheader()
            writer.writerow({'keyword': 'telescope', 'count': '20'})
            writer.writerow({'keyword': 'microscope', 'count': '15'})
        
        # Read CSV with auto-detection (to be implemented)
        from encyclopedia.utils.csv_reader import read_phrases_from_csv
        phrases, counts = read_phrases_from_csv(
            csv_file,
            phrase_column=None,  # Auto-detect
            count_column=None    # Auto-detect
        )
        
        # Verify results
        assert len(phrases) == 2, f"Expected 2 phrases, got {len(phrases)}"
        assert 'telescope' in phrases, "Expected 'telescope' in phrases"
        assert 'microscope' in phrases, "Expected 'microscope' in phrases"
        
        assert len(counts) == 2, f"Expected 2 counts, got {len(counts)}"
        assert 20 in counts, "Expected count 20 in counts"
        assert 15 in counts, "Expected count 15 in counts"
    
    def test_read_csv_empty_file(self):
        """Test reading empty CSV file."""
        # Create empty CSV file
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestCSVReading")
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_file = Path(output_dir, "test_empty.csv")
        
        # Write empty CSV (header only)
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['phrase', 'count'])
            writer.writeheader()
        
        # Read CSV (to be implemented)
        from encyclopedia.utils.csv_reader import read_phrases_from_csv
        phrases, counts = read_phrases_from_csv(
            csv_file,
            phrase_column='phrase',
            count_column='count'
        )
        
        # Verify results (empty lists)
        assert len(phrases) == 0, f"Expected 0 phrases for empty file, got {len(phrases)}"
        assert counts is None or len(counts) == 0, \
            f"Expected no counts for empty file, got {counts}"
    
    def test_read_csv_missing_column_error(self):
        """Test that missing column raises appropriate error."""
        # Create test CSV file
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestCSVReading")
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_file = Path(output_dir, "test_missing_column.csv")
        
        # Write CSV without the requested column
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['term', 'frequency'])
            writer.writeheader()
            writer.writerow({'term': 'test', 'frequency': '10'})
        
        # Attempt to read with non-existent column
        from encyclopedia.utils.csv_reader import read_phrases_from_csv
        with pytest.raises(ValueError, match=".*not found in CSV"):
            read_phrases_from_csv(
                csv_file,
                phrase_column='nonexistent_column',
                count_column='frequency'
            )
    
    def test_read_csv_invalid_column_number_error(self):
        """Test that invalid column number raises appropriate error."""
        # Create test CSV file
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestCSVReading")
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_file = Path(output_dir, "test_invalid_column_number.csv")
        
        # Write CSV with only 2 columns
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['phrase', 'count'])
            writer.writerow(['test', '10'])
        
        # Attempt to read with invalid column number
        from encyclopedia.utils.csv_reader import read_phrases_from_csv
        with pytest.raises(ValueError, match=".*out of range"):
            read_phrases_from_csv(
                csv_file,
                phrase_column=5,  # Column 5 doesn't exist (only 0 and 1)
                count_column=1
            )
