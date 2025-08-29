# Keyword Extraction Tool

A Python-based AI tool for extracting the most important keywords and keyphrases from scientific text documents using state-of-the-art Natural Language Processing models.

## Overview

This tool uses Hugging Face transformers to automatically identify and extract the most relevant keywords from academic texts, research papers, and scientific documents. It's particularly optimized for climate change research and IPCC reports, but can be used with any text content.

## Features

- **AI-Powered Extraction**: Uses pre-trained NLP models for accurate keyword identification
- **Multiple Processing Methods**: Supports sentence-based and chunk-based text processing
- **Batch Processing**: Efficiently handles large documents with configurable batch sizes
- **Flexible Output**: Generates CSV files for easy analysis in Excel or other tools
- **Configurable Results**: Extract top N keywords based on your needs
- **Climate Change Focus**: Optimized examples and demonstrations for climate research

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
```

### Dependencies
The tool requires several key packages:
- **transformers**: Hugging Face NLP models and pipelines
- **torch**: PyTorch backend for deep learning
- **pandas**: Data manipulation and CSV export
- **beautifulsoup4**: HTML parsing and processing
- **tqdm**: Progress bars for batch processing

## Usage

### Basic Command Structure
```bash
python Keyword_extraction.py -i <input_file> -s <save_directory> -o <output_file> -n <number_of_keywords>
```

### Parameters
- `-i, --input`: Input text file path (must end with .txt)
- `-s, --save_path`: Directory where results will be saved
- `-o, --output`: Output CSV filename (default: top_keywords.csv)
- `-n, --top_n`: Number of top keywords to extract (default: 1000)

### Examples

#### Extract Top 500 Keywords
```bash
python Keyword_extraction.py -i chapter6_text.txt -s results/ -o chapter6_keywords.csv -n 500
```

#### Extract Top 1000 Keywords (Default)
```bash
python Keyword_extraction.py -i document.txt -s output/ -o keywords.csv
```

#### Extract Top 100 Keywords
```bash
python Keyword_extraction.py -i research_paper.txt -s analysis/ -o paper_keywords.csv -n 100
```

## How It Works

### 1. Text Processing
The tool reads your input text file and processes it using one of two methods:
- **Sentence-based**: Splits text into individual sentences for processing
- **Chunk-based**: Divides text into 300-word chunks for batch processing

### 2. AI Model
Uses the `ml6team/keyphrase-extraction-kbir-inspec` model, which is:
- Pre-trained on scientific and academic text
- Optimized for keyphrase extraction
- Capable of identifying multi-word phrases and technical terms

### 3. Batch Processing
Processes text in configurable batches (default: 16 chunks) to:
- Optimize memory usage
- Provide progress feedback
- Handle large documents efficiently

### 4. Output Generation
Creates a CSV file containing:
- Extracted keywords/keyphrases
- Frequency counts
- Ranked by importance

## Input Requirements

### File Format
- **Must be a .txt file** (UTF-8 encoding recommended)
- Plain text content (no HTML markup)
- Can contain any length of text

### Content Guidelines
- Works best with academic/scientific content
- Handles technical terminology well
- Supports multiple languages (depending on model)
- Climate change research examples work particularly well

## Output Files

### CSV Format
The output CSV contains:
- **Keyword**: The extracted keyphrase
- **Frequency**: How often it appears in the processed text
- **Rank**: Position in the top-N list

### File Location
All output files are saved to the specified save directory to maintain project structure integrity.

## Advanced Usage

### Customizing Batch Size
Modify the `batch_size` parameter in the `extract_keywords` method:
```python
extractor.extract_keywords(batch_size=32)  # Process 32 chunks at once
```

### Text Processing Methods
The tool supports different text splitting strategies:
- **Sentence**: Natural sentence boundaries (recommended for most content)
- **Chunk**: Fixed word-count chunks (useful for very long documents)

### Model Selection
Currently uses the `ml6team/keyphrase-extraction-kbir-inspec` model, which is optimized for:
- Scientific literature
- Technical documents
- Academic papers
- Research reports

## Troubleshooting

### Common Issues

#### File Not Found
```
ValueError: Please provide a valid text file path ending with ".txt"
```
**Solution**: Ensure your input file exists and has a .txt extension

#### Invalid Save Path
```
ValueError: Please provide a valid saving path
```
**Solution**: Create the output directory before running the tool

#### Memory Issues
**Solution**: Reduce batch size or use chunk-based text processing for very long documents

### Performance Tips
- Use sentence-based processing for most documents
- Adjust batch size based on available memory
- Process very long documents in smaller sections if needed

## Examples and Use Cases

### Climate Change Research
- IPCC report analysis
- Climate adaptation studies
- Carbon sequestration research
- Global warming mitigation papers

### Academic Applications
- Literature review automation
- Research paper summarization
- Content indexing
- Topic modeling

### Content Analysis
- Document classification
- Key concept identification
- Terminology extraction
- Content summarization

## Development Notes

This tool follows established project style guidelines:
- Uses absolute imports with module prefixes
- Maintains clean project structure
- Follows established naming conventions
- Includes comprehensive error handling
- Provides clear user feedback

## Support

For additional help:
1. Check the main project README.md
2. Review the workflow.md file for step-by-step instructions
3. Examine the example outputs in the Dictionary directory
4. Check the requirements.txt for dependency versions

## License

See the main project LICENSE file for details.
