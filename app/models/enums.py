from enum import Enum, IntEnum
from typing import Tuple


class BaseStrEnum(str, Enum):
    def __new__(cls, value: str, label: str = None):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._label_ = label or value
        return obj

    @property
    def label(self) -> str:
        return self._label_

    @classmethod
    def options(cls) -> list[Tuple[str, str]]:
        return [(member.value, member.label) for member in cls]


class SocialProviders(BaseStrEnum):
    GOOGLE = "google", "Google"
    APPLE = "apple", "Apple"


# Form Fields Options
class Gender(BaseStrEnum):
    HOMME = "homme", "Homme"
    FEMME = "femme", "Femme"


class RelationshipGoal(BaseStrEnum):
    MARIAGE = "mariage", "Te marier"
    RELATION_SERIEUSE = "relation_serieuse", "Une relation sérieuse mais pas forcément le mariage"


class ProfessionalSituation(BaseStrEnum):
    ETUDIANT = "etudiant", "Étudiant(e)"
    SALARIE = "salarie", "Salarié(e)"
    INDEPENDANT = "independant", "Indépendant(e)"
    RECHERCHE_EMPLOI = "recherche_emploi", "En recherche d’emploi"
    RETRAITE = "retraite", "Retraité(e)"


class EducationLevel(BaseStrEnum):
    AUCUN_DIPLOME = "aucun_diplome", "Aucun diplôme"
    NIVEAU_LYCEE = "niveau_lycee", "Niveau lycée"
    BAC_OU_EQUIVALENT = "bac_ou_equivalent", "Bac ou équivalent"
    BAC_PLUS_2_3 = "bac_plus_2_3", "Bac+2 à Bac+3"
    BAC_PLUS_4_5 = "bac_plus_4_5", "Bac+4 ou Bac+5"
    DOCTORAT_OU_PLUS = "doctorat_ou_plus", "Doctorat ou plus"


class ReligiousPractice(BaseStrEnum):
    OUI = "oui", "Oui"
    NON = "non", "Non"
    OCCASIONNELLEMENT = "occasionnellement", "Occasionnellement"


class PartnerMustShareReligion(BaseStrEnum):
    OUI_ABSOLUMENT = "oui_absolument", "Oui, absolument"
    SERAIT_UN_PLUS = "serait_un_plus", "Ce serait un plus"
    PAS_NECESSAIRE = "pas_necessaire", "Non, ce n’est pas nécessaire"


class FaithTransmissionToChildren(BaseStrEnum):
    OUI = "oui", "Oui"
    NON = "non", "Non"
    JE_NE_SAIS_PAS_ENCORE = "je_ne_sais_pas_encore", "Je ne sais pas encore"


class PartnerSameReligiousEducationVision(BaseStrEnum):
    OUI = "oui", "Oui"
    NON = "non", "Non"
    PEU_IMPORTE = "peu_importe", "Peu importe"


class BodySize(BaseStrEnum):
    THIN = "thin", "Mince"
    ATHLETIC = "athletic", "Athlétique"
    WITH_FORMS = "with_forms", "Avec Formes"
    DONT_CARE = "dont_care", "Peu Importe"


class SportFrequency(BaseStrEnum):
    JAMAIS = "jamais", "Jamais"
    _1_2_PAR_SEMAINE = "1_2_par_semaine", "1 à 2 fois par semaine"
    _3_5_PAR_SEMAINE = "3_5_par_semaine", "3 à 5 fois par semaine"
    TOUS_LES_JOURS = "tous_les_jours", "Tous les jours"


class SpecificDietaryHabits(BaseStrEnum):
    AUCUNE = "aucune", "Aucune"
    VEGETARIEN = "vegetarien", "Végétarien(ne)"
    VEGAN = "vegan", "Vegan"
    HALAL = "halal", "Halal"
    CASHER = "casher", "Casher"


class HygieneTidinessApproach(BaseStrEnum):
    TRES_IMPORTANT = "tres_important", "Très important"
    IMPORTANT = "important", "Important"
    FLEXIBLE = "flexible", "Flexible"
    PAS_VRAIMENT = "pas_vraiment", "Je ne m’en préoccupe pas vraiment"


