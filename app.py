import os
import re
import html
import random
from pathlib import Path

import feedparser
import requests
import streamlit as st

from db_utils import (
    init_db,
    create_user,
    login_user,
    verify_user,
    user_exists_unverified,
    user_exists_verified,
    update_verification_code,
    get_user_full_name_by_email,
    log_auth_event,
    is_account_locked,
    set_reset_code,
    verify_reset_code,
    update_password
)

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Sentia Security Portal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "sentia_logo.png"
HERO_PATH = ASSETS_DIR / "hero_banner.png"

# =========================
# MICROSOFT GRAPH CONFIG
# =========================
SENDER_EMAIL = "info@sentiatechnologieslimited.com"

TENANT_ID = os.getenv("SENTIA_TENANT_ID", "")
CLIENT_ID = os.getenv("SENTIA_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("SENTIA_CLIENT_SECRET", "")

# =========================
# SECURITY SETTINGS
# =========================
BRUTE_FORCE_THRESHOLD = 5
BRUTE_FORCE_WINDOW_MINUTES = 10

# =========================
# MEDIUM CONFIG
# =========================
MEDIUM_FEED_URL = "https://medium.com/feed/@sentia_technologies_limited"

# =========================
# INIT DB
# =========================
init_db()

# =========================
# HELPERS
# =========================
def generate_verification_code():
    return str(random.randint(100000, 999999))


def generate_reset_code():
    return str(random.randint(100000, 999999))


def get_graph_access_token():
    if not TENANT_ID or not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError(
            "Microsoft Graph credentials are not set in environment variables. "
            "Please set SENTIA_TENANT_ID, SENTIA_CLIENT_ID, and SENTIA_CLIENT_SECRET."
        )

    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    response = requests.post(token_url, data=data, timeout=30)
    response.raise_for_status()

    token = response.json().get("access_token")
    if not token:
        raise ValueError("Could not obtain Microsoft Graph access token.")
    return token


def send_graph_email(recipient_email, subject, html_content):
    token = get_graph_access_token()

    url = f"https://graph.microsoft.com/v1.0/users/{SENDER_EMAIL}/sendMail"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": html_content
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": recipient_email
                    }
                }
            ]
        },
        "saveToSentItems": True
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()


def send_verification_email(recipient_email, code):
    subject = "Sentia Portal Verification Code"
    html_content = f"""
    <div style="font-family:Segoe UI,Arial,sans-serif; padding:28px; background:#020617; color:#ffffff;">
        <div style="max-width:620px; margin:0 auto; background:#071226; border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:28px;">
            <h2 style="margin-bottom:8px;">Sentia Security Portal</h2>
            <p style="color:#cbd5e1;">Use the verification code below to activate your account.</p>
            <div style="font-size:32px; font-weight:700; letter-spacing:4px; color:#38bdf8; margin:24px 0;">
                {code}
            </div>
            <p style="color:#cbd5e1;">If you did not request this, you can ignore this email.</p>
            <p style="color:#94a3b8; margin-top:24px;">Sentia Technologies Limited</p>
        </div>
    </div>
    """
    send_graph_email(recipient_email, subject, html_content)


def send_onboarding_email(recipient_email, full_name):
    subject = "Welcome to Sentia"
    html_content = f"""
    <div style="font-family:Segoe UI,Arial,sans-serif; padding:28px; background:#020617; color:#ffffff;">
        <div style="max-width:620px; margin:0 auto; background:#071226; border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:28px;">
            <h2>Welcome to Sentia</h2>
            <p>Hello {full_name},</p>
            <p>Your account has been successfully verified and activated.</p>
            <p>Sentia is designed to support growing businesses with practical digital guidance, structured support, and trusted visibility.</p>
            <p>You can now log in to explore:</p>
            <ul>
                <li>Business support insights</li>
                <li>Security guidance and practical recommendations</li>
                <li>Reports and account tools</li>
                <li>Sentia articles and updates</li>
            </ul>
            <p style="margin-top:24px; color:#94a3b8;">Sentia Technologies Limited</p>
        </div>
    </div>
    """
    send_graph_email(recipient_email, subject, html_content)


