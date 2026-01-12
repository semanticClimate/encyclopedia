# Encyclopedia Project

A comprehensive toolset for extracting and analyzing keywords from scientific documents, with a focus on climate change research and IPCC reports.

## 🆕 New: Encyclopedia Browser

**Interactive web browser for searching and exploring encyclopedia entries!**

- Fast search with exact, stemmed, and fuzzy matching
- Browse entries with pagination
- Support for up to 5,000 entries
- Clean web interface (Streamlit)

**Quick Start:**
```bash
pip install streamlit whoosh nltk lxml rapidfuzz
python -m nltk.downloader punkt stopwords
pip install -e .
python encyclopedia/browser/run_browser.py
```

See [encyclopedia/browser/QUICK_START.md](encyclopedia/browser/QUICK_START.md) for details.

## Example and info

  - [Demo book](https://vivliostyle.org/viewer/#src=https://github.com/semanticClimate/demo_book/blob/main/manifest.jsonld)
  - [Blogpost](https://semanticclimate.github.io/p/en/posts/climate_encyclopedia/)

## Project Overview

This project consists of two main subprojects that work together to process scientific documents and extract meaningful insights:

1. **Keyword_extraction** - AI-powered keyword extraction from text documents
2. **Dictionary** - Structured storage and analysis of extracted keywords and document content

## Subprojects

### Keyword_extraction
A Python-based tool that uses state-of-the-art Natural Language Processing (NLP) models to extract the most important keywords and keyphrases from scientific text documents. Built with Hugging Face transformers and optimized for academic content.

**Key Features:**
- AI-powered keyword extraction using pre-trained models
- Support for multiple text processing methods (sentence-based, chunk-based)
- Batch processing for large documents
- CSV output format for easy analysis
- Configurable top-N keyword extraction

**Use Cases:**
- Academic paper analysis
- Research document summarization
- Content indexing and search
- Literature review automation

### Dictionary
A structured storage system for organizing extracted keywords, document content, and metadata. Currently contains processed IPCC Working Group 1 reports with extracted keywords and full text content.

**Key Features:**
- Organized storage of document chapters
- Keyword frequency analysis
- HTML and plain text document versions
- CSV exports for data analysis
- Structured directory organization

**Current Content:**
- IPCC WG1 Chapter 1: Introduction
- IPCC WG1 Chapter 5: Global Carbon and Other Biogeochemical Cycles
- IPCC WG1 Chapter 6: Short-lived Climate Forcers

### Encyclopedia Browser
A web-based browser for searching and exploring encyclopedia entries. Supports up to 5,000 entries with advanced search capabilities.

**Key Features:**
- Fast full-text search with exact, stemmed, and fuzzy matching
- Interactive web interface (Streamlit)
- HTML content rendering
- Browse and search functionality
- Support for large encyclopedias

**Quick Start:**
```bash
# Install browser dependencies
pip install -r encyclopedia/browser/requirements.txt
python -m nltk.downloader punkt stopwords

# Launch browser
streamlit run encyclopedia/browser/app.py
```

See [encyclopedia/browser/README.md](encyclopedia/browser/README.md) for full tutorial.

## Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd encyclopedia

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For encyclopedia browser (optional)
pip install -r encyclopedia/browser/requirements.txt
python -m nltk.downloader punkt stopwords
```

### Basic Usage

#### Extract Keywords from a Document
```bash
cd Keyword_extraction
python Keyword_extraction.py -i your_document.txt -s results/ -o keywords.csv -n 500
```

**Parameters:**
- `-i`: Input text file path
- `-s`: Output directory for results
- `-o`: Output CSV filename
- `-n`: Number of top keywords to extract

#### View Extracted Keywords
```bash
# Navigate to Dictionary directory to view processed content
cd Dictionary/ipcc_wg1/ipcc_wg1_ch1
# View top keywords
cat top_keywords_only.txt
# Or open CSV file in Excel/Google Sheets
open top_keywords.csv
```

## Project Structure

```
encyclopedia/
├── README.md                    # This file
├── Keyword_extraction/          # Keyword extraction tool
│   ├── README.md               # Subproject documentation
│   ├── Keyword_extraction.py   # Main extraction script
│   ├── requirements.txt        # Python dependencies
│   └── workflow.md            # Usage workflow
├── Dictionary/                  # Document storage and analysis
│   ├── README.md               # Subproject documentation
│   └── ipcc_wg1/              # IPCC Working Group 1 content
│       ├── ipcc_wg1_ch1/      # Chapter 1 content and keywords
│       ├── ipcc_wg1_ch5/      # Chapter 5 content and keywords
│       └── ipcc_wg1_ch6/      # Chapter 6 content and keywords
└── LICENSE                     # Project license
```

## Technology Stack

- **Python**: Core programming language
- **Transformers**: Hugging Face NLP models for keyword extraction
- **BeautifulSoup**: HTML parsing and processing
- **Pandas**: Data manipulation and CSV export
- **PyTorch**: Deep learning backend for NLP models

## Contributing

This project follows established style guidelines:

- Use absolute imports with module prefixes
- Keep `__init__.py` files empty unless explicitly agreed
- Follow established naming conventions (alphanumeric + underscores only)
- Always propose changes before implementation
- Work in small, testable steps

## License

See [LICENSE](LICENSE) file for details.

## Support

For questions or issues:
1. Check the subproject-specific README files
2. Review the workflow documentation in `Keyword_extraction/workflow.md`
3. Examine existing examples in the `Dictionary` directory

## Development Notes

- All output files are stored in designated directories to maintain project structure
- The project follows climate change research examples for demonstrations
- Keywords are extracted using the `ml6team/keyphrase-extraction-kbir-inspec` model
- Document processing supports both HTML and plain text formats
