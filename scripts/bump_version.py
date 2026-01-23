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
    version_file = Path(project_root, "encyclopedia", "__init__.py")
    
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
    
    # Parse version parts - support both regular and alpha versions
    # Regular: int.int.int (e.g., 0.0.1)
    # Alpha: int.int.aint (e.g., 0.0.a1)
    try:
        parts = current_version.split('.')
        if len(parts) != 3:
            raise ValueError("Version must be in format major.minor.point or major.minor.apoint")
        
        major = int(parts[0])
        minor = int(parts[1])
        point_part = parts[2]
        
        # Check if it's an alpha version (starts with 'a' followed by one or more digits)
        # Supports multi-digit numbers: a1, a10, a99, etc.
        if len(point_part) > 1 and point_part[0] == 'a' and point_part[1:].isdigit():
            # Alpha version: e.g., "a3", "a10", "a99"
            alpha_num = int(point_part[1:])  # Extract all digits after 'a'
            new_alpha_num = alpha_num + 1
            new_version = f"{major}.{minor}.a{new_alpha_num}"
        elif point_part.isdigit():
            # Regular version: e.g., "1", "10", "99" (supports multi-digit numbers)
            point = int(point_part)  # Parse full number (handles 1, 10, 99, etc.)
            new_version = f"{major}.{minor}.{point + 1}"
        else:
            raise ValueError(f"Invalid point version format: '{point_part}' (must be integer or 'a' followed by integer)")
    except (ValueError, IndexError) as e:
        print(f"ERROR: Invalid version format '{current_version}': {e}", file=sys.stderr)
        return 1
    
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
