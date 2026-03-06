#!/usr/bin/env python3
"""
Example: real embeddings and vector search over a climate encyclopedia.

Loads an encyclopedia, builds sections and chunks, then:
1. InMemoryRetriever (keyword) — no extra deps
2. VectorRetriever (sentence-transformers + ChromaDB) — pip install encyclopedia[chatbot]

Usage (from repo root):
  python Examples/chatbot_embedding_example.py

Optional: set CHATBOT_ENCYCLOPEDIA to path to an HTML encyclopedia; otherwise
uses the first available fixture cache or creates a tiny in-memory corpus.
"""

from pathlib import Path
import os

# Project root
ROOT = Path(Path(__file__).resolve().parent.parent)

from encyclopedia.chatbot.corpus import load_entries_from_encyclopedia, entries_to_sections
from encyclopedia.chatbot.chunker import chunk_sections
from encyclopedia.chatbot.retrieval import InMemoryRetriever, VectorRetriever
from encyclopedia.chatbot.pipeline import answer_question
from encyclopedia.utils.resources import Resources


def _find_encyclopedia_path() -> Path:
    """First available: env, then fixture cache, then None (use in-memory)."""
    env_path = os.environ.get("CHATBOT_ENCYCLOPEDIA")
    if env_path and Path(env_path).exists():
        return Path(env_path)
    cache_dir = Path(ROOT, "test", "encyclopedia", "fixtures", "cache")
    if cache_dir.exists():
        for p in sorted(cache_dir.glob("encyclopedia_*.html")):
            return p
    for name in ["encyclopedia_output.html", "my_encyclopedia.html", "demo_encyclopedia.html"]:
        p = ROOT / name
        if p.exists():
            return p
    return None


def main():
    print("=" * 60)
    print("Climate Chatbot — Embedding and vector search example")
    print("=" * 60)

    # 1) Load corpus
    enc_path = _find_encyclopedia_path()
    if enc_path:
        print(f"\nLoading encyclopedia: {enc_path}")
        entries = load_entries_from_encyclopedia(enc_path)
    else:
        print("\nNo encyclopedia file found; using minimal in-memory corpus.")
        from encyclopedia.core.encyclopedia import AmiEncyclopedia
        enc = AmiEncyclopedia(title="Example")
        enc.entries = [
            {"term": "climate change", "description_html": "<p>Long-term shifts in temperatures and weather patterns.</p>", "wikidata_id": "Q7942"},
            {"term": "greenhouse gas", "description_html": "<p>Gases that trap heat in the atmosphere.</p>", "wikidata_id": "Q131784"},
            {"term": "carbon dioxide", "description_html": "<p>CO2 is a greenhouse gas produced by burning fossil fuels.</p>", "wikidata_id": "Q1218"},
        ]
        entries = load_entries_from_encyclopedia(enc)

    assert len(entries) >= 1, "Need at least one entry"
    print(f"Entries: {len(entries)}")

    sections = entries_to_sections(entries)
    chunks = chunk_sections(sections)
    print(f"Sections: {len(sections)}, Chunks: {len(chunks)}")

    # 2) InMemoryRetriever (no extra deps)
    print("\n--- InMemoryRetriever (keyword) ---")
    in_memory = InMemoryRetriever(chunks)
    for q in ["climate change", "greenhouse gas", "what is CO2?"]:
        results = in_memory.search(q, k=2)
        print(f"  Q: {q}")
        for ch, score in results:
            print(f"    [{score:.2f}] {ch.get('term', '')}: {ch.get('text', '')[:60]}...")
        print()

    # 3) VectorRetriever (sentence-transformers + ChromaDB)
    try:
        persist_dir = str(Path(Resources.get_temp_dir("examples", "chatbot"), "chroma"))
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        print("--- VectorRetriever (embeddings + ChromaDB) ---")
        print(f"  Index dir: {persist_dir}")
        vector_retriever = VectorRetriever(
            chunks,
            persist_directory=persist_dir,
            collection_name="example_climate",
        )
        for q in ["climate change", "greenhouse gas", "what is CO2?", "temperature and weather"]:
            results = vector_retriever.search(q, k=2)
            print(f"  Q: {q}")
            for ch, score in results:
                print(f"    [{score:.2f}] {ch.get('term', '')}: {ch.get('text', '')[:60]}...")
        print()

        # 4) Full pipeline with vector retriever (no LLM)
        print("--- Pipeline (vector retriever, no LLM) ---")
        out = answer_question("What is climate change?", vector_retriever, min_score=0.2, llm_generate=None)
        print(f"  Refused: {out['refused']}")
        print(f"  Answer: {out['answer'][:200]}...")
        print(f"  Citations: {len(out['citations'])}")
    except ImportError as e:
        print("\n--- VectorRetriever skipped (missing deps) ---")
        print("  Install with: pip install sentence-transformers chromadb")
        print(f"  Error: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()
