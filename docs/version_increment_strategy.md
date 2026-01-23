# Version Increment Strategy

**Date:** January 23, 2026 (system date of generation)  
**Purpose:** Explain how version increments work and Python-based automation options

## Version Strategy Summary

- **Starting version**: `0.0.1` (major.minor.point)
- **Each commit**: Increases point version (e.g., `0.0.1` → `0.0.2`)
- **--version flag**: All CLI commands must support `--version` to display current version

## How Version Incrementing Works

### Current Approach: Manual Increment

**Process:**
1. Developer makes code changes
2. **Before committing**: Manually edit `encyclopedia/__init__.py`
3. Increment point version: `__version__ = "0.0.1"` → `__version__ = "0.0.2"`
4. Commit with version number in message: `git commit -m "Description (v0.0.2)"`

**Pros:**
- ✅ Simple and explicit
- ✅ Developer has full control
- ✅ No additional tooling required
- ✅ Works immediately
- ✅ Cross-platform (works on all systems)

**Cons:**
- ❌ Requires discipline to remember
- ❌ Easy to forget to increment
- ❌ Manual step adds friction

### Option 1: Python Version Bump Script (Recommended)

**How it works:**
- Python script increments version in `encyclopedia/__init__.py`
- Developer runs script before committing
- Cross-platform (works on Windows, macOS, Linux)

**Implementation:**

Create `scripts/bump_version.py`:
```python
#!/usr/bin/env python3
"""
Version bump script for encyclopedia project.

Increments the point version in encyclopedia/__init__.py.
Usage: python scripts/bump_version.py
"""
import re
import sys
from pathlib import Path


def bump_version():
    """Increment point version in encyclopedia/__init__.py"""
    # Get project root (parent of scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    version_file = project_root / "encyclopedia" / "__init__.py"
    
    if not version_file.exists():
        print(f"ERROR: Could not find {version_file}", file=sys.stderr)
        return 1
    
    # Read current content
    content = version_file.read_text(encoding='utf-8')
    
    # Extract current version
    match = re.search(r'__version__ = "([^"]+)"', content)
    if not match:
        print("ERROR: Could not find __version__ in __init__.py", file=sys.stderr)
        return 1
    
    current_version = match.group(1)
    
    # Parse version parts
    try:
        parts = current_version.split('.')
        if len(parts) != 3:
            raise ValueError("Version must be in format major.minor.point")
        major, minor, point = int(parts[0]), int(parts[1]), int(parts[2])
    except (ValueError, IndexError) as e:
        print(f"ERROR: Invalid version format '{current_version}': {e}", file=sys.stderr)
        return 1
    
    # Increment point version
    new_version = f"{major}.{minor}.{point + 1}"
    
    # Update file
    new_content = re.sub(
        r'__version__ = "[^"]+"',
        f'__version__ = "{new_version}"',
        content
    )
    version_file.write_text(new_content, encoding='utf-8')
    
    print(f"Version bumped: {current_version} → {new_version}")
    print(f"Updated: {version_file}")
    print(f"\nNext steps:")
    print(f"  git add {version_file.relative_to(project_root)}")
    print(f"  git commit -m \"Description (v{new_version})\"")
    
    return 0


if __name__ == "__main__":
    sys.exit(bump_version())
```

**Usage:**
```bash
# From project root
python scripts/bump_version.py

# Output:
# Version bumped: 0.0.1 → 0.0.2
# Updated: encyclopedia/__init__.py
# 
# Next steps:
#   git add encyclopedia/__init__.py
#   git commit -m "Description (v0.0.2)"

# Then commit
git add encyclopedia/__init__.py
git commit -m "Description (v0.0.2)"
```

**Pros:**
- ✅ Cross-platform (Python works on Windows, macOS, Linux)
- ✅ Simple to use - just run Python script
- ✅ Explicit - developer runs when ready
- ✅ Can be integrated into workflow
- ✅ No bash dependency

**Cons:**
- ❌ Still requires manual step
- ❌ Easy to forget to run script
- ❌ Requires Python environment (but project already requires this)

### Option 2: Python Pre-commit Hook

**How it works:**
- Git pre-commit hook written in Python
- Runs automatically before each commit
- Increments version in `encyclopedia/__init__.py`
- Adds updated file to commit

**Implementation:**

