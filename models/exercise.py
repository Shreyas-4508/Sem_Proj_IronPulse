"""
Exercise model — defines exercises in the library.
Exercises are seeded once and shared across all users (read-only for users).
"""

from typing import Optional
from sqlalchemy import String, Text, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin


class Exercise(Base, TimestampMixin):
    """Represents a single exercise in the IronPulse exercise library."""

    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Muscle groups (comma-separated strings for simplicity)
    primary_muscle_group: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    secondary_muscle_groups: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Classification
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # warmup | chest | back | shoulders | arms | core | legs | glutes | full_body | cooldown

    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    # beginner | intermediate | advanced

    exercise_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # reps | timed | distance

    required_equipment: Mapped[str] = mapped_column(
        Text, default="none", nullable=False
    )
    # Comma-separated: "none" | "dumbbells" | "resistance_bands" | "pull_up_bar" | etc.

    # Default parameters
    default_sets: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    default_reps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    default_duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    default_rest_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    # Calorie estimation (MET value for metabolic equivalent)
    met_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Safety and variations
    safety_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    easier_variation_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    harder_variation_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Exercise id={self.id} name={self.name!r}>"

    @property
    def equipment_list(self) -> list[str]:
        if not self.required_equipment or self.required_equipment == "none":
            return []
        return [e.strip() for e in self.required_equipment.split(",") if e.strip()]

    @property
    def secondary_muscles_list(self) -> list[str]:
        if not self.secondary_muscle_groups:
            return []
        return [m.strip() for m in self.secondary_muscle_groups.split(",") if m.strip()]
