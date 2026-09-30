# Maintenance issues (backlog)

**Date:** 2026-05-27 (system date)  
**Status:** Backlog — items below are **deferred** until explicitly scheduled

Tracked problems that affect documentation quality or agent/human workflow. Not implementation plans; remediation comes later.

---

## MI-001: Systematic date hallucination in documentation (deferred)

**Severity:** High (credibility, trust in docs)  
**Status:** Deferred  
**Reported:** 2026-05-27 (system date)

### Problem

Assistants and reviewers sometimes **invent or infer dates** (from training priors, git history guesses, or “sounds right” years) instead of **reading the system clock** (`date`) or **filesystem revision time** (`stat`) as required in `docs/STYLE_GUIDE.md` (Documentation → Date Usage).

This is a **systematic** failure mode, not a one-off typo.

### Example (2026-05-27)

| Source | Value |
|--------|--------|
| `docs/overview.md` footer (before fix) | `August 29, 2024` |
| Git commit that introduced that footer | **2025-08-29** |
| Filesystem mtime of `docs/overview.md` (pre-edit) | **2026-01-14** |
| Incorrect assistant suggestions | Mixed 2024 / git dates / “today” without running `date` or `stat` |

Footer was corrected to **2026-01-14 (filesystem revision date)** after `stat` on the file. The underlying process issue remains open.

### Required practice (existing rule)

From `docs/STYLE_GUIDE.md`:

- Run **`date`** for “current” / generation dates in new or updated docs.
- For “last updated” on an **existing** file, use **`stat`** (or equivalent) on that path unless the user specifies another source.
- Label the source: e.g. `(system date)`, `(filesystem revision date)`, `(extracted from source document)`.
- **Do not** assume years (e.g. 2024 vs 2025) or copy dates from git without explicit user request.

### Deferred remediation (later)

To be designed and scheduled; not in scope now:

1. **Audit** — Scan `docs/` (and other markdown) for footers and `Date:` lines; flag entries without a labeled source or obvious year drift.
2. **Convention** — Single pattern for “last updated” vs “document created” vs “content extracted from source”.
3. **Automation** — Optional pre-commit or CI check: warn when `Last updated` / `**Date:**` changes without a matching `stat`/`date` note or scripted update.
4. **Agent rules** — Reinforce in project rules/skills: always shell `date` / `stat` before writing dates; never infer from git unless asked.

### Related

- `docs/STYLE_GUIDE.md` — Date Usage
- `docs/overview.md` — footer corrected 2026-05-27; see git history for prior wrong value

---

*Add new items as `MI-00N`. Mark **Deferred**, **In progress**, or **Done** when status changes.*
