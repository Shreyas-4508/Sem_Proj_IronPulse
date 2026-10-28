"""User-scoped daily progress aggregation for real workout and food data."""

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from models.nutrition import FoodLog
from models.profile import UserProfile
from models.user import User
from models.workout import WorkoutSession
from services.gamification_service import GamificationError, get_local_date


class ProgressError(ValueError):
    """Raised for invalid progress filters or unauthorized access."""


def get_progress_data(
    db: Session,
    user_id: int,
    days: int = 30,
    today: date | None = None,
) -> list[dict]:
    """Aggregate only the user's completed workouts and food entries by local date."""
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if user is None:
        raise ProgressError("User not found or inactive.")
    if not isinstance(days, int) or isinstance(days, bool) or not 7 <= days <= 365:
        raise ProgressError("Progress period must be between 7 and 365 days.")
    try:
        local_today = today or get_local_date(db, user_id)
    except GamificationError as exc:
        raise ProgressError(str(exc)) from exc
    if type(local_today) is not date:
        raise ProgressError("Progress date must be a calendar date.")
    first_day = local_today - timedelta(days=days - 1)

    profile = db.query(UserProfile).filter_by(user_id=user_id).first()
    try:
        local_tz = ZoneInfo(profile.timezone if profile else "UTC")
    except (ZoneInfoNotFoundError, TypeError) as exc:
        raise ProgressError("The profile timezone is not a valid IANA timezone.") from exc
    range_start = datetime.combine(first_day, time.min, tzinfo=local_tz).astimezone(timezone.utc)
    range_end = datetime.combine(local_today + timedelta(days=1), time.min, tzinfo=local_tz).astimezone(timezone.utc)

    workout_counts: dict[date, int] = defaultdict(int)
    workout_minutes: dict[date, int] = defaultdict(int)
    calories_burned: dict[date, float] = defaultdict(float)
    workouts = (
        db.query(WorkoutSession)
        .filter(
            WorkoutSession.user_id == user_id,
            WorkoutSession.status == "completed",
            WorkoutSession.completed_at >= range_start,
            WorkoutSession.completed_at < range_end,
        )
        .all()
    )
    for session in workouts:
        completed_at = session.completed_at
        if completed_at is None:
            continue
        if completed_at.tzinfo is None or completed_at.utcoffset() is None:
            completed_at = completed_at.replace(tzinfo=timezone.utc)
        day = completed_at.astimezone(local_tz).date()
        if first_day <= day <= local_today:
            workout_counts[day] += 1
            workout_minutes[day] += session.total_duration_minutes or 0
            calories_burned[day] += session.estimated_calories_burned or 0

    food_calories: dict[date, float] = defaultdict(float)
    food_logs = (
        db.query(FoodLog.log_date, FoodLog.calories_logged)
        .filter(
            FoodLog.user_id == user_id,
            FoodLog.log_date >= first_day,
            FoodLog.log_date <= local_today,
        )
        .all()
    )
    for day, calories in food_logs:
        food_calories[day] += calories

    return [
        {
            "date": first_day + timedelta(days=offset),
            "workouts": workout_counts[first_day + timedelta(days=offset)],
            "workout_minutes": workout_minutes[first_day + timedelta(days=offset)],
            "calories_burned": round(calories_burned[first_day + timedelta(days=offset)], 1),
            "calories_consumed": round(food_calories[first_day + timedelta(days=offset)], 1),
        }
        for offset in range(days)
    ]
