from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.enums import MeetingStatus


class MeetingRequest(BaseModel):
    """
    Meeting request model for physical meetings between users
    """
    journey_id = Column(UUID(as_uuid=True), ForeignKey("journey.id"), nullable=False)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    proposed_date = Column(DateTime, nullable=False)
    proposed_location = Column(String, nullable=False)
    status = Column(String, default=MeetingStatus.PROPOSED.value, nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    
    # Relationships
    journey = relationship("Journey", back_populates="meeting_requests")
    requester = relationship("User", back_populates="meeting_requests", foreign_keys=[requested_by])
    feedback = relationship("MeetingFeedback", back_populates="meeting_request", uselist=False)
    
    def __repr__(self):
        return f"<MeetingRequest {self.id}: Journey {self.journey_id}, Status: {self.status}>"
