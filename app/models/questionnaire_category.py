from typing import TYPE_CHECKING

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .questionnaire_subcategory import QuestionnaireSubCategory


class QuestionnaireCategory(Base):
    """
    Model for questionnaire categories
    """

    __tablename__ = "questionnaire_category"

    name: Mapped[str] = mapped_column(unique=True)
    label: Mapped[str]
    description: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str | None]
    order_position: Mapped[int] = mapped_column(default=0)

    # Define relationship with QuestionnaireSubCategory
    sub_categories: Mapped[list["QuestionnaireSubCategory"]] = relationship(
        back_populates="category", foreign_keys="QuestionnaireSubCategory.category_id"
    )
