"""Workout planning, active workout logging, and workout history."""

import uuid

import streamlit as st
from sqlalchemy.orm import joinedload

from database.connection import get_db_session
from models.workout import WorkoutPlanItem, WorkoutSession
from services.catalog_service import search_exercises
from services.workout_service import (
    WorkoutError,
    add_exercise_log,
    complete_workout,
    generate_workout,
    list_workouts,
    start_workout,
)


def render() -> None:
    user_id = st.session_state.get("user_id")
    st.title("Workout Engine")
    st.caption("Plans use your fitness profile and available equipment. Listen to your body and stop if you feel pain.")

    active_session_id = st.session_state.get("active_workout_id")
    if active_session_id:
        _render_active_workout(user_id, active_session_id)
        return

    st.subheader("Personalized workout")
    duration_options = [20, 30, 45, 60, 90]
    duration = st.selectbox("Session length", duration_options, index=2, format_func=lambda minutes: f"{minutes} minutes")
    if st.button("Generate my workout", type="primary", key="generate_workout"):
        try:
            with get_db_session() as db:
                plan = generate_workout(db, user_id, duration)
                exercises = {
                    item.id: item
                    for item in search_exercises(db)
                    if item.id in {entry["exercise_id"] for entry in plan}
                }
            st.session_state["generated_workout"] = plan
            st.session_state["generated_exercise_names"] = {
                exercise_id: exercise.name for exercise_id, exercise in exercises.items()
            }
        except WorkoutError as exc:
            st.error(str(exc))

    plan = st.session_state.get("generated_workout", [])
    if plan:
        st.markdown("Review your plan before starting:")
        for item in plan:
            name = st.session_state["generated_exercise_names"].get(
                item["exercise_id"], "Exercise"
            )
            target = (
                f"{item['prescribed_sets']} sets × {item['prescribed_reps']} reps"
                if item["prescribed_reps"] is not None
                else f"{item['prescribed_duration_seconds']} seconds"
            )
            st.write(f"{item['exercise_order'] + 1}. **{name}** — {target}")
        if st.button("Start workout", type="primary", key="start_workout"):
            try:
                with get_db_session() as db:
                    session = start_workout(
                        db,
                        user_id,
                        plan,
                        workout_name="Personalized Workout",
                        request_key=st.session_state.setdefault(
                            "workout_start_request_key", str(uuid.uuid4())
                        ),
                    )
                st.session_state["active_workout_id"] = session.id
                st.session_state.pop("generated_workout", None)
                st.session_state.pop("generated_exercise_names", None)
                st.session_state.pop("workout_start_request_key", None)
                st.rerun()
            except WorkoutError as exc:
                st.error(str(exc))

    st.divider()
    _render_exercise_library()
    st.divider()
    st.subheader("Recent workouts")
    with get_db_session() as db:
        history = list_workouts(db, user_id, limit=20)
    if not history:
        st.info("Your completed workouts will appear here.")
    for session in history:
        when = session.completed_at or session.session_date
        st.write(
            f"**{session.workout_name or 'Workout'}** · {when:%Y-%m-%d} · "
            f"{session.total_duration_minutes or 0} min · {session.xp_awarded} XP · {session.status}"
        )


