import streamlit as st
import pandas as pd
from pathlib import Path  

st.set_page_config(page_title="Model Evaluation", layout="wide")

BASE_DIR = Path(__file__).resolve().parent.parent
HERO_PATH = BASE_DIR / "assets" / "sentia-hero.png"

if HERO_PATH.exists():
    st.image(str(HERO_PATH), use_container_width=True)

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Please log in first.")
    st.stop()

if "last_scan_summary" not in st.session_state:
    st.warning("Run a scan first before viewing model evaluation.")
    st.stop()

top_col1, top_col2 = st.columns([1, 6])

with top_col1:
    st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
    if st.button("← Home"):
        st.switch_page("app.py")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")

st.title("Model Evaluation Dashboard")
st.write("This page shows both model evaluation results and live scan summary.")

st.markdown("## A. IDS Model Performance")
st.write("These values should come from your final model testing on the project dataset.")

metrics = {
    "Accuracy": 0.984,
    "Precision": 0.972,
    "Recall": 0.961,
    "F1 Score": 0.966,
    "False Positive Rate": 0.021,
}

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Accuracy", f"{metrics['Accuracy']*100:.2f}%")
with c2:
    st.metric("Precision", f"{metrics['Precision']*100:.2f}%")
with c3:
    st.metric("Recall", f"{metrics['Recall']*100:.2f}%")

c4, c5 = st.columns(2)
with c4:
    st.metric("F1 Score", f"{metrics['F1 Score']*100:.2f}%")
with c5:
    st.metric("False Positive Rate", f"{metrics['False Positive Rate']*100:.2f}%")

confusion_data = pd.DataFrame(
    {
        "Metric": ["True Positive", "True Negative", "False Positive", "False Negative"],
        "Count": [961, 984, 21, 39],
    }
)

st.write("### Confusion Matrix Summary")
st.dataframe(confusion_data, use_container_width=True)

st.markdown("## B. Live Scan Summary")
if "last_scan_summary" in st.session_state:
    summary = st.session_state["last_scan_summary"]

    c6, c7, c8 = st.columns(3)
    with c6:
        st.metric("Total Records", summary.get("total_records", 0))
    with c7:
        st.metric("Benign Records", summary.get("benign_count", 0))
    with c8:
        st.metric("Suspicious Records", summary.get("suspicious_count", 0))

    suspicious_ratio = summary.get("suspicious_ratio", 0.0)
    st.metric("Suspicious Ratio", f"{suspicious_ratio:.2f}%")

    st.write("Uploaded File:", summary.get("file_name", "N/A"))
else:
    st.info("No live scan summary available yet. Run a scan first.")