from datetime import datetime
from sqlalchemy import Column, ForeignKey, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

from app.core.database import Base


class Photo(Base):
    """
    Model for storing user profile photos
    """
    __tablename__ = "photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
