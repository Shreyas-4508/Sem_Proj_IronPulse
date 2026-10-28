"""
Gamification models — XP, HP, levels, achievements, and streaks.
"""

from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Integer, String, Float, Boolean, Text, DateTime,
    Date, ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin


class UserGameStats(Base, TimestampMixin):
    """
    Core gamification stats for a user: XP, HP, level, streak.
    One row per user; updated atomically.
    """

    __tablename__ = "user_game_stats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    # XP & Levels
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # HP (game mechanic, not real health)
    current_hp: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    max_hp: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    last_hp_regen: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Streak
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_active_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    def __repr__(self) -> str:
        return f"<UserGameStats user_id={self.user_id} xp={self.total_xp} level={self.current_level}>"


class XPTransaction(Base, TimestampMixin):
    """
    Auditable record of every XP change.
    Used to prevent duplicate rewards and review XP history.
    """

    __tablename__ = "xp_transactions"
    __table_args__ = (
        # Prevent duplicate XP for the same event
        UniqueConstraint("user_id", "source_type", "source_id", name="uq_xp_transaction"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    xp_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # workout_completion | achievement | streak_milestone | bonus
    source_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # e.g. workout_session_id, achievement_id
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    awarded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<XPTransaction user_id={self.user_id} xp={self.xp_amount} source={self.source_type}>"


class Achievement(Base, TimestampMixin):
    """Defines available achievements (admin-seeded)."""

    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str] = mapped_column(String(10), default="🏆", nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    # fitness | nutrition | streak | social | milestone

    def __repr__(self) -> str:
        return f"<Achievement key={self.key!r} name={self.name!r}>"


class UserAchievement(Base, TimestampMixin):
    """Records which achievements each user has unlocked."""

    __tablename__ = "user_achievements"
    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    achievement_id: Mapped[int] = mapped_column(
        ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False
    )
    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<UserAchievement user_id={self.user_id} achievement_id={self.achievement_id}>"


class StreakActivity(Base, TimestampMixin):
    """
    Records which calendar dates a user has qualifying workout activity.
    Used for accurate streak calculations without depending on session_state.
    """

    __tablename__ = "streak_activities"
    __table_args__ = (
        UniqueConstraint("user_id", "activity_date", name="uq_streak_activity"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    activity_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    workout_session_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<StreakActivity user_id={self.user_id} date={self.activity_date}>"
