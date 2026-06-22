from fastapi import APIRouter
from app.api import meals, dashboard

api_router = APIRouter()
api_router.include_router(meals.router)
api_router.include_router(dashboard.router)
