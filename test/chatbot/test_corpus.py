"""
TDD: Corpus loading and section extraction.

Tests define the contract for load_entries_from_encyclopedia and entries_to_sections.
"""

import pytest
from pathlib import Path

from encyclopedia.chatbot.corpus import (
    load_entries_from_encyclopedia,
    entries_to_sections,
)
from encyclopedia.core.encyclopedia import AmiEncyclopedia


class TestLoadEntriesFromEncyclopedia:
    """Contract: load_entries_from_encyclopedia returns list of entry dicts."""

    def test_accepts_path_returns_list(self, sample_entries):
        """When given an in-memory encyclopedia, returns list of entries."""
        enc = AmiEncyclopedia(title="Test")
        enc.entries = sample_entries
        result = load_entries_from_encyclopedia(enc)
        assert isinstance(result, list), "load_entries_from_encyclopedia must return a list"
        assert len(result) == 3, f"Expected 3 entries, got {len(result)}"

    def test_entries_have_term_or_search_term(self, sample_entries):
        """Each entry has at least term or search_term for section labelling."""
        enc = AmiEncyclopedia(title="Test")
        enc.entries = sample_entries
        result = load_entries_from_encyclopedia(enc)
        for i, entry in enumerate(result):
            has_term = "term" in entry or "search_term" in entry
            assert has_term, f"Entry {i} must have 'term' or 'search_term': {list(entry.keys())}"

    def test_accepts_html_path_when_file_exists(self):
        """When given a path to existing encyclopedia HTML, returns entries."""
        cache_dir = Path(Path(__file__).resolve().parent.parent, "encyclopedia", "fixtures", "cache")
        html_files = list(cache_dir.glob("encyclopedia_*.html")) if cache_dir.exists() else []
        if not html_files:
            pytest.skip("No fixture cache found; run encyclopedia tests first")
        first = html_files[0]
        result = load_entries_from_encyclopedia(first)
        assert isinstance(result, list), "Must return list"
        assert len(result) >= 1, f"Expected at least 1 entry from {first}, got {len(result)}"


class TestEntriesToSections:
    """Contract: entries_to_sections returns flat list of sections with labels."""

    def test_returns_list_of_sections(self, sample_entries):
        """Sections are dicts with section_label, text, entry_id, term."""
        sections = entries_to_sections(sample_entries)
        assert isinstance(sections, list), "entries_to_sections must return a list"
        assert len(sections) >= 3, f"Expected at least 3 sections from 3 entries, got {len(sections)}"

    def test_each_section_has_required_keys(self, sample_entries):
        """Every section has section_label, text, entry_id, term (or empty string)."""
        sections = entries_to_sections(sample_entries)
        for i, s in enumerate(sections):
            assert "section_label" in s, f"Section {i} missing section_label: {s.keys()}"
            assert "text" in s, f"Section {i} missing text: {s.keys()}"
            assert "entry_id" in s, f"Section {i} missing entry_id: {s.keys()}"
            assert "term" in s, f"Section {i} missing term: {s.keys()}"

    def test_section_labels_are_term_description_or_definition(self, sample_entries):
        """Section labels come from entry structure (term, description, definition)."""
        sections = entries_to_sections(sample_entries)
        labels = {s["section_label"] for s in sections}
        assert "term" in labels or "description" in labels or "definition" in labels, (
            f"Expected at least one of term/description/definition in labels, got {labels}"
        )

    def test_text_is_plain_not_html(self, sample_entries):
        """Section text must be plain text (no HTML tags)."""
        sections = entries_to_sections(sample_entries)
        for s in sections:
            text = s.get("text", "")
            assert "<" not in text or ">" not in text, (
                f"Section text should be plain; found HTML in: {text[:100]}"
            )
