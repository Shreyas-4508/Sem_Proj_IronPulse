"""
Profile service — reads and updates UserProfile data.
Enforces validation and authorization: users may only modify their own profile.
"""

import logging
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from models.profile import UserProfile
from models.user import User

logger = logging.getLogger(__name__)

# --- Allowed option values ---
VALID_FITNESS_GOALS = {
    "fat_loss", "muscle_gain", "general_fitness", "endurance", "maintenance"
}
VALID_EXPERIENCE_LEVELS = {"beginner", "intermediate", "advanced"}
VALID_INTENSITIES = {"low", "moderate", "high"}
VALID_DIETARY_PREFERENCES = {"omnivore", "vegetarian", "vegan", "keto", "paleo", "none"}
VALID_UNITS = {"metric", "imperial"}
VALID_DURATIONS = {20, 30, 45, 60, 90}


class ProfileError(Exception):
    """Raised for profile validation or authorization failures."""
    pass


def get_profile(db: Session, user_id: int) -> Optional[UserProfile]:
    """Returns the profile for the given user_id, or None if not found."""
    return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()


def get_or_create_profile(db: Session, user_id: int) -> UserProfile:
    """
    Returns the profile for user_id.
    Creates an empty one if it doesn't exist.
    """
    profile = get_profile(db, user_id)
    if profile is None:
        profile = UserProfile(user_id=user_id, onboarding_complete=False)
        db.add(profile)
        db.flush()
    return profile


def update_profile(
    db: Session,
    requesting_user_id: int,
    target_user_id: int,
    **kwargs,
) -> UserProfile:
    """
    Updates a user profile.
    requesting_user_id must equal target_user_id (no cross-user edits).
    Validates all supplied fields before applying changes.
    Raises ProfileError on authorization or validation failure.
    """
    if requesting_user_id != target_user_id:
        raise ProfileError("You are not authorized to modify another user's profile.")

    profile = get_or_create_profile(db, target_user_id)
    _validate_profile_data(kwargs)

    allowed_fields = {
        "display_name", "date_of_birth", "age",
        "height_cm", "weight_kg", "preferred_unit",
        "fitness_goal", "experience_level",
        "preferred_workout_duration_minutes", "workout_intensity",
        "available_equipment", "dietary_preference",
        "food_allergies", "food_restrictions",
        "timezone", "onboarding_complete",
    }

    for field, value in kwargs.items():
        if field not in allowed_fields:
            raise ProfileError(f"Unknown profile field: {field!r}")
        setattr(profile, field, value)

    # Mark onboarding complete if all critical fields are present
    if _has_minimum_profile_data(profile):
        profile.onboarding_complete = True

    db.flush()
    logger.info("Profile updated for user_id=%s", target_user_id)
    return profile


def _validate_profile_data(data: dict) -> None:
    """Validates profile field values. Raises ProfileError on invalid input."""

    if "age" in data and data["age"] is not None:
        age = data["age"]
        if not isinstance(age, int) or age < 13 or age > 120:
            raise ProfileError("Age must be between 13 and 120.")

    if "height_cm" in data and data["height_cm"] is not None:
        h = data["height_cm"]
        if not (50 < h < 300):
            raise ProfileError("Height must be between 50 cm and 300 cm.")

    if "weight_kg" in data and data["weight_kg"] is not None:
        w = data["weight_kg"]
        if not (20 < w < 500):
            raise ProfileError("Weight must be between 20 kg and 500 kg.")

    if "fitness_goal" in data and data["fitness_goal"] is not None:
        if data["fitness_goal"] not in VALID_FITNESS_GOALS:
            raise ProfileError(f"Invalid fitness goal. Choose from: {VALID_FITNESS_GOALS}")

    if "experience_level" in data and data["experience_level"] is not None:
        if data["experience_level"] not in VALID_EXPERIENCE_LEVELS:
            raise ProfileError(f"Invalid experience level. Choose from: {VALID_EXPERIENCE_LEVELS}")

    if "workout_intensity" in data and data["workout_intensity"] is not None:
        if data["workout_intensity"] not in VALID_INTENSITIES:
            raise ProfileError(f"Invalid intensity. Choose from: {VALID_INTENSITIES}")

    if "dietary_preference" in data and data["dietary_preference"] is not None:
        if data["dietary_preference"] not in VALID_DIETARY_PREFERENCES:
            raise ProfileError(f"Invalid dietary preference.")

    if "preferred_unit" in data and data["preferred_unit"] is not None:
        if data["preferred_unit"] not in VALID_UNITS:
            raise ProfileError("Unit must be 'metric' or 'imperial'.")

    if "preferred_workout_duration_minutes" in data and data["preferred_workout_duration_minutes"] is not None:
        d = data["preferred_workout_duration_minutes"]
        if d not in VALID_DURATIONS:
            raise ProfileError(f"Workout duration must be one of: {sorted(VALID_DURATIONS)} minutes.")

    if "display_name" in data and data["display_name"] is not None:
        dn = data["display_name"].strip()
        if len(dn) < 2 or len(dn) > 100:
            raise ProfileError("Display name must be 2–100 characters.")

    if "timezone" in data and data["timezone"] is not None:
        value = data["timezone"]
        if not isinstance(value, str) or not value.strip():
            raise ProfileError("Timezone must be a valid IANA timezone.")
        try:
            ZoneInfo(value.strip())
        except ZoneInfoNotFoundError as exc:
            raise ProfileError("Timezone must be a valid IANA timezone.") from exc


def _has_minimum_profile_data(profile: UserProfile) -> bool:
    """Returns True if the profile has enough data to consider onboarding complete."""
    return all([
        profile.fitness_goal,
        profile.experience_level,
        profile.preferred_workout_duration_minutes,
    ])


def complete_onboarding(
    db: Session,
    user_id: int,
    display_name: str,
    age: int,
    height_cm: float,
    weight_kg: float,
    fitness_goal: str,
    experience_level: str,
    preferred_workout_duration_minutes: int,
    workout_intensity: str,
    available_equipment: list[str],
    dietary_preference: str,
    food_allergies: list[str],
    food_restrictions: str,
    timezone: str,
    preferred_unit: str = "metric",
) -> UserProfile:
    """
    Saves all onboarding data in one call and marks onboarding complete.
    """
    equipment_str = ",".join(e.strip() for e in available_equipment if e.strip())
    allergies_str = ",".join(a.strip() for a in food_allergies if a.strip())

    return update_profile(
        db=db,
        requesting_user_id=user_id,
        target_user_id=user_id,
        display_name=display_name,
        age=age,
        height_cm=height_cm,
        weight_kg=weight_kg,
        fitness_goal=fitness_goal,
        experience_level=experience_level,
        preferred_workout_duration_minutes=preferred_workout_duration_minutes,
        workout_intensity=workout_intensity,
        available_equipment=equipment_str,
        dietary_preference=dietary_preference,
        food_allergies=allergies_str,
        food_restrictions=food_restrictions,
        timezone=timezone,
        preferred_unit=preferred_unit,
        onboarding_complete=True,
    )
