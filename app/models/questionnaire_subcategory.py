from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .questionnaire_category import QuestionnaireCategory
    from .questionnaire_field import QuestionnaireField


class QuestionnaireSubCategory(Base):
    """
    Model for questionnaire sub-categories
    """

    __tablename__ = "questionnaire_subcategory"

    name: Mapped[str] = mapped_column(unique=True)
    label: Mapped[str]
    description: Mapped[str] = mapped_column(Text, default="")
    order_position: Mapped[int] = mapped_column(default=0)
    # Foreign key to category
    category_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("questionnaire_category.id"),
        index=True,
    )

    # Define relationship with QuestionnaireField & QuestionnaireCategory
    fields: Mapped[list["QuestionnaireField"]] = relationship(
        back_populates="sub_category", foreign_keys="QuestionnaireField.sub_category_id"
    )
    category: Mapped["QuestionnaireCategory"] = relationship(
        back_populates="sub_categories", foreign_keys=[category_id]
    )
