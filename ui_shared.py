from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
HERO_PATH = ASSETS_DIR / "sentia-hero.png"   


def apply_shared_styles():
    st.markdown("""
    <style>
    :root {
        --bg-1: #020617;
        --bg-2: #06152f;
        --bg-3: #081b3a;
        --card: rgba(15, 23, 42, 0.74);
        --card-strong: rgba(15, 23, 42, 0.86);
        --border: rgba(255,255,255,0.08);
        --text-main: #ffffff;
        --text-soft: #cbd5e1;
        --text-muted: #94a3b8;
        --accent-1: #22d3ee;
        --accent-2: #38bdf8;
        --accent-dark: #03111f;
    }

    .stApp {
        background: linear-gradient(180deg, var(--bg-1) 0%, var(--bg-2) 48%, var(--bg-3) 100%);
        color: var(--text-main);
    }

    .main .block-container {
        max-width: 1180px;
        padding-top: 1.4rem;
        padding-bottom: 2.2rem;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617 0%, #06152f 100%);
        border-right: 1px solid var(--border);
    }

    section[data-testid="stSidebar"] * {
        color: var(--text-main) !important;
    }

    .page-title {
        text-align: center;
        font-size: 3rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-bottom: 0.35rem;
    }

    .page-subtitle {
        text-align: center;
        color: var(--text-muted) !important;
        margin-top: 0;
        margin-bottom: 1.2rem;
        font-size: 1.02rem;
    }

    .hero-wrap {
        margin-bottom: 26px;
    }

    .brand-title {
        font-size: 1.05rem;
        font-weight: 800;
        letter-spacing: 0.01em;
        margin-bottom: 0.1rem;
    }

    .brand-subtitle {
        color: var(--text-muted) !important;
        font-size: 0.92rem;
    }

    .glass-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 28px;
        box-shadow: 0 12px 34px rgba(0,0,0,0.22);
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
    }

    .section-title {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 0.35rem;
    }

    .section-subtitle {
        color: var(--text-muted) !important;
        margin-top: 0;
        margin-bottom: 1rem;
    }

    .soft-divider {
        height: 1px;
        background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.10), rgba(255,255,255,0.02));
        border-radius: 999px;
        margin: 12px 0 18px 0;
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

    .stButton > button {
        background: linear-gradient(90deg, var(--accent-1), var(--accent-2)) !important;
        color: var(--accent-dark) !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 0.85rem 1rem !important;
        font-weight: 800 !important;
        width: 100%;
        box-shadow: 0 8px 24px rgba(34, 211, 238, 0.18);
    }

    .stButton > button:hover {
        background: linear-gradient(90deg, #67e8f9, #60a5fa) !important;
        color: var(--accent-dark) !important;
    }
.secondary-btn button {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    color: white !important;
    border-radius: 10px !important;
    padding: 0.4rem 1rem !important;
    font-size: 0.85rem !important;
}

.secondary-btn button:hover {
    border: 1px solid #2fd4ff !important;
    color: #2fd4ff !important;
}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


def render_hero():
    if HERO_PATH.exists():
        st.markdown('<div class="hero-wrap">', unsafe_allow_html=True)
        st.image(str(HERO_PATH), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)