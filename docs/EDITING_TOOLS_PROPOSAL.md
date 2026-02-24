# Editing Tools Proposal

**Date:** February 21, 2026  
**Status:** Decisions Made - Ready for Implementation  
**Last Updated:** February 21, 2026 (Decisions finalized)

## Overview

Proposal for editing tools to enable users to manage encyclopedia entries. These tools will be integrated into the Streamlit browser (primary interface) with optional CLI support.

## Requirements Analysis

### 1. Delete Entries

**User Need:** Remove unwanted entries from the encyclopedia.

**Technical Considerations:**
- **Data Persistence:** Entries must be removed from `encyclopedia.entries` list
- **HTML Persistence:** Changes must be saved back to HTML file
- **Undo/Recovery:** Should entries be truly deleted or marked as deleted?
- **References:** What happens to links/references to deleted entries?
- **Confirmation:** Need user confirmation before deletion
- **Batch Operations:** Should support deleting multiple entries at once?

**Proposed Approach:**
- **Soft Delete First:** Mark entries as deleted in metadata, then allow hard delete
- **Metadata Tracking:** Store deleted entries in `metadata['deleted_entries']` with timestamp
- **Confirmation Dialog:** Streamlit confirmation before deletion
- **Undo Capability:** Keep deleted entries in metadata for 30 days (configurable)
- **Hard Delete Option:** After confirmation period, truly remove from entries list

**Implementation Notes:**
- Use existing `METADATA_ACTIONS` pattern
- Add `ACTION_DELETE` constant
- Store deletion info: `{entry_id, term, deleted_at, deleted_by}`
- Update `save_wiki_normalized_html()` to exclude deleted entries

---

### 2. Hide Entries (HTML/CSS)

**User Need:** Temporarily hide entries without deleting them (e.g., for review, incomplete entries).

**Technical Considerations:**
- **Display Only:** Entries remain in data but hidden in UI
- **CSS Approach:** Use `display: none` or `visibility: hidden`
- **Metadata Flag:** Store hidden state in entry metadata or encyclopedia metadata
- **Persistence:** Hidden state must persist across sessions
- **Reversibility:** Easy to show/hide entries
- **Filtering:** Search/browse should optionally include/exclude hidden entries

**Proposed Approach:**
- **Metadata Flag:** Store hidden entries in `metadata['hidden_entries']` (list of entry IDs)
- **HTML Attribute:** Add `data-hidden="true"` to entry divs in HTML
- **CSS Class:** Add `.hidden-entry { display: none; }` in generated HTML
- **Streamlit Filter:** Add toggle to show/hide hidden entries in UI
- **Visual Indicator:** Show hidden entries in a separate "Hidden Entries" section

**Implementation Notes:**
- Use existing `METADATA_HIDDEN_ENTRIES` constant (already defined!)
- Add `ACTION_HIDE` constant (already defined!)
- Update `create_wiki_normalized_html()` to add `data-hidden` attribute
- Add CSS to landing page HTML generator
- Streamlit UI: Checkbox/toggle for "Show hidden entries"

**Difference from Delete:**
- **Hide:** Temporary, reversible, entries still searchable (if enabled)
- **Delete:** Permanent (after confirmation period), entries removed from data

---

### 3. Add Entries by Wikipedia Search

**User Need:** Search Wikipedia for a term and add it as a new entry, checking for duplicates.

**Technical Considerations:**
- **Wikipedia Search:** Use existing `WikipediaPage` infrastructure
- **Duplicate Detection:** Check if entry already exists (by term, Wikidata ID, or URL)
- **Search Interface:** User-friendly search box with results preview
- **Entry Creation:** Create entry dictionary with Wikipedia content
- **Batch Addition:** Support adding multiple entries at once?
- **Validation:** Ensure entry has required fields before adding

**Proposed Approach:**
- **Search Flow:**
  1. User enters search term
  2. Search Wikipedia (use `WikipediaPage.lookup_wikipedia_page_for_term()`)
  3. Show preview of Wikipedia page (title, first paragraph, Wikidata ID)
  4. Check for duplicates:
     - By exact term match
     - By Wikidata ID match
     - By Wikipedia URL match
  5. If duplicate found, show existing entry and ask: "Merge? Replace? Skip?"
  6. If no duplicate, add entry to encyclopedia
