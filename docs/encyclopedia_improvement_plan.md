# Encyclopedia Scripts Improvement Plan

**Date:** 2026-01-15 (system date of generation)  
**Purpose:** Address style violations and improve encyclopedia creation/modification workflow

## Issues Identified

### 1. Single Script for Initial Creation
**Problem:** `create_encyclopedia_from_wordlist.py` does not automatically add definitions, descriptions, and images. Users must manually process entries afterward.

**Current State:**
- Creates basic encyclopedia structure
- Optionally tries to add Wikipedia content (but may fail silently)
- Does not add images automatically
- Requires separate batch processing for missing features

**Solution:** Create unified creation script with optional feature flags

### 2. Iterative Batch Processing Strategy
**Problem:** Need command-line strategy for users on slow connections to build encyclopedia incrementally.

**Current State:**
- `versioned_editor.py` has `process_batch()` function
- Can process batches of entries with features
- But lacks:
  - Progress tracking across sessions
  - Resume capability
  - Clear status reporting
  - Small batch defaults for slow connections

**Solution:** Enhance batch processing with progress tracking and resume capability

### 3. Interactive Features Review
**Problem:** Need to review and improve interactive features.

**Current State:**
- `interactive_delete_entries()` function exists
- Allows deletion by entry number
- But lacks:
  - Entry preview/edit
  - Batch operations
  - Undo capability
  - Better entry display

**Solution:** Enhance interactive features with better UX

## Implementation Plan

### Phase 1: Fix Style Violations

#### 1.1 Create Resources Module
**File:** `test/resources.py` (or `encyclopedia/utils/resources.py`)

```python
from pathlib import Path

class Resources:
    """Resource paths and configuration for encyclopedia project"""
    
    # Get project root (go up from test/ or encyclopedia/)
    _project_root = Path(__file__).parent.parent
    TEMP_DIR = Path(_project_root, "temp")
```

#### 1.2 Fix Temporary File Usage
**File:** `Examples/create_encyclopedia_from_wordlist.py`

**Changes:**
- Replace `tempfile.TemporaryDirectory()` with `Resources.TEMP_DIR`
- Replace `tempfile.NamedTemporaryFile()` with `Resources.TEMP_DIR` subdirectory
- Use `Path(Resources.TEMP_DIR, "examples", "create_encyclopedia_from_wordlist")`

#### 1.3 Fix Path Construction
**File:** `encyclopedia/cli/versioned_editor.py:851`

**Change:**
```python
# Before
app_path = Path(__file__).parent.parent / "browser" / "app.py"

# After
app_path = Path(Path(__file__).parent.parent, "browser", "app.py")
```

### Phase 2: Unified Creation Script

#### 2.1 Enhanced Creation Function
**File:** `Examples/create_encyclopedia_from_wordlist.py`

**New Function Signature:**
```python
def create_encyclopedia_from_wordlist(
    terms: List[str], 
    title: str = "My Encyclopedia",
    add_wikipedia: bool = True,
    add_images: bool = False,
    batch_size: int = 10,  # Small batches for slow connections
    save_intermediate: bool = True  # Save after each batch
) -> AmiEncyclopedia:
```

**Features:**
- `add_wikipedia=True`: Automatically add Wikipedia descriptions (default)
- `add_images=False`: Optionally add images (can be slow)
- `batch_size=10`: Process in small batches (good for slow connections)
- `save_intermediate=True`: Save after each batch (allows resume)

#### 2.2 Command-Line Interface
**Enhance:** `Examples/create_encyclopedia_from_wordlist.py` main()

**New Arguments:**
```python
--add-wikipedia      Add Wikipedia descriptions (default: True)
--no-wikipedia      Skip Wikipedia descriptions
--add-images        Add images from Wikipedia (default: False)
--batch-size N      Process N entries at a time (default: 10)
--no-save-intermediate  Don't save after each batch
```

### Phase 3: Enhanced Batch Processing

#### 3.1 Progress Tracking
**File:** `encyclopedia/cli/versioned_editor.py`

**Add:**
- Track processed entries in metadata
- Store batch progress state
- Resume from last processed entry

**New Metadata Fields:**
```python
METADATA_BATCH_PROGRESS = "batch_progress"
METADATA_LAST_PROCESSED = "last_processed"
METADATA_FEATURES_COMPLETE = "features_complete"
```

#### 3.2 Enhanced process_batch() Function
**Enhancements:**
- Check metadata for already-processed entries
- Skip entries that already have the feature
- Report progress: "Processed 5/100 entries (5%)"
- Save progress after each entry (for resume)
- Small default batch size (10) for slow connections

