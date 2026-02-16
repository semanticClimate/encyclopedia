# Phase 2 Review: Consolidate Encyclopedia Code

**Date:** February 9, 2026  
**System Date:** Monday Feb 9, 2026  
**Status:** Review - Not Yet Started

## Overview

Phase 2 aims to consolidate all encyclopedia-specific code from `../amilib` into the `./encyclopedia` project. This phase involves comparing existing implementations, merging functionality, and ensuring feature parity.

## Current State Analysis

### File Size Comparison

| Component | Source (amilib) | Target (encyclopedia) | Size Difference |
|-----------|----------------|---------------------|-----------------|
| Core Encyclopedia | 1,989 lines | 2,285 lines | +296 lines (encyclopedia has more) |
| Clustering | 910 lines | 910 lines | Same size |
| Utilities | 393 lines | 393 lines | Same size |
| CLI Args | 321 lines | 321 lines | Same size |
| **Total** | **3,613 lines** | **3,909 lines** | **+296 lines** |

### Key Observations

1. **Core Encyclopedia (`encyclopedia.py`)**: 
   - Encyclopedia version is **296 lines larger** than amilib version
   - Likely contains additional features or enhancements
   - Needs careful comparison to ensure amilib features aren't lost

2. **Clustering (`clusterer.py`)**:
   - Exact same line count (910 lines)
   - Likely already migrated or identical

3. **Utilities (`link_extractor.py`)**:
   - Exact same line count (393 lines)
   - Likely already migrated or identical

4. **CLI Args (`args.py`)**:
   - Exact same line count (321 lines)
   - Likely already migrated or identical

## Phase 2 Tasks Breakdown

### Task 2.1: Migrate Core Encyclopedia Class

**Source**: `../amilib/amilib/ami_encyclopedia.py` (1,989 lines)  
**Target**: `encyclopedia/core/encyclopedia.py` (2,285 lines)

**Status**: Target already exists and is larger - needs comparison

**Actions Required**:
1. **Compare implementations**:
   - Use diff tool to compare both files
   - Identify features unique to amilib version
   - Identify features unique to encyclopedia version
   - Document differences

2. **Merge missing functionality**:
   - If amilib has features not in encyclopedia: add them
   - If encyclopedia has enhancements: keep them
   - Ensure all public methods exist in both

3. **Update imports**:
   - Verify all imports use `amilib.*` (not relative imports)
   - Ensure no circular dependencies

4. **Test feature parity**:
   - Run tests from both projects
   - Verify all methods work identically
   - Check metadata handling, normalization, merging

**Risk Level**: Medium-High
- Large file with many methods
- Risk of losing functionality during merge
- Need comprehensive testing

**Estimated Effort**: 2-3 days

---

### Task 2.2: Migrate Clustering

**Source**: `../amilib/amilib/ami_encyclopedia_cluster.py` (910 lines)  
**Target**: `encyclopedia/clustering/clusterer.py` (910 lines)

**Status**: Same line count - likely already migrated

**Actions Required**:
1. **Verify migration completeness**:
   - Compare file contents (should be identical or very similar)
   - Check imports use `encyclopedia.core.encyclopedia.AmiEncyclopedia`
   - Verify no references to `amilib.ami_encyclopedia`

2. **Update imports if needed**:
   - Change `from amilib.ami_encyclopedia import AmiEncyclopedia`
   - To: `from encyclopedia.core.encyclopedia import AmiEncyclopedia`

3. **Test clustering functionality**:
   - Run clustering tests
   - Verify it works with encyclopedia version of AmiEncyclopedia

**Risk Level**: Low
- Files appear identical
- Likely already migrated
- Just needs import updates

**Estimated Effort**: 0.5-1 day

---

### Task 2.3: Migrate Utilities

**Source**: `../amilib/amilib/ami_encyclopedia_util.py` (393 lines)  
**Target**: `encyclopedia/utils/link_extractor.py` (393 lines)

**Status**: Same line count - likely already migrated

**Actions Required**:
1. **Compare implementations**:
   - Verify `EncyclopediaLinkExtractor` exists in both
   - Verify `LinkValidator` exists in both
   - Verify `SynonymNormalizer` exists in both

2. **Merge any differences**:
   - If amilib has additional utilities: add them
   - If encyclopedia has enhancements: keep them

3. **Update imports**:
   - Ensure uses `amilib.wikimedia` (should remain)
   - Ensure uses `encyclopedia.core.encyclopedia.AmiEncyclopedia` (not amilib version)

4. **Test utilities**:
   - Test link extraction
   - Test link validation
   - Test synonym normalization

**Risk Level**: Low-Medium
- Files appear similar
- May have minor differences
- Need to verify all classes/methods exist

**Estimated Effort**: 1 day

---

### Task 2.4: Migrate CLI Arguments

**Source**: `../amilib/amilib/ami_encyclopedia_args.py` (321 lines)  
**Target**: `encyclopedia/cli/args.py` (321 lines)

**Status**: Same line count - likely already migrated

**Actions Required**:
1. **Compare implementations**:
   - Verify `EncyclopediaArgs` class exists
   - Compare argument definitions
   - Compare operation handlers

2. **Merge differences**:
   - If amilib has additional operations: add them
   - If encyclopedia has enhancements: keep them

3. **Create standalone CLI entry point**:
   - Create `encyclopedia/cli/__main__.py` or `encyclopedia/cli/main.py`
   - Add `setup.py` entry point: `encyclopedia = encyclopedia.cli.main:main`
   - Allow running: `python -m encyclopedia.cli` or `encyclopedia`

4. **Update imports**:
   - Ensure uses `encyclopedia.core.encyclopedia.AmiEncyclopedia`
   - Ensure uses `amilib.ami_args.AbstractArgs` (should remain)

