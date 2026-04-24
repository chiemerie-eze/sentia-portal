from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from db_utils import save_scan_record

st.set_page_config(page_title="Run Scan", layout="wide")

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "model"
SCAN_HISTORY_DIR = BASE_DIR / "scan_history"
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "sentia_logo.png"

RF_MODEL_PATH = MODEL_DIR / "rf_model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"
LABEL_ENCODER_PATH = MODEL_DIR / "label_encoder.pkl"

SCAN_HISTORY_DIR.mkdir(exist_ok=True)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #020617 0%, #06152f 48%, #081b3a 100%) !important;
    color: #ffffff !important;
}

.main .block-container {
    max-width: 1200px;
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617 0%, #06152f 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.08);
}

section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

h1, h2, h3, h4, h5, h6, p, label, span, div {
    color: #ffffff !important;
}

.glass-card {
    background: rgba(15, 23, 42, 0.78) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 22px !important;
    padding: 24px !important;
    box-shadow: 0 10px 32px rgba(0,0,0,0.22) !important;
    backdrop-filter: blur(10px) !important;
    margin-bottom: 20px !important;
}

.glass-card * {
    color: #ffffff !important;
}

[data-testid="stFileUploader"] {
    background: rgba(15, 23, 42, 0.78) !important;
    border: 1px dashed rgba(255,255,255,0.16) !important;
    border-radius: 18px !important;
    padding: 8px !important;
}

[data-testid="stFileUploader"] * {
    color: #ffffff !important;
}

[data-testid="stFileUploaderFile"] {
    background: rgba(15, 23, 42, 0.65) !important;
    border-radius: 12px !important;
}

[data-testid="stFileUploaderFile"] * {
    color: #ffffff !important;
}

[data-testid="stBaseButton-secondary"] {
    background: rgba(255,255,255,0.08) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
}

