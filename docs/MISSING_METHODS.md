# Missing Methods in AmiEncyclopedia

**Date:** February 21, 2026 (system date)  
**Status:** Methods Required for Editing Tools Implementation

## Overview

This document lists all methods that need to be implemented in `AmiEncyclopedia` class to support the editing tools functionality. These methods are referenced in the test files but do not yet exist.

## Missing Methods

### Delete Functionality

#### 1. `delete_entry(entry_id: str, soft: bool = True) -> bool`
**Purpose:** Delete an entry from the encyclopedia.

**Parameters:**
- `entry_id`: Unique identifier for the entry to delete
- `soft`: If True, mark as deleted in metadata (recoverable). If False, remove from entries list.

**Returns:**
- `bool`: True if entry was deleted, False if entry not found

**Behavior:**
- Soft delete: Adds entry to `metadata['deleted_entries']` with full entry data for recovery
- Hard delete: Removes entry from `entries` list AND adds to `metadata['deleted_entries']`
- Updates `metadata['actions']` with deletion action
- Updates `metadata['last_edited']` timestamp

**Used in:** `test_editing_delete.py`

---

#### 2. `restore_entry(entry_id: str) -> bool`
**Purpose:** Restore a deleted entry.

**Parameters:**
- `entry_id`: Unique identifier for the entry to restore

**Returns:**
- `bool`: True if entry was restored, False if entry not found in deleted_entries

**Behavior:**
- Removes entry from `metadata['deleted_entries']`
- If entry was hard-deleted, adds it back to `entries` list
- Updates `metadata['actions']` with restore action
- Updates `metadata['last_edited']` timestamp

**Used in:** `test_editing_delete.py`

---

#### 3. `get_deleted_entries() -> List[Dict]`
**Purpose:** Get list of all deleted entries.

**Returns:**
- `List[Dict]`: List of deleted entry dictionaries from `metadata['deleted_entries']`

**Behavior:**
- Returns list of deleted entries with their metadata (entry_id, term, deleted_at, entry_data)

**Used in:** `test_editing_delete.py`

---

### Hide Functionality

#### 4. `hide_entry(entry_id: str) -> bool`
**Purpose:** Hide an entry (temporary, reversible).

**Parameters:**
- `entry_id`: Unique identifier for the entry to hide

**Returns:**
- `bool`: True if entry was hidden, False if entry not found

**Behavior:**
- Adds entry_id to `metadata['hidden_entries']` list
- Updates `metadata['actions']` with hide action
- Updates `metadata['last_edited']` timestamp
- Entry remains in `entries` list (not deleted)

**Used in:** `test_editing_hide.py`

---

#### 5. `show_entry(entry_id: str) -> bool`
**Purpose:** Show a hidden entry (remove from hidden list).

**Parameters:**
- `entry_id`: Unique identifier for the entry to show

**Returns:**
- `bool`: True if entry was shown, False if entry not found in hidden_entries

**Behavior:**
- Removes entry_id from `metadata['hidden_entries']` list
- Updates `metadata['actions']` with show action
- Updates `metadata['last_edited']` timestamp

**Used in:** `test_editing_hide.py`

---

#### 6. `get_hidden_entries() -> List[str]`
**Purpose:** Get list of hidden entry IDs.

**Returns:**
- `List[str]`: List of entry IDs from `metadata['hidden_entries']`

**Behavior:**
- Returns list of entry IDs that are currently hidden

**Used in:** `test_editing_hide.py`

---

### Mark Needs Editing Functionality

#### 7. `mark_entry_needs_editing(entry_id: str, reason: str, notes: str = "") -> bool`
**Purpose:** Mark an entry as needing editing.

**Parameters:**
- `entry_id`: Unique identifier for the entry
- `reason`: Reason code ("disambiguation", "incomplete", "error", "user_marked")
- `notes`: Optional notes about why it needs editing

**Returns:**
- `bool`: True if entry was marked, False if entry not found

**Behavior:**
- Adds `needs_editing` dict to entry with:
  - `flag`: True
  - `reason`: reason string
  - `notes`: notes string
  - `marked_at`: timestamp (system date)
