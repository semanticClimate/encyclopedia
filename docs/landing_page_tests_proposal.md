# Landing Page Tests Proposal

**Date:** February 21, 2026  
**Status:** Proposal (Not Yet Implemented)

## Overview

Comprehensive test suite for landing page features 1-5:
1. Table of Contents (TOC)
2. Search Functionality (with enhanced options)
3. Entry Display & Navigation
4. Statistics & Overview Dashboard
5. Pagination & Browsing

## Test Fixtures

### Small Encyclopedia Fixture
**Purpose:** Fast tests, basic functionality verification  
**Size:** 10-20 entries

**Characteristics:**
- Mix of entries with and without descriptions
- Mix of entries with and without images
- Mix of entries with and without Wikidata IDs
- Some entries with synonyms (merged entries)
- Some entries with definitions (first sentence)
- Diverse first letters (A-Z coverage)
- Real Wikipedia terms that have content

**Example Terms:**
```python
SMALL_ENCYCLOPEDIA_TERMS = [
    "atom",           # Has image, description, Wikidata
    "climate",        # Has description, Wikidata, synonyms
    "DNA",            # Has image, description, Wikidata
    "ecosystem",      # Has description, Wikidata
    "greenhouse gas", # Has image, description, Wikidata, synonyms
    "methane",        # Has image, description, Wikidata
    "ocean",          # Has description, Wikidata
    "photosynthesis", # Has description, Wikidata
    "protein",        # Has image, description, Wikidata
    "telescope"       # Has image, description, Wikidata
]
```

**Expected Properties:**
- ~80% with descriptions
- ~60% with images
- ~90% with Wikidata IDs
- ~30% with synonyms
- ~50% with definitions (first sentence)

### Medium Encyclopedia Fixture
**Purpose:** Realistic testing, performance checks  
**Size:** 50-100 entries

**Characteristics:**
- Similar mix to small encyclopedia but larger scale
- More diverse categories
- More synonym groups
- Some entries missing various fields (realistic incomplete data)
- Mix of single-word and multi-word terms
- Some entries with long descriptions, some with short

**Example Terms:**
```python
MEDIUM_ENCYCLOPEDIA_TERMS = [
    # Climate-related (10 entries)
    "climate change", "global warming", "greenhouse gas", "carbon dioxide",
    "methane", "ice sheet", "sea level rise", "ocean acidification",
    "atmosphere", "precipitation",
    
    # Science-related (15 entries)
    "atom", "molecule", "DNA", "protein", "cell", "evolution",
    "photosynthesis", "ecosystem", "biodiversity", "genetics",
    "microscope", "telescope", "microscope", "laboratory", "experiment",
    
    # Technology-related (10 entries)
    "computer", "algorithm", "software", "hardware", "network",
    "internet", "database", "programming", "artificial intelligence", "machine learning",
    
    # Geography-related (10 entries)
    "continent", "ocean", "mountain", "river", "desert",
    "forest", "island", "volcano", "glacier", "plateau",
    
    # Additional diverse terms (15 entries)
    # ... more terms to reach 50-100 total
]
```

**Expected Properties:**
- ~75% with descriptions
- ~55% with images
- ~85% with Wikidata IDs
- ~25% with synonyms
- ~45% with definitions

### Large Encyclopedia Fixture
**Purpose:** Performance testing, edge cases  
**Size:** 500-1000 entries

**Characteristics:**
- Large-scale realistic encyclopedia
- Many synonym groups
- Many categories
- Mix of complete and incomplete entries
- Performance-critical scenarios
- Edge cases (very long descriptions, special characters, etc.)

**Example Terms:**
```python
LARGE_ENCYCLOPEDIA_TERMS = [
    # Generate from multiple domains:
    # - Climate science (50 entries)
    # - Biology (50 entries)
    # - Chemistry (50 entries)
    # - Physics (50 entries)
    # - Technology (50 entries)
    # - Geography (50 entries)
    # - History (50 entries)
    # - Mathematics (50 entries)
    # - Medicine (50 entries)
    # - Astronomy (50 entries)
    # ... total 500+ entries
]
```