class Smoker(BaseStrEnum):
    OUI = "oui", "Oui"
    NON = "non", "Non"
    OCCASIONNELLEMENT = "occasionnellement", "Occasionnellement"


class DrinksAlcohol(BaseStrEnum):
    OUI = "oui", "Oui"
    NON = "non", "Non"
    OCCASIONNELLEMENT = "occasionnellement", "Occasionnellement"


class PartnerSportFrequency(BaseStrEnum):
    JAMAIS = "jamais", "Jamais"
    _1_2_PAR_SEMAINE = "1_2_par_semaine", "1 à 2 fois par semaine"
    _3_5_PAR_SEMAINE = "3_5_par_semaine", "3 à 5 fois par semaine"
    TOUS_LES_JOURS = "tous_les_jours", "Tous les jours"
    PEU_IMPORTE = "peu_importe", "Peu importe"


class PartnerSameDietaryHabits(BaseStrEnum):
    OUI = "oui", "Oui"
    NON_RESPECTE_CHOIX = "non_respecte_choix", "Non, tant qu’il/elle respecte mes choix"
    PEU_IMPORTE = "peu_importe", "Peu importe"


class PartnerCleanlinessImportance(BaseStrEnum):
    TRES_IMPORTANT = "tres_important", "Très important"
    IMPORTANT = "important", "Important"
    FLEXIBLE = "flexible", "Flexible"
    PEU_IMPORTANT = "peu_important", "Peu important"


class AcceptSmokerPartner(BaseStrEnum):
    OUI = "oui", "Oui"
    NON = "non", "Non"
    OCCASIONNELLEMENT_SEULEMENT = "occasionnellement_seulement", "Occasionnellement seulement"


class AcceptAlcoholConsumerPartner(BaseStrEnum):
    OUI = "oui", "Oui"
    NON = "non", "Non"
    OCCASIONNELLEMENT_SEULEMENT = "occasionnellement_seulement", "Occasionnellement seulement"


class ReadyToLiveWithPet(BaseStrEnum):
    OUI = "oui", "Oui"
    NON = "non", "Non"
    CA_DEPEND = "ca_depend"


class PersonalityType(BaseStrEnum):
    INTROVERTI = "introverti", "Introverti(e)"
    EXTRAVERTI = "extraverti", "Extraverti(e)"
    MELANGE_DES_DEUX = "melange_des_deux", "Un mélange des deux"


class PartnerPersonalityPreference(BaseStrEnum):
    INTROVERTI = "introverti", "Introverti(e)"
    EXTRAVERTI = "extraverti", "Extraverti(e)"
    AMBIVERT = "ambivert"
    PEU_IMPORTE = "peu_importe", "Peu importe"


class PrimaryLoveLanguage(BaseStrEnum):
    PAROLES_VALORISANTES = "paroles_valorisantes", "Paroles valorisantes"
    CONTACT_PHYSIQUE = "contact_physique", "Contact physique"
    TEMPS_DE_QUALITE = "temps_de_qualite", "Temps de qualité"
    CADEAUX = "cadeaux", "Cadeaux"
    SERVICES_RENDUS = "services_rendus", "Services rendus"


class FriendsVisitFrequency(BaseStrEnum):
    TRES_SOUVENT = "tres_souvent", "Très souvent"
    REGULIEREMENT = "regulierement", "Régulièrement"
    OCCASIONNELLEMENT = "occasionnellement", "Occasionnellement"
    RAREMENT = "rarement", "Rarement"


class ToleranceSocial(BaseStrEnum):
    BESOIN_EQUILIBRE = "besoin_equilibre", "J’ai besoin d’équilibre"
    PAS_DERANGE_EPANOUI = (
        "pas_derange_epanoui",
        "Ça ne me dérange pas tant qu’il/elle est épanoui(e)",
    )
    PREFERE_STYLE_PROCHE = "prefere_style_proche", "Je préfère un style de vie proche du mien"


