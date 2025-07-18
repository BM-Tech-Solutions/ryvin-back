from typing import TYPE_CHECKING, List
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .user import User


class Profile(Base):
    """
    User profile model containing personal information
    """

    __tablename__ = "profile"

    user_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), unique=True
    )

    first_name: Mapped[str]
    gender: Mapped[str]
    relationship_goal: Mapped[str]
    age: Mapped[int]
    city_of_residence: Mapped[str]
    nationality_cultural_origin: Mapped[str]
    languages_spoken: Mapped[List[str]] = mapped_column(JSONB, default=list)
    professional_situation: Mapped[str]
    education_level: Mapped[str]
    previously_married: Mapped[bool]

    photos: Mapped[List[str]] = mapped_column(JSONB, default=list)  # List of photo URLs as JSON
    is_profile_complete: Mapped[bool] = mapped_column(default=False)
    profile_completion_step: Mapped[int] = mapped_column(default=1)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="profile", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<Profile {self.id}: {self.first_name}, {self.age}>"
