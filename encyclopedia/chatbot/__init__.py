# Chatbot package: RAG over climate encyclopedia.
# Non-empty by agreement: re-exports for API.

from encyclopedia.chatbot.corpus import entries_to_sections, load_entries_from_encyclopedia
from encyclopedia.chatbot.chunker import chunk_sections
from encyclopedia.chatbot.retrieval import InMemoryRetriever, VectorRetriever
from encyclopedia.chatbot.guardrails import check_scope_refuse
from encyclopedia.chatbot.prompt import build_prompt
from encyclopedia.chatbot.pipeline import answer_question
from encyclopedia.chatbot.llm import make_ollama_generator, make_openai_generator

__all__ = [
    "entries_to_sections",
    "load_entries_from_encyclopedia",
    "chunk_sections",
    "InMemoryRetriever",
    "VectorRetriever",
    "check_scope_refuse",
    "build_prompt",
    "answer_question",
    "make_ollama_generator",
    "make_openai_generator",
]
