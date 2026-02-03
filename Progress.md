# Encyclopedia Project: Mutations in Lung Cancer  
Date: 2 Feb 2026  

## Project Topic  
**“Mutations in Lung Cancer.”**  
The aim of this project is to build a structured knowledge base on key genetic mutations, pathways, and biomarkers involved in lung cancer.  

---

## Step 1: Literature Search  
To collect relevant research articles, I used **pygetpapers** to search for publications with the query:  

!pip install pygetpapers

<img width="568" height="22" alt="image" src="https://github.com/user-attachments/assets/262bba35-7476-45cf-9549-feebd1d36e65" />

-The search returned multiple hits, providing a strong research base for the encyclopedia.  
-Total number of hits for the query are 278817

---

## Step 2: Downloading Research Papers  
From the available results, I selected and downloaded **10 PDF research papers** in a Google Colab notebook for initial analysis.  

All PDFs were stored inside a folder named:  

- `paper/`  

---

## Step 3: Converting PDFs into Text + Keyword Extraction  
After downloading the papers, I used **txt2phrases** to:  

- Convert all PDF files into `.txt` format  
- Automatically extract the most important keywords  

The command used was:  

```bash
!txt2phrases auto -i paper/ -o results/ -n 100
```  
<img width="948" height="259" alt="image" src="https://github.com/user-attachments/assets/4ae70d27-7c21-4af2-b2ad-1b3e20d77df7" />



Where:  
- `paper/` contains all the downloaded PDFs  
- `results/` stores the extracted text files and keyword outputs  
- `-n 100` extracts the top 100 keywords  

---


## Step 4: Keywords ----> encyclopedia (using amilib)
(on going)
