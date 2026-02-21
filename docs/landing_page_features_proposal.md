# Encyclopedia Landing Page - Features Proposal

**Date:** February 21, 2026  
**Status:** Proposal (Not Yet Implemented)

## Overview

A comprehensive landing page for the encyclopedia that provides an intuitive entry point for browsing, searching, and exploring encyclopedia entries. Designed to work with both static HTML files and dynamic web interfaces.

## Core Features

### 1. Table of Contents (TOC)

**Purpose:** Provide a structured, navigable overview of all encyclopedia entries.

**Features:**
- **Alphabetical Organization**
  - Group entries by first letter (A-Z)
  - Collapsible letter sections
  - Quick jump navigation (A-Z links at top)
  - Entry count per letter

- **Hierarchical Organization** (if categories exist)
  - Group by Wikidata categories
  - Group by subject matter (if metadata available)
  - Nested categories with expand/collapse

- **Compact vs. Detailed View**
  - Compact: Just term names (for quick scanning)
  - Detailed: Term + first sentence + image thumbnail
  - Toggle between views

- **Entry Links**
  - Clickable entries that scroll to full entry or open in new section
  - Visual indicators for entries with images (icon)
  - Visual indicators for entries with descriptions (icon)

**Implementation Considerations:**
- Generate TOC from `encyclopedia.entries`
- Use JavaScript for collapsible sections
- Support both static HTML and dynamic generation
- Consider pagination for very large encyclopedias (>1000 entries)

---

### 2. Search Functionality

**Purpose:** Fast, intuitive search across all entries.

**Features:**
- **Search Bar**
  - Prominent placement at top of page
  - Real-time search as user types (debounced)
  - Search suggestions/autocomplete
  - Clear button to reset search

- **Search Types** (reuse existing browser search engine)
  - **Quick Search**: Simple text matching (default)
  - **Exact Match**: Exact term matching
  - **Stemmed Search**: Word variation matching
  - **Fuzzy Search**: Similarity matching (typos, partial)
  - **Advanced Search**: Multiple criteria (term, description, Wikidata ID)

- **Search Results Display**
  - Highlight matching terms in results
  - Show relevance score (for fuzzy/stemmed)
  - Group results: "Exact Matches" vs "Related Entries"
  - Limit results with "Show More" button
  - Empty state message with suggestions

- **Search Filters**
  - Filter by: Has images, Has description, Has Wikidata ID
  - Filter by category (if available)
  - Sort by: Relevance, Alphabetical, Date added

**Implementation Considerations:**
- Leverage existing `EncyclopediaSearchEngine` from `browser/search_engine.py`
- Client-side search for small encyclopedias (<500 entries)
- Server-side search for larger encyclopedias
- Index generation on page load or pre-built

---

### 3. Entry Display & Navigation

**Purpose:** Present individual entries clearly and enable easy navigation.

**Features:**
- **Entry Card/Box Layout**
  - Term as heading (prominent)
  - Canonical term (if different from term)
  - Wikidata ID with link
  - Wikipedia link
  - Description (first paragraph, HTML rendered)
  - Image thumbnail (if available)
  - Synonyms list (if merged entries)

- **Entry Detail View**
  - Expandable/collapsible full description
  - Full-size image display
  - Related entries links
  - Metadata display (date added, last modified)

- **Navigation Between Entries**
  - Previous/Next entry buttons
  - Breadcrumb navigation
  - "Random Entry" button
  - Jump to entry by term

- **Entry Actions**
  - Copy entry link (shareable URL)
  - Export entry as JSON/Markdown
  - Edit entry (if editing enabled)
  - Report issue/error

**Implementation Considerations:**
- Use semantic HTML (`<article>`, `<section>`)
- Support deep linking (URL fragments for entries)
- Lazy load images for performance
- Progressive enhancement (works without JavaScript)

---

### 4. Statistics & Overview Dashboard

**Purpose:** Provide summary information about the encyclopedia.

**Features:**
- **Overview Statistics**
  - Total number of entries
  - Entries with descriptions (count and percentage)
  - Entries with images (count and percentage)
  - Entries with Wikidata IDs (count and percentage)
  - Entries with Wikipedia links (count and percentage)

- **Completeness Indicators**
  - Progress bars for each metric
  - Visual indicators (green/yellow/red)
  - "Completeness Score" (overall percentage)

- **Content Breakdown**
  - Entries by first letter (bar chart or list)
  - Entries by category (if categories exist)
  - Most common terms (if available)
  - Recent additions (if timestamps available)

- **Quality Metrics**
  - Average description length
  - Entries needing attention (missing descriptions/images)
  - Validation status summary

**Implementation Considerations:**
- Calculate statistics from `encyclopedia.entries`
- Use `validate_encyclopedia_completeness()` for metrics
- Display as cards or dashboard widgets
- Update dynamically if entries are modified

---

### 5. Pagination & Browsing

**Purpose:** Enable efficient browsing of large encyclopedias.

