from sqlalchemy.orm import Session
from app.models.meal import Meal, FoodItem
from app.schemas.meal import MealCreate


class MealService:
    """
    All database operations for meals and food items.
    Routes call these methods — no SQL leaks into the API layer.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_meal(self, data: MealCreate) -> Meal:
        """
        Persist a confirmed meal with its food items.
        Creates the Meal row first, then bulk-inserts FoodItem rows.
        SQLAlchemy handles the FK population automatically.
        """
        meal = Meal(
            image_path=data.image_path,
            total_calories=data.total_calories,
            total_protein=data.total_protein,
        )
        self.db.add(meal)
        self.db.flush()  # get meal.id without committing yet

        food_items = [
            FoodItem(
                meal_id=meal.id,
                name=item.name,
                estimated_weight_g=item.estimated_weight_g,
                calories=item.calories,
                protein_g=item.protein_g,
            )
            for item in data.foods
        ]
        self.db.add_all(food_items)
        self.db.commit()
        self.db.refresh(meal)
        return meal

    def get_meals(self, skip: int = 0, limit: int = 50) -> list[Meal]:
        """
        Return paginated meal history, newest first.
        food_items are loaded eagerly (lazy="selectin" on the model)
        so no N+1 queries when serializing.
        """
        return (
            self.db.query(Meal)
            .order_by(Meal.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_meal(self, meal_id: int) -> Meal | None:
        return self.db.query(Meal).filter(Meal.id == meal_id).first()

    def delete_meal(self, meal_id: int) -> bool:
        """Returns True if deleted, False if not found."""
        meal = self.get_meal(meal_id)
        if not meal:
            return False
        self.db.delete(meal)
        self.db.commit()
        return True
