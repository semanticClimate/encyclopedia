"""
Fixtures for chatbot tests: sample entries and chunks (no network, no mocks).
"""

import pytest

from encyclopedia.chatbot.corpus import entries_to_sections
from encyclopedia.chatbot.chunker import chunk_sections


@pytest.fixture
def sample_entries():
    """Minimal list of entry dicts with labelled content for tests."""
    return [
        {
            "term": "climate change",
            "description_html": "<p>Climate change refers to long-term shifts in temperatures and weather patterns.</p>",
            "definition_html": "<p>A change in global or regional climate patterns.</p>",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Climate_change",
            "wikidata_id": "Q7942",
        },
        {
            "term": "greenhouse gas",
            "description_html": "<p>Greenhouse gases trap heat in the atmosphere.</p>",
            "definition_html": "",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Greenhouse_gas",
            "wikidata_id": "Q131784",
        },
        {
            "term": "carbon dioxide",
            "description_html": "",
            "definition_html": "<p>CO2 is a greenhouse gas.</p>",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Carbon_dioxide",
            "wikidata_id": "Q1218",
        },
    ]


@pytest.fixture
def sample_sections(sample_entries):
    """Sections derived from sample_entries."""
    return entries_to_sections(sample_entries)


@pytest.fixture
def sample_chunks(sample_sections):
    """Chunks derived from sample_sections."""
    return chunk_sections(sample_sections)
