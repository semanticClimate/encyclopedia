import streamlit as st

# --- Page config ---
st.set_page_config(
    page_title="Research Toolkit",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Main Page ---
st.title("🧠 Research Toolkit")

st.markdown("""
Welcome to the **Research Toolkit** — a simple, modular platform for your research workflows.

### 🚀 What you can do
1. **Fetch Papers** from public repositories.  
2. **Extract Keywords** from research text or HTML.  
3. **Build an Encyclopedia** (XML dictionaries for research terms).  
4. **Contact Us** for help or feedback.

👉 Use the **sidebar** on the left to navigate between modules.
""")

st.image("https://static.streamlit.io/examples/dice.jpg", width=300)
st.markdown("---")







