"""Exercise discovery, personalized plan generation, and workout logging."""

from datetime import datetime, timezone
from math import ceil, isfinite
import re

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from models.exercise import Exercise
from models.profile import UserProfile
from models.user import User
from models.workout import ExerciseLog, WorkoutPlanItem, WorkoutSession
from services.catalog_service import search_exercises
from services.gamification_service import (
    apply_workout_hp_cost,
    award_xp,
    record_workout_activity,
    unlock_eligible_achievements,
)


class WorkoutError(ValueError):
    """Raised for invalid workout input or unauthorized workout access."""


def _require_owner(db: Session, user_id: int) -> User:
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise WorkoutError("A valid user ID is required.")
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if user is None:
        raise WorkoutError("User not found or inactive.")
    return user


def _validate_request_key(request_key: str | None) -> str | None:
    if request_key is None:
        return None
    if not isinstance(request_key, str) or not request_key.strip() or len(request_key) > 100:
        raise WorkoutError("Request key must contain 1–100 characters.")
    return request_key.strip()


def generate_workout(
    db: Session, user_id: int, duration_minutes: int | None = None
) -> list[dict[str, int | None]]:
    """Build a reproducible plan from the user's profile, equipment, level, and goal."""
    user = _require_owner(db, user_id)
    profile = db.query(UserProfile).filter_by(user_id=user.id).first()
    if profile is None or not profile.onboarding_complete:
        raise WorkoutError("Complete your profile before generating a workout.")

    duration = (
        profile.preferred_workout_duration_minutes
        if duration_minutes is None
        else duration_minutes
    )
    if not isinstance(duration, int) or isinstance(duration, bool) or duration not in {
        20, 30, 45, 60, 90
    }:
        raise WorkoutError("Workout duration must be 20, 30, 45, 60, or 90 minutes.")

    level = profile.experience_level
    if level not in {"beginner", "intermediate", "advanced"}:
        raise WorkoutError("Set a valid experience level in your profile.")
    allowed_difficulty = {
        "beginner": {"beginner"},
        "intermediate": {"beginner", "intermediate"},
        "advanced": {"beginner", "intermediate", "advanced"},
    }[level]
    equipment = {_equipment_key(item) for item in profile.equipment_list}
    available = []
    for exercise in search_exercises(db):
        required = {_equipment_key(item) for item in exercise.equipment_list}
        if exercise.difficulty in allowed_difficulty and (not required or required <= equipment):
            available.append(exercise)

    if not available:
        raise WorkoutError("No exercises match your profile and available equipment.")

    goal_categories = {
        "muscle_gain": ["legs", "chest", "back", "glutes", "shoulders", "arms", "core"],
        "endurance": ["warmup", "full_body", "legs", "core", "glutes"],
        "fat_loss": ["warmup", "full_body", "legs", "chest", "back", "core"],
        "maintenance": ["legs", "chest", "back", "glutes", "core"],
        "general_fitness": ["legs", "chest", "back", "glutes", "core"],
    }
    categories = goal_categories.get(profile.fitness_goal, goal_categories["general_fitness"])
    target_count = max(3, min(8, ceil(duration / 7)))
    selected: list[Exercise] = []
    used_ids: set[int] = set()
    for category in categories:
        match = next(
            (item for item in available if item.category == category and item.id not in used_ids),
            None,
        )
        if match:
            selected.append(match)
            used_ids.add(match.id)
        if len(selected) >= target_count:
            break
    for exercise in available:
        if len(selected) >= target_count:
            break
        if exercise.id not in used_ids:
            selected.append(exercise)
            used_ids.add(exercise.id)

    return [
        {
            "exercise_id": item.id,
            "prescribed_sets": item.default_sets,
            "prescribed_reps": item.default_reps,
            "prescribed_duration_seconds": item.default_duration_seconds,
            "exercise_order": order,
        }
        for order, item in enumerate(selected)
    ]


