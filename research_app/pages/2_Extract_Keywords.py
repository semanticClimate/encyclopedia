import streamlit as st
import os, zipfile, subprocess
from datetime import datetime
from pathlib import Path
import pandas as pd

st.set_page_config(page_title="Extract Keywords (txt2phrases)", layout="wide")

# ----------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------
def make_session_folder(base_dir: Path):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    session = base_dir / f"session_{ts}"
    txt_dir, key_dir = session / "txt_files", session / "keyphrases"
    txt_dir.mkdir(parents=True, exist_ok=True)
    key_dir.mkdir(parents=True, exist_ok=True)
    return session, txt_dir, key_dir

def zip_folder(folder: Path, zip_path: Path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(folder):
            for f in files:
                p = Path(root) / f
                z.write(p, p.relative_to(folder))
    return zip_path

def run_auto(input_dir, output_dir, top_n):
    cmd = [
        "txt2phrases",
        "auto", "-i", str(input_dir), "-o", str(output_dir), "-n", str(top_n)
    ]
    return subprocess.run(cmd, capture_output=True, text=True)

def pdf_to_txt(): 
    from txt2phrases.pdf2txt import convert_pdf_to_txt
    return convert_pdf_to_txt

def html_to_txt(): 
    from txt2phrases.html2txt import html_to_txt_folder
    return html_to_txt_folder

def keyword_extraction():
    from txt2phrases.keyword import KeywordExtraction
    return KeywordExtraction

# ----------------------------------------------------------------
# UI
# ----------------------------------------------------------------
st.title("🧠 Extract Keywords (txt2phrases)")
st.markdown("""
Use this tool to automatically extract keyphrases from:
1. The **output of your Fetch Research Papers app (PyGetPapers)**, or  
2. A manually **uploaded HTML or PDF file**.
""")

mode = st.radio("Select Mode", ["Auto from Fetch Paper Output", "Single File Upload (HTML or PDF)"])

# ===============================================================
# MODE 1 — AUTO FROM FETCH PAPER
# ===============================================================
if mode == "Auto from Fetch Paper Output":
    st.subheader("🚀 Automatic Mode (Fetch Paper Output Detection)")

    top_n = st.number_input("🔢 Number of keyphrases per file:", 10, 5000, 500)

    # 🔍 Automatically detect fetch_paper output
    detected_folder = st.session_state.get("corpus_folder", None)

    if detected_folder and Path(detected_folder).exists():
        st.success(f"✅ Detected fetch_paper output folder")
        corpus_folder = Path(detected_folder)
        folder_name = corpus_folder.name
        st.info(f"📁 Using folder: **{folder_name}**")
    else:
        st.warning("⚠️ No active fetch_paper output detected. You can manually enter a path.")
        manual_path = st.text_input("📁 Enter path to corpus folder:")
        corpus_folder = Path(manual_path.strip('"')) if manual_path else None
        if corpus_folder:
            folder_name = corpus_folder.name
            st.info(f"📁 Selected folder: **{folder_name}**")

    if corpus_folder and corpus_folder.exists():
        if st.button("▶️ Run txt2phrases Auto Pipeline"):
            base = Path("data/txt2phrases_auto")
            base.mkdir(parents=True, exist_ok=True)
            session, _, _ = make_session_folder(base)

            st.info(f"⚙️ Running txt2phrases Auto Pipeline on **{folder_name}**...")
            
            # Progress bar for auto pipeline
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Starting processing...")
            progress_bar.progress(10)
            
            status_text.text("Converting files to text format...")
            progress_bar.progress(30)
            
            status_text.text("Extracting keyphrases...")
            progress_bar.progress(60)
            
            result = run_auto(corpus_folder, session, top_n)
            
            status_text.text("Finalizing results...")
            progress_bar.progress(90)

            # Collect results
            csvs = list(session.rglob("*.csv"))
            if csvs:
                progress_bar.progress(100)
                status_text.text("Processing complete!")
                
                st.success(f"✅ Auto pipeline complete! {len(csvs)} CSVs generated.")
                with open(zip_folder(session, session/"results.zip"), "rb") as f:
                    st.download_button(
                        "⬇️ Download All Extracted Keyphrases (ZIP)",
                        f, "txt2phrases_auto_results.zip", "application/zip"
                    )
            else:
                st.warning("⚠️ No CSVs found — check if corpus contains valid HTML/TXT files.")
    else:
        st.info("ℹ️ Please run the Fetch Research Papers app first, or provide a valid folder path.")

# ===============================================================
# MODE 2 — SINGLE FILE UPLOAD
# ===============================================================
else:
    st.subheader("📤 Upload Single HTML or PDF File")
    upl = st.file_uploader("Upload file", type=["html", "pdf"])
    top_n = st.number_input("🔢 Number of keyphrases to extract:", 10, 2000, 200)

    if upl:
        base = Path("data/txt2phrases_uploads")
        session, txt_out, key_out = make_session_folder(base)
        uploaded = session / upl.name
        uploaded.write_bytes(upl.read())
        st.success(f"📄 Uploaded → **{upl.name}**")

        if st.button("⚙️ Convert & Extract Keywords"):
            txt_path = None
            
            # Progress bar for single file processing
            progress_bar = st.progress(0)
            status_text = st.empty()

            if uploaded.suffix.lower() == ".html":
                status_text.text("Converting HTML to text...")
                progress_bar.progress(30)
                
                html_to_txt()(str(session), str(txt_out))
                txt_path = next(txt_out.glob("*.txt"), None)
                
                progress_bar.progress(60)
                
            elif uploaded.suffix.lower() == ".pdf":
                status_text.text("Converting PDF to text...")
                progress_bar.progress(30)
                
                pdf_to_txt()(str(uploaded), str(txt_out))
                txt_path = next(txt_out.glob("*.txt"), None)
                
                progress_bar.progress(60)

            if txt_path:
                status_text.text(f"Extracting top {top_n} keyphrases...")
                progress_bar.progress(80)
                
                ke = keyword_extraction()
                extractor = ke(
                    textfile=str(txt_path),
                    saving_path=str(key_out),
                    output_filename=f"{txt_path.stem}_keywords.csv",
                    top_n=int(top_n)
                )
                extractor.extract_keywords()

                progress_bar.progress(95)
                status_text.text("Finalizing...")

                csv_path = key_out / f"{txt_path.stem}_keywords.csv"
                if csv_path.exists():
                    df = pd.read_csv(csv_path)
                    progress_bar.progress(100)
                    status_text.text("Complete!")
                    
                    st.success("✅ Extraction Complete!")
                    st.dataframe(df.head(20))
                    with open(csv_path, "rb") as f:
                        st.download_button(
                            "⬇️ Download CSV", 
                            f, 
                            csv_path.name, 
                            "text/csv"
                        )
                else:
                    st.warning("⚠️ No CSV generated.")


