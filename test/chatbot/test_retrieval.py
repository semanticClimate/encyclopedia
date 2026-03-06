"""
TDD: Retriever interface and InMemoryRetriever behaviour.
"""

import pytest

from encyclopedia.chatbot.retrieval import InMemoryRetriever


class TestInMemoryRetriever:
    """Contract: retriever.search(query, k) returns list of (chunk, score)."""

    def test_search_returns_list_of_tuples(self, sample_chunks):
        """search() returns list of (chunk_dict, score_float)."""
        retriever = InMemoryRetriever(sample_chunks)
        result = retriever.search("climate change", k=5)
        assert isinstance(result, list), "search must return a list"
        for item in result:
            assert isinstance(item, tuple), f"Each item must be (chunk, score), got {type(item)}"
            assert len(item) == 2, f"Each item must be (chunk, score), got len {len(item)}"
            ch, score = item
            assert isinstance(ch, dict), f"Chunk must be dict, got {type(ch)}"
            assert isinstance(score, (int, float)), f"Score must be numeric, got {type(score)}"

    def test_scores_in_zero_one(self, sample_chunks):
        """Scores are in [0, 1]."""
        retriever = InMemoryRetriever(sample_chunks)
        result = retriever.search("climate", k=10)
        for ch, score in result:
            assert 0 <= score <= 1, f"Score must be in [0,1], got {score}"

    def test_respects_k(self, sample_chunks):
        """At most k results returned."""
        retriever = InMemoryRetriever(sample_chunks)
        result = retriever.search("climate gas", k=2)
        assert len(result) <= 2, f"Expected at most 2 results, got {len(result)}"

    def test_empty_query_returns_empty(self, sample_chunks):
        """Empty query returns empty list."""
        retriever = InMemoryRetriever(sample_chunks)
        result = retriever.search("", k=5)
        assert result == [], f"Empty query must return empty list, got {result}"

    def test_empty_chunks_returns_empty(self):
        """Retriever with no chunks returns empty for any query."""
        retriever = InMemoryRetriever([])
        result = retriever.search("climate", k=5)
        assert result == [], f"Empty chunks must yield empty search, got {result}"

    def test_relevant_query_scores_higher(self, sample_chunks):
        """Query matching chunk content yields higher score than unrelated query."""
        retriever = InMemoryRetriever(sample_chunks)
        relevant = retriever.search("climate change", k=1)
        irrelevant = retriever.search("xyznonexistent", k=1)
        assert len(relevant) >= 1 and len(irrelevant) >= 1
        assert relevant[0][1] >= irrelevant[0][1], (
            f"Relevant query score {relevant[0][1]} should be >= irrelevant {irrelevant[0][1]}"
        )
