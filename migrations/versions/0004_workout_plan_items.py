"""Persist workout prescriptions separately from performed exercise logs.

Revision ID: 0004_workout_plan_items
Revises: 0003_idempotency_keys
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_workout_plan_items"
down_revision: Union[str, Sequence[str], None] = "0003_idempotency_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workout_plan_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("prescribed_sets", sa.Integer(), nullable=True),
        sa.Column("prescribed_reps", sa.Integer(), nullable=True),
        sa.Column("prescribed_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("exercise_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["session_id"], ["workout_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "exercise_order", name="uq_plan_item_order"),
    )
    op.create_index("ix_workout_plan_items_session_id", "workout_plan_items", ["session_id"])
    op.create_index("ix_workout_plan_items_exercise_id", "workout_plan_items", ["exercise_id"])
    with op.batch_alter_table("exercise_logs") as batch:
        batch.add_column(sa.Column("plan_item_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_exercise_logs_plan_item_id_workout_plan_items",
            "workout_plan_items",
            ["plan_item_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_index("ix_exercise_logs_plan_item_id", ["plan_item_id"])
        batch.create_unique_constraint("uq_exercise_log_plan_item", ["plan_item_id"])


def downgrade() -> None:
    with op.batch_alter_table("exercise_logs") as batch:
        batch.drop_constraint("uq_exercise_log_plan_item", type_="unique")
        batch.drop_index("ix_exercise_logs_plan_item_id")
        batch.drop_constraint(
            "fk_exercise_logs_plan_item_id_workout_plan_items", type_="foreignkey"
        )
        batch.drop_column("plan_item_id")
    op.drop_index("ix_workout_plan_items_exercise_id", table_name="workout_plan_items")
    op.drop_index("ix_workout_plan_items_session_id", table_name="workout_plan_items")
    op.drop_table("workout_plan_items")
