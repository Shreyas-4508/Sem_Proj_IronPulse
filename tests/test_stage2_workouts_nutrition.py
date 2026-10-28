"""Stage 2 service tests for workouts, nutrition, streaks, and persisted rewards."""

import os
import sqlite3
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from models.exercise import Exercise
from models.gamification import (
    Achievement,
    StreakActivity,
    UserAchievement,
    UserGameStats,
    XPTransaction,
)
from models.nutrition import Food, FoodLog
from models.profile import UserProfile
from models.user import User
from models.workout import ExerciseLog, WorkoutPlanItem, WorkoutSession
from services.catalog_service import seed_catalog, search_exercises, search_foods
from services.gamification_service import (
    GamificationError,
    award_xp,
    get_game_stats,
    get_local_date,
    level_for_xp,
    record_workout_activity,
    regenerate_hp,
    unlock_achievement,
)
from services.nutrition_service import (
    NutritionError,
    get_daily_nutrition,
    get_nutrition_targets,
    log_food,
)
from services.profile_service import update_profile
from services.progress_service import ProgressError, get_progress_data
from services.workout_service import (
    WorkoutError,
    add_exercise_log,
    complete_workout,
    generate_workout,
    list_workouts,
    start_workout,
)
from services.auth_service import register_user


def _create_user(db, username: str, timezone_name: str = "UTC", complete: bool = True):
    user = register_user(
        db,
        f"{username}@example.com",
        username,
        "SecurePass1!",
        "SecurePass1!",
    )
    update_profile(
        db,
        user.id,
        user.id,
        display_name=username.title(),
        age=30,
        height_cm=175.0,
        weight_kg=72.0,
        fitness_goal="general_fitness" if complete else None,
        experience_level="beginner" if complete else None,
        preferred_workout_duration_minutes=30 if complete else None,
        workout_intensity="moderate",
        available_equipment="No equipment (bodyweight only)",
        dietary_preference="omnivore",
        timezone=timezone_name,
        onboarding_complete=complete,
    )
    return user


def _start_bodyweight_workout(db, user_id: int, request_key: str = "start-1"):
    squat = db.query(Exercise).filter_by(name="Bodyweight Squat").one()
    return start_workout(
        db,
        user_id,
        [{
            "exercise_id": squat.id,
            "prescribed_sets": 3,
            "prescribed_reps": 10,
            "exercise_order": 0,
        }],
        request_key=request_key,
    )


