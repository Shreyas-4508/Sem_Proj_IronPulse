"""Nutrition summary and user-owned food logging."""

import uuid

import streamlit as st

from database.connection import get_db_session
from services.catalog_service import search_foods
from services.nutrition_service import (
    NutritionError,
    get_daily_nutrition,
    get_nutrition_targets,
    log_food,
)


def render() -> None:
    user_id = st.session_state.get("user_id")
    st.title("Nutrition")
    st.caption("Food values are estimates from the starter catalog. This tracker is not medical or dietetic advice.")

    try:
        with get_db_session() as db:
            summary = get_daily_nutrition(db, user_id)
            targets = get_nutrition_targets(db, user_id)
            foods = search_foods(db)
    except NutritionError as exc:
        st.info(str(exc))
        with get_db_session() as db:
            foods = search_foods(db)
        summary = {"entries": [], "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
        targets = None

    summary_date = summary.get("date")
    title = f"Today's intake · {summary_date:%A, %B %d}" if summary_date else "Today's intake"
    st.subheader(title)
    metric_cols = st.columns(4)
    for column, label, key in zip(
        metric_cols,
        ("Calories", "Protein", "Carbohydrates", "Fat"),
        ("calories", "protein_g", "carbs_g", "fat_g"),
    ):
        unit = "kcal" if key == "calories" else "g"
        value = summary[key]
        target = targets.get(key) if targets else None
        column.metric(label, f"{value:.0f} {unit}", f"of {target} {unit}" if target else None)
        if target:
            column.progress(min(value / target, 1.0))

    if targets:
        st.caption(targets["disclaimer"])

    st.subheader("Log food")
    search = st.text_input("Find a food", key="food_search")
    with get_db_session() as db:
        matching_foods = search_foods(db, search)
    if not matching_foods:
        st.info("No foods match. Try a different search term.")
    else:
        food_ids = [food.id for food in matching_foods]
        foods_by_id = {food.id: food for food in matching_foods}
        with st.form("food_log_form"):
            food_id = st.selectbox(
                "Food",
                food_ids,
                format_func=lambda value: (
                    f"{foods_by_id[value].name} · {foods_by_id[value].calories:.0f} kcal / "
                    f"{foods_by_id[value].serving_size:g} {foods_by_id[value].serving_unit}"
                ),
            )
            col1, col2 = st.columns(2)
            with col1:
                servings = st.number_input("Servings", min_value=0.1, max_value=30.0, value=1.0, step=0.1)
            with col2:
                meal = st.selectbox("Meal", ["breakfast", "lunch", "dinner", "snack"])
            submitted = st.form_submit_button("Add food", type="primary")
        if submitted:
            try:
                request_key = st.session_state.setdefault("food_log_request_key", str(uuid.uuid4()))
                with get_db_session() as db:
                    log_food(
                        db,
                        user_id,
                        food_id,
                        servings,
                        meal_type=meal,
                        request_key=request_key,
                    )
                st.session_state["food_log_request_key"] = str(uuid.uuid4())
                st.success("Food entry saved.")
                st.rerun()
            except NutritionError as exc:
                st.error(str(exc))

    st.subheader("Today's food log")
    if not summary["entries"]:
        st.info("No food has been logged today.")
    for entry in summary["entries"]:
        food_name = entry.food.name if entry.food else f"Food #{entry.food_id}"
        st.write(
            f"**{entry.meal_type.title()}** · {food_name} · {entry.servings:g} serving(s) · "
            f"{entry.calories_logged:.0f} kcal · P {entry.protein_g_logged:.1f}g / "
            f"C {entry.carbs_g_logged:.1f}g / F {entry.fat_g_logged:.1f}g"
        )
