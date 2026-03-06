"""
Tests for VectorRetriever (sentence-transformers + ChromaDB).
Skip if optional deps not installed: pip install encyclopedia[chatbot]
"""

import pytest

# Skip entire module if optional deps missing
pytest.importorskip("sentence_transformers")
pytest.importorskip("chromadb")

from encyclopedia.chatbot.retrieval import VectorRetriever


class TestVectorRetriever:
    """VectorRetriever contract: same as InMemoryRetriever.search(query, k) -> [(chunk, score)]."""

    def test_search_returns_list_of_tuples(self, sample_chunks):
        """search() returns list of (chunk_dict, score_float)."""
        retriever = VectorRetriever(sample_chunks, persist_directory=None)
        result = retriever.search("climate change", k=5)
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, tuple) and len(item) == 2
            ch, score = item
            assert isinstance(ch, dict)
            assert isinstance(score, (int, float))

    def test_scores_in_zero_one(self, sample_chunks):
        """Scores are in [0, 1] (similarity)."""
        retriever = VectorRetriever(sample_chunks, persist_directory=None)
        result = retriever.search("climate", k=10)
        for _ch, score in result:
            assert 0 <= score <= 1, f"Score must be in [0,1], got {score}"

    def test_respects_k(self, sample_chunks):
        """At most k results returned."""
        retriever = VectorRetriever(sample_chunks, persist_directory=None)
        result = retriever.search("climate gas", k=2)
        assert len(result) <= 2

    def test_empty_query_returns_empty(self, sample_chunks):
        """Empty query returns empty list."""
        retriever = VectorRetriever(sample_chunks, persist_directory=None)
        result = retriever.search("", k=5)
        assert result == []

    def test_chunk_has_section_label_text_entry_id_term(self, sample_chunks):
        """Returned chunks have required keys for pipeline."""
        retriever = VectorRetriever(sample_chunks, persist_directory=None)
        result = retriever.search("climate", k=1)
        if result:
            ch, _ = result[0]
            assert "section_label" in ch and "text" in ch and "entry_id" in ch and "term" in ch