**Features:**
- **Pagination**
  - Configurable entries per page (10, 20, 50, 100)
  - Page numbers with ellipsis for large page counts
  - First/Previous/Next/Last navigation
  - Current page indicator
  - Total pages display

- **Infinite Scroll Option**
  - Alternative to pagination
  - Load more entries as user scrolls
  - Show loading indicator

- **Alphabetical Browsing**
  - Jump to entries starting with specific letter
  - Letter navigation bar (A-Z)
  - Show all entries for selected letter

- **Category Browsing** (if categories exist)
  - Browse by Wikidata categories
  - Category tree navigation
  - Filter entries by category

**Implementation Considerations:**
- Client-side pagination for small encyclopedias
- Server-side pagination for large encyclopedias
- Preserve search/filter state across page changes
- URL parameters for bookmarkable pages

---

### 6. Filtering & Sorting

**Purpose:** Allow users to find entries matching specific criteria.

**Features:**
- **Filter Options**
  - **By Content**: Has description, Has image, Has Wikidata ID
  - **By Quality**: Complete entries, Incomplete entries, Needs review
  - **By Category**: Wikidata categories, Subject areas
  - **By Term**: Starts with letter, Contains text
  - **By Date**: Recently added, Recently modified (if timestamps available)

- **Filter Combinations**
  - Multiple filters active simultaneously
  - Clear all filters button
  - Filter count indicator ("Showing X of Y entries")
  - Save filter presets (if user accounts enabled)

- **Sorting Options**
  - Alphabetical (A-Z, Z-A)
  - By relevance (search results)
  - By completeness (most complete first)
  - By date (newest/oldest)
  - Random order

**Implementation Considerations:**
- Use URL query parameters for filter state
- Update TOC/search results based on active filters
- Show active filters as removable tags/chips
- Persist filter preferences (localStorage)

---

### 7. Visual Enhancements

**Purpose:** Improve visual appeal and usability.

**Features:**
- **Image Gallery**
  - Thumbnail grid view of all entries with images
  - Lightbox/modal for full-size image viewing
  - Image carousel for entries with multiple images
  - Lazy loading for performance

- **Visual Indicators**
  - Icons for entries with images (📷)
  - Icons for entries with descriptions (📝)
  - Icons for entries with Wikidata (🔗)
  - Status badges (Complete, Incomplete, Needs Review)
  - Category tags/chips

- **Theme Options**
  - Light/Dark mode toggle
  - Font size adjustment
  - Compact/Comfortable spacing
  - Color scheme options

- **Responsive Design**
  - Mobile-friendly layout
  - Tablet optimization
  - Desktop full-featured view
  - Touch-friendly controls

**Implementation Considerations:**
- Use CSS Grid/Flexbox for layouts
- CSS variables for theming
- Media queries for responsive breakpoints
- Progressive images (blur-up technique)

---

### 8. Advanced Features

**Purpose:** Additional functionality for power users.

**Features:**
- **Export Options**
  - Export filtered entries as HTML
  - Export as JSON
  - Export as CSV
  - Export as Markdown
  - Print-friendly view

- **Comparison View**
  - Side-by-side comparison of multiple entries
  - Diff view for entry versions (if versioning enabled)
  - Related entries comparison

- **Bookmarks/Favorites**
  - Save favorite entries
  - Create custom collections
  - Share collections via URL
  - Export bookmarks

- **History/Recent**
  - Recently viewed entries
  - Search history
  - Navigation history
  - Clear history option

- **Keyboard Shortcuts**
  - `/` to focus search
  - `Esc` to close modals
  - Arrow keys for navigation
  - `?` to show shortcuts help

**Implementation Considerations:**
- Use localStorage for client-side features
- Consider server-side storage for user accounts (future)
- Document keyboard shortcuts clearly
- Provide accessibility alternatives

---

### 9. Integration Features

**Purpose:** Connect with external resources and tools.

**Features:**
- **Wikipedia Integration**
  - Direct links to Wikipedia pages
  - "View on Wikipedia" button
  - Open Wikipedia in new tab
  - Wikipedia preview on hover (if API available)

- **Wikidata Integration**
  - Direct links to Wikidata items
  - Display Wikidata properties (if fetched)
  - "View on Wikidata" button
  - Wikidata QID search

- **Sharing**
  - Share individual entry (copy link)
  - Share filtered view (copy URL)
  - Social media sharing buttons
  - Embed code for entries

- **API Access** (if web server enabled)
  - REST API endpoints
  - JSON responses
  - API documentation
  - Rate limiting

**Implementation Considerations:**
- External links open in new tabs
- Use `rel="noopener noreferrer"` for security
- Consider CORS for API access
- Provide fallbacks if external services unavailable

---

### 10. Performance & Accessibility

**Purpose:** Ensure fast loading and universal access.

**Features:**
- **Performance Optimizations**
  - Lazy loading for images
  - Virtual scrolling for large lists
  - Debounced search input
  - Cached search results
  - Minified CSS/JavaScript
  - CDN for static assets

