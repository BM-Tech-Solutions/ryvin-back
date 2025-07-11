from enum import Enum, IntEnum
from typing import List, Tuple


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
    def options(cls) -> List[Tuple[str, str]]:
        return [(member.value, member.label) for member in cls]


class Gender(BaseStrEnum):
    MALE = "homme"
    FEMALE = "femme"


class RelationshipType(BaseStrEnum):
    MARRIAGE = "mariage"
    SERIOUS_RELATIONSHIP = "relation_serieuse"


class SubscriptionType(BaseStrEnum):
    FREE = "gratuit"
    PREMIUM = "premium"


class JourneyStep(IntEnum):
    PRE_COMPATIBILITY = 1
    VOICE_VIDEO_CALL = 2
    PHOTOS_UNLOCKED = 3
    PHYSICAL_MEETING = 4
    MEETING_FEEDBACK = 5


class MatchStatus(BaseStrEnum):
    PENDING = "en_attente"
    ACTIVE = "actif"
    PAUSED = "pause"
    ENDED = "termine"


# Religion
class PracticeLevel(BaseStrEnum):
    NOT_PRACTICING = "non_pratiquant"
    OCCASIONALLY = "occasionnellement"
    REGULARLY = "regulierement"
    STRICTLY = "strictement"


class PartnerSameReligion(BaseStrEnum):
    YES = "yes"
    NO = "non"
    ITS_A_PLUS = "c'est_un_plus"


class TransFaithToChild(BaseStrEnum):
    YES = "yes"
    NO = "non"
    DONT_KNOW = "sais_pas"


class PartnerSameReligEducView(BaseStrEnum):
    YES = "yes"
    NO = "non"
    DONT_CARE = "peu_importe"


# sport, diet & hygene
class SportFrequency(BaseStrEnum):
    NEVER = "jamais"
    RARELY = "rarement"
    OCCASIONALLY = "occasionnellement"
    REGULARLY = "regulierement"
    DAILY = "quotidiennement"


class DietType(BaseStrEnum):
    OMNIVORE = "omnivore"
    VEGETARIAN = "vegetarien"
    VEGAN = "vegan"
    PESCATARIAN = "pescetarien"
    HALAL = "halal"
    KOSHER = "casher"
    OTHER = "autre"


class HygieneImportance(BaseStrEnum):
    VERY_CAREFUL = "tres_soigneux"
    CAREFUL = "soigneux"
    NORMAL = "normal"
    RELAXED = "detendu"


class SmokingFrequency(BaseStrEnum):
    YES = "oui"
    NO = "non"
    OCCASIONALLY = "occasionnellement"


class ConsumptionLevel(BaseStrEnum):
    NEVER = "jamais"
    RARELY = "rarement"
    OCCASIONALLY = "occasionnellement"
    REGULARLY = "regulierement"
    DAILY = "quotidiennement"


# Partner Choices
class PartnerSportFrequency(BaseStrEnum):
    NEVER = "jamais"
    RARELY = "rarement"
    OCCASIONALLY = "occasionnellement"
    REGULARLY = "regulierement"
    DAILY = "quotidiennement"
    DONT_CARE = "peu_importe"


class PartnerSameDietType(BaseStrEnum):
    YES = "oui"
    NO = "non"
    DONT_CARE = "peu_importe"


class PartnerHygieneImportance(BaseStrEnum):
    VERY_CAREFUL = "tres_soigneux"
    CAREFUL = "soigneux"
    NORMAL = "normal"
    DONT_CARE = "peu_importe"


class AcceptPartnerSmoking(BaseStrEnum):
    YES = "oui"
    NO = "non"
    OCCASIONALLY = "occasionnellement"


class AcceptPartnerAlcohol(BaseStrEnum):
    YES = "oui"
    NO = "non"
    OCCASIONALLY = "occasionnellement"


class AcceptPartnerAnimal(BaseStrEnum):
    YES = "oui"
    NO = "non"
    IT_DEPENDS = "ca_depend"


# personality & relations
class PersonalityType(BaseStrEnum):
    INTROVERT = "introverti"
    AMBIVERT = "ambivert"
    EXTROVERT = "extraverti"


class PartnerPersonalityType(BaseStrEnum):
    INTROVERT = "introverti"
    AMBIVERT = "ambivert"
    EXTROVERT = "extraverti"
    DONT_CARE = "peu_importe"


class LoveLanguage(BaseStrEnum):
    WORDS_OF_AFFIRMATION = "mots_d_affirmation"
    QUALITY_TIME = "temps_de_qualite"
    RECEIVING_GIFTS = "cadeaux"
    ACTS_OF_SERVICE = "services_rendus"
    PHYSICAL_TOUCH = "contact_physique"


class SocialFrequency(BaseStrEnum):
    RARELY = "rarement"
    MONTHLY = "mensuellement"
    WEEKLY = "hebdomadairement"
    SEVERAL_TIMES_WEEK = "plusieurs_fois_semaine"
    DAILY = "quotidiennement"


class SocialTolerance(BaseStrEnum):
    VERY_LOW = "tres_faible"
    LOW = "faible"
    MODERATE = "moderee"
    HIGH = "elevee"
    VERY_HIGH = "tres_elevee"


