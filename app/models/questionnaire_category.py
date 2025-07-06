from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class QuestionnaireCategory(BaseModel):
    """
    Model for questionnaire categories
    """
    __tablename__ = "questionnaire_category"
    
    name = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    order_position = Column(Integer, nullable=False, default=0)
    
    # Define relationship with QuestionnaireField
    fields = relationship("QuestionnaireField", back_populates="category")
