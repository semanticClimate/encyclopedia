```
## txt2phrases

A Python library for:

1. **HTML to TXT conversion**  
2. **Keyword extraction using Hugging Face Transformers**  
3. **Per-chapter TF-IDF-based specific keyword classification**

---

## Installation

You can install `txt2phrases` directly from PyPI:

```bash
pip install txt2phrases
```

---

## CLI Usage

## Convert HTML → TXT

Convert all HTML files in a folder to plain text:

```bash
html2txt -i path/to/html_folder -o path/to/output_folder
```

- **-i / --input** : Path to the folder containing HTML files  
- **-o / --output** : Path to the folder where TXT files will be saved  

## Extract keywords from TXT files

Extract top keywords from all TXT files in a folder:

```bash
extract_keywords -i path/to/txt_folder -o path/to/output_folder -n 3500
```

- **-i / --input_folder** : Folder containing TXT files  
- **-o / --output_folder** : Folder to save keyword CSVs  
- **-n / --top_n** : Number of top keywords to extract (default: 3500)  

## Generate per-chapter specific keywords (TF-IDF)

Create per-chapter CSVs listing keywords specific to each chapter:

```bash
specific_keywords -i path/to/csv_folder -o path/to/output_folder -t 0.6 -f 5
```

- **-i / --input_dir** : Folder with per-chapter CSV files containing `keyword,count`  
- **-o / --output_dir** : Folder to save per-chapter specific keyword CSVs  
- **-t / --threshold** : TF-IDF threshold for a keyword to be considered specific (default: 0.6)  
- **-f / --min_freq** : Minimum frequency of a keyword to consider (default: 5)  

---

## Python Usage

## Convert HTML → TXT

```python
from txt2phrases.html2text import html_to_txt_folder

html_to_txt_folder("path/to/html_folder", "path/to/output_folder")
```

## Extract Keywords

```python
from txt2phrases.keyword import KeywordExtraction

extractor = KeywordExtraction(
    textfile="path/to/file.txt",
    saving_path="path/to/output_folder",
    output_filename="keywords.csv",
    top_n=1000
)

top_keywords = extractor.extract_keywords()
```

## Per-Chapter Specific Keywords

```python
from txt2phrases.classify_specific import classify_keywords_split_files

classify_keywords_split_files(
    input_dir="path/to/chapter_csv_folder",
    output_dir="path/to/output_folder",
    threshold=0.6,
    min_freq=5
)
```

---

## Requirements

- Python 3.8+  
- `beautifulsoup4`  
- `pandas`  
- `tqdm`  
- `transformers`  
- `scikit-learn`  

---


```
