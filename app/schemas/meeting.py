from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.security import utc_now
from app.models.enums import MeetingStatus


class MeetingRequestBase(BaseModel):
    """
    Base schema for meeting request data
    """

    model_config = ConfigDict(from_attributes=True)

    journey_id: UUID
    requested_by: UUID
    proposed_date: datetime
    proposed_location: str
    status: MeetingStatus = MeetingStatus.PROPOSED

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


class MeetingRequestInDBBase(MeetingRequestBase):
    """
    Base schema for meeting request in DB
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class MeetingRequestInDB(MeetingRequestInDBBase):
    """
    Schema for meeting request in DB (internal use)
    """

    pass


class MeetingRequestOut(MeetingRequestInDBBase):
    """
    Schema for meeting request response
    """

    pass


class MeetingFeedbackBase(BaseModel):
    """
    Base schema for meeting feedback data
    """

    meeting_request_id: UUID
    user_id: UUID
    rating: int = Field(ge=1, le=5)
    feedback: Optional[str] = None
    wants_to_continue: bool


class MeetingFeedbackCreate(MeetingFeedbackBase):
    """
    Schema for meeting feedback creation
    """

    pass


class MeetingFeedbackInDBBase(MeetingFeedbackBase):
    """
    Base schema for meeting feedback in DB
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class MeetingFeedbackInDB(MeetingFeedbackInDBBase):
    """
    Schema for meeting feedback in DB (internal use)
    """

    pass


class MeetingFeedback(MeetingFeedbackInDBBase):
    """
    Schema for meeting feedback response
    """

    pass
