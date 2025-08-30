from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

from .enums import FieldType

if TYPE_CHECKING:
    from .questionnaire_subcategory import QuestionnaireSubCategory


class QuestionnaireField(Base):
    """
    Model for questionnaire fields/questions
    """

    __tablename__ = "questionnaire_field"

    name: Mapped[str] = mapped_column(unique=True)
    label: Mapped[str]
    description: Mapped[str] = mapped_column(Text, default="")
    order_position: Mapped[int] = mapped_column(default=0)
    field_type: Mapped[str] = mapped_column(default=FieldType.TEXT)
    field_unit: Mapped[Optional[str]]
    placeholder: Mapped[Optional[str]]
    required: Mapped[bool] = mapped_column(default=False)
    allow_custom: Mapped[bool] = mapped_column(default=False)

    # Foreign key to parent field
    parent_id: Mapped[UUID | None] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("questionnaire_field.id", ondelete="SET NULL"),
        index=True,
    )

    # Foreign key to category
    sub_category_id: Mapped[UUID | None] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("questionnaire_subcategory.id"),
        index=True,
    )

    # Define the parent/child relationships
    children: Mapped[list["QuestionnaireField"]] = relationship(
        back_populates="parent",
        foreign_keys="QuestionnaireField.parent_id",
    )
    parent: Mapped[Optional["QuestionnaireField"]] = relationship(
        back_populates="children",
        foreign_keys=[parent_id],
        remote_side="QuestionnaireField.id",
    )

    # Define relationship with QuestionnaireSubCategory
    sub_category: Mapped[Optional["QuestionnaireSubCategory"]] = relationship(
        back_populates="fields",
        foreign_keys=[sub_category_id],
    )
