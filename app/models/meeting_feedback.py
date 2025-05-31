from sqlalchemy import Boolean, Column, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class MeetingFeedback(BaseModel):
    """
    Meeting feedback model for user feedback after physical meetings
    """
    meeting_request_id = Column(UUID(as_uuid=True), ForeignKey("meetingrequest.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 rating
    feedback = Column(Text, nullable=True)
    wants_to_continue = Column(Boolean, nullable=False)
    
    # Relationships
    meeting_request = relationship("MeetingRequest", back_populates="feedback")
    user = relationship("User", back_populates="meeting_feedback", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<MeetingFeedback {self.id}: Meeting {self.meeting_request_id}, Rating: {self.rating}>"
