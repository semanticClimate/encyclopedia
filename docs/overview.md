# Encyclopedia Project Overview

## Project Summary

The Encyclopedia Project is a comprehensive toolset for extracting and analyzing keywords from scientific documents, with a focus on climate change research and IPCC reports. The project combines AI-powered keyword extraction with structured document storage and analysis capabilities.

## Project Structure

```
encyclopedia/
├── README.md                    # Main project documentation
├── docs/                        # Project documentation
│   └── overview.md             # This overview document
├── Keyword_extraction/          # AI-powered keyword extraction tool
│   ├── README.md               # Tool documentation
│   ├── Keyword_extraction.py   # Main extraction script
│   ├── requirements.txt        # Optimized dependencies (5 packages)
│   ├── requirements_optimized.txt # Version-pinned requirements
│   ├── requirements_minimal.txt # Minimal requirements
│   ├── requirements_cleanup_summary.md # Cleanup documentation
│   └── workflow.md             # Usage workflow
├── Dictionary/                  # Document storage and analysis
│   ├── README.md               # Subproject documentation
│   └── ipcc_wg1/              # IPCC Working Group 1 content
│       ├── ipcc_wg1_ch1/      # Chapter 1: Introduction
│       ├── ipcc_wg1_ch5/      # Chapter 5: Carbon Cycles
│       └── ipcc_wg1_ch6/      # Chapter 6: Climate Forcers
├── temp/                       # Temporary output directory
│   └── wg1_ch1/               # Recent keyword extraction results
└── LICENSE                     # Project license
```

## Core Components

### 1. Keyword_extraction Subproject

**Purpose**: AI-powered keyword extraction from scientific documents using state-of-the-art NLP models.

**Key Features**:
- Uses Hugging Face transformers for accurate keyword identification
- Supports multiple text processing methods (sentence-based, chunk-based)
- Batch processing for large documents with configurable batch sizes
- Generates CSV files for easy analysis in Excel or other tools
- Configurable top-N keyword extraction

**Technology Stack**:
- **Python**: Core programming language
- **Transformers**: Hugging Face NLP models for keyword extraction
- **BeautifulSoup**: HTML parsing and processing
- **Pandas**: Data manipulation and CSV export
- **PyTorch**: Deep learning backend for NLP models

**Recent Improvements**:
- **Dependencies optimized**: Reduced from 32 packages to 5 essential packages (84% reduction)
- **Requirements cleaned**: Eliminated unused and auto-installed dependencies
- **Version compatibility**: Fixed pandas version issues and duplicate entries
- **Documentation enhanced**: Comprehensive README and workflow guides

### 2. Dictionary Subproject

**Purpose**: Structured storage and analysis system for organizing extracted keywords, document content, and metadata.

**Current Content**:
- **IPCC WG1 Chapter 1**: Introduction to climate change science (731KB text, 4,722 keywords)
- **IPCC WG1 Chapter 5**: Global Carbon and Other Biogeochemical Cycles
- **IPCC WG1 Chapter 6**: Short-lived Climate Forcers

**File Formats**:
- **Text files (.txt)**: Clean, readable text without formatting
- **HTML files (.html)**: Structured content with semantic markup and IDs
- **CSV files (.csv)**: Structured data with keyword frequencies and rankings

## Recent Achievements

### Keyword Extraction Success
- **Successfully processed** IPCC Chapter 1 HTML document
- **Extracted 4,722 unique keywords** using AI-powered NLP
- **Generated structured outputs**: CSV with frequencies, text-only list, plain text
- **Processing time**: ~4 minutes for 5,533 text chunks
- **Output location**: `./temp/wg1_ch1/`

### Dependencies Optimization
- **Before**: 32 packages with many unused dependencies
- **After**: 5 essential packages with automatic dependency resolution
- **Benefits**: Faster installation, cleaner environment, easier maintenance
- **Files created**: Multiple requirements variants for different use cases

### Documentation Enhancement
- **Comprehensive README files** for all project components
- **Style guide compliance** following established project standards
- **Usage examples** and troubleshooting guides
- **Technical specifications** and maintenance procedures

## Current Status

### ✅ **Completed**
- Project structure and organization
- Keyword extraction tool with AI models
- Document storage system for IPCC content
- Comprehensive documentation
- Dependencies optimization and cleanup
- Successful keyword extraction from IPCC Chapter 1

### 🔄 **In Progress**
- Analysis of extracted keywords
- Quality assessment of extraction results
- Performance optimization of processing pipeline

### 📋 **Planned**
- Additional IPCC chapter processing
- Enhanced keyword analysis tools
- Search and filtering capabilities
- API access for programmatic use
- Integration with other climate research tools

## Usage Examples

### Extract Keywords from IPCC Chapter
```bash
python Keyword_extraction/Keyword_extraction.py \
  -i ./Dictionary/ipcc_wg1/ipcc_wg1_ch1/html_with_ids.html \
  -s ./temp/wg1_ch1 \
  -o wg1_ch1_keywords.csv \
  -n 1000
```

### View Extracted Keywords
```bash
# View top keywords
head -20 ./temp/wg1_ch1/top_keywords_only.txt

# Analyze in Excel
open ./temp/wg1_ch1/wg1_ch1_keywords.csv
```

## Technical Specifications

### Performance Metrics
- **Processing speed**: ~1.4 chunks/second
- **Memory usage**: Optimized for large documents
- **Output formats**: Multiple formats for different analysis needs
- **Scalability**: Batch processing for documents of any size

### Quality Assurance
- **Source verification**: All content from official IPCC reports
- **Processing validation**: Keywords extracted using established AI models
- **Format consistency**: Standardized file structures and naming
- **Content accuracy**: Maintained through careful processing workflows

## Development Guidelines

### Style Compliance
- **Import style**: Use absolute imports with module prefixes
- **File naming**: Alphanumeric characters and underscores only
- **Code organization**: Follow established patterns and conventions
- **Documentation**: Comprehensive README files for all components

### Best Practices
- **Always propose changes** before implementation
- **Work in small, testable steps**
- **Maintain clean project structure**
- **Follow established naming conventions**
- **Document all decisions and changes**

## Future Roadmap

### Short Term (1-3 months)
- Process additional IPCC chapters
- Enhance keyword analysis capabilities
- Improve processing performance
- Add validation and testing tools

### Medium Term (3-6 months)
- Implement search and filtering
- Create web interface for exploration
- Add metadata management
- Integrate with external datasets

### Long Term (6+ months)
- API development for external access
- Machine learning model improvements
- Cross-document analysis capabilities
- Integration with climate research platforms

## Support and Maintenance

### Documentation
- **README files**: Comprehensive guides for each component
- **Workflow guides**: Step-by-step processing instructions
- **Style guidelines**: Consistent formatting and organization standards
- **Troubleshooting**: Common issues and solutions

### Quality Assurance
- **Regular reviews**: Periodic content and structure validation
- **Version control**: Track changes and maintain content history
- **Testing**: Ensure ongoing functionality and performance
- **Updates**: Keep dependencies and tools current

## Conclusion

The Encyclopedia Project represents a significant advancement in scientific document analysis and keyword extraction. By combining AI-powered NLP with structured storage and comprehensive documentation, it provides researchers with powerful tools for understanding and analyzing climate change literature.

The recent optimizations in dependencies and documentation demonstrate the project's commitment to maintainability and user experience. With successful keyword extraction from IPCC reports and a clear roadmap for future development, the project is well-positioned to become a valuable resource for climate research and scientific document analysis.

---

*Last updated: August 29, 2024*
*Project status: Active development with successful keyword extraction capabilities*




