# Migration Plan: Encyclopedia Code from amilib to encyclopedia Repository

**Date:** December 22, 2025  
**Status:** Draft - Pending Review

## Executive Summary

This plan outlines the migration of encyclopedia-specific code from `../amilib` to this `encyclopedia` repository, making `amilib` a dependency library rather than containing the encyclopedia implementation.

## Goals

1. **Move encyclopedia implementation** from `amilib` to `encyclopedia` repository
2. **Maintain amilib as dependency** - Keep `amilib` as a library for utilities
3. **Preserve functionality** - No breaking changes to existing workflows
4. **Improve architecture** - Clear separation: `amilib` = utilities, `encyclopedia` = application
5. **Update documentation** - Reflect new structure in all docs

## Current State Analysis

### Files in `../amilib/amilib/` to Migrate

| File | Size | Purpose | Dependencies |
|------|------|---------|--------------|
| `ami_encyclopedia.py` | ~1990 lines | Main encyclopedia class | `ami_html`, `wikimedia`, `ami_dict`, `file_lib`, `util`, `xml_lib` |
| `ami_encyclopedia_args.py` | ~280 lines | CLI argument parsing | `ami_encyclopedia`, `ami_args` |
| `ami_encyclopedia_cluster.py` | ~600 lines | Clustering functionality | `ami_encyclopedia`, `ami_util` |
| `ami_encyclopedia_util.py` | ~200 lines | Utility functions | `ami_encyclopedia` |
| `encyclopedia.css` | ~5KB | CSS stylesheet | None |

### Dependencies on amilib (to remain)

- `amilib.ami_html` - HTML processing utilities
- `amilib.wikimedia` - Wikipedia/Wikidata/Wiktionary lookups
- `amilib.ami_dict` - Dictionary creation and management
- `amilib.file_lib` - File utilities
- `amilib.util` - General utilities
- `amilib.xml_lib` - XML processing
- `amilib.ami_args` - Argument parsing base class

### What Stays in amilib

- All dictionary creation (`ami_dict.py`)
- All Wikimedia integration (`wikimedia.py`)
- All HTML utilities (`ami_html.py`)
- All other utility modules
- CLI entry points (for backward compatibility during transition)

## Target Structure

```
encyclopedia/
├── encyclopedia/                    # NEW: Encyclopedia package
│   ├── __init__.py                 # Package initialization
│   ├── core/
│   │   ├── __init__.py
│   │   ├── encyclopedia.py        # AmiEncyclopedia class (from ami_encyclopedia.py)
│   │   ├── normalizer.py           # Normalization logic (extracted)
│   │   └── merger.py              # Synonym merging (extracted)
│   ├── clustering/
│   │   ├── __init__.py
│   │   └── clusterer.py           # From ami_encyclopedia_cluster.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── args.py                # From ami_encyclopedia_args.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── link_extractor.py      # From ami_encyclopedia_util.py
│   └── resources/
│       └── encyclopedia.css        # CSS stylesheet
├── Keyword_extraction/             # Existing
├── Dictionary/                     # Existing
├── test/                          # Existing
│   └── encyclopedia/              # NEW: Encyclopedia tests
│       ├── __init__.py
│       ├── test_encyclopedia.py
│       ├── test_normalizer.py
│       └── test_merger.py
├── docs/                          # Existing
│   └── migration_plan.md          # This file
├── requirements.txt               # UPDATED: Add amilib dependency
├── setup.py                       # NEW: Package setup
└── README.md                      # UPDATED: Reflect new structure
```

## Migration Steps

### Phase 1: Preparation (Week 1)

#### 1.1 Create Target Structure
```bash
mkdir -p encyclopedia/core
mkdir -p encyclopedia/clustering
mkdir -p encyclopedia/cli
mkdir -p encyclopedia/utils
mkdir -p encyclopedia/resources
mkdir -p test/encyclopedia
```

#### 1.2 Set Up Package Infrastructure
- Create `setup.py` with `amilib` as dependency
- Create `requirements.txt` with `amilib>=X.X.X`
- Create `__init__.py` files following style guide (empty unless agreed)
- Update `.gitignore` if needed

#### 1.3 Document Current Dependencies
- List all imports from `amilib` in encyclopedia code
- Verify all dependencies are available in `amilib`
- Document any potential issues

### Phase 2: Code Migration (Week 2)

#### 2.1 Migrate Core Encyclopedia Class
**File**: `ami_encyclopedia.py` → `encyclopedia/core/encyclopedia.py`

**Changes needed**:
1. Update imports:
   ```python
   # OLD
   from amilib.ami_html import HtmlLib
   from amilib.wikimedia import WikipediaPage
   from amilib.ami_dict import AmiDictionary, AmiEntry
   
   # NEW (same, but verify paths)
   from amilib.ami_html import HtmlLib
   from amilib.wikimedia import WikipediaPage
   from amilib.ami_dict import AmiDictionary, AmiEntry
   ```

