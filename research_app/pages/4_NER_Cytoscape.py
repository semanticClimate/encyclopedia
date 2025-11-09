import streamlit as st
import subprocess
import os
import pandas as pd
import re
import networkx as nx
import streamlit_cytoscapejs as cytoscapejs

# -------------------------------------------------------
# 🔧 Page Configuration
# -------------------------------------------------------
st.set_page_config(page_title="NER & Knowledge Graph", layout="wide")

st.title("🧠 Named Entity Recognition (NER) & Knowledge Graph")

st.markdown("""
This module allows you to:
1. Run **NER** on research corpora (extract entities using predefined dictionaries).
2. Build an **interactive Cytoscape network** from extracted entities.

You can either:
- 🧩 Fetch a corpus using **PyGetPapers**, or  
- 📁 Directly upload / specify a corpus folder to analyze.
""")

# -------------------------------------------------------
# 📂 Select Corpus Folder
# -------------------------------------------------------
st.markdown("### 📁 Select or Provide Corpus Folder")

corpus_folder = st.text_input("Enter path to your corpus folder (e.g., `data/corpora/AI_Healthcare_20251109_113000`)")
use_existing = st.checkbox("Use the most recently fetched corpus (if available)")

if use_existing and "corpus_folder" in st.session_state:
    corpus_folder = st.session_state["corpus_folder"]
    st.info(f"Using corpus from session: `{corpus_folder}`")

if not corpus_folder or not os.path.exists(corpus_folder):
    st.warning("⚠️ Please provide a valid corpus folder path or fetch papers first.")
    st.stop()

# -------------------------------------------------------
# 🧠 NER (DocAnalysis)
# -------------------------------------------------------
st.markdown("### 🧩 Run Named Entity Recognition (NER)")

available_dictionaries = [
    "EO_ACTIVITY", "EO_COMPOUND", "EO_EXTRACTION", "EO_PLANT",
    "EO_PLANT_PART", "PLANT_GENUS", "EO_TARGET", "COUNTRY",
    "DISEASE", "DRUG", "ORGANIZATION"
]

selected_dictionaries = st.multiselect(
    "📚 Select Dictionaries to Process",
    options=available_dictionaries,
    default=["EO_PLANT", "EO_COMPOUND"]
)

search_sections = st.multiselect(
    "📄 Sections to Search",
    ["ALL", "ACK", "AFF", "AUT", "CON", "DIS", "ETH", "FIG", "INT", "KEY", "MET", "RES", "TAB", "TIL"],
    default=["ALL"]
)

def run_docanalysis_for_dict(output_dir, dictionary, args_list):
    """
    Runs DocAnalysis using Python 3.8 (if available).
    Keeps the rest of the Streamlit app on Python 3.12.
    """
    
    cmd = [
        "py", "-3.10", "-m", "docanalysis.docanalysis",
        "--project_name", output_dir,
        "--make_section",
        "--dictionary", dictionary,
        "--output", os.path.join(output_dir, f"entities_{dictionary}.csv"),
        "--make_json", os.path.join(output_dir, f"entities_{dictionary}.json")
    ] + args_list


    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


