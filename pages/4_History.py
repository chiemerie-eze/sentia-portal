from pathlib import Path
import pandas as pd
import streamlit as st

from db_utils import get_scan_history

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Scan History", layout="wide")

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
    margin-bottom: 20px;
    backdrop-filter: blur(10px);
    box-shadow: 0 10px 32px rgba(0,0,0,0.22);
}

.glass-card * {
    color: white !important;
}

[data-testid="metric-container"] {
    background: rgba(15, 23, 42, 0.88) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 18px !important;
    padding: 1rem !important;
}

[data-testid="metric-container"] * {
    color: white !important;
}

div[data-baseweb="select"] > div {
    background: rgba(15, 23, 42, 0.82) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
}

.stDownloadButton > button {
    background: linear-gradient(90deg, #22d3ee, #38bdf8) !important;
    color: #03111f !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.7rem 1rem !important;
    font-weight: 700 !important;
    width: 100% !important;
}

.stDownloadButton > button:hover {
    background: linear-gradient(90deg, #67e8f9, #60a5fa) !important;
    color: #03111f !important;
}

.status-pill {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 0.88rem;
    font-weight: 700;
    margin-top: 6px;
}

.status-clean {
    background: rgba(34,197,94,0.18);
    color: #86efac !important;
    border: 1px solid rgba(34,197,94,0.28);
}

.status-low {
    background: rgba(250,204,21,0.16);
    color: #fde68a !important;
    border: 1px solid rgba(250,204,21,0.24);
}

.status-high {
    background: rgba(239,68,68,0.16);
    color: #fca5a5 !important;
    border: 1px solid rgba(239,68,68,0.24);
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("<h1 style='text-align:center;'>Scan History</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color:#94a3b8;'>Review previous scans, understand past results, and download saved outputs when needed</p>",
    unsafe_allow_html=True
)

st.write("")

# =========================
# LOAD DATA
# =========================
rows = get_scan_history()

if not rows:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### No Scan History Yet")
    st.write(
        "Once you upload and analyse files using the scan tool, your results will appear here. "
        "This helps you track activity over time and review past analysis when needed."
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# =========================
# CREATE DATAFRAME
# =========================
df = pd.DataFrame(
    rows,
    columns=[
        "ID",
        "Scan Time",
        "Filename",
        "Result Path",
        "Benign",
        "Suspicious"
    ]
)

def classify_status(value):
    if value == 0:
        return "Clean"
    if value < 100:
        return "Low Risk"
    return "High Risk"

df["Status"] = df["Suspicious"].apply(classify_status)

# =========================
# SUMMARY METRICS
# =========================
total_scans = len(df)
total_benign = int(df["Benign"].sum())
total_suspicious = int(df["Suspicious"].sum())

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Total Scans", total_scans)
with m2:
    st.metric("Total Benign Records", total_benign)
with m3:
    st.metric("Total Suspicious Records", total_suspicious)

st.write("")

# =========================
# HISTORY TABLE
# =========================
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("### Scan Records")
st.write(
    "This table shows your previous scan activity and a simple status label to help you review results more quickly."
)

st.dataframe(
    df[["Scan Time", "Filename", "Benign", "Suspicious", "Status"]],
    use_container_width=True
)
st.markdown("</div>", unsafe_allow_html=True)

# =========================
# FILTER + DOWNLOAD SECTION
# =========================
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("### Review and Download Past Results")

status_filter = st.selectbox(
    "Filter by status",
    options=["All", "Clean", "Low Risk", "High Risk"],
    index=0
)

if status_filter == "All":
    filtered_df = df.copy()
else:
    filtered_df = df[df["Status"] == status_filter].copy()

st.write(f"Showing {len(filtered_df)} saved scan record(s).")

if filtered_df.empty:
    st.info("No scan records match the selected filter.")
else:
    for row_index, row in filtered_df.iterrows():
        result_path = Path(row["Result Path"])

        if row["Status"] == "Clean":
            status_html = '<span class="status-pill status-clean">Clean</span>'
        elif row["Status"] == "Low Risk":
            status_html = '<span class="status-pill status-low">Low Risk</span>'
        else:
            status_html = '<span class="status-pill status-high">High Risk</span>'

        with st.expander(f"{row['Filename']}  |  {row['Scan Time']}"):
            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown("**Benign Records**")
                st.write(int(row["Benign"]))

            with c2:
                st.markdown("**Suspicious Records**")
                st.write(int(row["Suspicious"]))

            with c3:
                st.markdown("**Status**", unsafe_allow_html=True)
                st.markdown(status_html, unsafe_allow_html=True)

            st.write("")
            st.markdown("**Saved Result File**")
            st.code(str(result_path), language=None)

            if result_path.exists():
                with open(result_path, "rb") as f:
                    st.download_button(
                        label="Download Result CSV",
                        data=f.read(),
                        file_name=result_path.name,
                        mime="text/csv",
                        key=f"download_result_{row['ID']}_{row_index}"
                    )
            else:
                st.warning("Saved result file could not be found on disk.")

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# EDUCATIONAL NOTE
# =========================
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("### Understanding Your Scan History")
st.write(
    "Your scan history gives you a record of how uploaded data has been analysed over time. "
    "Reviewing this regularly can help you stay organised, identify repeated patterns, and build better awareness of your digital environment."
)
st.write(
    "Even when results appear clean, consistent review is still valuable. Good oversight supports stronger continuity, "
    "better decision-making, and a more reliable business presence."
)
st.markdown("</div>", unsafe_allow_html=True)