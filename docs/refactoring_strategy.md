# Encyclopedia Refactoring Strategy

**Date:** February 9, 2026  
**System Date:** Monday Feb 9, 2026  
**Status:** Phase 1 In Progress

## Executive Summary

This document proposes a strategy for refactoring encyclopedia functionality across two projects: `../amilib` and `./encyclopedia`. The goal is to consolidate encyclopedia-specific code into the `encyclopedia` project while maintaining `amilib` as a utility library, and address several architectural concerns.

## Current State Analysis

### Encyclopedia Functionality in `../amilib`

The `amilib` project contains encyclopedia functionality that was added as an extension to the dictionary (`--DICT`) functionality. Key components include:

#### Core Files:
1. **`amilib/ami_encyclopedia.py`** (~1990 lines)
   - Main `AmiEncyclopedia` class
   - Entry extraction from HTML dictionaries
   - Wikidata ID normalization
   - Synonym merging and aggregation
   - HTML generation for normalized encyclopedias
   - Metadata management (created, last_edited, actions, hidden entries, etc.)
   - Entry classification and categorization

2. **`amilib/ami_encyclopedia_args.py`** (~280 lines)
   - CLI argument parsing for `--ENCYCLOPEDIA` operations
   - Subparser integration with main `amilib` CLI
   - Operations: create, normalize, merge, add figures, statistics

3. **`amilib/ami_encyclopedia_cluster.py`** (~600 lines)
   - Clustering functionality for encyclopedia entries
   - Description similarity-based clustering
   - `AmiEncyclopediaClusterer` class

4. **`amilib/ami_encyclopedia_util.py`** (~390 lines)
   - Link extraction and validation utilities
   - `EncyclopediaLinkExtractor` class
   - `LinkValidator` class
   - `SynonymNormalizer` class

5. **`amilib/dict_args.py`**
   - CLI arguments for `--DICT` operations
   - Dictionary creation from words/files/CSV
   - Wikimedia content enhancement (Wikipedia, Wikidata, Wiktionary)

#### Dependencies on amilib (to remain):
- `amilib.ami_dict` - Dictionary creation (`AmiDictionary`, `AmiEntry`)
- `amilib.wikimedia` - Wikipedia/Wikidata/Wiktionary lookups
- `amilib.ami_html` - HTML processing utilities
- `amilib.file_lib` - File utilities
- `amilib.util` - General utilities
- `amilib.xml_lib` - XML processing
- `amilib.ami_args` - Argument parsing base class

#### Key Functionality:
- **Dictionary Creation**: `AmiDictionary.create_dictionary_from_words()` creates basic dictionary structure
- **Enhancement**: Adds Wikipedia pages, Wikidata IDs, Wiktionary definitions
- **HTML Generation**: Converts dictionary to HTML format with semantic markup
- **Encyclopedia Creation**: Parses HTML dictionary into `AmiEncyclopedia` entries
- **Normalization**: Groups entries by Wikidata ID to identify synonyms
- **Merging**: Aggregates synonyms into canonical entries
- **Output**: Generates normalized HTML encyclopedia

### Encyclopedia Functionality in `./encyclopedia`

The `encyclopedia` project contains some encyclopedia functionality that has already been migrated or developed independently:

#### Core Files:
1. **`encyclopedia/core/encyclopedia.py`** (~2286 lines)
   - `AmiEncyclopedia` class (appears to be a copy/migration from amilib)
   - Same core functionality as amilib version
   - Entry management, normalization, merging
   - Currently imports from `amilib` for dependencies

2. **`encyclopedia/cli/args.py`** (~302 lines)
   - `EncyclopediaArgs` class for CLI operations
   - Similar to `ami_encyclopedia_args.py` but in encyclopedia project

3. **`encyclopedia/cli/versioned_editor.py`**
   - Versioned editor functionality for encyclopedia entries
   - Browser-based editing interface

4. **`encyclopedia/utils/encyclopedia_builder.py`**
   - Utility functions for building encyclopedias
   - Wrapper functions around amilib dictionary creation

