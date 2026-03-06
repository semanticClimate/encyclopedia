# Climate Chatbot — TDD Approach

**Date:** 2025-03-05 (system date)

This document describes the test-driven development strategy for the climate encyclopedia chatbot. Tests are written first to define contracts and behaviour; implementation follows to make them pass.

---

## 1. TDD Strategy

### 1.1 Order of development (test → implement)

We add tests in dependency order so that lower-level behaviour is fixed before higher-level tests run.

| Phase | Component | What the tests define | Test file |
|-------|------------|------------------------|-----------|
| **1** | Corpus for chatbot | Entries loaded from encyclopedia have labelled sections (term, description, definition, etc.); section extraction API | `test_corpus.py` |
| **2** | Chunker | Entries → list of chunks; each chunk has `section_label`, `text`, `entry_id` (and optional `term`) | `test_chunker.py` |
| **3** | Retrieval | Interface: `search(query: str, k: int) -> list[(chunk, score)]`; in-memory implementation for TDD; later swap to vector store | `test_retrieval.py` |
| **4** | Guardrails (scope) | When retrieval is empty or max score below threshold → return refusal message; no LLM call | `test_guardrails.py` |
| **5** | Prompt builder | Given chunks + question → string with system instructions, retrieved context (with labels), and question | `test_prompt_builder.py` |
| **6** | Answer pipeline | Question → retrieval → guardrail (refuse or continue) → prompt → LLM → response. Use a real stub LLM (returns fixed string) so no mocks | `test_answer_pipeline.py` |

### 1.2 Principles

- **No mocks:** Use real implementations or real test doubles (e.g. a class `StubLLM` that returns a fixed string). No `unittest.mock` or `patch`.
- **Assert, not return False:** All tests use `assert` with descriptive messages.
- **Small corpus in tests:** Use a few in-memory entries or the small encyclopedia fixture so tests are fast and deterministic.
- **Temporary files:** Use `Resources.TEMP_DIR` with subdir `test/chatbot/...` for any on-disk test artefacts.
- **Path construction:** Use `Path(a, b, c)`, never `Path("a/b")` or `x / "y"`.

### 1.3 Red–green–refactor

1. **Red:** Write a test that fails (missing or stub implementation).
2. **Green:** Implement the minimum code that makes the test pass.
3. **Refactor:** Improve implementation without changing behaviour; tests stay green.

---

## 2. Test layout

```
test/chatbot/
├── __init__.py
├── conftest.py              # Fixtures: sample_entries, sample_chunks, stub_llm
├── test_corpus.py           # Corpus loading and section structure
├── test_chunker.py          # Chunker contract
├── test_retrieval.py        # Retrieval interface + in-memory implementation
├── test_guardrails.py       # Scope guardrail (refuse when no/low results)
├── test_prompt_builder.py   # Prompt format
└── test_answer_pipeline.py  # End-to-end with stub LLM
```

---

## 3. Contracts (defined by tests)

### 3.1 Corpus

- **Input:** Encyclopedia (HTML path or `AmiEncyclopedia` instance).
- **Output:** List of entry dicts; each has at least `term` and one or more of `description_html`, `definition_html`, `wikipedia_url`, `wikidata_id`.
- **Section extraction:** A function `entries_to_sections(entries) -> list[dict]` where each section has `section_label`, `text`, `entry_id`, `term`.

### 3.2 Chunker

- **Input:** List of section dicts (or entries).
- **Output:** List of chunk dicts: `section_label`, `text`, `entry_id`, optional `term`. Chunk text is plain text (no HTML tags for embedding).

### 3.3 Retriever

- **Interface:** `search(query: str, k: int = 5) -> list[tuple[dict, float]]` (list of (chunk, score)).
- **In-memory implementation for TDD:** Keyword or simple string match; scores in [0, 1]. Enables tests without sentence-transformers/ChromaDB.

### 3.4 Guardrail (scope)

- **Input:** Retrieval result (list of (chunk, score)).
- **Parameters:** `min_score: float` (e.g. 0.2).
- **Output:** `(should_refuse: bool, message: str)`. Refuse when result is empty or `max(scores) < min_score`; message is the standard refusal text.

### 3.5 Prompt builder

- **Input:** `chunks: list[dict]`, `question: str`, optional `system_prompt: str`.
- **Output:** Single string: system + formatted chunks (with labels) + user question. Format is stable so tests can assert on substring presence.

### 3.6 Answer pipeline

- **Input:** `question: str`, retriever, guardrail, prompt builder, LLM (callable or interface).
- **Output:** `dict` with `answer: str`, `refused: bool`, optional `citations: list`. When refused, `answer` is the refusal message and `refused` is True.
- **Stub LLM:** A real class that implements the same interface as the real LLM (e.g. `generate(prompt: str) -> str`) and returns a fixed string for tests.

---

## 4. Running the tests

```bash
# From repo root
python -m pytest test/chatbot/ -v

# Exclude integration (if any added later)
python -m pytest test/chatbot/ -v -m "not integration"
```

Tests are written so they can run before full implementation (stubs return minimal values or raise; tests assert the desired behaviour and will go from red to green as code is added).
