from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.enums import (
    PracticeLevel, ImportanceLevel, SportFrequency, DietType, HygieneImportance,
    ConsumptionLevel, StyleType, EducationPreference, PersonalityType,
    LoveLanguage, SocialFrequency, SocialTolerance, IntimacyFrequency,
    ComfortLevel, PublicAffectionLevel, CompatibilityType
)


class Questionnaire(BaseModel):
    """
    User questionnaire model for compatibility matching
    """
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, unique=True)
    
    # Religion et spiritualité
    religion = Column(String, nullable=True)
    est_pratiquant = Column(String, nullable=True)
    partenaire_meme_religion = Column(String, nullable=True)
    accepte_autre_religion = Column(Boolean, nullable=True)
    transmission_foi_enfants = Column(Boolean, nullable=True)
    meme_vision_education_religieuse = Column(Boolean, nullable=True)
    
    # Mode de vie
    frequence_sport = Column(String, nullable=True)
    habitudes_alimentaires = Column(String, nullable=True)
    approche_hygiene = Column(String, nullable=True)
    fume = Column(String, nullable=True)
    boit_alcool = Column(String, nullable=True)
    
    # Préférences partenaire
    sport_partenaire = Column(String, nullable=True)
    memes_habitudes_alimentaires = Column(Boolean, nullable=True)
    importance_proprete_partenaire = Column(String, nullable=True)
    accepte_fumeur = Column(Boolean, nullable=True)
    accepte_buveur = Column(Boolean, nullable=True)
    
    # Physique
    description_physique = Column(Text, nullable=True)
    style_vestimentaire = Column(String, nullable=True)
    importance_apparence_soi = Column(String, nullable=True)
    importance_apparence_partenaire = Column(String, nullable=True)
    partenaire_ideal_physique = Column(Text, nullable=True)
    criteres_physiques_non_negotiables = Column(Text, nullable=True)
    
    # Enfants et famille
    souhaite_enfants = Column(Boolean, nullable=True)
    partenaire_doit_vouloir_enfants = Column(Boolean, nullable=True)
    nombre_enfants_souhaite = Column(String, nullable=True)
    importance_vie_famille = Column(String, nullable=True)
    relation_famille_origine = Column(Text, nullable=True)
    importance_relation_belle_famille = Column(String, nullable=True)
    
    # Éducation et valeurs
    valeurs_importantes = Column(Text, nullable=True)
    valeurs_partenaire = Column(Text, nullable=True)
    vision_roles_foyer = Column(Text, nullable=True)
    attentes_education_enfants = Column(Text, nullable=True)
    preference_education_enfants = Column(String, nullable=True)
    
    # Personnalité
    traits_personnalite = Column(Text, nullable=True)
    defauts_reconnus = Column(Text, nullable=True)
    personnalite_partenaire_compatible = Column(String, nullable=True)
    personnalite_partenaire_incompatible = Column(String, nullable=True)
    langage_amour = Column(String, nullable=True)
    
    # Loisirs et intérêts
    loisirs_principaux = Column(Text, nullable=True)
    interets_communs_necessaires = Column(Boolean, nullable=True)
    interets_importants_partenaire = Column(Text, nullable=True)
    activites_couple = Column(Text, nullable=True)
    
    # Social
    frequence_sorties = Column(String, nullable=True)
    type_sorties_preferees = Column(Text, nullable=True)
    introversion_extraversion = Column(String, nullable=True)
    tolerance_amis_partenaire = Column(String, nullable=True)
    
    # Communication et conflits
    style_communication = Column(Text, nullable=True)
    gestion_conflits = Column(Text, nullable=True)
    expression_emotions = Column(Text, nullable=True)
    attentes_communication_partenaire = Column(Text, nullable=True)
    
    # Intimité
    importance_intimite = Column(String, nullable=True)
    frequence_intimite_ideale = Column(String, nullable=True)
    confort_discussion_intimite = Column(String, nullable=True)
    niveau_affection_publique = Column(String, nullable=True)
    
    # Finances
    situation_financiere_actuelle = Column(Text, nullable=True)
    gestion_finances_couple = Column(Text, nullable=True)
    importance_situation_financiere_partenaire = Column(String, nullable=True)
    objectifs_financiers = Column(Text, nullable=True)
    
    # Habitation et géographie
    situation_logement_actuelle = Column(Text, nullable=True)
    preferences_habitation_future = Column(Text, nullable=True)
    flexibilite_demenagement = Column(Boolean, nullable=True)
    preferences_environnement_vie = Column(Text, nullable=True)
    
    # Compatibilité et attentes
    type_compatibilite_recherchee = Column(String, nullable=True)
    attentes_relation = Column(Text, nullable=True)
    rythme_progression_relation = Column(Text, nullable=True)
    
    # Completion status
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="questionnaire")
    
    def is_complete(self) -> bool:
        """Check if the questionnaire is complete"""
        # A questionnaire is considered complete if completed_at is set
        return self.completed_at is not None
