from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.enums import MatchStatus


class MatchBase(BaseModel):
    """
    Base schema for match data
    """
    user1_id: UUID
    user2_id: UUID
    compatibility_score: float = Field(ge=0.0, le=100.0)
    status: str = Field(default=MatchStatus.PENDING.value)
    
    @validator("status")
    def validate_status(cls, v):
        if v not in [status.value for status in MatchStatus]:
            raise ValueError(f"Invalid match status. Must be one of: {[status.value for status in MatchStatus]}")
        return v
    
    @validator("compatibility_score")
    def validate_compatibility_score(cls, v):
        if v < 0.0 or v > 100.0:
            raise ValueError("Compatibility score must be between 0 and 100")
        return v


class MatchCreate(MatchBase):
    """
    Schema for match creation
    """
    pass


class MatchUpdate(BaseModel):
    """
    Schema for match update
    """
    status: Optional[str] = None
    
    @validator("status")
    def validate_status(cls, v):
        if v is not None and v not in [status.value for status in MatchStatus]:
            raise ValueError(f"Invalid match status. Must be one of: {[status.value for status in MatchStatus]}")
        return v


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


class Match(MatchInDBBase):
    """
    Schema for match response
    """
    pass


class MatchResponse(BaseModel):
    """
    Schema for detailed match response with user information
    """
    id: UUID
    user1_id: UUID
    user2_id: UUID
    compatibility_score: float
    status: str
    created_at: datetime
    updated_at: datetime
    user_profile: Optional[dict] = None  # Simplified user profile information
    
    class Config:
        from_attributes = True
