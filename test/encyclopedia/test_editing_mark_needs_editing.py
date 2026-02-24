"""
Tests for marking entries as needing editing.

Tests cover:
- Mark entry as needing editing (with reason and notes)
- Resolve editing flag
- Get entries needing editing (filtered by reason)
- Persistence to HTML file (data-needs-editing attribute)
- Version bumping on save

All outputs saved to temp/ for human inspection.
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources


class TestMarkNeedsEditing:
    """Tests for marking entries as needing editing."""
    
    def test_mark_entry_needs_editing(self, small_encyclopedia):
        """Test marking an entry as needing editing adds flag to entry."""
        # Get first entry
        entry = small_encyclopedia.entries[0]
        entry_id = small_encyclopedia._generate_entry_id_from_entry(entry, 0)
        
        # Mark as needing editing
        reason = "disambiguation"
        notes = "This is a disambiguation page"
        result = small_encyclopedia.mark_entry_needs_editing(entry_id, reason, notes)
        assert result is True, f"Mark needs editing should return True, got {result}"
        
        # Entry should have needs_editing flag
        entry_dict = next((e for e in small_encyclopedia.entries 
                          if small_encyclopedia._generate_entry_id_from_entry(e, small_encyclopedia.entries.index(e)) == entry_id), None)
        assert entry_dict is not None, f"Entry with ID {entry_id} should exist"
        
        needs_editing = entry_dict.get('needs_editing', {})
        assert needs_editing.get('flag') is True, \
            f"Entry should have needs_editing flag set to True"
        assert needs_editing.get('reason') == reason, \
            f"Reason should be '{reason}', got '{needs_editing.get('reason')}'"
        assert needs_editing.get('notes') == notes, \
            f"Notes should be '{notes}', got '{needs_editing.get('notes')}'"
        assert 'marked_at' in needs_editing, \
            "needs_editing should have marked_at timestamp"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestMarkNeedsEditing")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "mark_needs_editing_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
        assert output_file.stat().st_size > 0, "Output file should not be empty"
        
        # Verify HTML contains data-needs-editing attribute
        html_content = output_file.read_text(encoding='utf-8')
        assert 'data-needs-editing="true"' in html_content or entry_id in html_content, \
            f"HTML should contain needs-editing marker for entry_id {entry_id}"
    
    def test_mark_entry_needs_editing_different_reasons(self, small_encyclopedia):
        """Test marking entries with different reasons."""
        reasons = ["disambiguation", "incomplete", "error", "user_marked"]
        
        marked_entries = []
        for i, reason in enumerate(reasons):
            if i >= len(small_encyclopedia.entries):
                break
            
            entry = small_encyclopedia.entries[i]
            entry_id = small_encyclopedia._generate_entry_id_from_entry(entry, i)
            notes = f"Test notes for {reason}"
            
            result = small_encyclopedia.mark_entry_needs_editing(entry_id, reason, notes)
            assert result is True, f"Mark needs editing should return True for {reason}"
            
            marked_entries.append((entry_id, reason))
        
        # Verify all are marked
        for entry_id, reason in marked_entries:
            entry_dict = next((e for e in small_encyclopedia.entries 
                              if small_encyclopedia._generate_entry_id_from_entry(e, small_encyclopedia.entries.index(e)) == entry_id), None)
            assert entry_dict is not None, f"Entry with ID {entry_id} should exist"
            
            needs_editing = entry_dict.get('needs_editing', {})
            assert needs_editing.get('flag') is True, \
                f"Entry {entry_id} should have needs_editing flag set"
            assert needs_editing.get('reason') == reason, \
                f"Entry {entry_id} should have reason '{reason}'"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestMarkNeedsEditing")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "mark_different_reasons_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
    
    def test_resolve_entry_editing(self, small_encyclopedia):
        """Test resolving editing flag removes needs_editing flag."""
        # Get first entry
        entry = small_encyclopedia.entries[0]
        entry_id = small_encyclopedia._generate_entry_id_from_entry(entry, 0)
        
        # Mark as needing editing
        small_encyclopedia.mark_entry_needs_editing(entry_id, "disambiguation", "Test notes")
        
        # Verify marked
        entry_dict = next((e for e in small_encyclopedia.entries 
                          if small_encyclopedia._generate_entry_id_from_entry(e, small_encyclopedia.entries.index(e)) == entry_id), None)
        needs_editing = entry_dict.get('needs_editing', {})
        assert needs_editing.get('flag') is True, \
            "Entry should be marked as needing editing"
        
        # Resolve editing
        result = small_encyclopedia.resolve_entry_editing(entry_id)
        assert result is True, f"Resolve editing should return True, got {result}"
        
        # Entry should no longer have needs_editing flag (or flag should be False)
        entry_dict = next((e for e in small_encyclopedia.entries 
                          if small_encyclopedia._generate_entry_id_from_entry(e, small_encyclopedia.entries.index(e)) == entry_id), None)
        needs_editing = entry_dict.get('needs_editing', {})
        assert needs_editing.get('flag') is False or 'needs_editing' not in entry_dict, \
            f"Entry should no longer need editing. needs_editing: {needs_editing}"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestMarkNeedsEditing")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "resolve_editing_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
    
    def test_get_entries_needing_editing(self, small_encyclopedia):
        """Test getting list of entries needing editing."""
        # Initially no entries needing editing
        needing_editing = small_encyclopedia.get_entries_needing_editing()
        assert len(needing_editing) == 0, \
            f"Expected 0 entries needing editing initially, got {len(needing_editing)}"
        
        # Mark two entries as needing editing
        entry1 = small_encyclopedia.entries[0]
        entry_id1 = small_encyclopedia._generate_entry_id_from_entry(entry1, 0)
        small_encyclopedia.mark_entry_needs_editing(entry_id1, "disambiguation", "Notes 1")
        
        entry2 = small_encyclopedia.entries[1]
        entry_id2 = small_encyclopedia._generate_entry_id_from_entry(entry2, 1)
        small_encyclopedia.mark_entry_needs_editing(entry_id2, "incomplete", "Notes 2")
        
        # Get all entries needing editing
        needing_editing = small_encyclopedia.get_entries_needing_editing()
        assert len(needing_editing) == 2, \
            f"Expected 2 entries needing editing, got {len(needing_editing)}"
        
        needing_editing_ids = [e.get('term') for e in needing_editing]
        assert entry1.get('term') in needing_editing_ids, \
            f"Entry '{entry1.get('term')}' should be in entries needing editing"
        assert entry2.get('term') in needing_editing_ids, \
            f"Entry '{entry2.get('term')}' should be in entries needing editing"
        
        # Get entries needing editing filtered by reason
        disambiguation_entries = small_encyclopedia.get_entries_needing_editing(reason="disambiguation")
        assert len(disambiguation_entries) == 1, \
            f"Expected 1 disambiguation entry, got {len(disambiguation_entries)}"
        assert disambiguation_entries[0].get('term') == entry1.get('term'), \
            f"Disambiguation entry should be '{entry1.get('term')}'"
        
        incomplete_entries = small_encyclopedia.get_entries_needing_editing(reason="incomplete")
        assert len(incomplete_entries) == 1, \
            f"Expected 1 incomplete entry, got {len(incomplete_entries)}"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestMarkNeedsEditing")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "get_entries_needing_editing_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        # Also save entries needing editing JSON
        needing_editing_file = Path(output_dir, "entries_needing_editing.json")
        import json
        needing_editing_file.write_text(
            json.dumps({
                'all': [{'term': e.get('term'), 'reason': e.get('needs_editing', {}).get('reason')} 
                       for e in needing_editing],
                'disambiguation': [{'term': e.get('term')} for e in disambiguation_entries],
                'incomplete': [{'term': e.get('term')} for e in incomplete_entries]
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
        assert needing_editing_file.exists(), f"Entries needing editing JSON should exist at {needing_editing_file}"
    
    def test_mark_needs_editing_persistence_to_html(self, small_encyclopedia):
        """Test that needs_editing flags are persisted to HTML file."""
        # Get first entry
        entry = small_encyclopedia.entries[0]
        entry_id = small_encyclopedia._generate_entry_id_from_entry(entry, 0)
        
        # Mark as needing editing
        small_encyclopedia.mark_entry_needs_editing(entry_id, "disambiguation", "Test notes")
        
        # Save to HTML
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestMarkNeedsEditing")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "mark_persistence_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        # Load from HTML
        loaded_encyclopedia = AmiEncyclopedia()
        loaded_encyclopedia.create_from_html_file(output_file)
        
        # Verify needs_editing flag is preserved
        # Find entry by ID (try multiple methods)
        entry_dict = None
        for idx, e in enumerate(loaded_encyclopedia.entries):
            e_id = loaded_encyclopedia._generate_entry_id_from_entry(e, idx)
            if e_id == entry_id:
                entry_dict = e
                break
        
        # Also try matching by term if ID match fails
        if entry_dict is None:
            original_entry = next((e for e in small_encyclopedia.entries 
                                  if small_encyclopedia._generate_entry_id_from_entry(e, small_encyclopedia.entries.index(e)) == entry_id), None)
            if original_entry:
                term = original_entry.get('term', '')
                entry_dict = next((e for e in loaded_encyclopedia.entries if e.get('term', '').lower() == term.lower()), None)
        
        assert entry_dict is not None, \
            f"Entry with ID {entry_id} should exist after loading. Available IDs: {[loaded_encyclopedia._generate_entry_id_from_entry(e, idx) for idx, e in enumerate(loaded_encyclopedia.entries[:5])]}"
        
        needs_editing = entry_dict.get('needs_editing', {})
        assert needs_editing.get('flag') is True, \
            f"Entry should still be marked as needing editing after loading. needs_editing: {needs_editing}, entry: {entry_dict.get('term')}"
        assert needs_editing.get('reason') == "disambiguation", \
            f"Reason should be preserved. Expected 'disambiguation', got '{needs_editing.get('reason')}'"
        
        # Save loaded encyclopedia for human inspection
        loaded_output_file = Path(output_dir, "mark_persistence_loaded_test.html")
        loaded_encyclopedia.save_wiki_normalized_html(loaded_output_file)
        
        assert loaded_output_file.exists(), f"Loaded output file should exist at {loaded_output_file}"
    
    def test_version_bump_on_mark_needs_editing(self, small_encyclopedia):
        """Test that version is bumped when entry is marked and saved."""
        # Get initial version
        initial_version = small_encyclopedia.metadata.get('version', '1.0.0')
        
        # Get first entry
        entry = small_encyclopedia.entries[0]
        entry_id = small_encyclopedia._generate_entry_id_from_entry(entry, 0)
        
        # Mark as needing editing
        small_encyclopedia.mark_entry_needs_editing(entry_id, "disambiguation", "Test")
        
        # Save to HTML (this should bump version)
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestMarkNeedsEditing")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "version_bump_mark_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        # Version should be bumped
        new_version = small_encyclopedia.metadata.get('version')
        assert new_version != initial_version, \
            f"Version should be bumped after mark and save. Initial: {initial_version}, New: {new_version}"
        
        # Save for human inspection
        assert output_file.exists(), f"Output file should exist at {output_file}"
        
        # Also save metadata JSON for inspection
        metadata_file = Path(output_dir, "version_bump_mark_metadata.json")
        import json
        metadata_file.write_text(
            json.dumps({
                'initial_version': initial_version,
                'new_version': new_version,
                'entries_needing_editing_count': len(small_encyclopedia.get_entries_needing_editing())
            }, indent=2),
            encoding='utf-8'
        )
        
        assert metadata_file.exists(), f"Metadata file should exist at {metadata_file}"
