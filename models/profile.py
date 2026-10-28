"""
UserProfile model — detailed fitness and preference data for each user.
Separated from User to keep authentication concerns clean.
"""

from typing import Optional, TYPE_CHECKING
from datetime import date

from sqlalchemy import (
    Integer, String, Float, Boolean, Date, Text, ForeignKey,
    CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from models.user import User


class UserProfile(Base, TimestampMixin):
    """
    Extended profile data collected during onboarding and editable thereafter.
    All measurement columns store values in metric (kg, cm) internally.
    """

    __tablename__ = "user_profiles"
    __table_args__ = (
        CheckConstraint("age IS NULL OR (age >= 13 AND age <= 120)", name="ck_profile_age"),
        CheckConstraint("height_cm IS NULL OR (height_cm > 50 AND height_cm < 300)", name="ck_profile_height"),
        CheckConstraint("weight_kg IS NULL OR (weight_kg > 20 AND weight_kg < 500)", name="ck_profile_weight"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # --- Personal ---
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Derived or manually entered

    # --- Body metrics (stored in metric) ---
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    preferred_unit: Mapped[str] = mapped_column(
        String(10), default="metric", nullable=False
    )  # "metric" or "imperial"

    # --- Fitness profile ---
    fitness_goal: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    # fat_loss | muscle_gain | general_fitness | endurance | maintenance

    experience_level: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    # beginner | intermediate | advanced

    preferred_workout_duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # e.g. 20, 30, 45, 60

    workout_intensity: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    # low | moderate | high

    available_equipment: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    # Comma-separated list: "dumbbells,resistance_bands,pull_up_bar"

    # --- Nutrition ---
    dietary_preference: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    # omnivore | vegetarian | vegan | keto | paleo | none

    food_allergies: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    # Comma-separated: "gluten,dairy,nuts"

    food_restrictions: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    # Additional restrictions free text

    # --- Settings ---
    timezone: Mapped[str] = mapped_column(
        String(50), default="UTC", nullable=False
    )
    onboarding_complete: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="profile")

    def __repr__(self) -> str:
        return f"<UserProfile user_id={self.user_id} display_name={self.display_name!r}>"

    @property
    def equipment_list(self) -> list[str]:
        """Returns available equipment as a Python list."""
        if not self.available_equipment:
            return []
        return [e.strip() for e in self.available_equipment.split(",") if e.strip()]

    @property
    def allergies_list(self) -> list[str]:
        """Returns food allergies as a Python list."""
        if not self.food_allergies:
            return []
        return [a.strip() for a in self.food_allergies.split(",") if a.strip()]
