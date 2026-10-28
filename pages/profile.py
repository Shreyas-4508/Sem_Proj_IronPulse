"""
Profile page — onboarding wizard and profile editor.
Validates and persists all changes to PostgreSQL/SQLite via profile_service.
"""

import streamlit as st
from components.cards import section_header, info_banner
from services.profile_service import (
    get_profile,
    update_profile,
    complete_onboarding,
    ProfileError,
    VALID_FITNESS_GOALS,
    VALID_EXPERIENCE_LEVELS,
    VALID_INTENSITIES,
    VALID_DIETARY_PREFERENCES,
)
from database.connection import get_db_session

# Equipment options available for home workouts
EQUIPMENT_OPTIONS = [
    "No equipment (bodyweight only)",
    "Dumbbells",
    "Resistance bands",
    "Pull-up bar",
    "Kettlebell",
    "Jump rope",
    "Yoga mat",
    "Stability ball",
    "Foam roller",
    "Bench or chair",
]

ALLERGY_OPTIONS = [
    "Gluten", "Dairy", "Nuts", "Shellfish", "Eggs", "Soy", "Fish",
]

TIMEZONE_OPTIONS = [
    "UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
    "Europe/London", "Europe/Paris", "Europe/Berlin", "Asia/Kolkata",
    "Asia/Shanghai", "Asia/Tokyo", "Australia/Sydney",
]

GOAL_LABELS = {
    "fat_loss": "Fat Loss",
    "muscle_gain": "Muscle Gain",
    "general_fitness": "General Fitness",
    "endurance": "Endurance",
    "maintenance": "Maintenance",
}

LEVEL_LABELS = {
    "beginner": "Beginner",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
}

INTENSITY_LABELS = {
    "low": "Low",
    "moderate": "Moderate",
    "high": "High",
}

DIET_LABELS = {
    "omnivore": "Omnivore",
    "vegetarian": "Vegetarian",
    "vegan": "Vegan",
    "keto": "Keto",
    "paleo": "Paleo",
    "none": "No preference",
}


def _safe_index(options: list, value, default: int = 0) -> int:
    """Returns the index of value in options, or default if not found."""
    try:
        return options.index(value)
    except ValueError:
        return default


def render():
    """Renders the profile setup and editing page."""
    user_id = st.session_state.get("user_id")

    with get_db_session() as db:
        profile = get_profile(db, user_id)

    is_onboarding = profile is None or not profile.onboarding_complete

    if is_onboarding:
        _render_onboarding_wizard(user_id, profile)
    else:
        _render_profile_editor(user_id, profile)


