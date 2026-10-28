"""
Settings page — account settings and application preferences.
"""

import streamlit as st
from components.cards import section_header, info_banner
from services.auth_service import change_password, AuthError
from database.connection import get_db_session


def render():
    """Renders the settings page."""
    user_id = st.session_state.get("user_id")
    username = st.session_state.get("username", "")

    section_header("⚙️ Account Settings")

    tabs = st.tabs(["Security", "About"])

    with tabs[0]:
        st.markdown("#### 🔐 Change Password")
        with st.form("settings_password_form"):
            current_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password",
                                   help="Minimum 8 characters.")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("🔑 Update Password", type="primary"):
                try:
                    with get_db_session() as db:
                        change_password(db, user_id, current_pw, new_pw, confirm_pw)
                    st.success("✅ Password updated successfully!")
                except AuthError as e:
                    info_banner(str(e), type="error")

    with tabs[1]:
        st.markdown("#### ℹ️ About IronPulse")
        st.markdown(
            """
            **IronPulse** is an AI-powered home fitness platform designed to help you:
            - Build personalized workout routines
            - Track your nutrition and calories
            - Monitor your fitness progress
            - Connect with a fitness community
            - Stay motivated with achievements and streaks

            ---
            **Version:** 1.0.0 · Stage 1  
            **Stack:** Python · Streamlit · SQLAlchemy · PostgreSQL  
            **Support:** Review `README.md` for setup and troubleshooting.
            """
        )