2. Update class name (optional - consider keeping `AmiEncyclopedia` for compatibility):
   ```python
   # Option A: Keep name for compatibility
   class AmiEncyclopedia:
       ...
   
   # Option B: Rename to Encyclopedia
   class Encyclopedia:
       ...
   ```

3. Update module docstring to reflect new location

**Testing**: Run existing tests to verify functionality

#### 2.2 Extract Normalization Logic
**Create**: `encyclopedia/core/normalizer.py`

Extract normalization methods from `AmiEncyclopedia`:
- `normalize_by_wikidata_id()`
- `_normalize_wikipedia_url()`
- Related helper methods

**Benefits**: Better separation of concerns, easier testing

#### 2.3 Extract Merging Logic
**Create**: `encyclopedia/core/merger.py`

Extract synonym merging methods:
- `merge_synonyms_by_wikidata_id()`
- `aggregate_synonyms_by_wikidata_id()`
- Related helper methods

#### 2.4 Migrate Clustering
**File**: `ami_encyclopedia_cluster.py` → `encyclopedia/clustering/clusterer.py`

**Changes**:
1. Update import:
   ```python
   # OLD
   from amilib.ami_encyclopedia import AmiEncyclopedia
   
   # NEW
   from encyclopedia.core.encyclopedia import AmiEncyclopedia
   ```

2. Update class name if desired:
   ```python
   # OLD
   class AmiEncyclopediaClusterer:
   
   # NEW (optional)
   class EncyclopediaClusterer:
   ```

#### 2.5 Migrate CLI Arguments
**File**: `ami_encyclopedia_args.py` → `encyclopedia/cli/args.py`

**Changes**:
1. Update imports:
   ```python
   # OLD
   from amilib.ami_encyclopedia import AmiEncyclopedia
   from amilib.ami_args import AbstractArgs
   
   # NEW
   from encyclopedia.core.encyclopedia import AmiEncyclopedia
   from amilib.ami_args import AbstractArgs  # Still in amilib
   ```

2. Consider creating CLI entry point in `setup.py`

#### 2.6 Migrate Utilities
**File**: `ami_encyclopedia_util.py` → `encyclopedia/utils/link_extractor.py`

**Changes**:
1. Update imports if needed
2. Rename class if desired (e.g., `EncyclopediaLinkExtractor`)

#### 2.7 Migrate Resources
**File**: `encyclopedia.css` → `encyclopedia/resources/encyclopedia.css`

No changes needed, just move file.

### Phase 3: Testing (Week 3)

#### 3.1 Create Test Suite
- Copy relevant tests from `amilib/test/` if they exist
- Create new tests in `test/encyclopedia/`
- Test all core functionality:
  - Dictionary → Encyclopedia conversion
  - Normalization by Wikidata ID
  - Synonym merging
  - HTML generation
  - Clustering (if used)

#### 3.2 Integration Testing
- Test with real data from `Dictionary/` directory
- Test with keyword extraction output
- Verify end-to-end pipeline works

#### 3.3 Compatibility Testing
- Test that code still works with `amilib` as dependency
- Verify all imports resolve correctly
- Test CLI if applicable

### Phase 4: Documentation (Week 4)

#### 4.1 Update README
- Add encyclopedia package description
- Update installation instructions
- Add usage examples with new import paths

#### 4.2 Update Pipeline Documentation
- Update `docs/encyclopedia_pipeline_documentation.md`
- Change all references from `../amilib/` to `encyclopedia/`
- Update code locations

#### 4.3 Create API Documentation
- Document all public classes and methods
- Add usage examples
- Document dependencies on `amilib`

#### 4.4 Update Migration Guide
- Document breaking changes (if any)
- Provide migration guide for users
- Document backward compatibility approach

### Phase 5: Backward Compatibility (Week 5)

#### 5.1 Deprecation in amilib
**Option A: Soft Deprecation (Recommended)**
- Keep `ami_encyclopedia.py` in `amilib` with deprecation warning
- Redirect to `encyclopedia` package:
  ```python
  # In amilib/amilib/ami_encyclopedia.py
  import warnings
  warnings.warn(
      "ami_encyclopedia is deprecated. "
      "Use 'from encyclopedia.core.encyclopedia import AmiEncyclopedia' instead.",
      DeprecationWarning,
      stacklevel=2
  )
  from encyclopedia.core.encyclopedia import AmiEncyclopedia
  ```

**Option B: Hard Removal**
- Remove from `amilib` entirely
- Update all `amilib` code that uses it
- Breaking change for `amilib` users

**Recommendation**: Use Option A for 1-2 release cycles, then Option B

#### 5.2 Update amilib Documentation
- Add deprecation notices
- Point to `encyclopedia` repository
- Update examples

### Phase 6: Release (Week 6)

#### 6.1 Version Management
- Create initial version: `encyclopedia v1.0.0`
- Tag release in git
- Update CHANGELOG.md

#### 6.2 Package Distribution (Optional)
- Consider publishing to PyPI if desired
- Or keep as git dependency