**Expected Properties:**
- ~70% with descriptions
- ~50% with images
- ~80% with Wikidata IDs
- ~20% with synonyms
- ~40% with definitions

---

## Test Structure

### Test File Organization

```
test/encyclopedia/
├── conftest.py                          # Shared fixtures
├── test_landing_page_toc.py            # TOC tests
├── test_landing_page_search.py         # Search tests
├── test_landing_page_entry_display.py  # Entry display tests
├── test_landing_page_statistics.py    # Statistics tests
├── test_landing_page_pagination.py     # Pagination tests
└── fixtures/
    ├── small_encyclopedia.py           # Small fixture generator
    ├── medium_encyclopedia.py         # Medium fixture generator
    └── large_encyclopedia.py          # Large fixture generator
```

---

## Feature 1: Table of Contents Tests

### Test Class: `TestTableOfContents`

#### Test Cases:

1. **`test_toc_generates_alphabetical_sections`**
   - Verify TOC has sections for each letter (A-Z)
   - Verify entries are grouped correctly by first letter
   - Verify empty letter sections are handled gracefully

2. **`test_toc_shows_entry_counts_per_letter`**
   - Verify each letter section shows correct count
   - Verify counts match actual entries
   - Verify zero counts are displayed correctly

3. **`test_toc_quick_jump_navigation`**
   - Verify A-Z quick jump links work
   - Verify clicking letter scrolls to section
   - Verify all letters are present in quick jump

4. **`test_toc_collapsible_sections`**
   - Verify sections can be expanded/collapsed
   - Verify default state (all expanded or all collapsed)
   - Verify state persists during session

5. **`test_toc_compact_vs_detailed_view`**
   - Verify toggle between views works
   - Verify compact view shows only term names
   - Verify detailed view shows term + first sentence + thumbnail
   - Verify view preference persists

6. **`test_toc_entry_links_work`**
   - Verify clicking entry scrolls to full entry
   - Verify entry links use correct anchors/IDs
   - Verify browser back button works after navigation

7. **`test_toc_visual_indicators`**
   - Verify entries with images show image icon
   - Verify entries with descriptions show description icon
   - Verify entries with Wikidata show Wikidata icon
   - Verify icons are clickable/filterable

8. **`test_toc_handles_special_characters`**
   - Verify entries starting with numbers (0-9) grouped correctly
   - Verify entries starting with special characters handled
   - Verify Unicode characters handled correctly

9. **`test_toc_performance_large_encyclopedia`**
   - Verify TOC generation completes in reasonable time (<1s for 1000 entries)
   - Verify rendering doesn't block UI
   - Verify scrolling performance is smooth

10. **`test_toc_updates_with_filtered_entries`**
    - Verify TOC updates when filters applied
    - Verify only matching entries shown
    - Verify letter sections update counts correctly

---

## Feature 2: Search Functionality Tests

### Test Class: `TestSearchFunctionality`

#### Search Option: Term Search

1. **`test_search_by_term_exact_match`**
   - Search for exact term "climate change"
   - Verify exact match appears first
   - Verify match highlighted in results
   - Verify case-insensitive matching works

2. **`test_search_by_term_partial_match`**
   - Search for "climat" (partial)
   - Verify "climate", "climate change" appear
   - Verify relevance ordering (more complete matches first)

