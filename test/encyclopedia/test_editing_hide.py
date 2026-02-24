"""
Tests for hide/show entry functionality.

Tests cover:
- Hide entry (add to hidden_entries metadata)
- Show entry (remove from hidden_entries)
- Persistence to HTML file (data-hidden attribute)
- Filtering hidden entries
- Version bumping on save

All outputs saved to temp/ for human inspection.
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources


class TestHideEntry:
    """Tests for hiding/showing encyclopedia entries."""
    
    def test_hide_entry(self, small_encyclopedia):
        """Test hiding an entry adds it to hidden_entries metadata."""
        # Get initial entry count
        initial_count = len(small_encyclopedia.entries)
        assert initial_count > 0, "Encyclopedia should have entries"
        
        # Get first entry
        entry = small_encyclopedia.entries[0]
        entry_id = small_encyclopedia._generate_entry_id_from_entry(entry, 0)
        
        # Hide entry
        result = small_encyclopedia.hide_entry(entry_id)
        assert result is True, f"Hide should return True, got {result}"
        
        # Entry should still be in entries list (not deleted)
        assert len(small_encyclopedia.entries) == initial_count, \
            f"Hide should not remove entry from list. Expected {initial_count}, got {len(small_encyclopedia.entries)}"
        
        # Entry should be in hidden_entries metadata
        hidden_entries = small_encyclopedia.metadata.get('hidden_entries', [])
        assert len(hidden_entries) == 1, \
            f"Expected 1 hidden entry in metadata, got {len(hidden_entries)}"
        
        assert entry_id in hidden_entries, \
            f"Entry ID {entry_id} should be in hidden_entries: {hidden_entries}"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestHideEntry")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "hide_entry_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
        assert output_file.stat().st_size > 0, "Output file should not be empty"
        
        # Verify HTML contains data-hidden attribute
        html_content = output_file.read_text(encoding='utf-8')
        assert f'data-hidden="true"' in html_content or f'data-entry-id="{entry_id}"' in html_content, \
            f"HTML should contain hidden entry marker for entry_id {entry_id}"
    
    def test_show_entry(self, small_encyclopedia):
        """Test showing a hidden entry removes it from hidden_entries."""
        # Get first entry
        entry = small_encyclopedia.entries[0]
        entry_id = small_encyclopedia._generate_entry_id_from_entry(entry, 0)
        
        # Hide entry
        small_encyclopedia.hide_entry(entry_id)
        
        # Verify hidden
        hidden_entries = small_encyclopedia.metadata.get('hidden_entries', [])
        assert len(hidden_entries) == 1, \
            f"Expected 1 hidden entry before show, got {len(hidden_entries)}"
        
        # Show entry
        result = small_encyclopedia.show_entry(entry_id)
        assert result is True, f"Show should return True, got {result}"
        
        # Entry should be removed from hidden_entries
        hidden_entries = small_encyclopedia.metadata.get('hidden_entries', [])
        assert len(hidden_entries) == 0, \
            f"Expected 0 hidden entries after show, got {len(hidden_entries)}"
        
        # Entry should still be in entries list
        assert len(small_encyclopedia.entries) > 0, \
            "Entry should still be in entries list after showing"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestHideEntry")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "show_entry_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
    
    def test_hide_nonexistent_entry(self, small_encyclopedia):
        """Test hiding non-existent entry returns False."""
        # Try to hide non-existent entry
        result = small_encyclopedia.hide_entry("nonexistent_entry_id")
        assert result is False, \
            f"Hiding non-existent entry should return False, got {result}"
        
        # No entries should be in hidden_entries
        hidden_entries = small_encyclopedia.metadata.get('hidden_entries', [])
        assert len(hidden_entries) == 0, \
            f"Expected 0 hidden entries, got {len(hidden_entries)}"
    
    def test_get_hidden_entries(self, small_encyclopedia):
        """Test getting list of hidden entry IDs."""
        # Initially no hidden entries
        hidden = small_encyclopedia.get_hidden_entries()
        assert len(hidden) == 0, \
            f"Expected 0 hidden entries initially, got {len(hidden)}"
        
        # Hide two entries
        entry1 = small_encyclopedia.entries[0]
        entry_id1 = small_encyclopedia._generate_entry_id_from_entry(entry1, 0)
        small_encyclopedia.hide_entry(entry_id1)
        
        entry2 = small_encyclopedia.entries[1]
        entry_id2 = small_encyclopedia._generate_entry_id_from_entry(entry2, 1)
        small_encyclopedia.hide_entry(entry_id2)
        
        # Get hidden entries
        hidden = small_encyclopedia.get_hidden_entries()
        assert len(hidden) == 2, \
            f"Expected 2 hidden entries, got {len(hidden)}"
        
        assert entry_id1 in hidden, \
            f"Entry ID {entry_id1} should be in hidden entries"
        assert entry_id2 in hidden, \
            f"Entry ID {entry_id2} should be in hidden entries"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestHideEntry")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "get_hidden_entries_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        # Also save hidden entries JSON
        hidden_file = Path(output_dir, "hidden_entries.json")
        import json
        hidden_file.write_text(
            json.dumps({'hidden_entry_ids': hidden}, indent=2),
            encoding='utf-8'
        )
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
        assert hidden_file.exists(), f"Hidden entries JSON should exist at {hidden_file}"
    
    def test_hide_persistence_to_html(self, small_encyclopedia):
        """Test that hidden entries are persisted to HTML file with data-hidden attribute."""
        # Get first entry
        entry = small_encyclopedia.entries[0]
        entry_id = small_encyclopedia._generate_entry_id_from_entry(entry, 0)
        
        # Hide entry
        small_encyclopedia.hide_entry(entry_id)
        
        # Save to HTML
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestHideEntry")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "hide_persistence_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        # Load from HTML
        loaded_encyclopedia = AmiEncyclopedia()
        loaded_encyclopedia.create_from_html_file(output_file)
        
        # Verify hidden entry is in metadata
        hidden_entries = loaded_encyclopedia.metadata.get('hidden_entries', [])
        assert len(hidden_entries) >= 1, \
            f"Expected at least 1 hidden entry after loading from HTML, got {len(hidden_entries)}"
        
        assert entry_id in hidden_entries, \
            f"Entry ID {entry_id} should be in hidden_entries after loading. Found: {hidden_entries}"
        
        # Verify HTML contains data-hidden attribute
        html_content = output_file.read_text(encoding='utf-8')
        assert 'data-hidden="true"' in html_content or entry_id in html_content, \
            f"HTML should contain data-hidden attribute or entry_id {entry_id}"
        
        # Save loaded encyclopedia for human inspection
        loaded_output_file = Path(output_dir, "hide_persistence_loaded_test.html")
        loaded_encyclopedia.save_wiki_normalized_html(loaded_output_file)
        
        assert loaded_output_file.exists(), f"Loaded output file should exist at {loaded_output_file}"
    
    def test_version_bump_on_hide(self, small_encyclopedia):
        """Test that version is bumped when entry is hidden and saved."""
        # Get initial version
        initial_version = small_encyclopedia.metadata.get('version', '1.0.0')
        
        # Get first entry
        entry = small_encyclopedia.entries[0]
        entry_id = small_encyclopedia._generate_entry_id_from_entry(entry, 0)
        
        # Hide entry
        small_encyclopedia.hide_entry(entry_id)
        
        # Save to HTML (this should bump version)
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestHideEntry")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "version_bump_hide_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        # Version should be bumped
        new_version = small_encyclopedia.metadata.get('version')
        assert new_version != initial_version, \
            f"Version should be bumped after hide and save. Initial: {initial_version}, New: {new_version}"
        
        # Save for human inspection
        assert output_file.exists(), f"Output file should exist at {output_file}"
        
        # Also save metadata JSON for inspection
        metadata_file = Path(output_dir, "version_bump_hide_metadata.json")
        import json
        metadata_file.write_text(
            json.dumps({
                'initial_version': initial_version,
                'new_version': new_version,
                'hidden_entries_count': len(small_encyclopedia.metadata.get('hidden_entries', []))
            }, indent=2),
            encoding='utf-8'
        )
        
        assert metadata_file.exists(), f"Metadata file should exist at {metadata_file}"
    
    def test_hide_multiple_entries(self, small_encyclopedia):
        """Test hiding multiple entries."""
        # Hide first 3 entries
        hidden_ids = []
        for i in range(min(3, len(small_encyclopedia.entries))):
            entry = small_encyclopedia.entries[i]
            entry_id = small_encyclopedia._generate_entry_id_from_entry(entry, i)
            small_encyclopedia.hide_entry(entry_id)
            hidden_ids.append(entry_id)
        
        # Verify all are hidden
        hidden_entries = small_encyclopedia.metadata.get('hidden_entries', [])
        assert len(hidden_entries) == len(hidden_ids), \
            f"Expected {len(hidden_ids)} hidden entries, got {len(hidden_entries)}"
        
        for entry_id in hidden_ids:
            assert entry_id in hidden_entries, \
                f"Entry ID {entry_id} should be in hidden_entries"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestHideEntry")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "hide_multiple_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
