# __init__.py
"""
txt2phrases: A library for text processing, keyword extraction, and classification.
"""

__version__ = "1.0.0"
__author__ = "Your Name"

try:
    from .html2txt import convert_html_to_text
    from .pdf2txt import convert_pdf_to_text
    from .keyword import KeywordExtraction
    from .classify_specific import classify_keywords_split_files
    from .pygetpaper import main as pygetpaper_main
except ImportError:
    # Handle the case when running as standalone scripts
    from html2txt import convert_html_to_text
    from pdf2txt import convert_pdf_to_text
    from keyword import KeywordExtraction
    from classify_specific import classify_keywords_split_files
    from pygetpaper import main as pygetpaper_main

__all__ = [
    "convert_html_to_text",
    "convert_pdf_to_text",
    "KeywordExtraction",
    "classify_keywords_split_files",
    "pygetpaper_main"
]



