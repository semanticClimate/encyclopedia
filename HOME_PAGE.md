# 📘 Research Toolkit – Full Documentation

A modular **Streamlit-based research application** for automating literature workflows:

1. **Fetch research papers** (PyGetPapers1)
2. **Extract keywords** (txt2phrases)
3. **Build encyclopedias** (AMILib DICT)
4. **Run NER + generate knowledge graphs** (docanalysis + Cytoscape)

This app works as a complete NLP + Data Extraction pipeline for academic research, climate research, bioinformatics and more.

---

# 📁 Repository Structure
```
research_app:
  app.py: "Main homepage"
  pages:
    "1_Fetch_Papers.py": "Fetch papers (PyGetPapers1)"
    "2_Extract_Keywords.py": "Extract keyphrases (txt2phrases)"
    "3_Build_Encyclopedia.py": "Build encyclopedia (AMILib DICT)"
    "4_NER_Cytoscape.py": "NER + Knowledge Graph"
  data:
    corpora: "Fetched papers stored here"
    txt2phrases_auto: "Auto keyword extraction sessions"
    txt2phrases_uploads: "Upload-based extraction"
    encyclopedias: "Generated encyclopedias"
```

---

# 🚀 1. Clone the Repository

```bash
git clone https://github.com/semanticClimate/encyclopedia.git
git checkout udita
cd encyclopedia/research_app
```
# 📦 2. Installation

## ✔ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate         # Linux/Mac
venv\Scripts\activate            # Windows
```
## ✔ Install Dependencies

```bash
pip install -r requirements.txt
```
---
# Requriments
```
streamlit
pandas
networkx
streamlit-cytoscapejs
datetime
beautifulsoup4
pdfminer.six
pdfplumber
txt2phrases
amilib
pygetpapers1
matplotlib
```
---

# ▶️ 4. Run the Application
```
streamlit run app.py
```
👉 Streamlit will automatically discover all modules inside the /pages/ folder and display them in the sidebar.
---
### 📄 MODULE 1 — Fetch Research Papers

**File:** `1_Fetch_Papers.py`

#### ✨ Features

- Fetch research papers using **PyGetPapers1**

#### Supports multiple APIs:
- europe_pmc  
- crossref  
- arxiv  
- biorxiv / medrxiv  
- openalex  

#### Download options:
- XML  
- PDF  

#### Automatically generates:
- `results.html`
- ZIP archive of the corpus

#### Supports:
- AMILib DataTable generation for visual inspection

---

### 🔑 MODULE 2 — Extract Keywords (txt2phrases)

**File:** `2_Extract_Keywords.py`

#### Supports two keyword extraction modes:

---

#### 🔹 1️⃣ Auto Mode (recommended)

- Automatically detects the folder created in Module 1
- Converts:
  - HTML → TXT
  - PDF → TXT
- Extracts top-N keyphrases 

Produces:

- CSV per document  
- Downloadable ZIP  

---

#### 🔹 2️⃣ Single-File Upload Mode

- Upload a PDF or HTML  
- Converts file → TXT  
- Extracts top-N keywords  
- Shows preview + enables CSV download  

#### 📁 Output Folders

```
data/txt2phrases_auto/
data/txt2phrases_uploads/
```

---

### 📘 MODULE 3 — Build Encyclopedia

**File:** `3_Build_Encyclopedia.py`

#### ✨ Features

- Upload a CSV of extracted keywords  
- Choose description sources:
  - Wikipedia
  - Wiktionary
  - Wikidata
- Uses AMILib DICT to automatically generate an encyclopedia

#### Outputs:
- Fully formatted HTML encyclopedia  

#### 📁 Output Location

```
data/encyclopedias/<ency_name_timestamp>.html
```

---

### 🧬 MODULE 4 — NER & Knowledge Graph

**File:** `4_NER_Cytoscape.py`

#### ✨ Features

- Runs NER using the **docanalysis** module

#### Supported dictionaries include:
- EO_PLANT  
- EO_COMPOUND  
- DISEASE  
- DRUG  
- COUNTRY  
- ORGANIZATION  
- and more  

#### Generates:
- CSV + JSON for each dictionary  

#### Builds an interactive knowledge graph:
- Nodes = PMC documents & extracted entities  
- Edges = weighted co-occurrence relations  

#### Available layouts:
- cose  
- circle  
- grid  
- breadthfirst  
- concentric  

#### Visualization:
- Fully interactive graph using **CytoscapeJS**

---
### 🏠 HOME PAGE

**File:** `app.py`

#### ✨ Features

- Clean landing interface  
- Introduces the toolkit workflow  
- Provides navigation via Streamlit sidebar  

---

### 🎯 6. End-To-End Workflow

The complete research processing pipeline:

- Fetch research papers  
- Extract keywords  
- Build encyclopedia  
- Run NER on corpus  
- Visualize knowledge graph  

#### Produces:

- ✔ Research corpus  
- ✔ Keyword datasets  
- ✔ Encyclopedia HTML  
- ✔ Entity knowledge graph  

All modules are automated and require no manual preprocessing.






