from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.enums import SubscriptionType


class User(BaseModel):
    """
    User model for authentication and basic user information
    """
    phone = Column(String, unique=True, index=True, nullable=True)  # Renamed from phone_number for consistency
    email = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)  # URL to profile image
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    subscription_type = Column(String, default=SubscriptionType.FREE.value, nullable=False)
    subscription_expires_at = Column(DateTime, nullable=True)
    
    # Authentication related fields
    hashed_password = Column(String, nullable=True)
    verification_id = Column(String, nullable=True)  # For storing Firebase verification ID
    firebase_uid = Column(String, nullable=True)  # Firebase User ID for phone auth
    google_id = Column(String, nullable=True)  # Google User ID for Google auth
    provider = Column(String, nullable=True)  # For social login (e.g., 'google.com')
    provider_user_id = Column(String, nullable=True)  # ID from the provider
    
    # Device information
    device_id = Column(String, nullable=True)  # Device identifier
    platform = Column(String, nullable=True)  # Device platform (iOS, Android, Web)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    questionnaire = relationship("UserQuestionnaire", back_populates="user", uselist=False)
    
    # Matches where this user is user1
    matches_as_user1 = relationship(
        "Match", 
        foreign_keys="Match.user1_id",
        back_populates="user1"
    )
    
    # Matches where this user is user2
    matches_as_user2 = relationship(
        "Match", 
        foreign_keys="Match.user2_id",
        back_populates="user2"
    )
    
    # Messages sent by this user
    sent_messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    
    # Meeting requests created by this user
    meeting_requests = relationship(
        "MeetingRequest", 
        back_populates="requester",
        foreign_keys="MeetingRequest.requested_by"
    )
    
    # Meeting feedback provided by this user
    meeting_feedback = relationship(
        "MeetingFeedback", 
        back_populates="user",
        foreign_keys="MeetingFeedback.user_id"
    )
    
    def __repr__(self):
        return f"<User {self.id}: {self.phone}>"