#### 6.3 Announcement
- Update project README
- Notify users of migration
- Provide migration guide

## Detailed File Changes

### `setup.py` (NEW)

```python
#!/usr/bin/env python
from pathlib import Path
from setuptools import setup, find_packages

# Read version
version = "1.0.0"  # Update from __init__.py

# Read README
readme = Path("README.md").read_text() if Path("README.md").exists() else ""

setup(
    name="encyclopedia",
    version=version,
    description="Encyclopedia generation from terms with Wikipedia/Wikidata enhancement",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/semanticClimate/encyclopedia",
    packages=find_packages(exclude=["test*"]),
    install_requires=[
        "amilib>=1.0.0",  # Specify minimum version
        "lxml",
        "requests",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "encyclopedia=encyclopedia.cli.args:main",  # If CLI desired
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
```

### `requirements.txt` (UPDATED)

```
# Core dependencies
amilib>=1.0.0

# For keyword extraction (existing)
transformers>=4.20.0
torch>=1.12.0
pandas>=1.5.0
beautifulsoup4>=4.11.0
tqdm>=4.64.0

# For testing
pytest>=7.0.0
pytest-cov>=4.0.0
```

### `encyclopedia/__init__.py`

```python
"""
Encyclopedia package for creating structured encyclopedias from terms.

This package provides functionality to:
- Create dictionaries from terms
- Enhance with Wikipedia/Wikidata/Wiktionary
- Normalize and merge synonyms
- Generate HTML encyclopedias
"""

__version__ = "1.0.0"

# Main exports
from encyclopedia.core.encyclopedia import AmiEncyclopedia

__all__ = ["AmiEncyclopedia"]
```

### Import Path Changes

**Before (in amilib)**:
```python
from amilib.ami_encyclopedia import AmiEncyclopedia
```

**After (in encyclopedia)**:
```python
from encyclopedia.core.encyclopedia import AmiEncyclopedia
# Or
from encyclopedia import AmiEncyclopedia
```

## Testing Strategy

### Unit Tests
- Test each class independently
- Mock `amilib` dependencies where appropriate
- Test edge cases and error handling

### Integration Tests
- Test full pipeline: terms → dictionary → encyclopedia
- Test with real data from `Dictionary/` directory
- Test with keyword extraction output

### Regression Tests
- Compare output with current `amilib` implementation
- Ensure no functionality is lost
- Verify HTML output matches

### Performance Tests
- Compare performance with current implementation
- Identify any regressions
- Optimize if needed

## Risk Assessment

### High Risk
- **Breaking existing workflows**: Mitigate with backward compatibility layer
- **Import path changes**: Mitigate with deprecation warnings and documentation

### Medium Risk
- **Dependency version conflicts**: Mitigate by pinning `amilib` version
- **Missing functionality**: Mitigate with comprehensive testing

### Low Risk
- **Documentation gaps**: Mitigate with thorough documentation updates
- **Performance regressions**: Mitigate with performance testing

## Rollback Plan

If issues arise:

1. **Keep amilib version**: Don't remove `ami_encyclopedia.py` from `amilib` immediately
2. **Version pinning**: Pin to specific `amilib` version in `requirements.txt`
3. **Feature flags**: Use feature flags to switch between old/new implementations
4. **Gradual migration**: Migrate users gradually, not all at once

## Success Criteria

- [ ] All encyclopedia code moved to `encyclopedia` repository
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Backward compatibility maintained (if desired)
- [ ] No breaking changes for end users (or clearly documented)
- [ ] Pipeline documentation reflects new structure
- [ ] README updated with new usage examples

## Timeline

| Phase | Duration | Start Date | End Date |
|-------|----------|------------|----------|
| Phase 1: Preparation | 1 week | TBD | TBD |
| Phase 2: Code Migration | 1 week | TBD | TBD |
| Phase 3: Testing | 1 week | TBD | TBD |
| Phase 4: Documentation | 1 week | TBD | TBD |
| Phase 5: Backward Compatibility | 1 week | TBD | TBD |
| Phase 6: Release | 1 week | TBD | TBD |
| **Total** | **6 weeks** | | |

## Next Steps

1. **Review this plan** with team
2. **Get approval** for migration approach
3. **Set timeline** and assign responsibilities
4. **Create GitHub issues** for each phase
5. **Begin Phase 1** when approved

## Questions to Resolve

1. **Class naming**: Keep `AmiEncyclopedia` or rename to `Encyclopedia`?
2. **Backward compatibility**: How long to maintain deprecation warnings?
3. **CLI**: Create new CLI entry point or keep using `amilib` CLI?
4. **Versioning**: Coordinate with `amilib` versioning?
5. **Distribution**: Publish to PyPI or keep as git dependency?

## References

- Current encyclopedia code: `../amilib/amilib/ami_encyclopedia.py`
- Style guide: `../amilib/docs/style_guide_compliance.md`
- Pipeline documentation: `docs/encyclopedia_pipeline_documentation.md`