def _render_active_workout(user_id: int, session_id: int) -> None:
    with get_db_session() as db:
        session = (
            db.query(WorkoutSession)
            .options(
                joinedload(WorkoutSession.plan_items).joinedload(WorkoutPlanItem.exercise),
                joinedload(WorkoutSession.exercise_logs),
            )
            .filter_by(id=session_id, user_id=user_id)
            .first()
        )
        if session is None or session.status != "in_progress":
            st.session_state.pop("active_workout_id", None)
            st.info("There is no active workout.")
            return
        plan = [
            {
                "id": item.id,
                "exercise_id": item.exercise_id,
                "name": item.exercise.name,
                "type": item.exercise.exercise_type,
                "sets": item.prescribed_sets,
                "reps": item.prescribed_reps,
                "duration": item.prescribed_duration_seconds,
                "order": item.exercise_order,
                "logged": any(log.plan_item_id == item.id for log in session.exercise_logs),
            }
            for item in session.plan_items
        ]

    st.subheader(session.workout_name or "Active workout")
    st.caption("Log each exercise you performed; planned targets are not counted as completed work.")
    for item in plan:
        with st.container(border=True):
            st.markdown(f"**{item['order'] + 1}. {item['name']}**")
            if item["logged"]:
                st.success("Performance logged")
                continue
            st.caption(
                f"Plan: {item['sets'] or 1} sets × {item['reps']} reps"
                if item["reps"] is not None
                else f"Plan: {item['duration']} seconds"
            )
            with st.form(f"log_exercise_{item['id']}"):
                skipped = st.checkbox("Skip this exercise", key=f"skip_{item['id']}")
                if item["type"] == "timed":
                    duration = st.number_input(
                        "Duration (seconds)",
                        min_value=1,
                        max_value=86400,
                        value=max(1, item["duration"] or 30),
                        disabled=skipped,
                        key=f"duration_{item['id']}",
                    )
                    sets, reps = None, None
                else:
                    c1, c2 = st.columns(2)
                    with c1:
                        sets = st.number_input(
                            "Sets completed",
                            min_value=1,
                            max_value=100,
                            value=max(1, item["sets"] or 1),
                            disabled=skipped,
                            key=f"sets_{item['id']}",
                        )
                    with c2:
                        reps = st.number_input(
                            "Reps completed",
                            min_value=1,
                            max_value=1000,
                            value=max(1, item["reps"] or 1),
                            disabled=skipped,
                            key=f"reps_{item['id']}",
                        )
                    duration = None
                weight = st.number_input(
                    "Weight used (kg, optional)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=0.0,
                    step=0.5,
                    disabled=skipped,
                    key=f"weight_{item['id']}",
                )
                notes = st.text_input("Notes (optional)", max_chars=1000, key=f"notes_{item['id']}")
                submitted = st.form_submit_button("Save exercise log")
            if submitted:
                try:
                    with get_db_session() as db:
                        add_exercise_log(
                            db,
                            user_id,
                            session_id,
                            item["exercise_id"],
                            plan_item_id=item["id"],
                            request_key=f"plan-item:{item['id']}",
                            sets_completed=sets,
                            reps_completed=reps,
                            duration_seconds=duration,
                            weight_kg=weight or None,
                            was_skipped=skipped,
                            notes=notes,
                        )
                    st.rerun()
                except WorkoutError as exc:
                    st.error(str(exc))

    with st.form("complete_workout_form"):
        duration_minutes = st.number_input(
            "Total workout time (minutes)", min_value=1, max_value=360, value=30
        )
        complete = st.form_submit_button("Finish workout", type="primary")
    if complete:
        try:
            with get_db_session() as db:
                completed = complete_workout(
                    db, user_id, session_id, int(duration_minutes)
                )
            st.session_state.pop("active_workout_id", None)
            st.success(
                f"Workout saved! +{completed.xp_awarded} XP. "
                "Estimated calories are shown only when profile weight is available."
            )
            st.rerun()
        except WorkoutError as exc:
            st.error(str(exc))


def _render_exercise_library() -> None:
    st.subheader("Exercise library")
    query = st.text_input("Search exercises", key="exercise_search")
    category = st.selectbox(
        "Muscle group",
        ["All", "warmup", "chest", "back", "shoulders", "arms", "core", "legs", "glutes", "full_body", "cooldown"],
        format_func=lambda value: value.replace("_", " ").title(),
    )
    with get_db_session() as db:
        exercises = search_exercises(db, query, None if category == "All" else category)
        results = [
            {
                "name": item.name,
                "category": item.category.replace("_", " ").title(),
                "difficulty": item.difficulty.title(),
                "equipment": ", ".join(item.equipment_list) or "No equipment",
                "description": item.description or "",
                "instructions": item.instructions or "",
                "safety": item.safety_notes or "",
            }
            for item in exercises
        ]
    if not results:
        st.info("No exercises match your search.")
    for item in results:
        with st.expander(f"{item['name']} · {item['difficulty']}"):
            st.write(item["description"])
            st.caption(f"{item['category']} · Equipment: {item['equipment']}")
            st.write(item["instructions"])
            if item["safety"]:
                st.warning(item["safety"])
