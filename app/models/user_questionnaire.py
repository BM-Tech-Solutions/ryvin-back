from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .user import User


class UserQuestionnaire(Base):
    """
    User questionnaire model containing compatibility information
    """

    __tablename__ = "user_questionnaire"

    user_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), unique=True
    )

    # Religion et spiritualité
    religion: Mapped[Optional[str]]
    est_pratiquant: Mapped[Optional[str]]  # Using PracticeLevel enum values
    partenaire_meme_religion: Mapped[Optional[str]]  # Using ImportanceLevel enum values
    accepte_autre_religion: Mapped[Optional[bool]]
    transmission_foi_enfants: Mapped[Optional[bool]]
    meme_vision_education_religieuse: Mapped[Optional[bool]]

    # Mode de vie
    frequence_sport: Mapped[Optional[str]]  # Using SportFrequency enum values
    habitudes_alimentaires: Mapped[Optional[str]]  # Using DietType enum values
    approche_hygiene: Mapped[Optional[str]]  # Using HygieneImportance enum values
    fume: Mapped[Optional[str]]  # Using ConsumptionLevel enum values
    boit_alcool: Mapped[Optional[str]]  # Using ConsumptionLevel enum values

    # Préférences partenaire
    sport_partenaire: Mapped[Optional[str]]  # Using SportFrequency enum values
    memes_habitudes_alimentaires: Mapped[Optional[bool]]
    importance_proprete_partenaire: Mapped[Optional[str]]  # Using ImportanceLevel enum values
    accepte_fumeur: Mapped[Optional[bool]]
    accepte_buveur: Mapped[Optional[bool]]

    # Physique
    description_physique: Mapped[Optional[str]] = mapped_column(Text)
    style_vestimentaire: Mapped[Optional[str]]  # Using StyleType enum values
    importance_apparence_soi: Mapped[Optional[str]]  # Using ImportanceLevel enum values
    importance_apparence_partenaire: Mapped[Optional[str]]  # Using ImportanceLevel enum values
    partenaire_ideal_physique: Mapped[Optional[str]] = mapped_column(Text)
    criteres_physiques_non_negotiables: Mapped[Optional[str]] = mapped_column(Text)

    # Enfants et famille
    souhaite_enfants: Mapped[Optional[bool]]
    partenaire_doit_vouloir_enfants: Mapped[Optional[bool]]
    nombre_enfants_souhaite: Mapped[Optional[int]]
    approche_educative: Mapped[Optional[str]] = mapped_column(Text)
    accepte_partenaire_avec_enfants: Mapped[Optional[bool]]
    memes_valeurs_educatives: Mapped[Optional[bool]]

    # Socio-économique
    importance_situation_financiere: Mapped[Optional[str]]  # Using ImportanceLevel enum values
    niveau_etudes_partenaire: Mapped[Optional[str]]  # Using EducationPreference enum values
    approche_argent_couple: Mapped[Optional[str]] = mapped_column(Text)

    # Personnalité
    personalite: Mapped[Optional[str]]  # Using PersonalityType enum values
    preference_personalite_partenaire: Mapped[Optional[str]]  # Using PersonalityType enum values
    langage_amour: Mapped[Optional[str]]  # Using LoveLanguage enum values
    meme_langage_amour: Mapped[Optional[bool]]
    frequence_voir_amis: Mapped[Optional[str]]  # Using SocialFrequency enum values
    tolerance_mode_vie_social: Mapped[Optional[str]]  # Using SocialTolerance enum values
    gestion_conflits: Mapped[Optional[str]] = mapped_column(Text)

    # Sexualité
    importance_sexualite: Mapped[Optional[str]]  # Using ImportanceLevel enum values
    frequence_ideale_rapports: Mapped[Optional[str]]  # Using IntimacyFrequency enum values
    confort_parler_sexualite: Mapped[Optional[str]]  # Using ComfortLevel enum values
    valeurs_sexuelles_proches: Mapped[Optional[bool]]
    demonstrations_publiques_affection: Mapped[
        Optional[str]
    ]  # Using PublicAffectionLevel enum values
    vision_sexualite_couple: Mapped[Optional[str]] = mapped_column(Text)

    # Valeurs politiques
    orientation_politique: Mapped[Optional[str]] = mapped_column(Text)
    importance_convictions_partenaire: Mapped[Optional[str]] = mapped_column(Text)

    # Animaux
    a_animal: Mapped[Optional[bool]]
    type_animal: Mapped[Optional[str]]
    accepte_partenaire_avec_animal: Mapped[Optional[bool]]
    allergies_animaux: Mapped[Optional[bool]]
    allergies_quels_animaux: Mapped[Optional[str]]

    # Compatibilité
    recherche_type: Mapped[Optional[str]]  # Using CompatibilityType enum values

    # Questions finales
    vie_couple_ideale: Mapped[Optional[str]] = mapped_column(Text)
    ce_qui_fait_craquer: Mapped[Optional[str]] = mapped_column(Text)
    defaut_intolerable: Mapped[Optional[str]] = mapped_column(Text)
    plus_grande_qualite: Mapped[Optional[str]] = mapped_column(Text)
    plus_grand_defaut: Mapped[Optional[str]] = mapped_column(Text)
    partenaire_ideal_personnalite: Mapped[Optional[str]] = mapped_column(Text)
    lecons_relations_passees: Mapped[Optional[str]] = mapped_column(Text)
    vision_10_ans: Mapped[Optional[str]] = mapped_column(Text)
    raison_inscription: Mapped[Optional[str]] = mapped_column(Text)

    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="questionnaire", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<UserQuestionnaire {self.id}: User {self.user_id}>"
