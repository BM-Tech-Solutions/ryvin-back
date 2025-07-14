from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .user import User


class UserProfile(Base):
    """
    User profile model containing personal information
    """

    __tablename__ = "user_profile"

    user_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), unique=True
    )
    prenom: Mapped[str]
    genre: Mapped[str]  # Using Gender enum values
    age: Mapped[int]
    ville: Mapped[str]
    nationalite: Mapped[str]
    langues: Mapped[List[str]] = mapped_column(JSONB, default=list)  # List of languages as JSON
    situation_professionnelle: Mapped[str]  # Using ProfessionalStatus enum values
    niveau_etudes: Mapped[str]  # Using EducationLevel enum values
    deja_marie: Mapped[bool]
    a_des_enfants: Mapped[bool]
    nombre_enfants: Mapped[Optional[int]]
    type_relation_recherchee: Mapped[str]  # Using RelationshipType enum values
    genre_recherche: Mapped[str]  # Using Gender enum values
    photos: Mapped[List[str]] = mapped_column(JSONB, default=list)  # List of photo URLs as JSON
    is_profile_complete: Mapped[bool] = mapped_column(default=False)
    profile_completion_step: Mapped[int] = mapped_column(default=1)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="profile", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<UserProfile {self.id}: {self.prenom}, {self.age}>"
