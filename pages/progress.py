"""Actual workout, nutrition, and gamification history charts."""

import pandas as pd
import plotly.express as px
import streamlit as st

from database.connection import get_db_session
from services.gamification_service import get_game_stats, list_user_achievements
from services.progress_service import ProgressError, get_progress_data


def render() -> None:
    user_id = st.session_state.get("user_id")
    st.title("Progress")
    period = st.selectbox("History period", [7, 30, 90, 180, 365], index=1, format_func=lambda days: f"Last {days} days")
    try:
        with get_db_session() as db:
            data = get_progress_data(db, user_id, days=period)
            stats = get_game_stats(db, user_id)
            achievements = list_user_achievements(db, user_id)
            stats_view = {
                "level": stats.current_level,
                "xp": stats.total_xp,
                "hp": stats.current_hp,
                "max_hp": stats.max_hp,
                "streak": stats.current_streak,
                "best_streak": stats.best_streak,
            }
            achievement_view = [
                (achievement.name, achievement.description, achievement.icon, record.unlocked_at)
                for achievement, record in achievements
            ]
    except ProgressError as exc:
        st.error(str(exc))
        return

    cols = st.columns(4)
    cols[0].metric("Level", stats_view["level"])
    cols[1].metric("Total XP", stats_view["xp"])
    cols[2].metric("Game energy", f"{stats_view['hp']} / {stats_view['max_hp']}")
    cols[3].metric(
        "Current / best streak",
        f"{stats_view['streak']} / {stats_view['best_streak']} days",
    )

    frame = pd.DataFrame(data)
    frame["date"] = pd.to_datetime(frame["date"])
    if frame["workouts"].sum() == 0:
        st.info("Complete a workout to start building your progress charts.")
    else:
        workout_fig = px.bar(
            frame,
            x="date",
            y="workouts",
            title="Completed workouts per day",
            labels={"date": "Date", "workouts": "Completed workouts"},
            color_discrete_sequence=["#FF6B35"],
        )
        workout_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#dddddd",
            xaxis_gridcolor="rgba(255,255,255,0.08)",
            yaxis_gridcolor="rgba(255,255,255,0.08)",
        )
        st.plotly_chart(workout_fig, width="stretch")

    duration_frame = frame[frame["workout_minutes"] > 0]
    if not duration_frame.empty:
        duration_fig = px.line(
            duration_frame,
            x="date",
            y="workout_minutes",
            markers=True,
            title="Logged workout minutes",
            labels={"date": "Date", "workout_minutes": "Minutes"},
        )
        duration_fig.update_traces(line_color="#7C6AF7")
        duration_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#dddddd")
        st.plotly_chart(duration_fig, width="stretch")

    calorie_frame = frame[
        (frame["calories_consumed"] > 0) | (frame["calories_burned"] > 0)
    ].melt(
        id_vars=["date"],
        value_vars=["calories_consumed", "calories_burned"],
        var_name="measure",
        value_name="calories",
    )
    if not calorie_frame.empty:
        calorie_frame["measure"] = calorie_frame["measure"].map(
            {"calories_consumed": "Logged intake", "calories_burned": "Estimated workout burn"}
        )
        calories_fig = px.line(
            calorie_frame,
            x="date",
            y="calories",
            color="measure",
            markers=True,
            title="Logged food calories and estimated workout calories",
            labels={"date": "Date", "calories": "kcal", "measure": "Metric"},
        )
        calories_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#dddddd")
        st.plotly_chart(calories_fig, width="stretch")

    st.subheader("Achievements")
    if not achievement_view:
        st.info("Achievements unlock as you log workouts and food.")
    for name, description, icon, unlocked_at in achievement_view:
        st.write(f"{icon} **{name}** — {description} · Unlocked {unlocked_at:%Y-%m-%d}")