def _render_onboarding_wizard(user_id: int, profile):
    """Shows first-time onboarding wizard."""
    st.markdown(
        """
        <div style="text-align:center;padding:1.5rem 0;">
            <span style="font-size:3rem;">🏋️</span>
            <h1 style="margin:0.5rem 0;font-size:1.8rem;color:#fff;">Welcome to IronPulse!</h1>
            <p style="color:#888;font-size:0.95rem;">
                Let's set up your profile to personalize your fitness experience.
                This takes about 2 minutes.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("onboarding_form"):
        section_header("👤 Personal Information")
        col1, col2 = st.columns(2)
        with col1:
            display_name = st.text_input(
                "Display Name *",
                value=profile.display_name if profile else st.session_state.get("username", ""),
                placeholder="How should we call you?",
                help="This name will appear throughout the app.",
            )
            age = st.number_input(
                "Age *",
                min_value=13,
                max_value=120,
                value=profile.age if (profile and profile.age) else 25,
                step=1,
            )

        with col2:
            preferred_unit = st.selectbox(
                "Measurement Unit *",
                options=["metric", "imperial"],
                format_func=lambda x: "Metric (kg / cm)" if x == "metric" else "Imperial (lbs / ft)",
                index=0 if (not profile or profile.preferred_unit == "metric") else 1,
            )
            timezone = st.selectbox(
                "Timezone *",
                options=TIMEZONE_OPTIONS,
                index=_safe_index(TIMEZONE_OPTIONS, profile.timezone if profile else "UTC"),
            )

        col3, col4 = st.columns(2)
        with col3:
            if preferred_unit == "metric":
                height_input = st.number_input(
                    "Height (cm) *",
                    min_value=50.0,
                    max_value=300.0,
                    value=float(profile.height_cm) if (profile and profile.height_cm) else 170.0,
                    step=0.5,
                )
                height_cm = height_input
            else:
                height_ft = st.number_input("Height (feet)", min_value=3, max_value=8, value=5)
                height_in = st.number_input("Height (inches)", min_value=0, max_value=11, value=9)
                height_cm = (height_ft * 12 + height_in) * 2.54

        with col4:
            if preferred_unit == "metric":
                weight_input = st.number_input(
                    "Weight (kg) *",
                    min_value=20.0,
                    max_value=500.0,
                    value=float(profile.weight_kg) if (profile and profile.weight_kg) else 70.0,
                    step=0.5,
                )
                weight_kg = weight_input
            else:
                weight_lbs = st.number_input(
                    "Weight (lbs) *",
                    min_value=44.0,
                    max_value=1100.0,
                    value=float(profile.weight_kg * 2.20462) if (profile and profile.weight_kg) else 154.0,
                    step=0.5,
                )
                weight_kg = weight_lbs / 2.20462

        section_header("🎯 Fitness Goals")
        col5, col6 = st.columns(2)
        with col5:
            fitness_goal = st.selectbox(
                "Primary Goal *",
                options=list(GOAL_LABELS.keys()),
                format_func=lambda x: GOAL_LABELS[x],
                index=_safe_index(list(GOAL_LABELS.keys()), profile.fitness_goal if profile else "general_fitness"),
            )
            experience_level = st.selectbox(
                "Experience Level *",
                options=list(LEVEL_LABELS.keys()),
                format_func=lambda x: LEVEL_LABELS[x],
                index=_safe_index(list(LEVEL_LABELS.keys()), profile.experience_level if profile else "beginner"),
            )

        with col6:
            workout_duration = st.selectbox(
                "Preferred Workout Duration *",
                options=[20, 30, 45, 60, 90],
                format_func=lambda x: f"{x} minutes",
                index=_safe_index(
                    [20, 30, 45, 60, 90],
                    profile.preferred_workout_duration_minutes if profile else 30,
                ),
            )
            workout_intensity = st.selectbox(
                "Workout Intensity *",
                options=list(INTENSITY_LABELS.keys()),
                format_func=lambda x: INTENSITY_LABELS[x],
                index=_safe_index(list(INTENSITY_LABELS.keys()), profile.workout_intensity if profile else "moderate"),
            )

        section_header("🏠 Home Equipment")
        existing_equipment = profile.equipment_list if profile else []
        selected_equipment = st.multiselect(
            "What equipment do you have at home?",
            options=EQUIPMENT_OPTIONS,
            default=existing_equipment if existing_equipment else ["No equipment (bodyweight only)"],
            help="Select all that apply. We'll tailor your workouts to what you have.",
        )

        section_header("🥗 Nutrition Preferences")
        col7, col8 = st.columns(2)
        with col7:
            dietary_preference = st.selectbox(
                "Dietary Preference",
                options=list(DIET_LABELS.keys()),
                format_func=lambda x: DIET_LABELS[x],
                index=_safe_index(list(DIET_LABELS.keys()), profile.dietary_preference if profile else "none"),
            )
        with col8:
            selected_allergies = st.multiselect(
                "Food Allergies / Intolerances",
                options=ALLERGY_OPTIONS,
                default=profile.allergies_list if profile else [],
            )

        food_restrictions = st.text_area(
            "Additional Dietary Restrictions",
            value=profile.food_restrictions if profile else "",
            placeholder="e.g. No pork, low-sodium diet, etc.",
            height=80,
        )

        st.divider()
        submitted = st.form_submit_button(
            "🚀 Complete Profile Setup",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not display_name or len(display_name.strip()) < 2:
            info_banner("Please enter a display name (at least 2 characters).", type="error")
            return

        try:
            with get_db_session() as db:
                complete_onboarding(
                    db=db,
                    user_id=user_id,
                    display_name=display_name.strip(),
                    age=int(age),
                    height_cm=float(height_cm),
                    weight_kg=float(weight_kg),
                    fitness_goal=fitness_goal,
                    experience_level=experience_level,
                    preferred_workout_duration_minutes=workout_duration,
                    workout_intensity=workout_intensity,
                    available_equipment=selected_equipment,
                    dietary_preference=dietary_preference,
                    food_allergies=selected_allergies,
                    food_restrictions=food_restrictions.strip(),
                    timezone=timezone,
                    preferred_unit=preferred_unit,
                )
            # Update session state
            st.session_state["display_name"] = display_name.strip()
            info_banner("Profile saved successfully! Redirecting to dashboard…", type="success")
            st.session_state["current_page"] = "Dashboard"
            st.rerun()
        except ProfileError as e:
            info_banner(str(e), type="error")
        except Exception as e:
            info_banner(f"An error occurred: {e}", type="error")


def _render_profile_editor(user_id: int, profile):
    """Shows the profile editor for users who have completed onboarding."""
    section_header("👤 Edit Profile", "Update your information and preferences below.")

    tabs = st.tabs(["Personal Info", "Fitness Settings", "Nutrition", "Account"])

    # ─── Personal Info ───────────────────────────────────────────────────────
    with tabs[0]:
        with st.form("personal_form"):
            col1, col2 = st.columns(2)
            with col1:
                display_name = st.text_input("Display Name", value=profile.display_name or "")
                age = st.number_input("Age", min_value=13, max_value=120,
                                      value=profile.age or 25, step=1)

            with col2:
                preferred_unit = st.selectbox(
                    "Measurement Unit",
                    options=["metric", "imperial"],
                    format_func=lambda x: "Metric (kg / cm)" if x == "metric" else "Imperial (lbs / ft)",
                    index=0 if profile.preferred_unit == "metric" else 1,
                )
                timezone = st.selectbox(
                    "Timezone",
                    options=TIMEZONE_OPTIONS,
                    index=_safe_index(TIMEZONE_OPTIONS, profile.timezone),
                )

            col3, col4 = st.columns(2)
            with col3:
                if preferred_unit == "metric":
                    height_cm = st.number_input("Height (cm)", min_value=50.0, max_value=300.0,
                                                value=float(profile.height_cm or 170), step=0.5)
                else:
                    cur_h_in = (profile.height_cm or 170) / 2.54
                    h_ft = st.number_input("Height (feet)", min_value=3, max_value=8,
                                           value=int(cur_h_in // 12))
                    h_in = st.number_input("Height (inches)", min_value=0, max_value=11,
                                           value=int(cur_h_in % 12))
                    height_cm = (h_ft * 12 + h_in) * 2.54
            with col4:
                if preferred_unit == "metric":
                    weight_kg = st.number_input("Weight (kg)", min_value=20.0, max_value=500.0,
                                                value=float(profile.weight_kg or 70), step=0.5)
                else:
                    cur_w_lbs = (profile.weight_kg or 70) * 2.20462
                    w_lbs = st.number_input("Weight (lbs)", min_value=44.0, max_value=1100.0,
                                            value=float(cur_w_lbs), step=0.5)
                    weight_kg = w_lbs / 2.20462

            if st.form_submit_button("💾 Save Personal Info", type="primary"):
                _save_profile_fields(
                    user_id,
                    display_name=display_name.strip(),
                    age=int(age),
                    height_cm=float(height_cm),
                    weight_kg=float(weight_kg),
                    preferred_unit=preferred_unit,
                    timezone=timezone,
                )

    # ─── Fitness Settings ────────────────────────────────────────────────────
    with tabs[1]:
        with st.form("fitness_form"):
            col1, col2 = st.columns(2)
            with col1:
                fitness_goal = st.selectbox(
                    "Primary Goal",
                    options=list(GOAL_LABELS.keys()),
                    format_func=lambda x: GOAL_LABELS[x],
                    index=_safe_index(list(GOAL_LABELS.keys()), profile.fitness_goal),
                )
                experience_level = st.selectbox(
                    "Experience Level",
                    options=list(LEVEL_LABELS.keys()),
                    format_func=lambda x: LEVEL_LABELS[x],
                    index=_safe_index(list(LEVEL_LABELS.keys()), profile.experience_level),
                )
            with col2:
                workout_duration = st.selectbox(
                    "Preferred Duration",
                    options=[20, 30, 45, 60, 90],
                    format_func=lambda x: f"{x} minutes",
                    index=_safe_index([20, 30, 45, 60, 90], profile.preferred_workout_duration_minutes),
                )
                workout_intensity = st.selectbox(
                    "Workout Intensity",
                    options=list(INTENSITY_LABELS.keys()),
                    format_func=lambda x: INTENSITY_LABELS[x],
                    index=_safe_index(list(INTENSITY_LABELS.keys()), profile.workout_intensity),
                )

            selected_equipment = st.multiselect(
                "Available Equipment",
                options=EQUIPMENT_OPTIONS,
                default=profile.equipment_list,
            )

            if st.form_submit_button("💾 Save Fitness Settings", type="primary"):
                _save_profile_fields(
                    user_id,
                    fitness_goal=fitness_goal,
                    experience_level=experience_level,
                    preferred_workout_duration_minutes=workout_duration,
                    workout_intensity=workout_intensity,
                    available_equipment=",".join(selected_equipment),
                )

    # ─── Nutrition ───────────────────────────────────────────────────────────
    with tabs[2]:
        with st.form("nutrition_form"):
            col1, col2 = st.columns(2)
            with col1:
                dietary_preference = st.selectbox(
                    "Dietary Preference",
                    options=list(DIET_LABELS.keys()),
                    format_func=lambda x: DIET_LABELS[x],
                    index=_safe_index(list(DIET_LABELS.keys()), profile.dietary_preference or "none"),
                )
            with col2:
                selected_allergies = st.multiselect(
                    "Food Allergies",
                    options=ALLERGY_OPTIONS,
                    default=profile.allergies_list,
                )

            food_restrictions = st.text_area(
                "Additional Restrictions",
                value=profile.food_restrictions or "",
                height=100,
            )

            if st.form_submit_button("💾 Save Nutrition Preferences", type="primary"):
                _save_profile_fields(
                    user_id,
                    dietary_preference=dietary_preference,
                    food_allergies=",".join(selected_allergies),
                    food_restrictions=food_restrictions.strip(),
                )

    # ─── Account ─────────────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown("#### Account Information")
        st.info(f"**Username:** {st.session_state.get('username', '')}")
        st.divider()
        section_header("🔐 Change Password")
        with st.form("password_form"):
            current_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")

            if st.form_submit_button("🔑 Change Password", type="primary"):
                from services.auth_service import change_password, AuthError
                try:
                    with get_db_session() as db:
                        change_password(db, user_id, current_pw, new_pw, confirm_pw)
                    st.success("Password changed successfully!")
                except AuthError as e:
                    info_banner(str(e), type="error")


def _save_profile_fields(user_id: int, **kwargs):
    """Helper to save profile fields and show a success/error message."""
    try:
        with get_db_session() as db:
            profile = update_profile(
                db=db,
                requesting_user_id=user_id,
                target_user_id=user_id,
                **kwargs,
            )
        if "display_name" in kwargs:
            st.session_state["display_name"] = kwargs["display_name"]
        st.success("✅ Saved successfully!")
        st.rerun()
    except ProfileError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