.stButton > button {
    background: linear-gradient(90deg, #22d3ee, #38bdf8) !important;
    color: #03111f !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.8rem 1.2rem !important;
    font-weight: 700 !important;
    width: 100% !important;
    box-shadow: 0 8px 24px rgba(34, 211, 238, 0.18) !important;
}

.stButton > button:hover {
    background: linear-gradient(90deg, #67e8f9, #60a5fa) !important;
    color: #03111f !important;
}

[data-testid="stDataFrame"] {
    background: rgba(15, 23, 42, 0.88) !important;
    border-radius: 16px !important;
}

[data-testid="stDataFrame"] * {
    color: #ffffff !important;
}

[data-testid="metric-container"] {
    background: rgba(15, 23, 42, 0.88) !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 18px !important;
    padding: 1rem !important;
    box-shadow: 0 8px 28px rgba(0,0,0,0.18) !important;
}

[data-testid="metric-container"] * {
    color: #ffffff !important;
}

.stSuccess, .stInfo, .stWarning, .stError {
    border-radius: 14px !important;
}

.stSuccess *, .stInfo *, .stWarning *, .stError * {
    font-weight: 600 !important;
}

.stDownloadButton > button {
    background: linear-gradient(90deg, #22d3ee, #38bdf8) !important;
    color: #03111f !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.8rem 1rem !important;
    font-weight: 700 !important;
    width: 100% !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), width=90)

st.sidebar.markdown("## Sentia Portal")
st.sidebar.caption("Secure Your Digital Future")

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

@st.cache_resource
def load_artifacts():
    model = joblib.load(RF_MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    label_encoder = joblib.load(LABEL_ENCODER_PATH)
    return model, scaler, label_encoder


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]

    for label_col in ["Label", "label"]:
        if label_col in df.columns:
            df = df.drop(columns=[label_col])

    df = df.select_dtypes(include=[np.number])
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.fillna(0)
    df = df.clip(lower=-1e12, upper=1e12)
    return df


def align_features(df: pd.DataFrame, fitted_scaler) -> pd.DataFrame:
    if hasattr(fitted_scaler, "feature_names_in_"):
        expected_cols = list(fitted_scaler.feature_names_in_)
        for col in expected_cols:
            if col not in df.columns:
                df[col] = 0
        df = df[expected_cols]
    return df


def decode_predictions(preds, fitted_label_encoder):
    try:
        return fitted_label_encoder.inverse_transform(preds)
    except Exception:
        return preds


def save_result_file(result_df: pd.DataFrame, original_name: str) -> Path:
    safe_name = Path(original_name).stem
    output_path = SCAN_HISTORY_DIR / f"{safe_name}_results.csv"
    result_df.to_csv(output_path, index=False)
    return output_path


try:
    model, scaler, label_encoder = load_artifacts()
except Exception as e:
    st.error(f"Could not load model files: {e}")
    st.stop()

st.markdown("<h1 style='text-align:center;'>Run Security Scan</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color:#94a3b8;'>Upload CSV traffic data and analyse it with the Sentia detection model</p>",
    unsafe_allow_html=True
)

st.write("")

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("### Upload CSV File")
uploaded_file = st.file_uploader(
    "Upload a CSV file for analysis",
    type=["csv"],
    help="Supported format: CSV"
)
st.markdown("</div>", unsafe_allow_html=True)

if uploaded_file is None:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### How this works")
    st.write(
        "Upload a CSV traffic dataset, run the model, and review the results summary. "
        "The scan output will also be saved into your history for later review."
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

try:
    raw_df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Could not read the uploaded CSV file: {e}")
    st.stop()

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown("### Uploaded Data Preview")
st.dataframe(raw_df.head(), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if st.button("Run Detection"):
    try:
        working_df = clean_dataframe(raw_df)

        if working_df.empty:
            st.error("No usable numeric columns were found after cleaning the uploaded file.")
            st.stop()

        working_df = align_features(working_df, scaler)

        scaled_data = scaler.transform(working_df)
        predictions = model.predict(scaled_data)
        decoded_predictions = decode_predictions(predictions, label_encoder)

        result_df = working_df.copy()
        result_df["Prediction"] = decoded_predictions

        prediction_series = result_df["Prediction"].astype(str).str.upper()
        benign_count = int((prediction_series == "BENIGN").sum())
        suspicious_count = int(len(result_df) - benign_count)

        total_records = len(result_df)
        suspicious_ratio = (suspicious_count / total_records * 100) if total_records > 0 else 0

        st.session_state["last_scan_summary"] = {
                "file_name": uploaded_file.name,
                "total_records": total_records,
                "benign_count": benign_count,
                "suspicious_count": suspicious_count,
                "suspicious_ratio": suspicious_ratio
            }

        saved_result_path = save_result_file(result_df, uploaded_file.name)

        save_scan_record(
                original_filename=uploaded_file.name,
                saved_result_path=saved_result_path,
                benign_count=benign_count,
                suspicious_count=suspicious_count
            )

        st.success("Detection completed successfully and saved to scan history.")

        st.markdown("## Current Scan Summary")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### Benign Records")
            st.markdown(f"<h1 style='color:#22c55e;'>{benign_count}</h1>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### Suspicious Records")
            st.markdown(f"<h1 style='color:#ef4444;'>{suspicious_count}</h1>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with c3:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### Uploaded File")
            st.write(uploaded_file.name)
            st.markdown("</div>", unsafe_allow_html=True)

        if suspicious_count == 0:
            st.info("No suspicious activity was detected in this uploaded file.")
        elif suspicious_count < 100:
            st.warning("Low-risk suspicious activity was detected. Review the prediction results below.")
        else:
            st.error("High suspicious activity detected. Immediate review is recommended.")

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### Prediction Results Preview")
        st.dataframe(result_df.head(50), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.download_button(
            label="Download Full Results CSV",
            data=result_df.to_csv(index=False).encode("utf-8"),
            file_name=f"{Path(uploaded_file.name).stem}_results.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Error during prediction: {e}")