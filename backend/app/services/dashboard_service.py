from datetime import date, datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.meal import Meal
from app.schemas.meal import DashboardToday


class DashboardService:
    """
    Aggregated stats for the dashboard.
    All calculations happen in the database — no Python-side math on full rows.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_today(self) -> DashboardToday:
        """
        Sums calories and protein for all meals created today (UTC date).
        Returns zeros when no meals exist — never None.
        """
        today = date.today()

        row = (
            self.db.query(
                func.coalesce(func.sum(Meal.total_calories), 0.0).label("total_calories"),
                func.coalesce(func.sum(Meal.total_protein), 0.0).label("total_protein"),
                func.count(Meal.id).label("meal_count"),
            )
            .filter(func.date(Meal.created_at) == today)
            .one()
        )

        return DashboardToday(
            total_calories=round(row.total_calories, 1),
            total_protein=round(row.total_protein, 1),
            meal_count=row.meal_count,
        )
