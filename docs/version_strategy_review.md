# Version Strategy Review

**Date:** January 23, 2026 (system date of generation)  
**Purpose:** Review version management strategy from amilib and document for encyclopedia project

## Summary

### amilib Version Strategy

**Single Source of Truth:** `amilib/__init__.py`

```python
# amilib/__init__.py
__version__ = "1.1.0a4" # 2025-11-10
```

**setup.py Pattern:**
```python
# amilib/setup.py
import re
from pathlib import Path

parent = Path(__file__).parent
with open(str(Path(parent, "amilib", "__init__.py"))) as f:
    content = f.read()
version = re.search(r'__version__ = ["\']([^"\']+)["\']', content).group(1)

setup(
    name='amilib',
    version=version,  # Read from __init__.py
    # ...
)
```

**Key Points:**
- ✅ Version stored in `__init__.py` as `__version__`
- ✅ `setup.py` reads version using regex pattern
- ✅ Single source of truth prevents version mismatches
- ✅ Format: `\d.\d.\da\d+` during development (e.g., `1.2.5a21`)

### pygetpapers Style Guide Rule

**Rule:** Every edit should increase the version

- ✅ **Good**: Increment version number for every code change during development
- ❌ **Bad**: Making multiple changes without version bumps

**Rationale**: During development this will be `\d.\d.\da\d+`, e.g. `1.2.5a21`. This prevents confusion with cached installations and makes it clear when changes were made.

### Encyclopedia Current State

**Current Implementation:**
```python
# encyclopedia/__init__.py
__version__ = "1.0.0"
```

```python
# setup.py
version = "1.0.0"  # Hardcoded - NOT reading from __init__.py
```

**Issues:**
- ❌ `setup.py` has hardcoded version (not reading from `__init__.py`)
- ❌ Not following amilib pattern
- ❌ No single source of truth

**Recommendation:**
- ✅ Update `setup.py` to read from `encyclopedia/__init__.py` (like amilib)
- ✅ Make `encyclopedia/__init__.py` the single source of truth
- ✅ Use development version format (`1.0.0a1`, `1.0.0a2`, etc.)

## Version Management Rules Added to STYLE_GUIDE.md

### 1. Single Source of Truth
- Version must be stored in `encyclopedia/__init__.py` as `__version__`
- `setup.py` should read from `__init__.py`, not hardcode

### 2. Version Format
- Development: `\d.\d.\da\d+` (e.g., `1.0.0a1`, `1.2.5a21`)
- Release: Semantic versioning (e.g., `1.0.0`, `1.2.5`)

### 3. Version Increment on Every Edit
- Every code change should increase the version number
- Prevents confusion with cached installations

### 4. Commits Must Include Version Number
- All commits should reference the version number
- Format: `"Description (v1.0.0a2)"`

### 5. Version Update Process
1. Note current version from `encyclopedia/__init__.py`
2. Make code changes
3. Increment version in `encyclopedia/__init__.py`
4. Commit with version number in message
5. Verify `setup.py` reads version correctly

## Action Items

### Immediate
1. ✅ Add version management rules to STYLE_GUIDE.md
2. ⏳ Update `setup.py` to read version from `encyclopedia/__init__.py` (following amilib pattern)
3. ⏳ Update `encyclopedia/__init__.py` to use development version format (`1.0.0a1`)

### Future
- Consider adding version bump script/command
- Consider adding version validation in CI/CD
- Document release process (when to move from `a\d+` to release version)

## References

- **amilib version location**: `../amilib/amilib/__init__.py`
- **amilib setup.py pattern**: `../amilib/setup.py` (lines 7-13)
- **pygetpapers style guide**: `../pygetpapers/docs/styleguide.md` (lines 98-105)
- **Encyclopedia STYLE_GUIDE**: `docs/STYLE_GUIDE.md` (Version Management section)
