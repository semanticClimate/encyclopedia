# Keyword Extraction and Classification Pipeline

This document provides a comprehensive guide to using the `KeywordPipelineWrapper` class for extracting and classifying keywords from HTML files. The pipeline automates the process of converting HTML files to text, extracting keywords, and classifying them into general and specific categories using TF-IDF.

---

## Overview

The pipeline consists of three main steps:
1. **HTML to Text Conversion**: Converts HTML files into plain text files.
2. **Keyword Extraction**: Extracts the most relevant keywords from the text files.
3. **Keyword Classification**: Classifies the extracted keywords into general and specific categories using TF-IDF.

The pipeline is implemented in the `wrapper.py` file and can be executed as a standalone script or integrated into other projects.

---

## How It Works

### 1. HTML to Text Conversion

The first step involves converting HTML files into plain text files. This is done using the `BeautifulSoup` library, which extracts the visible text content from HTML files.

- **Input**: A folder containing `.html` files.
- **Output**: A folder containing `.txt` files, where each `.txt` file corresponds to an HTML file.

#### Code:
```python
def html_to_txt(self):
    html_files = [f for f in os.listdir(self.html_input_folder) if f.endswith(".html")]
    for filename in html_files:
        input_path = os.path.join(self.html_input_folder, filename)
        output_filename = os.path.splitext(filename)[0] + ".txt"
        output_path = os.path.join(self.txt_output_folder, output_filename)

        with open(input_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            text = soup.get_text()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"Converted: {filename} → {output_filename}")
```

---

### 2. Keyword Extraction

The second step extracts keywords from the text files. This step uses the `KeywordExtraction` class, which processes each `.txt` file and generates a corresponding `.csv` file containing the extracted keywords.

- **Input**: A folder containing `.txt` files.
- **Output**: A folder containing `.csv` files, where each `.csv` file contains the extracted keywords, their frequency, and rank.

#### Code:
```python
def extract_keywords(self):
    txt_files = [f for f in os.listdir(self.txt_output_folder) if f.endswith(".txt")]
    for txt_file in txt_files:
        input_path = os.path.join(self.txt_output_folder, txt_file)
        base_name = os.path.splitext(txt_file)[0]
        output_filename = base_name + "_keywords.csv"

        print(f"\nProcessing keyword extraction: {txt_file} ...")

        extractor = KeywordExtraction(
            textfile=input_path,
            saving_path=self.keyword_output_folder,
            output_filename=output_filename,
            top_n=self.top_n,
        )
        extractor.extract_keywords()
```

---

### 3. Keyword Classification

The third step classifies the extracted keywords into general and specific categories using TF-IDF. This step uses the `classify_keywords` function, which processes the keyword `.csv` files and generates three output files:
2. **General Keywords**: Contains keywords that appear in all chapters.
3. **Specific Keywords**: Contains keywords unique to each chapter.

- **Input**: A folder containing keyword `.csv` files.
- **Output**: A folder containing the classified `.csv` files.

#### Code:
```python
def classify_keywords(self):
    classify_keywords(
        input_dir=self.keyword_output_folder,
        output_dir=self.classified_output_folder,
        threshold=self.tfidf_threshold,
        min_freq=self.tfidf_min_freq
    )
```

---

## Full Pipeline Execution

The `run_pipeline` method orchestrates the entire process by executing the three steps in sequence.

#### Code:
```python
def run_pipeline(self):
    print("\nStep 1: Converting HTML to TXT ...")
    self.html_to_txt()

    print("\nStep 2: Extracting Keywords from TXT files ...")
    self.extract_keywords()

    print("\nStep 3: Classifying Keywords into General/Specific ...")
    self.classify_keywords()

    print("\nPipeline completed successfully!")
```

---

## Command-Line Interface (CLI)

The pipeline can be executed from the command line using the following arguments:

### Command:
```bash
python wrapper.py -i <html_input_folder> -t <txt_output_folder> -k <keyword_output_folder> -c <classified_output_folder> [--top_n <number>] [--tfidf_threshold <value>] [--tfidf_min_freq <value>]
```

### Arguments:
- `-i, --html_input`: Path to the folder containing HTML files.
- `-t, --txt_output`: Path to the folder where `.txt` files will be saved.
- `-k, --keyword_output`: Path to the folder where keyword `.csv` files will be saved.
- `-c, --classified_output`: Path to the folder where classified `.csv` files will be saved.
- `--top_n`: Number of top keywords to extract (default: 3500).
- `--tfidf_threshold`: TF-IDF threshold for specific keywords (default: 0.6).
- `--tfidf_min_freq`: Minimum frequency for TF-IDF classification (default: 5).

### Example:
```bash
python wrapper.py -i html_files/ -t txt_files/ -k keywords/ -c classified/ --top_n 3000 --tfidf_threshold 0.7 --tfidf_min_freq 10
```

---

## Folder Structure

### Input:
- `html_input_folder`: Contains `.html` files.

### Intermediate:
- `txt_output_folder`: Contains `.txt` files converted from HTML.
- `keyword_output_folder`: Contains `.csv` files with extracted keywords.

### Output:
- `classified_output_folder`: Contains the following `.csv` files:
  - `merged_keywords.csv`: All keywords from all chapters.
  - `general_keywords.csv`: Keywords common to all chapters.
  - `specific_keywords_<chapter>.csv`: Keywords unique to each chapter.

---

## Example Workflow

1. **Prepare Input**: Place all `.html` files in the `html_files/` folder.
2. **Run Pipeline**:
   ```bash
   python wrapper.py -i html_files/ -t txt_files/ -k keywords/ -c classified/
   ```
3. **View Results**:
   - Check `txt_files/` for converted `.txt` files.
   - Check `keywords/` for extracted keyword `.csv` files.
   - Check `classified/` for classified keyword `.csv` files.

---

## Dependencies

Ensure the following Python packages are installed:
- `beautifulsoup4`
- `pandas`
- `KeywordExtraction` (custom class)
- `classify_keywords` (custom function)

Install dependencies using:
```bash
pip install -r requirements.txt
```

---

## Notes

- Ensure all input folders exist before running the pipeline.
- Adjust `top_n`, `tfidf_threshold`, and `tfidf_min_freq` as needed for your use case.
- The pipeline provides progress updates for each step.

---

## Support

For additional help, refer to the project documentation or contact the development team.




