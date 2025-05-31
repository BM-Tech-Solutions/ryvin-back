from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.enums import (
    PracticeLevel, ImportanceLevel, SportFrequency, DietType, HygieneImportance,
    ConsumptionLevel, StyleType, EducationPreference, PersonalityType,
    LoveLanguage, SocialFrequency, SocialTolerance, IntimacyFrequency,
    ComfortLevel, PublicAffectionLevel, CompatibilityType
)


class QuestionnaireBase(BaseModel):
    """
    Base schema for user questionnaire data
    """
    # Religion et spiritualité
    religion: Optional[str] = None
    est_pratiquant: Optional[str] = None
    partenaire_meme_religion: Optional[str] = None
    accepte_autre_religion: Optional[bool] = None
    transmission_foi_enfants: Optional[bool] = None
    meme_vision_education_religieuse: Optional[bool] = None
    
    # Mode de vie
    frequence_sport: Optional[str] = None
    habitudes_alimentaires: Optional[str] = None
    approche_hygiene: Optional[str] = None
    fume: Optional[str] = None
    boit_alcool: Optional[str] = None
    
    # Préférences partenaire
    sport_partenaire: Optional[str] = None
    memes_habitudes_alimentaires: Optional[bool] = None
    importance_proprete_partenaire: Optional[str] = None
    accepte_fumeur: Optional[bool] = None
    accepte_buveur: Optional[bool] = None
    
    # Physique
    description_physique: Optional[str] = None
    style_vestimentaire: Optional[str] = None
    importance_apparence_soi: Optional[str] = None
    importance_apparence_partenaire: Optional[str] = None
    partenaire_ideal_physique: Optional[str] = None
    criteres_physiques_non_negotiables: Optional[str] = None
    
    # Enfants et famille
    souhaite_enfants: Optional[bool] = None
    partenaire_doit_vouloir_enfants: Optional[bool] = None
    nombre_enfants_souhaite: Optional[int] = None
    approche_educative: Optional[str] = None
    accepte_partenaire_avec_enfants: Optional[bool] = None
    memes_valeurs_educatives: Optional[bool] = None
    
    # Socio-économique
    importance_situation_financiere: Optional[str] = None
    niveau_etudes_partenaire: Optional[str] = None
    approche_argent_couple: Optional[str] = None
    
    # Personnalité
    personalite: Optional[str] = None
    preference_personalite_partenaire: Optional[str] = None
    langage_amour: Optional[str] = None
    meme_langage_amour: Optional[bool] = None
    frequence_voir_amis: Optional[str] = None
    tolerance_mode_vie_social: Optional[str] = None
    gestion_conflits: Optional[str] = None
    
    # Sexualité
    importance_sexualite: Optional[str] = None
    frequence_ideale_rapports: Optional[str] = None
    confort_parler_sexualite: Optional[str] = None
    valeurs_sexuelles_proches: Optional[bool] = None
    demonstrations_publiques_affection: Optional[str] = None
    vision_sexualite_couple: Optional[str] = None
    
    # Valeurs politiques
    orientation_politique: Optional[str] = None
    importance_convictions_partenaire: Optional[str] = None
    
    # Animaux
    a_animal: Optional[bool] = None
    type_animal: Optional[str] = None
    accepte_partenaire_avec_animal: Optional[bool] = None
    allergies_animaux: Optional[bool] = None
    allergies_quels_animaux: Optional[str] = None
    
    # Compatibilité
    recherche_type: Optional[str] = None
    
    # Questions finales
    vie_couple_ideale: Optional[str] = None
    ce_qui_fait_craquer: Optional[str] = None
    defaut_intolerable: Optional[str] = None
    plus_grande_qualite: Optional[str] = None
    plus_grand_defaut: Optional[str] = None
    partenaire_ideal_personnalite: Optional[str] = None
    lecons_relations_passees: Optional[str] = None
    vision_10_ans: Optional[str] = None
    raison_inscription: Optional[str] = None

    # Validators for enum fields
    @validator("est_pratiquant")
    def validate_est_pratiquant(cls, v):
        if v is not None and v not in [level.value for level in PracticeLevel]:
            raise ValueError(f"Invalid practice level. Must be one of: {[level.value for level in PracticeLevel]}")
        return v

    @validator("partenaire_meme_religion", "importance_proprete_partenaire", 
               "importance_apparence_soi", "importance_apparence_partenaire",
               "importance_situation_financiere", "importance_sexualite")
    def validate_importance_level(cls, v):
        if v is not None and v not in [level.value for level in ImportanceLevel]:
            raise ValueError(f"Invalid importance level. Must be one of: {[level.value for level in ImportanceLevel]}")
        return v

    @validator("frequence_sport", "sport_partenaire")
    def validate_sport_frequency(cls, v):
        if v is not None and v not in [freq.value for freq in SportFrequency]:
            raise ValueError(f"Invalid sport frequency. Must be one of: {[freq.value for freq in SportFrequency]}")
        return v

    @validator("habitudes_alimentaires")
    def validate_diet_type(cls, v):
        if v is not None and v not in [diet.value for diet in DietType]:
            raise ValueError(f"Invalid diet type. Must be one of: {[diet.value for diet in DietType]}")
        return v

    @validator("approche_hygiene")
    def validate_hygiene_importance(cls, v):
        if v is not None and v not in [level.value for level in HygieneImportance]:
            raise ValueError(f"Invalid hygiene importance. Must be one of: {[level.value for level in HygieneImportance]}")
        return v

    @validator("fume", "boit_alcool")
    def validate_consumption_level(cls, v):
        if v is not None and v not in [level.value for level in ConsumptionLevel]:
            raise ValueError(f"Invalid consumption level. Must be one of: {[level.value for level in ConsumptionLevel]}")
        return v

    @validator("style_vestimentaire")
    def validate_style_type(cls, v):
        if v is not None and v not in [style.value for style in StyleType]:
            raise ValueError(f"Invalid style type. Must be one of: {[style.value for style in StyleType]}")
        return v

    @validator("niveau_etudes_partenaire")
    def validate_education_preference(cls, v):
        if v is not None and v not in [pref.value for pref in EducationPreference]:
            raise ValueError(f"Invalid education preference. Must be one of: {[pref.value for pref in EducationPreference]}")
        return v

    @validator("personalite", "preference_personalite_partenaire")
    def validate_personality_type(cls, v):
        if v is not None and v not in [ptype.value for ptype in PersonalityType]:
            raise ValueError(f"Invalid personality type. Must be one of: {[ptype.value for ptype in PersonalityType]}")
        return v

    @validator("langage_amour")
    def validate_love_language(cls, v):
        if v is not None and v not in [lang.value for lang in LoveLanguage]:
            raise ValueError(f"Invalid love language. Must be one of: {[lang.value for lang in LoveLanguage]}")
        return v

    @validator("frequence_voir_amis")
    def validate_social_frequency(cls, v):
        if v is not None and v not in [freq.value for freq in SocialFrequency]:
            raise ValueError(f"Invalid social frequency. Must be one of: {[freq.value for freq in SocialFrequency]}")
        return v

    @validator("tolerance_mode_vie_social")
    def validate_social_tolerance(cls, v):
        if v is not None and v not in [tol.value for tol in SocialTolerance]:
            raise ValueError(f"Invalid social tolerance. Must be one of: {[tol.value for tol in SocialTolerance]}")
        return v

    @validator("frequence_ideale_rapports")
    def validate_intimacy_frequency(cls, v):
        if v is not None and v not in [freq.value for freq in IntimacyFrequency]:
            raise ValueError(f"Invalid intimacy frequency. Must be one of: {[freq.value for freq in IntimacyFrequency]}")
        return v

    @validator("confort_parler_sexualite")
    def validate_comfort_level(cls, v):
        if v is not None and v not in [level.value for level in ComfortLevel]:
            raise ValueError(f"Invalid comfort level. Must be one of: {[level.value for level in ComfortLevel]}")
        return v

    @validator("demonstrations_publiques_affection")
    def validate_public_affection_level(cls, v):
        if v is not None and v not in [level.value for level in PublicAffectionLevel]:
            raise ValueError(f"Invalid public affection level. Must be one of: {[level.value for level in PublicAffectionLevel]}")
        return v

    @validator("recherche_type")
    def validate_compatibility_type(cls, v):
        if v is not None and v not in [ctype.value for ctype in CompatibilityType]:
            raise ValueError(f"Invalid compatibility type. Must be one of: {[ctype.value for ctype in CompatibilityType]}")
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
