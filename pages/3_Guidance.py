from pathlib import Path

import streamlit as st
# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Guidance", layout="wide")

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "sentia_logo.png"

# =========================
# ADMIN EMAIL
# =========================
ADMIN_EMAIL = "info@sentiatechnologieslimited.com"

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

user_email = st.session_state.get("user_email", "").lower()
is_admin = user_email == ADMIN_EMAIL.lower()

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
    max-width: 1180px;
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

h1, h2, h3, h4, p, div, span, label, li {
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

.muted {
    color: #94a3b8 !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =========================
# PAGE HEADER
# =========================
st.markdown("<h1 style='text-align:center;'>Security Guidance</h1>", unsafe_allow_html=True)

if is_admin:
    st.markdown(
        "<p style='text-align:center; color:#94a3b8;'>Internal operational guidance for Sentia administration and service oversight</p>",
        unsafe_allow_html=True
    )
else:
    st.markdown(
        "<p style='text-align:center; color:#94a3b8;'>Practical guidance to help your business stay secure, trusted, and ready to grow online</p>",
        unsafe_allow_html=True
    )

st.write("")

# =========================
# ADMIN VIEW
# =========================
if is_admin:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Daily Operational Checklist")
    st.markdown("""
- Review scan results and recent platform activity.
- Check for suspicious login attempts and failed access patterns.
- Confirm email verification and onboarding workflows are functioning properly.
- Keep systems, software, and dependencies updated.
- Verify backup status and confirm scan records are saving correctly.
- Review customer support needs and unresolved issues.
- Report unusual activity immediately and document observations.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Incident Response Guidance")
    st.markdown("""
1. Identify the suspicious activity or service issue clearly.  
2. Check related logs, alerts, and recent account events.  
3. Isolate affected systems or workflows if required.  
4. Review the scope and likely impact.  
5. Escalate to the appropriate security or technical contact.  
6. Document actions taken, timestamps, and outcomes.  
7. Follow up to confirm resolution and prevent recurrence.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Internal Customer Service Priorities")
    st.markdown("""
- Ensure customers can register, verify, and access the platform without friction.
- Monitor password reset and verification email delivery.
- Keep scan history accurate and available for review.
- Maintain a professional, supportive, and responsive experience.
- Track recurring customer pain points and improve the platform accordingly.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Internal Documents and Guidance")
    st.markdown("""
- Password policy  
- Phishing awareness guide  
- Daily cyber hygiene checklist  
- Small business security recommendations  
- Client communication and escalation notes  
- Service quality review checklist  
    """)
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# CUSTOMER VIEW
# =========================
else:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Building a Stronger Business in a Secure Digital Environment")
    st.write(
        "A strong business today is not built on visibility alone. It is built on trust, consistency, "
        "and the confidence that your customers can rely on your digital presence. Sentia supports "
        "businesses that want to grow in a way that is practical, secure, and sustainable."
    )
    st.write(
        "For many growing businesses, digital growth brings both opportunity and pressure. You may be "
        "building a website, reaching more customers online, managing digital communication, or handling "
        "important information through cloud services and shared platforms. As your business grows, so does "
        "the need to protect your presence, maintain trust, and avoid unnecessary disruption."
    )
    st.write(
        "That is why good security should not feel separate from business growth. It should support it. "
        "A secure business is easier to trust, easier to operate, and better prepared to grow with confidence."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Key Security Practices Every Business Should Follow")
    st.markdown("""
- Use strong, unique passwords for business accounts and platforms.
- Do not share passwords between staff, partners, or devices.
- Enable verification steps where available and keep login details private.
- Review account activity regularly and act quickly if anything looks unusual.
- Keep software, plugins, browsers, and operating systems updated.
- Back up important files and customer information consistently.
- Be cautious with unknown links, attachments, and unexpected requests for sensitive data.
- Limit access to important systems so only the right people can use them.
    """)
    st.write(
        "These simple habits reduce avoidable risk and help protect the day-to-day continuity of your business."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Protecting Trust While You Grow")
    st.write(
        "Growth is not only about attracting more attention. It is also about keeping the confidence of the "
        "people who already rely on you. Customers, partners, and clients are more likely to stay with a business "
        "that feels organised, reliable, and careful with its operations."
    )
    st.write(
        "When your online presence is stable, your communication is clear, and your systems are handled responsibly, "
        "your business becomes easier to trust. That trust supports stronger relationships, repeat engagement, and "
        "better long-term growth."
    )
    st.write(
        "In practical terms, this means taking care of the details that often go unnoticed until something goes wrong: "
        "access control, updates, account monitoring, responsible use of data, and having a plan for what to do when "
        "something unexpected happens."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Good Digital Habits for Growing Businesses")
    st.markdown("""
- Review your main business accounts regularly.
- Keep your business email secure and monitored.
- Use professional and trusted communication channels.
- Make sure your website and core business tools stay current and maintained.
- Document important processes so your team can work consistently.
- Keep essential files, records, and assets organised and backed up.
- Build your online reputation with clarity, consistency, and professionalism.
    """)
    st.write(
        "Good digital habits make your business more resilient. They also help you stay prepared as your customer base, "
        "team size, and service demands increase."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### How Sentia Supports Your Journey")
    st.write(
        "Sentia is not only about protection. It is also about support, structure, and helping businesses move forward "
        "with confidence. Through guidance, digital insight, and practical tools, the aim is to help businesses strengthen "
        "their foundations while building a presence that is credible, sustainable, and ready for growth."
    )
    st.write(
        "Whether you are just starting out or trying to improve how your business appears and operates online, the goal is "
        "to support you in a way that is clear, useful, and realistic. Good support should help businesses grow, not overwhelm them."
    )
    st.write(
        "As the platform continues to grow, this space can provide more educational content, practical recommendations, and "
        "supportive guidance that helps businesses become more secure, more visible, and better prepared for long-term success."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### What Customers Should Remember")
    st.markdown("""
- Growth and security should work together.
- Trust is easier to build when your business feels stable and well managed.
- Simple digital habits can prevent bigger problems later.
- A reliable online presence supports stronger customer confidence.
- Support, clarity, and preparation are part of sustainable growth.
    """)
    st.markdown("</div>", unsafe_allow_html=True)