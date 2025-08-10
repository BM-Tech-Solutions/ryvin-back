from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

from .enums import FieldType

if TYPE_CHECKING:
    from .questionnaire_category import QuestionnaireCategory


class QuestionnaireField(Base):
    """
    Model for questionnaire fields/questions
    """

    __tablename__ = "questionnaire_field"

    name: Mapped[str] = mapped_column(unique=True)
    label: Mapped[str]
    description: Mapped[str] = mapped_column(Text, default="")
    order_position: Mapped[int] = mapped_column(default=0)
    parent_field: Mapped[Optional[str]]
    field_type: Mapped[str] = mapped_column(default=FieldType.TEXT)
    field_unit: Mapped[Optional[str]]
    placeholder: Mapped[Optional[str]]
    required: Mapped[bool] = mapped_column(default=False)
    allow_custom: Mapped[bool] = mapped_column(default=False)

    # Foreign key to category
    category_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("questionnaire_category.id"),
        index=True,
    )

    # Define relationship with QuestionnaireCategory
    category: Mapped["QuestionnaireCategory"] = relationship(
        back_populates="fields", foreign_keys=[category_id]
    )
