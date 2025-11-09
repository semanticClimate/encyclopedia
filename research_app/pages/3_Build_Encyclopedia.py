import streamlit as st
import pandas as pd
import subprocess
import tempfile
import os
from datetime import datetime
import time

# ---------------------------------------------
# 📘 STREAMLIT PAGE: Build Encyclopedia (Phase 3)
# ---------------------------------------------
st.set_page_config(page_title="📘 Build Encyclopedia", layout="wide")
st.title("📘Build Encyclopedia from Keywords")
st.markdown("This phase creates an encyclopedia from extracted keywords using **amilib DICT**.")

# Step 1: Upload CSV
uploaded_csv = st.file_uploader("📤 Upload your CSV file (keywords in first column)", type=["csv"])

# Step 2: User inputs
ency_name = st.text_input("📝 Enter Encyclopedia Name", "My_Encyclopedia")
description_sources = st.multiselect(
    "🌐 Select Description Sources",
    ["wikipedia", "wiktionary", "wikidata"],
    default=["wikipedia"]
)
generate_button = st.button("🚀 Generate Encyclopedia")

# Step 3: When button is clicked
if generate_button:
    if uploaded_csv is None:
        st.error("⚠️ Please upload a CSV file first.")
    else:
        with st.spinner("Processing your encyclopedia... this may take a few minutes ⏳"):

            # Create directories
            os.makedirs("data/encyclopedias", exist_ok=True)

            # Load CSV and extract keywords
            df = pd.read_csv(uploaded_csv)
            keywords = df.iloc[:, 0].dropna().astype(str).tolist()

            # Save keywords to a temporary text file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp_file:
                tmp_file.write("\n".join(keywords))
                words_path = tmp_file.name

            # Define encyclopedia output path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ency_folder = "data/encyclopedias"
            html_output = os.path.join(ency_folder, f"{ency_name}_{timestamp}.html")

            # Build command for amilib DICT
            cmd = [
                "amilib", "DICT",
                "--operation", "create",
                "--words", words_path,
                "--dict", html_output,
                "--description", *description_sources,
                "--figures", "wikipedia",
                "--title", ency_name
            ]

            # Progress bar setup
            progress = st.progress(0)
            progress_text = st.empty()
            progress_text.text("Starting encyclopedia creation...")

            # Run amilib command
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            total_steps = 10
            step = 0

            for line in process.stdout:
                step = min(step + 1, total_steps)
                progress.progress(step / total_steps)
                progress_text.text(line.strip())
                time.sleep(0.3)

            process.wait()
            progress.progress(1.0)
            progress_text.text("✅ Encyclopedia creation completed!")

            # Clean up extra files (keep only final HTML)
            for file in os.listdir(ency_folder):
                if not file.endswith(".html"):
                    os.remove(os.path.join(ency_folder, file))

            # Download button for final HTML
            with open(html_output, "rb") as f:
                st.download_button(
                    label="📥 Download Encyclopedia (HTML)",
                    data=f,
                    file_name=os.path.basename(html_output),
                    mime="text/html"
                )

            st.success(f"✅ Encyclopedia '{ency_name}' created successfully!")