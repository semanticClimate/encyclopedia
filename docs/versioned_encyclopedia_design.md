# Versioned Incremental Encyclopedia System - Design Document

**Date:** 2026-01-12  
**Status:** Design Proposal  
**Author:** Encyclopedia Team

## Executive Summary

This document proposes a design for a versioned, incremental encyclopedia system that supports:
- Wikipedia-like versioning and revert capabilities
- Incremental building (e.g., 100 words per session)
- "Carry on from where we left off" functionality
- Serverless operation (all state in HTML file)
- Entry-level history and state management
- Multiple update strategies

## Requirements

### Core Requirements

1. **Versioning**: Wikipedia-like versioning with ability to revert without complex systems
2. **Incremental Building**: Process entries in batches (e.g., 10 sessions of 100 words each)
3. **Resume Capability**: "Carry on from where we left off" - track progress across sessions
4. **Serverless**: All state stored in the HTML file itself (no database, no server)
5. **Entry Omission**: Entries can be hidden via CSS for easy re-instatement
6. **Entry History**: Each entry can maintain its own version history
7. **Update Strategies**: Support multiple ways to update entries:
   - Display next unedited entry for manual editing
   - Add Wikipedia descriptions for unedited entries
   - Add external data sources (e.g., GBIF, EOL, iNaturalist) - extensible, not hardcoded
   - Other future enhancements

### Use Cases

1. **Batch Processing**: Process 1000 words in 10 sessions of 100 words each
2. **Manual Editing**: Edit entries one at a time with checkboxes
3. **Feature Addition**: Add features incrementally (e.g., Wikipedia descriptions, then external data sources)
4. **Daily Workflow**: Users make multiple edits during the day, commit once per day
5. **Branch-Based Work**: Users work on separate Git branches for different encyclopedias (no complex merges needed)
6. **Personal Encyclopedia Merging**: Merge multiple personal encyclopedias into one (future requirement)
7. **Revert Changes**: Undo changes to individual entries or entire encyclopedia

## Architecture Overview

### Design Principles

1. **Self-Contained**: All state in HTML file (no external dependencies)
2. **Git-Like Versioning**: Simple, linear version history per entry
3. **CSS-Based Hiding**: Use CSS classes/attributes for hiding entries
4. **Attribute-Based State**: Use HTML data attributes for state tracking
5. **Incremental Processing**: Track processing status per entry
6. **History Embedded**: Entry history stored in entry element itself

### System Components

```
┌─────────────────────────────────────────────────────────┐
│              Encyclopedia HTML File                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Metadata Section (data-metadata attribute)      │  │
│  │  - Global version number                           │  │
│  │  - Processing state                               │  │
│  │  - Last session info                             │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Entry Elements (div[role="ami_entry"])            │  │
│  │  - Entry content                                  │  │
│  │  - Processing status (data-status)                 │  │
│  │  - Version history (data-history)                 │  │
│  │  - Hidden state (class="hidden")                 │  │
│  │  - Last edited timestamp                          │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Data Model

### Entry State Attributes

Each entry (`div[role="ami_entry"]`) will have:

```html
<div role="ami_entry"
     data-entry-id="Q12345"
     data-status="unprocessed"           <!-- unprocessed | processing | processed | skipped -->
     data-processed-features="wikipedia" <!-- comma-separated list -->
     data-last-edited="2026-01-12T10:30:00Z"
     data-editor="user@example.com"
     data-version="3"
     data-history='[{"version":1,"timestamp":"...","action":"created"},...]'
     class="entry processed wikipedia-added">
  <!-- Entry content -->
