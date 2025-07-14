from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .meeting_request import MeetingRequest
    from .user import User


class MeetingFeedback(Base):
    """
    Meeting feedback model for user feedback after physical meetings
    """

    __tablename__ = "meeting_feedback"

    meeting_request_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("meeting_request.id")
    )
    user_id: Mapped[UUID] = mapped_column(pgUUID(as_uuid=True), ForeignKey("user.id"))

    rating: Mapped[int]  # 1-5 rating
    feedback: Mapped[str | None] = mapped_column(Text)
    wants_to_continue: Mapped[bool]

    # Relationships
    meeting_request: Mapped["MeetingRequest"] = relationship(
        back_populates="feedback", foreign_keys=[meeting_request_id]
    )
    user: Mapped["User"] = relationship(back_populates="meeting_feedbacks", foreign_keys=[user_id])

    def __repr__(self):
        return (
            f"<MeetingFeedback {self.id}: Meeting {self.meeting_request_id}, Rating: {self.rating}>"
        )
