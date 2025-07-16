from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .user import User


class Questionnaire(Base):
    """
    User questionnaire model for compatibility matching
    """

    __tablename__ = "questionnaire"

    user_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), unique=True
    )

    # religious_and_spiritual_beliefs
    religion_spirituality: Mapped[Optional[str]]
    religious_practice: Mapped[Optional[str]]
    partner_must_share_religion: Mapped[Optional[str]]
    accept_non_believer: Mapped[Optional[str]]
    faith_transmission_to_children: Mapped[Optional[str]]
    partner_same_religious_education_vision: Mapped[Optional[str]]

    # political_and_societal_values
    political_orientation: Mapped[Optional[str]]
    partner_share_convictions_importance: Mapped[Optional[str]]
    lessons_from_past_relationships: Mapped[Optional[str]]

    # lifestyle_you
    sport_frequency: Mapped[Optional[str]]
    specific_dietary_habits: Mapped[Optional[str]]
    hygiene_tidiness_approach: Mapped[Optional[str]]
    smoker: Mapped[Optional[str]]
    drinks_alcohol: Mapped[Optional[str]]

    # lifestyle_partner
    partner_sport_frequency: Mapped[Optional[str]]
    partner_same_dietary_habits: Mapped[Optional[str]]
    partner_cleanliness_importance: Mapped[Optional[str]]
    accept_smoker_partner: Mapped[Optional[str]]
    accept_alcohol_consumer_partner: Mapped[Optional[str]]
    has_pet: Mapped[Optional[str]]
    type_of_pet: Mapped[Optional[str]]
    ready_to_live_with_pet: Mapped[Optional[str]]
    allergic_to_animals: Mapped[Optional[str]]
    which_animals_allergic: Mapped[Optional[str]]

    # personality_and_social_relations
    personality_type: Mapped[Optional[str]]
    partner_personality_preference: Mapped[Optional[str]]
    primary_love_language: Mapped[Optional[str]]
    partner_same_love_language: Mapped[Optional[str]]
    friends_visit_frequency: Mapped[Optional[str]]
    tolerance_social_vs_homebody: Mapped[Optional[str]]
    conflict_management: Mapped[Optional[str]]
    greatest_quality_in_relationship: Mapped[Optional[str]]
    greatest_flaw_in_relationship: Mapped[Optional[str]]
    what_attracts_you: Mapped[Optional[str]]
    intolerable_flaw: Mapped[Optional[str]]

    # physical_preferences_and_attraction
    physical_description: Mapped[Optional[str]]
    main_dressing_style: Mapped[Optional[str]]
    importance_of_appearance: Mapped[Optional[str]]
    partner_hygiene_appearance_importance: Mapped[Optional[str]]
    important_physical_aspects_partner: Mapped[Optional[str]]

    # sexuality_and_intimacy
    importance_of_sexuality: Mapped[Optional[str]]
    ideal_intimate_frequency: Mapped[Optional[str]]
    comfort_level_talking_sexuality: Mapped[Optional[str]]
    partner_sexual_values_alignment: Mapped[Optional[str]]
    comfortable_public_affection: Mapped[Optional[str]]
    ideal_sexuality_vision: Mapped[Optional[str]]

    # desired_compatibility
    partner_similarity_preference: Mapped[Optional[str]]
    partner_age_range: Mapped[Optional[str]]

    # socio_economic_level
    importance_financial_situation_partner: Mapped[Optional[str]]
    ideal_partner_education_profession: Mapped[Optional[str]]
    money_approach_in_couple: Mapped[Optional[str]]
    ideal_partner_description: Mapped[Optional[str]]
    ideal_couple_life_description: Mapped[Optional[str]]

    # children_and_family
    has_children: Mapped[Optional[str]]
    number_of_children: Mapped[Optional[str]]
    wants_children: Mapped[Optional[str]]
    partner_must_want_children: Mapped[Optional[str]]
    partner_desired_number_of_children: Mapped[Optional[str]]
    educational_approach: Mapped[Optional[str]]
    accept_partner_with_children: Mapped[Optional[str]]
    share_same_educational_values: Mapped[Optional[str]]
    imagine_yourself_in10_years: Mapped[Optional[str]]
    reason_for_registration: Mapped[Optional[str]]

    # Completion status
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="questionnaire", foreign_keys=[user_id])

    def is_complete(self) -> bool:
        """Check if the questionnaire is complete"""
        return self.completed_at is not None

    @classmethod
    def get_required_fields(cls):
        return [
            "religion_spirituality",
            "religious_practice",
            "partner_must_share_religion",
            "accept_non_believer",
            "faith_transmission_to_children",
            "partner_same_religious_education_vision",
            "political_orientation",
            "partner_share_convictions_importance",
            "lessons_from_past_relationships",
            "sport_frequency",
            "specific_dietary_habits",
            "hygiene_tidiness_approach",
            "smoker",
            "drinks_alcohol",
            "partner_sport_frequency",
            "partner_same_dietary_habits",
            "partner_cleanliness_importance",
            "accept_smoker_partner",
            "accept_alcohol_consumer_partner",
            "has_pet",
            "type_of_pet",
            "ready_to_live_with_pet",
            "allergic_to_animals",
            "which_animals_allergic",
            "personality_type",
            "partner_personality_preference",
            "primary_love_language",
            "partner_same_love_language",
            "friends_visit_frequency",
            "tolerance_social_vs_homebody",
            "conflict_management",
            "greatest_quality_in_relationship",
            "greatest_flaw_in_relationship",
            "what_attracts_you",
            "intolerable_flaw",
            "physical_description",
            "main_dressing_style",
            "importance_of_appearance",
            "partner_hygiene_appearance_importance",
            "important_physical_aspects_partner",
            "importance_of_sexuality",
            "ideal_intimate_frequency",
            "comfort_level_talking_sexuality",
            "partner_sexual_values_alignment",
            "comfortable_public_affection",
            "ideal_sexuality_vision",
            "partner_similarity_preference",
            "partner_age_range",
            "importance_financial_situation_partner",
            "ideal_partner_education_profession",
            "money_approach_in_couple",
            "ideal_partner_description",
            "ideal_couple_life_description",
            "has_children",
            "number_of_children",
            "wants_children",
            "partner_must_want_children",
            "partner_desired_number_of_children",
            "educational_approach",
            "accept_partner_with_children",
            "share_same_educational_values",
            "imagine_yourself_in10_years",
            "reason_for_registration",
        ]

    def get_missing_fields(self):
        missing_fields = []
        for field in Questionnaire.get_required_fields():
            if getattr(self, field) in [None, ""]:
                missing_fields.append(field)
        return missing_fields
