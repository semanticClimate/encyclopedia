# CABook Chatbot — Onboarding for New Team Members

**Date:** 2026-03-17 (system date)  
**Audience:** New team member creating a chatbot for the Climate Academy Student Book (CABook)  
**Source:** `test/chatbot/full_student_book.html`

---

## 1. Style guides (read first)

Before writing code, read and follow:

1. **amilib style guide**  
   - Path: `../amilib/docs/style_guide_compliance.md` (or project docs that reference it).  
   - Rules: absolute imports with module prefix; empty `__init__.py`; no mocks in tests; no magic strings; path construction; use `assert` in tests with descriptive messages.

2. **Encyclopedia project style guide**  
   - Path: `docs/STYLE_GUIDE.md`.  
   - Extends amilib: use `Path(Resources.TEMP_DIR, ...)` for temp files; `Path()` with comma-separated arguments (no string concatenation with `/`); constants instead of magic strings; document with **system date** (e.g. run `date` for “Date: YYYY-MM-DD (system date)”); propose changes and get approval before implementing.

Use **system date** in any new docs or comments (e.g. “2026-03-17 (system date)”).

---

## 2. CABook: what you’re building on

- **Book file:** `<root>/test/chatbot/full_student_book.html`  
  Single HTML file: **Climate Academy Student Book** (CABook), 16 chapters, narrative content (not encyclopedia entries).

- **Structure of the HTML:**  
  - **h1** — main chapters (e.g. “Contents”, “Introduction”, “The Absolute Basics”, “Mass Extinction Events”, “Spaceship Earth”) with `id` (e.g. `id="the-absolute-basics"`).  
  - **h2 / h3 / h4 / h5** — sub-sections (“Chapter Summary”, “Introduction”, “Main Text”, “Finding the right seat (N°1)”, etc.).  
  - **p** — paragraphs; some contain footnote refs (`class="footnote-ref"`).

So the corpus is **chapter/section + paragraphs**, not term/definition/description entries.

---

## 3. Existing chatbot (encyclopedia) vs CABook

| Aspect | Existing climate encyclopedia chatbot | CABook chatbot (to build) |
|--------|----------------------------------------|----------------------------|
| **Corpus** | Encyclopedia entries (term, description_html, definition_html, wikidata_id) | Single HTML book: chapters and sections (h1–h5 + paragraphs) |
| **Source** | HTML/JSON with `AmiEncyclopedia` or `load_entries_from_json` | `full_student_book.html` — needs an HTML book parser |
| **Sections** | `entries_to_sections()`: one section per term/description/definition per entry | Need: sections = “chapter/section heading + text under it” (e.g. by heading level) |
| **Chunks** | One chunk per section; `chunk_sections()` already works on `section_label`, `text`, `entry_id`, `term` | Same chunk format: use `section_label` = chapter/section title, `entry_id` = section id or slug, `term` = heading text |
| **Rest of stack** | Retrieval → guardrails → prompt → LLM | **Reuse**: `chunker.chunk_sections`, `VectorRetriever`, `pipeline.answer_question`, `guardrails`, `prompt`, optional FastAPI app |

So the new work is: **parse CABook HTML into sections**, then feed those sections into the existing chunker and pipeline.

---

## 4. Suggested steps for CABook chatbot

1. **Parse CABook HTML into sections**  
   - Use lxml/html (or amilib if there are suitable helpers).  
   - Walk the DOM: for each heading (h1–h5), take its `id` and text as section identity; collect all following sibling text (e.g. until the next same-or-higher-level heading).  
   - Strip HTML to plain text for retrieval (you can reuse or mirror `_strip_html` in `encyclopedia.chatbot.corpus`).  
   - Output list of dicts compatible with existing sections: e.g. `section_label`, `text`, `entry_id` (e.g. heading `id`), `term` (heading text).

2. **Book-specific loader**  
   - Add a loader (e.g. in `encyclopedia.chatbot.corpus` or a dedicated module) that:  
     - Accepts `Path("test/chatbot/full_student_book.html")`.  
     - Calls your HTML book parser.  
     - Returns a list of section dicts in the same shape as `entries_to_sections()` (so `chunk_sections()` and the rest of the pipeline need no change).

3. **Reuse existing pipeline**  
   - `chunk_sections(sections)` → build `VectorRetriever` (or `InMemoryRetriever`) → `answer_question(question, retriever=..., llm_generate=...)`.  
   - Optional: small script or FastAPI app that loads CABook, builds retriever, and runs the same pipeline (see `Examples/chatbot_embedding_example.py` and `encyclopedia.chatbot.app`).

4. **Tests**  
   - Put tests under `test/chatbot/`.  
   - Follow style: no mocks; real parsing; use `Path(Resources.TEMP_DIR, "test", "chatbot", ...)` for any temp output; assertions with clear, descriptive messages.

5. **Temp and paths**  
   - All temporary files under `Resources.TEMP_DIR`, e.g. `Path(Resources.TEMP_DIR, "test", "chatbot", "cabook_...")`.  
   - Use `Path(..., "a", "b")` (comma-separated), not string concatenation with `/`.

---

## 5. Key file locations

| What | Where |
|------|--------|
| CABook HTML | `test/chatbot/full_student_book.html` |
| Style guide (encyclopedia) | `docs/STYLE_GUIDE.md` |
| Climate chatbot design | `docs/CLIMATE_CHATBOT_DESIGN.md` |
| Chatbot package (corpus, chunker, retrieval, pipeline, guardrails, prompt, llm) | `encyclopedia/chatbot/` |
| Chatbot tests | `test/chatbot/` |
| Example (load corpus, retriever, pipeline) | `Examples/chatbot_embedding_example.py` |
| API + UI | `encyclopedia/chatbot/app.py`, `scripts/run_chatbot_api.py` |
| amilib style guide | `../amilib/docs/style_guide_compliance.md` |

---

## 6. Quick reference: section format

The existing pipeline expects sections (and chunks) with at least:

- `section_label` — e.g. `"description"` (encyclopedia) or `"Chapter 1: The Absolute Basics"` (book).  
- `text` — plain text (no HTML).  
- `entry_id` — stable id (e.g. wikidata_id for encyclopedia, or heading `id` for book).  
- `term` — short label (e.g. term name or heading text).

Your book parser should produce section dicts in this shape so that `chunk_sections()` and the rest of the code work unchanged.

---

## 7. Optional: run the existing chatbot

To see the current behaviour (encyclopedia corpus):

```bash
# From repo root
pip install -e ".[chatbot]"
python scripts/run_chatbot_api.py
# Open http://localhost:8000/
```

To use the aggregated climate encyclopedia JSON (if present):

```bash
python scripts/count_climate_encyclopedia_entries.py --export
# Then run the API; it will use temp/chatbot/climate_encyclopedia_entries.json
```

For CABook, you will add a way to load `test/chatbot/full_student_book.html` and pass the resulting sections into the same pipeline (and optionally switch the default corpus in the app or a dedicated script).

---

*This onboarding doc will be updated as the CABook chatbot design is refined. Always follow the style guides and use system date in new documentation.*
