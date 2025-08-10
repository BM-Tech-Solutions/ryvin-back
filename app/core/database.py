import uuid
from datetime import datetime
from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy import DateTime, create_engine
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.core.security import utc_now

from .config import settings

# Create a synchronous engine
engine = create_engine(str(settings.DATABASE_URI), echo=False, future=True)

# Create a configured session class
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


# Base class for all models
class Base(DeclarativeBase):
    """
    Base model for all SQLAlchemy models
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    Backward-compatible alias for obtaining a database session.
    Mirrors get_session() so modules can depend on get_db.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SessionDep = Annotated[Session, Depends(get_session)]
