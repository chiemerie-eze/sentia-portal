from pathlib import Path

import pandas as pd
import streamlit as st


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Reports", layout="wide")

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "sentia_logo.png"

# =========================
# SIDEBAR
# =========================
if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), width=90)

st.sidebar.markdown("## Sentia Portal")
st.sidebar.caption("Secure Your Digital Future")

# =========================
# ACCESS CHECK
# =========================
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Please log in first.")
    st.stop()

top_col1, top_col2 = st.columns([1, 6])

with top_col1:
    st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
    if st.button("← Home"):
        st.switch_page("app.py")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")
# =========================
# STYLING
# =========================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #020617 0%, #06152f 48%, #081b3a 100%);
    color: white;
}

.main .block-container {
    max-width: 1200px;
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617 0%, #06152f 100%);
    border-right: 1px solid rgba(255,255,255,0.08);
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

h1, h2, h3, h4, p, div, span, label {
    color: white;
}

.glass-card {
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 22px;
    padding: 24px;
    box-shadow: 0 10px 32px rgba(0,0,0,0.22);
    backdrop-filter: blur(10px);
    margin-bottom: 20px;
}

.glass-card * {
    color: white !important;
}

[data-testid="metric-container"] {
    background: rgba(15, 23, 42, 0.88) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 18px !important;
    padding: 1rem !important;
    box-shadow: 0 8px 28px rgba(0,0,0,0.18);
}

[data-testid="metric-container"] * {
    color: white !important;
}

div[data-baseweb="notification"] {
    border-radius: 14px !important;
}

.stAlert * {
    font-weight: 600 !important;
}

.stButton > button {
    background: linear-gradient(90deg, #22d3ee, #38bdf8) !important;
    color: #03111f !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.8rem 1.2rem !important;
    font-weight: 700 !important;
    width: 100% !important;
    box-shadow: 0 8px 24px rgba(34, 211, 238, 0.18);
}

.stButton > button:hover {
    background: linear-gradient(90deg, #67e8f9, #60a5fa) !important;
    color: #03111f !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =========================
# MODEL REPORT DATA
# =========================
# You can edit these values later if your evaluation changes.
reports_df = pd.DataFrame([
    {
        "Model": "Random Forest",
        "Accuracy": 1.0000,
        "Precision": 1.0000,
        "Recall": 0.8333,
        "F1 Score": 0.9091,
        "False Positive Rate": 0.0000
    },
    {
        "Model": "Logistic Regression",
        "Accuracy": 0.9930,
        "Precision": 0.0058,
        "Recall": 0.8333,
        "F1 Score": 0.0115,
        "False Positive Rate": 0.0069
    }
])

# =========================
# PAGE HEADER
# =========================
st.markdown("<h1 style='text-align:center;'>Model Performance Reports</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color:#94a3b8;'>A clear summary of model performance and what it means for operational decision-making</p>",
    unsafe_allow_html=True
)

st.write("")

# =========================
# TOP METRICS
# =========================
best_model = reports_df.iloc[0]

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Primary Model", best_model["Model"])
with m2:
    st.metric("Accuracy", f"{best_model['Accuracy']:.4f}")
with m3:
    st.metric("Recall", f"{best_model['Recall']:.4f}")
with m4:
    st.metric("False Positive Rate", f"{best_model['False Positive Rate']:.4f}")

st.write("")

# =========================
# PERFORMANCE COMPARISON
# =========================
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("### Performance Comparison")
st.write(
    "This section compares the evaluated machine learning models using the main classification metrics used in the project."
)
st.dataframe(reports_df, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# =========================
# INTERPRETATION
# =========================
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("### Interpretation")
st.write(
    "The Random Forest model performed better overall than Logistic Regression across the most important evaluation measures. "
    "It achieved stronger precision and a lower false positive rate, which makes it more suitable for intrusion detection tasks "
    "where reliability and alert quality are important."
)
st.write(
    "Although both models achieved the same recall in this test summary, Logistic Regression produced far more false positives "
    "and a much weaker precision score. This means it is more likely to generate unnecessary alerts, which can reduce trust in the system."
)
st.markdown("</div>", unsafe_allow_html=True)

# =========================
# BUSINESS VALUE
# =========================
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("### Why This Matters")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("#### Better Detection Confidence")
    st.write(
        "A stronger-performing model gives users more confidence that results are meaningful and worth reviewing."
    )

with c2:
    st.markdown("#### Fewer Unnecessary Alerts")
    st.write(
        "Lower false positive rates help reduce alert fatigue and improve how teams respond to suspicious activity."
    )

with c3:
    st.markdown("#### Stronger Decision Support")
    st.write(
        "Clear reporting helps users and stakeholders understand which model is more suitable for real use."
    )

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# REPORT SUMMARY
# =========================
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("### Report Summary")
st.write(
    "Based on the available evaluation results, Random Forest is the preferred model for this project. "
    "Its performance profile makes it the stronger option for operational use within the Sentia portal."
)
st.write(
    "This page can later be expanded with confusion matrices, class distribution charts, scan trends, "
    "or client-ready reporting outputs."
)
st.markdown("</div>", unsafe_allow_html=True)

# =========================
# DOWNLOAD REPORT TABLE
# =========================
csv_data = reports_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Report Summary CSV",
    data=csv_data,
    file_name="sentia_model_reports.csv",
    mime="text/csv"
)