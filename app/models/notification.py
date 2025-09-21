from typing import TYPE_CHECKING
from uuid import UUID

from firebase_admin import messaging
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .user import User


class Notification(Base):
    """
    Notification model
    """

    __tablename__ = "notification"
    user_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
    )

    title: Mapped[str]
    body: Mapped[str]
    is_ready: Mapped[bool] = mapped_column(default=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="notifications", foreign_keys=[user_id])

    def __str__(self):
        return f"notif: '{self.title}' to '{self.user}'"

    def send_to_user(self, data: dict = None):
        message = messaging.Message(
            token=self.user.firebase_token,
            notification=messaging.Notification(title=self.title, body=self.body),
            data=data or {},
        )

        messaging.send(message)
