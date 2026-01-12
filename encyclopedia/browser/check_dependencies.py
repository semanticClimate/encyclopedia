#!/usr/bin/env python3
"""
Check if all required dependencies are installed.

Run this before launching the browser to diagnose issues.
"""

import sys

print("=" * 60)
print("Dependency Check for Encyclopedia Browser")
print("=" * 60)
print(f"\nPython version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path[:3]}...")
print()

# Check required dependencies
required = {
    "streamlit": "Streamlit web framework",
    "whoosh": "Whoosh search engine",
    "nltk": "NLTK for stemming",
    "lxml": "lxml for HTML processing",
}

optional = {
    "rapidfuzz": "RapidFuzz for fuzzy search (optional)",
}

print("Required Dependencies:")
print("-" * 60)
all_required_ok = True
for package, description in required.items():
    try:
        mod = __import__(package)
        version = getattr(mod, "__version__", "unknown")
        print(f"✓ {package:15} {description:40} (version: {version})")
    except ImportError:
        print(f"✗ {package:15} {description:40} MISSING")
        all_required_ok = False

print("\nOptional Dependencies:")
print("-" * 60)
for package, description in optional.items():
    try:
        mod = __import__(package)
        version = getattr(mod, "__version__", "unknown")
        print(f"✓ {package:15} {description:40} (version: {version})")
    except ImportError:
        print(f"○ {package:15} {description:40} Not installed (optional)")

print("\n" + "=" * 60)
if all_required_ok:
    print("✓ All required dependencies are installed!")
    print("\nYou can launch the browser with:")
    print("  streamlit run encyclopedia/browser/app.py")
else:
    print("✗ Some required dependencies are missing!")
    print("\nInstall missing dependencies with:")
    print("  pip install streamlit whoosh nltk lxml")
    print("\nFor fuzzy search (optional):")
    print("  pip install rapidfuzz")
    print("\nThen download NLTK data:")
    print("  python -m nltk.downloader punkt stopwords")
print("=" * 60)
