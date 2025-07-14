from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text
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

    # Religion et spiritualité
    religion: Mapped[Optional[str]]
    est_pratiquant: Mapped[Optional[str]]
    partenaire_meme_religion: Mapped[Optional[str]]
    accepte_autre_religion: Mapped[Optional[bool]]
    transmission_foi_enfants: Mapped[Optional[bool]]
    meme_vision_education_religieuse: Mapped[Optional[bool]]

    # Mode de vie
    frequence_sport: Mapped[Optional[str]]
    habitudes_alimentaires: Mapped[Optional[str]]
    approche_hygiene: Mapped[Optional[str]]
    fume: Mapped[Optional[str]]
    boit_alcool: Mapped[Optional[str]]

    # Préférences partenaire
    sport_partenaire: Mapped[Optional[str]]
    memes_habitudes_alimentaires: Mapped[Optional[bool]]
    importance_proprete_partenaire: Mapped[Optional[str]]
    accepte_fumeur: Mapped[Optional[bool]]
    accepte_buveur: Mapped[Optional[bool]]

    # Physique
    description_physique: Mapped[Optional[str]] = mapped_column(Text)
    style_vestimentaire: Mapped[Optional[str]]
    importance_apparence_soi: Mapped[Optional[str]]
    importance_apparence_partenaire: Mapped[Optional[str]]
    partenaire_ideal_physique: Mapped[Optional[str]] = mapped_column(Text)
    criteres_physiques_non_negotiables: Mapped[Optional[str]] = mapped_column(Text)

    # Enfants et famille
    souhaite_enfants: Mapped[Optional[bool]]
    partenaire_doit_vouloir_enfants: Mapped[Optional[bool]]
    nombre_enfants_souhaite: Mapped[Optional[str]]
    importance_vie_famille: Mapped[Optional[str]]
    relation_famille_origine: Mapped[Optional[str]] = mapped_column(Text)
    importance_relation_belle_famille: Mapped[Optional[str]]

    # Éducation et valeurs
    valeurs_importantes: Mapped[Optional[str]] = mapped_column(Text)
    valeurs_partenaire: Mapped[Optional[str]] = mapped_column(Text)
    vision_roles_foyer: Mapped[Optional[str]] = mapped_column(Text)
    attentes_education_enfants: Mapped[Optional[str]] = mapped_column(Text)
    preference_education_enfants: Mapped[Optional[str]]

    # Personnalité
    traits_personnalite: Mapped[Optional[str]] = mapped_column(Text)
    defauts_reconnus: Mapped[Optional[str]] = mapped_column(Text)
    personnalite_partenaire_compatible: Mapped[Optional[str]]
    personnalite_partenaire_incompatible: Mapped[Optional[str]]
    langage_amour: Mapped[Optional[str]]

    # Loisirs et intérêts
    loisirs_principaux: Mapped[Optional[str]] = mapped_column(Text)
    interets_communs_necessaires: Mapped[Optional[bool]]
    interets_importants_partenaire: Mapped[Optional[str]] = mapped_column(Text)
    activites_couple: Mapped[Optional[str]] = mapped_column(Text)

    # Social
    frequence_sorties: Mapped[Optional[str]]
    type_sorties_preferees: Mapped[Optional[str]] = mapped_column(Text)
    introversion_extraversion: Mapped[Optional[str]]
    tolerance_amis_partenaire: Mapped[Optional[str]]

    # Communication et conflits
    style_communication: Mapped[Optional[str]] = mapped_column(Text)
    gestion_conflits: Mapped[Optional[str]] = mapped_column(Text)
    expression_emotions: Mapped[Optional[str]] = mapped_column(Text)
    attentes_communication_partenaire: Mapped[Optional[str]] = mapped_column(Text)

    # Intimité
    importance_intimite: Mapped[Optional[str]]
    frequence_intimite_ideale: Mapped[Optional[str]]
    confort_discussion_intimite: Mapped[Optional[str]]
    niveau_affection_publique: Mapped[Optional[str]]

    # Finances
    situation_financiere_actuelle: Mapped[Optional[str]] = mapped_column(Text)
    gestion_finances_couple: Mapped[Optional[str]] = mapped_column(Text)
    importance_situation_financiere_partenaire: Mapped[Optional[str]]
    objectifs_financiers: Mapped[Optional[str]] = mapped_column(Text)

    # Habitation et géographie
    situation_logement_actuelle: Mapped[Optional[str]] = mapped_column(Text)
    preferences_habitation_future: Mapped[Optional[str]] = mapped_column(Text)
    flexibilite_demenagement: Mapped[Optional[bool]]
    preferences_environnement_vie: Mapped[Optional[str]] = mapped_column(Text)

    # Compatibilité et attentes
    type_compatibilite_recherchee: Mapped[Optional[str]]
    attentes_relation: Mapped[Optional[str]] = mapped_column(Text)
    rythme_progression_relation: Mapped[Optional[str]] = mapped_column(Text)

    # Completion status
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id])

    def is_complete(self) -> bool:
        """Check if the questionnaire is complete"""
        return self.completed_at is not None
