from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Shared base class for all ORM models.
    Import this Base in every model file so SQLAlchemy
    can discover all tables via Base.metadata.create_all().
    """
    pass
