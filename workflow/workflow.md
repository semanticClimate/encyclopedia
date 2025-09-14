# Workflow for Running the Keyword Extraction Tool

This guide explains how to set up and run the Keyword Extraction Tool. Follow the steps below carefully.

---

## Prerequisites

Before you begin, ensure you have the following:
1. **Python Installed**: Download and install Python (version 3.8 or higher) from [python.org](https://www.python.org/).
2. **Text Editor or IDE**: Install a text editor like Visual Studio Code or any other IDE.
3. **Command Line Access**: Use Command Prompt (Windows) or Terminal (Mac/Linux).

---

## Step 1: Set Up the Environment

1. **Download the Project**:
   - Download the `Keyword_extraction` folder and save it to your computer.

2. **Open the Command Line**:
   - Navigate to the folder where the project is saved. For example:
     ```bash
     cd path/to/Keyword_extraction
     ```

3. **Create a Virtual Environment**:
   - Run the following command to create a virtual environment:
     ```bash
     python -m venv venv
     ```
   - Activate the virtual environment:
     - On Windows:
       ```bash
       venv\Scripts\activate
       ```
     - On Mac/Linux:
       ```bash
       source venv/bin/activate
       ```

4. **Install Required Libraries**:
   - Install the libraries listed in the `requirements.txt` file:
     ```bash
     pip install -r requirements.txt
     ```

---

## Step 2: Run the Pipeline

The pipeline processes HTML files, extracts keywords, and classifies them. Follow these steps:

1. **Prepare Input Files**:
   - Place all your `.html` files in a folder (e.g., `html_files`).

2. **Run the Pipeline**:
   - Use the following command to run the pipeline:
     ```bash
     python wrapper.py -i html_files/ -t txt_files/ -k keywords/ -g tfidf_output/ -h hybrid_output/
     ```
   - Replace the folder names (`html_files`, `txt_files`, etc.) with your desired folder paths.

3. **View Results**:
   - After the pipeline runs, you will find the following output:
     - `txt_files/`: Contains plain text files converted from HTML.
     - `keywords/`: Contains CSV files with extracted keywords.
     - `tfidf_output/`: Contains classified keywords (general and specific).
     - `hybrid_output/`: Contains hybrid classification results.

---

## Step 3: Troubleshooting

If you encounter any issues:
1. **Check Python Installation**:
   - Ensure Python is installed and added to your system's PATH.

2. **Check Folder Paths**:
   - Ensure the input folder paths are correct.

3. **Reinstall Dependencies**:
   - Run the following command to reinstall libraries:
     ```bash
     pip install --force-reinstall -r requirements.txt
     ```

---

## Example Workflow

Here’s an example of how to run the pipeline:

1. Place your `.html` files in a folder called `html_files`.
2. Run the following command:
   ```bash
   python wrapper.py -i html_files/ -t txt_files/ -k keywords/ -g tfidf_output/ -h hybrid_output/
   ```
3. Check the output folders for results:
   - `txt_files/`: Contains converted text files.
   - `keywords/`: Contains extracted keywords.
   - `tfidf_output/`: Contains classified keywords.
   - `hybrid_output/`: Contains hybrid classification results.

---

## Support

If you need help, contact the project team or refer to the documentation in the `README.md` file.# Keyword Extraction and Classification Pipeline

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

The third step classifies the extracted keywords into general and specific categories using TF-IDF. This step uses the `classify_keywords` function, which processes the keyword `.csv` files and generates three output files:# Workflow for Keyword Extraction and Classification

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
### Command
```
python Keyword_extraction.py -i <input_folder> -o <output_folder>
```
```
-i,--input_dir:Path of input folder which contains keyword.csv file
-o,--output_dir:Path of output folder 

### Output:
- `merged_keywords.csv`: Contains all keywords from all chapters.
- `general_keywords.csv`: Contains keywords common to all
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




