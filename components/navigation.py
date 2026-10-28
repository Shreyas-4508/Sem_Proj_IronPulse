"""
Navigation component — renders the sidebar with IronPulse branding and menu.
"""

import streamlit as st


def render_sidebar(current_page: str = "Dashboard") -> str:
    """
    Renders the sidebar navigation and returns the selected page name.
    Requires st.session_state['user_id'] to be set.
    """
    with st.sidebar:
        # ─── Brand ───────────────────────────────────────────────
        st.markdown(
            """
            <div style="text-align:center; padding: 1rem 0 0.5rem;">
                <span style="font-size:2.2rem;">🏋️</span>
                <h1 style="
                    margin:0;
                    font-size:1.6rem;
                    font-weight:800;
                    background: linear-gradient(135deg, #FF6B35, #FF8C42);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    letter-spacing:-0.5px;
                ">IronPulse</h1>
                <p style="margin:0;font-size:0.7rem;color:#888;letter-spacing:2px;">FITNESS PLATFORM</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        # ─── User Info ────────────────────────────────────────────
        username = st.session_state.get("username", "User")
        display_name = st.session_state.get("display_name", username)
        st.markdown(
            f"""
            <div style="
                background:rgba(255,107,53,0.1);
                border:1px solid rgba(255,107,53,0.2);
                border-radius:8px;
                padding:0.6rem 0.8rem;
                margin-bottom:0.8rem;
            ">
                <p style="margin:0;font-size:0.75rem;color:#888;">Logged in as</p>
                <p style="margin:0;font-size:0.9rem;font-weight:600;color:#FF6B35;">@{username}</p>
                <p style="margin:0;font-size:0.8rem;color:#ccc;">{display_name}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ─── Navigation Menu ──────────────────────────────────────
        pages = {
            "🏠  Dashboard": "Dashboard",
            "🏋️  Workouts": "Workouts",
            "🥗  Nutrition": "Nutrition",
            "📈  Progress": "Progress",
            "👤  Profile": "Profile",
            "⚙️  Settings": "Settings",
        }

        selected = None
        for label, page_name in pages.items():
            is_active = page_name == current_page
            if st.button(
                label,
                key=f"nav_{page_name}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                selected = page_name

        st.divider()

        # ─── Logout ───────────────────────────────────────────────
        if st.button("🚪  Logout", use_container_width=True, key="nav_logout"):
            selected = "Logout"

        st.markdown(
            """
            <div style="
                text-align:center;
                margin-top:1rem;
                font-size:0.65rem;
                color:#555;
            ">IronPulse v1.0 · Stage 1</div>
            """,
            unsafe_allow_html=True,
        )

    return selected or current_page