class TestStage2CatalogAndWorkout:
    def test_seed_catalog_is_repeatable_and_searchable(self, db):
        seed_catalog(db)
        first_counts = (
            db.query(Exercise).count(),
            db.query(Food).count(),
            db.query(Achievement).count(),
        )
        seed_catalog(db)
        assert first_counts == (15, 10, 8)
        assert (
            db.query(Exercise).count(),
            db.query(Food).count(),
            db.query(Achievement).count(),
        ) == first_counts
        assert search_exercises(db, "squat")[0].name == "Bodyweight Squat"
        assert search_foods(db, "banana")[0].name == "Banana"

    def test_generator_uses_profile_and_rejects_invalid_profile_or_duration(self, db):
        user = _create_user(db, "planuser")
        seed_catalog(db)
        plan = generate_workout(db, user.id, 30)
        assert 1 <= len(plan) <= 8
        assert all(item["exercise_id"] for item in plan)
        assert all(item["prescribed_duration_seconds"] is not None or item["prescribed_reps"] is not None for item in plan)
        with pytest.raises(WorkoutError, match="duration"):
            generate_workout(db, user.id, 25)
        incomplete = _create_user(db, "incomplete", complete=False)
        with pytest.raises(WorkoutError, match="Complete your profile"):
            generate_workout(db, incomplete.id)

    def test_plan_and_performance_are_separate_and_start_is_idempotent(self, db):
        user = _create_user(db, "planpersist")
        seed_catalog(db)
        session = _start_bodyweight_workout(db, user.id)
        session_id = session.id
        assert db.query(WorkoutPlanItem).filter_by(session_id=session_id).count() == 1
        assert db.query(ExerciseLog).filter_by(session_id=session_id).count() == 0

        duplicate = _start_bodyweight_workout(db, user.id)
        assert duplicate.id == session_id
        changed = [{
            "exercise_id": session.plan_items[0].exercise_id,
            "prescribed_sets": 4,
            "prescribed_reps": 10,
            "exercise_order": 0,
        }]
        with pytest.raises(WorkoutError, match="different workout"):
            start_workout(db, user.id, changed, request_key="start-1")

        db.commit()
        db.expire_all()
        saved = db.query(WorkoutSession).filter_by(id=session_id, user_id=user.id).one()
        assert saved.workout_name == "Personalized Workout"
        assert len(saved.plan_items) == 1

    def test_exercise_logging_validation_and_idempotency(self, db):
        user = _create_user(db, "loguser")
        seed_catalog(db)
        session = _start_bodyweight_workout(db, user.id)
        item = session.plan_items[0]
        with pytest.raises(WorkoutError, match="positive integer"):
            add_exercise_log(db, user.id, session.id, item.exercise_id, reps_completed=-1)

        log = add_exercise_log(
            db,
            user.id,
            session.id,
            item.exercise_id,
            plan_item_id=item.id,
            request_key="exercise-1",
            sets_completed=3,
            reps_completed=10,
        )
        repeated = add_exercise_log(
            db,
            user.id,
            session.id,
            item.exercise_id,
            plan_item_id=item.id,
            request_key="exercise-1",
            sets_completed=3,
            reps_completed=10,
        )
        assert repeated.id == log.id
        with pytest.raises(WorkoutError, match="different exercise log"):
            add_exercise_log(
                db,
                user.id,
                session.id,
                item.exercise_id,
                plan_item_id=item.id,
                request_key="exercise-1",
                sets_completed=2,
                reps_completed=10,
            )
        with pytest.raises(WorkoutError, match="already logged"):
            add_exercise_log(
                db,
                user.id,
                session.id,
                item.exercise_id,
                plan_item_id=item.id,
                sets_completed=3,
                reps_completed=10,
            )

    def test_completion_xp_hp_streak_and_achievement_are_once_only(self, db):
        user = _create_user(db, "completeuser")
        seed_catalog(db)
        session = _start_bodyweight_workout(db, user.id)
        item = session.plan_items[0]
        with pytest.raises(WorkoutError, match="at least one exercise"):
            complete_workout(db, user.id, session.id, 30)
        add_exercise_log(
            db,
            user.id,
            session.id,
            item.exercise_id,
            plan_item_id=item.id,
            sets_completed=3,
            reps_completed=10,
        )
        finished = complete_workout(db, user.id, session.id, 30)
        saved_id = finished.id
        assert finished.status == "completed"
        assert finished.xp_awarded == 55
        assert finished.estimated_calories_burned is not None
        stats = get_game_stats(db, user.id)
        assert stats.total_xp >= 80  # workout plus first-workout achievement and streak rewards, if due
        assert stats.current_hp < stats.max_hp
        assert stats.current_streak == 1
        assert db.query(XPTransaction).filter_by(
            user_id=user.id, source_type="workout_completion", source_id=str(saved_id)
        ).count() == 1
        assert db.query(StreakActivity).filter_by(user_id=user.id).count() == 1
        assert db.query(UserAchievement).filter_by(user_id=user.id).count() >= 1

        repeated = complete_workout(db, user.id, session.id, 30)
        assert repeated.id == saved_id
        assert db.query(XPTransaction).filter_by(
            user_id=user.id, source_type="workout_completion", source_id=str(saved_id)
        ).count() == 1
        assert unlock_achievement(db, user.id, "first_workout") is False

        db.commit()
        db.expire_all()
        persisted = db.query(WorkoutSession).filter_by(id=saved_id).one()
        assert persisted.status == "completed"
        assert db.query(UserGameStats).filter_by(user_id=user.id).one().total_xp == stats.total_xp

    def test_user_ownership_and_xp_validation(self, db):
        owner = _create_user(db, "owneruser")
        other = _create_user(db, "otheruser")
        seed_catalog(db)
        session = _start_bodyweight_workout(db, owner.id)
        with pytest.raises(WorkoutError, match="not found"):
            complete_workout(db, other.id, session.id, 30)
        assert list_workouts(db, other.id) == []

        with pytest.raises(GamificationError, match="positive integer"):
            award_xp(db, owner.id, -10, "bonus", "bad")
        with pytest.raises(GamificationError, match="source type"):
            award_xp(db, owner.id, 10, "unknown", "bad")
        assert level_for_xp(0) == 1
        assert level_for_xp(250) == 2
        assert award_xp(db, owner.id, 10, "bonus", "same") is not None
        assert award_xp(db, owner.id, 10, "bonus", "same") is None

    def test_timezone_date_conversion_and_idempotent_streak(self, db):
        user = _create_user(db, "timezoneuser", timezone_name="US/Pacific")
        other = _create_user(db, "timezoneother")
        seed_catalog(db)
        event = datetime(2026, 3, 8, 7, 30, tzinfo=timezone.utc)
        assert get_local_date(db, user.id, event) == date(2026, 3, 7)

        completed_at = datetime.now(timezone.utc)
        session = WorkoutSession(
            user_id=user.id,
            session_date=completed_at - timedelta(minutes=30),
            completed_at=completed_at,
            status="completed",
        )
        db.add(session)
        db.flush()
        first = record_workout_activity(db, user.id, session.id, completed_at)
        duplicate = record_workout_activity(db, user.id, session.id, completed_at)
        assert first[1] is True
        assert duplicate[1] is False
        assert first[0] == duplicate[0] == 1
        assert db.query(StreakActivity).filter_by(user_id=user.id).count() == 1
        with pytest.raises(GamificationError, match="owned"):
            record_workout_activity(db, other.id, session.id, completed_at)

    def test_hp_regeneration_caps_at_max(self, db):
        user = _create_user(db, "hpuser")
        stats = get_game_stats(db, user.id)
        stats.current_hp = 80
        start = datetime.now(timezone.utc)
        stats.last_hp_regen = start
        regenerate_hp(stats, start + timedelta(hours=2))
        assert stats.current_hp == 90
        regenerate_hp(stats, start + timedelta(days=2))
        assert stats.current_hp == stats.max_hp


