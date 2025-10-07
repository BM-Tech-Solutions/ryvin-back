from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from firebase_admin import messaging
from sqlalchemy import DateTime, ForeignKey, Text, text
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

    sender_id: Mapped[Optional[UUID]] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("user.id"), nullable=True
    )

    content: Mapped[str] = mapped_column(Text)
    message_type: Mapped[str] = mapped_column(default=MessageType.TEXT)

    is_read: Mapped[bool] = mapped_column(default=False)
    is_flagged: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_deleted: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    twilio_msg_id: Mapped[str | None]

    # Relationships
    journey: Mapped["Journey"] = relationship(back_populates="messages", foreign_keys=[journey_id])
    sender: Mapped[Optional["User"]] = relationship(
        back_populates="sent_messages", foreign_keys=[sender_id]
    )

    def __repr__(self):
        return f"<Message {self.id}: Journey {self.journey_id}, Sender {self.sender_id}>"

    def send_notif_to_reciever(self, title: str):
        from app.schemas.message import MessageOut

        reciever = self.journey.match.get_other_user(self.sender_id)
        if reciever.firebase_token:
            message = messaging.Message(
                token=reciever.firebase_token,
                notification=messaging.Notification(title=title, body=self.content),
                data=MessageOut.model_validate(self).model_dump(),
            )

            messaging.send(message)

            print(f"{message.data = }")
            print(f"{message.notification = }")
            print(f"{message.token = }")
