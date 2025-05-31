import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr

from app.core.database import Base


class BaseModel(Base):
    """
    Base model for all SQLAlchemy models
    """
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