5. **`encyclopedia/utils/link_extractor.py`**
   - Link extraction utilities (similar to `ami_encyclopedia_util.py`)

6. **`encyclopedia/browser/`**
   - Web-based browser for searching encyclopedia entries
   - Streamlit-based interface
   - Search engine with indexing capabilities

#### Additional Components:
- **`Keyword_extraction/`** - AI-powered keyword extraction (separate concern)
- **`Dictionary/`** - Storage for processed keywords and documents
- **`txt2phrases/`** - Text to phrases conversion (needs removal - see below)

### Key Differences: DICT vs ENCYCLOPEDIA

**AmiDictionary (`--DICT`)**:
- Creates a list of entries from terms
- Each entry has: term, name, optional Wikipedia/Wikidata/Wiktionary content
- Output: HTML dictionary with entries
- Purpose: Basic term-to-content mapping
- Structure: Flat list of entries

**AmiEncyclopedia (`--ENCYCLOPEDIA`)**:
- Built on top of `AmiDictionary` (composition relationship)
- Adds normalization by Wikidata ID
- Merges synonyms (entries with same Wikidata ID)
- Adds metadata tracking (actions, hidden entries, disambiguation selections)
- Output: Normalized HTML encyclopedia with merged entries
- Purpose: Semantic, normalized knowledge base
- Structure: Normalized entries grouped by Wikidata ID

**Key Insight**: An `AmiDictionary` is essentially a list of encyclopedia entries. The main difference is that `AmiEncyclopedia` adds:
1. Wikidata ID-based normalization
2. Synonym merging
3. Metadata tracking
4. Enhanced HTML output with normalization indicators

## Issues to Address

### 1. txt2phrases Subproject

**Current State**: `txt2phrases/` directory exists in `encyclopedia` project

**Purpose**: 
- Converts PDF/HTML to text
- Extracts keywords using AI models (Hugging Face transformers)
- Classifies keywords using TF-IDF
- Creates wordlists from documents

**Why it needs removal**:
- It's a separate concern from encyclopedia creation
- Main purpose is wordlist creation (precursor to encyclopedia, but not encyclopedia itself)
- Should be its own project
- Currently used by `scripts/extract_keyphrases_and_create_encyclopedia.py` and `scripts/extract_keyphrases_from_papers.py`

**Dependencies**:
- Used by encyclopedia scripts to extract terms from papers
- Can be replaced with direct import if moved to separate project

### 2. DICT vs ENCYCLOPEDIA Overlap

**Current State**: Both exist in amilib, with significant overlap

**Analysis**:
- `AmiDictionary` creates entries from terms
- `AmiEncyclopedia` uses `AmiDictionary` internally (composition)
- The HTML output formats are very similar
- Main difference is normalization and merging in encyclopedia

**Future Direction**: 
- Focus on encyclopedias going forward
- Dictionary creation remains in amilib as a utility
- Encyclopedia becomes the primary output format

### 3. wikimedia.py Location

**Current State**: `amilib/wikimedia.py` contains Wikipedia/Wikidata/Wiktionary integration

**Decision**: Keep in amilib
- Used by both dictionary and encyclopedia creation
- General-purpose Wikimedia integration
- Will continue to be developed for encyclopedia needs
- Shared utility across projects

### 4. Future Features

**Planned Enhancements**:
- Search capabilities in `AmiEncyclopedia` (partially implemented in `encyclopedia/browser/`)
- Link creation between encyclopedia entries
- Knowledge graph generation from encyclopedia links

**Current State**:
- Browser-based search exists (`encyclopedia/browser/`)
- Link extraction exists (`encyclopedia/utils/link_extractor.py`, `amilib/ami_encyclopedia_util.py`)
- Knowledge graph functionality not yet implemented

## Proposed Refactoring Strategy

### Phase 1: Remove txt2phrases (Week 1) - COMPLETED

**Goal**: Extract `txt2phrases` to its own project

**Status**: ✅ COMPLETED - GitHub repository created at https://github.com/semanticClimate/txt2phrases
**Completion Date**: February 9, 2026

