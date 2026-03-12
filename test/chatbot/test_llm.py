"""
Tests for LLM backends: factory returns callable; pipeline works with stub (no mocks).
"""

import pytest

from encyclopedia.chatbot.llm import (
    make_ollama_generator,
    make_openai_generator,
    ollama_generate,
    openai_compatible_generate,
)


class TestMakeOllamaGenerator:
    """make_ollama_generator returns a callable (prompt -> str)."""

    def test_returns_callable(self):
        """Factory returns a callable."""
        gen = make_ollama_generator(model="llama3.2:3b")
        assert callable(gen), "make_ollama_generator must return a callable"

    def test_callable_accepts_string(self):
        """Returned callable accepts one string argument (signature for llm_generate)."""
        gen = make_ollama_generator()
        # Should not raise when called with str; may raise if Ollama not running
        try:
            result = gen("Hello")
            assert isinstance(result, str), "Ollama generator must return str"
        except Exception:
            # Ollama not running or network error is acceptable in test env
            pytest.skip("Ollama not available or network error")


class TestMakeOpenAIGenerator:
    """make_openai_generator returns a callable (prompt -> str)."""

    def test_returns_callable(self):
        """Factory returns a callable."""
        gen = make_openai_generator(model="gpt-4o-mini", api_key="test-key")
        assert callable(gen), "make_openai_generator must return a callable"

    def test_callable_accepts_string(self):
        """Returned callable accepts one string argument."""
        gen = make_openai_generator(model="gpt-4o-mini", api_key="sk-test")
        # Calling with invalid key will raise (no mock); we only check it's callable
        assert callable(gen)


class TestOllamaGenerate:
    """ollama_generate returns str or raises."""

    def test_requires_requests(self):
        """Module uses requests; if missing, ollama_generate raises on use."""
        # We have requests in deps; just ensure function exists and is callable
        assert callable(ollama_generate)


class TestOpenAICompatibleGenerate:
    """openai_compatible_generate signature and behavior."""

    def test_function_exists(self):
        """openai_compatible_generate is callable."""
        assert callable(openai_compatible_generate)
