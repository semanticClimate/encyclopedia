import streamlit as st
import os
import zipfile
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="Extract Keywords (txt2phrases)", layout="wide")

# ----------------------------
# Utility Functions
# ----------------------------

def make_session_folder(base_dir):
    """Create a unique session folder inside data/txt2phrases."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = base_dir / f"session_{timestamp}"
    txt_dir = session_dir / "txt_files"
    key_dir = session_dir / "keyphrases"
    txt_dir.mkdir(parents=True, exist_ok=True)
    key_dir.mkdir(parents=True, exist_ok=True)
    return session_dir, txt_dir, key_dir


def load_html_to_txt():
    """Lazy import html_to_txt_folder when needed."""
    try:
        from txt2phrases.html2txt import html_to_txt_folder
        return html_to_txt_folder
    except Exception as e:
        st.error(f"❌ Failed to import html2txt: {e}")
        return None


def load_keyword_extraction():
    """Lazy import KeywordExtraction only when needed."""
    try:
        from txt2phrases.keyword import KeywordExtraction
        return KeywordExtraction
    except Exception as e:
        st.error(f"❌ Failed to import keyword extractor: {e}")
        return None


def zip_folder(folder_path, zip_path):
    """Zip all files in a folder."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for f in files:
                full_path = os.path.join(root, f)
                arcname = os.path.relpath(full_path, folder_path)
                zipf.write(full_path, arcname)
    return zip_path


# ----------------------------
# Streamlit UI
# ----------------------------

st.title("🧠 Extract Keywords (txt2phrases)")
st.markdown("""
This tool performs two automatic steps:
1. **Convert all HTML files → TXT**  
2. **Extract key phrases from each TXT file**  

Each run creates a **unique workspace**, so your data never overlaps with previous sessions.
""")

html_folder = st.text_input("📂 Enter path to folder containing HTML files:")

if html_folder:
    html_folder = Path(html_folder.strip('"').strip("'"))
    if not html_folder.exists():
        st.error("❌ Folder not found. Please check the path.")
    else:
        base_output = Path("data/txt2phrases")
        base_output.mkdir(parents=True, exist_ok=True)

        # ✅ Create or reuse the same session folder
        if "session_dir" not in st.session_state or st.session_state.get("last_html_folder") != str(html_folder):
            session_dir, txt_out, key_out = make_session_folder(base_output)
            st.session_state.session_dir = session_dir
            st.session_state.txt_out = txt_out
            st.session_state.key_out = key_out
            st.session_state.last_html_folder = str(html_folder)
        else:
            session_dir = st.session_state.session_dir
            txt_out = st.session_state.txt_out
            key_out = st.session_state.key_out

        st.info(f"📁 Working directory: `{session_dir}`")

        # ------------------------
        # User input for top_n keywords
        # ------------------------
        top_n = st.number_input(
            "🔢 Enter number of keyphrases to extract per TXT file:",
            min_value=10, max_value=5000, value=1000, step=10,
            help="Select how many top keyphrases you want to extract from each text file."
        )

        # Buttons
        col1, col2 = st.columns(2)
        with col1:
            run_convert = st.button("🔄 Convert HTML → TXT")
        with col2:
            run_extract = st.button("✨ Extract Keywords")

        # ------------------------
        # Step 1: Convert HTML → TXT
        # ------------------------
        if run_convert:
            html_to_txt_folder = load_html_to_txt()
            if html_to_txt_folder:
                with st.spinner("Converting HTML files to TXT..."):
                    html_to_txt_folder(str(html_folder), str(txt_out))
                st.success(f"✅ Conversion complete! TXT files saved in `{txt_out}`")

                zip_path = session_dir / "txt_files.zip"
                zip_folder(txt_out, zip_path)
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download Converted TXT Files (ZIP)",
                        data=f,
                        file_name=f"{session_dir.name}_txt_files.zip",
                        mime="application/zip"
                    )

        # ------------------------
        # Step 2: Extract Keywords
        # ------------------------
        if run_extract:
            KeywordExtraction = load_keyword_extraction()
            if KeywordExtraction:
                txt_files = list(txt_out.glob("*.txt"))
                if not txt_files:
                    st.warning("⚠️ No TXT files found. Please run the conversion step first.")
                else:
                    with st.spinner(f"Extracting top {top_n} key phrases from all TXT files..."):
                        for txt_file in txt_files:
                            extractor = KeywordExtraction(
                                textfile=str(txt_file),
                                saving_path=str(key_out),
                                output_filename=f"{txt_file.stem}_keywords.csv",
                                top_n=int(top_n)
                            )
                            extractor.extract_keywords()

                    st.success(f"✅ Keyword extraction complete for all files! Results saved in `{key_out}`")

                    zip_path = session_dir / "keyphrases.zip"
                    zip_folder(key_out, zip_path)
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download Extracted Keywords (CSV ZIP)",
                            data=f,
                            file_name=f"{session_dir.name}_keywords.zip",
                            mime="application/zip"
                        )