5. **Test CLI**:
   - Test all operations: create, normalize, merge, add figures, statistics
   - Verify help text
   - Test error handling

**Risk Level**: Medium
- Need to create CLI entry point
- Need to ensure all operations work
- May need to update documentation

**Estimated Effort**: 1-2 days

---

### Task 2.5: Update Dependencies

**Status**: Partially complete

**Actions Required**:
1. **Verify requirements.txt**:
   - Ensure `amilib>=X.X.X` is specified
   - Determine minimum version needed
   - Check if version constraints are correct

2. **Update all imports**:
   - Search for any remaining `from amilib.ami_encyclopedia import`
   - Replace with `from encyclopedia.core.encyclopedia import`
   - Search for `from amilib.ami_encyclopedia_cluster import`
   - Replace with `from encyclopedia.clustering.clusterer import`
   - Search for `from amilib.ami_encyclopedia_util import`
   - Replace with `from encyclopedia.utils.link_extractor import`

3. **Update test files**:
   - Check `test/` directory for imports
   - Update test imports to use encyclopedia versions
   - Ensure tests still pass

4. **Update documentation**:
   - Update README files
   - Update docstrings if needed
   - Update pipeline documentation

5. **Test everything**:
   - Run all tests
   - Verify no import errors
   - Verify functionality works

**Risk Level**: Low-Medium
- Systematic find/replace
- Need to test thoroughly
- May miss some imports

**Estimated Effort**: 1 day

---

## Migration Strategy

### Recommended Order

1. **Task 2.2** (Clustering) - Lowest risk, quick win
2. **Task 2.3** (Utilities) - Low risk, similar to clustering
3. **Task 2.1** (Core Encyclopedia) - Highest risk, needs careful comparison
4. **Task 2.4** (CLI Args) - Medium risk, needs CLI entry point
5. **Task 2.5** (Dependencies) - Ongoing throughout, final verification

### Comparison Tools

**Recommended approach**:
1. Use `diff` or `meld` to visually compare files
2. Use `grep` to find method/class definitions
3. Use Python AST parsing to compare class structures
4. Create comparison script to list methods in each file

**Example comparison script**:
```python
import ast
import sys

def get_class_methods(filepath):
    with open(filepath) as f:
        tree = ast.parse(f.read())
    
    methods = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods[node.name] = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
    return methods

# Compare methods
amilib_methods = get_class_methods('../amilib/amilib/ami_encyclopedia.py')
encyclopedia_methods = get_class_methods('encyclopedia/core/encyclopedia.py')

print("In amilib but not encyclopedia:")
for cls, methods in amilib_methods.items():
    if cls in encyclopedia_methods:
        missing = set(methods) - set(encyclopedia_methods[cls])
        if missing:
            print(f"  {cls}: {missing}")
```

## Testing Strategy

### Unit Tests

1. **Core Encyclopedia**:
   - Test entry creation
   - Test normalization
   - Test synonym merging
   - Test metadata handling
   - Test HTML generation

2. **Clustering**:
   - Test clustering algorithm
   - Test with various entry sets
   - Test performance

3. **Utilities**:
   - Test link extraction
   - Test link validation
   - Test synonym normalization

4. **CLI**:
   - Test all operations
   - Test argument parsing
   - Test error handling

### Integration Tests

1. **End-to-end workflow**:
   - Create dictionary → Create encyclopedia → Normalize → Merge → Generate HTML
   - Verify output matches amilib version

2. **Cross-project compatibility**:
   - Verify encyclopedia works with amilib dependencies
   - Verify no circular dependencies

## Risk Assessment

### High Risk Areas

1. **Core Encyclopedia merge**:
   - Large file with many methods
   - Risk of losing functionality
   - Need careful comparison

2. **Breaking existing code**:
   - Other projects may import from amilib
   - Need deprecation period (Phase 3)

### Medium Risk Areas

1. **CLI entry point creation**:
   - Need to ensure all operations work
   - Need to update documentation

2. **Import updates**:
   - May miss some imports
   - Need comprehensive search

### Low Risk Areas

1. **Clustering and Utilities**:
   - Files appear identical
   - Likely already migrated
   - Just need import updates

## Success Criteria

- [ ] All encyclopedia code consolidated in `encyclopedia` project
- [ ] Feature parity with amilib version verified
- [ ] All tests passing
- [ ] No broken imports
- [ ] CLI entry point created and working
- [ ] Documentation updated
- [ ] Dependencies properly specified

## Timeline Estimate

| Task | Effort | Dependencies |
|------|--------|--------------|
| 2.2 Clustering | 0.5-1 day | None |
| 2.3 Utilities | 1 day | None |
| 2.1 Core Encyclopedia | 2-3 days | 2.2, 2.3 |
| 2.4 CLI Args | 1-2 days | 2.1 |
| 2.5 Dependencies | 1 day | All above |
| **Total** | **5.5-8 days** | |

**Recommended**: 2 weeks (allowing for testing and refinement)

## Next Steps

1. **Create comparison script** to analyze differences
2. **Start with Task 2.2** (Clustering) - quick win
3. **Proceed systematically** through tasks
4. **Test thoroughly** after each task
5. **Document any issues** encountered

## Questions to Resolve

1. **Minimum amilib version**: What version of amilib is required?
2. **Breaking changes**: Are we okay with breaking existing imports (or wait for Phase 3)?
3. **CLI naming**: What should the CLI command be? `encyclopedia` or `encyclopedia-cli`?
4. **Test coverage**: Do we have sufficient tests for all functionality?
5. **Documentation**: Where should CLI documentation live?

---

**Prepared by**: AI Assistant  
**Date**: February 9, 2026  
**Status**: Ready for review and approval
