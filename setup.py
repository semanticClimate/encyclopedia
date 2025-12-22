#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup script for encyclopedia package.
"""
from pathlib import Path
from setuptools import setup, find_packages

# Read version from __init__.py
version = "1.0.0"

# Read README
readme_path = Path(__file__).parent / "README.md"
readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="encyclopedia",
    version=version,
    description="Encyclopedia generation from terms with Wikipedia/Wikidata enhancement",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/semanticClimate/encyclopedia",
    packages=find_packages(exclude=["test*", "tests*"]),
    install_requires=[
        "amilib>=1.0.0",  # Core dependency
        "lxml>=4.9.0",
        "requests>=2.28.0",
    ],
    python_requires=">=3.8",
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