class ClothingStyle(BaseStrEnum):
    CLASSIQUE_ELEGANT = "classique_elegant", "Classique / Élégant"
    DECONTRACTE_SPORTIF = "decontracte_sportif", "Décontracté / Sportif"
    URBAIN_TENDANCE = "urbain_tendance", "Urbain / Tendance"
    CHANGEANT_HUMEUR = "changeant_humeur", "Changeant selon l’humeur"


class PartnerClothingStyle(BaseStrEnum):
    CLASSIC = "classic", "Classique"
    URBAIN = "urbain", "Urbain"
    TRENDING = "trending", "Tendance"
    DONT_CARE = "dont_care", "Peu Importe"


class ImportanceOfAppearance(BaseStrEnum):
    TRES_IMPORTANTE = "tres_importante", "Très importante"
    MOYENNE = "moyenne", "Moyenne"
    PEU_IMPORTANTE = "peu_importante", "Peu importante"


class PartnerHygieneAppearanceImportance(BaseStrEnum):
    TRES_IMPORTANTE = "tres_importante", "Très importante"
    MOYENNE = "moyenne", "Moyenne"
    FAIBLE = "faible", "Faible"


class ImportantPhysicalAspectsPartner(BaseStrEnum):
    TAILLE = "taille", "Taille"
    CORPULENCE = "corpulence", "Corpulence"
    STYLE_VESTIMENTAIRE = "style_vestimentaire", "Style vestimentaire"
    SOIN_HYGIENE = "soin_hygiene", "Soin de soi / hygiène"
    PEU_IMPORTE_RESSENTI = (
        "peu_importe_ressenti",
        "Peu importe, je me fie surtout au ressenti global",
    )


class ImportanceOfSexuality(BaseStrEnum):
    TRES_IMPORTANTE = "tres_importante", "Très importante"
    MOYENNE = "moyenne", "Moyenne"
    PEU_IMPORTANTE = "peu_importante", "Peu importante"
    PAS_IMPORTANTE_DU_TOUT = "pas_importante_du_tout", "Pas importante du tout"


class IdealIntimateFrequency(BaseStrEnum):
    PLUSIEURS_FOIS_SEMAINE = "plusieurs_fois_semaine", "Plusieurs fois par semaine"
    _1_2_FOIS_SEMAINE = "1_2_fois_semaine", "1–2 fois par semaine"
    QUELQUES_FOIS_MOIS = "quelques_fois_mois", "Quelques fois par mois"
    PEU_OU_PAS_SOUVENT = "peu_ou_pas_souvent", "Peu ou pas souvent"


class ComfortLevelTalkingSexuality(BaseStrEnum):
    TRES_A_LAISE = "tres_a_laise", "Très à l’aise"
    A_LAISE_SELON_PERSONNE = "a_laise_selon_personne", "À l’aise selon la personne"
    PEU_A_LAISE = "peu_a_laise", "Peu à l’aise"
    PAS_DU_TOUT_A_LAISE = "pas_du_tout_a_laise", "Pas du tout à l’aise"


class PartnerSexualValuesAlignment(BaseStrEnum):
    OUI = "oui", "Oui"
    NON_COMMUNIQUE = "non_communique", "Non, tant qu’on communique"
    PEU_IMPORTE = "peu_importe", "Peu importe"


class ComfortablePublicAffection(BaseStrEnum):
    OUI = "oui", "Oui"
    OUI_DISCRETION = "oui_discretion", "Oui, mais avec discrétion"
    NON = "non", "Non"


class PartnerSimilarityPreference(BaseStrEnum):
    TRES_SIMILAIRE = "tres_similaire", "Très similaire à toi"
    PLUTOT_COMPLEMENTAIRE = "plutot_complementaire", "Plutôt complémentaire"
    BON_MELANGE = "bon_melange", "Un bon mélange des deux"


