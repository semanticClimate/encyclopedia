"""
Test configuration for text links analysis
Defines constants, paths, and test parameters
"""

from pathlib import Path
import os

# Test directory structure
TEST_ROOT = Path(__file__).parent
PROJECT_ROOT = TEST_ROOT.parent.parent  # Go up two levels: test/text_links -> test -> encyclopedia
TEMP_DIR = Path(PROJECT_ROOT, "temp")
OUTPUT_DIR = Path(TEMP_DIR, "text_links_output")

# Input files
ENCYCLOPEDIA_FILE = Path(PROJECT_ROOT, "test", "wg1chap03_dict.html")
ENCYCLOPEDIA_FILE_MINI = Path(PROJECT_ROOT, "test", "wg1chap03_dict_mini.html")

# Test parameters
USE_MINI_FILE = True  # Use mini file for faster tests during development
USE_FULL_FILE_FOR_SHARED_LINKS = True  # Use full file for shared links test
CURRENT_ENCYCLOPEDIA_FILE = ENCYCLOPEDIA_FILE_MINI if USE_MINI_FILE else ENCYCLOPEDIA_FILE

TEST_TERMS = [
    "fingerprinting",
    "External forcing", 
    "Observational data",
    "whiskers",
    "infrared radiation",
    "IPCC",
    "radiosonde data",
    "Argentina"
]

# URL patterns
WIKIPEDIA_SEARCH_PATTERN = r"https://en\.wikipedia\.org/w/index\.php\?search=([^&]+)"
WIKIPEDIA_ARTICLE_PATTERN = r"/wiki/([^#\s]+)"
WIKIPEDIA_FILE_PATTERN = r"/wiki/File:([^#\s]+)"
WIKIPEDIA_HELP_PATTERN = r"/wiki/Help:([^#\s]+)"
CITATION_PATTERN = r"#cite_note-(\d+)"

# Expected output structure
# Function to get the current encyclopedia file to use
def get_encyclopedia_file():
    """Get the current encyclopedia file based on configuration"""
    return CURRENT_ENCYCLOPEDIA_FILE

# Expected output structure
EXPECTED_ENTRY_STRUCTURE = {
    "term": str,
    "name": str,
    "search_url": str,
    "canonical_url": str,
    "description_html": str,
    "description_links": list,
    "external_links": list,
    "file_links": list,
    "help_links": list
}

# Test assertions
MIN_LINKS_PER_ENTRY = 1
MAX_REDIRECT_DEPTH = 5
TIMEOUT_SECONDS = 30
