#!/usr/bin/env python3
"""
Example: real embeddings and vector search over a climate encyclopedia.

Loads an encyclopedia, builds sections and chunks, then:
1. InMemoryRetriever (keyword) — no extra deps
2. VectorRetriever (sentence-transformers + ChromaDB) — pip install encyclopedia[chatbot]
3. Full pipeline: query -> retrieve -> guardrail -> prompt -> LLM -> answer

Usage (from repo root):
  python Examples/chatbot_embedding_example.py

Optional env:
  CHATBOT_ENCYCLOPEDIA  Path to HTML or JSON corpus (default: aggregated JSON or fixture)
  OLLAMA_MODEL         Ollama model for LLM (e.g. llama3.2:3b). If set, pipeline uses Ollama.
  OPENAI_API_KEY       If set (and no OLLAMA_MODEL), pipeline uses OpenAI-compatible API.
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
    """First available: env, aggregated JSON, fixture cache, root files, or None (in-memory)."""
    env_path = os.environ.get("CHATBOT_ENCYCLOPEDIA")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p
    # Aggregated export from: python scripts/count_climate_encyclopedia_entries.py --export
    json_path = Path(Resources.TEMP_DIR, "chatbot", "climate_encyclopedia_entries.json")
    if json_path.exists():
        return json_path
    cache_dir = Path(ROOT, "test", "encyclopedia", "fixtures", "cache")
    if cache_dir.exists():
        for p in sorted(cache_dir.glob("encyclopedia_*.html")):
            return p
    for name in ["encyclopedia_output.html", "my_encyclopedia.html", "demo_encyclopedia.html"]:
        p = Path(ROOT, name)
        if p.exists():
            return p
    return None


def _make_llm_generator():
    """Return llm_generate callable from env: Ollama, then OpenAI, else None."""
    ollama_model = os.environ.get("OLLAMA_MODEL")
    if ollama_model:
        try:
            from encyclopedia.chatbot.llm import make_ollama_generator
            return make_ollama_generator(model=ollama_model)
        except Exception:
            return None
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        try:
            from encyclopedia.chatbot.llm import make_openai_generator
            return make_openai_generator(model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), api_key=api_key)
        except Exception:
            return None
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

        # 4) Full pipeline: retrieve -> guardrail -> prompt -> LLM
        llm_generate = _make_llm_generator()
        if llm_generate is None:
            print("--- Pipeline (vector retriever, no LLM) ---")
            print("  Set OLLAMA_MODEL or OPENAI_API_KEY to use an LLM.")
        else:
            print("--- Pipeline (vector retriever + LLM) ---")
        out = answer_question(
            "What is climate change?",
            vector_retriever,
            min_score=0.2,
            llm_generate=llm_generate,
        )
        print(f"  Refused: {out['refused']}")
        answer_preview = (out.get("answer") or "")[:300]
        print(f"  Answer: {answer_preview}{'...' if len(out.get('answer') or '') > 300 else ''}")
        print(f"  Citations: {len(out['citations'])}")
    except ImportError as e:
        print("\n--- VectorRetriever skipped (missing deps) ---")
        print("  Install with: pip install sentence-transformers chromadb")
        print(f"  Error: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()
