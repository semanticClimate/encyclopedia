# Encyclopedia Editing Quick Reference

**Date:** February 21, 2026 (system date)  
**Quick reference for editing encyclopedia entries**

## Python API

### Delete Entries

```python
from encyclopedia.core.encyclopedia import AmiEncyclopedia

# Load encyclopedia
encyclopedia = AmiEncyclopedia()
encyclopedia.create_from_html_file(Path("my_encyclopedia.html"))

# Get entry ID
entry_id = encyclopedia._generate_entry_id_from_entry(entry, index)

# Soft delete (recoverable)
encyclopedia.delete_entry(entry_id, soft=True)

# Hard delete (permanent)
encyclopedia.delete_entry(entry_id, soft=False)

# Restore deleted entry
encyclopedia.restore_entry(entry_id)

# List deleted entries
deleted = encyclopedia.get_deleted_entries()
```

### Hide/Show Entries

```python
# Hide entry
encyclopedia.hide_entry(entry_id)

# Show entry
encyclopedia.show_entry(entry_id)

# List hidden entries
hidden = encyclopedia.get_hidden_entries()
```

### Mark Needs Editing

```python
# Mark entry as needing editing
encyclopedia.mark_entry_needs_editing(
    entry_id, 
    reason="disambiguation",  # or "incomplete", "error", "user_marked"
    notes="Optional notes"
)

# Resolve editing flag
encyclopedia.resolve_entry_editing(entry_id)

# Get entries needing editing
needing_editing = encyclopedia.get_entries_needing_editing()

# Filter by reason
disambiguation = encyclopedia.get_entries_needing_editing(reason="disambiguation")
```

### Add From Wikipedia

```python
# Add entry from Wikipedia
result = encyclopedia.add_entry_from_wikipedia("quantum mechanics", check_duplicates=True)

if result.get('added'):
    print(f"Added: {result['entry']['term']}")
elif result.get('is_duplicate'):
    print(f"Duplicate: {result['existing_entry']['term']}")
elif result.get('error'):
    print(f"Error: {result['error']}")

# Check for duplicate
is_dup, existing, match_type = encyclopedia.check_duplicate_entry(new_entry)
```

### Merge Encyclopedias

```python
# Load source encyclopedia
source = AmiEncyclopedia()
source.create_from_html_file(Path("source.html"))

# Merge (no conflict resolution)
result = encyclopedia.merge_encyclopedia(source)

# Merge with conflict resolution
conflict_resolution = {
    "term1": "keep_target",      # Keep existing entry
    "term2": "replace_with_source",  # Replace with source
    "term3": "merge",            # Combine entries
    "term4": "skip"              # Skip source entry
}
result = encyclopedia.merge_encyclopedia(source, conflict_resolution=conflict_resolution)

print(f"Added: {result['entries_added']}")
print(f"Merged: {result['entries_merged']}")
print(f"Conflicts: {len(result['conflicts'])}")
```

### Save Encyclopedia

```python
# Save (version automatically bumped)
encyclopedia.save_wiki_normalized_html(Path("output.html"))
```

## Command-Line Scripts

### Delete Entries

```bash
# List entries
python Examples/edit_encyclopedia_delete.py --input in.html --output out.html

# Delete entry
python Examples/edit_encyclopedia_delete.py --input in.html --output out.html --entry-id <id>

# Hard delete
python Examples/edit_encyclopedia_delete.py --input in.html --output out.html --entry-id <id> --hard

# List deleted
python Examples/edit_encyclopedia_delete.py --input in.html --output out.html --list-deleted

# Restore
python Examples/edit_encyclopedia_delete.py --input in.html --output out.html --restore <id>
```

### Hide/Show

```bash
# Hide
python Examples/edit_encyclopedia_hide.py --input in.html --output out.html --hide <id>

# Show
python Examples/edit_encyclopedia_hide.py --input in.html --output out.html --show <id>

# List hidden
python Examples/edit_encyclopedia_hide.py --input in.html --output out.html --list-hidden
```

### Mark Needs Editing

```bash
# Mark entry
python Examples/edit_encyclopedia_mark_needs_editing.py --input in.html --output out.html \
    --entry-id <id> --reason disambiguation --notes "Notes"

# List entries needing editing
python Examples/edit_encyclopedia_mark_needs_editing.py --input in.html --output out.html --list

# Filter by reason
python Examples/edit_encyclopedia_mark_needs_editing.py --input in.html --output out.html \
    --list --filter-reason disambiguation

# Resolve
python Examples/edit_encyclopedia_mark_needs_editing.py --input in.html --output out.html --resolve <id>
```

### Add From Wikipedia

```bash
# Add entry
python Examples/edit_encyclopedia_add_from_wikipedia.py --input in.html --output out.html \
    --term "quantum mechanics"
```

### Merge

```bash
# Merge
python Examples/edit_encyclopedia_merge.py --target target.html --source source.html --output merged.html

# With conflict resolution
python Examples/edit_encyclopedia_merge.py --target target.html --source source.html \
    --output merged.html --conflicts-file conflicts.json
```

## Jupyter Notebook

```bash
# Open tutorial
jupyter notebook docs/tutorials/ENCYCLOPEDIA_EDITING_TUTORIAL.ipynb
```

## Common Patterns

### Batch Operations

```python
# Hide multiple entries
for entry in entries_to_hide:
    entry_id = encyclopedia._generate_entry_id_from_entry(entry, index)
    encyclopedia.hide_entry(entry_id)

# Mark multiple entries
for entry in entries_to_mark:
    entry_id = encyclopedia._generate_entry_id_from_entry(entry, index)
    encyclopedia.mark_entry_needs_editing(entry_id, "incomplete", "Missing description")
```

### Workflow: Clean Up Encyclopedia

```python
# 1. Mark incomplete entries
for entry in encyclopedia.entries:
    if not entry.get('description_html'):
        entry_id = encyclopedia._generate_entry_id_from_entry(entry, index)
        encyclopedia.mark_entry_needs_editing(entry_id, "incomplete", "Missing description")

# 2. Hide entries temporarily
for entry in entries_to_review:
    entry_id = encyclopedia._generate_entry_id_from_entry(entry, index)
    encyclopedia.hide_entry(entry_id)

# 3. Delete unwanted entries
for entry in entries_to_delete:
    entry_id = encyclopedia._generate_entry_id_from_entry(entry, index)
    encyclopedia.delete_entry(entry_id, soft=False)

# 4. Save
encyclopedia.save_wiki_normalized_html(Path("cleaned.html"))
```

### Workflow: Add New Entries

```python
# Add entries from wordlist
terms = ["term1", "term2", "term3"]

for term in terms:
    result = encyclopedia.add_entry_from_wikipedia(term, check_duplicates=True)
    
    if result.get('added'):
        print(f"✓ Added: {term}")
    elif result.get('is_duplicate'):
        print(f"⚠ Duplicate: {term}")
    elif result.get('error'):
        print(f"✗ Error: {term} - {result['error']}")

# Save
encyclopedia.save_wiki_normalized_html(Path("updated.html"))
```

## See Also

- **Full Tutorial:** `docs/tutorials/ENCYCLOPEDIA_EDITING_TUTORIAL.ipynb`
- **Implementation Details:** `docs/EDITING_IMPLEMENTATION_SUMMARY.md`
- **Method Documentation:** `docs/MISSING_METHODS.md`
- **Proposal:** `docs/EDITING_TOOLS_PROPOSAL.md`