- **Duplicate Detection Logic:**
  ```python
  def check_duplicate(encyclopedia, new_entry):
      # Check by term (case-insensitive)
      # Check by Wikidata ID
      # Check by Wikipedia URL
      # Return: (is_duplicate, existing_entry, match_type)
  ```
- **Entry Creation:** Use existing `add_wikipedia_feature()` pattern
- **UI:** Streamlit form with search, preview, and add button

**Implementation Notes:**
- Reuse `WikipediaPage` from `amilib.wikimedia`
- Reuse `add_wikipedia_feature()` from `encyclopedia.cli.versioned_editor`
- Add `add_entry_from_wikipedia()` method to `AmiEncyclopedia`
- Add duplicate detection helper function
- Streamlit UI: Search box → Preview → Add button → Confirmation

**Edge Cases:**
- Disambiguation pages (handle separately - mark as needing editing)
- Redirect pages (follow redirect to actual page)
- No Wikipedia page found (show error, suggest alternatives)
- Multiple Wikipedia pages found (show list, let user choose)

---

### 4. Merge One Encyclopedia into Another

**User Need:** Combine two encyclopedia files into one, handling duplicates intelligently.

**Technical Considerations:**
- **File Loading:** Load both source encyclopedias
- **Duplicate Resolution:** How to handle entries that exist in both?
  - Same term, same Wikidata ID → Merge synonyms
  - Same term, different Wikidata ID → Conflict resolution
  - Different terms, same Wikidata ID → Merge as synonyms
- **Conflict Resolution:** User choice or automatic?
- **Metadata Merging:** How to merge metadata (actions, history)?
- **Statistics:** Update statistics after merge
- **Output:** Save merged encyclopedia to new file or overwrite?

**Proposed Approach:**
- **Merge Strategy:**
  1. Load source encyclopedia (to merge FROM)
  2. Load target encyclopedia (to merge INTO)
  3. For each entry in source:
     - Check for duplicates in target (by Wikidata ID, then term, then URL)
     - If duplicate found:
       - **Same Wikidata ID:** Merge synonyms, keep best description
       - **Same term, different Wikidata ID:** Show conflict, ask user
       - **Different term, same Wikidata ID:** Merge as synonyms
     - If no duplicate: Add entry to target
  4. Save merged encyclopedia
- **Conflict Resolution UI:**
  - Streamlit: Show side-by-side comparison
  - Options: Keep target, Replace with source, Merge (combine), Skip
- **Metadata Handling:**
  - Merge `metadata['actions']` lists
  - Merge `metadata['hidden_entries']` lists
  - Update `metadata['merge_operations']` with merge history
- **Batch Mode:** CLI option for automatic merge (no user interaction)

**Implementation Notes:**
- Add `merge_encyclopedia()` method to `AmiEncyclopedia`
- Reuse existing `normalize_by_wikidata_id()` and `merge()` methods
- Add conflict resolution helper
- Streamlit UI: File upload → Preview conflicts → Resolve → Merge
- CLI: `encyclopedia merge --source file1.html --target file2.html --output merged.html`

**Edge Cases:**
- Title conflicts (use target title or ask user)
- Metadata conflicts (merge or prefer target)
- Large encyclopedias (batch processing, progress indicator)

---

### 5. Mark Entries as Needing Editing

**User Need:** Flag entries that need attention (e.g., disambiguation pages, incomplete entries).

**Technical Considerations:**
- **Flag Storage:** Where to store editing flags?
  - Entry metadata field: `needs_editing: true`
  - Encyclopedia metadata: `entries_needing_editing: [entry_ids]`
  - HTML attribute: `data-needs-editing="true"`
- **Reason/Notes:** Why does it need editing? (disambiguation, incomplete, etc.)
- **Visual Indicator:** How to show flagged entries in UI?
- **Filtering:** Filter/search by editing status
- **Workflow:** How to process flagged entries?

