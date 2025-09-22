from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import MatchStatus


class MatchBase(BaseModel):
    """
    Base schema for match data
    """

    model_config = ConfigDict(from_attributes=True, validate_by_name=True)

    user1_id: UUID
    user2_id: UUID
    compatibility_score: float = Field(ge=0.0, le=100.0)
    status: MatchStatus = Field(default=MatchStatus.PENDING)
    user1_accepted: bool = Field(default=False)
    user2_accepted: bool = Field(default=False)

    @field_validator("compatibility_score")
    def validate_compatibility_score(cls, v):
        if v < 0.0 or v > 100.0:
            raise ValueError("Compatibility score must be between 0 and 100")
        return v


class MatchCreate(MatchBase):
    """
    Schema for match creation
    """

    pass


class MatchCreateRequest(BaseModel):
    """
    Schema for manual match creation between two users
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    user1_id: UUID = Field(description="ID of the first user")
    user2_id: UUID = Field(description="ID of the second user") 
    compatibility_score: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="Compatibility score between users (0-100)"
    )
    
    @field_validator("user1_id", "user2_id")
    def validate_user_ids(cls, v):
        if not v:
            raise ValueError("User ID cannot be empty")
        return v
    
    @field_validator("compatibility_score")
    def validate_compatibility_score_create(cls, v):
        if v < 0.0 or v > 100.0:
            raise ValueError("Compatibility score must be between 0 and 100")
        return v


class MatchUpdate(BaseModel):
    """
    Schema for match update
    """

    status: Optional[MatchStatus] = None


class MatchInDBBase(MatchBase):
    """
    Base schema for match in DB
    """

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MatchInDB(MatchInDBBase):
    """
    Schema for match in DB (internal use)
    """

    pass


class MatchOut(BaseModel):
    """
    Schema for detailed match response with user information
    """

    model_config = ConfigDict(from_attributes=True, validate_by_name=True)

    id: UUID
    user1_id: UUID
    user2_id: UUID
    compatibility_score: float
    status: str
    created_at: datetime
    updated_at: datetime
    user1_accepted: bool = Field(default=False)
    user2_accepted: bool = Field(default=False)
    journey_id: Optional[UUID] = Field(default=None, description="ID of the journey created when both users accept the match")
    
    @classmethod
    def from_match(cls, match):
        """Create MatchOut from Match model, including journey_id if available"""
        journey_id = match.journey.id if match.journey else None
        
        return cls(
            id=match.id,
            user1_id=match.user1_id,
            user2_id=match.user2_id,
            compatibility_score=match.compatibility_score,
            status=match.status,
            created_at=match.created_at,
            updated_at=match.updated_at,
            user1_accepted=match.user1_accepted,
            user2_accepted=match.user2_accepted,
            journey_id=journey_id
        )
