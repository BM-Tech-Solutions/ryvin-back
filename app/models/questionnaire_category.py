from typing import TYPE_CHECKING

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .questionnaire_field import QuestionnaireField


class QuestionnaireCategory(Base):
    """
    Model for questionnaire categories
    """

    __tablename__ = "questionnaire_category"

    name: Mapped[str] = mapped_column(unique=True)
    label: Mapped[str]
    description: Mapped[str] = mapped_column(Text, default="")
    order: Mapped[int] = mapped_column(default=0)
    step: Mapped[int]

    # Define relationship with QuestionnaireField
    fields: Mapped[list["QuestionnaireField"]] = relationship(back_populates="category")