**Proposed Approach:**
- **Metadata Structure:**
  ```python
  entry['needs_editing'] = {
      'flag': True,
      'reason': 'disambiguation',  # or 'incomplete', 'error', 'user_marked'
      'notes': 'User notes here',
      'marked_at': '2026-02-21T10:00:00Z',
      'marked_by': 'user_name'  # optional
  }
  ```
- **Reasons:**
  - `disambiguation` - Disambiguation page detected
  - `incomplete` - Missing description or required fields
  - `error` - Error during processing
  - `user_marked` - User manually flagged
- **Visual Indicators:**
  - Streamlit: Badge/icon next to entry
  - HTML: CSS class `.needs-editing` with visual styling
  - Filter: "Show only entries needing editing"
- **Workflow:**
  - List all entries needing editing
  - Show reason and notes
  - Allow editing entry
  - Mark as resolved when done

**Implementation Notes:**
- Add `mark_entry_needs_editing()` method to `AmiEncyclopedia`
- Add `get_entries_needing_editing()` helper
- Update HTML generation to add `data-needs-editing` attribute
- Streamlit UI: Badge, filter, editing interface
- Auto-detect disambiguation pages (check Wikipedia page type)

**Integration with Other Features:**
- When adding from Wikipedia, auto-detect disambiguation pages
- When merging, preserve editing flags
- When deleting, remove editing flags

---

## Architecture Proposal

### Component Structure

```
encyclopedia/
├── core/
│   └── encyclopedia.py          # AmiEncyclopedia class (add methods)
├── browser/
│   ├── app.py                    # Streamlit UI (add editing tabs)
│   └── editing.py                # NEW: Editing utilities
├── cli/
│   └── versioned_editor.py       # CLI commands (add merge, etc.)
└── utils/
    └── editing_helpers.py         # NEW: Helper functions
```

### New Methods for `AmiEncyclopedia`

```python
class AmiEncyclopedia:
    # Delete
    def delete_entry(self, entry_id: str, soft: bool = True) -> bool
    def restore_entry(self, entry_id: str) -> bool
    def get_deleted_entries(self) -> List[Dict]
    
    # Hide
    def hide_entry(self, entry_id: str) -> bool
    def show_entry(self, entry_id: str) -> bool
    def get_hidden_entries(self) -> List[str]
    
    # Add from Wikipedia
    def add_entry_from_wikipedia(self, term: str, check_duplicates: bool = True) -> Dict
    def check_duplicate_entry(self, entry: Dict) -> Tuple[bool, Optional[Dict], str]
    
    # Merge
    def merge_encyclopedia(self, other: 'AmiEncyclopedia', 
                          conflict_resolution: Dict = None) -> Dict
    
    # Mark for editing
    def mark_entry_needs_editing(self, entry_id: str, reason: str, notes: str = "") -> bool
    def resolve_entry_editing(self, entry_id: str) -> bool
    def get_entries_needing_editing(self, reason: Optional[str] = None) -> List[Dict]
```

### Streamlit UI Structure

```
Streamlit Browser Tabs:
├── 🏠 Landing Page (existing)
├── 🔍 Search (existing)
├── 📖 Browse All (existing)
├── ✏️ Edit Entries (NEW)
│   ├── Delete Entries
│   ├── Hide/Show Entries
│   ├── Add from Wikipedia
│   └── Mark for Editing
├── 🔀 Merge Encyclopedias (NEW)
└── ⚙️ Settings (NEW)
    └── Show hidden entries
    └── Show deleted entries (for recovery)
```

### Data Persistence

**HTML Format:**
- Add `data-hidden="true"` attribute to hidden entries
- Add `data-needs-editing="true"` with `data-editing-reason="disambiguation"` attribute
- Store deleted entries in `metadata['deleted_entries']` (not in HTML, but in metadata JSON)
- Update `metadata['actions']` with all editing operations

