from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.enums import JourneyStep


class Journey(BaseModel):
    """
    Journey model representing the structured path of a relationship
    """
    match_id = Column(UUID(as_uuid=True), ForeignKey("match.id"), nullable=False, unique=True)
    current_step = Column(Integer, default=JourneyStep.PRE_COMPATIBILITY.value, nullable=False)
    step1_completed_at = Column(DateTime, nullable=True)  # Pré-compatibilité
    step2_completed_at = Column(DateTime, nullable=True)  # Appel vocal/vidéo
    step3_completed_at = Column(DateTime, nullable=True)  # Photos débloquées
    step4_completed_at = Column(DateTime, nullable=True)  # Rencontre physique
    step5_completed_at = Column(DateTime, nullable=True)  # Bilan rencontre
    is_completed = Column(Boolean, default=False, nullable=False)
    ended_by = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=True)
    end_reason = Column(String, nullable=True)
    
    # Relationships
    match = relationship("Match", back_populates="journey")
    messages = relationship("Message", back_populates="journey")
    meeting_requests = relationship("MeetingRequest", back_populates="journey")
    
    def __repr__(self):
        return f"<Journey {self.id}: Match {self.match_id}, Step: {self.current_step}>"
