from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .user import User


class Photo(Base):
    """
    Model for storing user profile photos
    """

    __tablename__ = "photo"

    user_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE")
    )
    file_path: Mapped[str]
    is_primary: Mapped[bool] = mapped_column(default=False)

    # Relationship
    user: Mapped["User"] = relationship(back_populates="photos", foreign_keys=[user_id])
