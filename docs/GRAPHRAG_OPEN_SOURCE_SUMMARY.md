# GraphRAG with Open Source Tools — Summary

**Date:** 2026-03-17 (system date)

Short reference for building GraphRAG with open source tools and running it **without API keys**.

---

## Open source GraphRAG options

| Option | Repo | License | Notes |
|--------|------|---------|--------|
| **Microsoft GraphRAG** | [microsoft/graphrag](https://github.com/microsoft/graphrag) | MIT | Main option: indexing (entities, communities, summaries) + local/global search. `pip install graphrag`. |
| **AWS GraphRAG Toolkit** | [awslabs/graphrag-toolkit](https://github.com/awslabs/graphrag-toolkit) | Apache 2.0 | Lexical Graph, BYOKG-RAG; integrates with Neptune, OpenSearch, PostgreSQL. |
| **Roll your own** | — | — | Use this repo’s `encyclopedia.utils.knowledge_graph` (NetworkX, GraphML) + community detection (e.g. `leidenalg`) + local LLM for summarisation and QA. |

---

## Using Microsoft GraphRAG without API keys

Use **Ollama** (local LLM and embeddings) so no OpenAI/Azure API key is required.

1. **Install and run Ollama**, then pull models, e.g.:
   - `ollama pull llama3.2` (or mistral, phi3)
   - `ollama pull nomic-embed-text`
2. **Configure GraphRAG** (`settings.yaml`) to use Ollama:

   ```yaml
   llm:
     type: ollama_chat
     model: llama3.2:latest
     model_supports_json: true
     api_base: http://localhost:11434
     # no api_key

   embeddings:
     llm:
       type: ollama_embedding
       model: nomic-embed-text
       api_base: http://localhost:11434
   ```

3. If your GraphRAG version only has OpenAI-compatible client, point it at Ollama:
   - `api_base: http://localhost:11434/v1` and use a local model name; no real API key needed.

**Community option:** [TheAiSingularity/graphrag-local-ollama](https://github.com/TheAiSingularity/graphrag-local-ollama) is a fork/wrapper set up for local Ollama-only use (no API keys).

---

## Pipeline (Microsoft GraphRAG)

- **Indexing:** Text → chunks → LLM extracts entities/relationships → build graph → community detection (e.g. Leiden) → summarise communities → embed. Stored as Parquet + vectors.
- **Query:** **Local search** (entity-focused, graph traversal) and **Global search** (community summaries). Optional drift search.
- **Caveat:** Indexing is compute- and LLM-heavy; start with small data and cheap/small models.

---

## Relation to this project

The encyclopedia’s **knowledge graph** (`encyclopedia.utils.knowledge_graph`: `KnowledgeGraphBuilder`, `GraphExporter` → GraphML) can feed a custom GraphRAG-style pipeline: add community detection, summarise subgraphs with a local LLM, then use the same retrieval + generation pattern (e.g. as in `encyclopedia.chatbot`).

---

*See also: `docs/CLIMATE_CHATBOT_DESIGN.md` (vector RAG), `docs/CABOOK_CHATBOT_ONBOARDING.md` (book chatbot).*