- Updates `metadata['actions']` with mark action
- Updates `metadata['last_edited']` timestamp

**Used in:** `test_editing_mark_needs_editing.py`

---

#### 8. `resolve_entry_editing(entry_id: str) -> bool`
**Purpose:** Resolve editing flag (mark as no longer needing editing).

**Parameters:**
- `entry_id`: Unique identifier for the entry

**Returns:**
- `bool`: True if entry was resolved, False if entry not found or not marked

**Behavior:**
- Sets `needs_editing['flag']` to False or removes `needs_editing` from entry
- Updates `metadata['actions']` with resolve action
- Updates `metadata['last_edited']` timestamp

**Used in:** `test_editing_mark_needs_editing.py`

---

#### 9. `get_entries_needing_editing(reason: Optional[str] = None) -> List[Dict]`
**Purpose:** Get list of entries that need editing.

**Parameters:**
- `reason`: Optional filter by reason (if None, returns all entries needing editing)

**Returns:**
- `List[Dict]`: List of entry dictionaries that need editing

**Behavior:**
- Filters entries where `needs_editing['flag']` is True
- If reason provided, filters by `needs_editing['reason']`
- Returns full entry dictionaries

**Used in:** `test_editing_mark_needs_editing.py`

---

### Add From Wikipedia Functionality

#### 10. `add_entry_from_wikipedia(term: str, check_duplicates: bool = True) -> Dict`
**Purpose:** Add a new entry by searching Wikipedia.

**Parameters:**
- `term`: Search term for Wikipedia
- `check_duplicates`: If True, check for duplicates before adding

**Returns:**
- `Dict`: Dictionary with:
  - `added`: bool - Whether entry was added
  - `is_duplicate`: bool - Whether duplicate was detected
  - `existing_entry`: Dict or None - Existing entry if duplicate
  - `match_type`: str or None - Type of duplicate match ("wikidata_id", "term", "url")
  - `error`: str or None - Error message if failed
  - `entry`: Dict or None - New entry if added

**Behavior:**
- Searches Wikipedia using `WikipediaPage.lookup_wikipedia_page_for_term()`
- If duplicate detected and `check_duplicates=True`, returns duplicate info without adding
- Creates entry dictionary with Wikipedia content
- Adds entry to `entries` list
- If disambiguation page detected, auto-marks as needing editing
- Updates `metadata['actions']` with add action
- Updates `metadata['last_edited']` timestamp

**Used in:** `test_editing_add_from_wikipedia.py`

---

#### 11. `check_duplicate_entry(entry: Dict) -> Tuple[bool, Optional[Dict], str]`
**Purpose:** Check if an entry is a duplicate of an existing entry.

**Parameters:**
- `entry`: Entry dictionary to check

**Returns:**
- `Tuple[bool, Optional[Dict], str]`: 
  - `is_duplicate`: bool - Whether duplicate was found
  - `existing_entry`: Dict or None - Existing entry if duplicate found
  - `match_type`: str - Type of match ("wikidata_id", "term", "url", or "")

**Behavior:**
- Checks for duplicates in this order:
  1. Exact Wikidata ID match (highest priority)
  2. Exact term match (case-insensitive)
  3. Wikipedia URL match
- Returns first match found

**Used in:** `test_editing_add_from_wikipedia.py`

---

### Merge Functionality

#### 12. `merge_encyclopedia(other: 'AmiEncyclopedia', conflict_resolution: Optional[Dict] = None) -> Dict`
**Purpose:** Merge another encyclopedia into this one.

**Parameters:**
- `other`: AmiEncyclopedia instance to merge FROM
- `conflict_resolution`: Optional dict mapping term -> strategy ("keep_target", "replace_with_source", "merge", "skip")

**Returns:**
- `Dict`: Dictionary with merge results:
  - `entries_added`: int - Number of new entries added
  - `entries_merged`: int - Number of entries merged (same Wikidata ID)
  - `conflicts`: List[Dict] - List of conflicts detected
  - `resolved_conflicts`: List[Dict] - List of conflicts resolved
  - `merge_operations`: List[Dict] - History of merge operations