def start_workout(
    db: Session,
    user_id: int,
    exercises: list[dict],
    workout_name: str = "Personalized Workout",
    workout_type: str = "generated",
    request_key: str | None = None,
    occurred_at: datetime | None = None,
) -> WorkoutSession:
    """Create an owned workout session and its planned exercise entries."""
    _require_owner(db, user_id)
    request_key = _validate_request_key(request_key)
    if not isinstance(workout_name, str) or not 1 <= len(workout_name.strip()) <= 200:
        raise WorkoutError("Workout name must contain 1–200 characters.")
    if not isinstance(workout_type, str) or workout_type not in {"generated", "custom"}:
        raise WorkoutError("Workout type must be 'generated' or 'custom'.")
    if not isinstance(exercises, list) or not 1 <= len(exercises) <= 20:
        raise WorkoutError("A workout must contain between 1 and 20 exercises.")
    occurred_at = occurred_at or datetime.now(timezone.utc)
    if not isinstance(occurred_at, datetime) or occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise WorkoutError("Workout start time must include a timezone.")
    if occurred_at > datetime.now(timezone.utc):
        raise WorkoutError("Workout start time cannot be in the future.")
    occurred_at = occurred_at.astimezone(timezone.utc)

    entries = []
    seen_orders = set()
    for index, item in enumerate(exercises):
        if not isinstance(item, dict):
            raise WorkoutError("Each exercise entry must be an object.")
        exercise_id = item.get("exercise_id")
        if not isinstance(exercise_id, int) or isinstance(exercise_id, bool) or exercise_id <= 0:
            raise WorkoutError("Exercise ID must be a positive integer.")
        exercise = db.query(Exercise).filter_by(id=exercise_id, is_active=True).first()
        if exercise is None:
            raise WorkoutError(f"Exercise {exercise_id!r} is unavailable.")
        order = item.get("exercise_order", index)
        if not isinstance(order, int) or isinstance(order, bool) or order < 0 or order in seen_orders:
            raise WorkoutError("Exercise order values must be unique non-negative integers.")
        seen_orders.add(order)
        entries.append((exercise, _validate_plan_item(item, exercise, order)))

    if request_key:
        existing = (
            db.query(WorkoutSession)
            .options(joinedload(WorkoutSession.plan_items))
            .filter_by(user_id=user_id, request_key=request_key)
            .first()
        )
        if existing:
            if _same_workout_request(existing, workout_name, workout_type, entries):
                return existing
            raise WorkoutError("This request key was already used for a different workout.")

    session = WorkoutSession(
        user_id=user_id,
        session_date=occurred_at,
        status="in_progress",
        workout_name=workout_name.strip(),
        workout_type=workout_type,
        request_key=request_key,
    )
    try:
        with db.begin_nested():
            db.add(session)
            db.flush()
            for exercise, values in entries:
                db.add(WorkoutPlanItem(session_id=session.id, exercise_id=exercise.id, **values))
            db.flush()
    except IntegrityError:
        if request_key:
            existing = (
                db.query(WorkoutSession)
                .options(joinedload(WorkoutSession.plan_items))
                .filter_by(user_id=user_id, request_key=request_key)
                .first()
            )
            if existing is not None:
                if _same_workout_request(existing, workout_name, workout_type, entries):
                    return existing
                raise WorkoutError("This request key was already used for a different workout.") from None
        raise
    return session


def add_exercise_log(
    db: Session,
    user_id: int,
    session_id: int,
    exercise_id: int,
    plan_item_id: int | None = None,
    request_key: str | None = None,
    **performance,
) -> ExerciseLog:
    """Append or idempotently retrieve one performance entry in an owned session."""
    _require_owner(db, user_id)
    request_key = _validate_request_key(request_key)
    session = (
        db.query(WorkoutSession)
        .filter_by(id=session_id, user_id=user_id)
        .first()
    )
    if session is None:
        raise WorkoutError("Workout session not found.")
    if session.status != "in_progress":
        raise WorkoutError("Exercises can only be added to an in-progress workout.")
    if not isinstance(exercise_id, int) or isinstance(exercise_id, bool) or exercise_id <= 0:
        raise WorkoutError("Exercise ID must be a positive integer.")
    if plan_item_id is not None and (
        not isinstance(plan_item_id, int) or isinstance(plan_item_id, bool) or plan_item_id <= 0
    ):
        raise WorkoutError("Planned exercise ID must be a positive integer.")
    plan_item = None
    if plan_item_id is not None:
        plan_item = (
            db.query(WorkoutPlanItem)
            .filter_by(id=plan_item_id, session_id=session_id, exercise_id=exercise_id)
            .first()
        )
        if plan_item is None:
            raise WorkoutError("Planned exercise not found in this workout.")
    exercise = db.query(Exercise).filter_by(id=exercise_id, is_active=True).first()
    if exercise is None:
        raise WorkoutError("Exercise not found or inactive.")
    values = _validate_performance(
        performance, exercise, plan_item.exercise_order if plan_item else len(session.exercise_logs)
    )
    if request_key:
        existing = (
            db.query(ExerciseLog)
            .filter_by(session_id=session_id, request_key=request_key)
            .first()
        )
        if existing:
            same_values = all(
                getattr(existing, key) == value
                for key, value in values.items()
            )
            if (
                existing.exercise_id == exercise_id
                and existing.plan_item_id == (plan_item.id if plan_item else None)
                and same_values
            ):
                return existing
            raise WorkoutError("This request key was already used for a different exercise log.")
    if plan_item and db.query(ExerciseLog).filter_by(plan_item_id=plan_item.id).first():
        raise WorkoutError("Performance for this planned exercise is already logged.")
    entry = ExerciseLog(
        session_id=session_id,
        exercise_id=exercise_id,
        request_key=request_key,
        plan_item_id=plan_item.id if plan_item else None,
        **values,
    )
    try:
        with db.begin_nested():
            db.add(entry)
            db.flush()
    except IntegrityError:
        if request_key:
            existing = (
                db.query(ExerciseLog)
                .filter_by(session_id=session_id, request_key=request_key)
                .first()
            )
            if existing is not None:
                return existing
        if plan_item_id is not None:
            raise WorkoutError("Performance for this planned exercise is already logged.") from None
        raise
    return entry


