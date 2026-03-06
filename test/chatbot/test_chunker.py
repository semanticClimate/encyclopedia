"""
TDD: Chunker produces chunks with section_label, text, entry_id, term.
"""

import pytest

from encyclopedia.chatbot.chunker import chunk_sections


class TestChunkSections:
    """Contract: chunk_sections returns list of chunk dicts."""

    def test_returns_list(self, sample_sections):
        """chunk_sections returns a list."""
        result = chunk_sections(sample_sections)
        assert isinstance(result, list), "chunk_sections must return a list"

    def test_chunk_count_at_most_section_count(self, sample_sections):
        """Number of chunks is at most number of sections (empty text skipped)."""
        result = chunk_sections(sample_sections)
        assert len(result) <= len(sample_sections), (
            f"Chunks {len(result)} should be <= sections {len(sample_sections)}"
        )

    def test_each_chunk_has_section_label_text_entry_id_term(self, sample_chunks):
        """Every chunk has section_label, text, entry_id, term."""
        for i, ch in enumerate(sample_chunks):
            assert "section_label" in ch, f"Chunk {i} missing section_label"
            assert "text" in ch, f"Chunk {i} missing text"
            assert "entry_id" in ch, f"Chunk {i} missing entry_id"
            assert "term" in ch, f"Chunk {i} missing term"

    def test_chunk_text_is_non_empty(self, sample_chunks):
        """Chunk text must be non-empty."""
        for i, ch in enumerate(sample_chunks):
            assert (ch.get("text") or "").strip(), (
                f"Chunk {i} has empty text: {ch}"
            )

    def test_empty_sections_yields_empty_chunks(self):
        """Empty section list yields empty chunk list."""
        result = chunk_sections([])
        assert result == [], "Empty sections must yield empty chunks"

    def test_sections_with_empty_text_skipped(self):
        """Sections with no text are not emitted as chunks."""
        sections = [
            {"section_label": "description", "text": "  ", "entry_id": "e1", "term": "x"},
            {"section_label": "definition", "text": "real content", "entry_id": "e1", "term": "x"},
        ]
        result = chunk_sections(sections)
        assert len(result) == 1, f"Expected 1 chunk (empty text skipped), got {len(result)}"
        assert result[0]["text"] == "real content", f"Expected chunk text 'real content', got {result[0]}"