class ImportanceFinancialSituationPartner(BaseStrEnum):
    TRES_IMPORTANTE_STABILITE = (
        "tres_importante_stabilite",
        "Très importante : je veux une stabilité financière claire",
    )
    ASSEZ_IMPORTANTE_EQUILIBRE = (
        "assez_importante_equilibre",
        "Assez importante : je cherche un équilibre, sans trop d’écart",
    )
    PEU_IMPORTANTE_VALEURS = "peu_importante_valeurs", "Peu importante : je privilégie les valeurs"
    PAS_DU_TOUT_IMPORTANTE = "pas_du_tout_importante", "Pas du tout importante"


class IdealPartnerEducationProfession(BaseStrEnum):
    ETUDES_EQUIVALENTES_SUPERIEURES = (
        "etudes_equivalentes_superieures",
        "Un niveau d'études équivalent ou supérieur au tien",
    )
    PEU_IMPORTE_ETUDES_INTELLIGENT = (
        "peu_importe_etudes_intelligent",
        "Peu importe le niveau d’études, tant qu’il/elle est intelligent(e)",
    )
    AMBITION_PROFESSIONNELLE_SIMILAIRE = (
        "ambition_professionnelle_similaire",
        "Une ambition professionnelle similaire",
    )
    PEU_IMPORTE_EPANOUI = "peu_importe_epanoui", "Peu importe, s’il/elle est épanoui(e)"


class PartnerMustWantChildren(BaseStrEnum):
    OUI = "oui", "Oui"
    NON = "non", "Non"
    PAS_FORCEMENT = "pas_forcément", "Pas forcément"


# Not used
class PracticeLevel(BaseStrEnum):
    NOT_PRACTICING = "non_pratiquant"
    OCCASIONALLY = "occasionnellement"
    REGULARLY = "regulierement"
    STRICTLY = "strictement"


class ComfortLevel(BaseStrEnum):
    VERY_UNCOMFORTABLE = "tres_inconfortable"
    UNCOMFORTABLE = "inconfortable"
    NEUTRAL = "neutre"
    COMFORTABLE = "confortable"
    VERY_COMFORTABLE = "tres_confortable"


class ImportanceLevel(BaseStrEnum):
    NOT_IMPORTANT = "pas_important"
    SOMEWHAT_IMPORTANT = "peu_important"
    IMPORTANT = "important"
    VERY_IMPORTANT = "tres_important"
    ESSENTIAL = "essentiel"


# others
class JourneyStatus(BaseStrEnum):
    ACTIVE = "active", "actif"
    ENDED = "ended", "termine"
    COMPLETED = "completed", "completé"


class MatchStatus(BaseStrEnum):
    PENDING = "pending", "En Attente"
    ACTIVE = "active", "actif"
    DECLINED = "declined", "rejeté"
    PAUSED = "paused", "pause"
    ENDED = "ended", "termine"


class SubscriptionType(BaseStrEnum):
    FREE = "gratuit"
    PREMIUM = "premium"


class JourneyStep(IntEnum):
    STEP1_PRE_COMPATIBILITY = 1
    STEP2_PHOTOS_UNLOCKED = 2
    STEP3_VOICE_VIDEO_CALL = 3
    STEP4_PHYSICAL_MEETING = 4
    STEP5_MEETING_FEEDBACK = 5


class MessageType(BaseStrEnum):
    TEXT = "texte"
    VOICE_CALL_REQUEST = "demande_appel_vocal"
    VIDEO_CALL_REQUEST = "demande_appel_video"


class MeetingStatus(BaseStrEnum):
    PROPOSED = "proposee"
    ACCEPTED = "acceptee"
    REJECTED = "refusee"
    COMPLETED = "terminee"
    CANCELLED = "annulee"


class FieldType(BaseStrEnum):
    TEXT = "text"
    TEXT_AREA = "text_area"
    INTEGER = "integer"
    RANGE = "range"
    SELECT = "select"
    FIELDS_GROUP = "fields_group"  # not used for now
    BOOLEAN = "boolean"
    MULTIPLE_SELECT = "multiple_select"
    ARRAY = "array"


class FieldUnit(BaseStrEnum):
    YEAR = "ans", "Ans"
    CM = "cm", "Cm"


