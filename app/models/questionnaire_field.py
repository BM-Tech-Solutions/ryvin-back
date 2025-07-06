from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class QuestionnaireField(BaseModel):
    """
    Model for questionnaire fields/questions
    """
    __tablename__ = "questionnaire_field"
    
    name = Column(String, nullable=False, unique=True)
    label = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    field_type = Column(String, nullable=False, default="text")  # text, boolean, select, etc.
    options = Column(Text, nullable=True)  # JSON string for select options
    required = Column(Boolean, default=False)
    order_position = Column(Integer, nullable=False, default=0)
    
    # Foreign key to category
    category_id = Column(Integer, ForeignKey("questionnaire_category.id"), nullable=False)
    
    # Define relationship with QuestionnaireCategory
    category = relationship("QuestionnaireCategory", back_populates="fields")
