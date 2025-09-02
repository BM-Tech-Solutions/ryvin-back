from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
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
        pgUUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )

    # profile
    first_name: Mapped[Optional[str]]
    gender: Mapped[Optional[str]]
    relationship_goal: Mapped[Optional[str]]
    age: Mapped[Optional[str]]
    city_of_residence: Mapped[Optional[str]]
    nationality_cultural_origin: Mapped[Optional[str]]
    languages_spoken: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list)
    professional_situation: Mapped[Optional[str]]
    education_level: Mapped[Optional[str]]
    previously_married: Mapped[Optional[str]]

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
    what_attracts_you: Mapped[Optional[str]]
    intolerable_flaw: Mapped[Optional[str]]

    # physical_preferences_and_attraction
    physical_description: Mapped[Optional[str]]
    clothing_style: Mapped[Optional[str]]
    appearance_importance: Mapped[Optional[str]]
    partner_hygiene_appearance_importance: Mapped[Optional[str]]
    partner_physical_preferences: Mapped[Optional[str]]  # parent field
    partner_waist_size: Mapped[Optional[str]]  # child field
    partner_body_size: Mapped[Optional[str]]  # child field
    partner_clothing_style: Mapped[Optional[str]]  # child field
    care_partner_self_hygiene: Mapped[Optional[str]]  # child field
    dont_care_partner_physical_aspects: Mapped[Optional[str]]  # child field

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
    children_infos: Mapped[Optional[str]]  # parent field
    has_children: Mapped[Optional[str]]  # child field
    number_of_children: Mapped[Optional[str]]  # child field
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

    def is_field_answered(self, field_name: str) -> bool:
        """Check if some field is answered in this Questionnaire"""
        return getattr(self, field_name, None) not in [None, "", []]

    def __repr__(self) -> str:
        return f"<Questionnaire {self.id}: {self.first_name}, {self.age}>"

    @classmethod
    def fields_to_exclude(cls) -> list[str]:
        return ["id", "user_id", "completed_at", "created_at", "updated_at"]