3. **`test_search_by_term_multiple_words`**
   - Search for "greenhouse gas"
   - Verify multi-word terms matched correctly
   - Verify word order matters (or doesn't, depending on design)

4. **`test_search_by_term_no_results`**
   - Search for non-existent term
   - Verify "No results" message displayed
   - Verify suggestions provided (similar terms)

#### Search Option: Synonym Search

5. **`test_search_by_synonym_finds_canonical`**
   - Search for synonym term
   - Verify canonical entry found
   - Verify synonym highlighted in results
   - Verify all synonyms of entry shown

6. **`test_search_by_synonym_multiple_synonyms`**
   - Entry has synonyms: ["climate", "weather pattern"]
   - Search for "climate" finds entry
   - Search for "weather pattern" finds same entry
   - Verify canonical term displayed

7. **`test_search_by_synonym_case_insensitive`**
   - Verify synonym matching is case-insensitive
   - Verify "CLIMATE" matches "climate" synonym

#### Search Option: Text in Definition

8. **`test_search_by_definition_text`**
   - Search for text that appears in first sentence definition
   - Verify entry found even if term doesn't match
   - Verify definition text highlighted in results
   - Verify only entries with definitions searched

9. **`test_search_by_definition_partial_text`**
   - Search for partial phrase from definition
   - Verify fuzzy matching works for definitions
   - Verify relevance scoring includes definition match

10. **`test_search_by_definition_no_definition_entries`**
    - Search for text that only appears in definitions
    - Verify entries without definitions excluded
    - Verify search results accurate

#### Search Option: Text in Description

11. **`test_search_by_description_text`**
    - Search for text that appears in description paragraph
    - Verify entry found
    - Verify description text highlighted
    - Verify HTML tags stripped for search

12. **`test_search_by_description_html_content`**
    - Search for text within HTML links in description
    - Verify link text is searchable
    - Verify HTML structure preserved in display

13. **`test_search_by_description_multiple_matches`**
    - Search for common word appearing in multiple descriptions
    - Verify all matching entries returned
    - Verify results ordered by relevance

#### Search Option: Presence of Image

14. **`test_search_by_image_presence`**
    - Filter/search for entries with images
    - Verify only entries with `figure_html` or `image_link` shown
    - Verify image count matches expected

15. **`test_search_by_image_absence`**
    - Filter/search for entries without images
    - Verify entries without images shown
    - Verify count accurate

16. **`test_search_by_image_combined_with_text`**
    - Search for "climate" AND has image
    - Verify only climate entries with images shown
    - Verify AND logic works correctly

#### Combined Search Options

17. **`test_search_multiple_options_and`**
    - Search: term="climate" AND has_image=True
    - Verify only entries matching both criteria
    - Verify AND logic works

18. **`test_search_multiple_options_or`**
    - Search: term="climate" OR synonym="weather"
    - Verify entries matching either criterion
    - Verify OR logic works

19. **`test_search_all_options_combined`**
    - Search: term="climate" AND description_contains="change" AND has_image=True
    - Verify complex query works
    - Verify results accurate

#### Search Performance

20. **`test_search_performance_small_encyclopedia`**
    - Verify search completes in <100ms for small encyclopedia
    - Verify no UI blocking

21. **`test_search_performance_medium_encyclopedia`**
    - Verify search completes in <500ms for medium encyclopedia
    - Verify debouncing works (doesn't search on every keystroke)

22. **`test_search_performance_large_encyclopedia`**
    - Verify search completes in <2s for large encyclopedia
    - Verify results limited appropriately
    - Verify pagination works for large result sets

#### Search UI

23. **`test_search_autocomplete_suggestions`**
    - Type "clim" in search box
    - Verify suggestions appear (climate, climate change, etc.)
    - Verify clicking suggestion fills search box
    - Verify suggestions ordered by relevance

24. **`test_search_real_time_updates`**
    - Type search query
    - Verify results update as user types (debounced)
    - Verify loading indicator shown during search
    - Verify empty state when no query

25. **`test_search_result_highlighting`**
    - Search for "climate"
    - Verify "climate" highlighted in term matches
    - Verify "climate" highlighted in description matches
    - Verify highlighting works for HTML content

26. **`test_search_result_grouping`**
    - Verify "Exact Matches" section shown first
    - Verify "Related Entries" section shown second
    - Verify grouping accurate

27. **`test_search_clear_button`**
    - Enter search query
    - Click clear button
    - Verify search box cleared
    - Verify all entries shown again

---

## Feature 3: Entry Display & Navigation Tests

### Test Class: `TestEntryDisplay`

#### Entry Card Layout

1. **`test_entry_card_displays_term`**
   - Verify term shown prominently as heading
   - Verify term is clickable/linkable
   - Verify canonical term shown if different

2. **`test_entry_card_displays_metadata`**
   - Verify Wikidata ID displayed with link
   - Verify Wikipedia URL displayed with link
   - Verify links open in new tab
   - Verify external link security (rel="noopener")

3. **`test_entry_card_displays_description`**
   - Verify description HTML rendered correctly
   - Verify first paragraph shown by default
   - Verify "Show More" expands full description
   - Verify HTML formatting preserved

4. **`test_entry_card_displays_image`**
   - Verify image thumbnail displayed if available
   - Verify image is clickable (lightbox/modal)
   - Verify alt text present
   - Verify placeholder if no image

5. **`test_entry_card_displays_synonyms`**
   - Verify synonyms list displayed
   - Verify canonical term highlighted
   - Verify synonyms are clickable
   - Verify "See also" or similar label

6. **`test_entry_card_missing_fields`**
   - Verify entry without description handled gracefully
   - Verify entry without image shows placeholder
   - Verify entry without Wikidata ID handled
   - Verify "Missing" indicators shown

#### Entry Detail View

7. **`test_entry_detail_expandable`**
   - Verify entry can be expanded to show full details
   - Verify expanded state persists
   - Verify collapse works

8. **`test_entry_detail_full_description`**
   - Verify full description shown when expanded
   - Verify multiple paragraphs displayed
   - Verify HTML rendering correct

9. **`test_entry_detail_full_image`**
   - Verify full-size image displayed in modal/lightbox
   - Verify image metadata shown (if available)
   - Verify close button works

10. **`test_entry_detail_related_entries`**
    - Verify related entries links shown
    - Verify links navigate correctly
    - Verify related entries calculated correctly

#### Navigation Between Entries

11. **`test_entry_navigation_previous_next`**
    - Verify Previous/Next buttons work
    - Verify navigation wraps (last → first)
    - Verify current entry highlighted
    - Verify URL updates with navigation

12. **`test_entry_navigation_breadcrumb`**
    - Verify breadcrumb shows current location
    - Verify breadcrumb links work
    - Verify breadcrumb updates on navigation

13. **`test_entry_navigation_random`**
    - Verify "Random Entry" button works
    - Verify random entry displayed
    - Verify different entry each time (usually)

14. **`test_entry_navigation_jump_to_term`**
    - Verify jump to entry by term works
    - Verify autocomplete in jump box
    - Verify navigation to correct entry

15. **`test_entry_deep_linking`**
    - Verify URL fragment (#entry-id) navigates to entry
    - Verify entry scrolled into view
    - Verify entry highlighted
    - Verify browser back/forward works

#### Entry Actions

16. **`test_entry_copy_link`**
    - Verify "Copy Link" button works
    - Verify link copied to clipboard
    - Verify link includes entry ID/fragment

17. **`test_entry_export_json`**
    - Verify "Export as JSON" works
    - Verify JSON structure correct
    - Verify all entry fields included

18. **`test_entry_export_markdown`**
    - Verify "Export as Markdown" works
    - Verify Markdown formatting correct
    - Verify images handled correctly

---

## Feature 4: Statistics & Overview Dashboard Tests

### Test Class: `TestStatisticsDashboard`

#### Overview Statistics

1. **`test_statistics_total_entries`**
   - Verify total entry count displayed correctly
   - Verify count matches actual entries
   - Verify count updates with filters

2. **`test_statistics_entries_with_descriptions`**
   - Verify count of entries with descriptions
   - Verify percentage calculated correctly
   - Verify matches `validate_encyclopedia_completeness()` results

3. **`test_statistics_entries_with_images`**
   - Verify count of entries with images
   - Verify percentage calculated correctly
   - Verify matches validation results

4. **`test_statistics_entries_with_wikidata`**
   - Verify count of entries with Wikidata IDs
   - Verify percentage calculated correctly
   - Verify matches validation results

5. **`test_statistics_entries_with_wikipedia`**
   - Verify count of entries with Wikipedia URLs
   - Verify percentage calculated correctly

#### Completeness Indicators

6. **`test_statistics_progress_bars`**
   - Verify progress bars displayed for each metric
   - Verify progress bar values match percentages
   - Verify visual indicators (green/yellow/red) correct

7. **`test_statistics_completeness_score`**
   - Verify overall completeness score calculated
   - Verify score formula correct (weighted average?)
   - Verify score displayed prominently

8. **`test_statistics_visual_indicators`**
   - Verify green indicator for >80% complete
   - Verify yellow indicator for 50-80% complete
   - Verify red indicator for <50% complete

#### Content Breakdown

9. **`test_statistics_entries_by_letter`**
   - Verify breakdown by first letter displayed
   - Verify counts match actual entries
   - Verify chart/list format works

10. **`test_statistics_entries_by_category`**
    - Verify breakdown by category (if categories exist)
    - Verify "Uncategorized" group shown
    - Verify category counts accurate

11. **`test_statistics_most_common_terms`**
    - Verify most common terms list displayed (if available)
    - Verify ordering correct
    - Verify limit applied (top 10?)

#### Quality Metrics

12. **`test_statistics_average_description_length`**
    - Verify average description length calculated
    - Verify calculation excludes empty descriptions
    - Verify displayed in readable format (words/chars)

13. **`test_statistics_entries_needing_attention`**
    - Verify list of incomplete entries shown
    - Verify entries missing descriptions listed
    - Verify entries missing images listed
    - Verify links to entries work

14. **`test_statistics_validation_status`**
    - Verify validation status summary displayed
    - Verify matches `validate_encyclopedia_completeness()` output
    - Verify "Pass" or "Fail" indicators

#### Statistics Updates

15. **`test_statistics_updates_with_filters`**
    - Apply filter (e.g., "has images")
    - Verify statistics update to reflect filtered set
    - Verify counts recalculated correctly

16. **`test_statistics_updates_with_search`**
    - Perform search
    - Verify statistics show results for search results only
    - Verify "Showing X of Y entries" message

---

## Feature 5: Pagination & Browsing Tests

### Test Class: `TestPaginationBrowsing`

#### Pagination Controls

1. **`test_pagination_displays_correct_page`**
   - Verify first page shows entries 1-20 (if 20 per page)
   - Verify page number displayed correctly
   - Verify total pages calculated correctly

2. **`test_pagination_next_previous_buttons`**
   - Verify Next button advances to next page
   - Verify Previous button goes to previous page
   - Verify buttons disabled at boundaries (first/last page)

3. **`test_pagination_first_last_buttons`**
   - Verify First button jumps to page 1
   - Verify Last button jumps to last page
   - Verify navigation works correctly

4. **`test_pagination_page_numbers`**
   - Verify page numbers displayed (1, 2, 3, ...)
   - Verify ellipsis for large page counts (1 ... 5 6 7 ... 20)
   - Verify clicking page number navigates correctly

5. **`test_pagination_entries_per_page`**
   - Verify dropdown/selector for entries per page
   - Verify changing entries per page recalculates pages
   - Verify current page adjusted if needed
   - Verify options: 10, 20, 50, 100

6. **`test_pagination_url_parameters`**
   - Verify page number in URL (?page=2)
   - Verify entries per page in URL (?per_page=50)
   - Verify URL updates on navigation
   - Verify browser back/forward works

#### Alphabetical Browsing

7. **`test_alphabetical_browse_letter_navigation`**
   - Verify A-Z navigation bar displayed
   - Verify clicking letter filters to that letter
   - Verify all entries for letter shown
   - Verify pagination works within letter

8. **`test_alphabetical_browse_jump_to_letter`**
   - Verify "Jump to letter" functionality works
   - Verify letter selection updates display
   - Verify "All" option shows all entries

9. **`test_alphabetical_browse_entry_counts`**
   - Verify entry count shown for each letter
   - Verify counts accurate
   - Verify zero counts handled (letter disabled?)

#### Infinite Scroll (Alternative)

10. **`test_infinite_scroll_loads_more`**
    - Verify scrolling loads more entries
    - Verify loading indicator shown
    - Verify entries appended correctly
    - Verify no duplicates

11. **`test_infinite_scroll_performance`**
    - Verify scrolling smooth
    - Verify no performance degradation
    - Verify memory usage reasonable

#### Pagination with Filters

12. **`test_pagination_preserves_filters`**
    - Apply filter (e.g., "has images")
    - Navigate to page 2
    - Verify filter still applied
    - Verify only filtered entries paginated

13. **`test_pagination_preserves_search`**
    - Perform search
    - Navigate to page 2 of results
    - Verify search query preserved
    - Verify results still filtered by search

14. **`test_pagination_resets_on_new_search`**
    - Perform search, go to page 3
    - Perform new search
    - Verify pagination resets to page 1
    - Verify new results shown

#### Pagination Performance

15. **`test_pagination_performance_small`**
    - Verify pagination instant for small encyclopedia
    - Verify no loading delays

16. **`test_pagination_performance_medium`**
    - Verify pagination fast for medium encyclopedia (<100ms)
    - Verify smooth transitions

17. **`test_pagination_performance_large`**
    - Verify pagination acceptable for large encyclopedia (<500ms)
    - Verify virtual scrolling if needed
    - Verify memory efficient

---

## Fixture Specifications

### Small Encyclopedia Fixture

**File:** `test/encyclopedia/fixtures/small_encyclopedia.py`

**Function:** `create_small_encyclopedia() -> AmiEncyclopedia`

**Properties:**
- 10-20 entries
- Mix of complete/incomplete entries
- Some synonym groups
- Diverse letters
- Real Wikipedia terms

**Usage:**
```python
@pytest.fixture
def small_encyclopedia():
    """Create small encyclopedia for fast tests."""
    from encyclopedia.fixtures.small_encyclopedia import create_small_encyclopedia
    return create_small_encyclopedia()
```

### Medium Encyclopedia Fixture

**File:** `test/encyclopedia/fixtures/medium_encyclopedia.py`

**Function:** `create_medium_encyclopedia() -> AmiEncyclopedia`

**Properties:**
- 50-100 entries
- Realistic mix of content
- Multiple categories
- Performance testing scenarios

**Usage:**
```python
@pytest.fixture
def medium_encyclopedia():
    """Create medium encyclopedia for realistic tests."""
    from encyclopedia.fixtures.medium_encyclopedia import create_medium_encyclopedia
    return create_medium_encyclopedia()
```

### Large Encyclopedia Fixture

**File:** `test/encyclopedia/fixtures/large_encyclopedia.py`

**Function:** `create_large_encyclopedia() -> AmiEncyclopedia`

**Properties:**
- 500-1000 entries
- Large-scale testing
- Performance critical
- Edge cases included

**Usage:**
```python
@pytest.fixture
def large_encyclopedia():
    """Create large encyclopedia for performance tests."""
    from encyclopedia.fixtures.large_encyclopedia import create_large_encyclopedia
    return create_large_encyclopedia()
```

### Fixture Helper Functions

**File:** `test/encyclopedia/fixtures/helpers.py`

**Functions:**
- `create_entry_with_all_fields(term, ...)` - Complete entry
- `create_entry_without_description(term, ...)` - Missing description
- `create_entry_without_image(term, ...)` - Missing image
- `create_entry_with_synonyms(term, synonyms, ...)` - Entry with synonyms
- `create_entry_with_definition(term, definition, ...)` - Entry with definition

---

## Test Data Requirements

### Entry Structure for Testing

Each test entry should have:
```python
{
    'term': str,                    # Primary term
    'canonical_term': str,          # Canonical term (may differ)
    'wikidata_id': str,             # Wikidata Q/P ID (e.g., "Q7937")
    'wikipedia_url': str,           # Full Wikipedia URL
    'description_html': str,        # HTML description (first paragraph)
    'definition_html': str,        # HTML definition (first sentence)
    'figure_html': Element,        # Image element (lxml) or None
    'image_link': str,             # Image URL or None
    'synonyms': List[str],         # List of synonym terms
    # ... other metadata
}
```

### Test Scenarios

#### Scenario 1: Complete Entry
- Has term, description, definition, image, Wikidata ID, Wikipedia URL
- Used for: Testing full functionality

#### Scenario 2: Entry Without Description
- Has term, image, Wikidata ID, but no description
- Used for: Testing missing content handling

#### Scenario 3: Entry Without Image
- Has term, description, Wikidata ID, but no image
- Used for: Testing image absence handling

#### Scenario 4: Entry With Synonyms
- Has term + multiple synonyms (merged entry)
- Used for: Testing synonym search and display

#### Scenario 5: Entry With Definition Only
- Has term, definition (first sentence), but no full description
- Used for: Testing definition search

#### Scenario 6: Minimal Entry
- Has only term and Wikipedia URL
- Used for: Testing incomplete entry handling

---

## Test Implementation Strategy

### Phase 1: Fixtures
1. Create fixture generators
2. Create helper functions for entry creation
3. Test fixtures themselves (verify properties)

### Phase 2: Unit Tests
1. Test individual components (TOC generator, search, etc.)
2. Test with small encyclopedia fixture
3. Verify basic functionality

### Phase 3: Integration Tests
1. Test full landing page generation
2. Test with medium encyclopedia fixture
3. Test component interactions

### Phase 4: Performance Tests
1. Test with large encyclopedia fixture
2. Measure performance metrics
3. Verify acceptable performance

### Phase 5: Edge Cases
1. Test empty encyclopedia
2. Test single entry
3. Test special characters
4. Test very long descriptions
5. Test missing fields

---

## Assertion Patterns

### Standard Assertions

```python
# Count assertions
assert len(toc_sections) == 26, f"Expected 26 letter sections, got {len(toc_sections)}"

# Content assertions
assert "climate change" in search_results, \
    f"Expected 'climate change' in results, got: {[r.term for r in search_results]}"

# State assertions
assert current_page == 2, f"Expected page 2, got page {current_page}"

# Performance assertions
assert search_time < 0.5, f"Search took {search_time}s, expected <0.5s"
```

### Descriptive Assert Messages

Following style guide: Use descriptive assert messages that reference variable names and context.

```python
# ✅ GOOD
assert entries_with_images == expected_count, \
    f"Expected {expected_count} entries with images in {encyclopedia.title}, " \
    f"but found {entries_with_images}. Total entries: {len(encyclopedia.entries)}"

# ❌ BAD
assert entries_with_images == expected_count, "Count mismatch"
```

---

## Test Coverage Goals

- **Unit Tests**: 90%+ coverage for landing page components
- **Integration Tests**: All user flows covered
- **Performance Tests**: All size categories tested
- **Edge Cases**: All edge cases identified and tested

---

## Related Documentation

- `docs/landing_page_features_proposal.md` - Feature specifications
- `encyclopedia/browser/search_engine.py` - Search engine implementation
- `encyclopedia/utils/validation.py` - Validation functions
- `docs/STYLE_GUIDE.md` - Coding standards for tests

---

**Next Steps:**
1. Review and approve test proposal
2. Create fixture generators
3. Implement tests incrementally
4. Run tests and verify coverage
5. Iterate based on results
