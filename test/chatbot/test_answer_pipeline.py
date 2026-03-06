"""
TDD: Answer pipeline — question -> retrieve -> guardrail -> prompt -> LLM -> response.
"""

import pytest

from encyclopedia.chatbot.pipeline import answer_question
from encyclopedia.chatbot.retrieval import InMemoryRetriever
from encyclopedia.chatbot.guardrails import REFUSAL_MESSAGE


def _stub_llm(prompt: str) -> str:
    """Real stub: returns fixed string for tests (no mock)."""
    return "According to the encyclopedia, climate change refers to long-term shifts in temperatures."


class TestAnswerQuestion:
    """Contract: answer_question returns dict with answer, refused, citations."""

    def test_returns_dict_with_answer_refused_citations(self, sample_chunks):
        """Return value has keys answer, refused, citations."""
        retriever = InMemoryRetriever(sample_chunks)
        result = answer_question("What is climate change?", retriever, llm_generate=_stub_llm)
        assert isinstance(result, dict), "answer_question must return a dict"
        assert "answer" in result, "Result must have 'answer' key"
        assert "refused" in result, "Result must have 'refused' key"
        assert "citations" in result, "Result must have 'citations' key"

    def test_refused_when_retrieval_empty(self):
        """When retriever returns no results, refused is True and answer is refusal message."""
        retriever = InMemoryRetriever([])
        result = answer_question("anything", retriever, llm_generate=_stub_llm)
        assert result["refused"] is True, "Empty retrieval must set refused=True"
        assert REFUSAL_MESSAGE in (result.get("answer") or ""), (
            f"Refusal answer must contain REFUSAL_MESSAGE, got {result.get('answer')}"
        )
        assert result.get("citations") == [], "Refused response must have empty citations"

    def test_refused_when_score_below_threshold(self, sample_chunks):
        """When best score is below min_score, refuse."""
        retriever = InMemoryRetriever(sample_chunks)
        # Query that doesn't match any chunk well
        result = answer_question("xyznonexistentword", retriever, min_score=0.99, llm_generate=_stub_llm)
        assert result["refused"] is True, "Low score must trigger refuse"

    def test_not_refused_when_relevant_result(self, sample_chunks):
        """When retrieval has relevant result, refused is False and answer from LLM."""
        retriever = InMemoryRetriever(sample_chunks)
        result = answer_question("What is climate change?", retriever, llm_generate=_stub_llm)
        assert result["refused"] is False, "Relevant query must not refuse"
        assert len((result.get("answer") or "")) > 0, "Answer must be non-empty"
        assert "According to the encyclopedia" in (result.get("answer") or ""), (
            "Answer must come from stub LLM when provided"
        )

    def test_citations_populated_when_not_refused(self, sample_chunks):
        """When not refused, citations list contains retrieved chunks."""
        retriever = InMemoryRetriever(sample_chunks)
        result = answer_question("climate change", retriever, llm_generate=_stub_llm)
        assert result["refused"] is False
        assert len(result.get("citations", [])) >= 1, (
            "Citations must contain at least one chunk when not refused"
        )

    def test_no_llm_returns_placeholder_when_not_refused(self, sample_chunks):
        """When llm_generate is None, answer is placeholder (implementation detail)."""
        retriever = InMemoryRetriever(sample_chunks)
        result = answer_question("climate", retriever, llm_generate=None)
        assert result["refused"] is False
        assert "No LLM configured" in (result.get("answer") or ""), (
            "Without LLM, answer should indicate no LLM configured"
        )
