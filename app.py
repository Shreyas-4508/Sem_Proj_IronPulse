"""
IronPulse — Main Streamlit Application Entry Point
Handles routing, authentication gate, and global CSS theming.
"""

import logging
import streamlit as st

# ─── Page config must be the FIRST Streamlit call ────────────────────────────
st.set_page_config(
    page_title="IronPulse — AI Fitness Platform",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "IronPulse v1.0 — AI-Powered Home Fitness Platform",
    },
)

# ─── Imports after set_page_config ───────────────────────────────────────────
from config import settings
from database.connection import get_db_session, init_db, check_database_connection
from services.auth_service import register_user, login_user, AuthError
from components.cards import info_banner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Global CSS / Theme ───────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset & base ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0d0d0d !important;
    color: #e8e8e8 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Hide default Streamlit elements ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
[data-testid="stToolbar"] { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111111 0%, #0a0a0a 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] * { font-family: 'Inter', sans-serif !important; }

/* ── Primary buttons ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #FF6B35, #FF4500) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 12px rgba(255,107,53,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(255,107,53,0.5) !important;
}

/* ── Secondary buttons ── */
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #ccc !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.1) !important;
    border-color: rgba(255,107,53,0.4) !important;
    color: #fff !important;
}

/* ── Text inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #e8e8e8 !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(255,107,53,0.6) !important;
    box-shadow: 0 0 0 2px rgba(255,107,53,0.15) !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #e8e8e8 !important;
    border-radius: 8px !important;
}

/* ── Form container ── */
[data-testid="stForm"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 8px !important;
    padding: 4px !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px !important;
    color: #888 !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(255,107,53,0.2) !important;
    color: #FF6B35 !important;
}

/* ── Divider ── */
hr {
    border-color: rgba(255,255,255,0.07) !important;
    margin: 1rem 0 !important;
}

/* ── Info / Success / Warning ── */
.stAlert {
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Multiselect ── */
.stMultiSelect > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important;
}

