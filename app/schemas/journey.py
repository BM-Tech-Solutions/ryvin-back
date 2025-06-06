from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.enums import JourneyStep


class JourneyBase(BaseModel):
    """
    Base schema for journey data
    """
    match_id: UUID
    current_step: int = Field(default=JourneyStep.PRE_COMPATIBILITY.value)
    is_completed: bool = Field(default=False)
    
    @validator("current_step")
    def validate_current_step(cls, v):
        if v not in [step.value for step in JourneyStep]:
            raise ValueError(f"Invalid journey step. Must be one of: {[step.value for step in JourneyStep]}")
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
    current_step: Optional[int] = None
    step1_completed_at: Optional[datetime] = None
    step2_completed_at: Optional[datetime] = None
    step3_completed_at: Optional[datetime] = None
    step4_completed_at: Optional[datetime] = None
    step5_completed_at: Optional[datetime] = None
    is_completed: Optional[bool] = None
    ended_by: Optional[UUID] = None
    end_reason: Optional[str] = None
    
    @validator("current_step")
    def validate_current_step(cls, v):
        if v is not None and v not in [step.value for step in JourneyStep]:
            raise ValueError(f"Invalid journey step. Must be one of: {[step.value for step in JourneyStep]}")
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


class Journey(JourneyInDBBase):
    """
    Schema for journey response
    """
    pass


class JourneyResponse(BaseModel):
    """
    Schema for detailed journey response with additional data
    """
    id: UUID
    match_id: UUID
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
    match_data: Optional[dict] = None  # Additional match information
    partner_profile: Optional[dict] = None  # Partner profile information
    
    class Config:
        from_attributes = True
