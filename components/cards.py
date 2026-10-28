"""
Shared card components for IronPulse UI.
"""

import streamlit as st


def metric_card(title: str, value: str, subtitle: str = "", icon: str = "📊", color: str = "#FF6B35"):
    """Renders a styled metric card."""
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, rgba(30,30,30,0.9), rgba(20,20,20,0.9));
            border: 1px solid rgba(255,255,255,0.08);
            border-left: 3px solid {color};
            border-radius: 12px;
            padding: 1.2rem 1.4rem;
            margin-bottom: 0.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        ">
            <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem;">
                <span style="font-size:1.2rem;">{icon}</span>
                <span style="font-size:0.75rem;color:#888;text-transform:uppercase;letter-spacing:1px;">{title}</span>
            </div>
            <div style="font-size:1.8rem;font-weight:700;color:#fff;line-height:1;">{value}</div>
            {f'<div style="font-size:0.75rem;color:#666;margin-top:0.3rem;">{subtitle}</div>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_banner(message: str, type: str = "info"):
    """Renders a styled info/warning/success banner."""
    colors = {
        "info":    ("#1a3a5c", "#2d7dd2", "ℹ️"),
        "success": ("#1a3d2b", "#2d9e5f", "✅"),
        "warning": ("#3d2d1a", "#e8a020", "⚠️"),
        "error":   ("#3d1a1a", "#e83020", "❌"),
    }
    bg, border, icon = colors.get(type, colors["info"])
    st.markdown(
        f"""
        <div style="
            background:{bg};
            border:1px solid {border};
            border-radius:8px;
            padding:0.8rem 1rem;
            margin:0.5rem 0;
            display:flex;
            align-items:flex-start;
            gap:0.5rem;
        ">
            <span>{icon}</span>
            <span style="font-size:0.88rem;color:#ddd;">{message}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = ""):
    """Renders a section title with optional subtitle."""
    st.markdown(
        f"""
        <div style="margin: 1.5rem 0 1rem;">
            <h2 style="
                margin:0;
                font-size:1.4rem;
                font-weight:700;
                color:#fff;
            ">{title}</h2>
            {f'<p style="margin:0.2rem 0 0;font-size:0.85rem;color:#888;">{subtitle}</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(icon: str, title: str, body: str):
    """Renders a styled empty-state message."""
    st.markdown(
        f"""
        <div style="
            text-align:center;
            padding: 3rem 2rem;
            background:rgba(255,255,255,0.03);
            border:1px dashed rgba(255,255,255,0.1);
            border-radius:12px;
            margin:1rem 0;
        ">
            <div style="font-size:3rem;margin-bottom:1rem;">{icon}</div>
            <h3 style="margin:0;color:#ccc;font-size:1.1rem;">{title}</h3>
            <p style="margin:0.5rem 0 0;color:#666;font-size:0.85rem;">{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def progress_bar(label: str, current: int, maximum: int, color: str = "#FF6B35"):
    """Renders a labeled progress bar."""
    pct = min(100, int((current / maximum) * 100)) if maximum > 0 else 0
    st.markdown(
        f"""
        <div style="margin:0.4rem 0;">
            <div style="
                display:flex;
                justify-content:space-between;
                font-size:0.8rem;
                color:#aaa;
                margin-bottom:0.3rem;
            ">
                <span>{label}</span>
                <span>{current:,} / {maximum:,}</span>
            </div>
            <div style="
                background:rgba(255,255,255,0.08);
                border-radius:999px;
                height:8px;
                overflow:hidden;
            ">
                <div style="
                    background:linear-gradient(90deg, {color}, {color}cc);
                    width:{pct}%;
                    height:100%;
                    border-radius:999px;
                    transition:width 0.3s ease;
                "></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