/* ── Labels ── */
label, .stMarkdown p { color: #ccc !important; }
</style>
"""

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ─── Database Initialization ─────────────────────────────────────────────────

def _ensure_database():
    """Initialize the database on first run. Shows an error banner if unavailable."""
    ok, msg = check_database_connection()
    if not ok:
        st.error(f"⚠️ Database unavailable: {msg}\n\nCheck your `.env` or `DATABASE_URL` setting.")
        st.stop()

    # For development with SQLite, auto-create tables
    if settings.using_sqlite:
        init_db()


# ─── Auth Pages ───────────────────────────────────────────────────────────────

def _render_auth_page():
    """Renders login/registration page when the user is not authenticated."""
    col_l, col_c, col_r = st.columns([1, 2, 1])

    with col_c:
        # Brand header
        st.markdown(
            """
            <div style="text-align:center; padding: 2rem 0 1.5rem;">
                <span style="font-size:4rem;">🏋️</span>
                <h1 style="
                    margin: 0.5rem 0 0;
                    font-size: 2.5rem;
                    font-weight: 800;
                    background: linear-gradient(135deg, #FF6B35, #FF8C42);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    letter-spacing: -1px;
                ">IronPulse</h1>
                <p style="color:#888;font-size:0.95rem;margin:0.3rem 0 0;">
                    Your AI-powered home fitness companion
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_login, tab_register = st.tabs(["🔑 Sign In", "📝 Create Account"])

        # ── Login ──────────────────────────────────────────────────
        with tab_login:
            with st.form("login_form"):
                st.markdown("##### Welcome back!")
                identifier = st.text_input(
                    "Email or Username",
                    placeholder="your@email.com or username",
                    key="login_identifier",
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="••••••••",
                    key="login_password",
                )
                submitted = st.form_submit_button(
                    "Sign In →",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                if not identifier or not password:
                    info_banner("Please fill in all fields.", type="error")
                else:
                    try:
                        with get_db_session() as db:
                            user = login_user(db, identifier, password)
                        # Store minimal session state
                        st.session_state["user_id"] = user.id
                        st.session_state["username"] = user.username
                        st.session_state["display_name"] = (
                            user.profile.display_name if user.profile else user.username
                        )
                        st.session_state["current_page"] = "Dashboard"
                        st.rerun()
                    except AuthError as e:
                        info_banner(str(e), type="error")
                    except Exception as e:
                        logger.error("Login error: %s", e)
                        info_banner("An unexpected error occurred. Please try again.", type="error")

        # ── Register ───────────────────────────────────────────────
        with tab_register:
            with st.form("register_form"):
                st.markdown("##### Start your fitness journey")
                email = st.text_input(
                    "Email Address *",
                    placeholder="your@email.com",
                    key="reg_email",
                )
                username = st.text_input(
                    "Username *",
                    placeholder="ironpulse_user",
                    help="3–50 characters. Letters, numbers, underscores only.",
                    key="reg_username",
                )
                password = st.text_input(
                    "Password *",
                    type="password",
                    placeholder="Minimum 8 characters",
                    key="reg_password",
                )
                confirm_password = st.text_input(
                    "Confirm Password *",
                    type="password",
                    placeholder="Repeat your password",
                    key="reg_confirm",
                )
                agree = st.checkbox(
                    "I understand this app provides fitness estimates, not medical advice.",
                    key="reg_agree",
                )
                submitted = st.form_submit_button(
                    "Create Account →",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                if not agree:
                    info_banner("Please acknowledge the disclaimer to continue.", type="warning")
                else:
                    try:
                        with get_db_session() as db:
                            user = register_user(db, email, username, password, confirm_password)
                        st.session_state["user_id"] = user.id
                        st.session_state["username"] = user.username
                        st.session_state["display_name"] = user.username
                        st.session_state["current_page"] = "Profile"  # Send to onboarding
                        info_banner("Account created! Let's set up your profile.", type="success")
                        st.rerun()
                    except AuthError as e:
                        info_banner(str(e), type="error")
                    except Exception as e:
                        logger.error("Registration error: %s", e)
                        info_banner("An unexpected error occurred. Please try again.", type="error")

        # Feature highlights
        st.markdown(
            """
            <div style="margin-top:2rem;display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.8rem;">
                <div style="
                    background:rgba(255,107,53,0.08);
                    border:1px solid rgba(255,107,53,0.2);
                    border-radius:10px;padding:0.8rem;text-align:center;
                ">
                    <div style="font-size:1.5rem;">🏋️</div>
                    <div style="font-size:0.75rem;color:#ccc;margin-top:0.3rem;font-weight:500;">
                        AI Workouts
                    </div>
                </div>
                <div style="
                    background:rgba(255,107,53,0.08);
                    border:1px solid rgba(255,107,53,0.2);
                    border-radius:10px;padding:0.8rem;text-align:center;
                ">
                    <div style="font-size:1.5rem;">🥗</div>
                    <div style="font-size:0.75rem;color:#ccc;margin-top:0.3rem;font-weight:500;">
                        Nutrition Plans
                    </div>
                </div>
                <div style="
                    background:rgba(255,107,53,0.08);
                    border:1px solid rgba(255,107,53,0.2);
                    border-radius:10px;padding:0.8rem;text-align:center;
                ">
                    <div style="font-size:1.5rem;">🏆</div>
                    <div style="font-size:0.75rem;color:#ccc;margin-top:0.3rem;font-weight:500;">
                        Achievements
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─── Authenticated App Shell ──────────────────────────────────────────────────

def _render_app():
    """Renders the main authenticated application with navigation."""
    from components.navigation import render_sidebar
    from pages import dashboard, profile, settings as settings_page
    from pages import nutrition, progress, workouts

    current_page = st.session_state.get("current_page", "Dashboard")
    selected = render_sidebar(current_page)

    if selected == "Logout":
        _logout()
        return

    # Update current page
    if selected != current_page:
        st.session_state["current_page"] = selected
        st.rerun()

    # Route to page modules
    page_map = {
        "Dashboard": dashboard.render,
        "Workouts": workouts.render,
        "Nutrition": nutrition.render,
        "Progress": progress.render,
        "Profile":   profile.render,
        "Settings":  settings_page.render,
    }

    render_fn = page_map.get(current_page, dashboard.render)
    try:
        render_fn()
    except Exception as e:
        logger.exception("Error rendering page %s: %s", current_page, e)
        st.error(f"⚠️ Page error: {e}")


def _logout():
    """Clears session state and redirects to auth page."""
    keys_to_clear = ["user_id", "username", "display_name", "current_page"]
    for key in keys_to_clear:
        st.session_state.pop(key, None)
    st.rerun()


# ─── App Entry Point ──────────────────────────────────────────────────────────

def main():
    _ensure_database()

    if "user_id" in st.session_state and st.session_state["user_id"]:
        _render_app()
    else:
        _render_auth_page()


if __name__ == "__main__":
    main()
