"""
Stage 2 migration: add exercises, workout_sessions, exercise_logs,
foods, food_logs, user_game_stats, xp_transactions,
achievements, user_achievements, streak_activities tables.

Revision ID: 0002_stage2_workout_nutrition_gamification
Revises: 0001_initial
Create Date: 2026-10-28
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_stage2"
down_revision: Union[str, Sequence[str], None] = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── exercises ─────────────────────────────────────────────────────────────
    op.create_table(
        "exercises",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("primary_muscle_group", sa.String(50), nullable=False),
        sa.Column("secondary_muscle_groups", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("exercise_type", sa.String(20), nullable=False),
        sa.Column("required_equipment", sa.Text(), server_default="none", nullable=False),
        sa.Column("default_sets", sa.Integer(), nullable=True),
        sa.Column("default_reps", sa.Integer(), nullable=True),
        sa.Column("default_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("default_rest_seconds", sa.Integer(), server_default="60", nullable=False),
        sa.Column("met_value", sa.Float(), nullable=True),
        sa.Column("safety_notes", sa.Text(), nullable=True),
        sa.Column("easier_variation_id", sa.Integer(), nullable=True),
        sa.Column("harder_variation_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_exercises_name", "exercises", ["name"], unique=True)
    op.create_index("ix_exercises_category", "exercises", ["category"])
    op.create_index("ix_exercises_primary_muscle_group", "exercises", ["primary_muscle_group"])

    # ── workout_sessions ──────────────────────────────────────────────────────
    op.create_table(
        "workout_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_date", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), server_default="in_progress", nullable=False),
        sa.Column("workout_name", sa.String(200), nullable=True),
        sa.Column("workout_type", sa.String(50), nullable=True),
        sa.Column("total_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("estimated_calories_burned", sa.Float(), nullable=True),
        sa.Column("xp_awarded", sa.Integer(), server_default="0", nullable=False),
        sa.Column("xp_awarded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workout_sessions_user_id", "workout_sessions", ["user_id"])

    # ── exercise_logs ─────────────────────────────────────────────────────────
    op.create_table(
        "exercise_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("sets_completed", sa.Integer(), nullable=True),
        sa.Column("reps_completed", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("was_skipped", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("exercise_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["session_id"], ["workout_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exercise_logs_session_id", "exercise_logs", ["session_id"])
    op.create_index("ix_exercise_logs_exercise_id", "exercise_logs", ["exercise_id"])

    # ── foods ─────────────────────────────────────────────────────────────────
    op.create_table(
        "foods",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("serving_size", sa.Float(), nullable=False),
        sa.Column("serving_unit", sa.String(30), nullable=False),
        sa.Column("calories", sa.Float(), nullable=False),
        sa.Column("protein_g", sa.Float(), nullable=False),
        sa.Column("carbs_g", sa.Float(), nullable=False),
        sa.Column("fat_g", sa.Float(), nullable=False),
        sa.Column("fiber_g", sa.Float(), nullable=True),
        sa.Column("data_source", sa.String(100), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("is_vegetarian", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("is_vegan", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("is_gluten_free", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("contains_dairy", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("contains_nuts", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_foods_name", "foods", ["name"])

    # ── food_logs ─────────────────────────────────────────────────────────────
    op.create_table(
        "food_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("meal_type", sa.String(20), nullable=False),
        sa.Column("servings", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("calories_logged", sa.Float(), nullable=False),
        sa.Column("protein_g_logged", sa.Float(), nullable=False),
        sa.Column("carbs_g_logged", sa.Float(), nullable=False),
        sa.Column("fat_g_logged", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["food_id"], ["foods.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_food_logs_user_id", "food_logs", ["user_id"])
    op.create_index("ix_food_logs_log_date", "food_logs", ["log_date"])

    # ── user_game_stats ───────────────────────────────────────────────────────
    op.create_table(
        "user_game_stats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("total_xp", sa.Integer(), server_default="0", nullable=False),
        sa.Column("current_level", sa.Integer(), server_default="1", nullable=False),
        sa.Column("current_hp", sa.Integer(), server_default="100", nullable=False),
        sa.Column("max_hp", sa.Integer(), server_default="100", nullable=False),
        sa.Column("last_hp_regen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("best_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_active_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_game_stats_user_id", "user_game_stats", ["user_id"])

    # ── xp_transactions ───────────────────────────────────────────────────────
    op.create_table(
        "xp_transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("xp_amount", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(100), nullable=True),
        sa.Column("description", sa.String(200), nullable=True),
        sa.Column("awarded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "source_type", "source_id", name="uq_xp_transaction"),
    )
    op.create_index("ix_xp_transactions_user_id", "xp_transactions", ["user_id"])

    # ── achievements ──────────────────────────────────────────────────────────
    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("icon", sa.String(10), server_default="🏆", nullable=False),
        sa.Column("xp_reward", sa.Integer(), server_default="0", nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_achievements_key", "achievements", ["key"], unique=True)

    # ── user_achievements ─────────────────────────────────────────────────────
    op.create_table(
        "user_achievements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("achievement_id", sa.Integer(), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["achievement_id"], ["achievements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )
    op.create_index("ix_user_achievements_user_id", "user_achievements", ["user_id"])

    # ── streak_activities ─────────────────────────────────────────────────────
    op.create_table(
        "streak_activities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column("workout_session_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "activity_date", name="uq_streak_activity"),
    )
    op.create_index("ix_streak_activities_user_id", "streak_activities", ["user_id"])
    op.create_index("ix_streak_activities_activity_date", "streak_activities", ["activity_date"])


def downgrade() -> None:
    op.drop_table("streak_activities")
    op.drop_table("user_achievements")
    op.drop_table("achievements")
    op.drop_table("xp_transactions")
    op.drop_table("user_game_stats")
    op.drop_table("food_logs")
    op.drop_table("foods")
    op.drop_table("exercise_logs")
    op.drop_table("workout_sessions")
    op.drop_table("exercises")