# Physique
class StyleType(BaseStrEnum):
    CASUAL = "decontracte"
    CLASSIC = "classique"
    ELEGANT = "elegant"
    SPORTY = "sportif"
    TRENDY = "tendance"
    ALTERNATIVE = "alternatif"
    OTHER = "autre"


class SelfAppearanceImportance(BaseStrEnum):
    VERY_IMPORTANT = "tres_important"
    AVERAGE = "moyenne"
    DONT_CARE = "peu_importe"


class PartnerAppearanceImportance(BaseStrEnum):
    VERY_IMPORTANT = "tres_important"
    AVERAGE = "moyenne"
    NOT_SO_MUCH = "faible"


# Intimité
class IntimacyImportance(BaseStrEnum):
    IMPORTANT = "tres_important"
    AVERAGE = "moyenne"
    DONT_CARE = "peu_importante"
    DONT_CARE_AT_ALL = "pas_importante_de_tous"


class IntimacyFrequency(BaseStrEnum):
    RARELY = "rarement"
    MONTHLY = "mensuellement"
    WEEKLY = "hebdomadairement"
    SEVERAL_TIMES_WEEK = "plusieurs_fois_semaine"
    DAILY = "quotidiennement"
    MULTIPLE_DAILY = "plusieurs_fois_jour"


class IntimacyTalkComfort(BaseStrEnum):
    VERY_COMFORTABLE = "tres_a_laise"
    DEPENDS_ON_PERSON = "selon_personne"
    BIT_COMFORTABLE = "peu_confortable"
    UNCOMFORTABLE = "inconfortable"


class SameIntimacyValues(BaseStrEnum):
    YES = "oui"
    NO = "non"
    DONT_CARE = "peu_importe"


class PublicAffectionLevel(BaseStrEnum):
    NONE = "aucune"
    MINIMAL = "minimale"
    MODERATE = "moderee"
    EXPRESSIVE = "expressive"
    VERY_EXPRESSIVE = "tres_expressive"


# compatibilité
class CompatibilityType(BaseStrEnum):
    COMPLEMENTARY = "complementaire"
    SIMILAR = "similaire"
    BALANCED = "equilibre"


class EducationLevel(BaseStrEnum):
    PRIMARY = "primaire"
    SECONDARY = "secondaire"
    HIGH_SCHOOL = "lycee"
    ASSOCIATE = "bac_plus_2"
    BACHELOR = "licence"
    MASTER = "master"
    DOCTORATE = "doctorat"
    OTHER = "autre"


class EducationPreference(BaseStrEnum):
    ANY = "indifferent"
    SIMILAR = "similaire"
    HIGHER = "superieur"
    LOWER = "inferieur"


class ImportanceLevel(BaseStrEnum):
    NOT_IMPORTANT = "pas_important"
    SOMEWHAT_IMPORTANT = "peu_important"
    IMPORTANT = "important"
    VERY_IMPORTANT = "tres_important"
    ESSENTIAL = "essentiel"


class ComfortLevel(BaseStrEnum):
    VERY_UNCOMFORTABLE = "tres_inconfortable"
    UNCOMFORTABLE = "inconfortable"
    NEUTRAL = "neutre"
    COMFORTABLE = "confortable"
    VERY_COMFORTABLE = "tres_confortable"


class ProfessionalStatus(BaseStrEnum):
    STUDENT = "etudiant"
    EMPLOYED = "employe"
    SELF_EMPLOYED = "independant"
    UNEMPLOYED = "sans_emploi"
    RETIRED = "retraite"
    OTHER = "autre"


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
    SELECT = "select"
    BOOLEAN = "boolean"


def get_field_enum(field_name: str) -> BaseStrEnum | None:
    return fields_enums.get(field_name)


fields_enums = {
    "est_pratiquant": PracticeLevel,
    "partenaire_meme_religion": PartnerSameReligion,
    "transmission_foi_enfants": TransFaithToChild,
    "meme_vision_education_religieuse": PartnerSameReligEducView,
    "frequence_sport": SportFrequency,
    "habitudes_alimentaires": DietType,
    "approche_hygiene": HygieneImportance,
    "fume": SmokingFrequency,
    "boit_alcool": ConsumptionLevel,
    "sport_partenaire": PartnerSportFrequency,
    "memes_habitudes_alimentaires": PartnerSameDietType,
    "importance_proprete_partenaire": PartnerHygieneImportance,
    "accepte_fumeur": AcceptPartnerSmoking,
    "accepte_buveur": AcceptPartnerAlcohol,
    "accepte_partenaire_avec_animal": AcceptPartnerAnimal,
    "style_vestimentaire": StyleType,
    "importance_apparence_soi": SelfAppearanceImportance,
    "importance_apparence_partenaire": PartnerAppearanceImportance,
    "personalite": PersonalityType,
    "preference_personalite_partenaire": PartnerPersonalityType,
    "langage_amour": LoveLanguage,
    "frequence_voir_amis": SocialFrequency,
    "tolerance_mode_vie_social": SocialTolerance,
    "importance_intimite": IntimacyImportance,
    "frequence_intimite_ideale": IntimacyFrequency,
    "confort_discussion_intimite": IntimacyTalkComfort,
    "niveau_affection_publique": PublicAffectionLevel,
    "type_compatibilite_recherchee": CompatibilityType,
}