class TwilioEvent(BaseStrEnum):
    ON_PARTICIPANT_ADD = "onParticipantAdd"
    ON_PARTICIPANT_ADDED = "onParticipantAdded"
    ON_PARTICIPANT_UPDATE = "onParticipantUpdate"
    ON_PARTICIPANT_UPDATED = "onParticipantUpdated"
    ON_PARTICIPANT_REMOVE = "onParticipantRemove"
    ON_PARTICIPANT_REMOVED = "onParticipantRemoved"
    ON_CONVERSATION_ADD = "onConversationAdd"
    ON_CONVERSATION_ADDED = "onConversationAdded"
    ON_CONVERSATION_UPDATE = "onConversationUpdate"
    ON_CONVERSATION_UPDATED = "onConversationUpdated"
    ON_CONVERSATION_REMOVE = "onConversationRemove"
    ON_CONVERSATION_REMOVED = "onConversationRemoved"
    ON_MESSAGE_ADD = "onMessageAdd"
    ON_MESSAGE_ADDED = "onMessageAdded"
    ON_MESSAGE_REMOVE = "onMessageRemove"
    ON_MESSAGE_REMOVED = "onMessageRemoved"
    ON_MESSAGE_UPDATE = "onMessageUpdate"
    ON_MESSAGE_UPDATED = "onMessageUpdated"
    ON_DELIVERY_UPDATED = "onDeliveryUpdated"
    ON_CONVERSATION_STATE_UPDATED = "onConversationStateUpdated"


def get_field_enum(field_name: str) -> BaseStrEnum | None:
    return fields_enums.get(field_name)


fields_enums = {
    "gender": Gender,
    "relationship_goal": RelationshipGoal,
    "professional_situation": ProfessionalSituation,
    "education_level": EducationLevel,
    "religious_practice": ReligiousPractice,
    "partner_must_share_religion": PartnerMustShareReligion,
    "faith_transmission_to_children": FaithTransmissionToChildren,
    "partner_same_religious_education_vision": PartnerSameReligiousEducationVision,
    "sport_frequency": SportFrequency,
    "specific_dietary_habits": SpecificDietaryHabits,
    "hygiene_tidiness_approach": HygieneTidinessApproach,
    "smoker": Smoker,
    "drinks_alcohol": DrinksAlcohol,
    "partner_sport_frequency": PartnerSportFrequency,
    "partner_same_dietary_habits": PartnerSameDietaryHabits,
    "partner_cleanliness_importance": PartnerCleanlinessImportance,
    "accept_smoker_partner": AcceptSmokerPartner,
    "accept_alcohol_consumer_partner": AcceptAlcoholConsumerPartner,
    "ready_to_live_with_pet": ReadyToLiveWithPet,
    "personality_type": PersonalityType,
    "partner_personality_preference": PartnerPersonalityPreference,
    "primary_love_language": PrimaryLoveLanguage,
    "friends_visit_frequency": FriendsVisitFrequency,
    "clothing_style": ClothingStyle,
    "appearance_importance": ImportanceOfAppearance,
    "partner_hygiene_appearance_importance": PartnerHygieneAppearanceImportance,
    "important_physical_aspects_partner": ImportantPhysicalAspectsPartner,
    "importance_of_sexuality": ImportanceOfSexuality,
    "ideal_intimate_frequency": IdealIntimateFrequency,
    "comfort_level_talking_sexuality": ComfortLevelTalkingSexuality,
    "partner_sexual_values_alignment": PartnerSexualValuesAlignment,
    "comfortable_public_affection": ComfortablePublicAffection,
    "partner_similarity_preference": PartnerSimilarityPreference,
    "importance_financial_situation_partner": ImportanceFinancialSituationPartner,
    "ideal_partner_education_profession": IdealPartnerEducationProfession,
    "partner_must_want_children": PartnerMustWantChildren,
    "tolerance_social_vs_homebody": ToleranceSocial,
    "partner_body_size": BodySize,
    "partner_clothing_style": PartnerClothingStyle,
}