</div>
```

### Processing Status Values

- `unprocessed`: Entry hasn't been processed yet
- `processing`: Currently being processed (prevents duplicate processing)
- `processed`: Fully processed
- `skipped`: User skipped this entry
- `hidden`: Entry is hidden (via CSS class)

### Feature Flags

Track which features have been added (extensible, not hardcoded):
- `wikipedia`: Wikipedia description added
- `wikidata`: Wikidata data added
- `images`: Images added
- `citations`: Citations added
- `[custom]`: Any custom feature name (e.g., `gbif`, `eol`, `inaturalist`, etc.)

### Entry History Format

```json
[
  {
    "version": 1,
    "timestamp": "2026-01-12T10:00:00Z",
    "action": "created",
    "editor": "user@example.com",
    "changes": {
      "term": "climate change",
      "wikipedia_url": "https://en.wikipedia.org/wiki/Climate_change"
    }
  },
  {
    "version": 2,
    "timestamp": "2026-01-12T11:00:00Z",
    "action": "added_wikipedia",
    "editor": "user@example.com",
    "changes": {
      "description_html": "<p>Climate change is...</p>"
    }
  },
  {
    "version": 3,
    "timestamp": "2026-01-12T12:00:00Z",
    "action": "added_feature",
    "feature": "gbif",
    "editor": "user@example.com",
    "changes": {
      "gbif_id": "12345",
      "gbif_data": {...}
    }
  }
]
```

### Global Metadata Format

Stored in `data-metadata` attribute of encyclopedia container:

```json
{
  "version": 5,
  "created": "2026-01-10T09:00:00Z",
  "last_edited": "2026-01-12T15:30:00Z",
  "last_session": {
    "date": "2026-01-12T15:30:00Z",
    "entries_processed": 100,
    "last_entry_id": "Q12345",
    "session_id": "session_20260112_153000"
  },
  "processing_state": {
    "total_entries": 1000,
    "unprocessed": 750,
    "processed": 200,
    "skipped": 50,
    "current_batch_start": 200,
    "current_batch_size": 100
  },
  "features": {
    "wikipedia": {"enabled": true, "entries_with": 200},
    "wikidata": {"enabled": true, "entries_with": 150},
    "images": {"enabled": false, "entries_with": 0}
    // Features are extensible - any feature name can be added
  },
  "history": [
    {
      "version": 1,
      "timestamp": "2026-01-10T09:00:00Z",
      "action": "created",
      "entries_count": 1000
    }
  ]
}
```

## Versioning Strategy

### Entry-Level Versioning

Each entry maintains its own version number and history:

1. **Version Increment**: Version increments on any change
2. **History Storage**: Full history stored in `data-history` attribute (JSON)
3. **Revert Capability**: Can revert to any previous version
4. **Diff Storage**: Store diffs (what changed) not full copies

### Global Versioning

1. **Global Version**: Increments on any entry change
2. **Snapshot Capability**: Can create snapshots at any point
3. **Change Log**: Track major changes in global metadata

### Revert Mechanisms

#### Option 1: Entry-Level Revert (Recommended)

```python
def revert_entry(entry_element, target_version):
    """Revert entry to specific version"""
    history = json.loads(entry_element.get('data-history', '[]'))
    
    # Find target version
    target = next((h for h in history if h['version'] == target_version), None)
    if not target:
        raise ValueError(f"Version {target_version} not found")
    
    # Apply changes in reverse order from current to target
    current_version = int(entry_element.get('data-version', 1))
    for version in range(current_version, target_version, -1):
        # Undo changes for this version
        pass
    
    # Update entry
    entry_element.set('data-version', str(target_version))
    # Update content based on target version
```

#### Option 2: Snapshot-Based Revert

Create periodic snapshots of entire encyclopedia:

```python
def create_snapshot(encyclopedia_html):
    """Create snapshot of current state"""
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "version": get_global_version(encyclopedia_html),
        "entries": extract_all_entries(encyclopedia_html)
    }
    return snapshot

def revert_to_snapshot(encyclopedia_html, snapshot):
    """Revert entire encyclopedia to snapshot"""
    # Replace all entries with snapshot entries
    pass
```

## Incremental Processing

### "Carry On From Where We Left Off"

Track processing state in global metadata:

```python
def get_next_unprocessed_entry(encyclopedia_html):
    """Get next unprocessed entry"""
    entries = encyclopedia_html.xpath(".//div[@role='ami_entry']")
    
    # Find first unprocessed entry
    for entry in entries:
        status = entry.get('data-status', 'unprocessed')
        if status == 'unprocessed':
            return entry
    
    return None

def mark_entry_processing(entry_element):
    """Mark entry as currently being processed"""
    entry_element.set('data-status', 'processing')
    entry_element.set('data-processing-started', datetime.now().isoformat())

def mark_entry_processed(entry_element, features_added=None):
    """Mark entry as processed"""
    entry_element.set('data-status', 'processed')
    if features_added:
        current_features = entry_element.get('data-processed-features', '').split(',')
        current_features.extend(features_added)
        entry_element.set('data-processed-features', ','.join(set(current_features)))
    
    # Increment version
    current_version = int(entry_element.get('data-version', 1))
    entry_element.set('data-version', str(current_version + 1))
    
    # Add to history
    add_history_entry(entry_element, 'processed', features_added)