def _validate_performance(
    values: dict, exercise: Exercise, exercise_order: int
) -> dict:
    allowed = {
        "sets_completed",
        "reps_completed",
        "duration_seconds",
        "weight_kg",
        "was_skipped",
        "notes",
    }
    if values.keys() - allowed:
        raise WorkoutError("Performance entry contains unsupported fields.")
    sets = values.get("sets_completed")
    reps = values.get("reps_completed")
    duration = values.get("duration_seconds")
    weight = values.get("weight_kg")
    skipped = values.get("was_skipped", False)
    notes = values.get("notes")
    if not isinstance(skipped, bool):
        raise WorkoutError("Skipped status must be true or false.")
    if notes is not None and (not isinstance(notes, str) or len(notes) > 1000):
        raise WorkoutError("Exercise notes must be at most 1,000 characters.")
    if not isinstance(exercise_order, int) or isinstance(exercise_order, bool) or exercise_order < 0:
        raise WorkoutError("Exercise order must be a non-negative integer.")

    for label, value, upper in (
        ("Sets", sets, 100),
        ("Reps", reps, 1000),
        ("Duration", duration, 24 * 60 * 60),
    ):
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= upper
        ):
            raise WorkoutError(f"{label} must be a positive integer no greater than {upper}.")
    if weight is not None and (
        isinstance(weight, bool)
        or not isinstance(weight, (int, float))
        or not isfinite(weight)
        or not 0 <= weight <= 1000
    ):
        raise WorkoutError("Weight must be a finite value between 0 and 1,000 kg.")
    if not skipped:
        if exercise.exercise_type == "timed" and duration is None:
            duration = exercise.default_duration_seconds
        elif exercise.exercise_type in {"reps", "distance"}:
            reps = reps or exercise.default_reps
            sets = sets or exercise.default_sets
        if exercise.exercise_type == "timed" and duration is None:
            raise WorkoutError("Timed exercises require a duration.")
        if exercise.exercise_type == "reps" and reps is None:
            raise WorkoutError("Repetition exercises require a repetition count.")
        if sets is None and exercise.exercise_type != "distance":
            sets = 1
    return {
        "sets_completed": sets,
        "reps_completed": reps,
        "duration_seconds": duration,
        "weight_kg": float(weight) if weight is not None else None,
        "was_skipped": skipped,
        "notes": notes.strip() if notes else None,
        "exercise_order": exercise_order,
    }


def _validate_plan_item(values: dict, exercise: Exercise, exercise_order: int) -> dict:
    allowed = {
        "exercise_id",
        "prescribed_sets",
        "prescribed_reps",
        "prescribed_duration_seconds",
        "exercise_order",
    }
    if values.keys() - allowed:
        raise WorkoutError("Plan entry contains unsupported fields.")
    sets = values.get("prescribed_sets", exercise.default_sets)
    reps = values.get("prescribed_reps", exercise.default_reps)
    duration = values.get("prescribed_duration_seconds", exercise.default_duration_seconds)
    for label, value, upper in (
        ("Sets", sets, 100),
        ("Reps", reps, 1000),
        ("Duration", duration, 24 * 60 * 60),
    ):
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= upper
        ):
            raise WorkoutError(f"Prescribed {label.lower()} must be a positive integer no greater than {upper}.")
    if exercise.exercise_type == "timed" and duration is None:
        raise WorkoutError("Timed exercises require a prescribed duration.")
    if exercise.exercise_type == "reps" and reps is None:
        raise WorkoutError("Repetition exercises require a prescribed repetition count.")
    if not isinstance(exercise_order, int) or isinstance(exercise_order, bool) or exercise_order < 0:
        raise WorkoutError("Exercise order must be a non-negative integer.")
    return {
        "prescribed_sets": sets,
        "prescribed_reps": reps,
        "prescribed_duration_seconds": duration,
        "exercise_order": exercise_order,
    }


