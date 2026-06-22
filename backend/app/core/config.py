from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./snaptrack.db"

    # AI provider
    AI_PROVIDER: str = "openai"       # swap to "gemini" etc. when you add new providers
    OPENAI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o"

    # File storage
    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE_MB: int = 10

    # App
    APP_NAME: str = "SnapTrack"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure upload directory exists on import
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
