import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "history.db"
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "sentia_logo.png"

ADMIN_EMAIL = "info@sentiatechnologieslimited.com"

st.set_page_config(page_title="Admin Dashboard", layout="wide")

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

h1, h2, h3, h4 {
    color: white !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617 0%, #06152f 100%);
    border-right: 1px solid rgba(255,255,255,0.08);
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

[data-testid="metric-container"] {
    background: rgba(15, 23, 42, 0.78) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 16px !important;
    padding: 1rem !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), width=90)

st.sidebar.markdown("## Sentia Admin")
st.sidebar.caption("Security Oversight Panel")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Please log in first.")
    st.stop()

if "user_email" not in st.session_state:
    st.error("No user session found.")
    st.stop()

if st.session_state.user_email.lower() != ADMIN_EMAIL.lower():
    st.error("Access denied. This page is for admin users only.")
    st.stop()

def run_query(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def run_scalar(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params)
    value = cursor.fetchone()
    conn.close()
    return value[0] if value else 0

def get_users_df():
    rows = run_query("""
        SELECT id, full_name, email, is_verified
        FROM users
        ORDER BY id DESC
    """)
    return pd.DataFrame(rows, columns=["ID", "Full Name", "Email", "Verified"])

def get_scan_history_df():
    rows = run_query("""
        SELECT id, scan_time, original_filename, saved_result_path, benign_count, suspicious_count
        FROM scan_history
        ORDER BY id DESC
        LIMIT 100
    """)
    return pd.DataFrame(
        rows,
        columns=["ID", "Scan Time", "Original Filename", "Saved Result Path", "Benign Count", "Suspicious Count"]
    )

def get_auth_log_df(limit=100):
    rows = run_query("""
        SELECT id, event_time, email, event_type, status, reason, source_ip
        FROM auth_audit_log
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    return pd.DataFrame(
        rows,
        columns=["ID", "Event Time", "Email", "Event Type", "Status", "Reason", "Source IP"]
    )

def get_recent_failed_attempts_df():
    since_time = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    rows = run_query("""
        SELECT event_time, email, event_type, status, reason, source_ip
        FROM auth_audit_log
        WHERE status IN ('failed', 'blocked')
          AND event_time >= ?
        ORDER BY id DESC
        LIMIT 100
    """, (since_time,))
    return pd.DataFrame(
        rows,
        columns=["Event Time", "Email", "Event Type", "Status", "Reason", "Source IP"]
    )

def get_bruteforce_summary_df():
    since_time = (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    rows = run_query("""
        SELECT email, COUNT(*) as failed_count
        FROM auth_audit_log
        WHERE event_type = 'login'
          AND status = 'failed'
          AND event_time >= ?
        GROUP BY email
        HAVING COUNT(*) >= 3
        ORDER BY failed_count DESC
    """, (since_time,))
    return pd.DataFrame(rows, columns=["Email", "Failed Attempts (Last 10 min)"])

total_users = run_scalar("SELECT COUNT(*) FROM users")
verified_users = run_scalar("SELECT COUNT(*) FROM users WHERE is_verified = 1")
unverified_users = run_scalar("SELECT COUNT(*) FROM users WHERE is_verified = 0")
total_scans = run_scalar("SELECT COUNT(*) FROM scan_history")

failed_last_24h = run_scalar("""
    SELECT COUNT(*)
    FROM auth_audit_log
    WHERE status = 'failed'
      AND event_time >= ?
""", ((datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S"),))

blocked_last_24h = run_scalar("""
    SELECT COUNT(*)
    FROM auth_audit_log
    WHERE status = 'blocked'
      AND event_time >= ?
""", ((datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S"),))

st.markdown("<h1 style='text-align:center;'>Admin Security Dashboard</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color:#94a3b8;'>Overview of users, scans, authentication events, and suspicious activity</p>",
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Users", total_users)
with c2:
    st.metric("Verified Users", verified_users)
with c3:
    st.metric("Unverified Users", unverified_users)
with c4:
    st.metric("Total Scans", total_scans)

c5, c6 = st.columns(2)
with c5:
    st.metric("Failed Logins (24h)", failed_last_24h)
with c6:
    st.metric("Blocked Attempts (24h)", blocked_last_24h)

st.markdown("### Brute-Force Monitoring")
bruteforce_df = get_bruteforce_summary_df()
if not bruteforce_df.empty:
    st.warning("Potential brute-force activity detected based on repeated failed logins.")
    st.dataframe(bruteforce_df, use_container_width=True)
else:
    st.success("No obvious brute-force pattern detected in the last 10 minutes.")

st.markdown("### Registered Users")
users_df = get_users_df()
if not users_df.empty:
    users_df["Verified"] = users_df["Verified"].map({1: "Yes", 0: "No"})
    st.dataframe(users_df, use_container_width=True)
else:
    st.info("No users found.")

st.markdown("### Recent Failed or Blocked Access Events")
failed_df = get_recent_failed_attempts_df()
if not failed_df.empty:
    st.dataframe(failed_df, use_container_width=True)
else:
    st.info("No failed or blocked events recorded in the last 24 hours.")

st.markdown("### Recent Authentication Audit Log")
auth_df = get_auth_log_df(limit=100)
if not auth_df.empty:
    st.dataframe(auth_df, use_container_width=True)
else:
    st.info("No authentication audit logs recorded yet.")

st.markdown("### Recent Scan History")
scan_df = get_scan_history_df()
if not scan_df.empty:
    st.dataframe(scan_df, use_container_width=True)
else:
    st.info("No scans recorded yet.")