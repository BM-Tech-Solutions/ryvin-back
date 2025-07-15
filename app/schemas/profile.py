from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import EducationLevel, Gender, ProfessionalStatus, RelationshipType


class ProfileBase(BaseModel):
    """
    Base schema for user profile data
    """

    prenom: str
    genre: str = Field(description="Gender of the user")
    age: int = Field(ge=18, description="Age of the user (must be at least 18)")
    ville: str
    nationalite: str
    langues: List[str] = Field(default_factory=list)
    situation_professionnelle: str
    niveau_etudes: str
    deja_marie: bool
    a_des_enfants: bool
    nombre_enfants: Optional[int] = None
    type_relation_recherchee: str
    genre_recherche: str

    @field_validator("genre")
    def validate_genre(cls, v):
        if v not in [gender.value for gender in Gender]:
            raise ValueError(
                f"Invalid gender. Must be one of: {[gender.value for gender in Gender]}"
            )
        return v

    @field_validator("situation_professionnelle")
    def validate_situation_professionnelle(cls, v):
        if v not in [status.value for status in ProfessionalStatus]:
            raise ValueError(
                f"Invalid professional status. Must be one of: {[status.value for status in ProfessionalStatus]}"
            )
        return v

    @field_validator("niveau_etudes")
    def validate_niveau_etudes(cls, v):
        if v not in [level.value for level in EducationLevel]:
            raise ValueError(
                f"Invalid education level. Must be one of: {[level.value for level in EducationLevel]}"
            )
        return v

    @field_validator("type_relation_recherchee")
    def validate_type_relation_recherchee(cls, v):
        if v not in [rel_type.value for rel_type in RelationshipType]:
            raise ValueError(
                f"Invalid relationship type. Must be one of: {[rel_type.value for rel_type in RelationshipType]}"
            )
        return v

    @field_validator("genre_recherche")
    def validate_genre_recherche(cls, v):
        if v not in [gender.value for gender in Gender]:
            raise ValueError(
                f"Invalid gender preference. Must be one of: {[gender.value for gender in Gender]}"
            )
        return v

    @field_validator("nombre_enfants")
    def validate_nombre_enfants(cls, v, values):
        if values.get("a_des_enfants") and v is None:
            raise ValueError("Number of children is required when a_des_enfants is True")
        if not values.get("a_des_enfants") and v is not None:
            return None  # Reset to None if a_des_enfants is False
        return v


class ProfileCreate(ProfileBase):
    """
    Schema for profile creation
    """

    pass


class ProfileUpdate(BaseModel):
    """
    Schema for profile update
    """

    prenom: Optional[str] = None
    genre: Optional[str] = None
    age: Optional[int] = Field(None, ge=18)
    ville: Optional[str] = None
    nationalite: Optional[str] = None
    langues: Optional[List[str]] = None
    situation_professionnelle: Optional[str] = None
    niveau_etudes: Optional[str] = None
    deja_marie: Optional[bool] = None
    a_des_enfants: Optional[bool] = None
    nombre_enfants: Optional[int] = None
    type_relation_recherchee: Optional[str] = None
    genre_recherche: Optional[str] = None
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

    class Config:
        from_attributes = True


class ProfileInDB(ProfileInDBBase):
    """
    Schema for profile in DB (internal use)
    """

    pass


class Profile(ProfileInDBBase):
    """
    Schema for profile response
    """

    pass


class ProfileCompletion(BaseModel):
    """
    Schema for profile completion status
    """

    completion_percentage: int = Field(..., ge=0, le=100)
    missing_fields: List[str] = Field(default_factory=list)
    has_photos: bool = False
    photo_count: int = 0
    has_primary_photo: bool = False
