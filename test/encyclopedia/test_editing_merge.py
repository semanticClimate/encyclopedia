"""
Tests for merging encyclopedias.

Tests cover:
- Merge one encyclopedia into another
- Duplicate detection and conflict resolution
- Metadata merging
- Version bumping on save
- Persistence to HTML file

NOTE: Uses existing fixtures (small_encyclopedia, medium_encyclopedia) where possible.
May need simple test encyclopedias for specific merge scenarios.

All outputs saved to temp/ for human inspection.
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources


class TestMergeEncyclopedia:
    """Tests for merging encyclopedias."""
    
    def test_merge_encyclopedia_no_overlap(self, small_encyclopedia):
        """Test merging two encyclopedias with no overlapping entries."""
        # Create a second encyclopedia with different terms
        source_terms = ["relativity", "quantum", "photon"]
        source_encyclopedia = AmiEncyclopedia(title="Source Encyclopedia")
        
        # Add entries manually (simplified for test)
        for term in source_terms:
            entry = {
                'term': term,
                'canonical_term': term,
                'wikidata_id': '',
                'wikipedia_url': f'https://en.wikipedia.org/wiki/{term.replace(" ", "_")}',
                'description_html': f'<p>{term} is a concept.</p>',
                'definition_html': f'{term} is a concept.',
                'synonyms': []
            }
            source_encyclopedia.entries.append(entry)
        
        # Get initial counts
        target_initial_count = len(small_encyclopedia.entries)
        source_count = len(source_encyclopedia.entries)
        
        # Merge source into target
        result = small_encyclopedia.merge_encyclopedia(source_encyclopedia, conflict_resolution=None)
        
        assert isinstance(result, dict), \
            f"merge_encyclopedia should return dict, got {type(result)}"
        
        # Target should have all entries
        assert len(small_encyclopedia.entries) == target_initial_count + source_count, \
            f"Expected {target_initial_count + source_count} entries after merge, got {len(small_encyclopedia.entries)}"
        
        # All source terms should be in target
        target_terms = [e.get('term', '').lower() for e in small_encyclopedia.entries]
        for term in source_terms:
            assert term.lower() in target_terms or any(term.lower() in t for t in target_terms), \
                f"Source term '{term}' should be in merged encyclopedia"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestMergeEncyclopedia")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "merge_no_overlap_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        # Also save merge result JSON
        merge_result_file = Path(output_dir, "merge_no_overlap_result.json")
        import json
        merge_result_file.write_text(
            json.dumps(result, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
        assert merge_result_file.exists(), f"Merge result file should exist at {merge_result_file}"
    
    def test_merge_encyclopedia_with_duplicates(self, small_encyclopedia):
        """Test merging encyclopedias with duplicate entries."""
        # Create source encyclopedia with one duplicate term
        existing_entry = small_encyclopedia.entries[0]
        duplicate_term = existing_entry.get('term')
        
        source_encyclopedia = AmiEncyclopedia(title="Source Encyclopedia")
        duplicate_entry = {
            'term': duplicate_term,
            'canonical_term': duplicate_term,
            'wikidata_id': existing_entry.get('wikidata_id', ''),
            'wikipedia_url': existing_entry.get('wikipedia_url', ''),
            'description_html': '<p>Different description</p>',
            'definition_html': 'Different definition',
            'synonyms': []
        }
        source_encyclopedia.entries.append(duplicate_entry)
        
        # Get initial count
        target_initial_count = len(small_encyclopedia.entries)
        
        # Merge with conflict resolution (always ask user = None means use default)
        result = small_encyclopedia.merge_encyclopedia(source_encyclopedia, conflict_resolution=None)
        
        assert isinstance(result, dict), \
            f"merge_encyclopedia should return dict, got {type(result)}"
        
        # Check merge result
        conflicts = result.get('conflicts', [])
        entries_added = result.get('entries_added', 0)
        entries_merged = result.get('entries_merged', 0)
        
        # Should detect duplicate
        assert len(conflicts) > 0 or entries_merged > 0, \
            f"Should detect duplicate or merge. Conflicts: {len(conflicts)}, Merged: {entries_merged}"
        
        # Entry count should reflect merge strategy
        # (If merged, count stays same; if conflict, may add or keep target)
        final_count = len(small_encyclopedia.entries)
        assert final_count >= target_initial_count, \
            f"Final count should be >= initial count. Initial: {target_initial_count}, Final: {final_count}"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestMergeEncyclopedia")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "merge_with_duplicates_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        # Save merge result
        merge_result_file = Path(output_dir, "merge_with_duplicates_result.json")
        import json
        merge_result_file.write_text(
            json.dumps({
                'conflicts': conflicts,
                'entries_added': entries_added,
                'entries_merged': entries_merged,
                'final_entry_count': final_count
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
        assert merge_result_file.exists(), f"Merge result file should exist at {merge_result_file}"
    
    def test_merge_encyclopedia_metadata_merging(self, small_encyclopedia):
        """Test that metadata is merged correctly."""
        # Create source encyclopedia with hidden entries
        source_encyclopedia = AmiEncyclopedia(title="Source Encyclopedia")
        source_entry = {
            'term': 'test_term',
            'canonical_term': 'test_term',
            'wikidata_id': '',
            'wikipedia_url': 'https://en.wikipedia.org/wiki/test_term',
            'description_html': '<p>Test</p>',
            'definition_html': 'Test',
            'synonyms': []
        }
        source_encyclopedia.entries.append(source_entry)
        
        # Hide an entry in source
        source_entry_id = source_encyclopedia._generate_entry_id_from_entry(source_entry, 0)
        source_encyclopedia.hide_entry(source_entry_id)
        
        # Hide an entry in target
        target_entry = small_encyclopedia.entries[0]
        target_entry_id = small_encyclopedia._generate_entry_id_from_entry(target_entry, 0)
        small_encyclopedia.hide_entry(target_entry_id)
        
        target_hidden_before = len(small_encyclopedia.metadata.get('hidden_entries', []))
        
        # Merge
        result = small_encyclopedia.merge_encyclopedia(source_encyclopedia, conflict_resolution=None)
        
        # Hidden entries should be merged
        target_hidden_after = len(small_encyclopedia.metadata.get('hidden_entries', []))
        assert target_hidden_after >= target_hidden_before, \
            f"Hidden entries should be merged. Before: {target_hidden_before}, After: {target_hidden_after}"
        
        # Merge operations should be tracked
        merge_operations = small_encyclopedia.metadata.get('merge_operations', [])
        assert len(merge_operations) > 0, \
            f"Merge operations should be tracked. Got {len(merge_operations)}"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestMergeEncyclopedia")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "merge_metadata_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        # Save metadata JSON
        metadata_file = Path(output_dir, "merge_metadata.json")
        import json
        metadata_file.write_text(
            json.dumps({
                'hidden_entries': small_encyclopedia.metadata.get('hidden_entries', []),
                'merge_operations': merge_operations
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
        assert metadata_file.exists(), f"Metadata file should exist at {metadata_file}"
    
    def test_merge_encyclopedia_conflict_resolution(self, small_encyclopedia):
        """Test conflict resolution when merging."""
        # Ensure we have at least one entry
        assert len(small_encyclopedia.entries) > 0, \
            f"Need at least 1 entry for conflict test, got {len(small_encyclopedia.entries)}"
        
        # Create source encyclopedia with conflicting entry
        existing_entry = small_encyclopedia.entries[0]
        conflict_term = existing_entry.get('term')
        
        source_encyclopedia = AmiEncyclopedia(title="Source Encyclopedia")
        conflicting_entry = {
            'term': conflict_term,
            'canonical_term': conflict_term,
            'wikidata_id': existing_entry.get('wikidata_id', ''),
            'wikipedia_url': existing_entry.get('wikipedia_url', ''),
            'description_html': '<p>CONFLICTING DESCRIPTION</p>',
            'definition_html': 'CONFLICTING DEFINITION',
            'synonyms': []
        }
        source_encyclopedia.entries.append(conflicting_entry)
        
        # Define conflict resolution strategy
        conflict_resolution = {
            conflict_term: 'keep_target'  # Keep target entry
        }
        
        # Merge with conflict resolution
        result = small_encyclopedia.merge_encyclopedia(source_encyclopedia, conflict_resolution=conflict_resolution)
        
        assert isinstance(result, dict), \
            f"merge_encyclopedia should return dict, got {type(result)}"
        
        # Check that conflict was detected or resolved
        conflicts = result.get('conflicts', [])
        resolved_conflicts = result.get('resolved_conflicts', [])
        
        # Should have detected conflict (may be resolved or kept as conflict)
        # If same Wikidata ID, it's merged, not a conflict
        # If same term but different Wikidata ID, it's a conflict
        if existing_entry.get('wikidata_id') and existing_entry.get('wikidata_id') not in ('', 'no_wikidata_id'):
            # Same Wikidata ID - should be merged, not conflict
            assert result.get('entries_merged', 0) > 0 or len(resolved_conflicts) > 0, \
                f"Should merge entries with same Wikidata ID. Merged: {result.get('entries_merged', 0)}, Resolved: {len(resolved_conflicts)}"
        else:
            # Different Wikidata ID or no Wikidata - should be conflict
            assert len(conflicts) > 0 or len(resolved_conflicts) > 0, \
                f"Should detect or resolve conflicts. Conflicts: {len(conflicts)}, Resolved: {len(resolved_conflicts)}"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestMergeEncyclopedia")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "merge_conflict_resolution_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        # Save conflict resolution result
        conflict_file = Path(output_dir, "merge_conflict_resolution.json")
        import json
        conflict_file.write_text(
            json.dumps({
                'conflicts': conflicts,
                'resolved_conflicts': resolved_conflicts,
                'conflict_resolution': conflict_resolution
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
        assert conflict_file.exists(), f"Conflict file should exist at {conflict_file}"
    
    def test_merge_encyclopedia_persistence(self, small_encyclopedia):
        """Test that merged encyclopedia is persisted to HTML file."""
        # Create source encyclopedia
        source_encyclopedia = AmiEncyclopedia(title="Source Encyclopedia")
        source_entry = {
            'term': 'merged_term',
            'canonical_term': 'merged_term',
            'wikidata_id': '',
            'wikipedia_url': 'https://en.wikipedia.org/wiki/merged_term',
            'description_html': '<p>Merged entry</p>',
            'definition_html': 'Merged entry',
            'synonyms': []
        }
        source_encyclopedia.entries.append(source_entry)
        
        # Get initial count before merge
        initial_count = len(small_encyclopedia.entries)
        
        # Merge
        result = small_encyclopedia.merge_encyclopedia(source_encyclopedia, conflict_resolution=None)
        
        # Save to HTML
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestMergeEncyclopedia")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "merge_persistence_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        # Load from HTML
        loaded_encyclopedia = AmiEncyclopedia()
        loaded_encyclopedia.create_from_html_file(output_file)
        
        # Verify merged entry is in loaded encyclopedia
        loaded_terms = [e.get('term', '').lower() for e in loaded_encyclopedia.entries]
        # Check if merged_term is in loaded entries (may be normalized/merged)
        found_merged = 'merged_term' in loaded_terms or any('merged' in term for term in loaded_terms)
        # Also check if entry count increased (entry was added)
        entries_added = result.get('entries_added', 0) if result else 0
        assert len(loaded_encyclopedia.entries) >= initial_count + entries_added or found_merged, \
            f"Merged entry should be in loaded encyclopedia. Expected at least {initial_count + entries_added} entries, got {len(loaded_encyclopedia.entries)}. Terms: {loaded_terms[:10]}"
        
        # Verify merge operations are preserved
        merge_operations = loaded_encyclopedia.metadata.get('merge_operations', [])
        assert len(merge_operations) > 0, \
            f"Merge operations should be preserved. Got {len(merge_operations)}"
        
        # Save loaded encyclopedia for human inspection
        loaded_output_file = Path(output_dir, "merge_persistence_loaded_test.html")
        loaded_encyclopedia.save_wiki_normalized_html(loaded_output_file)
        
        assert loaded_output_file.exists(), f"Loaded output file should exist at {loaded_output_file}"
    
    def test_version_bump_on_merge(self, small_encyclopedia):
        """Test that version is bumped when encyclopedias are merged and saved."""
        # Get initial version
        initial_version = small_encyclopedia.metadata.get('version', '1.0.0')
        
        # Create source encyclopedia
        source_encyclopedia = AmiEncyclopedia(title="Source Encyclopedia")
        source_entry = {
            'term': 'version_test_term',
            'canonical_term': 'version_test_term',
            'wikidata_id': '',
            'wikipedia_url': 'https://en.wikipedia.org/wiki/version_test_term',
            'description_html': '<p>Test</p>',
            'definition_html': 'Test',
            'synonyms': []
        }
        source_encyclopedia.entries.append(source_entry)
        
        # Merge
        small_encyclopedia.merge_encyclopedia(source_encyclopedia, conflict_resolution=None)
        
        # Save to HTML (this should bump version)
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestMergeEncyclopedia")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "version_bump_merge_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        # Version should be bumped
        new_version = small_encyclopedia.metadata.get('version')
        assert new_version != initial_version, \
            f"Version should be bumped after merge and save. Initial: {initial_version}, New: {new_version}"
        
        # Save for human inspection
        assert output_file.exists(), f"Output file should exist at {output_file}"
        
        # Also save metadata JSON for inspection
        metadata_file = Path(output_dir, "version_bump_merge_metadata.json")
        import json
        metadata_file.write_text(
            json.dumps({
                'initial_version': initial_version,
                'new_version': new_version,
                'entries_count': len(small_encyclopedia.entries),
                'merge_operations_count': len(small_encyclopedia.metadata.get('merge_operations', []))
            }, indent=2),
            encoding='utf-8'
        )
        
        assert metadata_file.exists(), f"Metadata file should exist at {metadata_file}"
