from sqlalchemy import Column, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.enums import MatchStatus


class Match(BaseModel):
    """
    Match model representing a potential connection between two users
    """
    user1_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    user2_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    compatibility_score = Column(Float, nullable=False)
    status = Column(String, default=MatchStatus.PENDING.value, nullable=False)
    
    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id], back_populates="matches_as_user1")
    user2 = relationship("User", foreign_keys=[user2_id], back_populates="matches_as_user2")
    journey = relationship("Journey", back_populates="match", uselist=False)
    
    # Ensure that a match between two users is unique
    __table_args__ = (
        UniqueConstraint('user1_id', 'user2_id', name='unique_match'),
    )
    
    def __repr__(self):
        return f"<Match {self.id}: {self.user1_id} - {self.user2_id}, Score: {self.compatibility_score}>"