class TestStage2NutritionAndProgress:
    def test_food_logging_idempotency_validation_and_persistence(self, db):
        user = _create_user(db, "fooduser", timezone_name="Asia/Kolkata")
        seed_catalog(db)
        banana = db.query(Food).filter_by(name="Banana").one()
        logged = log_food(
            db,
            user.id,
            banana.id,
            servings=1.5,
            meal_type="breakfast",
            request_key="food-1",
        )
        duplicate = log_food(
            db,
            user.id,
            banana.id,
            servings=1.5,
            meal_type="breakfast",
            request_key="food-1",
        )
        assert logged.id == duplicate.id
        assert duplicate.calories_logged == pytest.approx(133.5)
        with pytest.raises(NutritionError, match="different food entry"):
            log_food(
                db,
                user.id,
                banana.id,
                servings=2,
                meal_type="breakfast",
                request_key="food-1",
            )
        with pytest.raises(NutritionError, match="greater than 0"):
            log_food(db, user.id, banana.id, servings=0)
        with pytest.raises(NutritionError, match="Meal type"):
            log_food(db, user.id, banana.id, meal_type="midnight")
        with pytest.raises(NutritionError, match="Food ID"):
            log_food(db, user.id, True)

        summary = get_daily_nutrition(db, user.id)
        assert summary["calories"] == pytest.approx(133.5)
        assert summary["entries"][0].food.name == "Banana"
        assert get_nutrition_targets(db, user.id)["calories"] > 0
        db.commit()
        db.expire_all()
        persisted = db.query(FoodLog).filter_by(id=logged.id, user_id=user.id).one()
        assert persisted.protein_g_logged == pytest.approx(1.65)

    def test_food_log_and_targets_are_user_scoped(self, db):
        owner = _create_user(db, "foodowner")
        other = _create_user(db, "foodother")
        seed_catalog(db)
        apple = db.query(Food).filter_by(name="Banana").one()
        log_food(db, owner.id, apple.id)
        assert get_daily_nutrition(db, other.id)["entries"] == []
        assert get_nutrition_targets(db, other.id)["calories"] > 0

    def test_progress_chart_data_comes_from_owned_records(self, db):
        user = _create_user(db, "progressuser")
        other = _create_user(db, "progressother")
        seed_catalog(db)
        session = _start_bodyweight_workout(db, user.id)
        item = session.plan_items[0]
        add_exercise_log(
            db,
            user.id,
            session.id,
            item.exercise_id,
            plan_item_id=item.id,
            reps_completed=10,
            sets_completed=3,
        )
        complete_workout(db, user.id, session.id, 30)
        banana = db.query(Food).filter_by(name="Banana").one()
        log_food(db, user.id, banana.id)

        own_data = get_progress_data(db, user.id, days=7)
        other_data = get_progress_data(db, other.id, days=7)
        assert len(own_data) == len(other_data) == 7
        assert sum(day["workouts"] for day in own_data) == 1
        assert sum(day["calories_consumed"] for day in own_data) > 0
        assert sum(day["workouts"] for day in other_data) == 0
        with pytest.raises(ProgressError, match="between 7 and 365"):
            get_progress_data(db, user.id, days=1)


def test_migrations_upgrade_without_deleting_existing_user_data(tmp_path):
    project_dir = Path(__file__).resolve().parents[1]
    database_path = tmp_path / "stage2_migration.sqlite"
    database_url = f"sqlite:///{database_path.as_posix()}"
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url

    initial = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "0001_initial"],
        cwd=project_dir,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert initial.returncode == 0, initial.stderr
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "INSERT INTO users (email, username, password_hash, is_active, is_verified) "
            "VALUES (?, ?, ?, ?, ?)",
            ("persist@example.com", "persistuser", "hash", 1, 0),
        )
        connection.execute(
            "INSERT INTO user_profiles (user_id, display_name, preferred_unit, timezone, onboarding_complete) "
            "VALUES (?, ?, ?, ?, ?)",
            (1, "Persist User", "metric", "UTC", 0),
        )

    upgrade = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=project_dir,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert upgrade.returncode == 0, upgrade.stderr
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT username FROM users WHERE id=1").fetchone() == ("persistuser",)
        assert connection.execute("SELECT display_name FROM user_profiles WHERE user_id=1").fetchone() == ("Persist User",)
        assert connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone() == ("0004_workout_plan_items",)
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='workout_plan_items'"
        ).fetchone() == ("workout_plan_items",)
