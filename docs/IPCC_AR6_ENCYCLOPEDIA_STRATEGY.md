# IPCC AR6/SYR Encyclopedia — Strategy

**Date:** 2026-05-27 (system date)  
**Status:** Active (planning; implementation incremental)  
**Audience:** Team building an encyclopedia from the IPCC AR6 Synthesis Report (SYR)

---

## Purpose

Build a coordinated set of encyclopedias grounded in **IPCC AR6/SYR**, using the project’s existing **wordlist → curation → Wikimedia enrichment → manual repair → disambiguation** pipeline (`docs/encyclopedia_creation_review.md`). Work proceeds **incrementally**: after each stage, inspect artifacts and score relevance on a **1–5 scale** before continuing.

For this corpus, **`main_subject`** is IPCC-related climate assessment vocabulary. The same pipeline applies to other corpora by setting a different `main_subject`; disambiguation and Wikipedia labelling use **`main_subject`** rather than hard-coded “climate” in code and docs.

Follow `../amilib/docs/style_guide_compliance.md`, `../pygetpapers/docs/styleguide.md`, and `docs/STYLE_GUIDE.md` for code and documentation.

---

## Three-encyclopedia model

Use three separate encyclopedias to keep precision high and avoid mixing concept terms with metadata terms.

| Encyclopedia | Scope | Includes | Excludes |
|--------------|-------|----------|----------|
| **`main_subject`** | Core subject vocabulary for this project | IPCC concepts and science terms; **organizations** relevant to IPCC context | Country/region gazetteers; report-section labels; author-role markup |
| **`geopolitical`** | Place and political-entity metadata | Countries, regions, geopolitical groupings used in reports | Core science concepts; report-structure tokens |
| **`reports`** | Document-structure and report annotation metadata | Sections/chapters/figures/tables, annotation language (likelihood/confidence), actors/roles, report-specific metadata | Core science concept vocabulary and general geopolitical lookup terms |

**Operating rule:** classify each term into exactly one primary encyclopedia at ingestion time. Cross-links are allowed, but source ownership stays single to keep curation and quality scoring auditable.

---

## Quality principle: precision over recall (this stage)

**False positives are more serious than false negatives at this stage.**

| Error | What it means | Why it matters now |
|-------|----------------|-------------------|
| **False positive** | A term or link that should not appear in the encyclopedia | **Visible** to users; can lower perceived quality of the whole product |
| **False negative** | AR6/SYR does not cover a topic users might expect | Often **not visible**; less damaging while the corpus is AR6/SYR–centric |

**Implications**

- **Automatic curation (2a):** Prefer **rejection** when unsure. Keep rejected lists **auditable and reversible**, but bias toward dropping noise (off-`main_subject` terms, common words, boilerplate).
- **Manual curation (2b):** **Authoritative** gate. When unsure, reject. A smaller, cleaner wordlist is success.
- **Wikipedia / disambiguation:** Run only on **approved** terms so weak links do not ship.
- **Coverage gaps (false negatives):** Acceptable for an AR6/SYR–first v1. **Recall** is addressed deliberately via **non-IPCC annotation** (see below), not by loosening AR6/SYR extraction.

---

## Recall path: non-IPCC annotation

One anticipated use of the encyclopedia is to **annotate non-IPCC material**. When terms or phrases are **common in that material** but absent from the AR6/SYR wordlist, **update the wordlist** and re-run later pipeline stages. This grows coverage without lowering the precision bar on the IPCC-derived set.

---

## Pipeline (order of work)

Stages align with the existing encyclopedia creation flow; stage 1 is the new IPCC-specific input.

| # | Stage | Purpose |
|---|--------|---------|
| **1** | **Wordlist from AR6/SYR** | Extract candidate terms/phrases (e.g. amilib **txt2phrases** on report text). Raw list may be inclusive; noise is expected. |
| **2a** | **Automatic curation** | Remove false positives: off-`main_subject`, common words, headings/footnotes/boilerplate where possible. **Conservative (high precision).** |
| **2b** | **Manual curation** | Human selection of entries to keep or drop. Overrides automation where flagged. |
| **3** | **Wikipedia / Wikimedia lookup** | Link approved terms to pages; collect unresolved list. |
| **4** | **Manual entries for unresolved** | Create or delete manually supported entries for IPCC-specific or corrected concepts. |
| **5** | **Identify disambiguation links** | Flag Wikipedia disambiguation pages. |
| **6** | **Disambiguation editor** | Order candidates by **`main_subject` relevance** or **reject all** when no sense fits. Labelling strategy: see below (not yet specified). |

**Do not** run full encyclopedia HTML generation until stages 1–6 score consistently high on the 1–5 relevance scale.

**Relation to existing code:** Stages 2–7 in `docs/encyclopedia_creation_review.md` (dictionary, Wikipedia/Wikidata, HTML encyclopedia, normalize/merge, disambiguation UI) are the natural home for bullets 2–6; bullet 1 is AR6/SYR → wordlist via amilib-style tooling.

---

## `main_subject`: labelling Wikipedia entries (not yet specified)

Stage 6 (and related curation) need a way to mark or rank Wikipedia candidates as **`main_subject` related**. **No strategy is chosen yet.** Candidates under consideration:

