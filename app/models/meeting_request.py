from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import MeetingStatus

if TYPE_CHECKING:
    from .journey import Journey
    from .meeting_feedback import MeetingFeedback
    from .user import User


class MeetingRequest(Base):
    """
    Meeting request model for physical meetings between users
    """

    __tablename__ = "meeting_request"

    journey_id: Mapped[UUID] = mapped_column(pgUUID(as_uuid=True), ForeignKey("journey.id"))
    requested_by: Mapped[UUID] = mapped_column(pgUUID(as_uuid=True), ForeignKey("user.id"))

    proposed_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    proposed_location: Mapped[str]
    status: Mapped[str] = mapped_column(default=MeetingStatus.PROPOSED)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    journey: Mapped["Journey"] = relationship(
        back_populates="meeting_requests", foreign_keys=[journey_id]
    )
    requester: Mapped["User"] = relationship(
        back_populates="meeting_requests", foreign_keys=[requested_by]
    )
    feedback: Mapped["MeetingFeedback | None"] = relationship(
        back_populates="meeting_request",
        uselist=False,
        foreign_keys="MeetingFeedback.meeting_request_id",
    )

    def __repr__(self):
        return f"<MeetingRequest {self.id}: Journey {self.journey_id}, Status: {self.status}>"
