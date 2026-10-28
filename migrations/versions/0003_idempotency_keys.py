"""Add nullable idempotency keys to user-created log records.

Revision ID: 0003_idempotency_keys
Revises: 0002_stage2
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_idempotency_keys"
down_revision: Union[str, Sequence[str], None] = "0002_stage2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("workout_sessions") as batch:
        batch.add_column(sa.Column("request_key", sa.String(length=100), nullable=True))
        batch.create_unique_constraint(
            "uq_workout_session_request", ["user_id", "request_key"]
        )
    with op.batch_alter_table("exercise_logs") as batch:
        batch.add_column(sa.Column("request_key", sa.String(length=100), nullable=True))
        batch.create_unique_constraint(
            "uq_exercise_log_request", ["session_id", "request_key"]
        )
    with op.batch_alter_table("food_logs") as batch:
        batch.add_column(sa.Column("request_key", sa.String(length=100), nullable=True))
        batch.create_unique_constraint("uq_food_log_request", ["user_id", "request_key"])


def downgrade() -> None:
    with op.batch_alter_table("food_logs") as batch:
        batch.drop_constraint("uq_food_log_request", type_="unique")
        batch.drop_column("request_key")
    with op.batch_alter_table("exercise_logs") as batch:
        batch.drop_constraint("uq_exercise_log_request", type_="unique")
        batch.drop_column("request_key")
    with op.batch_alter_table("workout_sessions") as batch:
        batch.drop_constraint("uq_workout_session_request", type_="unique")
        batch.drop_column("request_key")
