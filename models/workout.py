"""
Workout models — session, exercise log entries, and generated plan items.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.user import User
    from models.exercise import Exercise


class WorkoutSession(Base, TimestampMixin):
    """
    A single workout session performed by a user.
    Created when the user starts a workout; completed when they finish.
    """

    __tablename__ = "workout_sessions"
    __table_args__ = (
        UniqueConstraint("user_id", "request_key", name="uq_workout_session_request"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    request_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Session metadata
    session_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="in_progress", nullable=False
    )
    # in_progress | completed | skipped

    # Workout details
    workout_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    workout_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # generated | custom

    # Summary stats (computed on completion)
    total_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_calories_burned: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    xp_awarded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    exercise_logs: Mapped[list["ExerciseLog"]] = relationship(
        "ExerciseLog",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    plan_items: Mapped[list["WorkoutPlanItem"]] = relationship(
        "WorkoutPlanItem",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="WorkoutPlanItem.exercise_order",
    )

    def __repr__(self) -> str:
        return f"<WorkoutSession id={self.id} user_id={self.user_id} status={self.status!r}>"


class WorkoutPlanItem(Base, TimestampMixin):
    """One prescribed exercise in a generated or custom workout plan."""

    __tablename__ = "workout_plan_items"
    __table_args__ = (
        UniqueConstraint("session_id", "exercise_order", name="uq_plan_item_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    prescribed_sets: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prescribed_reps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prescribed_duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    exercise_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    session: Mapped["WorkoutSession"] = relationship(
        "WorkoutSession", back_populates="plan_items"
    )
    exercise: Mapped["Exercise"] = relationship("Exercise")


class ExerciseLog(Base, TimestampMixin):
    """
    Records actual performance for one exercise within a workout session.
    """

    __tablename__ = "exercise_logs"
    __table_args__ = (
        UniqueConstraint("session_id", "request_key", name="uq_exercise_log_request"),
        UniqueConstraint("plan_item_id", name="uq_exercise_log_plan_item"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    request_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    plan_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("workout_plan_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Actual performance
    sets_completed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reps_completed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Status
    was_skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Order within the session
    exercise_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    session: Mapped["WorkoutSession"] = relationship(
        "WorkoutSession", back_populates="exercise_logs"
    )

    def __repr__(self) -> str:
        return f"<ExerciseLog id={self.id} session_id={self.session_id} exercise_id={self.exercise_id}>"
