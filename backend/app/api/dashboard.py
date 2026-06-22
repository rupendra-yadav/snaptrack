from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.meal import DashboardToday
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/today",
    response_model=DashboardToday,
    summary="Today's calorie and protein totals",
)
def get_today(db: Session = Depends(get_db)):
    """
    Returns the sum of calories and protein across all meals logged today.
    Returns zeros when no meals have been logged — never 404.
    """
    return DashboardService(db).get_today()
