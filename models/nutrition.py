"""
Nutrition models — food database and daily food logging.
"""

from datetime import date
from typing import Optional

from sqlalchemy import Integer, String, Float, Boolean, Date, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimestampMixin


class Food(Base, TimestampMixin):
    """
    A food item in the nutrition database.
    Shared across all users; admin-seeded.
    """

    __tablename__ = "foods"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    serving_size: Mapped[float] = mapped_column(Float, nullable=False)
    serving_unit: Mapped[str] = mapped_column(String(30), nullable=False)  # g | ml | oz | piece
    calories: Mapped[float] = mapped_column(Float, nullable=False)
    protein_g: Mapped[float] = mapped_column(Float, nullable=False)
    carbs_g: Mapped[float] = mapped_column(Float, nullable=False)
    fat_g: Mapped[float] = mapped_column(Float, nullable=False)
    fiber_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    data_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # proteins | carbs | vegetables | fruits | dairy | fats | snacks

    is_vegetarian: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_vegan: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_gluten_free: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    contains_dairy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    contains_nuts: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<Food id={self.id} name={self.name!r} cal={self.calories}>"


class FoodLog(Base, TimestampMixin):
    """Records food intake for a specific user on a specific day."""

    __tablename__ = "food_logs"
    __table_args__ = (
        UniqueConstraint("user_id", "request_key", name="uq_food_log_request"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    request_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    food_id: Mapped[int] = mapped_column(
        ForeignKey("foods.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # breakfast | lunch | dinner | snack
    servings: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Cached macros at time of logging (avoid recomputing if food data changes)
    calories_logged: Mapped[float] = mapped_column(Float, nullable=False)
    protein_g_logged: Mapped[float] = mapped_column(Float, nullable=False)
    carbs_g_logged: Mapped[float] = mapped_column(Float, nullable=False)
    fat_g_logged: Mapped[float] = mapped_column(Float, nullable=False)
    food: Mapped["Food"] = relationship("Food")

    def __repr__(self) -> str:
        return f"<FoodLog id={self.id} user_id={self.user_id} date={self.log_date}>"
