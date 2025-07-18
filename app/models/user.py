from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import SubscriptionType

if TYPE_CHECKING:
    from .match import Match
    from .meeting_feedback import MeetingFeedback
    from .meeting_request import MeetingRequest
    from .message import Message
    from .photo import Photo
    from .profile import Profile
    from .questionnaire import Questionnaire


class User(Base):
    """
    User model for authentication and basic user information
    """

    __tablename__ = "user"

    phone_number: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(unique=True, index=True)
    has_completed_questionnaire: Mapped[bool] = mapped_column(default=False)
    subscription_type: Mapped[str] = mapped_column(default=SubscriptionType.FREE)
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(server_default=text("false"), default=False)
    is_verified: Mapped[bool] = mapped_column(default=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    profile: Mapped[Optional["Profile"]] = relationship(
        back_populates="user", uselist=False, foreign_keys="Profile.user_id"
    )
    questionnaire: Mapped[Optional["Questionnaire"]] = relationship(
        back_populates="user", uselist=False, foreign_keys="Questionnaire.user_id"
    )

    matches_as_user1: Mapped[List["Match"]] = relationship(
        back_populates="user1", foreign_keys="Match.user1_id"
    )
    matches_as_user2: Mapped[List["Match"]] = relationship(
        back_populates="user2", foreign_keys="Match.user2_id"
    )

    sent_messages: Mapped[List["Message"]] = relationship(
        back_populates="sender", foreign_keys="Message.sender_id"
    )
    meeting_requests: Mapped[List["MeetingRequest"]] = relationship(
        back_populates="requester", foreign_keys="MeetingRequest.requested_by"
    )
    meeting_feedbacks: Mapped[List["MeetingFeedback"]] = relationship(
        back_populates="user", foreign_keys="MeetingFeedback.user_id"
    )
    photos: Mapped[List["Photo"]] = relationship(
        back_populates="user", foreign_keys="Photo.user_id"
    )

    def __repr__(self) -> str:
        return f"<User {self.id}: {self.phone_number}>"