```

### Batch Processing

```python
def process_batch(encyclopedia_html, batch_size=100, feature='wikipedia'):
    """Process next batch of entries"""
    unprocessed = get_unprocessed_entries(encyclopedia_html, limit=batch_size)
    
    for entry in unprocessed:
        mark_entry_processing(entry)
        
        # Process entry (e.g., add Wikipedia description)
        if feature == 'wikipedia':
            add_wikipedia_description(entry)
        elif feature == 'gbif':
            add_gbif_data(entry)
        
        mark_entry_processed(entry, features_added=[feature])
    
    # Update global metadata
    update_processing_state(encyclopedia_html)
    save_encyclopedia(encyclopedia_html)
```

## CSS-Based Hiding

### Implementation

```css
/* Hidden entries */
div[role="ami_entry"].hidden {
    display: none;
}

/* Or use data attribute */
div[role="ami_entry"][data-hidden="true"] {
    display: none;
}

/* Entry status indicators */
div[role="ami_entry"][data-status="unprocessed"] {
    border-left: 4px solid #ffc107; /* Yellow - needs processing */
}

div[role="ami_entry"][data-status="processed"] {
    border-left: 4px solid #28a745; /* Green - processed */
}

div[role="ami_entry"][data-status="skipped"] {
    border-left: 4px solid #6c757d; /* Gray - skipped */
    opacity: 0.6;
}
```

### Hide/Show Operations

```python
def hide_entry(entry_element, reason="user_hidden"):
    """Hide entry via CSS"""
    entry_element.set('class', f"{entry_element.get('class', '')} hidden")
    entry_element.set('data-hidden', 'true')
    entry_element.set('data-hide-reason', reason)
    
    # Add to history
    add_history_entry(entry_element, 'hidden', {'reason': reason})

def show_entry(entry_element):
    """Show hidden entry"""
    classes = entry_element.get('class', '').replace('hidden', '').strip()
    entry_element.set('class', classes)
    entry_element.set('data-hidden', 'false')
    
    # Add to history
    add_history_entry(entry_element, 'shown', {})
```

## Update Strategies

### Strategy 1: Display Next Unedited Entry

```python
class EntryEditor:
    """Editor for processing entries one at a time"""
    
    def get_next_entry(self, encyclopedia_html):
        """Get next unprocessed entry"""
        entries = encyclopedia_html.xpath(".//div[@role='ami_entry']")
        
        for entry in entries:
            status = entry.get('data-status', 'unprocessed')
            if status == 'unprocessed' and not self.is_hidden(entry):
                return entry
        
        return None
    
    def display_entry_for_editing(self, entry_element):
        """Display entry with editing interface"""
        # Show entry with checkboxes
        # Allow user to:
        # - Add Wikipedia description
        # - Skip entry
        # - Hide entry
        # - Add other features
        pass
```

### Strategy 2: Add Wikipedia Descriptions for Unprocessed Entries

```python
def add_wikipedia_for_unprocessed(encyclopedia_html, limit=100):
    """Add Wikipedia descriptions for unprocessed entries"""
    unprocessed = get_unprocessed_entries(encyclopedia_html, limit=limit)
    
    for entry in unprocessed:
        term = entry.get('term', '')
        if not term:
            continue
        
        # Lookup Wikipedia
        wikipedia_page = lookup_wikipedia(term)
        if wikipedia_page:
            # Add description
            description_elem = ET.SubElement(entry, 'div')
            description_elem.set('class', 'wikipedia-description')
            description_elem.text = wikipedia_page.first_paragraph
            
            # Update entry
            mark_entry_processed(entry, features_added=['wikipedia'])
            add_history_entry(entry, 'added_feature', {
                'feature': 'wikipedia',
                'wikipedia_url': wikipedia_page.url
            })
    
    # Save
    save_encyclopedia(encyclopedia_html)
```

### Strategy 3: Feature-Specific Processing (Generic)

```python
def process_feature(encyclopedia_html, feature_name, feature_handler, limit=None):
    """Process specific feature for unprocessed entries
    
    Args:
        feature_name: Name of feature (e.g., 'wikipedia', 'gbif', 'images')
        feature_handler: Function that takes entry element and adds feature
        limit: Maximum number of entries to process
    """
    entries = get_entries_missing_feature(encyclopedia_html, feature_name, limit)
    
    for entry in entries:
        # Call feature handler to add the feature
        feature_handler(entry)
        
        # Mark as processed with this feature
        mark_entry_processed(entry, features_added=[feature_name])
        add_history_entry(entry, 'added_feature', {
            'feature': feature_name
        })
    
    save_encyclopedia(encyclopedia_html)

# Example usage:
def add_gbif_handler(entry):
    """Handler for adding GBIF data"""
    term = entry.get('term', '')
    gbif_data = lookup_gbif(term)
    if gbif_data:
        # Add GBIF data to entry
        pass

