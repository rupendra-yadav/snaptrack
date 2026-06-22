from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings


# SQLite needs connect_args for thread safety in FastAPI's async context.
# For Postgres in production, remove connect_args entirely.
connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    # Echo SQL to console in debug mode — turn off in production
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a DB session per request.

    Usage in a route:
        def my_route(db: Session = Depends(get_db)):
            ...

    The session is always closed in the finally block,
    even if the route raises an exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
