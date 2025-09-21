from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .user import User


class Device(Base):
    """
    Model for storing device unique tokens for sending push notifications
    """

    __tablename__ = "devices"
    user_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
    )

    token: Mapped[str] = mapped_column(unique=True, index=True)
    brand: Mapped[str | None]
    model: Mapped[str | None]
    name: Mapped[str | None]

    # Relationships
    user: Mapped["User"] = relationship(back_populates="devices", foreign_keys=[user_id])

    def __str__(self):
        return f"{self.user.name}: {self.token}"
