from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MatchStatus


class MatchBase(BaseModel):
    """
    Base schema for match data
    """

    model_config = ConfigDict(from_attributes=True)

    user1_id: UUID
    user2_id: UUID
    compatibility_score: float = Field(ge=0.0, le=100.0)


class MatchCreate(MatchBase):
    """
    Schema for match creation
    """

    pass


class MatchUpdate(BaseModel):
    """
    Schema for match update
    """

    status: Optional[MatchStatus] = None
    compatibility_score: float = Field(ge=0.0, le=100.0)


class MatchOut(MatchBase):
    """
    Schema for detailed match response with user information
    """

    id: UUID
    user1_accepted: Optional[bool]
    user2_accepted: Optional[bool]
    matched_at: Optional[datetime]
    status: MatchStatus = MatchStatus.PENDING
    compatibility_score: float
    created_at: datetime
    updated_at: datetime


class PotentialMatch(BaseModel):
    """
    Schema for potential match response
    """

    user_id: UUID
    compatibility_score: float