def _equipment_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def _same_workout_request(session, workout_name, workout_type, entries) -> bool:
    old_items = sorted(session.plan_items, key=lambda item: item.exercise_order)
    new_items = sorted(entries, key=lambda item: item[1]["exercise_order"])
    return (
        session.workout_name == workout_name.strip()
        and session.workout_type == workout_type
        and [
            (
                item.exercise_id,
                item.prescribed_sets,
                item.prescribed_reps,
                item.prescribed_duration_seconds,
                item.exercise_order,
            )
            for item in old_items
        ]
        == [
            (
                exercise.id,
                values["prescribed_sets"],
                values["prescribed_reps"],
                values["prescribed_duration_seconds"],
                values["exercise_order"],
            )
            for exercise, values in new_items
        ]
    )


def complete_workout(
    db: Session,
    user_id: int,
    session_id: int,
    duration_minutes: int,
    completed_at: datetime | None = None,
) -> WorkoutSession:
    """Complete an owned workout once, then award XP, HP and a local-day streak."""
    _require_owner(db, user_id)
    if not isinstance(duration_minutes, int) or isinstance(duration_minutes, bool) or not 1 <= duration_minutes <= 360:
        raise WorkoutError("Workout duration must be between 1 and 360 minutes.")
    completed_at = completed_at or datetime.now(timezone.utc)
    if not isinstance(completed_at, datetime) or completed_at.tzinfo is None or completed_at.utcoffset() is None:
        raise WorkoutError("Completion time must include a timezone.")
    completed_at = completed_at.astimezone(timezone.utc)
    session = (
        db.query(WorkoutSession)
        .options(joinedload(WorkoutSession.exercise_logs))
        .filter_by(id=session_id, user_id=user_id)
        .with_for_update()
        .populate_existing()
        .first()
    )
    if session is None:
        raise WorkoutError("Workout session not found.")
    if session.status == "completed":
        return session
    if session.status != "in_progress":
        raise WorkoutError("Only in-progress workouts can be completed.")
    session_started = session.session_date
    if session_started.tzinfo is None or session_started.utcoffset() is None:
        session_started = session_started.replace(tzinfo=timezone.utc)
    if completed_at < session_started or completed_at > datetime.now(timezone.utc):
        raise WorkoutError("Completion time must be between the workout start and now.")
    if not any(not entry.was_skipped for entry in session.exercise_logs):
        raise WorkoutError("Complete or log at least one exercise before finishing.")

    profile = db.query(UserProfile).filter_by(user_id=user_id).first()
    weight = profile.weight_kg if profile else None
    calories = None
    if weight:
        met_values = (
            db.query(Exercise.met_value)
            .join(ExerciseLog, ExerciseLog.exercise_id == Exercise.id)
            .filter(ExerciseLog.session_id == session.id, ExerciseLog.was_skipped.is_(False))
            .all()
        )
        met_values = [value for (value,) in met_values if value is not None]
        if met_values:
            average_met = sum(met_values) / len(met_values)
            calories = round(average_met * 3.5 * weight / 200 * duration_minutes, 1)

    session.status = "completed"
    session.completed_at = completed_at
    session.total_duration_minutes = duration_minutes
    session.estimated_calories_burned = calories
    session.xp_awarded = min(200, 25 + duration_minutes)
    session.xp_awarded_at = completed_at
    db.flush()

    award_xp(
        db,
        user_id,
        session.xp_awarded,
        "workout_completion",
        str(session.id),
        session.workout_name or "Workout completed",
    )
    apply_workout_hp_cost(db, user_id, completed_at)
    record_workout_activity(db, user_id, session.id, completed_at)
    unlock_eligible_achievements(db, user_id)
    db.flush()
    return session


def list_workouts(
    db: Session, user_id: int, limit: int = 50
) -> list[WorkoutSession]:
    """List only the requesting user's workout history."""
    _require_owner(db, user_id)
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 200:
        raise WorkoutError("History limit must be between 1 and 200.")
    return (
        db.query(WorkoutSession)
        .options(joinedload(WorkoutSession.exercise_logs))
        .filter_by(user_id=user_id)
        .order_by(WorkoutSession.session_date.desc())
        .limit(limit)
        .all()
    )
