from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import MatchStatus

if TYPE_CHECKING:
    from .journey import Journey
    from .user import User


class Match(Base):
    """
    Match model representing a potential connection between two users
    """

    __tablename__ = "match"
    __table_args__ = (UniqueConstraint("user1_id", "user2_id", name="unique_match"),)

    user1_id: Mapped[UUID] = mapped_column(pgUUID(as_uuid=True), ForeignKey("user.id"), index=True)
    user2_id: Mapped[UUID] = mapped_column(pgUUID(as_uuid=True), ForeignKey("user.id"), index=True)
    compatibility_score: Mapped[float]
    status: Mapped[str] = mapped_column(default=MatchStatus.PENDING)

    # Relationships
    user1: Mapped["User"] = relationship(back_populates="matches_as_user1", foreign_keys=[user1_id])
    user2: Mapped["User"] = relationship(back_populates="matches_as_user2", foreign_keys=[user2_id])
    journey: Mapped["Journey"] = relationship(
        back_populates="match", uselist=False, foreign_keys="Journey.match_id"
    )

    def __repr__(self):
        return f"<Match {self.id}: {self.user1_id} - {self.user2_id}, Score: {self.compatibility_score}>"