**New Function Signature:**
```python
def process_batch(
    input_file: Path, 
    feature: str, 
    batch_size: int = 10,  # Small default
    resume: bool = True,   # Resume from last position
    save_progress: bool = True  # Save after each entry
):
```

#### 3.3 Status Command
**Add:** `show_status()` function

**Shows:**
- Total entries
- Entries with Wikipedia descriptions
- Entries with images
- Entries with Wikidata IDs
- Progress percentage for each feature
- Next batch to process

### Phase 4: Interactive Features Enhancement

#### 4.1 Enhanced Entry Display
**File:** `Examples/create_encyclopedia_from_wordlist.py`

**Improvements:**
- Better formatting with colors (optional)
- Show entry status (has Wikipedia, has images, etc.)
- Show entry preview (first 200 chars of description)
- Pagination for large encyclopedias

#### 4.2 Enhanced Interactive Deletion
**Improvements:**
- Preview entry before deletion
- Batch selection (e.g., "1-5,10,15-20")
- Undo last deletion
- Filter entries (e.g., "show only entries without Wikipedia")
- Search/filter by term

#### 4.3 New Interactive Features
**Add:**
- `interactive_review_entries()`: Review and edit entries
- `interactive_add_features()`: Add features to selected entries
- `interactive_merge_entries()`: Merge duplicate entries

## Proposed Workflow

### For Fast Connections
```bash
# Create encyclopedia with all features
python Examples/create_encyclopedia_from_wordlist.py \
    --wordlist terms.txt \
    --output my_encyclopedia.html \
    --add-wikipedia \
    --add-images \
    --batch-size 50
```

### For Slow Connections
```bash
# Step 1: Create basic encyclopedia (fast)
python Examples/create_encyclopedia_from_wordlist.py \
    --wordlist terms.txt \
    --output my_encyclopedia.html \
    --no-wikipedia \
    --batch-size 5

# Step 2: Add Wikipedia descriptions in small batches
python -m encyclopedia.cli.versioned_editor process \
    --input my_encyclopedia.html \
    --feature wikipedia \
    --batch-size 5

# Step 3: Add images in small batches (optional)
python -m encyclopedia.cli.versioned_editor process \
    --input my_encyclopedia.html \
    --feature images \
    --batch-size 3

# Check status anytime
python -m encyclopedia.cli.versioned_editor status \
    --input my_encyclopedia.html
```

### Interactive Review
```bash
# Review and delete entries
python Examples/create_encyclopedia_from_wordlist.py \
    --wordlist terms.txt \
    --output my_encyclopedia.html \
    --interactive-delete

# Or review existing encyclopedia
python -m encyclopedia.cli.versioned_editor review \
    --input my_encyclopedia.html
```

## File Structure Changes

### New Files
1. `test/resources.py` - Resources class with TEMP_DIR
2. `encyclopedia/cli/interactive.py` - Interactive features module (optional)

### Modified Files
1. `Examples/create_encyclopedia_from_wordlist.py` - Enhanced creation
2. `encyclopedia/cli/versioned_editor.py` - Enhanced batch processing
3. `encyclopedia/core/encyclopedia.py` - Add progress tracking metadata

## Testing Strategy

1. **Unit Tests:**
   - Test Resources.TEMP_DIR creation
   - Test batch processing with progress tracking
   - Test resume capability

2. **Integration Tests:**
   - Test full workflow for fast connections
   - Test incremental workflow for slow connections
   - Test interactive features

3. **Manual Testing:**
   - Test with slow connection simulation
   - Test resume after interruption
   - Test interactive deletion and review

## Migration Notes

### Backward Compatibility
- Existing scripts will continue to work
- New features are opt-in (defaults preserve current behavior)
- Old encyclopedia files will work (progress tracking added on first batch)

### Breaking Changes
- None planned
- All changes are additive

## Timeline

1. **Phase 1 (Style Fixes):** 1-2 hours
2. **Phase 2 (Unified Creation):** 2-3 hours
3. **Phase 3 (Batch Processing):** 2-3 hours
4. **Phase 4 (Interactive Features):** 3-4 hours

**Total:** ~8-12 hours

## Next Steps

1. Create Resources module
2. Fix style violations
3. Implement unified creation script
4. Enhance batch processing
5. Review and improve interactive features
6. Test with slow connection simulation
7. Update documentation

---

**Date:** 2026-01-15 (system date of generation)
