"""
Tests for delete entry functionality.

Tests cover:
- Soft delete (mark as deleted in metadata)
- Hard delete (remove from entries list)
- Recovery from metadata
- Version bumping on save
- Persistence to HTML file

All outputs saved to temp/ for human inspection.
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources


class TestDeleteEntry:
    """Tests for deleting encyclopedia entries."""
    
    def test_soft_delete_entry(self, small_encyclopedia):
        """Test soft delete marks entry as deleted in metadata but keeps in entries list."""
        # Get initial entry count
        initial_count = len(small_encyclopedia.entries)
        assert initial_count > 0, "Encyclopedia should have entries"
        
        # Get first entry
        entry = small_encyclopedia.entries[0]
        entry_id = small_encyclopedia._generate_entry_id_from_entry(entry, 0)
        
        # Soft delete entry
        result = small_encyclopedia.delete_entry(entry_id, soft=True)
        assert result is True, f"Soft delete should return True, got {result}"
        
        # Entry should still be in entries list
        assert len(small_encyclopedia.entries) == initial_count, \
            f"Soft delete should not remove entry from list. Expected {initial_count}, got {len(small_encyclopedia.entries)}"
        
        # Entry should be in deleted_entries metadata
        deleted_entries = small_encyclopedia.metadata.get('deleted_entries', [])
        assert len(deleted_entries) == 1, \
            f"Expected 1 deleted entry in metadata, got {len(deleted_entries)}"
        
        deleted_entry = deleted_entries[0]
        assert deleted_entry['entry_id'] == entry_id, \
            f"Deleted entry ID mismatch. Expected {entry_id}, got {deleted_entry['entry_id']}"
        assert deleted_entry['term'] == entry.get('term'), \
            f"Deleted entry term mismatch. Expected {entry.get('term')}, got {deleted_entry['term']}"
        assert 'deleted_at' in deleted_entry, \
            "Deleted entry should have deleted_at timestamp"
        assert 'entry_data' in deleted_entry, \
            "Deleted entry should have full entry_data for recovery"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestDeleteEntry")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "soft_delete_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
        assert output_file.stat().st_size > 0, "Output file should not be empty"
    
    def test_hard_delete_entry(self, small_encyclopedia):
        """Test hard delete removes entry from entries list."""
        # Get initial entry count
        initial_count = len(small_encyclopedia.entries)
        assert initial_count > 0, "Encyclopedia should have entries"
        
        # Get first entry
        entry = small_encyclopedia.entries[0]
        entry_id = small_encyclopedia._generate_entry_id_from_entry(entry, 0)
        term = entry.get('term')
        
        # Hard delete entry
        result = small_encyclopedia.delete_entry(entry_id, soft=False)
        assert result is True, f"Hard delete should return True, got {result}"
        
        # Entry should be removed from entries list
        assert len(small_encyclopedia.entries) == initial_count - 1, \
            f"Hard delete should remove entry from list. Expected {initial_count - 1}, got {len(small_encyclopedia.entries)}"
        
        # Entry should not be in entries list anymore
        remaining_terms = [e.get('term') for e in small_encyclopedia.entries]
        assert term not in remaining_terms, \
            f"Deleted entry '{term}' should not be in remaining entries: {remaining_terms}"
        
        # Entry should be in deleted_entries metadata
        deleted_entries = small_encyclopedia.metadata.get('deleted_entries', [])
        assert len(deleted_entries) == 1, \
            f"Expected 1 deleted entry in metadata, got {len(deleted_entries)}"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestDeleteEntry")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "hard_delete_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
    
    def test_delete_nonexistent_entry(self, small_encyclopedia):
        """Test deleting non-existent entry returns False."""
        # Try to delete non-existent entry
        result = small_encyclopedia.delete_entry("nonexistent_entry_id", soft=True)
        assert result is False, \
            f"Deleting non-existent entry should return False, got {result}"
        
        # No entries should be in deleted_entries
        deleted_entries = small_encyclopedia.metadata.get('deleted_entries', [])
        assert len(deleted_entries) == 0, \
            f"Expected 0 deleted entries, got {len(deleted_entries)}"
    
    def test_restore_deleted_entry(self, small_encyclopedia):
        """Test restoring a soft-deleted entry."""
        # Get first entry
        entry = small_encyclopedia.entries[0]
        entry_id = small_encyclopedia._generate_entry_id_from_entry(entry, 0)
        initial_count = len(small_encyclopedia.entries)
        
        # Soft delete entry
        small_encyclopedia.delete_entry(entry_id, soft=True)
        
        # Verify deleted
        deleted_entries = small_encyclopedia.metadata.get('deleted_entries', [])
        assert len(deleted_entries) == 1, \
            f"Expected 1 deleted entry before restore, got {len(deleted_entries)}"
        
        # Restore entry
        result = small_encyclopedia.restore_entry(entry_id)
        assert result is True, f"Restore should return True, got {result}"
        
        # Entry should be removed from deleted_entries
        deleted_entries = small_encyclopedia.metadata.get('deleted_entries', [])
        assert len(deleted_entries) == 0, \
            f"Expected 0 deleted entries after restore, got {len(deleted_entries)}"
        
        # Entry count should be unchanged (soft delete doesn't remove from list)
        assert len(small_encyclopedia.entries) == initial_count, \
            f"Entry count should remain {initial_count} after soft delete and restore"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestDeleteEntry")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "restore_deleted_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
    
    def test_restore_hard_deleted_entry(self, small_encyclopedia):
        """Test restoring a hard-deleted entry adds it back to entries list."""
        # Get first entry
        entry = small_encyclopedia.entries[0]
        entry_id = small_encyclopedia._generate_entry_id_from_entry(entry, 0)
        term = entry.get('term')
        initial_count = len(small_encyclopedia.entries)
        
        # Hard delete entry
        small_encyclopedia.delete_entry(entry_id, soft=False)
        
        # Verify removed from entries
        assert len(small_encyclopedia.entries) == initial_count - 1, \
            f"Entry should be removed after hard delete"
        
        # Restore entry
        result = small_encyclopedia.restore_entry(entry_id)
        assert result is True, f"Restore should return True, got {result}"
        
        # Entry should be back in entries list
        assert len(small_encyclopedia.entries) == initial_count, \
            f"Entry should be restored to entries list. Expected {initial_count}, got {len(small_encyclopedia.entries)}"
        
        # Entry term should be in entries
        restored_terms = [e.get('term') for e in small_encyclopedia.entries]
        assert term in restored_terms, \
            f"Restored entry '{term}' should be in entries: {restored_terms}"
        
        # Entry should be removed from deleted_entries
        deleted_entries = small_encyclopedia.metadata.get('deleted_entries', [])
        assert len(deleted_entries) == 0, \
            f"Expected 0 deleted entries after restore, got {len(deleted_entries)}"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestDeleteEntry")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "restore_hard_deleted_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
    
    def test_delete_persistence_to_html(self, small_encyclopedia):
        """Test that deleted entries are persisted to HTML file."""
        # Get first entry
        entry = small_encyclopedia.entries[0]
        entry_id = small_encyclopedia._generate_entry_id_from_entry(entry, 0)
        
        # Soft delete entry
        small_encyclopedia.delete_entry(entry_id, soft=True)
        
        # Save to HTML
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestDeleteEntry")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "delete_persistence_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        # Load from HTML
        loaded_encyclopedia = AmiEncyclopedia()
        loaded_encyclopedia.create_from_html_file(output_file)
        
        # Verify deleted entry is in metadata
        deleted_entries = loaded_encyclopedia.metadata.get('deleted_entries', [])
        assert len(deleted_entries) >= 1, \
            f"Expected at least 1 deleted entry after loading from HTML, got {len(deleted_entries)}"
        
        # Find deleted entry by ID
        deleted_entry_found = next((de for de in deleted_entries if de.get('entry_id') == entry_id), None)
        assert deleted_entry_found is not None, \
            f"Deleted entry ID {entry_id} should be in deleted_entries. Found IDs: {[de.get('entry_id') for de in deleted_entries]}"
        
        # Save loaded encyclopedia for human inspection
        loaded_output_file = Path(output_dir, "delete_persistence_loaded_test.html")
        loaded_encyclopedia.save_wiki_normalized_html(loaded_output_file)
        
        assert loaded_output_file.exists(), f"Loaded output file should exist at {loaded_output_file}"
    
    def test_version_bump_on_delete(self, small_encyclopedia):
        """Test that version is bumped when entry is deleted and saved."""
        # Get initial version
        initial_version = small_encyclopedia.metadata.get('version', '1.0.0')
        
        # Get first entry
        entry = small_encyclopedia.entries[0]
        entry_id = small_encyclopedia._generate_entry_id_from_entry(entry, 0)
        
        # Delete entry
        small_encyclopedia.delete_entry(entry_id, soft=True)
        
        # Save to HTML (this should bump version)
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestDeleteEntry")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "version_bump_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        # Version should be bumped
        new_version = small_encyclopedia.metadata.get('version')
        assert new_version != initial_version, \
            f"Version should be bumped after delete and save. Initial: {initial_version}, New: {new_version}"
        
        # Save for human inspection
        assert output_file.exists(), f"Output file should exist at {output_file}"
        
        # Also save metadata JSON for inspection
        metadata_file = Path(output_dir, "version_bump_metadata.json")
        import json
        metadata_file.write_text(
            json.dumps({
                'initial_version': initial_version,
                'new_version': new_version,
                'deleted_entries_count': len(small_encyclopedia.metadata.get('deleted_entries', []))
            }, indent=2),
            encoding='utf-8'
        )
        
        assert metadata_file.exists(), f"Metadata file should exist at {metadata_file}"
    
    def test_get_deleted_entries(self, small_encyclopedia):
        """Test getting list of deleted entries."""
        # Initially no deleted entries
        deleted = small_encyclopedia.get_deleted_entries()
        assert len(deleted) == 0, \
            f"Expected 0 deleted entries initially, got {len(deleted)}"
        
        # Ensure we have at least 2 entries
        assert len(small_encyclopedia.entries) >= 2, \
            f"Need at least 2 entries for this test, got {len(small_encyclopedia.entries)}"
        
        # Delete two entries
        entry1 = small_encyclopedia.entries[0]
        entry_id1 = small_encyclopedia._generate_entry_id_from_entry(entry1, 0)
        small_encyclopedia.delete_entry(entry_id1, soft=True)
        
        entry2 = small_encyclopedia.entries[1]
        entry_id2 = small_encyclopedia._generate_entry_id_from_entry(entry2, 1)
        small_encyclopedia.delete_entry(entry_id2, soft=True)
        
        # Get deleted entries
        deleted = small_encyclopedia.get_deleted_entries()
        assert len(deleted) == 2, \
            f"Expected 2 deleted entries, got {len(deleted)}"
        
        deleted_ids = [d['entry_id'] for d in deleted]
        assert entry_id1 in deleted_ids, \
            f"Entry ID {entry_id1} should be in deleted entries"
        assert entry_id2 in deleted_ids, \
            f"Entry ID {entry_id2} should be in deleted entries"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestDeleteEntry")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "get_deleted_entries_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        # Also save deleted entries JSON
        deleted_file = Path(output_dir, "deleted_entries.json")
        import json
        deleted_file.write_text(
            json.dumps(deleted, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
        assert deleted_file.exists(), f"Deleted entries JSON should exist at {deleted_file}"
