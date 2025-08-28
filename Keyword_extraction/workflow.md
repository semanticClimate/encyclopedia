# Keyword Extraction Tool  

This project helps you:  
1. Convert a chapter in HTML format into plain text (.txt).  
2. Extract the most important keywords from that text using Artificial Intelligence.  
3. Save those keywords into a CSV file (which you can open in Excel).  
---
## Step 1: Clone the Repository  
```bash
https://github.com/semanticClimate/encyclopedia/new/main/Keyword_extraction
```
---
## Create a Virtual Environment

Open the terminal and execute the following commands:

### a) Create a new virtual environment
```sh
python -m venv venv
```

### b) Activate the virtual environment
```sh
venv\Scripts\activate
```

## Install required dependencies
```sh
pip install -r requirements.txt
```
## Extract Keywords
```
python keyword_extraction.py -i Chapter6_text.html -s results/ -o chapter6_keywords.csv -n 500
```
-i → input html file (from Step 4)

-s → folder where results are saved (for example, results/)

-o → name of CSV file (for example, chapter6_keywords.csv)

-n → number of top keywords (for example, 100, 500, 1000)

This extracts the top 1000 keywords.




