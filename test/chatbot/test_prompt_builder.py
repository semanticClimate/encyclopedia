"""
TDD: Prompt builder includes system, chunks with labels, and question.
"""

import pytest

from encyclopedia.chatbot.prompt import build_prompt


class TestBuildPrompt:
    """Contract: build_prompt(chunks, question, system_prompt) -> str."""

    def test_returns_string(self, sample_chunks):
        """build_prompt returns a single string."""
        result = build_prompt(sample_chunks[:2], "What is climate change?")
        assert isinstance(result, str), "build_prompt must return str"

    def test_contains_question(self, sample_chunks):
        """Prompt must contain the user question."""
        question = "What is climate change?"
        result = build_prompt(sample_chunks[:1], question)
        assert question in result, f"Prompt must contain question '{question}'"

    def test_contains_chunk_text_or_term(self, sample_chunks):
        """Prompt must include content from chunks (term or text)."""
        result = build_prompt(sample_chunks, "What is climate?")
        has_chunk_content = any(
            (c.get("term") or "") in result or (c.get("text") or "")[:50] in result
            for c in sample_chunks
        )
        assert has_chunk_content, "Prompt must include chunk content for context"

    def test_system_prompt_included_when_provided(self, sample_chunks):
        """When system_prompt is non-empty, it appears in the output."""
        system = "Answer only from the encyclopedia."
        result = build_prompt(sample_chunks[:1], "What is CO2?", system_prompt=system)
        assert system in result, f"System prompt must appear in output: {result[:200]}"

    def test_empty_chunks_still_includes_question(self):
        """With no chunks, prompt still contains question."""
        result = build_prompt([], "What is climate?")
        assert "What is climate?" in result, "Question must appear even with no chunks"