def send_password_reset_email(recipient_email, code):
    subject = "Sentia Password Reset Code"
    html_content = f"""
    <div style="font-family:Segoe UI,Arial,sans-serif; padding:28px; background:#020617; color:#ffffff;">
        <div style="max-width:620px; margin:0 auto; background:#071226; border:1px solid rgba(255,255,255,0.08); border-radius:18px; padding:28px;">
            <h2>Reset Your Password</h2>
            <p style="color:#cbd5e1;">Use the code below to reset your Sentia account password.</p>
            <div style="font-size:32px; font-weight:700; letter-spacing:4px; color:#38bdf8; margin:24px 0;">
                {code}
            </div>
            <p style="color:#cbd5e1;">If you did not request a reset, you can ignore this email.</p>
            <p style="color:#94a3b8; margin-top:24px;">Sentia Technologies Limited</p>
        </div>
    </div>
    """
    send_graph_email(recipient_email, subject, html_content)


def strip_html_tags(text):
    if not text:
        return ""
    text = re.sub(r"<.*?>", "", text)
    return html.unescape(text).strip()


def extract_first_image(html_text):
    if not html_text:
        return None
    match = re.search(r'<img[^>]+src="([^"]+)"', html_text)
    if match:
        return match.group(1)
    return None


@st.cache_data(ttl=1800)
def get_medium_posts():
    feed = feedparser.parse(MEDIUM_FEED_URL)
    posts = []

    if not getattr(feed, "entries", None):
        return posts

    for entry in feed.entries[:3]:
        title = entry.get("title", "Untitled Article")
        link = entry.get("link", "#")

        content_html = ""
        if "content" in entry and entry.content:
            content_html = entry.content[0].value
        else:
            content_html = entry.get("summary", "")

        image_url = extract_first_image(content_html)
        preview_text = strip_html_tags(content_html)
        preview_text = preview_text[:220] + "..." if len(preview_text) > 220 else preview_text

        posts.append({
            "title": title,
            "link": link,
            "image": image_url,
            "preview": preview_text
        })

    return posts


def render_hero():
    if HERO_PATH.exists():
        st.markdown('<div class="hero-wrap">', unsafe_allow_html=True)
        st.image(str(HERO_PATH), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


def render_auth_header(title, subtitle):
    render_hero()
    st.markdown(f"<h1 class='page-title'>{title}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='page-subtitle'>{subtitle}</p>", unsafe_allow_html=True)


def auth_shell():
    left, center, right = st.columns([1, 1.05, 1])
    return center


# =========================
# STYLING
# =========================
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

h1, h2, h3, h4, h5, h6, p, div, span, label {
    color: var(--text-main);
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

.glass-card * {
    color: var(--text-main) !important;
}

.panel-card {
    background: var(--card-strong);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 22px;
    padding: 24px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.18);
    margin-bottom: 18px;
}

.panel-card * {
    color: var(--text-main) !important;
}

.article-card {
    background: var(--card-strong);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 18px;
    min-height: 100%;
    box-shadow: 0 10px 28px rgba(0,0,0,0.16);
}

.article-card * {
    color: var(--text-main) !important;
}

.article-image img {
    border-radius: 14px !important;
}

.stTextInput {
    margin-bottom: 14px;
}

.stTextInput input {
    background: rgba(15, 23, 42, 0.82) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 14px !important;
    padding: 0.95rem !important;
    box-shadow: none !important;
}

.stTextInput input:focus {
    border: 1px solid #38bdf8 !important;
    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.22) !important;
    outline: none !important;
}

.stTextInput input::placeholder {
    color: #9fb1c7 !important;
}

label, .stTextInput label, .stTextInput div[data-testid="stWidgetLabel"] {
    color: #dbe4f0 !important;
    font-weight: 600;
}

.stButton > button {
    background: linear-gradient(90deg, var(--accent-1), var(--accent-2)) !important;
    color: var(--accent-dark) !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.85rem 1.1rem !important;
    font-weight: 800 !important;
    width: 100% !important;
    box-shadow: 0 8px 24px rgba(34, 211, 238, 0.18);
}

