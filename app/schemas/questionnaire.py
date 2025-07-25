from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class QuestionnaireBase(BaseModel):
    """
    Base schema for user questionnaire data
    """

    model_config = ConfigDict(from_attributes=True, validate_by_name=True)

    # profile
    first_name: Optional[str] = None
    gender: Optional[str] = Field(default=None, description="Gender of the user")
    relationship_goal: Optional[str] = None
    age: Optional[int] = Field(
        default=None, ge=18, description="Age of the user (must be at least 18)"
    )
    city_of_residence: Optional[str] = None
    nationality_cultural_origin: Optional[str] = None
    languages_spoken: List[str] = None
    professional_situation: Optional[str] = None
    education_level: Optional[str] = None
    previously_married: Optional[str] = None

    # religious_and_spiritual_beliefs
    religion_spirituality: Optional[str] = None
    religious_practice: Optional[str] = None
    partner_must_share_religion: Optional[str] = None
    accept_non_believer: Optional[str] = None
    faith_transmission_to_children: Optional[str] = None
    partner_same_religious_education_vision: Optional[str] = None

    # political_and_societal_values
    political_orientation: Optional[str] = None
    partner_share_convictions_importance: Optional[str] = None
    lessons_from_past_relationships: Optional[str] = None

    # lifestyle_you
    sport_frequency: Optional[str] = None
    specific_dietary_habits: Optional[str] = None
    hygiene_tidiness_approach: Optional[str] = None
    smoker: Optional[str] = None
    drinks_alcohol: Optional[str] = None

    # lifestyle_partner
    partner_sport_frequency: Optional[str] = None
    partner_same_dietary_habits: Optional[str] = None
    partner_cleanliness_importance: Optional[str] = None
    accept_smoker_partner: Optional[str] = None
    accept_alcohol_consumer_partner: Optional[str] = None
    has_pet: Optional[str] = None
    type_of_pet: Optional[str] = None
    ready_to_live_with_pet: Optional[str] = None
    allergic_to_animals: Optional[str] = None
    which_animals_allergic: Optional[str] = None

    # personality_and_social_relations
    personality_type: Optional[str] = None
    partner_personality_preference: Optional[str] = None
    primary_love_language: Optional[str] = None
    partner_same_love_language: Optional[str] = None
    friends_visit_frequency: Optional[str] = None
    tolerance_social_vs_homebody: Optional[str] = None
    conflict_management: Optional[str] = None
    greatest_quality_in_relationship: Optional[str] = None
    what_attracts_you: Optional[str] = None
    intolerable_flaw: Optional[str] = None

    # physical_preferences_and_attraction
    physical_description: Optional[str] = None
    clothing_style: Optional[str] = None
    appearance_importance: Optional[str] = None
    partner_hygiene_appearance_importance: Optional[str] = None
    partner_waist_size: Optional[str] = None
    partner_body_size: Optional[str] = None
    partner_clothing_style: Optional[str] = None
    care_partner_self_hygiene: Optional[bool] = None
    dont_care_partner_physical_aspects: Optional[bool] = None

    # sexuality_and_intimacy
    importance_of_sexuality: Optional[str] = None
    ideal_intimate_frequency: Optional[str] = None
    comfort_level_talking_sexuality: Optional[str] = None
    partner_sexual_values_alignment: Optional[str] = None
    comfortable_public_affection: Optional[str] = None
    ideal_sexuality_vision: Optional[str] = None

    # desired_compatibility
    partner_similarity_preference: Optional[str] = None
    partner_age_range: Optional[str] = None

    # socio_economic_level
    importance_financial_situation_partner: Optional[str] = None
    ideal_partner_education_profession: Optional[str] = None
    money_approach_in_couple: Optional[str] = None
    ideal_partner_description: Optional[str] = None
    ideal_couple_life_description: Optional[str] = None

    # children_and_family
    has_children: Optional[str] = None
    number_of_children: Optional[str] = None
    wants_children: Optional[str] = None
    partner_must_want_children: Optional[str] = None
    partner_desired_number_of_children: Optional[str] = None
    educational_approach: Optional[str] = None
    accept_partner_with_children: Optional[str] = None
    share_same_educational_values: Optional[str] = None
    imagine_yourself_in10_years: Optional[str] = None
    reason_for_registration: Optional[str] = None

    @field_validator("number_of_children")
    def validate_number_of_children(cls, v, info: ValidationInfo):
        if info.data.get("has_children") and v is None:
            raise ValueError("Number of children is required when has_children is True")
        if not info.data.get("has_children") and v is not None:
            return None  # Reset to None if has_children is False
        return v


class QuestionnaireCreate(QuestionnaireBase):
    """
    Schema for questionnaire creation
    """

    pass


class QuestionnaireUpdate(QuestionnaireBase):
    """
    Schema for questionnaire update
    """

    pass


class QuestionnaireInDBBase(QuestionnaireBase):
    """
    Base schema for questionnaire in DB
    """

    id: UUID
    user_id: UUID
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class QuestionnaireInDB(QuestionnaireInDBBase):
    """
    Schema for questionnaire in DB (internal use)
    """

    pass


class Questionnaire(QuestionnaireInDBBase):
    """
    Schema for questionnaire response
    """

    pass


class QuestionnaireCompletion(BaseModel):
    """
    Schema for Questionnaire completion status
    """

    completion_percentage: int = Field(..., ge=0, le=100)
    missing_fields: List[str] = Field(default_factory=list)
    photo_count: int = 0
    has_primary_photo: bool = False