**Metadata Structure:**
```json
{
  "metadata": {
    "hidden_entries": ["entry_id1", "entry_id2"],
    "deleted_entries": [
      {
        "entry_id": "entry_id3",
        "term": "Old Term",
        "deleted_at": "2026-02-21T10:00:00Z",
        "entry_data": {...}  // Full entry for recovery
      }
    ],
    "entries_needing_editing": [
      {
        "entry_id": "entry_id4",
        "reason": "disambiguation",
        "notes": "User notes",
        "marked_at": "2026-02-21T10:00:00Z"
      }
    ],
    "merge_operations": [
      {
        "source_file": "file1.html",
        "target_file": "file2.html",
        "merged_at": "2026-02-21T10:00:00Z",
        "entries_added": 10,
        "entries_merged": 5,
        "conflicts_resolved": 2
      }
    ]
  }
}
```

---

## Implementation Phases

### Phase 1: Core Infrastructure
1. ✅ Extend `AmiEncyclopedia` metadata structure
2. ✅ Add helper methods for entry manipulation
3. ✅ Update `save_wiki_normalized_html()` to handle hidden/editing flags
4. ✅ Add duplicate detection utilities

### Phase 2: Basic Editing (Streamlit)
1. ✅ Hide/Show entries UI
2. ✅ Delete entries UI (with confirmation)
3. ✅ Mark for editing UI
4. ✅ Filter by editing status

### Phase 3: Advanced Editing
1. ✅ Add from Wikipedia (with duplicate detection)
2. ✅ Entry editing interface (modify existing entries)
3. ✅ Batch operations (hide/delete multiple)

### Phase 4: Merge Functionality
1. ✅ Merge encyclopedias (CLI)
2. ✅ Merge encyclopedias (Streamlit UI)
3. ✅ Conflict resolution interface

### Phase 5: Polish & Integration
1. ✅ Undo/Redo functionality
2. ✅ Export/Import editing history
3. ✅ Statistics dashboard updates
4. ✅ Documentation

---

## Technical Challenges & Solutions

### Challenge 1: Entry Identification
**Problem:** How to uniquely identify entries for editing operations?

**Solution:**
- Use `entry_id` generated by `_generate_entry_id_from_entry()` (Wikidata ID or term-based)
- Store entry IDs in metadata lists
- Ensure IDs are stable across save/load cycles

### Challenge 2: Duplicate Detection
**Problem:** What constitutes a duplicate? (Same term? Same Wikidata ID? Same URL?)

**Solution:**
- Multi-level duplicate detection:
  1. Exact Wikidata ID match (highest priority)
  2. Exact term match (case-insensitive)
  3. Wikipedia URL match
  4. Similar term match (fuzzy, optional)
- Return match type so user can decide

### Challenge 3: Conflict Resolution
**Problem:** When merging, how to resolve conflicts automatically?

**Solution:**
- Default strategy: Prefer target encyclopedia
- User override: Show conflicts in UI, let user choose
- Batch mode: Use default strategy, log conflicts

### Challenge 4: Performance
**Problem:** Large encyclopedias (1000+ entries) may be slow to process.

**Solution:**
- Batch operations with progress indicators
- Lazy loading in Streamlit (paginate)
- Cache duplicate detection results
- Optimize HTML generation (only regenerate changed entries?)

### Challenge 5: Data Integrity
**Problem:** Ensure editing operations don't corrupt encyclopedia structure.

**Solution:**
- Validate entries before saving
- Backup before major operations (merge, batch delete)
- Transaction-like operations (all-or-nothing)
- Version control integration (optional)

---

## User Workflows

### Workflow 1: Clean Up Encyclopedia
1. Browse entries
2. Mark incomplete entries as "needing editing"
3. Hide entries temporarily for review
4. Delete unwanted entries
5. Save changes

### Workflow 2: Add New Entries
1. Search Wikipedia for term
2. Preview Wikipedia page
3. Check for duplicates
4. Add entry (or merge if duplicate)
5. Review and mark if needs editing

### Workflow 3: Merge Two Encyclopedias
1. Load source encyclopedia
2. Load target encyclopedia
3. Preview merge conflicts
4. Resolve conflicts (keep/replace/merge)
5. Execute merge
6. Review merged encyclopedia
7. Save result

### Workflow 4: Process Disambiguation Pages
1. Filter entries marked as "disambiguation"
2. Review each disambiguation page
3. Select correct meaning or add multiple entries
4. Resolve editing flag
5. Save changes

---

## Decisions Made (February 21, 2026)

