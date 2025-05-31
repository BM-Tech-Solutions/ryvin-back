from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.enums import MessageType


class Message(BaseModel):
    """
    Message model for communication between users in a journey
    """
    journey_id = Column(UUID(as_uuid=True), ForeignKey("journey.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String, default=MessageType.TEXT.value, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    journey = relationship("Journey", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    
    def __repr__(self):
        return f"<Message {self.id}: Journey {self.journey_id}, Sender {self.sender_id}>"