| Strategy | Idea | Notes |
|----------|------|--------|
| **A. Reference corpus** | Provide a corpus of documents known to be about `main_subject`; compare candidate pages or descriptions against that corpus (similarity, embeddings, etc.). | Up-front cost to assemble corpus; explicit and auditable. |
| **B. Iterative descriptions** | Use Wikipedia descriptions already extracted for **resolved** entries as the reference set; refine over passes. | Attractive when only a **small fraction** of entries need disambiguation (e.g. **&lt; 10%** unresolved): lower manual cost, bootstraps from the same pipeline. Risk if early resolutions are wrong—errors propagate. |

**Open decisions (defer):** How to score “`main_subject` related”; when to prefer A vs B; human override rules; whether AR6/SYR text itself counts as reference corpus for strategy A.

---

## Risks (high level)

- **Phrase quality vs. report structure:** Full SYR text may over-index headings, footnotes, and boilerplate unless input is scoped (e.g. body text only).
- **“In the report” ≠ encyclopedia headword:** Country names, generic science words, etc. may appear in AR6 without being good entries.
- **Automatic filters:** Can remove true positives; rejected lists must stay reviewable (precision-first does not mean silent loss).
- **Wikipedia ≠ IPCC usage:** A resolved Wikipedia page may still be wrong for assessment vocabulary; manual entries remain essential.
- **Disambiguation “reject all”** is a first-class outcome when no Wikipedia sense fits `main_subject` / IPCC context.

---

## Suggested tests per stage

Use as **acceptance checks** before scoring relevance (1–5). Write temporary outputs under `Path(Resources.TEMP_DIR, "<main_subject>", ...)` (for this project, `temp/ipcc/...`) so each stage is inspectable. Keep automated tests in `test/` at project root. Tests: **real implementations, no mocks**, descriptive `assert` messages (per amilib / pygetpapers).

| Stage | Purpose | Suggested tests (high level) |
|--------|---------|------------------------------|
| **1. Wordlist** | Raw candidates from AR6/SYR | Small SYR excerpt fixture → non-empty phrase list; stable output schema; bounds on phrase length; spot-check known `main_subject` terms in fixture; no unbounded duplicate explosion. |
| **2a. Automatic curation** | Remove obvious false positives | Filter reduces count but not to zero; stopwords/common words absent; `main_subject` terms retained on golden subset; rejected list written and auditable; rules idempotent. |
| **2b. Manual curation** | Human-in-the-loop | Load/save round-trip preserves term IDs; selected vs rejected disjoint; manual overrides beat automatic rules when flagged; export matches saved “approved” fixture. |
| **3. Wikipedia lookup** | Link terms to pages | Small approved wordlist: URL or explicit unresolved; batch size limits; graceful failure structure; Wikidata ID when Wikipedia resolves; unresolved list inspectable. |
| **4. Manual unresolved** | IPCC-specific entries | Manual entry has stable `term` + optional URL/description; delete does not orphan HTML; golden manual entry survives pipeline step. |
| **5. Disambiguation detection** | Flag disambiguation pages | Known disambiguation URL detected; non-disambiguation not flagged; counts match fixture spot-check. |
| **6. Disambiguation editor** | Choose sense or reject | Ordered candidates persisted; “reject all” removes term from active set; chosen candidate is canonical link; fixture: two candidates → pick one → single canonical URL in export. |

---

## Incremental workflow and 1–5 scoring

After each bullet, inspect artifacts (lists, CSV/HTML, small encyclopedia slice) and score **relevance** 1–5 before coding the next stage. Score **precision** heavily in stages 2–6.

| Stage | Scoring focus |
|--------|----------------|
| **1. Wordlist** | Are headwords encyclopedia-worthy and IPCC-grounded? |
| **2. Curation** | Precision of `main_subject` vs. noise (prefer few embarrassing keeps over many marginal ones). |
| **3. Wikipedia** | Correct page for `main_subject` / IPCC context, not merely any page. |
| **4. Manual entries** | Gap coverage without polluting the set. |
| **5. Disambiguation detection** | Are flags trustworthy? |
| **6. Disambiguation resolution** | Is the chosen (or rejected) sense right for `main_subject`? (Depends on labelling strategy once specified.) |

Use **frozen, versioned outputs per stage** and **small golden fixtures** for regression tests.

---

## Summary recommendation

Proceed **in the order listed**, with versioned outputs per stage and golden fixtures for tests. Treat automatic curation as **assistive and conservative**, manual curation and disambiguation as **authoritative**, and non-IPCC wordlist updates as the **deliberate** way to improve recall—not looser AR6/SYR extraction.

---

## Related documentation

| Topic | Location |
|--------|----------|
| Wordlist → encyclopedia pipeline | `docs/encyclopedia_creation_review.md` |
| Create from wordlist (script) | `Examples/create_encyclopedia_from_wordlist.py`, `docs/create_encyclopedia_from_wordlist_summary.md` |
| HTML → wordlist → KG workflow | `docs/html_to_knowledge_graph_workflow.md` |
| Project style guide | `docs/STYLE_GUIDE.md` |

---

*Revised 2026-05-28 (system date): three-encyclopedia model (`main_subject`, `geopolitical`, `reports`) and `main_subject` terminology.*

*Update this document when AR6/SYR tooling paths, fixtures, stage gates, or `main_subject` labelling strategy change. Use system date in revisions.*