**Steps**:
1. ✅ Create new repository `txt2phrases` (or identify existing location)
   - Repository: https://github.com/semanticClimate/txt2phrases
2. ✅ Move `txt2phrases/` directory to new project
   - Content copied to ../txt2phrases repository
3. ✅ Update `encyclopedia` scripts that use it:
   - `scripts/extract_keyphrases_and_create_encyclopedia.py` - Already uses external import
   - `scripts/extract_keyphrases_from_papers.py` - Already uses external import
4. ✅ Update imports to use external package - Already done
5. ✅ Update `requirements.txt` to include `txt2phrases` as dependency
6. ✅ Remove `txt2phrases/` from `encyclopedia` project

**Dependencies**: None - isolated change

### Phase 2: Consolidate Encyclopedia Code (Weeks 2-3)

**Goal**: Move all encyclopedia-specific code from `amilib` to `encyclopedia`

**Steps**:

#### 2.1 Migrate Core Encyclopedia Class
- **Source**: `amilib/ami_encyclopedia.py`
- **Target**: `encyclopedia/core/encyclopedia.py` (already exists, needs update)
- **Action**: 
  - Compare amilib version with encyclopedia version
  - Merge any missing functionality
  - Update imports to use `amilib` dependencies
  - Ensure feature parity

#### 2.2 Migrate Clustering
- **Source**: `amilib/ami_encyclopedia_cluster.py`
- **Target**: `encyclopedia/clustering/clusterer.py` (already exists)
- **Action**: 
  - Move clustering code
  - Update imports to use `encyclopedia.core.encyclopedia.AmiEncyclopedia`

#### 2.3 Migrate Utilities
- **Source**: `amilib/ami_encyclopedia_util.py`
- **Target**: `encyclopedia/utils/link_extractor.py` (already exists)
- **Action**: 
  - Merge link extraction utilities
  - Consolidate duplicate functionality
  - Keep `amilib.wikimedia` imports

#### 2.4 Migrate CLI Arguments
- **Source**: `amilib/ami_encyclopedia_args.py`
- **Target**: `encyclopedia/cli/args.py` (already exists)
- **Action**: 
  - Merge CLI argument handling
  - Create standalone CLI entry point
  - Remove `--ENCYCLOPEDIA` from amilib CLI (or deprecate)

#### 2.5 Update Dependencies
- Update all imports in `encyclopedia` to use `amilib` as external dependency
- Ensure `requirements.txt` includes `amilib>=X.X.X`
- Test all functionality works with amilib as dependency

### Phase 3: Deprecate Encyclopedia in amilib (Week 4)

**Goal**: Remove encyclopedia code from amilib while maintaining backward compatibility

**Steps**:
1. Add deprecation warnings to amilib encyclopedia modules
2. Redirect imports to `encyclopedia` package:
   ```python
   # In amilib/ami_encyclopedia.py
   import warnings
   warnings.warn(
       "ami_encyclopedia is deprecated. "
       "Use 'from encyclopedia.core.encyclopedia import AmiEncyclopedia' instead.",
       DeprecationWarning,
       stacklevel=2
   )
   from encyclopedia.core.encyclopedia import AmiEncyclopedia
   ```
3. Update amilib documentation
4. Maintain for 1-2 release cycles
5. Remove after migration period

### Phase 4: Enhance Encyclopedia Project (Weeks 5-6)

**Goal**: Add planned features and improve architecture

**Steps**:

#### 4.1 Search Capabilities
- Integrate browser search (`encyclopedia/browser/`) into core `AmiEncyclopedia`
- Add search methods to `AmiEncyclopedia` class
- Create search index during normalization

#### 4.2 Link Management
- Enhance link extraction utilities
- Add link creation between entries
- Store link graph in encyclopedia metadata

#### 4.3 Knowledge Graph
- Design knowledge graph structure
- Implement graph generation from encyclopedia links
- Export to graph formats (RDF, GraphML, etc.)

