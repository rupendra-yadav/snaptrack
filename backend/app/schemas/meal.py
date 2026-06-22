from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# FoodItem schemas
# ---------------------------------------------------------------------------

class FoodItemBase(BaseModel):
    name: str
    estimated_weight_g: Optional[float] = None
    calories: float = Field(ge=0)
    protein_g: float = Field(ge=0)


class FoodItemCreate(FoodItemBase):
    """Used internally when saving a meal — no extra fields needed."""
    pass


class FoodItemResponse(FoodItemBase):
    id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Analysis schemas  (used by POST /meals/analyze — nothing is saved yet)
# ---------------------------------------------------------------------------

class AnalysisResult(BaseModel):
    """
    The structured output returned by the AI analysis endpoint.
    This is a preview — the user must confirm before anything is saved.
    """
    foods: list[FoodItemBase]
    total_calories: float = Field(ge=0)
    total_protein: float = Field(ge=0)
    image_path: str   # temporary path on disk, sent back so POST /meals can reference it


# ---------------------------------------------------------------------------
# Meal schemas
# ---------------------------------------------------------------------------

class MealCreate(BaseModel):
    """
    Body of POST /meals — sent after the user confirms the analysis.
    Includes the image_path returned by the analyze endpoint and the food list.
    """
    image_path: str
    foods: list[FoodItemCreate]
    total_calories: float = Field(ge=0)
    total_protein: float = Field(ge=0)


class MealResponse(BaseModel):
    id: int
    image_path: str
    total_calories: float
    total_protein: float
    created_at: datetime
    food_items: list[FoodItemResponse] = []

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Dashboard schema
# ---------------------------------------------------------------------------

class DashboardToday(BaseModel):
    total_calories: float
    total_protein: float
    meal_count: int
