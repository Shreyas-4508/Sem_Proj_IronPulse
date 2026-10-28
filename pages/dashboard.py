"""Dashboard page with profile information and persisted Stage 2 progress."""

import pandas as pd
import plotly.express as px
import streamlit as st
from components.cards import metric_card, section_header, info_banner
from services.profile_service import get_profile
from database.connection import get_db_session
from services.gamification_service import get_game_stats
from services.progress_service import get_progress_data


def render():
    """Renders the IronPulse dashboard for the logged-in user."""
    user_id = st.session_state.get("user_id")
    username = st.session_state.get("username", "User")

    with get_db_session() as db:
        profile = get_profile(db, user_id)
        stats = get_game_stats(db, user_id)
        stats_view = (
            stats.current_level,
            stats.total_xp,
            stats.current_hp,
            stats.max_hp,
            stats.current_streak,
        )
        progress = get_progress_data(db, user_id, days=14)

    display_name = profile.display_name if profile and profile.display_name else username

    # ─── Welcome Header ──────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, rgba(255,107,53,0.15), rgba(255,140,66,0.05));
            border: 1px solid rgba(255,107,53,0.25);
            border-radius: 16px;
            padding: 1.8rem 2rem;
            margin-bottom: 1.5rem;
        ">
            <h1 style="margin:0;font-size:1.8rem;color:#fff;">
                Welcome back, <span style="color:#FF6B35;">{display_name}</span> 👋
            </h1>
            <p style="margin:0.4rem 0 0;color:#888;font-size:0.9rem;">
                Your IronPulse fitness journey starts here.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ─── Onboarding Banner ───────────────────────────────────────────────────
    if profile is None or not profile.onboarding_complete:
        info_banner(
            "Complete your profile to unlock personalized workouts, nutrition plans, and progress tracking.",
            type="warning",
        )
        if st.button("✏️ Complete Profile Setup", key="dash_complete_profile", type="primary"):
            st.session_state["current_page"] = "Profile"
            st.rerun()

    # ─── Profile Summary Cards ───────────────────────────────────────────────
    section_header("Your Profile Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        goal_display = {
            "fat_loss": "Fat Loss",
            "muscle_gain": "Muscle Gain",
            "general_fitness": "General Fitness",
            "endurance": "Endurance",
            "maintenance": "Maintenance",
        }
        goal = profile.fitness_goal if profile else None
        metric_card(
            "Fitness Goal",
            goal_display.get(goal, "Not set"),
            icon="🎯",
            color="#FF6B35",
        )

    with col2:
        level = profile.experience_level.capitalize() if profile and profile.experience_level else "Not set"
        metric_card("Experience Level", level, icon="⚡", color="#FF8C42")

    with col3:
        dur = f"{profile.preferred_workout_duration_minutes} min" if profile and profile.preferred_workout_duration_minutes else "Not set"
        metric_card("Workout Duration", dur, icon="⏱️", color="#FFA64D")

    with col4:
        intensity = profile.workout_intensity.capitalize() if profile and profile.workout_intensity else "Not set"
        metric_card("Intensity", intensity, icon="🔥", color="#FFB347")

    # ─── Body Metrics Row ────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        if profile and profile.weight_kg:
            unit = profile.preferred_unit or "metric"
            if unit == "imperial":
                val = f"{profile.weight_kg * 2.20462:.1f} lbs"
            else:
                val = f"{profile.weight_kg:.1f} kg"
        else:
            val = "Not set"
        metric_card("Weight", val, icon="⚖️", color="#7C6AF7")

    with col2:
        if profile and profile.height_cm:
            unit = profile.preferred_unit or "metric"
            if unit == "imperial":
                total_inches = profile.height_cm / 2.54
                feet = int(total_inches // 12)
                inches = int(total_inches % 12)
                val = f"{feet}'{inches}\""
            else:
                val = f"{profile.height_cm:.0f} cm"
        else:
            val = "Not set"
        metric_card("Height", val, icon="📏", color="#7C6AF7")

    with col3:
        age_val = f"{profile.age} years" if profile and profile.age else "Not set"
        metric_card("Age", age_val, icon="🎂", color="#7C6AF7")

    section_header("Your Progress", "XP and activity are loaded from your saved records")
    game_cols = st.columns(4)
    game_cols[0].metric("Level", stats_view[0])
    game_cols[1].metric("Total XP", stats_view[1])
    game_cols[2].metric("Game energy", f"{stats_view[2]} / {stats_view[3]}")
    game_cols[3].metric("Workout streak", f"{stats_view[4]} days")

    chart_data = pd.DataFrame(progress)
    chart_data["date"] = pd.to_datetime(chart_data["date"])
    chart = px.bar(
        chart_data,
        x="date",
        y="workouts",
        title="Completed workouts · last 14 days",
        labels={"date": "Date", "workouts": "Completed workouts"},
        color_discrete_sequence=["#FF6B35"],
    )
    chart.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#dddddd",
    )
    st.plotly_chart(chart, width="stretch")
    st.caption("Calories, XP, and activity reflect logged data; calorie values are estimates.")
