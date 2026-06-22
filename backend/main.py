from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.api.router import api_router

# Import models so SQLAlchemy discovers them before create_all()
import app.models.meal  # noqa: F401


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI-powered meal tracking API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS — allow the Flutter app (and local dev tools) to call the API.
    # Tighten origins in production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Serve uploaded images as static files at /uploads/<filename>
    app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

    # Register all API routes under /api prefix
    app.include_router(api_router, prefix="/api")

    @app.on_event("startup")
    def on_startup():
        # Create all tables if they don't exist.
        # Safe to run repeatedly — won't drop existing data.
        Base.metadata.create_all(bind=engine)
        print(f"✓ Database ready at {settings.DATABASE_URL}")
        print(f"✓ Uploads directory: {settings.UPLOAD_DIR.resolve()}")

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok", "app": settings.APP_NAME}

    return app


app = create_app()
