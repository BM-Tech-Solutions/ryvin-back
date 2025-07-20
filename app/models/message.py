from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.security import utc_now
from app.models.enums import MessageType

if TYPE_CHECKING:
    from .journey import Journey
    from .user import User


class Message(Base):
    """
    Message model for communication between users in a journey
    """

    __tablename__ = "message"

    journey_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("journey.id"), index=True
    )

    sender_id: Mapped[UUID] = mapped_column(pgUUID(as_uuid=True), ForeignKey("user.id"))

    content: Mapped[str] = mapped_column(Text)
    message_type: Mapped[str] = mapped_column(default=MessageType.TEXT)

    is_read: Mapped[bool] = mapped_column(default=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    journey: Mapped["Journey"] = relationship(back_populates="messages", foreign_keys=[journey_id])
    sender: Mapped["User"] = relationship(back_populates="sent_messages", foreign_keys=[sender_id])

    def __repr__(self):
        return f"<Message {self.id}: Journey {self.journey_id}, Sender {self.sender_id}>"