if st.button("🔍 Run NER for Selected Dictionaries"):
    if not selected_dictionaries:
        st.warning("Please select at least one dictionary.")
    else:
        args_list = []
        if search_sections:
            args_list += ["--search_section"] + search_sections

        generated_files = []
        for dictionary in selected_dictionaries:
            st.info(f"🔎 Processing dictionary: `{dictionary}`...")
            result = run_docanalysis_for_dict(corpus_folder, dictionary, args_list)

            st.code(result.stdout, language='text')
            if result.stderr:
                st.code(result.stderr, language='text')

            if result.returncode != 0:
                st.error(f"❌ NER failed for `{dictionary}`.")
                continue
            else:
                st.success(f"✅ NER completed for `{dictionary}`.")

            csv_path = os.path.join(corpus_folder, f"entities_{dictionary}.csv")
            if os.path.exists(csv_path):
                generated_files.append(csv_path)
                try:
                    df = pd.read_csv(csv_path)
                    st.markdown(f"### 📄 Preview for `{dictionary}`")
                    st.dataframe(df.head(50))
                    with open(csv_path, "rb") as f:
                        st.download_button(
                            f"⬇️ Download CSV ({dictionary})",
                            f,
                            file_name=f"entities_{dictionary}.csv"
                        )
                except Exception as e:
                    st.warning(f"⚠️ Error loading {dictionary}: {e}")

        if generated_files:
            st.session_state['ner_outputs'] = generated_files
            st.success("✅ NER outputs saved for Cytoscape visualization!")

# -------------------------------------------------------
# 🌐 Cytoscape Knowledge Graph
# -------------------------------------------------------
st.markdown("---")
st.header("🌐 Knowledge Graph Visualization")

if "ner_outputs" not in st.session_state:
    st.warning("⚠️ Please run NER first to generate entity CSVs.")
else:
    ner_files = st.session_state["ner_outputs"]

    st.subheader("📁 Available NER CSVs")
    st.write(ner_files)

    selected_csvs = st.multiselect(
        "Select CSVs for Network Creation",
        ner_files,
        default=ner_files
    )

    layout_choice = st.selectbox(
        "🧩 Choose Layout for Visualization",
        ["cose", "circle", "grid", "breadthfirst", "concentric"],
        index=0
    )

    if st.button("🔗 Build Knowledge Graph"):
        all_edges = []

        for csv_file in selected_csvs:
            try:
                df = pd.read_csv(csv_file)

                if "file_path" not in df.columns or "0" not in df.columns:
                    st.warning(f"⚠️ Skipped {csv_file} (missing required columns).")
                    continue

                for _, row in df.iterrows():
                    file_path = str(row["file_path"])
                    match = re.search(r"(PMC\d+)", file_path)
                    source = match.group(1) if match else os.path.basename(file_path)

                    targets = str(row["0"]).split(",")
                    weight = int(row["weight_0"]) if "weight_0" in df.columns else 1

                    for target in targets:
                        t = target.strip()
                        if t:
                            all_edges.append((source, t, weight))
            except Exception as e:
                st.error(f"Error reading {csv_file}: {e}")

        if not all_edges:
            st.error("❌ No edges created — check your CSVs.")
        else:
            G = nx.Graph()
            for s, t, w in all_edges:
                G.add_edge(s, t, weight=w)

            nodes = []
            for n in G.nodes():
                node_type = "File" if n.startswith("PMC") else "Entity"
                color = "#1f77b4" if node_type == "File" else "#2ca02c"
                nodes.append({"data": {"id": n, "label": n, "type": node_type, "color": color}})

            edges_cyto = [
                {"data": {"source": s, "target": t, "weight": d["weight"]}}
                for s, t, d in G.edges(data=True)
            ]

            stylesheet = [
                {"selector": "node", "style": {"label": "data(label)", "background-color": "data(color)", "font-size": "10px"}},
                {"selector": "edge", "style": {"width": 2, "line-color": "#ccc"}},
            ]

            st.session_state["network_elements"] = nodes + edges_cyto
            st.session_state["network_stylesheet"] = stylesheet
            st.session_state["network_layout"] = {"name": layout_choice}

            st.success(f"✅ Graph created with {len(G.nodes())} nodes and {len(G.edges())} edges!")

    # Display Cytoscape network
    if "network_elements" in st.session_state:
        st.markdown("### 🌿 Interactive Knowledge Graph")

        cytoscapejs.st_cytoscapejs(
            elements=st.session_state["network_elements"],
            stylesheet=st.session_state["network_stylesheet"],
            layout=st.session_state["network_layout"],
            height="700px",
            key="network_view"
        )