# Process GBIF feature
process_feature(encyclopedia_html, 'gbif', add_gbif_handler, limit=100)
```

## Open Source Approaches

### 1. Git-Based Versioning

**Approach**: Use Git to version the HTML file

**Pros**:
- Well-established version control
- Built-in diff and merge
- Easy revert
- Branching support
- Users work on separate branches (different encyclopedias)
- Daily commits (once per day after multiple edits)

**Cons**:
- Requires Git installation
- Not self-contained (needs .git directory)
- Binary-like HTML files don't diff well

**Usage Pattern**:
- Users make multiple edits during the day
- Commit once per day: `git commit -m "Daily update: processed 100 entries"`
- Work on separate branches for different encyclopedias
- No complex merges needed (different encyclopedias = different branches)

**Implementation**:
```python
import subprocess

def save_with_version(encyclopedia_file, commit_message=None):
    """Save encyclopedia file
    
    Note: Git commits are done manually by users once per day,
    not automatically per save.
    """
    # Save file
    encyclopedia_file.write_text(html_content)
    
    # Optional: Stage for commit (user commits manually)
    if commit_message:
        subprocess.run(['git', 'add', str(encyclopedia_file)])
        # User commits manually: git commit -m "Daily update"
```

### 2. MediaWiki-Style Versioning

**Approach**: Store versions inline in HTML (like MediaWiki)

**Pros**:
- Self-contained
- No external dependencies
- Easy to implement

**Cons**:
- File size grows with history
- Slower to parse

**Implementation**: Store history in `data-history` attribute (as proposed above)

### 3. JSON Patch / RFC 6902

**Approach**: Store changes as JSON Patch operations

**Pros**:
- Standard format
- Efficient storage
- Easy to apply/revert

**Cons**:
- More complex to implement
- Requires JSON Patch library

**Example**:
```json
{
  "version": 2,
  "patches": [
    {"op": "add", "path": "/description_html", "value": "<p>New description</p>"},
    {"op": "replace", "path": "/wikipedia_url", "value": "https://..."}
  ]
}
```

### 4. Operational Transformation (OT)

**Approach**: Store operations, not states

**Pros**:
- Efficient for collaborative editing
- Handles conflicts well

**Cons**:
- Complex to implement
- Overkill for single-file encyclopedia

### 5. HTML5 History API Pattern

**Approach**: Use browser History API pattern for versioning

**Pros**:
- Familiar to web developers
- Simple implementation

**Cons**:
- Not designed for file-based versioning

## Recommended Approach

### Hybrid: Entry-Level History + Git Backup

**Primary**: Entry-level history in HTML attributes
- Self-contained
- Fast access
- Easy revert per entry
- Tracks all changes during the day

**Backup**: Git for full file versioning
- Daily commits (once per day after multiple edits)
- Users work on separate branches (different encyclopedias)
- No complex merges needed (different encyclopedias = different branches)
- Future: Support merging personal encyclopedias

**Implementation**:

1. **Entry History**: Store in `data-history` attribute (JSON)
2. **Global Metadata**: Track in `data-metadata` attribute
3. **Git Integration**: Manual Git commits once per day
4. **CSS Hiding**: Use classes for hiding entries
5. **Feature System**: Generic, extensible feature system (not hardcoded)

**Workflow**:
- User makes multiple edits during the day (all tracked in entry history)
- User commits once per day: `git commit -m "Daily update"`
- Each encyclopedia on its own Git branch
- Future: Merge personal encyclopedias using merge tools

## Implementation Plan

### Phase 1: Core Versioning (MVP)

1. Add entry-level version tracking
2. Implement `data-status` attributes
3. Add `data-history` storage
4. Implement basic revert

### Phase 2: Incremental Processing

1. Track processing state in metadata
2. Implement "next unprocessed entry" functionality
3. Add batch processing support
4. Implement "carry on" functionality

### Phase 3: CSS Hiding

1. Add CSS classes for hiding
2. Implement hide/show operations
3. Add status indicators

### Phase 4: Update Strategies

1. Implement "display next entry" editor
2. Add Wikipedia batch processing
3. Add generic feature-specific processing system
4. Add example feature handlers (e.g., Wikipedia, external data sources)

### Phase 5: Advanced Features

1. Git integration helpers (optional, manual commits)
2. Snapshot creation
3. Global revert
4. Personal encyclopedia merging tools
5. Merge conflict resolution for combining encyclopedias

## API Design

### Core Classes

```python
class VersionedEncyclopedia(AmiEncyclopedia):
    """Extended encyclopedia with versioning support"""
    
    def get_next_unprocessed_entry(self):
        """Get next unprocessed entry"""
        pass
    
    def mark_entry_processed(self, entry_id, features_added=None):
        """Mark entry as processed"""
        pass
    
    def revert_entry(self, entry_id, target_version):
        """Revert entry to specific version"""
        pass
    
    def hide_entry(self, entry_id, reason="user_hidden"):
        """Hide entry"""
        pass
    
    def show_entry(self, entry_id):
        """Show hidden entry"""
        pass
    
    def process_batch(self, batch_size=100, feature='wikipedia', feature_handler=None):
        """Process batch of entries
        
        Args:
            batch_size: Number of entries to process
            feature: Name of feature to add (e.g., 'wikipedia', 'gbif', 'images')
            feature_handler: Function to add feature to entry (if None, uses default)
        """
        pass
    
    def process_feature(self, feature_name, feature_handler, limit=None):
        """Process specific feature for entries missing it
        
        Args:
            feature_name: Name of feature (extensible, not hardcoded)
            feature_handler: Function(entry_element) that adds the feature
            limit: Maximum entries to process
        """
        pass
    
    def get_processing_stats(self):
        """Get processing statistics"""
        pass
