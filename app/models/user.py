from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import SubscriptionType

if TYPE_CHECKING:
    from .match import Match
    from .meeting_feedback import MeetingFeedback
    from .meeting_request import MeetingRequest
    from .message import Message
    from .notification import Notification
    from .photo import Photo
    from .questionnaire import Questionnaire


class User(Base):
    """
    User model for authentication and basic user information
    """

    __tablename__ = "user"
    __table_args__ = (
        UniqueConstraint("phone_region", "phone_number", name="unique_phone_number"),
        CheckConstraint(
            text(
                "(phone_region IS NOT NULL AND phone_number IS NOT NULL) OR (phone_region IS NULL AND phone_number IS NULL)"
            ),
            name="both_number_and_region_or_none",
        ),
        UniqueConstraint("social_provider", "social_id", name="unique_social_account"),
    )

    phone_region: Mapped[Optional[str]] = mapped_column(nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(nullable=True, index=True)
    email: Mapped[Optional[str]]
    password: Mapped[Optional[str]]
    name: Mapped[Optional[str]] = mapped_column(unique=True, index=True)
    profile_image: Mapped[Optional[str]] = mapped_column(unique=True, index=True)
    has_completed_questionnaire: Mapped[bool] = mapped_column(default=False)
    subscription_type: Mapped[str] = mapped_column(default=SubscriptionType.FREE)
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(server_default=text("false"), default=False)
    is_verified: Mapped[bool] = mapped_column(default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_banned: Mapped[bool] = mapped_column(server_default=text("false"), default=False)
    ban_reason: Mapped[Optional[str]]
    banned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # OAuth
    social_provider: Mapped[Optional[str]]
    social_id: Mapped[Optional[str]]
    social_image: Mapped[Optional[str]]

    # firebase token
    firebase_token: Mapped[str | None]

    # Relationships
    questionnaire: Mapped[Optional["Questionnaire"]] = relationship(
        back_populates="user", uselist=False, foreign_keys="Questionnaire.user_id"
    )

    matches_as_user1: Mapped[list["Match"]] = relationship(
        back_populates="user1", foreign_keys="Match.user1_id"
    )
    matches_as_user2: Mapped[list["Match"]] = relationship(
        back_populates="user2", foreign_keys="Match.user2_id"
    )

    sent_messages: Mapped[list["Message"]] = relationship(
        back_populates="sender", foreign_keys="Message.sender_id"
    )
    meeting_requests: Mapped[list["MeetingRequest"]] = relationship(
        back_populates="requester", foreign_keys="MeetingRequest.requested_by"
    )
    meeting_feedbacks: Mapped[list["MeetingFeedback"]] = relationship(
        back_populates="user", foreign_keys="MeetingFeedback.user_id"
    )
    photos: Mapped[list["Photo"]] = relationship(
        back_populates="user", foreign_keys="Photo.user_id"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", foreign_keys="Notification.user_id"
    )

    def __repr__(self) -> str:
        return f"<User {self.id}: {self.phone_region} {self.phone_number}>"