- **Accessibility**
  - ARIA labels and roles
  - Keyboard navigation support
  - Screen reader friendly
  - High contrast mode
  - Focus indicators
  - Skip to content link

- **SEO** (if public-facing)
  - Semantic HTML structure
  - Meta tags for entries
  - Structured data (JSON-LD)
  - Sitemap generation
  - Open Graph tags

**Implementation Considerations:**
- Test with screen readers
- Validate HTML accessibility
- Use semantic HTML5 elements
- Provide text alternatives for images
- Ensure color contrast ratios meet WCAG standards

---

## Page Layout Structure

### Header Section
```
┌─────────────────────────────────────────────────────────┐
│  [Logo] Encyclopedia Title          [Search Bar] [☰]   │
├─────────────────────────────────────────────────────────┤
│  [Stats] [TOC] [Browse] [Search] [Settings]           │
└─────────────────────────────────────────────────────────┘
```

### Main Content Area
```
┌─────────────────────────────────────────────────────────┐
│  [Sidebar Filters] │  [Entry List/Grid]                │
│                     │                                   │
│  - Has Images       │  [Entry 1]                        │
│  - Has Description  │  [Entry 2]                         │
│  - Category         │  [Entry 3]                         │
│                     │  ...                              │
│                     │  [Pagination]                     │
└─────────────────────────────────────────────────────────┘
```

### Entry Display
```
┌─────────────────────────────────────────────────────────┐
│  Entry Title                                    [🔗] [📷]│
├─────────────────────────────────────────────────────────┤
│  [Image Thumbnail]  Description paragraph...            │
│                        More description...               │
│                                                          │
│  Wikidata: Q123 | Wikipedia: [link]                     │
│  Synonyms: term1, term2                                  │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Core Features (MVP)
1. Table of Contents (alphabetical)
2. Basic search (exact match)
3. Entry display
4. Pagination (20 entries per page)
5. Basic statistics

### Phase 2: Enhanced Search
1. Advanced search types (stemmed, fuzzy)
2. Search filters
3. Search result highlighting
4. Autocomplete suggestions

### Phase 3: Visual Enhancements
1. Image gallery
2. Visual indicators
3. Theme options
4. Responsive design

### Phase 4: Advanced Features
1. Export options
2. Bookmarks/favorites
3. Comparison view
4. Keyboard shortcuts

### Phase 5: Integration & Polish
1. External integrations
2. Performance optimization
3. Accessibility improvements
4. SEO enhancements

---

## Technical Considerations

### Static HTML Generation
- Generate landing page HTML from `AmiEncyclopedia` object
- Include all JavaScript/CSS inline or as separate files
- Self-contained HTML file (no server required)
- Works offline

### Dynamic Web Application
- Use existing Streamlit browser as base
- Enhance with proposed features
- Server-side rendering for large encyclopedias
- Real-time updates if entries modified

### Hybrid Approach
- Static HTML for basic browsing
- JavaScript enhancements for interactivity
- Optional server component for advanced features
- Progressive enhancement (works without JS)

---

## File Structure Proposal

```
encyclopedia/
├── browser/
│   ├── landing_page.py          # Landing page generator
│   ├── templates/
│   │   ├── landing_page.html    # HTML template
│   │   ├── entry_card.html      # Entry card template
│   │   └── toc.html             # TOC template
│   ├── static/
│   │   ├── css/
│   │   │   └── landing.css      # Landing page styles
│   │   └── js/
│   │       ├── landing.js       # Landing page JavaScript
│   │       └── search.js        # Search functionality
│   └── components/
│       ├── toc.py               # TOC generator
│       ├── stats.py             # Statistics generator
│       └── filters.py           # Filter components
```

---

## User Experience Flow

### First-Time Visitor
1. Lands on landing page
2. Sees overview statistics
3. Browses TOC or uses search
4. Clicks entry to view details
5. Explores related entries

### Returning User
1. Uses search to find specific entry
2. Applies filters to narrow results
3. Bookmarks favorite entries
4. Exports filtered results

### Power User
1. Uses advanced search
2. Compares multiple entries
3. Exports data for analysis
4. Uses keyboard shortcuts

---

## Success Metrics

- **Usability**: Users can find entries quickly (<3 clicks)
- **Performance**: Page loads in <2 seconds
- **Accessibility**: WCAG 2.1 AA compliance
- **Engagement**: Users browse multiple entries per session
- **Completeness**: Users can identify incomplete entries easily

---

## Related Documentation

- `encyclopedia/browser/README.md` - Existing browser documentation
- `docs/encyclopedia_browser_design.md` - Browser design document
- `encyclopedia/browser/search_engine.py` - Search engine implementation
- `encyclopedia/utils/validation.py` - Validation functions for statistics

---

**Next Steps:**
1. Review and prioritize features
2. Create detailed mockups/wireframes
3. Implement Phase 1 (MVP)
4. Gather user feedback
5. Iterate based on feedback
