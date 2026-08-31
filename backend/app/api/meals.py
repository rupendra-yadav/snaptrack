import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.meal import MealCreate, MealResponse, AnalysisResult
from app.services.meal_service import MealService
from app.services.ai_analysis import AIAnalysisService
from app.services.ai.base import AIProviderError
from app.core.config import settings

router = APIRouter(prefix="/meals", tags=["meals"])


@router.post(
    "/analyze",
    response_model=AnalysisResult,
    summary="Analyze a meal photo with AI",
)
async def analyze_meal(
    file: UploadFile = File(..., description="Meal photo (JPEG or PNG)"),
):
    """
    Step 1 of the add-meal flow.

    Accepts an image upload, saves it to disk, and calls the AI service
    to identify foods and estimate macros. Returns a preview — nothing
    is written to the database until the user confirms via POST /meals.

    Phase 2 will replace the stub below with the real AIAnalysisService call.
    """
    # Validate file type — be lenient with camera uploads which may have null/unexpected MIME
    allowed = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    content_type = file.content_type or "image/jpeg"
    if content_type not in allowed:
        # Fall back to checking file extension
        ext = Path(file.filename or "").suffix.lower()
        if ext not in (".jpg", ".jpeg", ".png", ".webp"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Only JPEG, PNG, and WEBP images are supported.",
            )
        content_type = "image/jpeg"  # treat unknown as jpeg

    # Check file size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image must be under {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    # Save to disk with a UUID filename to avoid collisions
    ext = Path(file.filename or "upload.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    image_path = settings.UPLOAD_DIR / filename
    image_path.write_bytes(contents)

    # Call the AI service — provider is determined by AI_PROVIDER in .env
    try:
        service = AIAnalysisService()
        result = await service.analyze(contents, content_type)
    except AIProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI analysis failed: {e}",
        )

    # Attach the saved image path so the Flutter app can reference it
    # when calling POST /meals to confirm the meal
    result.image_path = str(image_path)
    return result


@router.post(
    "",
    response_model=MealResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a confirmed meal",
)
def create_meal(
    data: MealCreate,
    db: Session = Depends(get_db),
):
    """
    Step 2 of the add-meal flow.

    Called after the user reviews and confirms the analysis result.
    Persists the meal and food items to the database.
    """
    service = MealService(db)
    return service.create_meal(data)


@router.get(
    "",
    response_model=list[MealResponse],
    summary="Get meal history",
)
def list_meals(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Returns paginated meal history, newest first."""
    service = MealService(db)
    return service.get_meals(skip=skip, limit=limit)


@router.get(
    "/{meal_id}",
    response_model=MealResponse,
    summary="Get a single meal",
)
def get_meal(
    meal_id: int,
    db: Session = Depends(get_db),
):
    service = MealService(db)
    meal = service.get_meal(meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found.")
    return meal


@router.delete(
    "/{meal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a meal",
)
def delete_meal(
    meal_id: int,
    db: Session = Depends(get_db),
):
    service = MealService(db)
    if not service.delete_meal(meal_id):
        raise HTTPException(status_code=404, detail="Meal not found.")