#### 4.4 Architecture Improvements
- Separate normalization logic into `encyclopedia/core/normalizer.py`
- Separate merging logic into `encyclopedia/core/merger.py`
- Improve separation of concerns

### Phase 5: Documentation and Testing (Week 7)

**Goal**: Update documentation and ensure comprehensive testing

**Steps**:
1. Update all documentation to reflect new structure
2. Update pipeline diagrams
3. Create migration guide for users
4. Write comprehensive tests
5. Update README files

## Detailed Migration Plan

### File Mapping

| Source (amilib) | Target (encyclopedia) | Status | Notes |
|----------------|----------------------|--------|-------|
| `ami_encyclopedia.py` | `core/encyclopedia.py` | Exists | Needs merge/update |
| `ami_encyclopedia_cluster.py` | `clustering/clusterer.py` | Exists | Needs update |
| `ami_encyclopedia_util.py` | `utils/link_extractor.py` | Exists | Needs merge |
| `ami_encyclopedia_args.py` | `cli/args.py` | Exists | Needs merge |
| `encyclopedia.css` | `resources/encyclopedia.css` | Exists | Already migrated |

### Import Changes

**Before**:
```python
from amilib.ami_encyclopedia import AmiEncyclopedia
from amilib.ami_encyclopedia_cluster import AmiEncyclopediaClusterer
from amilib.ami_encyclopedia_util import EncyclopediaLinkExtractor
```

**After**:
```python
from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.clustering.clusterer import AmiEncyclopediaClusterer
from encyclopedia.utils.link_extractor import EncyclopediaLinkExtractor
```

### Dependencies

**encyclopedia/requirements.txt**:
```
amilib>=1.1.0  # Minimum version with required features
txt2phrases>=1.0.3  # After Phase 1
lxml>=4.9.0
requests>=2.28.0
```

## Risk Assessment

### High Risk
- **Breaking existing workflows**: Mitigate with deprecation period and backward compatibility
- **Import path changes**: Mitigate with deprecation warnings and clear migration guide

### Medium Risk
- **Feature parity**: Ensure all amilib functionality exists in encyclopedia version
- **Dependency version conflicts**: Pin amilib version in requirements.txt

### Low Risk
- **Documentation gaps**: Comprehensive documentation updates in Phase 5
- **Performance regressions**: Performance testing during migration

## Success Criteria

- [x] `txt2phrases` removed from encyclopedia project
- [ ] All encyclopedia code consolidated in `encyclopedia` project
- [ ] All amilib encyclopedia code deprecated/removed
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Search capabilities integrated
- [ ] Link management enhanced
- [ ] Knowledge graph foundation in place
- [ ] No breaking changes for end users (or clearly documented)

## Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Remove txt2phrases | 1 week | None |
| Phase 2: Consolidate Code | 2 weeks | Phase 1 |
| Phase 3: Deprecate in amilib | 1 week | Phase 2 |
| Phase 4: Enhance Features | 2 weeks | Phase 2 |
| Phase 5: Documentation | 1 week | All phases |
| **Total** | **7 weeks** | |

## Questions to Resolve

1. **txt2phrases location**: Where should txt2phrases project be located? New repo or existing?
   - ✅ **Resolved**: GitHub repository created at https://github.com/semanticClimate/txt2phrases
2. **Backward compatibility**: How long to maintain deprecation warnings in amilib?
3. **CLI integration**: Keep separate CLI or integrate with amilib CLI?
4. **Version coordination**: Coordinate versioning with amilib releases?
5. **Knowledge graph format**: What format for knowledge graph export?

## Next Steps

1. **Review this strategy** with team
2. **Resolve questions** above
3. **Get approval** for approach
4. **Create GitHub issues** for each phase
5. **Begin Phase 1** when approved

## References

- Current amilib encyclopedia code: `../amilib/amilib/ami_encyclopedia.py`
- Current encyclopedia code: `./encyclopedia/core/encyclopedia.py`
- Migration plan (previous): `docs/migration_plan.md`
- Pipeline documentation: `docs/encyclopedia_pipeline_documentation.md`
