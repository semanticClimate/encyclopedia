import streamlit as st
import subprocess
import os
import shutil
import pandas as pd
from datetime import datetime
from streamlit import components

# -------------------------------------------------------
# 🔧 Page Configuration
# -------------------------------------------------------
st.set_page_config(page_title="Fetch Research Papers", layout="wide")

st.title("📄 Fetch Research Papers using PyGetPapers1")
st.markdown("""
Fetch research papers from public repositories using **PyGetPapers1**,  
then instantly generate and preview interactive **DataTables** with **AMILib**.
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

st.markdown("### 🗓️ Optional Date Filters")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("📅 Start Date (optional)", value=None)
with col2:
    end_date = st.date_input("📅 End Date (optional)", value=None)

st.markdown("### 📦 Select formats to download")
xml_option = st.checkbox("Download XML files", value=True)
pdf_option = st.checkbox("Download PDF files", value=True)

limit = st.number_input("📈 Number of papers to fetch", min_value=1, max_value=1000, value=100)

start_button = st.button("🚀 Fetch Papers")

# -------------------------------------------------------
# ⚙️ Directory Setup
# -------------------------------------------------------
BASE_DIR = os.path.join(os.getcwd(), "data", "corpora")
os.makedirs(BASE_DIR, exist_ok=True)

# -------------------------------------------------------
# 🚀 Fetch Papers Section
# -------------------------------------------------------
if start_button:
    if not query or not corpus_name:
        st.error("❌ Please enter both a query and a corpus name.")
    elif not xml_option and not pdf_option:
        st.error("❌ Please select at least one file format.")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        corpus_folder = os.path.join(BASE_DIR, f"{corpus_name}_{timestamp}")
        os.makedirs(corpus_folder, exist_ok=True)

        # -------------------------------------------------------
        # 🧩 Build Command (no nested folder, use --save_query + --makehtml)
        # -------------------------------------------------------
        command = [
            "pygetpapers1",
            "-q", query,
            "-o", corpus_folder,
            "-k", str(limit),
            "--api", selected_api,
            "--save_query",
            "--makehtml",
        ]

        if xml_option:
            command.append("-x")
        if pdf_option:
            command.append("-p")

        if start_date:
            command.extend(["--startdate", start_date.strftime("%Y-%m-%d")])
        if end_date:
            command.extend(["--enddate", end_date.strftime("%Y-%m-%d")])

        st.code(" ".join(command), language="bash")
        st.info("⚙️ Fetching papers... this may take a few minutes.")

        # -------------------------------------------------------
        # ▶️ Run Command
        # -------------------------------------------------------
        try:
            process = subprocess.run(command, capture_output=True, text=True)
            if process.returncode == 0:
                st.success("✅ Papers fetched successfully!")
                st.text_area("📜 PyGetPapers Output Log", process.stdout, height=200)
                st.session_state["corpus_folder"] = corpus_folder

                # Display summary HTML if available
                html_summary = os.path.join(corpus_folder, "results.html")
                if os.path.exists(html_summary):
                    st.markdown("### 🌐 Quick Preview: Results Summary")
                    with open(html_summary, "r", encoding="utf-8") as f:
                        components.v1.html(f.read(), height=500, scrolling=True)

                # ZIP results for download
                zip_path = shutil.make_archive(corpus_folder, 'zip', corpus_folder)
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
# 📊 DataTable (AMILib)
# -------------------------------------------------------
st.markdown("---")
st.header("📊 Generate and View DataTable (AMILib)")

if "corpus_folder" not in st.session_state:
    st.info("ℹ️ Please fetch papers first to generate the DataTable.")
else:
    output_dir = st.session_state["corpus_folder"]

    if st.button("🧮 Create DataTable from Corpus"):
        st.info("🔍 Running AMILib HTML → DATATABLES command...")

        amilib_cmd = [
            "amilib", "HTML",
            "--operation", "DATATABLES",
            "--indir", output_dir
        ]

        with st.spinner("⚙️ Generating DataTables using AMILib..."):
            process = subprocess.run(amilib_cmd, capture_output=True, text=True)

        if process.returncode == 0:
            st.success("✅ DataTables generated successfully!")

            tables_dir = os.path.join(output_dir, "tables")
            html_file_path = os.path.join(output_dir, "datatables.html")

            # Show CSV tables (if any)
            if os.path.exists(tables_dir):
                csv_files = [f for f in os.listdir(tables_dir) if f.endswith(".csv")]
                for csv_file in csv_files:
                    file_path = os.path.join(tables_dir, csv_file)
                    st.markdown(f"### 📘 Preview: `{csv_file}`")
                    try:
                        df = pd.read_csv(file_path)
                        st.dataframe(df, use_container_width=True, height=500)
                    except Exception as e:
                        st.warning(f"⚠️ Could not load {csv_file}: {e}")
            else:
                st.warning("⚠️ No CSV tables found in the tables folder.")

            # Show HTML DataTable directly on screen
            if os.path.exists(html_file_path):
                st.markdown("### 🌐 Interactive HTML DataTable")
                custom_css = """
                    <style>
                    body, table.dataTable, .dataTables_wrapper {
                        background-color: white !important;
                        color: black !important;
                        font-family: 'Segoe UI', sans-serif !important;
                    }
                    table.dataTable th, table.dataTable td {
                        border: 1px solid #ddd !important;
                        padding: 8px !important;
                    }
                    table.dataTable thead th {
                        background-color: #f4f4f4 !important;
                        color: #000 !important;
                        font-weight: bold !important;
                    }
                    .dataTables_wrapper .dataTables_filter input,
                    .dataTables_wrapper .dataTables_length select {
                        color: black !important;
                        background-color: white !important;
                        border: 1px solid #aaa !important;
                    }
                    </style>
                """

                with open(html_file_path, "r", encoding="utf-8") as f:
                    html_content = f.read()

                # Inject the custom style before rendering
                styled_html = custom_css + html_content

                # Render inside Streamlit
                components.v1.html(styled_html, height=650, scrolling=True)

                with open(html_file_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download DataTable (HTML)",
                        data=f,
                        file_name="DataTable.html",
                        mime="text/html"
                    )
        else:
            st.error("❌ AMILib DataTable creation failed.")
            st.text_area("Error Log", process.stderr, height=200)


