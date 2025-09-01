# Workflow for Keyword Extraction and Classification

This document outlines the step-by-step process for using the tools provided in this project to extract keywords from HTML files, process them, and classify them into general and chapter-specific categories.

---

## Step 1: Convert HTML Files to Text
###  Download the Chapter
First, download the required chapter from the [IPCC cleaned content repository](https://github.com/semanticClimate/ipcc/tree/main/cleaned_content).

### Script: `html_to_text.py`

This script processes a folder containing HTML files and converts each file into a plain text file.

### Input:
- A folder containing HTML files.

### Output:
- A folder containing `.txt` files, where each `.txt` file corresponds to an HTML file from the input folder.

### Command:
```bash
python html_to_text.py -i <html_folder> -o <output_folder>
```

### Parameters:
- `-i, --input`: Path to the folder containing HTML files.
- `-o, --output`: Path to the folder where the converted `.txt` files will be saved.

---

## Step 2: Extract Keywords from Text Files

### Script: `Keyword_extraction.py`

This script extracts keywords from text files. It supports two types of input:
1. A single `.txt` file.
2. A folder containing multiple `.txt` files.

### Input:
- Either a single `.txt` file or a folder containing `.txt` files.

### Output:
- A CSV file for each input file, containing the extracted keywords.
- The CSV files include columns for the keyword, frequency, and rank.

### Command:
```bash
python Keyword_extraction.py -i <input_path> -s <save_directory> -o <output_file> -n <number_of_keywords>
```

### Parameters:
- `-i, --input`: Path to the input file or folder (must be `.txt` files).
- `-s, --save_path`: Directory where the output CSV files will be saved.
- `-o, --output`: Name of the output CSV file (default: `top_keywords.csv`).
- `-n, --top_n`: Number of top keywords to extract (default: 1000).

### Example:
To process a folder of `.txt` files and extract the top 500 keywords for each file:
```bash
python Keyword_extraction.py -i text_files/ -s results/ -n 500
```

---

## Step 3: Classify Keywords

### Script: `classification.py`

This script takes the keyword CSV files generated in Step 2 and classifies the keywords into three categories:
1. **Merged**: A single file containing all keywords from all chapters.
2. **General**: A file containing keywords that appear in all chapters.
3. **Specific**: Separate files for each chapter, containing keywords unique to that chapter.

### Input:
- A folder containing the keyword CSV files generated in Step 2.

### Output:
- `merged_keywords.csv`: Contains all keywords from all chapters.
- `general_keywords.csv`: Contains keywords common to all chapters.





