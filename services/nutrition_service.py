"""Food logging and estimated daily nutrition summaries."""

from datetime import date
from math import isfinite

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from models.nutrition import Food, FoodLog
from models.profile import UserProfile
from models.user import User
from services.gamification_service import (
    GamificationError,
    award_xp,
    get_local_date,
    unlock_eligible_achievements,
)


class NutritionError(ValueError):
    """Raised for invalid nutrition input or unauthorized food-log access."""


VALID_MEALS = {"breakfast", "lunch", "dinner", "snack"}


def _require_owner(db: Session, user_id: int) -> User:
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise NutritionError("A valid user ID is required.")
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if user is None:
        raise NutritionError("User not found or inactive.")
    return user


def _validate_request_key(request_key: str | None) -> str | None:
    if request_key is None:
        return None
    if not isinstance(request_key, str) or not request_key.strip() or len(request_key) > 100:
        raise NutritionError("Request key must contain 1–100 characters.")
    return request_key.strip()


def get_nutrition_targets(db: Session, user_id: int) -> dict[str, int | str]:
    """Return transparent, approximate daily targets based on profile weight and goal."""
    _require_owner(db, user_id)
    profile = db.query(UserProfile).filter_by(user_id=user_id).first()
    if profile is None or not profile.weight_kg:
        raise NutritionError("Add your weight to your profile to view estimated targets.")
    calorie_factor = {
        "fat_loss": 25,
        "muscle_gain": 35,
        "endurance": 32,
        "maintenance": 30,
        "general_fitness": 30,
    }.get(profile.fitness_goal, 30)
    calories = round(profile.weight_kg * calorie_factor)
    protein = round(profile.weight_kg * (1.6 if profile.fitness_goal == "muscle_gain" else 1.2))
    fat = round(profile.weight_kg * 0.8)
    carbs = max(0, round((calories - protein * 4 - fat * 9) / 4))
    return {
        "calories": calories,
        "protein_g": protein,
        "carbs_g": carbs,
        "fat_g": fat,
        "disclaimer": "Approximate estimates for general tracking, not medical or dietetic advice.",
    }


def log_food(
    db: Session,
    user_id: int,
    food_id: int,
    servings: float = 1.0,
    meal_type: str = "snack",
    log_date: date | None = None,
    request_key: str | None = None,
) -> FoodLog:
    """Record a food entry for the owner, idempotent when a request key is supplied."""
    _require_owner(db, user_id)
    request_key = _validate_request_key(request_key)
    if isinstance(servings, bool) or not isinstance(servings, (int, float)):
        raise NutritionError("Servings must be a positive number.")
    if not isfinite(servings) or not 0 < servings <= 30:
        raise NutritionError("Servings must be greater than 0 and no greater than 30.")
    if not isinstance(meal_type, str) or meal_type not in VALID_MEALS:
        raise NutritionError(f"Meal type must be one of: {', '.join(sorted(VALID_MEALS))}.")
    if not isinstance(food_id, int) or isinstance(food_id, bool) or food_id <= 0:
        raise NutritionError("Food ID must be a positive integer.")
    try:
        local_today = get_local_date(db, user_id)
    except GamificationError as exc:
        raise NutritionError(str(exc)) from exc
    log_date = log_date or local_today
    if type(log_date) is not date or log_date > local_today:
        raise NutritionError("Food entries must use a valid date no later than today.")

    food = db.query(Food).filter_by(id=food_id).first()
    if food is None:
        raise NutritionError("Food was not found.")
    servings = float(servings)
    if request_key:
        existing = db.query(FoodLog).filter_by(user_id=user_id, request_key=request_key).first()
        if existing:
            if (
                existing.food_id != food_id
                or existing.servings != servings
                or existing.meal_type != meal_type
                or existing.log_date != log_date
            ):
                raise NutritionError("This request key was already used for a different food entry.")
            return existing

    log = FoodLog(
        user_id=user_id,
        food_id=food_id,
        request_key=request_key,
        log_date=log_date,
        meal_type=meal_type,
        servings=servings,
        calories_logged=round(food.calories * servings, 2),
        protein_g_logged=round(food.protein_g * servings, 2),
        carbs_g_logged=round(food.carbs_g * servings, 2),
        fat_g_logged=round(food.fat_g * servings, 2),
    )
    try:
        with db.begin_nested():
            db.add(log)
            db.flush()
    except IntegrityError as exc:
        if request_key:
            existing = db.query(FoodLog).filter_by(user_id=user_id, request_key=request_key).first()
            if existing is not None:
                if (
                    existing.food_id == food_id
                    and existing.servings == servings
                    and existing.meal_type == meal_type
                    and existing.log_date == log_date
                ):
                    return existing
                raise NutritionError("This request key was already used for a different food entry.") from exc
        raise

    award_xp(db, user_id, 5, "bonus", f"food_log:{log.id}", "Food entry logged")
    unlock_eligible_achievements(db, user_id)
    return log


def delete_food_log(db: Session, user_id: int, food_log_id: int) -> bool:
    """Delete a food entry only when it belongs to the requesting user."""
    _require_owner(db, user_id)
    log = db.query(FoodLog).filter_by(id=food_log_id, user_id=user_id).first()
    if log is None:
        return False
    db.delete(log)
    db.flush()
    return True


def get_daily_nutrition(
    db: Session, user_id: int, log_date: date | None = None
) -> dict:
    """Return the user's actual food records and aggregate totals for a local date."""
    _require_owner(db, user_id)
    try:
        local_today = get_local_date(db, user_id)
    except GamificationError as exc:
        raise NutritionError(str(exc)) from exc
    log_date = log_date or local_today
    if type(log_date) is not date or log_date > local_today:
        raise NutritionError("Nutrition summaries must use a date no later than today.")
    entries = (
        db.query(FoodLog)
        .options(joinedload(FoodLog.food))
        .filter_by(user_id=user_id, log_date=log_date)
        .order_by(FoodLog.created_at)
        .all()
    )
    return {
        "date": log_date,
        "entries": entries,
        "calories": round(sum(item.calories_logged for item in entries), 2),
        "protein_g": round(sum(item.protein_g_logged for item in entries), 2),
        "carbs_g": round(sum(item.carbs_g_logged for item in entries), 2),
        "fat_g": round(sum(item.fat_g_logged for item in entries), 2),
    }


def list_food_logs(db: Session, user_id: int, limit: int = 100) -> list[FoodLog]:
    """List only the requesting user's recent food entries."""
    _require_owner(db, user_id)
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 500:
        raise NutritionError("History limit must be between 1 and 500.")
    return (
        db.query(FoodLog)
        .options(joinedload(FoodLog.food))
        .filter_by(user_id=user_id)
        .order_by(FoodLog.log_date.desc(), FoodLog.created_at.desc())
        .limit(limit)
        .all()
    )