```

### Utility Functions

```python
def get_unprocessed_entries(encyclopedia_html, limit=None):
    """Get list of unprocessed entries"""
    pass

def get_entries_missing_feature(encyclopedia_html, feature_name, limit=None):
    """Get entries missing specific feature"""
    pass

def add_history_entry(entry_element, action, changes):
    """Add entry to history"""
    pass

def update_processing_state(encyclopedia_html):
    """Update global processing state"""
    pass
```

## File Format Example

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    div[role="ami_entry"].hidden { display: none; }
    div[role="ami_entry"][data-status="unprocessed"] { border-left: 4px solid #ffc107; }
    div[role="ami_entry"][data-status="processed"] { border-left: 4px solid #28a745; }
  </style>
</head>
<body>
  <div role="ami_encyclopedia" 
       title="Climate Encyclopedia"
       data-metadata='{"version":5,"processing_state":{...}}'>
    
    <div role="ami_entry"
         data-entry-id="Q7942"
         data-status="processed"
         data-processed-features="wikipedia,wikidata"
         data-version="3"
         data-history='[{"version":1,"action":"created",...}]'
         term="climate change">
      <!-- Entry content -->
    </div>
    
    <div role="ami_entry"
         data-entry-id="Q12345"
         data-status="unprocessed"
         data-version="1"
         class="hidden"
         term="greenhouse gas">
      <!-- Entry content -->
    </div>
    
  </div>
</body>
</html>
```

## Testing Strategy

1. **Unit Tests**: Test versioning operations
2. **Integration Tests**: Test incremental processing
3. **Performance Tests**: Test with large encyclopedias (5000+ entries)
4. **Revert Tests**: Test revert operations
5. **State Tests**: Test state persistence across saves

## Personal Encyclopedia Merging (Future)

### Requirements

- Merge multiple personal encyclopedias into one
- Handle duplicate entries (same Wikidata ID)
- Resolve conflicts (different descriptions, features)
- Preserve history from both encyclopedias

### Approach

```python
def merge_encyclopedias(source_files, target_file, conflict_strategy='prefer_newer'):
    """Merge multiple personal encyclopedias
    
    Args:
        source_files: List of encyclopedia HTML files to merge
        target_file: Output file for merged encyclopedia
        conflict_strategy: How to handle conflicts
            - 'prefer_newer': Use newer version
            - 'prefer_longer': Use longer description
            - 'merge': Combine both
            - 'manual': Flag for manual review
    """
    # Load all source encyclopedias
    # Group entries by Wikidata ID
    # Merge entries with same ID
    # Handle conflicts based on strategy
    # Preserve history from all sources
    # Save merged encyclopedia
```

### Conflict Resolution

- **Same Wikidata ID**: Merge into single entry
- **Different descriptions**: Use conflict strategy
- **Different features**: Combine feature lists
- **History**: Merge history arrays chronologically

## Migration Path

For existing encyclopedias:

1. Add version attributes to all entries (default version=1)
2. Initialize processing state
3. Mark all entries as "unprocessed" initially
4. Add empty history arrays
5. Update metadata
6. Initialize Git repository (optional, for daily commits)

## Conclusion

This design provides:
- ✅ Wikipedia-like versioning (entry-level)
- ✅ Incremental processing with resume capability
- ✅ Serverless operation (all state in HTML)
- ✅ CSS-based hiding for easy re-instatement
- ✅ Entry-level history tracking
- ✅ Multiple update strategies
- ✅ Simple revert mechanisms

The system is self-contained, easy to use, and supports collaborative editing while maintaining full version history.
