# Climate Encyclopedia Chatbot — Design

**Basis:** Aggregated, deduplicated climate encyclopedia (~544 entries from existing HTML sources in the repo).  
**Goal:** Lightweight, open-source chatbot that answers user questions from labelled sections only, with guardrails.

**Date:** 2025-03-05 (system date)

---

## 1. Strategy

### 1.1 High-level approach

- **Retrieval-first (RAG):** For each user question, retrieve the most relevant **entries** and **labelled sections** (term, definition, description, etc.) from the encyclopedia corpus. No generation from model memory; answers are grounded in retrieved text.
- **Section-aware:** Use existing structure (e.g. `term`, `description_html`, `definition_html`, `wikipedia_url`, `wikidata_id`) so responses can cite “definition of X” or “description of Y” and stay within labelled content.
- **Guardrails:**
  - **Scope:** Answer only from retrieved encyclopedia content; refuse or say “I don’t know” when retrieval is empty or low-confidence.
  - **Citation:** Prefer answers that reference which entry/section the information came from.
  - **No off-corpus claims:** Optional post-check that the answer does not contradict or invent beyond the retrieved snippets.
- **Lightweight:** Small embedding model + small local or API-based LLM; single-process app (e.g. FastAPI or CLI) without heavy orchestration for v1.

### 1.2 Data flow

1. **Ingest:** Load encyclopedia HTML (or pre-exported JSON) → parse into entries with labelled sections.
2. **Index:** Chunk by entry and/or by section (e.g. one chunk per `term` + `definition` + first paragraph) → compute embeddings → store in a vector index.
3. **Query:** User question → embed → retrieve top-k chunks (with section labels) → build prompt with only those chunks → LLM generates short answer (and optional citation) → optional guardrail check → return to user.

### 1.3 Out-of-scope / refusal

- Questions with no or very low relevance to the corpus → respond with “I can only answer from the climate encyclopedia; I don’t have information on that.”
- Requests for medical/legal advice or non-encyclopedia content → refuse politely and restate scope.

---

## 2. External libraries and models

### 2.1 Recommended stack (open-source)

| Layer | Library / model | Role |
|--------|------------------|------|
| **Embeddings** | `sentence-transformers` | Encode question and section chunks (e.g. `all-MiniLM-L6-v2`). Implemented in `encyclopedia.chatbot.embeddings`. |
| **Vector store** | `chromadb` | Store and search embeddings; used by `VectorRetriever` in `encyclopedia.chatbot.retrieval`. Optional: `pip install encyclopedia[chatbot]`. |
| **LLM** | **Option A:** `ollama` + small model (e.g. `llama3.2:3b`, `phi3:mini`) | Local inference, no API key |
| | **Option B:** `openai`-compatible API (e.g. local server or hosted open model) | Same interface for different backends |
| **Web / API** | `fastapi` + `uvicorn` | REST API for “question → answer”; optional simple HTML UI |
| **Corpus loading** | Existing `encyclopedia` package | `AmiEncyclopedia`, `create_from_html_file()` to get entries/sections |

### 2.2 Optional

- **Guardrail check:** Heuristic (e.g. overlap of key phrases between answer and retrieved text) or a tiny classifier; no extra library required for v1.
- **Evaluation:** `pytest` + small set of (question, expected-section) pairs to regress on retrieval and “answer-from-section” behaviour.

### 2.3 Models (concrete choices)

- **Embedding:** `sentence-transformers/all-MiniLM-L6-v2` (80M params, fast, good for semantic similarity).
- **LLM (local):** e.g. `llama3.2:3b` or `phi3:mini` via Ollama (run `ollama run llama3.2:3b`).
- **LLM (API):** Any OpenAI-compatible endpoint serving an open model (e.g. Mistral, Llama) if not running locally.

---

## 3. Architecture diagrams (Graphviz)

Two diagrams are defined in the repo and can be rendered with `dot`:

- **Components:** `docs/climate_chatbot_components.dot` — main components and their interfaces.
- **Program flow:** `docs/climate_chatbot_flow.dot` — request path from user question to answer.

### 3.1 Render commands

```bash
# From repo root
dot -Tsvg docs/climate_chatbot_components.dot -o docs/climate_chatbot_components.svg
dot -Tpng docs/climate_chatbot_components.dot -o docs/climate_chatbot_components.png

dot -Tsvg docs/climate_chatbot_flow.dot -o docs/climate_chatbot_flow.svg
dot -Tpng docs/climate_chatbot_flow.dot -o docs/climate_chatbot_flow.png
```

### 3.2 Component diagram (overview)

- **Corpus:** Encyclopedia HTML/JSON → Parser → Entries with labelled sections.
- **Indexer:** Sections → Embedding model → Vector store.
- **API / App:** HTTP or CLI → Query handler.
- **Retrieval:** Query → Embed → Vector search → Top-k chunks (with labels).
- **Generator:** Prompt (system + retrieved chunks + question) → LLM → Answer (+ optional citation).
- **Guardrails:** Scope check (retrieval non-empty, confidence); optional consistency check.

### 3.3 Flow diagram (per request)

- User question → embed question → vector search → get top-k sections.
- If none or low score → return “I don’t have information on that.”
- Else: build prompt (instructions + retrieved sections with labels) → call LLM → parse answer → optional guardrail → return answer (and citations).

---

## 4. File locations

| Artefact | Path |
|----------|------|
| Design doc | `docs/CLIMATE_CHATBOT_DESIGN.md` (this file) |
| TDD approach and test order | `docs/CLIMATE_CHATBOT_TDD.md` |
| Component diagram (Graphviz source) | `docs/climate_chatbot_components.dot` |
| Component diagram (rendered) | `docs/climate_chatbot_components.svg` |
| Program flow diagram (Graphviz source) | `docs/climate_chatbot_flow.dot` |
| Program flow diagram (rendered) | `docs/climate_chatbot_flow.svg` |
| Corpus aggregation script | `scripts/count_climate_encyclopedia_entries.py` (basis: ~544 deduplicated entries) |
| Chatbot package (corpus, chunker, retrieval, guardrails, prompt, pipeline) | `encyclopedia/chatbot/` |
| Chatbot tests (TDD) | `test/chatbot/` |

---

## 5. Implemented: embeddings and vector search

- **Embeddings:** `encyclopedia.chatbot.embeddings.SentenceTransformerEmbedder` (model: `all-MiniLM-L6-v2`).
- **Vector retriever:** `encyclopedia.chatbot.retrieval.VectorRetriever` — indexes chunks with ChromaDB (cosine), `search(query, k)` returns `[(chunk, score)]`. Drop-in for `answer_question(..., retriever=vector_retriever)`.
- **Optional install:** `pip install encyclopedia[chatbot]` (sentence-transformers, chromadb).
- **Example:** `Examples/chatbot_embedding_example.py` — loads encyclopedia, runs InMemoryRetriever and VectorRetriever, then pipeline with vector retriever.

## 6. Next steps

1. Export aggregated encyclopedia to a single JSON or HTML for indexing (script exists: `scripts/count_climate_encyclopedia_entries.py`).
2. Wire query → retrieve → prompt → LLM (Ollama or API) with guardrails.
3. Add simple FastAPI endpoint and optional UI for testing.
