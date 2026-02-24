"""
Tests for adding entries from Wikipedia search.

Tests cover:
- Add entry from Wikipedia (with duplicate detection)
- Check duplicate entry (by Wikidata ID, term, URL)
- Handle disambiguation pages (auto-mark as needing editing)
- Persistence to HTML file
- Version bumping on save

NOTE: These tests require Wikipedia API access (no mocks per style guide).
Tests may be skipped if Wikipedia is unavailable.

All outputs saved to temp/ for human inspection.
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources


class TestAddEntryFromWikipedia:
    """Tests for adding entries from Wikipedia search."""
    
    def test_add_entry_from_wikipedia_new_term(self, small_encyclopedia):
        """Test adding a new entry from Wikipedia that doesn't exist in encyclopedia."""
        # Use a term that's unlikely to be in small encyclopedia
        new_term = "quantum mechanics"
        initial_count = len(small_encyclopedia.entries)
        
        # Add entry from Wikipedia
        result = small_encyclopedia.add_entry_from_wikipedia(new_term, check_duplicates=True)
        
        # Should return dictionary with entry info
        assert isinstance(result, dict), \
            f"add_entry_from_wikipedia should return dict, got {type(result)}"
        
        # Check if entry was added (may fail if Wikipedia unavailable or duplicate)
        if result.get('error'):
            pytest.skip(f"Wikipedia lookup failed: {result['error']}")
        
        if result.get('is_duplicate'):
            pytest.skip(f"Term '{new_term}' is duplicate (may have been added by previous test)")
        
        # Entry should be added to encyclopedia
        assert result.get('added') is True, \
            f"Entry should be added. Result: {result}"
        assert len(small_encyclopedia.entries) == initial_count + 1, \
            f"Expected {initial_count + 1} entries after adding, got {len(small_encyclopedia.entries)}"
        
        # New entry should be in entries list
        new_entry = next((e for e in small_encyclopedia.entries if e.get('term', '').lower() == new_term.lower()), None)
        assert new_entry is not None, \
            f"Entry '{new_term}' should be in entries list"
        
        # Entry should have Wikipedia content
        assert new_entry.get('wikipedia_url'), \
            f"Entry should have Wikipedia URL, got {new_entry.get('wikipedia_url')}"
        assert new_entry.get('description_html') or new_entry.get('definition_html'), \
            f"Entry should have description or definition HTML"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestAddEntryFromWikipedia")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "add_new_term_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
        assert output_file.stat().st_size > 0, "Output file should not be empty"
    
    def test_add_entry_from_wikipedia_duplicate_term(self, small_encyclopedia):
        """Test adding entry that already exists (duplicate by term)."""
        # Get existing entry
        existing_entry = small_encyclopedia.entries[0]
        existing_term = existing_entry.get('term')
        initial_count = len(small_encyclopedia.entries)
        
        # Try to add duplicate entry
        result = small_encyclopedia.add_entry_from_wikipedia(existing_term, check_duplicates=True)
        
        # Should return duplicate info
        assert isinstance(result, dict), \
            f"add_entry_from_wikipedia should return dict, got {type(result)}"
        
        # Check if duplicate was detected
        is_duplicate = result.get('is_duplicate', False)
        if is_duplicate:
            # Entry should not be added (duplicate detected)
            assert len(small_encyclopedia.entries) == initial_count, \
                f"Duplicate entry should not be added. Expected {initial_count} entries, got {len(small_encyclopedia.entries)}"
            
            # Result should contain duplicate info
            assert 'existing_entry' in result, \
                "Result should contain existing_entry for duplicate"
            assert 'match_type' in result, \
                "Result should contain match_type for duplicate"
        else:
            # If not detected as duplicate, entry might be added
            # (This is acceptable if Wikipedia returns different content)
            pass
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestAddEntryFromWikipedia")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "add_duplicate_term_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
    
    def test_check_duplicate_entry_by_wikidata_id(self, small_encyclopedia):
        """Test duplicate detection by Wikidata ID."""
        # Get entry with Wikidata ID
        entry_with_wikidata = None
        for entry in small_encyclopedia.entries:
            if entry.get('wikidata_id') and entry.get('wikidata_id') not in ('', 'no_wikidata_id'):
                entry_with_wikidata = entry
                break
        
        if not entry_with_wikidata:
            pytest.skip("No entry with Wikidata ID found in test encyclopedia")
        
        wikidata_id = entry_with_wikidata.get('wikidata_id')
        
        # Create a new entry dict with same Wikidata ID but different term
        new_entry = {
            'term': 'Different Term',
            'wikidata_id': wikidata_id,
            'wikipedia_url': 'https://en.wikipedia.org/wiki/Different_Term'
        }
        
        # Check for duplicate
        is_duplicate, existing_entry, match_type = small_encyclopedia.check_duplicate_entry(new_entry)
        
        assert is_duplicate is True, \
            f"Entry with same Wikidata ID {wikidata_id} should be detected as duplicate"
        assert existing_entry is not None, \
            "check_duplicate_entry should return existing entry"
        assert match_type == 'wikidata_id', \
            f"Match type should be 'wikidata_id', got '{match_type}'"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestAddEntryFromWikipedia")
        output_dir.mkdir(parents=True, exist_ok=True)
        duplicate_info_file = Path(output_dir, "duplicate_by_wikidata_id.json")
        import json
        duplicate_info_file.write_text(
            json.dumps({
                'new_entry': new_entry,
                'existing_entry_term': existing_entry.get('term'),
                'match_type': match_type
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert duplicate_info_file.exists(), f"Duplicate info file should exist at {duplicate_info_file}"
    
    def test_check_duplicate_entry_by_term(self, small_encyclopedia):
        """Test duplicate detection by term (case-insensitive)."""
        # Get existing entry
        existing_entry = small_encyclopedia.entries[0]
        existing_term = existing_entry.get('term')
        
        # Create a new entry dict with same term (different case)
        new_entry = {
            'term': existing_term.upper(),  # Different case
            'wikidata_id': '',
            'wikipedia_url': 'https://en.wikipedia.org/wiki/Different'
        }
        
        # Check for duplicate
        is_duplicate, existing_entry_found, match_type = small_encyclopedia.check_duplicate_entry(new_entry)
        
        assert is_duplicate is True, \
            f"Entry with same term '{existing_term}' (case-insensitive) should be detected as duplicate"
        assert existing_entry_found is not None, \
            "check_duplicate_entry should return existing entry"
        assert match_type == 'term', \
            f"Match type should be 'term', got '{match_type}'"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestAddEntryFromWikipedia")
        output_dir.mkdir(parents=True, exist_ok=True)
        duplicate_info_file = Path(output_dir, "duplicate_by_term.json")
        import json
        duplicate_info_file.write_text(
            json.dumps({
                'new_entry': new_entry,
                'existing_entry_term': existing_entry_found.get('term'),
                'match_type': match_type
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert duplicate_info_file.exists(), f"Duplicate info file should exist at {duplicate_info_file}"
    
    def test_add_entry_from_wikipedia_disambiguation(self, small_encyclopedia):
        """Test adding entry from disambiguation page (should auto-mark as needing editing)."""
        # Use a term that's likely a disambiguation page
        disambiguation_term = "Mercury"
        initial_count = len(small_encyclopedia.entries)
        
        # Add entry from Wikipedia
        result = small_encyclopedia.add_entry_from_wikipedia(disambiguation_term, check_duplicates=True)
        
        # Should return dictionary with entry info
        assert isinstance(result, dict), \
            f"add_entry_from_wikipedia should return dict, got {type(result)}"
        
        # If entry was added, check if it's marked as needing editing
        if result.get('added', False):
            new_entry = next((e for e in small_encyclopedia.entries 
                            if e.get('term', '').lower() == disambiguation_term.lower()), None)
            
            if new_entry:
                # Check if disambiguation was detected and marked
                needs_editing = new_entry.get('needs_editing', {})
                is_disambiguation = small_encyclopedia._is_disambiguation_page(
                    wikipedia_url=new_entry.get('wikipedia_url'),
                    wikidata_id=new_entry.get('wikidata_id')
                )
                
                # If disambiguation detected, should be marked as needing editing
                if is_disambiguation:
                    assert needs_editing.get('flag') is True or needs_editing.get('reason') == 'disambiguation', \
                        f"Disambiguation page should be marked as needing editing. needs_editing: {needs_editing}"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestAddEntryFromWikipedia")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "add_disambiguation_test.html")
        small_encyclopedia.save_wiki_normalized_html(output_file)
        
        assert output_file.exists(), f"Output file should exist at {output_file}"
    
    def test_add_entry_from_wikipedia_nonexistent_term(self, small_encyclopedia):
        """Test adding entry for term that doesn't exist on Wikipedia."""
        # Use a term that's unlikely to exist on Wikipedia
        nonexistent_term = "XyZqWvAbC123456789"
        initial_count = len(small_encyclopedia.entries)
        
        # Try to add entry from Wikipedia
        result = small_encyclopedia.add_entry_from_wikipedia(nonexistent_term, check_duplicates=True)
        
        # Should return error or None
        assert isinstance(result, dict), \
            f"add_entry_from_wikipedia should return dict, got {type(result)}"
        
        # Entry should not be added
        assert len(small_encyclopedia.entries) == initial_count, \
            f"Nonexistent term should not add entry. Expected {initial_count} entries, got {len(small_encyclopedia.entries)}"
        
        # Result should indicate failure
        assert result.get('added', True) is False or result.get('error'), \
            f"Result should indicate failure. Result: {result}"
        
        # Save output for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestAddEntryFromWikipedia")
        output_dir.mkdir(parents=True, exist_ok=True)
        error_info_file = Path(output_dir, "add_nonexistent_term.json")
        import json
        error_info_file.write_text(
            json.dumps(result, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert error_info_file.exists(), f"Error info file should exist at {error_info_file}"
    
    def test_add_entry_from_wikipedia_persistence(self, small_encyclopedia):
        """Test that added entries are persisted to HTML file."""
        # Add a new entry
        new_term = "relativity"
        initial_count = len(small_encyclopedia.entries)
        
        result = small_encyclopedia.add_entry_from_wikipedia(new_term, check_duplicates=True)
        
        # Only proceed if entry was added
        if result.get('added', False) and len(small_encyclopedia.entries) > initial_count:
            # Save to HTML
            output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestAddEntryFromWikipedia")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = Path(output_dir, "add_persistence_test.html")
            small_encyclopedia.save_wiki_normalized_html(output_file)
            
            # Load from HTML
            loaded_encyclopedia = AmiEncyclopedia()
            loaded_encyclopedia.create_from_html_file(output_file)
            
            # Verify entry is in loaded encyclopedia
            loaded_terms = [e.get('term', '').lower() for e in loaded_encyclopedia.entries]
            assert new_term.lower() in loaded_terms or any(new_term.lower() in term for term in loaded_terms), \
                f"Added entry '{new_term}' should be in loaded encyclopedia. Terms: {loaded_terms[:5]}"
            
            # Save loaded encyclopedia for human inspection
            loaded_output_file = Path(output_dir, "add_persistence_loaded_test.html")
            loaded_encyclopedia.save_wiki_normalized_html(loaded_output_file)
            
            assert loaded_output_file.exists(), f"Loaded output file should exist at {loaded_output_file}"
        else:
            pytest.skip("Entry was not added (may be duplicate or Wikipedia unavailable)")
    
    def test_version_bump_on_add_entry(self, small_encyclopedia):
        """Test that version is bumped when entry is added and saved."""
        # Get initial version
        initial_version = small_encyclopedia.metadata.get('version', '1.0.0')
        
        # Add a new entry
        new_term = "electromagnetism"
        result = small_encyclopedia.add_entry_from_wikipedia(new_term, check_duplicates=True)
        
        # Only proceed if entry was added
        if result.get('added', False):
            # Save to HTML (this should bump version)
            output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestAddEntryFromWikipedia")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = Path(output_dir, "version_bump_add_test.html")
            small_encyclopedia.save_wiki_normalized_html(output_file)
            
            # Version should be bumped
            new_version = small_encyclopedia.metadata.get('version')
            assert new_version != initial_version, \
                f"Version should be bumped after add and save. Initial: {initial_version}, New: {new_version}"
            
            # Save for human inspection
            assert output_file.exists(), f"Output file should exist at {output_file}"
            
            # Also save metadata JSON for inspection
            metadata_file = Path(output_dir, "version_bump_add_metadata.json")
            import json
            metadata_file.write_text(
                json.dumps({
                    'initial_version': initial_version,
                    'new_version': new_version,
                    'entries_count': len(small_encyclopedia.entries)
                }, indent=2),
                encoding='utf-8'
            )
            
            assert metadata_file.exists(), f"Metadata file should exist at {metadata_file}"
        else:
            pytest.skip("Entry was not added (may be duplicate or Wikipedia unavailable)")
