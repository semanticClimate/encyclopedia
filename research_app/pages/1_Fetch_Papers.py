import streamlit as st
import subprocess
import os
import shutil
from datetime import datetime

# -------------------------------------------------------
# 🔧 Page Configuration
# -------------------------------------------------------
st.set_page_config(page_title="Fetch Research Papers", layout="wide")

st.title("📄 Fetch Research Papers using PyGetPapers1")
st.markdown("""
Fetch research papers from various repositories using **PyGetPapers1**.  
Supports only **XML** and **PDF** downloads for simplicity.
""")

# -------------------------------------------------------
# 🧠 User Inputs
# -------------------------------------------------------
st.markdown("### 🧩 Search Parameters")

query = st.text_input("🔍 Enter your search query", placeholder="e.g. Machine learning in healthcare")

corpus_name = st.text_input(
    "🗂️ Enter corpus name (folder will be created automatically)",
    placeholder="e.g. AI_Healthcare_Review"
)

# --- Choose API Source ---
api_options = [
    "europe_pmc",
    "crossref",
    "arxiv",
    "biorxiv",
    "medrxiv",
    "rxivist",
    "openalex"
]
selected_api = st.selectbox("🌐 Select source repository (API)", api_options, index=0)

# --- Select Date Range ---
st.markdown("### 🗓️ Optional Date Filters")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("📅 Start Date (optional)", value=None)
with col2:
    end_date = st.date_input("📅 End Date (optional)", value=None)

# --- Choose Formats ---
st.markdown("### 📦 Select formats to download")
xml_option = st.checkbox("Download XML files", value=True)
pdf_option = st.checkbox("Download PDF files", value=True)

if not xml_option and not pdf_option:
    st.warning("⚠️ Please select at least one format (XML or PDF).")

# --- Limit ---
limit = st.number_input("📈 Number of papers to fetch", min_value=1,value=100)

# --- Start button ---
start_button = st.button("🚀 Fetch Papers")

# -------------------------------------------------------
# ⚙️ Directory Preparation
# -------------------------------------------------------
BASE_DIR = os.path.join(os.getcwd(), "data")
os.makedirs(BASE_DIR, exist_ok=True)

# -------------------------------------------------------
# 🚀 When user clicks fetch
# -------------------------------------------------------
if start_button:
    if not query or not corpus_name:
        st.error("❌ Please enter both a query and a corpus name.")
    elif not xml_option and not pdf_option:
        st.error("❌ Please select at least one file format.")
    else:
        # Create a timestamped corpus folder for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        corpus_folder = os.path.join(BASE_DIR, f"{corpus_name}_{timestamp}")
        result_folder = os.path.join(corpus_folder, "pygetpapers_result")
        os.makedirs(result_folder, exist_ok=True)

        # -------------------------------------------------------
        # 🧩 Build PyGetPapers Command
        # -------------------------------------------------------
        command = [
            "pygetpapers1",
            "-q", query,
            "-o", result_folder,
            "-k", str(limit),
            "--api", selected_api
        ]

        # Add selected formats
        if xml_option:
            command.append("-x")
        if pdf_option:
            command.append("-p")

        # Add date filters if provided
        if start_date:
            command.extend(["--startdate", start_date.strftime("%Y-%m-%d")])
        if end_date:
            command.extend(["--enddate", end_date.strftime("%Y-%m-%d")])

        st.write("⚙️ Running command:")
        st.code(" ".join(command), language="bash")

        # -------------------------------------------------------
        # ▶️ Execute Command
        # -------------------------------------------------------
        try:
            process = subprocess.run(command, capture_output=True, text=True)
            if process.returncode == 0:
                st.success("✅ Papers fetched successfully!")
                st.text_area("📜 PyGetPapers Output Log", process.stdout, height=200)

                # Zip results for download
                zip_path = shutil.make_archive(corpus_folder, 'zip', corpus_folder)
                st.success("📦 Results ready for download:")
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download Corpus ZIP",
                        data=f,
                        file_name=f"{corpus_name}.zip",
                        mime="application/zip"
                    )
            else:
                st.error("❌ PyGetPapers failed.")
                st.text_area("Error log", process.stderr, height=200)

        except Exception as e:
            st.error(f"⚠️ Something went wrong: {e}")

# -------------------------------------------------------
# 📘 Info Section
# -------------------------------------------------------
st.markdown("---")
st.markdown("""
### ✅ Key Points from This Output

**Supported APIs:**
- `--api europe_pmc | crossref | arxiv | biorxiv | medrxiv | rxivist | openalex`

**Supported Download Formats:**
- `-x` → download XML  
- `-p` → download PDF  
(Currently restricted to only these two formats.)

**Date Filters:**
- `--startdate YYYY-MM-DD`
- `--enddate YYYY-MM-DD`

**Output Directory:**
- Automatically created under:  
  `data/<corpus_name_timestamp>/pygetpapers_result`

**Limit:**
- Controlled by `--limit` or `-k`.

Each corpus gets its own folder and is zipped for download.
""")



