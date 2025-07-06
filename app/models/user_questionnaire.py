from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.enums import (
    PracticeLevel, ImportanceLevel, SportFrequency, DietType, HygieneImportance,
    ConsumptionLevel, StyleType, EducationPreference, PersonalityType,
    LoveLanguage, SocialFrequency, SocialTolerance, IntimacyFrequency,
    ComfortLevel, PublicAffectionLevel, CompatibilityType
)


class UserQuestionnaire(BaseModel):
    """
    User questionnaire model containing compatibility information
    """
    __tablename__ = 'userquestionnaire'
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, unique=True)
    
    # Religion et spiritualité
    religion = Column(String, nullable=True)
    est_pratiquant = Column(String, nullable=True)  # Using PracticeLevel enum values
    partenaire_meme_religion = Column(String, nullable=True)  # Using ImportanceLevel enum values
    accepte_autre_religion = Column(Boolean, nullable=True)
    transmission_foi_enfants = Column(Boolean, nullable=True)
    meme_vision_education_religieuse = Column(Boolean, nullable=True)
    
    # Mode de vie
    frequence_sport = Column(String, nullable=True)  # Using SportFrequency enum values
    habitudes_alimentaires = Column(String, nullable=True)  # Using DietType enum values
    approche_hygiene = Column(String, nullable=True)  # Using HygieneImportance enum values
    fume = Column(String, nullable=True)  # Using ConsumptionLevel enum values
    boit_alcool = Column(String, nullable=True)  # Using ConsumptionLevel enum values
    
    # Préférences partenaire
    sport_partenaire = Column(String, nullable=True)  # Using SportFrequency enum values
    memes_habitudes_alimentaires = Column(Boolean, nullable=True)
    importance_proprete_partenaire = Column(String, nullable=True)  # Using ImportanceLevel enum values
    accepte_fumeur = Column(Boolean, nullable=True)
    accepte_buveur = Column(Boolean, nullable=True)
    
    # Physique
    description_physique = Column(Text, nullable=True)
    style_vestimentaire = Column(String, nullable=True)  # Using StyleType enum values
    importance_apparence_soi = Column(String, nullable=True)  # Using ImportanceLevel enum values
    importance_apparence_partenaire = Column(String, nullable=True)  # Using ImportanceLevel enum values
    partenaire_ideal_physique = Column(Text, nullable=True)
    criteres_physiques_non_negotiables = Column(Text, nullable=True)
    
    # Enfants et famille
    souhaite_enfants = Column(Boolean, nullable=True)
    partenaire_doit_vouloir_enfants = Column(Boolean, nullable=True)
    nombre_enfants_souhaite = Column(Integer, nullable=True)
    approche_educative = Column(Text, nullable=True)
    accepte_partenaire_avec_enfants = Column(Boolean, nullable=True)
    memes_valeurs_educatives = Column(Boolean, nullable=True)
    
    # Socio-économique
    importance_situation_financiere = Column(String, nullable=True)  # Using ImportanceLevel enum values
    niveau_etudes_partenaire = Column(String, nullable=True)  # Using EducationPreference enum values
    approche_argent_couple = Column(Text, nullable=True)
    
    # Personnalité
    personalite = Column(String, nullable=True)  # Using PersonalityType enum values
    preference_personalite_partenaire = Column(String, nullable=True)  # Using PersonalityType enum values
    langage_amour = Column(String, nullable=True)  # Using LoveLanguage enum values
    meme_langage_amour = Column(Boolean, nullable=True)
    frequence_voir_amis = Column(String, nullable=True)  # Using SocialFrequency enum values
    tolerance_mode_vie_social = Column(String, nullable=True)  # Using SocialTolerance enum values
    gestion_conflits = Column(Text, nullable=True)
    
    # Sexualité
    importance_sexualite = Column(String, nullable=True)  # Using ImportanceLevel enum values
    frequence_ideale_rapports = Column(String, nullable=True)  # Using IntimacyFrequency enum values
    confort_parler_sexualite = Column(String, nullable=True)  # Using ComfortLevel enum values
    valeurs_sexuelles_proches = Column(Boolean, nullable=True)
    demonstrations_publiques_affection = Column(String, nullable=True)  # Using PublicAffectionLevel enum values
    vision_sexualite_couple = Column(Text, nullable=True)
    
    # Valeurs politiques
    orientation_politique = Column(Text, nullable=True)
    importance_convictions_partenaire = Column(Text, nullable=True)
    
    # Animaux
    a_animal = Column(Boolean, nullable=True)
    type_animal = Column(String, nullable=True)
    accepte_partenaire_avec_animal = Column(Boolean, nullable=True)
    allergies_animaux = Column(Boolean, nullable=True)
    allergies_quels_animaux = Column(String, nullable=True)
    
    # Compatibilité
    recherche_type = Column(String, nullable=True)  # Using CompatibilityType enum values
    
    # Questions finales
    vie_couple_ideale = Column(Text, nullable=True)
    ce_qui_fait_craquer = Column(Text, nullable=True)
    defaut_intolerable = Column(Text, nullable=True)
    plus_grande_qualite = Column(Text, nullable=True)
    plus_grand_defaut = Column(Text, nullable=True)
    partenaire_ideal_personnalite = Column(Text, nullable=True)
    lecons_relations_passees = Column(Text, nullable=True)
    vision_10_ans = Column(Text, nullable=True)
    raison_inscription = Column(Text, nullable=True)
    
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="questionnaire", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<UserQuestionnaire {self.id}: User {self.user_id}>"