1. **Delete vs Hide:** ✅ **Both** - Hide for temporary, delete for permanent
   - Hide: Temporary, reversible, entries remain searchable (if enabled)
   - Delete: Permanent (after confirmation period), entries removed from data

2. **Undo/Redo:** ✅ **Recovery from metadata first, undo/redo later**
   - Start with recovery from metadata (deleted entries stored for 30 days)
   - Add full undo/redo functionality in future phase

3. **Batch Operations:** ✅ **Batch creation and editing workflow**
   - Start with skeleton entries (term only)
   - Add Wikipedia content in batches
   - Resolve manual edits in batches
   - Support batch operations with progress indicators

4. **Conflict Resolution:** ✅ **Always ask user**
   - No automatic resolution
   - Show conflicts in UI with side-by-side comparison
   - User chooses: Keep target, Replace with source, Merge, Skip

5. **Editing Interface:** ✅ **Form-based**
   - Start with form-based editing (Streamlit forms)
   - Add rich/WYSIWYG editor later if needed

6. **Version Control:** ✅ **Version bump when saved to file**
   - Increment version in metadata when encyclopedia is saved
   - Track in `metadata['version']` field
   - Optional Git integration later

7. **HTML Browser Editing:** ✅ **Streamlit only, but...**
   - Editing always in Streamlit (requires server for persistence)
   - **HTML users marking files as needing editing:**
     - Challenge: No central server for HTML browser
     - **Proposed solution:** GitHub Issues integration
     - HTML browser could generate GitHub Issue URL with entry details
     - Or: Save editing flags to HTML metadata, sync via Git when file is committed
     - Or: Add comment/annotation system that saves to HTML file itself (readable by Streamlit)

---

## Implementation Plan (Based on Decisions)

### Phase 1: Core Infrastructure
1. ✅ Extend `AmiEncyclopedia` metadata structure
2. ✅ Add helper methods for entry manipulation
3. ✅ Update `save_wiki_normalized_html()` to handle hidden/editing flags
4. ✅ Add duplicate detection utilities
5. ✅ **Version bumping on save** - Increment version in metadata

### Phase 2: Basic Editing (Streamlit)
1. ✅ Hide/Show entries UI
2. ✅ Delete entries UI (with confirmation, soft delete first)
3. ✅ Mark for editing UI (form-based)
4. ✅ Filter by editing status
5. ✅ **Batch operations** - Start with skeleton entries, batch Wikipedia addition

### Phase 3: Advanced Editing
1. ✅ Add from Wikipedia (with duplicate detection, always ask on conflict)
2. ✅ Entry editing interface (form-based editing)
3. ✅ Batch operations (hide/delete multiple, batch Wikipedia addition)
4. ✅ **Recovery from metadata** - Restore deleted entries

### Phase 4: Merge Functionality
1. ✅ Merge encyclopedias (CLI)
2. ✅ Merge encyclopedias (Streamlit UI, always ask user on conflicts)
3. ✅ Conflict resolution interface (side-by-side comparison)

### Phase 5: HTML Browser Integration
1. ✅ **GitHub Issues integration** - Allow HTML users to mark entries needing editing
2. ✅ Or: HTML metadata comments that Streamlit can read
3. ✅ Export/Import editing history
4. ✅ Statistics dashboard updates
5. ✅ Documentation

### Phase 6: Future Enhancements
1. Full undo/redo functionality
2. Rich text editor (if needed)
3. Git integration for version control
4. Advanced batch processing workflows

## Next Steps

1. ✅ **Decisions made** - All questions answered
2. **Design UI mockups** - Sketch Streamlit interface layouts based on decisions
3. **Implement Phase 1** - Core infrastructure with version bumping
4. **Test with real data** - Use actual encyclopedia files
5. **Iterate based on feedback** - Refine based on user needs

---

## References

- `encyclopedia/core/encyclopedia.py` - Main encyclopedia class
- `encyclopedia/cli/versioned_editor.py` - Existing CLI editing
- `encyclopedia/browser/app.py` - Streamlit browser
- `amilib.wikimedia.WikipediaPage` - Wikipedia integration
- `docs/BROWSER_COMPARISON.md` - Browser options
