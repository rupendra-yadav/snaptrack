from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Meal(Base):
    """
    One row per logged meal (one photo upload).
    Stores the image path and pre-computed macro totals
    so the dashboard query is a simple SUM — no JOIN required.
    """
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, nullable=False)
    total_calories = Column(Float, nullable=False, default=0.0)
    total_protein = Column(Float, nullable=False, default=0.0)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # One meal → many food items
    # cascade: deleting a Meal removes all its FoodItems automatically
    food_items = relationship(
        "FoodItem",
        back_populates="meal",
        cascade="all, delete-orphan",
        lazy="selectin",   # load food_items in the same query, not a second round-trip
    )

    def __repr__(self) -> str:
        return f"<Meal id={self.id} calories={self.total_calories} created={self.created_at.date()}>"


class FoodItem(Base):
    """
    One row per detected food within a meal.
    Keeps the per-item breakdown so the user can see exactly what was found.
    """
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    estimated_weight_g = Column(Float, nullable=True)   # grams; nullable if AI can't estimate
    calories = Column(Float, nullable=False, default=0.0)
    protein_g = Column(Float, nullable=False, default=0.0)

    meal = relationship("Meal", back_populates="food_items")

    def __repr__(self) -> str:
        return f"<FoodItem name={self.name!r} cal={self.calories} protein={self.protein_g}g>"
