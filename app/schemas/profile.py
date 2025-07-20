from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProfileBase(BaseModel):
    """
    Base schema for user profile data
    """

    model_config = ConfigDict(from_attributes=True, strict=False, validate_by_name=True)

    first_name: str
    gender: str = Field(description="Gender of the user")
    relationship_goal: str
    age: int = Field(ge=18, description="Age of the user (must be at least 18)")
    city_of_residence: str
    nationality_cultural_origin: str
    languages_spoken: List[str]
    professional_situation: str
    education_level: str
    previously_married: bool


class ProfileCreate(ProfileBase):
    """
    Schema for profile creation
    """

    pass


class ProfileUpdate(ProfileBase):
    """
    Schema for profile update
    """

    is_profile_complete: Optional[bool] = None
    profile_completion_step: Optional[int] = None


class ProfileInDBBase(ProfileBase):
    """
    Base schema for profile in DB
    """

    id: UUID
    user_id: UUID
    photos: List[str] = Field(default_factory=list)
    is_profile_complete: bool
    profile_completion_step: int
    created_at: datetime
    updated_at: datetime


class ProfileInDB(ProfileInDBBase):
    """
    Schema for profile in DB (internal use)
    """

    pass


class ProfileOut(ProfileInDBBase):
    """
    Schema for profile response
    """

    pass


class ProfileCompletion(BaseModel):
    """
    Schema for profile completion status
    """

    completion_percentage: int = Field(..., ge=0, le=100)
    missing_profile_fields: List[str] = Field(default_factory=list)
    missing_questionnaire_fields: List[str] = Field(default_factory=list)
    has_photos: bool = False
    photo_count: int = 0
    has_primary_photo: bool = False