.stButton > button:hover {
    background: linear-gradient(90deg, #67e8f9, #60a5fa) !important;
    color: var(--accent-dark) !important;
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

.stAlert * {
    font-weight: 600 !important;
}

div[data-baseweb="notification"] {
    border-radius: 14px !important;
}

div[data-baseweb="notification"] * {
    color: #0f172a !important;
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

.small-note {
    color: var(--text-soft) !important;
    line-height: 1.7;
}

.read-link a {
    font-weight: 700;
    text-decoration: none;
}

.read-link a:hover {
    text-decoration: underline;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================
if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), width=90)

st.sidebar.markdown("<div class='brand-title'>Sentia Portal</div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='brand-subtitle'>Secure Your Digital Future</div>", unsafe_allow_html=True)
st.sidebar.write("")

# =========================
# SESSION STATE
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

if "verify_email" not in st.session_state:
    st.session_state.verify_email = ""

if "reset_email" not in st.session_state:
    st.session_state.reset_email = ""

# =========================
# VERIFY ACCOUNT
# =========================
def verify_account():
    render_auth_header("Verify Account", "Enter the code sent to your email to activate your Sentia account")

    with auth_shell():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        email = st.text_input(
            "Email",
            value=st.session_state.get("verify_email", ""),
            placeholder="Enter your email"
        )
        code = st.text_input("Verification Code", placeholder="Enter your 6-digit code")

        c1, c2 = st.columns(2)

        with c1:
            if st.button("Verify Account"):
                if verify_user(email, code):
                    log_auth_event(email, "verification", "success", "Account verified")
                    full_name = get_user_full_name_by_email(email)

                    try:
                        send_onboarding_email(email, full_name)
                        log_auth_event(email, "onboarding_email", "success", "Onboarding email sent")
                    except Exception as e:
                        log_auth_event(email, "onboarding_email", "failed", str(e))

                    st.success("Account verified successfully. You can now log in.")
                    st.session_state.auth_mode = "login"
                    st.rerun()
                else:
                    log_auth_event(email, "verification", "failed", "Invalid verification code")
                    st.error("Invalid verification code.")

        with c2:
            if st.button("Resend Code"):
                if user_exists_unverified(email):
                    new_code = generate_verification_code()
                    updated = update_verification_code(email, new_code)

                    if updated:
                        try:
                            send_verification_email(email, new_code)
                            log_auth_event(email, "verification_email", "success", "Verification code resent")
                            st.success("A new verification code has been sent to your email.")
                        except Exception as e:
                            log_auth_event(email, "verification_email", "failed", str(e))
                            st.error(f"Could not resend code: {e}")
                    else:
                        st.error("Could not update verification code.")
                else:
                    st.error("No unverified account found for this email.")

        if st.button("Back to Login"):
            st.session_state.auth_mode = "login"
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# =========================
# FORGOT PASSWORD
# =========================
def forgot_password():
    render_auth_header("Reset Password", "Request a reset code and create a new password for your Sentia account")

    with auth_shell():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        email = st.text_input(
            "Email",
            value=st.session_state.get("reset_email", ""),
            placeholder="Enter your verified email"
        )
        reset_code = st.text_input("Reset Code", placeholder="Enter the code sent to your email")
        new_password = st.text_input("New Password", type="password", placeholder="Create a new password")
        confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Confirm your new password")

        c1, c2 = st.columns(2)

        with c1:
            if st.button("Send Reset Code"):
                if not email:
                    st.error("Please enter your email address.")
                elif not user_exists_verified(email):
                    log_auth_event(email, "password_reset", "failed", "No verified account found")
                    st.error("No verified account found for this email.")
                else:
                    reset_code_value = generate_reset_code()
                    updated = set_reset_code(email, reset_code_value)

                    if updated:
                        try:
                            send_password_reset_email(email, reset_code_value)
                            log_auth_event(email, "password_reset_email", "success", "Password reset code sent")
                            st.session_state.reset_email = email
                            st.success("Password reset code sent to your email.")
                        except Exception as e:
                            log_auth_event(email, "password_reset_email", "failed", str(e))
                            st.error(f"Could not send reset email: {e}")
                    else:
                        st.error("Could not create reset code for this account.")

        with c2:
            if st.button("Reset Password"):
                if not email or not reset_code or not new_password or not confirm_password:
                    st.error("Please complete all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif not verify_reset_code(email, reset_code):
                    log_auth_event(email, "password_reset", "failed", "Invalid reset code")
                    st.error("Invalid reset code.")
                else:
                    updated = update_password(email, new_password)
                    if updated:
                        log_auth_event(email, "password_reset", "success", "Password updated successfully")
                        st.success("Password reset successful. You can now log in.")
                        st.session_state.auth_mode = "login"
                        st.rerun()
                    else:
                        st.error("Could not update password.")

        if st.button("Back to Login"):
            st.session_state.auth_mode = "login"
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# =========================
# SIGNUP
# =========================
def signup():
    render_auth_header("Create Account", "Join the Sentia customer portal and access insights, guidance, and platform tools")

    with auth_shell():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        full_name = st.text_input("Full Name", placeholder="Enter your full name")
        email = st.text_input("Email", placeholder="Enter your email address")
        password = st.text_input("Password", type="password", placeholder="Create a password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")

        if st.button("Create Account"):
            log_auth_event(email, "signup", "attempt", "User submitted signup form")

            if not full_name or not email or not password or not confirm_password:
                log_auth_event(email, "signup", "failed", "Missing required fields")
                st.error("Please complete all fields.")
            elif password != confirm_password:
                log_auth_event(email, "signup", "failed", "Passwords do not match")
                st.error("Passwords do not match.")
            elif user_exists_verified(email):
                log_auth_event(email, "signup", "failed", "Verified account already exists")
                st.error("An account with this email already exists.")
            else:
                code = generate_verification_code()
                success, message = create_user(full_name, email, password, code)

                if success:
                    log_auth_event(email, "signup", "success", "Account created")
                    try:
                        send_verification_email(email, code)
                        log_auth_event(email, "verification_email", "success", "Verification email sent")
                        st.success("Verification code sent to your email.")
                        st.session_state.verify_email = email
                        st.session_state.auth_mode = "verify"
                        st.rerun()
                    except Exception as e:
                        log_auth_event(email, "verification_email", "failed", str(e))
                        st.error(f"Account created, but email could not be sent: {e}")
                else:
                    log_auth_event(email, "signup", "failed", message)
                    st.error(message)

        if st.button("Back to Login"):
            st.session_state.auth_mode = "login"
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# =========================
# LOGIN
# =========================
def login():
    render_auth_header("Sentia Security Portal", "A secure client space for business support, guidance, learning, and service access")

    with auth_shell():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        st.markdown("<div class='section-title' style='font-size:1.5rem; text-align:center;'>Customer Login</div>", unsafe_allow_html=True)
        st.markdown("<div class='section-subtitle' style='text-align:center;'>Access your account and continue building with confidence</div>", unsafe_allow_html=True)

        email = st.text_input("Email", placeholder="Enter your email address")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        if st.button("Login"):
            locked, failed_count = is_account_locked(
                email,
                threshold=BRUTE_FORCE_THRESHOLD,
                window_minutes=BRUTE_FORCE_WINDOW_MINUTES
            )

            if locked:
                log_auth_event(
                    email,
                    "login",
                    "blocked",
                    f"Potential brute-force pattern detected. Failed attempts in last {BRUTE_FORCE_WINDOW_MINUTES} minutes: {failed_count}"
                )
                st.error("Too many failed login attempts detected. Please try again later.")
            else:
                user = login_user(email, password)
                if user:
                    log_auth_event(email, "login", "success", "User logged in successfully")
                    st.session_state.logged_in = True
                    st.session_state.user_name = user[1]
                    st.session_state.user_email = user[2]
                    st.success("Login successful.")
                    st.rerun()
                else:
                    if user_exists_unverified(email):
                        log_auth_event(email, "login", "failed", "Account not verified")
                        st.error("This account is not verified yet. Please verify your email first.")
                        st.session_state.verify_email = email
                        st.session_state.auth_mode = "verify"
                    else:
                        log_auth_event(email, "login", "failed", "Invalid email or password")
                        remaining = BRUTE_FORCE_THRESHOLD - (failed_count + 1)
                        if remaining > 0:
                            st.error(f"Invalid email or password. Remaining attempts before lockout: {remaining}")
                        else:
                            st.error("Invalid email or password. Security lockout threshold reached.")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Create New Account"):
                st.session_state.auth_mode = "signup"
                st.rerun()
        with c2:
            if st.button("Forgot Password"):
                st.session_state.auth_mode = "forgot_password"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# =========================
# DASHBOARD
# =========================
def dashboard():
    render_hero()

    st.markdown(
        f"<h1 class='page-title'>Welcome, {st.session_state.user_name}</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p class='page-subtitle'>Sentia Business Support Portal</p>",
        unsafe_allow_html=True
    )

    st.write("")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Business Support", "Active")
    with m2:
        st.metric("Digital Presence", "Growing")
    with m3:
        st.metric("Trusted Guidance", "Available")

    st.write("")

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Helping Your Business Stay Visible, Trusted, and Ready to Grow</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-subtitle'>Support designed for growing businesses that want to move with more clarity and confidence</div>", unsafe_allow_html=True)
    st.markdown("<div class='soft-divider'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='small-note'>Sentia supports startups and growing businesses with practical digital guidance, business education, and structured support designed to help you build confidence online.</div>",
        unsafe_allow_html=True
    )
    st.write("")
    st.markdown(
        "<div class='small-note'>Whether you are strengthening your business foundation, improving trust with customers, or building a stronger online presence, this platform is designed to support that journey in a practical and professional way.</div>",
        unsafe_allow_html=True
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    st.markdown("<div class='section-title' style='font-size:2.1rem;'>Latest Insights from Sentia</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-subtitle'>Read practical articles on business growth, trust, visibility, and secure digital progress</div>", unsafe_allow_html=True)

    medium_posts = get_medium_posts()

    if medium_posts:
        cols = st.columns(len(medium_posts))
        for i, post in enumerate(medium_posts):
            with cols[i]:
                st.markdown('<div class="article-card">', unsafe_allow_html=True)

                if post["image"]:
                    st.markdown('<div class="article-image">', unsafe_allow_html=True)
                    st.image(post["image"], use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                st.markdown(f"#### {post['title']}")
                st.write(post["preview"])
                st.markdown(
                    f"<div class='read-link'><a href='{post['link']}' target='_blank'>Continue reading on Medium</a></div>",
                    unsafe_allow_html=True
                )

                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.write("Latest Sentia articles will appear here automatically after publication on Medium.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("<div class='section-title'>What You Can Explore Next</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-subtitle'>Use the portal to learn, review, and move forward with better structure</div>", unsafe_allow_html=True)
    st.markdown("<div class='soft-divider'></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown("### Business Tools")
        st.write("Explore platform tools and service pathways that support your growth journey.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown("### Reports and Guidance")
        st.write("Review practical guidance and reports that support more confident business decisions.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown("### Learn with Sentia")
        st.write("Read educational insights designed to help businesses build trust, visibility, and resilience.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.info("Use the sidebar to explore scan tools, reports, guidance, and history as needed.")

    st.write("")
    if st.button("Logout"):
        log_auth_event(st.session_state.user_email, "logout", "success", "User logged out")
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.session_state.user_email = ""
        st.session_state.auth_mode = "login"
        st.rerun()

# =========================
# ROUTING
# =========================
if st.session_state.logged_in:
    dashboard()
else:
    if st.session_state.auth_mode == "signup":
        signup()
    elif st.session_state.auth_mode == "verify":
        verify_account()
    elif st.session_state.auth_mode == "forgot_password":
        forgot_password()
    else:
        login()