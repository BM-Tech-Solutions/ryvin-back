from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import JourneyStep
from app.schemas.match import MatchOut


class JourneyBase(BaseModel):
    """
    Base schema for journey data
    """

    model_config = ConfigDict(from_attributes=True, validate_by_name=True)

    match_id: UUID
    current_step: int = Field(default=JourneyStep.STEP1_PRE_COMPATIBILITY)
    is_completed: bool = Field(default=False)

    @field_validator("current_step")
    def validate_current_step(cls, v):
        if v not in [step.value for step in JourneyStep]:
            raise ValueError(
                f"Invalid journey step. Must be one of: {[step.value for step in JourneyStep]}"
            )
        return v


class JourneyCreate(JourneyBase):
    """
    Schema for journey creation
    """

    pass


class JourneyUpdate(BaseModel):
    """
    Schema for journey update
    """

    model_config = ConfigDict(from_attributes=True, validate_by_name=True)

    current_step: Optional[int] = None
    step1_completed_at: Optional[datetime] = None
    step2_completed_at: Optional[datetime] = None
    step3_completed_at: Optional[datetime] = None
    step4_completed_at: Optional[datetime] = None
    step5_completed_at: Optional[datetime] = None
    is_completed: Optional[bool] = None
    ended_by: Optional[UUID] = None
    end_reason: Optional[str] = None

    @field_validator("current_step")
    def validate_current_step(cls, v):
        if v is not None and v not in [step.value for step in JourneyStep]:
            raise ValueError(
                f"Invalid journey step. Must be one of: {[step.value for step in JourneyStep]}"
            )
        return v


class JourneyInDBBase(JourneyBase):
    """
    Base schema for journey in DB
    """

    id: UUID
    step1_completed_at: Optional[datetime] = None
    step2_completed_at: Optional[datetime] = None
    step3_completed_at: Optional[datetime] = None
    step4_completed_at: Optional[datetime] = None
    step5_completed_at: Optional[datetime] = None
    ended_by: Optional[UUID] = None
    end_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JourneyInDB(JourneyInDBBase):
    """
    Schema for journey in DB (internal use)
    """

    pass


class JourneyOut(BaseModel):
    """
    Schema for detailed journey response with additional data
    """

    model_config = ConfigDict(from_attributes=True, validate_by_name=True)

    id: UUID
    match_id: UUID
    user1_accepted: bool
    user2_accepted: bool
    current_step: int
    is_completed: bool
    step1_completed_at: Optional[datetime] = None
    step2_completed_at: Optional[datetime] = None
    step3_completed_at: Optional[datetime] = None
    step4_completed_at: Optional[datetime] = None
    step5_completed_at: Optional[datetime] = None
    ended_by: Optional[UUID] = None
    end_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    match: Optional[MatchOut] = None

    @classmethod
    def from_journey(cls, journey) -> "JourneyOut":
        return cls(
            id=journey.id,
            match_id=journey.match_id,
            user1_accepted=journey.match.user1_accepted if journey.match else False,
            user2_accepted=journey.match.user2_accepted if journey.match else False,
            current_step=journey.current_step,
            is_completed=journey.is_completed,
            step1_completed_at=journey.step1_completed_at,
            step2_completed_at=journey.step2_completed_at,
            step3_completed_at=journey.step3_completed_at,
            step4_completed_at=journey.step4_completed_at,
            step5_completed_at=journey.step5_completed_at,
            ended_by=journey.ended_by,
            end_reason=journey.end_reason,
            created_at=journey.created_at,
            updated_at=journey.updated_at,
            match=MatchOut.from_match(journey.match) if journey.match else None,
        )
