from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class QuestionnaireBase(BaseModel):
    """
    Base schema for user questionnaire data
    """

    # religious_and_spiritual_beliefs
    religion_spirituality: str | None = None
    religious_practice: str | None = None
    partner_must_share_religion: str | None = None
    accept_non_believer: str | None = None
    faith_transmission_to_children: str | None = None
    partner_same_religious_education_vision: str | None = None

    # political_and_societal_values
    political_orientation: str | None = None
    partner_share_convictions_importance: str | None = None
    lessons_from_past_relationships: str | None = None

    # lifestyle_you
    sport_frequency: str | None = None
    specific_dietary_habits: str | None = None
    hygiene_tidiness_approach: str | None = None
    smoker: str | None = None
    drinks_alcohol: str | None = None

    # lifestyle_partner
    partner_sport_frequency: str | None = None
    partner_same_dietary_habits: str | None = None
    partner_cleanliness_importance: str | None = None
    accept_smoker_partner: str | None = None
    accept_alcohol_consumer_partner: str | None = None
    has_pet: str | None = None
    type_of_pet: str | None = None
    ready_to_live_with_pet: str | None = None
    allergic_to_animals: str | None = None
    which_animals_allergic: str | None = None

    # personality_and_social_relations
    personality_type: str | None = None
    partner_personality_preference: str | None = None
    primary_love_language: str | None = None
    partner_same_love_language: str | None = None
    friends_visit_frequency: str | None = None
    tolerance_social_vs_homebody: str | None = None
    conflict_management: str | None = None
    greatest_quality_in_relationship: str | None = None
    greatest_flaw_in_relationship: str | None = None
    what_attracts_you: str | None = None
    intolerable_flaw: str | None = None

    # physical_preferences_and_attraction
    physical_description: str | None = None
    main_dressing_style: str | None = None
    importance_of_appearance: str | None = None
    partner_hygiene_appearance_importance: str | None = None
    important_physical_aspects_partner: str | None = None

    # sexuality_and_intimacy
    importance_of_sexuality: str | None = None
    ideal_intimate_frequency: str | None = None
    comfort_level_talking_sexuality: str | None = None
    partner_sexual_values_alignment: str | None = None
    comfortable_public_affection: str | None = None
    ideal_sexuality_vision: str | None = None

    # desired_compatibility
    partner_similarity_preference: str | None = None
    partner_age_range: str | None = None

    # socio_economic_level
    importance_financial_situation_partner: str | None = None
    ideal_partner_education_profession: str | None = None
    money_approach_in_couple: str | None = None
    ideal_partner_description: str | None = None
    ideal_couple_life_description: str | None = None

    # children_and_family
    has_children: str | None = None
    number_of_children: str | None = None
    wants_children: str | None = None
    partner_must_want_children: str | None = None
    partner_desired_number_of_children: str | None = None
    educational_approach: str | None = None
    accept_partner_with_children: str | None = None
    share_same_educational_values: str | None = None
    imagine_yourself_in10_years: str | None = None
    reason_for_registration: str | None = None

    @field_validator("number_of_children")
    def validate_number_of_children(cls, v, values):
        if values.get("has_children") and v is None:
            raise ValueError("Number of children is required when has_children is True")
        if not values.get("has_children") and v is not None:
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

    class Config:
        from_attributes = True


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
