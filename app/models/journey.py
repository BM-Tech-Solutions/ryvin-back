from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import JourneyStep

if TYPE_CHECKING:
    from .match import Match
    from .meeting_request import MeetingRequest
    from .message import Message


class Journey(Base):
    """
    Journey model representing the structured path of a relationship
    """

    __tablename__ = "journey"

    match_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("match.id"), unique=True
    )
    ended_by: Mapped[UUID | None] = mapped_column(pgUUID(as_uuid=True), ForeignKey("user.id"))
    current_step: Mapped[int] = mapped_column(default=JourneyStep.PRE_COMPATIBILITY)
    # Pré-compatibilité
    step1_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Appel vocal/vidéo
    step2_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Photos débloquées
    step3_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Rencontre physique
    step4_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Bilan rencontre
    step5_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    is_completed: Mapped[bool] = mapped_column(default=False)
    end_reason: Mapped[str | None]

    # Relationships
    match: Mapped["Match"] = relationship(back_populates="journey", foreign_keys=[match_id])
    messages: Mapped[list["Message"]] = relationship(back_populates="journey")
    meeting_requests: Mapped[list["MeetingRequest"]] = relationship(back_populates="journey")

    def __repr__(self):
        return f"<Journey {self.id}: Match {self.match_id}, Step: {self.current_step}>"
