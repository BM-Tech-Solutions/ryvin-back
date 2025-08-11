from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.security import utc_now
from app.models.enums import MeetingStatus


# Meeting Request
class MeetingRequestBase(BaseModel):
    """
    Base schema for meeting request data
    """

    model_config = ConfigDict(from_attributes=True)

    proposed_date: datetime
    proposed_location: str

    @field_validator("proposed_date")
    def validate_proposed_date(cls, v):
        if v < utc_now():
            raise ValueError("Proposed date must be in the future")
        return v


class MeetingRequestCreate(MeetingRequestBase):
    """
    Schema for meeting request creation
    """

    pass


class MeetingRequestUpdate(BaseModel):
    """
    Schema for meeting request update
    """

    proposed_date: Optional[datetime] = None
    proposed_location: Optional[str] = None
    status: Optional[MeetingStatus] = None

    @field_validator("proposed_date")
    def validate_proposed_date(cls, v):
        if v is not None and v < utc_now():
            raise ValueError("Proposed date must be in the future")
        return v


class MeetingRequestOut(MeetingRequestBase):
    """
    Schema for meeting request response
    """

    id: UUID
    journey_id: UUID
    requester_id: UUID
    status: MeetingStatus = MeetingStatus.PROPOSED
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# Meeting Feedback
class MeetingFeedbackBase(BaseModel):
    """
    Base schema for meeting feedback data
    """

    model_config = ConfigDict(from_attributes=True)

    rating: int = Field(ge=1, le=5)
    feedback: Optional[str] = None
    wants_to_continue: bool


class MeetingFeedbackCreate(MeetingFeedbackBase):
    """
    Schema for meeting feedback creation
    """

    pass


class MeetingFeedbackUpdate(MeetingFeedbackBase):
    """
    Schema for meeting feedback update
    """

    rating: int = Field(default=None, ge=1, le=5)
    wants_to_continue: bool = None


class MeetingFeedbackOut(MeetingFeedbackBase):
    """
    Schema for meeting feedback response
    """

    id: UUID
    meeting_request_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