Create `.git/hooks/pre-commit` (Python script):
```python
#!/usr/bin/env python3
"""
Git pre-commit hook to automatically increment version.

This hook increments the point version in encyclopedia/__init__.py
before each commit.
"""
import re
import subprocess
import sys
from pathlib import Path


def bump_version():
    """Increment point version in encyclopedia/__init__.py"""
    # Get project root (parent of .git directory)
    git_dir = Path(__file__).parent.parent
    project_root = git_dir.parent
    version_file = project_root / "encyclopedia" / "__init__.py"
    
    if not version_file.exists():
        print(f"WARNING: Could not find {version_file}", file=sys.stderr)
        return False
    
    # Read current content
    content = version_file.read_text(encoding='utf-8')
    
    # Extract current version
    match = re.search(r'__version__ = "([^"]+)"', content)
    if not match:
        print("WARNING: Could not find __version__ in __init__.py", file=sys.stderr)
        return False
    
    current_version = match.group(1)
    
    # Parse version parts
    try:
        parts = current_version.split('.')
        if len(parts) != 3:
            raise ValueError("Version must be in format major.minor.point")
        major, minor, point = int(parts[0]), int(parts[1]), int(parts[2])
    except (ValueError, IndexError) as e:
        print(f"ERROR: Invalid version format '{current_version}': {e}", file=sys.stderr)
        return False
    
    # Increment point version
    new_version = f"{major}.{minor}.{point + 1}"
    
    # Update file
    new_content = re.sub(
        r'__version__ = "[^"]+"',
        f'__version__ = "{new_version}"',
        content
    )
    version_file.write_text(new_content, encoding='utf-8')
    
    # Add updated file to commit
    try:
        subprocess.run(
            ['git', 'add', str(version_file.relative_to(project_root))],
            cwd=project_root,
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Could not add {version_file} to git: {e}", file=sys.stderr)
        return False
    
    print(f"Version incremented: {current_version} → {new_version}")
    return True


if __name__ == "__main__":
    if bump_version():
        sys.exit(0)
    else:
        # Don't fail commit if version bump fails (just warn)
        sys.exit(0)
```

**Setup:**
```bash
# Copy script to .git/hooks/pre-commit
cp scripts/pre-commit-hook.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Or create symlink (if supported)
ln -s ../../scripts/pre-commit-hook.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Pros:**
- ✅ Automatic - no manual step required
- ✅ Never forget to increment
- ✅ Consistent version tracking
- ✅ Cross-platform (Python works everywhere)
- ✅ No bash dependency

**Cons:**
- ❌ Requires hook setup (one-time)
- ❌ Can be bypassed with `--no-verify`
- ❌ May increment version even for non-code commits

### Option 3: Python Post-commit Hook (Validation Only)

**How it works:**
- Git post-commit hook written in Python
- Runs after commit succeeds
- Validates that commit message includes version number
- Warns if version not found in commit message

**Implementation:**

Create `.git/hooks/post-commit` (Python script):
```python
#!/usr/bin/env python3
"""
Git post-commit hook to validate version in commit message.

This hook checks that the commit message includes a version number.
"""
import re
import subprocess
import sys
from pathlib import Path


def check_version_in_commit():
    """Check if commit message contains version number"""
    # Get project root
    git_dir = Path(__file__).parent.parent
    project_root = git_dir.parent
    
    # Get latest commit message
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=%B'],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True
        )
        commit_msg = result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Could not get commit message: {e}", file=sys.stderr)
        return False
    
    # Check for version pattern: (v0.0.1) or v0.0.1
    version_pattern = r'\(?v\d+\.\d+\.\d+\)?'
    if re.search(version_pattern, commit_msg):
        return True
    
    print("WARNING: Commit message doesn't include version number", file=sys.stderr)
    print("Consider amending commit with version number:", file=sys.stderr)
    print("  git commit --amend -m \"Original message (v0.0.X)\"", file=sys.stderr)
    return False


if __name__ == "__main__":
    check_version_in_commit()
    # Don't fail - just warn
    sys.exit(0)
```

**Pros:**
- ✅ Validates version in commit message
- ✅ Doesn't modify files automatically
- ✅ Less intrusive than pre-commit
- ✅ Cross-platform (Python)
- ✅ No bash dependency

**Cons:**
- ❌ Doesn't actually increment version
- ❌ Only validates, doesn't enforce
- ❌ Still requires manual version increment

## Recommendation

### Phase 1: Manual Increment (Current)
- Start with manual increment
- Document process clearly
- Require version in commit messages

### Phase 2: Add Python Version Bump Script (Short-term)
- Create `scripts/bump_version.py`
- Make it easy to run before commits
- Document in README
- Cross-platform Python solution

### Phase 3: Python Pre-commit Hook (Long-term)
- Once process is established, add Python pre-commit hook
- Automate version incrementing
- Keep script as fallback option
- All Python-based (no bash dependency)

## Implementation Checklist

- [x] Update STYLE_GUIDE.md with version strategy
- [x] Update `encyclopedia/__init__.py` to `0.0.1`
- [x] Update `setup.py` to read from `__init__.py` (like amilib)
- [ ] Add `--version` flag to CLI commands
- [ ] Create `scripts/bump_version.py` (Python script)
- [ ] Document version process in README
- [ ] Test `--version` flag works correctly
- [ ] (Optional) Add Python pre-commit hook for automation

## Testing --version Flag

**CLI Commands to Add --version:**

```python
# In encyclopedia/cli/versioned_editor.py
import argparse
from encyclopedia import __version__

parser = argparse.ArgumentParser(...)
parser.add_argument('--version', action='version', 
                   version=f'%(prog)s {__version__}',
                   help='Show version number and exit')
```

**Test:**
```bash
python -m encyclopedia.cli.versioned_editor --version
# Expected output: encyclopedia.cli.versioned_editor 0.0.1
```

## References

- **STYLE_GUIDE.md**: Version Management section
- **amilib pattern**: `../amilib/setup.py` (reads version from `__init__.py`)
- **Semantic Versioning**: https://semver.org/
