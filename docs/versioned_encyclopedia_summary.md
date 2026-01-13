# Versioned Incremental Encyclopedia - Quick Summary

**Date:** 2026-01-12  
**Full Design:** See `versioned_encyclopedia_design.md`

## Overview

Design for a versioned, incremental encyclopedia system that supports Wikipedia-like versioning, incremental building, and collaborative editing - all stored in a single HTML file.

## Key Features

1. **Entry-Level Versioning**: Each entry maintains its own version history
2. **Incremental Processing**: Process entries in batches (e.g., 100 at a time)
3. **Resume Capability**: "Carry on from where we left off"
4. **Serverless**: All state in HTML file (no database)
5. **CSS Hiding**: Hide entries for easy re-instatement
6. **Generic Feature System**: Extensible features (not hardcoded - Wikipedia, GBIF, etc. are examples)
7. **Daily Git Commits**: Multiple edits per day, commit once per day
8. **Branch-Based Work**: Separate Git branches for different encyclopedias
9. **Future Merging**: Support for merging personal encyclopedias

## Architecture

### Entry State Tracking

Each entry tracks:
- **Status**: `unprocessed`, `processing`, `processed`, `skipped`, `hidden`
- **Features**: Which features have been added (`wikipedia`, `gbif`, etc.)
- **Version**: Current version number
- **History**: JSON array of all changes
- **Timestamps**: When last edited, by whom

### Global State

Stored in `data-metadata` attribute:
- Total entries, processed count, unprocessed count
- Last session info (where we left off)
- Feature tracking
- Global version number

## Example Entry

```html
<div role="ami_entry"
     data-entry-id="Q7942"
     data-status="processed"
     data-processed-features="wikipedia,wikidata"
     data-version="3"
     data-history='[{"version":1,"action":"created",...}]'
     term="climate change">
  <!-- Entry content -->
</div>
```

## Update Strategies

### 1. Display Next Unedited Entry
```python
entry = encyclopedia.get_next_unprocessed_entry()
# Show entry with editing interface
```

### 2. Batch Process Feature (Generic)
```python
# Generic feature processing (not hardcoded)
def add_wikipedia_handler(entry):
    # Add Wikipedia description to entry
    pass

encyclopedia.process_batch(
    batch_size=100, 
    feature='wikipedia',
    feature_handler=add_wikipedia_handler
)
```

### 3. Add Feature to Unprocessed (Generic)
```python
# Any feature can be added - not hardcoded
def add_custom_feature_handler(entry):
    # Add custom feature data (e.g., GBIF, EOL, iNaturalist, etc.)
    pass

encyclopedia.process_feature('custom_feature', add_custom_feature_handler, limit=50)
```

## Git Workflow

- **Daily Commits**: Users make multiple edits during the day, commit once per day
- **Separate Branches**: Each encyclopedia on its own Git branch
- **No Complex Merges**: Different encyclopedias = different branches
- **Future**: Merge personal encyclopedias using merge tools

## Open Source Approaches Considered

1. **Git-Based**: Use Git for versioning (requires Git)
2. **MediaWiki-Style**: Store versions inline (recommended)
3. **JSON Patch**: Store changes as patches
4. **Operational Transformation**: For collaborative editing

## Recommended Approach

**Hybrid**: Entry-level history in HTML + optional Git backup
- Primary: Self-contained HTML with entry history
- Backup: Git for full file snapshots

## Implementation Status

**Design Complete** - Ready for implementation

See full design document for:
- Detailed API design
- Implementation phases
- Code examples
- Migration path