**Behavior:**
- For each entry in `other.entries`:
  - Check for duplicates using `check_duplicate_entry()`
  - If duplicate found:
    - Same Wikidata ID: Merge synonyms, keep best description
    - Same term, different Wikidata ID: Conflict (use conflict_resolution or ask user)
    - Different term, same Wikidata ID: Merge as synonyms
  - If no duplicate: Add entry to this encyclopedia
- Merge metadata:
  - Merge `hidden_entries` lists
  - Merge `deleted_entries` lists
  - Merge `actions` lists
  - Add merge operation to `merge_operations`
- Updates `metadata['last_edited']` timestamp

**Used in:** `test_editing_merge.py`

---

## Helper Methods (May Already Exist)

### `_generate_entry_id_from_entry(entry: Dict, index: int) -> str`
**Status:** ✅ EXISTS (line 1345 in encyclopedia.py)

**Purpose:** Generate unique entry ID from entry dictionary.

**Used in:** All test files

---

## Metadata Structure Updates Needed

### New Metadata Fields

The following metadata fields need to be added to `_create_metadata()`:

```python
METADATA_DELETED_ENTRIES = "deleted_entries"  # NEW
METADATA_ENTRIES_NEEDING_EDITING = "entries_needing_editing"  # NEW (or store in entry dict)
```

### Metadata Structure

```python
metadata = {
    # ... existing fields ...
    'deleted_entries': [
        {
            'entry_id': str,
            'term': str,
            'deleted_at': str,  # ISO 8601 timestamp
            'entry_data': Dict,  # Full entry dictionary for recovery
            'deleted_by': str  # Optional user identifier
        }
    ],
    'hidden_entries': [str],  # List of entry IDs (already exists)
    'merge_operations': [
        {
            'source_file': str,
            'target_file': str,
            'merged_at': str,  # ISO 8601 timestamp
            'entries_added': int,
            'entries_merged': int,
            'conflicts_resolved': int
        }
    ]
}
```

### Entry Dictionary Structure Updates

Entries may have:
```python
entry = {
    # ... existing fields ...
    'needs_editing': {
        'flag': bool,
        'reason': str,  # "disambiguation", "incomplete", "error", "user_marked"
        'notes': str,
        'marked_at': str  # ISO 8601 timestamp
    }
}
```

---

## HTML Output Updates Needed

### Attributes to Add to Entry Divs

When saving HTML, entry divs should have:

```html
<div role="ami_entry" 
     data-entry-id="entry_id"
     data-hidden="true"  <!-- if entry is hidden -->
     data-needs-editing="true"  <!-- if entry needs editing -->
     data-editing-reason="disambiguation">  <!-- reason if needs editing -->
```

---

## Action Constants Needed

Add to existing action constants:

```python
ACTION_DELETE = "delete"
ACTION_RESTORE = "restore"
ACTION_SHOW = "show"  # (ACTION_HIDE already exists)
ACTION_MARK_NEEDS_EDITING = "mark_needs_editing"
ACTION_RESOLVE_EDITING = "resolve_editing"
ACTION_ADD_FROM_WIKIPEDIA = "add_from_wikipedia"
ACTION_MERGE = "merge"
```

---

## Summary

**Total Missing Methods:** 12

1. `delete_entry()` - Delete entry (soft/hard)
2. `restore_entry()` - Restore deleted entry
3. `get_deleted_entries()` - Get deleted entries list
4. `hide_entry()` - Hide entry
5. `show_entry()` - Show hidden entry
6. `get_hidden_entries()` - Get hidden entries list
7. `mark_entry_needs_editing()` - Mark entry as needing editing
8. `resolve_entry_editing()` - Resolve editing flag
9. `get_entries_needing_editing()` - Get entries needing editing
10. `add_entry_from_wikipedia()` - Add entry from Wikipedia search
11. `check_duplicate_entry()` - Check for duplicate entry
12. `merge_encyclopedia()` - Merge another encyclopedia

**Helper Method:** `_generate_entry_id_from_entry()` ✅ EXISTS

**Metadata Updates:** Add `deleted_entries` field, update `merge_operations` structure

**HTML Output Updates:** Add `data-hidden`, `data-needs-editing`, `data-editing-reason` attributes

**Action Constants:** Add 6 new action constants
